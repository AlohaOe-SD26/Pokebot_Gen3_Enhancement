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
# ⛔⛔ `_check_abort` IS IMPORTED AT MODULE LEVEL ON PURPOSE (2026-09-16). This file's own §Ch24 probe
# docstring records the trap three times over: *"a helper another function imported locally is NOT
# available to yours, and the first run of this probe died on `NameError: name '_check_abort' is not
# defined` after correctly reaching the lobby."* A bounded loop that calls it would otherwise raise
# NameError on the ABORT path only — the one path no happy-path drive ever exercises.
from modules.story.early_game import _check_abort, wait_until_truly_controllable
from modules.story.overworld_items import Target, plan_healing, party_is_gauntlet_ready
from modules.tasks import task_is_active


def _take(report: dict, reading: str) -> None:
    """Record that a reading actually happened. ⛔ A grade must enumerate what OCCURRED."""
    report.setdefault("readings", set()).add(reading)


# ⛔ ONE IMPLEMENTATION, NOT TWO. These position/budget helpers already exist in
# `modules/story/victory_road.py` and are proven across eleven driven legs. Re-declaring them here
# would be "the same fact in two functions", which that module's own comment calls the P5 doc shape
# in code form — it drifts. Function-local import keeps the module graph acyclic.
def _where():
    from modules.story.victory_road import _where as _impl

    return _impl()


def _here_tile():
    from modules.story.victory_road import _here_tile as _impl

    return _impl()


def _on_map(map_enum) -> bool:
    from modules.story.victory_road import _on_map as _impl

    return _impl(map_enum)


def _navigate_riding_out(map_enum, tile: tuple):
    from modules.story.victory_road import _navigate_riding_out as _impl

    return _impl(map_enum, tile)


def _budgeted(generator, frames: int, what: str):
    from modules.story.victory_road import _budgeted as _impl

    return _impl(generator, frames, what)

#: ⛔⛔ **ITERATIONS, NOT FRAMES — THE OLD COMMENT WAS WRONG BY 4× (corrected 2026-09-16).**
#: *(It read “Frames to spend on one item use before giving up.”)* The loop it bounds does
#: `wait_for_n_frames(4)` per iteration, so 900 iterations is ~**3,600 frames** — and the ENTIRE
#: measured seven-action heal cost **2,949** frames of controller time (`ch24heal`, 2026-09-04).
#: ⇒ this 'bound' is ~8.5× the whole operation it is supposed to cap, i.e. it would not catch a
#: hang inside one item use until long after the run had visibly stopped.
#: ‼ LEFT AT 900 DELIBERATELY: lowering it is a BEHAVIOUR change to the gauntlet's only healing
#: path, and no per-call frame cost has ever been measured to justify a number. What is fixed
#: here is the LIE, not the value — a bound nobody can reason about is worse than a loose one.
#: A bound, not a preference: a menu that never reaches the next state is a hung run, and this
#: one runs where there is no escape.
ONE_USE_BUDGET = 900

#: ⛔ THE TASK THE PARTY MENU RUNS UNDER while asking "Use on which POKéMON?".
#: `CB2_ShowPartyMenuForItemUse` (`src/party_menu.c:4229-4272`) sets `sPartyMenuInternal->task` to
#: this, and `src/party_menu.c:505,663` create it. ⭐ This is the state our code had never driven.
CHOOSE_MON_TASK = "Task_HandleChooseMonInput"

#: The bag's context menu. Medicine has FOUR actions (USE/GIVE/TOSS/CANCEL — `src/item_menu.c:286`),
#: and `:1683-1688` picks the MultipleRows task when there are more than two. ⭐ The cursor starts on
#: index 0 = `ACTION_USE`, so a plain A selects "Use" with no navigation.
ITEM_CONTEXT_TASK = "Task_ItemContext_MultipleRows"

#: ⛔ EVERY context-menu task the bag can raise. `src/item_menu.c:1683-1688` picks SingleRow when the
#: item has <= 2 actions and MultipleRows otherwise, so the task depends on the ITEM, not the pocket.
#: ‼ Naming only one of these cost four drives — the bot sat on the bag list and the failure blamed
#: the party cursor. ⇒ accept them all; the diagnostic names what was really up.
ITEM_CONTEXT_TASKS = (
    "Task_ItemContext_MultipleRows",
    "Task_ItemContext_SingleRow",
    "Task_ItemContext_ItemPc_MultipleRows",
    "Task_FieldItemContextMenuHandleInput",
)


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
    # ⛔⛔ THIS LINE LOOKS WRONG AND IS NOT — A “FIX” HERE WAS MEASURED AS A REGRESSION 2026-09-16.
    # The concern is real: this waits on the SINGULAR `ITEM_CONTEXT_TASK`, while the file defines
    # `ITEM_CONTEXT_TASKS` (all four) precisely because naming only one cost four drives on the
    # TEACH path — and that fix was never applied here.
    # ‼ BUT THE OBVIOUS TRANSPLANT BREAKS IT. Replacing this with the teach path's bounded
    # accept-any-task loop (`scroll_to_tm_verified`, ~:536) turns a START-**AND-FINISH** wait into a
    # START-ONLY wait: that loop stops pressing A once the context menu OPENS, so “Use” is never
    # SELECTED and the party menu never appears. MEASURED A/B on `--driver ch24heal`,
    # `post_league_shop.ss1`, same staged damage:
    #     BEFORE  ready=True  failure=None                       ACCEPTANCE: PASS (7 actions)
    #     AFTER   ready=False failure=…Task_HandleChooseMonInput ACCEPTANCE: FAIL (0 actions)
    # evidence: `tools/story-dev/evidence/2026-09-16-ch24heal-{BASELINE,AFTER-fixes}.stdout.txt`.
    # ⇒ the correct fix must generalise START-AND-FINISH across all four task names, not borrow a
    # loop whose contract is only START. Filed as `#24-itemcontextplural`; do NOT retry the
    # transplant without re-running that A/B.
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


def _screen_message() -> str:
    """Decode the game's on-screen message buffer, or "" if it cannot be read.

    ⛔ A DIAGNOSTIC MUST NEVER REPLACE THE DIAGNOSIS WITH A CRASH — hence the broad except. This is
    the one exception to the no-silent-except ratchet's spirit that the ratchet itself allows: it
    returns a sentinel that is PRINTED, so a failure to read is visible rather than swallowed.
    """
    try:
        from modules.memory import read_symbol
        from modules.game import decode_string

        return decode_string(read_symbol("gStringVar4", size=0x3E8)).strip()
    except Exception as _e:  # noqa: BLE001 — returns a PRINTED sentinel naming the exception type,
        # so a failed read is visible in the trace rather than swallowed. ⛔ Never widen this to
        # return "" — an empty string is indistinguishable from "the game said nothing", which is
        # exactly the ambiguity that cost six drives here.
        return f"<unreadable: {type(_e).__name__}>"


def _bag_cursor_item() -> str:
    """Name the item the BAG CURSOR IS ON, read back out of `gBagPosition`.

    ⛔ THIS IS THE READING THAT WAS NEVER TAKEN. `[TEACH-ITEM]` printed the pocket's CONTENTS and
    was mistaken for proof that the right item was selected — the exact "a candidate is not an
    attempt" trap this project has written down twice. The cursor is the only thing A acts on.
    Offsets mirror `modules/menuing.py::scroll_to_item_slot::currently_selected_slot`.
    """
    try:
        from modules.items import get_item_bag
        from modules.memory import read_symbol, unpack_uint16

        pocket_index = read_symbol("gBagPosition", offset=0x05, size=1)[0]
        cursor = unpack_uint16(read_symbol("gBagPosition", offset=8 + (pocket_index * 2), size=2))
        scroll = unpack_uint16(read_symbol("gBagPosition", offset=18 + (pocket_index * 2), size=2))
        slot = cursor + scroll
        pocket = get_item_bag().tms_hms
        name = pocket[slot].item.name if 0 <= slot < len(pocket) else "<out of range>"
        return f"pocket={pocket_index} slot={slot} -> {name}"
    except Exception as _e:  # noqa: BLE001 — a diagnostic must not replace the diagnosis
        return f"<unreadable: {type(_e).__name__}>"


def _bag_cursor_slot() -> int:
    """The TM/HM pocket slot the cursor is on, from `gBagPosition`. -1 if unreadable."""
    try:
        from modules.memory import read_symbol, unpack_uint16

        pocket_index = read_symbol("gBagPosition", offset=0x05, size=1)[0]
        cursor = unpack_uint16(read_symbol("gBagPosition", offset=8 + (pocket_index * 2), size=2))
        scroll = unpack_uint16(read_symbol("gBagPosition", offset=18 + (pocket_index * 2), size=2))
        return cursor + scroll
    except Exception:  # noqa: BLE001 — the caller RAISES on -1; this never silently passes
        return -1


def scroll_to_tm_verified(item: Item) -> Generator:
    """Put the bag cursor on `item` and PROVE it is there before anyone presses A.

    ⛔⛔ MEASURED 2026-09-05: upstream's `scroll_to_item_in_bag` returns SUCCESSFULLY with the cursor
    on the wrong item. Asked for TM13 (Ice Beam) it left the cursor on **HM08 Dive** — it scrolls to
    a slot number from `first_slot_index_for()`, and for TM13 that number is not the slot the
    on-screen cursor counts. The bot then used Dive on Wailord and the game said *"DIVER already
    knows DIVE."*, bouncing back to the bag with nothing consumed. ‼ SIX diagnoses were spent
    downstream of this, every one of them about the party menu, because the item side had only ever
    been "verified" by printing the pocket's CONTENTS — which is not the cursor.
    ⇒ ⭐ **A CANDIDATE IS NOT AN ATTEMPT. Read what A will act on.**

    Corrective scroll uses `get_item_bag().tms_hms`, which the same measurement showed IS the order
    the on-screen cursor counts (slot 13 in that list is HM08, exactly what the game used).
    """
    from modules.modes.util.items import scroll_to_item_in_bag

    def _under_cursor() -> "tuple[int, str]":
        pocket = get_item_bag().tms_hms
        slot = _bag_cursor_slot()
        return slot, (pocket[slot].item.name if 0 <= slot < len(pocket) else "<out of range>")

    yield from scroll_to_item_in_bag(item)          # upstream first: correct for most items
    slot, name = _under_cursor()
    if name == item.name:
        return

    pocket = [s.item.name for s in get_item_bag().tms_hms]
    if item.name not in pocket:
        raise BotModeError(f"§Ch24 teach: {item.name} is not in the TM/HM pocket ({pocket}).")
    want = pocket.index(item.name)
    print(f"[TEACH-CURSOR] ⛔ upstream left the cursor on slot {slot} ({name}); correcting to "
          f"slot {want} ({item.name}).")

    # Closed-loop and BOUNDED — a pocket has at most ~60 slots, so ~120 presses is generous and
    # cannot spin. ‼ Never `while True`: KI-38 is this project's most expensive unbounded loop.
    for _ in range(120):
        slot = _bag_cursor_slot()
        if slot == want:
            break
        if slot < 0:
            raise BotModeError("§Ch24 teach: could not read the bag cursor from `gBagPosition`.")
        context.emulator.press_button("Down" if slot < want else "Up")
        yield
        yield
        yield

    slot, name = _under_cursor()
    if name != item.name:
        raise BotModeError(
            f"§Ch24 teach: could not put the bag cursor on {item.name}; it is on slot {slot} "
            f"({name}). ⛔ Refusing to press A — a Gen-3 TM is single-use, and pressing A on the "
            f"wrong item is exactly how this leg wasted six drives. Pocket order: {pocket}."
        )
    print(f"[TEACH-CURSOR] verified: cursor on slot {slot} -> {name}")


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

    # ⛔⛔ YOU CANNOT FORGET AN HM MOVE. THE ANSWER WAS IN THE TASK NAME ALL ALONG:
    # the forget-move screen is `Task_HandleInputCantForget**HMs**Moves`.
    # ‼ MEASURED 2026-09-05 across FOUR drives: asking to replace Wailord's **Dive (HM08)** made the
    # game refuse the TM and bounce straight back to the bag. Wailord knows Dive (HM08), Surf (HM03)
    # and Waterfall (HM07) — **three of its four slots are unforgettable** — so the plan was asking
    # for the one thing the engine will never do.
    # ⭐ Upstream's `teach_hm_or_tm` has exactly this check (`items.py:188-195`); I dropped it when I
    # wrote my own driver and then spent four drives rediscovering it. ⇒ **WHEN YOU REPLACE A PROVEN
    # HELPER, PORT ITS GUARDS FIRST — they are the part that encodes what it learned.**
    from modules.items import get_item_by_move_id

    doomed = target.moves[move_index_to_replace]
    if doomed is not None and doomed.move is not None:
        as_item = get_item_by_move_id(doomed.move.index)
        if as_item is not None and as_item.name.startswith("HM"):
            raise BotModeError(
                f"§Ch24 teach: {target.species.name} cannot forget {doomed.move.name} — it is an HM "
                f"move ({as_item.name}). ⛔ The game refuses, silently bouncing back to the bag. "
                f"Pick a non-HM slot. {target.species.name} knows: "
                f"{[m.move.name for m in target.moves if m is not None and m.move is not None]}."
            )

    # ⛔ BASELINE FIRST. `gStringVar4` is never cleared, so a message is evidence only if it CHANGED.
    print(f"[TEACH-BASELINE] gStringVar4 on entry = {_screen_message()!r}")
    print(f"[TEACH-BASELINE] target nickname={target.nickname!r} species={target.species.name!r} "
          f"moves={[m.move.name for m in target.moves if m is not None and m.move is not None]}")
    yield from StartMenuNavigator("BAG").step()
    # ⛔ NOT `scroll_to_item_in_bag` — it returns success with the cursor on the WRONG ITEM. See
    # `scroll_to_tm_verified`, which proves the cursor before anything presses A.
    yield from scroll_to_tm_verified(item)
    print(f"[TEACH-CURSOR] armed: {_bag_cursor_item()}")
    # ⛔ (retired) INSTRUMENT THE OTHER HALF OF THE ACTION. Five diagnoses blamed the PARTY cursor and a
    # trace proved that side CORRECT. The ITEM side was never measured — and "used an HM the mon
    # already knows" produces exactly the observed bounce-to-bag with nothing consumed.
    try:
        from modules.items import get_item_bag as _gib

        _pocket = [s.item.name for s in _gib().tms_hms]
        print(f"[TEACH-ITEM] asked for {item.name}; TM/HM pocket order = {_pocket}")
    except Exception as _e:  # noqa: BLE001 — a diagnostic must not replace the diagnosis
        print(f"[TEACH-ITEM] asked for {item.name}; pocket unreadable: {type(_e).__name__}")

    # ---- open the context menu and take "Use" ----------------------------------------------------
    # ⛔⛔ THE CONTEXT-MENU TASK DEPENDS ON HOW MANY ACTIONS THE ITEM HAS.
    # `src/item_menu.c:1683-1688`: `if (contextMenuNumItems <= 2) SingleRow else MultipleRows`. A
    # medicine in the ITEMS pocket has four actions (USE/GIVE/TOSS/CANCEL) -> MultipleRows; a TM in
    # the TM/HM pocket does NOT necessarily.
    # ‼ MEASURED 2026-09-05: waiting only for `Task_ItemContext_MultipleRows` left the bot sitting on
    # the bag LIST with `Task_BagMenu_HandleInput` active — it never opened the menu at all, and the
    # leg died four drives running with a message about the party slot that was pure misdirection.
    # ⇒ ⭐ **ACCEPT EVERY CONTEXT TASK, AND SAY WHAT WAS ACTUALLY UP IF NONE APPEARS.** A wait that
    # times out mute is how three separate task-name mistakes cost this session its afternoon.
    from modules.tasks import get_tasks

    opened_menu = False
    for _ in range(300):
        if any(task_is_active(n) for n in ITEM_CONTEXT_TASKS):
            opened_menu = True
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)
    if not opened_menu:
        live = [k.symbol for k in get_tasks()]
        raise BotModeError(
            f"§Ch24 teach: pressed A on {item.name} in the bag for 300 frames and none of "
            f"{ITEM_CONTEXT_TASKS} became active. ⛔ LIVE TASKS: {live}. The item-context task "
            f"depends on the action count (`item_menu.c:1683`), so a TM may use a different one "
            f"than medicine — add whichever of these is the context menu to ITEM_CONTEXT_TASKS."
        )
    print(f"[TEACH-CURSOR] context menu open; bag cursor = {_bag_cursor_item()}; "
          f"gStringVar4 = {_screen_message()!r}")
    # Take "Use" — the cursor starts on index 0 = ACTION_USE.
    context.emulator.press_button("A")
    yield from wait_for_n_frames(6)

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
    # ⛔⛔ THE PARTY CURSOR NEEDS THE SAME STABILITY REQUIREMENT THE MOVE CURSOR GOT.
    # ‼ MEASURED 2026-09-05: this loop broke on a SINGLE matching read. `gPartyMenu` offset 9 is
    # still settling while the party menu animates in — the identical hazard `battle_move_replacing`
    # documents for `sMonSummaryScreen` (2026-07-25: *"a stale read of 4 while the real cursor sat on
    # slot 1"*). A stale match here presses A on the WRONG POKEMON, the game refuses the TM (only
    # Wailord, Zigzagoon and Castform can learn TM13 — Sceptile CANNOT), and the flow bounces
    # straight back to the bag.
    # ⇒ ⭐ **I FIXED THIS EXACT SHAPE FOR THE MOVE CURSOR EARLIER TODAY AND DID NOT CARRY IT ACROSS
    # TO THE PARTY CURSOR TWENTY LINES ABOVE.** A rule applied to one of two cursors in the same
    # function is not applied.
    stable = 0
    landed = False
    _ptrace = []
    for _ in range(180):
        cursor = _slot_cursor()
        if len(_ptrace) < 30:
            _ptrace.append(cursor)
        if cursor == party_index:
            stable += 1
            if stable >= FORGET_CURSOR_STABLE_READS:
                landed = True
                break
            yield
            continue
        stable = 0
        context.emulator.press_button("Down" if cursor < party_index else "Up")
        yield
        yield
    # ⛔ INSTRUMENT THE ACTION: what the cursor READ, and WHICH POKEMON is under it when A is
    # pressed. Naming the intended target proves nothing — five drives blamed the wrong thing.
    try:
        _under = get_party()[_slot_cursor()]
        _under_name = _under.species.name if _under is not None and _under.species else "<none>"
    except Exception:  # noqa: BLE001 — the diagnostic must not replace the diagnosis with a crash
        _under_name = "<unreadable>"
    print(f"[TEACH-PARTY] want slot {party_index} ({target.species.name}); cursor reads={_ptrace}; "
          f"landed={landed}; mon under cursor at A-press = {_under_name}; "
          f"gStringVar4 = {_screen_message()!r}")
    if not landed:
        raise BotModeError(
            f"§Ch24 teach: could not settle the party cursor on slot {party_index} "
            f"({target.species.name}); it reads {_slot_cursor()}. ⛔ Refusing to press A on the "
            f"wrong Pokemon — a Gen-3 TM is single-use."
        )
    context.emulator.press_button("A")
    yield

    # ---- ⛔ THE FORGET-MOVE SCREEN. Advance WITHOUT mashing past it. ------------------------------
    # A-presses here are gated on the screen NOT being up yet, which is exactly the guard the
    # upstream helper lacks.
    # ⛔⛔ CHECK EVERY FRAME, AND STOP PRESSING THE INSTANT THE SCREEN IS UP.
    # ‼ MEASURED 2026-09-05, after FIVE wrong diagnoses. A party-cursor trace proved the selection
    # was correct all along (`cursor reads=[2,2,2,2,2,2,2,3,3,3]; mon under cursor = Wailord`), which
    # left only this loop. It pressed A and then slept 4 frames — so the forget-move screen could
    # APPEAR and be dismissed by the very next press, confirming its default: **move index 0, which
    # is Dive, an HM**. The game refuses (HMs cannot be forgotten), asks "give up learning?", and the
    # same mash confirms THAT. ⇒ bounce back to the bag, nothing learned, nothing consumed.
    # ⛔⛔ THIS IS EXACTLY `KI-88`, WHICH I WROTE UP FOR UPSTREAM THIS MORNING — *"its A-mash can blow
    # past the move-selection screen and confirm the default cursor at index 0"* — AND THEN REBUILT
    # IN THE REPLACEMENT I WROTE TO AVOID IT.
    # ⇒ ⭐ **DOCUMENTING A BUG DOES NOT INOCULATE YOU AGAINST WRITING IT.** The guard has to be in the
    # code, not in the note about the code.
    up = False
    press_cooldown = 0
    _msgs: "list[str]" = []  # ⛔ EVERY DISTINCT THING THE GAME SAID, IN ORDER. See `_screen_message`.
    for _ in range(1800):
        _m = _screen_message()
        if _m and (not _msgs or _msgs[-1] != _m):
            _msgs.append(_m)
        if any(task_is_active(n) for n in FORGET_MOVE_TASKS):
            up = True
            break
        if get_game_state() is GameState.BAG_MENU:
            print(f"[TEACH-SAID] {len(_msgs)} distinct message(s) before the bounce:")
            for _i, _s in enumerate(_msgs):
                print(f"[TEACH-SAID]   {_i}: {_s!r}")
            # ⛔⛔ NEVER SILENTLY DERAIL. This used to `return` here, treating "bounced back to the
            # bag" as success — which is how a REFUSED teach reported nothing and left the caller's
            # post-condition to notice that the moveset had not changed. Two drives ended exactly
            # that way.
            # ⇒ Distinguish the two cases the bounce can mean, and say which:
            #    * the mon had an EMPTY move slot -> it learned the move, nothing to forget: SUCCESS
            #    * the game REFUSED (wrong target, incompatible species): FAILURE
            # The only honest discriminator is whether the mon now knows the move.
            learned = any(
                mv is not None and mv.move is not None and mv.move.name == item.tm_hm_move().name
                for mv in get_party()[party_index].moves
            )
            if learned:
                return
            raise BotModeError(
                f"§Ch24 teach: {item.name} bounced back to the BAG without "
                f"{target.species.name} learning {item.tm_hm_move().name}. ⛔ The game REFUSED the "
                f"teach. ⛔ READ `[TEACH-SAID]` ABOVE — the game's own message is the diagnosis, "
                f"and six inferences from BEHAVIOUR alone were wrong before it was ever read. "
                f"Nothing was consumed."
            )
        # Press at most once every 8 frames, and NEVER on the frame after a press — the screen
        # needs a window in which no input lands, or it is dismissed before it can be seen.
        if press_cooldown <= 0:
            context.emulator.press_button("A")
            press_cooldown = 8
        else:
            press_cooldown -= 1
        yield
    if not up:
        raise BotModeError(
            f"§Ch24 teach: none of {FORGET_MOVE_TASKS} appeared for {target.species.name} within "
            f"1800 frames. ⛔ WHAT THE GAME SAID, in order: {_msgs}. "
            f"LIVE TASKS: {[k.symbol for k in get_tasks()]}. state={get_game_state()}."
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


def _bag_has(item_name: str) -> bool:
    """Is `item_name` in the ITEMS pocket? ⛔ Read the bag, never assume a pickup landed."""
    return any(s.item.name == item_name for s in get_item_bag().items if s.quantity > 0)


def _tm_pocket_has(item_name: str) -> bool:
    """Is `item_name` in the TM/HM pocket?

    ‼ A SEPARATE POCKET, AND THAT MATTERS: `get_item_bag().items` is the ITEMS pocket ONLY. Reading
    a TM through it returns nothing and looks exactly like "the pickup failed" — measured 2026-09-05,
    when a bag dump reported an EMPTY TM/HM list because it filtered `.items` by name prefix.
    """
    return any(s.item.name == item_name for s in get_item_bag().tms_hms if s.quantity > 0)


# ==================================================================================================
# §Ch24 PREP — `#24-icebeamtrip`: FETCH TM13 ICE BEAM
# ==================================================================================================
#: ⭐⭐ WHY: Drake is 4/5 dragon-ish and carries ZERO Ice moves; Wailord takes only 22-56% from his
#: whole team. With Ice Beam, Wailord is predicted to do Flygon 88% / Salamence 73% / Altaria 71% /
#: Shelgon 71% — and **Flygon has LEVITATE**, so Ice is the ONLY super-effective type reachable on
#: it. ⚠ PREDICTED, NOT OBSERVED (IV-31/EV-0, ±15%, Intimidate unmodelled): the bot has never fought
#: Drake. Cost: ₽0.
#:
#: ⛔⛔ EVERY COORDINATE BELOW WAS READ FROM **OUR OWN RUNTIME MAP DATA**, not from the decomp — via
#: `get_map_data(<map>.value, (0,0)).warps / .objects / .bg_events` against `post_slateport.ss1`.
#: The decomp recon agreed, which is reassuring and is NOT why these are trusted: this project's rule
#: is that our own data outranks a decomp claim, because it is what the bot will actually see.
#:
#: THE CHAIN, measured (map numbers: 54=DECK, 55=CORRIDORS_1F, 57=CORRIDORS_B1F, 61=ROOM_B1F,
#: 63=CAPTAINS_OFFICE):
#:   ROUTE108 (29,6)        -> DECK              ‼ the ONLY warp on Route 108, so it is unambiguous
#:   DECK (12,5)            -> CAPTAINS_OFFICE   [Storage Key at (0,6)]
#:   CAPTAINS_OFFICE (7,6)  -> DECK
#:   DECK (13,9)            -> CORRIDORS_1F
#:   CORRIDORS_1F (16,2)    -> CORRIDORS_B1F
#:   CORRIDORS_B1F (11,4)   -> ROOM_B1F          [TM13 at (4,4)] — GATED on the Storage Key
#: ⇒ ⭐ **NO DIVE IS REQUIRED** — the route never touches `ABANDONED_SHIP_UNDERWATER1/2`. That is a
#: STRUCTURAL fact from the warp tables, not an inference.
#: ⚠ ⛔ **THERE ARE TWO SIMILARLY NAMED MAPS**: `ABANDONED_SHIP_ROOMS_B1F` (plural, map 58) and
#: `ABANDONED_SHIP_ROOM_B1F` (singular, map 61). **The TM is in the SINGULAR one.** The FLAG,
#: confusingly, is named `..._ROOMS_B1F_TM_ICE_BEAM` — plural. Do not "correct" either.

SHIP_ENTRANCE = (29, 6)          # ROUTE108's only warp -> the deck
#: ⛔ THE TILE WE NAVIGATE TO *BEFORE* THE WARP — non-warp, walkable, elevation 3, and MEASURED as
#: where drive 1 actually came to rest. Aiming AT the warp is what stuck the navigator.
#: ⛔ THE TILE WE SURF TO, DIRECTLY SOUTH OF THE ARROW. The arrow fires NORTH, so we must arrive
#: from below. (29,7) is `MB_OCEAN_WATER`, elevation 1, surfable — the sea outside the shelf.
SHIP_APPROACH = (29, 7)
#: ⚠ (30,6) is **"Shallow Water"** at elevation 3 — part of the shelf, NOT a land platform as an
#: earlier note here claimed. Kept only to document that aiming at it WEDGES the navigator:
#: the warp-override rewrites the destination to the deck, the bot walks to (30,6), and then
#: re-paths (30,6)->(30,6) = ZERO waypoints forever. Do not aim here.
SHIP_APRON_DO_NOT_USE = (30, 6)

#: The interior warp tiles, all read from our own `get_map_data(...).warps`.
DECK_TO_CAPTAINS_OFFICE = (12, 5)
CAPTAINS_OFFICE_TO_DECK = (7, 6)
DECK_TO_CORRIDORS_1F = (13, 9)
CORRIDORS_1F_TO_B1F = (16, 2)

#: The two item balls. ⛔ Tiles and flags are MEASURED from `.objects`; the flag names came back
#: attached to the objects themselves, so they cannot be mistyped here the way a hand-copied name can.
STORAGE_KEY_BALL = {
    "map": "ABANDONED_SHIP_CAPTAINS_OFFICE", "tile": (0, 6),
    "flag": "ITEM_ABANDONED_SHIP_CAPTAINS_OFFICE_STORAGE_KEY", "item": "Storage Key",
}
ICE_BEAM_BALL = {
    "map": "ABANDONED_SHIP_ROOM_B1F", "tile": (4, 4),
    "flag": "ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM", "item": "TM13",
}

#: The locked door: a BG **Script** event at CORRIDORS_B1F (11,4) with `player_facing_direction:
#: 'Any'`, running `AbandonedShip_Corridors_B1F_EventScript_StorageRoomDoor`, which does
#: `checkitem ITEM_STORAGE_KEY`. A WARP sits on the SAME tile. ⇒ the script gates the warp.
STORAGE_DOOR = (11, 4)

#: ⚠ A TRAINER SITS BETWEEN THE STAIRS AND THE DOOR: **Duncan**, CORRIDORS_B1F (9,6),
#: `trainer: {type Normal, range 4, is_defeated False}`. Expect a battle — the party is L47-53, so
#: this is TIME and attrition, not a loss risk. It is REPORTED, never graded.
CORRIDORS_B1F_TRAINER = (9, 6)

ICEBEAM_BUDGET = 400_000
#: ⛔ `RIB-TAUGHT` IS DELIBERATELY NOT HERE. The leg's contract is **"TM13 is in the bag and the bot
#: is back outside"** — the teach is `#24-icebeamteach`, a separate item, because it cost six drives
#: and does not need a 700k-frame ship trip to reproduce once `post_icebeam.ss1` exists.
ICEBEAM_READINGS = ("RIB-KEY", "RIB-DOOR", "RIB-TM", "RIB-OUT")


def _insert_storage_key(report=None) -> Generator:
    """Press A at the Storage Room door to INSERT the key, and assert the door actually unlocked.

    ⛔⛔ THIS STEP EXISTS BECAUSE THE DOOR IS **METATILE-GATED, NOT WARP-GATED**. While
    `FLAG_USED_STORAGE_KEY` is unset, the map's `OnLoad` stamps (11,4) with a LOCKED metatile whose
    behaviour is `MB_NORMAL` — so `TryDoorWarp` can never fire and the tile is, to the engine, a
    wall. Holding the key changes nothing on its own.
    ⭐ GRADED ON THE FLAG, NOT ON THE PRESS: `FLAG_USED_STORAGE_KEY` going True is the only signal
    that the script ran to completion. "We pressed A" is not "the door is open".
    """
    report = report if report is not None else {}
    from modules.memory import get_event_flag
    from modules.modes.util.walking import ensure_facing_direction
    from modules.map_data import MapRSE

    CORR_B1F = MapRSE.ABANDONED_SHIP_CORRIDORS_B1F
    if get_event_flag("USED_STORAGE_KEY"):
        report["door_already_open"] = True
        return

    approach, facing = _ball_approach(CORR_B1F, STORAGE_DOOR, "storage room door")
    report["door_approach"] = {"tile": approach, "facing": facing}
    yield from _navigate_riding_out(CORR_B1F, approach)
    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction(facing)
    yield

    for _frame in range(900):
        if get_event_flag("USED_STORAGE_KEY"):
            break
        context.emulator.press_button("A")
        yield
        yield from wait_for_n_frames(3)
    report["door_unlocked"] = get_event_flag("USED_STORAGE_KEY")
    if not report["door_unlocked"]:
        raise BotModeError(
            f"§Ch24 ice beam: pressed A at the Storage Room door from {approach} facing {facing} "
            f"for 900 frames and `FLAG_USED_STORAGE_KEY` is still unset. ⛔ Without it the tile at "
            f"{STORAGE_DOOR} stays MB_NORMAL — a wall — and no warp can fire."
        )
    # ‼ A flag set by a script is NOT the end of that script (the Strength lesson) — ride the rest
    # of the message chain out before anything else touches the D-pad.
    from modules.story.early_game import _ride_out_scripted_scene

    yield from _ride_out_scripted_scene("B")


def _ball_approach(map_enum, ball_tile: tuple, label: str) -> tuple:
    """MEASURE which neighbour of an item ball we can stand on. Returns `(tile, facing)`.

    ⛔ DERIVED, NEVER HARDCODED — the project rule, and `collect_item_ball`'s own docstring demands
    it: *"Not every neighbour is reachable — the Magma Hideout's Escape Rope had exactly one usable
    approach out of four — so the caller passes the approach and facing it measured."*
    ⭐ This is `victory_road._ladder_apron` re-pointed at an object instead of a ladder; the returned
    facing is the direction to press FROM the approach TOWARD the ball, which is the OPPOSITE of the
    offset that produced it. ‼ Three index/direction inversions have shipped in this codebase.
    """
    from modules.story.victory_road import _can_reach

    bx, by = ball_tile
    for (dx, dy), facing in (((1, 0), "Left"), ((-1, 0), "Right"),
                             ((0, 1), "Up"), ((0, -1), "Down")):
        candidate = (bx + dx, by + dy)
        if _can_reach(map_enum, candidate):
            return candidate, facing
    raise BotModeError(
        f"§Ch24 {label}: the item ball {ball_tile} has no reachable neighbour, so there is nowhere "
        f"to stand to pick it up."
    )


def _hop(from_map, door_tile: tuple, to_map, what: str) -> Generator:
    """Walk to `door_tile` on `from_map` and warp through it, then ASSERT we landed on `to_map`.

    ⛔ Uses `_pass_through_door`, which makes the warp the NAVIGATION DESTINATION rather than
    hand-stepping onto it — the codebase measured the hand-step as flaky (ML-9, the Petalburg-Woods
    stall: map reads flicker during the warp fade and single-frame presses do not complete a step).
    ‼ AND IT GRADES THE ARRIVAL, not the call. "The door helper returned" is not "we are on the
    other side" — the shape that has bitten this chapter repeatedly.
    """
    from modules.story.early_game import _pass_through_door

    if not _on_map(from_map):
        raise BotModeError(
            f"§Ch24 ice beam: about to hop to {what} via {door_tile}, but we are not on {from_map} "
            f"— we are at {_where()}."
        )
    yield from _pass_through_door(door_tile, from_map.value)
    yield from wait_until_truly_controllable()
    # ⭐ `_pass_through_door` is a no-op when we are not on `from_map`; the guard above already
    # asserted we are, so a silent skip cannot happen here.
    if not _on_map(to_map):
        raise BotModeError(
            f"§Ch24 ice beam: stepped onto {door_tile} to reach {what} and did not arrive — we are "
            f"at {_where()}. ⛔ If this is the Storage Room door (11,4), the most likely cause is "
            f"that the Storage Key is not in the bag and its script refused."
        )


def _goto_warp(from_map, warp_tile: tuple, to_map, what: str) -> Generator:
    """Navigate ONTO a warp tile from anywhere, and assert we landed on `to_map`.

    ⛔ THE TARGET IS THE WARP, NOT A NEIGHBOUR. `navigate_to`'s override
    (`modules/modes/util/walking.py:462-468`) rewrites the destination to the warp's FAR SIDE when
    the last waypoint is a warp — so aiming AT the warp is what makes the arrival check satisfiable.
    Aiming at the tile beside it produces a path that ends on the warp anyway, walks to the
    neighbour, and then re-paths to ZERO waypoints forever (MEASURED: two drives, both wedged).
    """
    from modules.modes.util.global_navigation import navigate_to_anywhere

    yield from navigate_to_anywhere(from_map, warp_tile)
    yield from wait_until_truly_controllable()
    if not _on_map(to_map):
        raise BotModeError(
            f"§Ch24 ice beam: navigated onto the warp {warp_tile} to reach {what} and did not "
            f"arrive — we are at {_where()}."
        )


def _goto(map_enum, tile: tuple, what: str) -> Generator:
    """Cross-map travel via the warp graph, then assert we ARRIVED.

    ⛔ `navigate_to_anywhere` routes through warps and re-plans after each one. It RAISES for a map
    outside the graph — all ten maps on this route were confirmed present before this was written.
    ‼ AND THE ARRIVAL IS ASSERTED, because "the navigator returned" is not "we are there" — the
    leg-11 lesson, and the shape that has bitten this chapter repeatedly.
    """
    from modules.modes.util.global_navigation import navigate_to_anywhere

    yield from navigate_to_anywhere(map_enum, tile)
    yield from wait_until_truly_controllable()
    if not _on_map(map_enum):
        raise BotModeError(
            f"§Ch24 {what}: asked to reach {map_enum} {tile} and ended on {_where()}."
        )


def fetch_ice_beam(report=None, *, teach: bool = False, skip_key: bool = False) -> Generator:
    """`#24-icebeamtrip` — collect the Storage Key, open the Storage Room, take TM13, teach it.

    ⛔ ORDER IS FORCED AND IT IS THE WHOLE LEG: **the key must be held before the door is
    approached**, because the door's script does `checkitem ITEM_STORAGE_KEY`. Doing the halves in
    the other order wastes the whole trip.

    ⭐ GRADED ON THE BAG AND THE MOVESET, NEVER ON THE WALK. `collect_item_ball` already measures the
    bag delta rather than the flag (a full pocket sets NO flag and gives NO item), and this leg then
    asserts Wailord actually KNOWS Ice Beam.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    from modules.map_data import MapRSE
    from modules.story.early_game import collect_item_ball

    ROUTE108 = MapRSE.ROUTE108
    DECK = MapRSE.ABANDONED_SHIP_DECK
    CORR_1F = MapRSE.ABANDONED_SHIP_CORRIDORS_1F
    CAPT = MapRSE.ABANDONED_SHIP_CAPTAINS_OFFICE
    CORR_B1F = MapRSE.ABANDONED_SHIP_CORRIDORS_B1F
    #: ⚠ SINGULAR. `ABANDONED_SHIP_ROOMS_B1F` (plural, map 58) is a DIFFERENT map; the TM is in
    #: map 61. The FLAG is confusingly named `..._ROOMS_B1F_TM_ICE_BEAM`. Do not "correct" either.
    ROOM_B1F = MapRSE.ABANDONED_SHIP_ROOM_B1F

    yield from wait_until_truly_controllable()
    report["start"] = _where()

    # ---- 0. GET ABOARD — ⛔⛔ (29,6) IS A **NORTH ARROW WARP**, NOT A STEP-ON WARP ------------
    # THREE DRIVES DIED HERE, AND EVERY ONE OF MY DIAGNOSES WAS WRONG BEFORE THE RECON LANDED:
    #   guess 1 "warp-as-waypoint"     — wrong
    #   guess 2 "elevation transition" — wrong
    #   guess 3 "aim at the warp"      — wrong (navigate_to still could not make the step)
    # ⭐ THE MEASUREMENT THAT SETTLED IT: hand-stepping WEST across (29,6) walked straight THROUGH to
    # (28,6) **without firing the warp**. A step-on warp cannot do that. ⇒ it is not a step-on warp.
    # ⭐ AND THE DECOMP CONFIRMS THE KIND: the behaviour is `MB_STAIRS_OUTSIDE_ABANDONED_SHIP`, and
    # `MetatileBehavior_IsNorthArrowWarp` returns TRUE for it (`src/metatile_behavior.c:304-311`).
    # ⇒ **STAND ON THE TILE AND HOLD UP.** This project's own warp taxonomy already names this case:
    #     step-on  -> stand BESIDE, press TOWARD
    #     arrow    -> stand **ON**, press ITS OWN direction     <- THIS ONE
    #     door     -> stand beside, face, HOLD
    # ‼ §Ch23 leg 9 learned the identical lesson on `MB_SOUTH_ARROW_WARP` and wrote the rule down:
    # *"WHEN A MECHANIC IS NAMED AS DIFFERENT, DO NOT REUSE THE PREVIOUS LEG'S PATTERN FOR IT."*
    # I reused the door pattern anyway. The rule was right; I did not apply it.
    # ⭐ The surf dismount is AUTOMATIC on landing — `CanStopSurfing` fires because the destination
    # elevation equals `ELEVATION_DEFAULT` (3) (`src/field_player_avatar.c:729-742`), so no explicit
    # dismount is needed. (28,6)/(29,6)/(30,6) are a 3-tile elevation-3 shelf in an elevation-1 sea.
    from modules.story.early_game import _walk_through_warp
    from modules.story.victory_road import _bounded_step

    yield from _budgeted(_goto(ROUTE108, SHIP_APPROACH, "surf to the ship's stairs"),
                         ICEBEAM_BUDGET, "surf to the ship's stairs")
    report["ship_approach"] = _here_tile()

    # (1) ONE EXPLICIT STEP ONTO THE ARROW TILE — never navigate onto it.
    yield from _bounded_step("Up", SHIP_ENTRANCE, map_enum=ROUTE108)
    yield from wait_until_truly_controllable()
    report["on_arrow_tile"] = _here_tile()
    if _here_tile() != SHIP_ENTRANCE:
        raise BotModeError(
            f"§Ch24 ice beam: stepped NORTH from {SHIP_APPROACH} but landed on {_here_tile()} "
            f"instead of the arrow tile {SHIP_ENTRANCE}. ⛔ The warp cannot fire unless we are "
            f"STANDING on it."
        )

    # (2) HOLD Up until the map changes. Generous budget: the surf dismount animation runs first.
    yield from _walk_through_warp("Up", ROUTE108.value, timeout_frames=600)
    yield from wait_until_truly_controllable()
    report["aboard"] = _where()
    if not _on_map(DECK):
        raise BotModeError(
            f"§Ch24 ice beam: held Up on the arrow warp {SHIP_ENTRANCE} and never reached the DECK "
            f"— we are at {_where()}. ⛔ `IsNorthArrowWarp` needs the player STANDING on the tile "
            f"with Up held; a single step does nothing."
        )

    # ==========================================================================================
    # ⛔⛔ THE SHIP IS NOT ONE CONNECTED SPACE. THIS IS THE WHOLE DIFFICULTY OF THE LEG.
    # A decomp collision BFS found — and OUR OWN PLANNER then CONFIRMED LIVE — that:
    #   * the DECK is split in two: from the boarding tile (13,15) only 15 tiles are reachable, and
    #     the Captain's Office door (12,5) is NOT among them (separators (11,10) and (12,11));
    #   * CORRIDORS_1F is split too, by a solid column at x=7;
    #   * ⭐ **CORRIDORS_B1F ROW 5 IS THE ONLY CROSSOVER IN THE ENTIRE SHIP.**
    # ⇒ reaching the key REQUIRES: board (east) -> down to B1F -> cross row 5 -> up the WEST stair ->
    #   deck west half -> Captain's Office. There is no shortcut.
    # ‼ THE LIVE CONFIRMATION, from the drive that had just boarded successfully:
    #     BotModeError: Could not find a path from (13/15 @ DECK) to (12/5 @ DECK)
    #   ⇒ the decomp predicted it from collision data and our planner refused the hop independently.
    # ⚠ Every landing tile below was resolved from the measured warp tables by INDEX, not guessed.
    # ==========================================================================================

    # ---- 1. OUTBOUND: east deck -> B1F -> cross -> west deck -> the Storage Key ------------------
    yield from _hop(DECK, (13, 9), CORR_1F, "the 1F corridor (RIGHT half)")
    yield from _hop(CORR_1F, (16, 2), CORR_B1F, "the B1F corridor")
    # ⭐ THE CROSSOVER, AND IT IS A SINGLE HOP — NOT A WALK FOLLOWED BY A WARP.
    # ‼ MEASURED 2026-09-05: I first wrote this as `_goto(CORR_B1F, (0,2))` to "cross row 5" and THEN
    # a separate `_hop` through (0,2). But **(0,2) IS the warp**, so navigating to it crosses row 5
    # AND fires the warp in one move — and my arrival assertion then failed complaining we had ended
    # on `CORRIDORS_1F (5,2)`, which is EXACTLY where we wanted to be. The run had succeeded and the
    # check called it a failure.
    # ⇒ ⭐ **WHEN THE FAR SIDE OF A WARP IS THE GOAL, THE WALK TO IT IS NOT A SEPARATE STEP.** Aiming
    # at the warp does both, which is the same rule that fixed the boarding two drives earlier.
    yield from _hop(CORR_B1F, (0, 2), CORR_1F, "the 1F corridor (LEFT half), crossing B1F row 5")
    yield from _hop(CORR_1F, (0, 11), DECK, "the deck (WEST half)")
    yield from _hop(DECK, (12, 5), CAPT, "the Captain's Office")

    approach, facing = _ball_approach(CAPT, STORAGE_KEY_BALL["tile"], "storage key")
    report["key_approach"] = {"tile": approach, "facing": facing}
    if skip_key:
        # ⛔ FAULT ARM (`POKEBOT_CH24_FAULT_NOKEY=1`) — prove the refusal fires BEFORE the long walk
        # back to the door. The expensive failure here is a WASTED ROUND TRIP, not a crash.
        held = False
    else:
        held = yield from collect_item_ball(
            CAPT, STORAGE_KEY_BALL["tile"], approach, facing,
            STORAGE_KEY_BALL["flag"], STORAGE_KEY_BALL["item"], label="Storage Key",
        )
    report["have_key"] = False if skip_key else (bool(held) or _bag_has(STORAGE_KEY_BALL["item"]))
    _take(report, "RIB-KEY")
    if not report["have_key"]:
        raise BotModeError(
            "§Ch24 ice beam: the Storage Key is not in the bag. ⛔ Stopping HERE rather than walking "
            "the whole way back to a door that is still a WALL — the tile only becomes a warp once "
            "the key is INSERTED."
        )

    # ---- 2. RETURN: west deck -> left 1F -> B1F, and INSERT the key ------------------------------
    yield from _hop(CAPT, (7, 6), DECK, "the deck (WEST half)")
    yield from _hop(DECK, (8, 9), CORR_1F, "the 1F corridor (LEFT half)")
    yield from _hop(CORR_1F, (5, 2), CORR_B1F, "the B1F corridor")
    report["at_corridor"] = _here_tile()
    # ⚠ Duncan (9,6), sight 4, undefeated, sits on this floor. A battle is EXPECTED and REPORTED,
    # never graded — grading an objdata claim would turn "we learned it was wrong" into "the run
    # failed".

    # ---- 3. ⛔⛔ THE DOOR IS METATILE-GATED. HOLDING THE KEY IS NOT ENOUGH. ----------------------
    # `AbandonedShip_Corridors_B1F_OnLoad` runs on EVERY map load and, while `FLAG_USED_STORAGE_KEY`
    # is unset, does `setmetatile 11, 4, ..._Locked, TRUE`. The locked metatile's behaviour is
    # **MB_NORMAL**, and `MetatileBehavior_IsWarpDoor(MB_NORMAL)` is FALSE ⇒ **the warp CANNOT FIRE**,
    # in any direction, no matter how it is approached. The tile is a WALL.
    # ⇒ the bg_event at (11,4) (`BG_EVENT_PLAYER_FACING_ANY`) must be TRIGGERED WITH A: it does
    # `checkitem` -> `removeitem` -> `setflag FLAG_USED_STORAGE_KEY` -> `UnlockStorageRoom` ->
    # `special DrawWholeMapView`. Only then does the metatile become `MB_ANIMATED_DOOR`.
    # ‼ An earlier version of this leg simply warped at (11,4) and would NEVER have worked.
    yield from _insert_storage_key(report)

    yield from _hop(CORR_B1F, STORAGE_DOOR, ROOM_B1F, "the Storage Room")
    report["in_storage_room"] = _on_map(ROOM_B1F)
    _take(report, "RIB-DOOR")

    # ---- 4. TM13 --------------------------------------------------------------------------------
    approach, facing = _ball_approach(ROOM_B1F, ICE_BEAM_BALL["tile"], "TM13")
    report["tm_approach"] = {"tile": approach, "facing": facing}
    yield from collect_item_ball(
        ROOM_B1F, ICE_BEAM_BALL["tile"], approach, facing,
        ICE_BEAM_BALL["flag"], ICE_BEAM_BALL["item"], label="TM13 Ice Beam",
    )
    report["have_tm13"] = _tm_pocket_has("TM13")
    _take(report, "RIB-TM")
    if not report["have_tm13"]:
        raise BotModeError("§Ch24 ice beam: TM13 is not in the TM/HM pocket after the pickup.")

    # ---- 5. GET BACK OUT BEFORE TEACHING -------------------------------------------------------
    # ⛔⛔ MEASURED 2026-09-05: the whole route succeeded — key, door, TM all collected — and then the
    # teach did NOTHING inside `ROOM_B1F`. `before` and `after` were byte-identical
    # (`['Dive','Surf','Water Spout','Waterfall']`), and `apply_moveset_plan`'s post-condition caught
    # it rather than letting a "success" through. ⭐ **THE TM WAS NOT CONSUMED** (`tm13_in_pocket`
    # was still True), so nothing was lost — that guard exists precisely because a Gen-3 TM is
    # single-use.
    # ‼ EVERY PROVEN TEACH IN THIS PROJECT RAN OUTDOORS ON A NORMAL MAP (`ch24moves`, `ch24fly`).
    # This one ran in a cramped interior room immediately after an item-ball script. Rather than
    # debug the menu inside a 2-warp closet, LEAVE FIRST — which is also a better end state, because
    # Fly needs the outdoors and the caller will want to go somewhere next.
    # ⚠ This is a WORKAROUND, not a diagnosis: whether the blocker is the room, the preceding script,
    # or something else is NOT established. Recorded as such rather than dressed up as a fix.
    yield from _hop(ROOM_B1F, (4, 7), CORR_B1F, "back into the B1F corridor")
    yield from _hop(CORR_B1F, (8, 2), CORR_1F, "the 1F corridor (RIGHT half)")
    yield from _hop(CORR_1F, (8, 11), DECK, "the deck (EAST half)")
    yield from _hop(DECK, (13, 15), ROUTE108, "back out to Route 108")
    report["back_outside"] = _where()
    _take(report, "RIB-OUT")

    # ---- 6. TEACH IT ----------------------------------------------------------------------------
    # ⛔ Wailord's DIVE is the slot to spend: a FIELD move with no battle value, and nothing on the
    # remaining route needs it (Zigzagoon carries Surf, Sceptile Rock Smash + Strength, Swellow Fly).
    # Wailord keeps Surf, Water Spout and Waterfall.
    if teach:
        # ⛔⛔ IT MUST BE **WATER SPOUT** — IT IS THE ONLY SLOT WAILORD IS ALLOWED TO FORGET.
        # Wailord knows Dive (HM08), Surf (HM03), Water Spout, Waterfall (HM07). **Three of the four
        # are HMs and the game refuses to forget an HM** (`Task_HandleInputCantForgetHMsMoves`).
        # ⚠ AND THIS IS A REAL COST, NOT A FREE SWAP — the earlier plan to spend "the dead field-move
        # slot" was simply not available. Water Spout is 150 base power (scaled by current HP) and
        # Wailord's biggest hit; Ice Beam is 95. We trade raw damage for the COVERAGE that decides
        # Drake: Ice is 4x on Flygon (Ground/Dragon, and LEVITATE makes Ice the only
        # super-effective type that reaches it) and 2x on Salamence, Altaria and Shelgon.
        # ⇒ Wailord keeps **Surf** as its water STAB; it loses the burst, not the type.
        plan = (("Wailord", "TM13", "Ice Beam", "Water Spout",
                 "Drake carries ZERO Ice moves and Flygon's LEVITATE makes Ice the only "
                 "super-effective type reachable on it. ⚠ Water Spout is the ONLY forgettable slot "
                 "— Dive/Surf/Waterfall are all HMs and the game refuses to forget those"),)
        yield from apply_moveset_plan(report, plan)
        _take(report, "RIB-TAUGHT")


# ==================================================================================================
# §Ch24 PREP — FLY OFF THE PLATEAU (`#24-dexcatch` prerequisite)
# ==================================================================================================
FLY_READINGS = ("R-FLYABLE", "R-FLOWN", "R-CONTINUE")


#: ⛔ THE MAP YOU ARE STANDING ON MUST ALLOW FLY — the fourth guard, and the one most easily
#: forgotten because the other three pass happily inside a cave and the failure then surfaces
#: in the field-move menu, far from its cause.
#: ⭐ VERIFIED at `src/overworld.c:1366-1375` `Overworld_MapTypeAllowsTeleportAndFly`: the
#: allow-list is FOUR NAMED TYPES, not a notion of "outdoors". `Underground` (caves),
#: `Indoor` (buildings) and `Underwater` are all refused. Encoded verbatim rather than
#: paraphrased, because a first attempt at this check tested `== "Indoor"` and cheerfully
#: reported YES for a cave.
#: ‼ MEASURED 2026-09-17: the finished §Ch24 party sits at VICTORY_ROAD_1F,
#: `map_type=Underground` — so this is not an edge case for this chapter, it is the
#: chapter's own grind tile.
_FLY_ALLOWED_MAP_TYPES = ("Route", "Town", "City", "Ocean Route", "OceanRoute", "Ocean_Route")


def fly_is_legal_from_current_map() -> bool:
    """Does the map under our feet permit Fly? Fails CLOSED — an unreadable type is NO.

    Shares `_FLY_ALLOWED_MAP_TYPES` with `fly_to_destination`'s own guard, so a caller that
    asks this question in advance and the leg that enforces it can never disagree.
    ⇒ this is the cheap PREDICATE form; `fly_to_destination` still raises its own detailed
    `BotModeError` when the guard actually trips, because a leg must explain itself.
    """
    try:
        from modules.map import get_map_data_for_current_position

        return get_map_data_for_current_position().map_type in _FLY_ALLOWED_MAP_TYPES
    except Exception:  # noqa: BLE001 - an unknown is treated as NO, exactly as the leg does
        return False


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
    # ⛔⛔ THE FOURTH GUARD, AND THE ONE THIS FUNCTION SHIPPED WITHOUT: **THE MAP YOU ARE STANDING ON
    # MUST ALLOW FLY.** The three checks above all pass inside a cave, and the failure then happens
    # in the field-move menu — far from the cause, and with nothing naming it.
    # ‼ MEASURED 2026-09-17 (`probe_fly_allowed_here.py`): the finished §Ch24 party
    # (`post_e4ice_FINAL.ss1`) is parked at **VICTORY_ROAD_1F, `map_type=Underground`**, and the
    # chapter's first planned move was "it is ONE Fly to the League door". It is not, from there.
    # ⭐ THE ALLOW-LIST IS NOT "outdoors" — it is four named types, VERIFIED at
    # `src/overworld.c:1366-1375` `Overworld_MapTypeAllowsTeleportAndFly`: ROUTE, TOWN, OCEAN_ROUTE,
    # CITY. Caves (`Underground`), buildings (`Indoor`) and `Underwater` are all refused. My first
    # version of the check tested `== "Indoor"` and reported a cheerful "yes" for a cave, so the
    # list is encoded verbatim here rather than paraphrased as a notion of outdoorsiness.
    # ‼ HOISTED TO MODULE SCOPE 2026-09-23 (`#24-flyladder` 2b/2c) so there is exactly ONE
    # definition of this allow-list. A second copy was about to be written in
    # `training_areas.can_fly_to_anchor`, and a DUPLICATED allow-list that drifts is how a
    # guard silently stops matching the thing it guards. The local name is kept as an alias
    # so this proven leg's own code below is untouched.
    FLY_ALLOWED_MAP_TYPES = _FLY_ALLOWED_MAP_TYPES
    # ‼ IMPORTED LOCALLY, like every other map helper in this module — a helper another
    # function imports locally is NOT available to yours (this file's own recorded trap).
    from modules.map import get_map_data_for_current_position
    try:
        here_type = get_map_data_for_current_position().map_type
    except Exception as error:  # noqa: BLE001 — an unreadable map type must REFUSE, never assume yes
        # ⛔⛔ FIRST STATEMENT, ALWAYS. This handler raises a BRAND-NEW `BotModeError`, and
        # `reraise_if_aborting`'s own docstring names that exact shape as the way an abort's identity
        # is lost: after a whiteout the message below would be **a fabricated diagnosis** — the map
        # type is irrelevant, the player is standing outside a Poké Center. Keyed on the LATCH, not
        # on the exception type, because by here the original object may already be gone.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        raise BotModeError(
            f"§Ch24 fly: could not read the current map type ({type(error).__name__}: {error}), so "
            f"whether Fly is legal here is UNKNOWN. ⛔ Refusing — an unknown is treated as NO."
        )
    report["map_type"] = here_type
    if here_type not in FLY_ALLOWED_MAP_TYPES:
        raise BotModeError(
            f"§Ch24 fly: Fly is REFUSED on `map_type={here_type}` at {_where()}. Gen 3 allows it only "
            f"on {list(FLY_ALLOWED_MAP_TYPES[:4])} (`src/overworld.c` "
            f"`Overworld_MapTypeAllowsTeleportAndFly`). ⇒ walk to an outdoor route/town/city FIRST. "
            f"‼ If this fired from VICTORY_ROAD_1F, that is the §Ch24 party's own grind tile: leave "
            f"Victory Road to EVER_GRANDE_CITY before flying to the League door."
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
        # ⛔⛔ ORDER GUARD — `TRAVEL_PLAN` SILENTLY ASSUMES `MOVESET_PLAN` HAS ALREADY RUN.
        # `TRAVEL_PLAN`'s stated reason for sacrificing **Wing Attack** is that it is *"strictly
        # dominated by the Aerial Ace Swellow already knows"* — and that is true only AFTER
        # `MOVESET_PLAN` has replaced **Peck** with **Facade**. Run the two the other way round and
        # Swellow still has **Peck (35 BP, the worst move on the team)**: the teach then destroys
        # **Wing Attack (60 BP)** and KEEPS Peck — strictly the wrong slot.
        # ‼‼ AND EVERY EXISTING CHECK WOULD HAVE PASSED IT. The species is present, the doomed move
        # is known, the item is in the bag, and the post-teach verification confirms Fly was learned
        # and Wing Attack lost. The leg would report success while having made the party WORSE. ⇒ a
        # silent wrong-slot teach is exactly the failure this function was written to refuse
        # (`KI-88`: two drives burned single-use TMs over the wrong move), so it gets the same
        # treatment — REFUSE, do not guess.
        # ⚠ FOUND BY REVIEW 2026-09-17, NOT BY A FAILURE: the §Ch24 lineage happens to have been
        # built in the right order (`post_ch24ready.ss1`'s Swellow reads `Facade, Fly, Aerial Ace,
        # Quick Attack`), so the defect is LATENT. The next lineage to run prep from scratch pays
        # it, which is why this is a guard and not a comment.
        # ⭐ STATED GENERALLY, NOT AS A SPECIAL CASE FOR SWELLOW: refuse when this Pokémon still has
        # an OUTSTANDING `MOVESET_PLAN` change that the plan being applied right now does not itself
        # carry. `MOVESET_PLAN` therefore never trips on its own entries.
        here_and_now = {(s, r) for s, _i, _l, r, _w in plan}
        outstanding = [
            (o_replace, o_learn)
            for o_species, _o_item, o_learn, o_replace, _o_why in MOVESET_PLAN
            if o_species == species
            and (o_species, o_replace) not in here_and_now
            and o_replace in have
            and o_learn not in have
        ]
        if outstanding:
            missing.append(
                f"{species}: this plan would replace {replace}, but MOVESET_PLAN still has an "
                f"outstanding change on the SAME Pokémon — {outstanding} — so the plans are being "
                f"applied OUT OF ORDER. ⛔ Run MOVESET_PLAN first. (Teaching {learn} over {replace} "
                f"now is defensible only once those are done: e.g. Fly over Wing Attack is correct "
                f"AFTER Peck→Facade, and destroys the better move before it.)"
            )
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


# ==================================================================================================
# PIECE 3 — THE §Ch24 TRAINING LEG (`#24-flyladder`)
# ==================================================================================================

#: USER RULING (2026-09-19): every party member must sit between L65 and L75, and they need not be
#: equal. USER RULING 12 (2026-09-23): train ALL SIX — the party is NOT reduced, and Zigzagoon and
#: Castform are NOT boxed.
#: ⛔ BARE NAME, NO `FLAG_` PREFIX. No row in `modules/data/event_flags/emerald.txt`
#: carries one, and `get_event_flag` returns **False silently** for an unknown name
#: (`memory.py:336-338`) — so the prefixed spelling reads as a hardcoded False forever.
#: Two live bugs of exactly this shape were found in the harness on 2026-09-24.
CH24_ENTERED_FLAG = "ENTERED_ELITE_FOUR"

CH24_LEVEL_FLOOR = 65

#: ⛔ THE PURSE IS A BACKSTOP, NOT A SCHEDULER, AND THAT DISTINCTION IS THE WHOLE DESIGN.
#: An earlier spec had this leg "spend a bounded slice of each run and resume next run". That was
#: incoherent and is retracted: `MAX_FRAMES_PER_RUN` belongs to `StoryEndlessResetMode`, NOT to
#: `StoryMode` (which has no cap), and the story bot NEVER SAVES — `save_the_game()` has zero call
#: sites in `modules/story/` or `plugins/custom_modes/`, so levels live in emulator RAM and do not
#: survive a run boundary. ⇒ in the mode with the budget nothing persists; in the mode where things
#: persist there is no budget and no "next run".
#: ⇒ THEREFORE: train to target in ONE run, and use the purse only to stop a WEDGED grind running
#: forever — which is exactly what `_yield_bounded_by_frames` was built for (KI-28's 19.9M shape).
#: ‼ SIZED ABOVE THE WHOLE JOB, DELIBERATELY. The measured solo cost of both trainees is ~21 h
#: ≈ 4.5M frames (`probe_ladder_economics.py`). A purse BELOW that would abort honest work and look
#: like a defect; a purse far above it still catches a true wedge. 6M is ~1.3× the measured job.
CH24_TRAIN_PURSE_FRAMES = 6_000_000

#: Per-rung purse. One rung is at most a few hundred battles (~800 × 2,368 frames ≈ 1.9M for the
#: Victory Road rung, which carries 73-94 % of the climb). 2.5M gives that headroom while still
#: bounding a single rung that goes wrong.
CH24_RUNG_PURSE_FRAMES = 2_500_000

#: ⛔ A SANITY BOUND ON THE RUNG LOOP ITSELF. Each pass must either raise the trainee's level or
#: stop. This is the "bound every loop" rule: without it a rung that returns immediately without
#: levelling would spin forever inside the purse.
CH24_MAX_RUNGS_PER_TRAINEE = 12


def ch24_trainees_below_floor(floor: int = CH24_LEVEL_FLOOR) -> list:
    """[(pid, species, level)] for every non-egg party member under `floor`, WEAKEST FIRST.

    ⛔⛔ THIS DELIBERATELY DOES NOT USE `victory_road.battler_identities()`, AND THE REASON IS NOT
    STYLE. That helper skips `BENCH_SPECIES = ("Zigzagoon", "Linoone", "Castform")`
    (`victory_road.py:503`) — which is EXACTLY the two mōn USER RULING 12 names as the trainees.
    Reusing it would make this leg report "nobody needs training" on turn one, having trained
    nobody: a check that answers without ever asking.
    ⛔ AND THE OBVIOUS REPAIR IS WORSE. Widening `BENCH_SPECIES` would change §Ch23 leg 4's gate
    (`team_is_ready(TRAIN_TARGET=47)`, `victory_road.py:3393`), which fires BEFORE Wally — so §Ch23
    would start grinding a L19 Zigzagoon to L47. That is KI-28's shape. ⇒ this leg keeps its own
    membership rule and touches nothing shared.

    ‼ IDENTITY, NEVER POSITION. Returns PIDs. Slot indices are meaningless across the rotations this
    leg performs (`_rotate_lead_safely` SWAPS), and this project's rule 3 exists because a
    position-keyed check reads TRUE while the thing it named has moved.
    """
    from modules.pokemon_party import get_party

    out = []
    try:
        for mon in get_party():
            if mon is None or getattr(mon, "is_egg", False):
                continue
            if mon.level < floor:
                out.append((mon.personality_value, mon.species.name, mon.level))
    except Exception as error:  # noqa: BLE001 - an unreadable party is not "nobody needs training"
        # ⛔ A LAUNDERED ABORT IS WORSE THAN A SWALLOWED ONE (`early_game.py:139-159`). If a
        # whiteout latched mid-read, returning [] here would report "nobody needs training" and the
        # leg would exit looking successful.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return []
    return sorted(out, key=lambda t: t[2])


def _ch24_slot_of(pid: int) -> "int | None":
    """Current slot of a PID, or None. ‼ Re-read every time: rotations move mōn."""
    from modules.pokemon_party import get_party

    try:
        for i, mon in enumerate(get_party()):
            if mon is not None and mon.personality_value == pid:
                return i
    except Exception as error:  # noqa: BLE001 - see ch24_trainees_below_floor on laundered aborts
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return None
    return None


def _ch24_level_of(pid: int) -> "int | None":
    from modules.pokemon_party import get_party

    try:
        for mon in get_party():
            if mon is not None and mon.personality_value == pid:
                return mon.level
    except Exception as error:  # noqa: BLE001 - see ch24_trainees_below_floor on laundered aborts
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return None
    return None


def _ch24_step_out_if_fly_illegal(report=None) -> Generator:
    """Leave a Fly-illegal map before a ground is picked. MEASURED DEFECT, not a precaution.

    ⛔⛔ WHAT THE MULTI-RUNG DRIVE FOUND (2026-09-24, `--driver ch24train CH24_TRAIN_FLOOR=40`).
    The climb worked — six rungs, Zigzagoon L19 → L40 — and ended standing on
    `VICTORY_ROAD_1F (15,39)`, which is the LAST rung's own ground. Then the leg turned to the
    second trainee and reported *"no reachable ground Castform out-levels at L36"* and stopped it.
    ‼ That was not a ladder hole. It was a POSITION problem:
      * `map_type=Underground` ⇒ `fly_is_legal_from_current_map()` is **False**, so
        `can_fly_to_anchor` is False and `_training_area_allowed`'s **entire Fly disjunct fails for
        every ground**;
      * and walking ≤ `_MAX_TRAINING_TRAVEL_LEGS` hops from inside the cave reaches almost nothing.
    ⇒ every ground was refused, and the leg correctly-but-uselessly gave up on a mōn it could have
    trained from one map away. The `floor=21` drives never saw this because they never entered
    Victory Road.

    ⭐ WHY IT IS FIXED HERE AND NOT IN `_CAVE_EXITS`. `_exit_training_cave_if_inside()` is the
    obvious home — and it is a no-op inside Victory Road, because `_CAVE_EXITS` knows only Granite
    Cave and Fiery Path. But that table is read by THREE other call sites (`train_team`'s heal path
    and two in `story_mode.py`), and adding a row would change when all of them leave a cave. This
    leg's need is narrower and its own: *be somewhere a ground can be chosen from*. A shared table
    is the wrong place to encode one caller's precondition.

    NO-OPS WHEREVER FLY IS ALREADY LEGAL, which is every route, town and city — so the common path
    pays one map-type read.
    """
    from modules.console import console
    from modules.story import victory_road as VR
    from modules.story.early_game import _yield_bounded_by_frames

    report = report if report is not None else {}
    try:
        if fly_is_legal_from_current_map():
            return
    except Exception as error:  # noqa: BLE001 - an unreadable map type must not strand the leg
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return

    # ⛔ ONLY VICTORY ROAD IS HANDLED, AND THAT IS DELIBERATE. It is the one Fly-illegal map this
    # ladder actually trains on (its band 36-40 makes it the L39+ rung). Inventing exits for caves
    # the leg never visits would be untested code guarding a case that cannot arise.
    try:
        if not VR._on_map(VR.VR1F):
            report.setdefault("fly_illegal_unhandled", []).append(str(VR._where()))
            console.print("[yellow]§Ch24: Fly is illegal here and this is not Victory Road — "
                          "cannot step out, so the next ground pick may fail.[/]")
            return
    except Exception as error:  # noqa: BLE001 - a map-identity read that fails must not strand the
        # climb: we are only deciding WHERE we are, and guessing "not Victory Road" costs one refused
        # ground pick, whereas propagating costs the whole leg. A real abort still re-raises below.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return

    console.print("[cyan]§Ch24: inside Victory Road, where Fly is refused — stepping out to "
                  "Ever Grande so a training ground can be chosen.[/]")
    finished = yield from _yield_bounded_by_frames(
        VR._navigate_riding_out(VR.EG, VR.EG_PC_APRON), 120_000)
    report["stepped_out"] = bool(finished)
    if not finished:
        console.print("[yellow]§Ch24: could not step out of Victory Road within budget — the next "
                      "ground pick will probably refuse.[/]")


def train_one_for_league(pid: int, species: str, report=None, *,
                         floor: int = CH24_LEVEL_FLOOR) -> Generator:
    """Climb ONE mōn to `floor` on the per-trainee Fly ladder, rung by rung.

    ⛔⛔ WHY THIS IS A RUNG LOOP AND NOT ONE `train_team` CALL. `train_team`'s `grass` is a FIXED
    parameter: the loop re-navigates to that same tuple every round (`early_game.py`) and never
    re-picks the ground. ⇒ a single call with `target=floor` would grind the entire climb on the
    ground chosen for the ENTRY level — for a L19 Zigzagoon that is ROUTE117, whose real band is
    (13, 14), at ~100 xp/battle all the way to L65. The economics probe says so in its own words:
    *"THE GRIND IS NOT ONE GROUND — the trainee climbs rungs as it levels, and exp/battle RISES."*
    ⭐ MEASURED, the rungs matter enormously: VICTORY_ROAD_1F (band 36-40) opens at L39 and carries
    **751 of Zigzagoon's 1,026 battles**. Pricing the whole climb at the first rung is not a small
    error.

    ⭐ AND THE GROUND IS CHOSEN BY THE PRODUCTION PICKER, NEVER MODELLED HERE. `best_training_area`
    with `max_wild_max=level + 1` is the out-level rule (`#24-ladderleak`): it returns only grounds
    the trainee OUT-LEVELS, which is what stops `SwapTrainBattleStrategy`'s trigger 1 firing and
    leaking an equal exp share to a L75 finisher.
    """
    # ‼ `console` IS NOT A MODULE-LEVEL NAME HERE. `pokemon_league.py` had ZERO `console` uses
    # before this leg, so there is nothing to inherit — every print below would raise NameError on
    # a path that only runs mid-grind. This module's siblings import it locally per function and so
    # does this leg. (Caught by checking, not by running: `early_game.py` cost a run to this exact
    # shape, and `repro_undefined_names.py` does not scan for it here.)
    from modules.console import console
    from modules.story.early_game import (
        _rotate_lead_safely,
        _yield_bounded_by_frames,
        train_team,
        wait_until_truly_controllable,
    )
    from modules.story.training_areas import best_training_area

    report = report if report is not None else {}
    report.setdefault("readings", set())
    rungs = report.setdefault("rungs", [])

    # ‼ The reachability predicate and the heal map both live in the story-mode plugin. Imported
    # HERE rather than at module scope: `modules/` must not depend on `plugins/` at import time,
    # and this leg is only ever reached from that plugin anyway.
    from plugins.custom_modes.story_mode import _training_area_allowed, _training_area_heal_map

    heal_map = _training_area_heal_map()

    # ⛔ BEFORE THE FIRST GROUND PICK, NOT AFTER IT. `_training_area_allowed`'s Fly disjunct reads
    # the CURRENT map, so standing somewhere Fly is refused makes every ground unreachable and the
    # pick fails for a reason that has nothing to do with the ladder. Measured: the multi-rung
    # drive gave up on Castform while standing inside Victory Road, one map from a working anchor.
    yield from _ch24_step_out_if_fly_illegal(report)

    for _pass in range(CH24_MAX_RUNGS_PER_TRAINEE):
        level = _ch24_level_of(pid)
        if level is None:
            raise BotModeError(
                f"§Ch24 training: {species}#{pid:08X} is no longer in the party. Refusing to "
                f"continue — a leg that cannot find its own trainee must not keep grinding."
            )
        if level >= floor:
            return

        best = best_training_area(level, max_wild_max=level + 1, allow=_training_area_allowed)
        if best is None:
            # ⛔ NOT AN EXCEPTION. "No ground this trainee out-levels is reachable" is a real
            # answer about the world, and the caller decides what to do with a partially-trained
            # party. Raising here would turn a survivable shortfall into a dead run.
            report.setdefault("no_ground", []).append((species, level))
            console.print(f"[yellow]§Ch24 training: no reachable ground {species} out-levels at "
                          f"L{level} — stopping this trainee at L{level}.[/]")
            return
        ground, tile, (lo, hi) = best
        heal_center = heal_map.get(ground)
        if heal_center is None:
            # ⛔ FAIL CLOSED. Without an anchor `_goto_training_area` cannot fly, and the two
            # consumers that do `.get(map, cfg["heal"])` would silently substitute the BOSS's
            # centre — healing somewhere that may be unreachable from the grind tile.
            report.setdefault("no_anchor", []).append((species, ground.name))
            console.print(f"[yellow]§Ch24 training: {ground.name} has no heal anchor — skipping "
                          f"it rather than guessing one.[/]")
            return

        # ⭐ WHERE THIS RUNG ENDS: ask the picker, do not model it. Step the level until it answers
        # with a DIFFERENT ground; that way the rung boundary is the bot's, whatever the table says.
        # ‼ COST MEASURED, BECAUSE THIS LOOP DOES NOT YIELD AND `best_training_area` READS THE
        # EMULATOR (its `allow` predicate runs a region-reach graph search and reads flags):
        # **3.45 ms per call, 162 ms for a full 47-level sweep**, and ~3.9 s across the whole leg
        # at the loop's maximum. That is a brief hitch, not a hang — the no-progress watchdog
        # counts thousands of frames — so it is left simple deliberately.
        # ⇒ DO NOT "optimise" this into a cached table: a cache would be a transcribed copy of the
        # production picker, which is exactly the defect `probe_ladder_economics.py` shipped (four
        # of six rungs wrong) and had to be fixed by calling the picker instead.
        stop = floor
        for probe_level in range(level + 1, floor + 1):
            nxt = best_training_area(probe_level, max_wild_max=probe_level + 1,
                                     allow=_training_area_allowed)
            if nxt is not None and nxt[0] is not ground:
                stop = probe_level
                break
        stop = min(stop, floor)

        # ⛔⛔ ROTATE THE TRAINEE TO SLOT 0 AND VERIFY BY PID. `train_team(slots={i})` with i != 0 is
        # MEASURED BROKEN (`victory_road.py:2053`): it does ONE spin-batch and returns as if
        # finished, because `need` is computed from `party[i]` BY INDEX while `_rotate_lead_safely`
        # performs a SWAP — so on the next iteration `party[i]` is the OLD LEAD. A 900k-frame run
        # produced 8 battles against an estimate of 306.
        slot = _ch24_slot_of(pid)
        if slot is None:
            raise BotModeError(f"§Ch24 training: lost {species}#{pid:08X} before rotating it.")
        if slot != 0:
            yield from _rotate_lead_safely(slot)
            yield from wait_until_truly_controllable()
        if _ch24_slot_of(pid) != 0:
            # ⛔ `_rotate_lead_safely` "gives up gracefully" after 3 attempts — its own docstring
            # calls the rotation an optimisation. A silent give-up here is NOT cosmetic: the leg
            # would grind whatever else is in slot 0, level the wrong mōn, and look successful.
            raise BotModeError(
                f"§Ch24 training: could not put {species}#{pid:08X} in slot 0 (it is in slot "
                f"{_ch24_slot_of(pid)}). Refusing to grind — training the wrong mōn reads as "
                f"success and is the expensive kind of wrong."
            )

        console.print(f"[cyan]§Ch24 training: {species} L{level} → L{stop} at {ground.name} "
                      f"(wilds {lo}-{hi}, heal at {heal_center.name}).[/]")

        # ⛔ heal_on_lead_pp=True IS NOT OPTIONAL (`#24-ppscope`). `_team_is_out_of_pp()` is
        # all-quantified, so on a bench of L75s it is PERMANENTLY False and the PP heal can never
        # fire for the one mōn swinging. Without this the trainee goes dry at ~44 battles, trigger
        # 2's PP half fires on EVERY battle thereafter, a L75 finisher enters, and the exp splits
        # 50/50 — silently, because the bot keeps winning and keeps levelling.
        finished = yield from _yield_bounded_by_frames(
            train_team(stop, slots={0}, grass=(ground, tile), heal_center=heal_center,
                       heal_on_lead_pp=True),
            CH24_RUNG_PURSE_FRAMES,
        )
        after = _ch24_level_of(pid)
        rungs.append({"species": species, "ground": ground.name, "from": level,
                      "to": after, "target": stop, "finished": bool(finished)})

        if not finished:
            console.print(f"[yellow]§Ch24 training: rung purse expired at {ground.name} "
                          f"({species} L{level} → L{after}).[/]")
            return
        # ⛔ ANTI-SPIN: a rung that returns "finished" without raising the level would loop forever
        # under the outer purse. Progress, or stop.
        if after is None or after <= level:
            report.setdefault("no_progress", []).append((species, ground.name, level))
            console.print(f"[yellow]§Ch24 training: {ground.name} produced no level for {species} "
                          f"(L{level} → L{after}) — stopping rather than repeating it.[/]")
            return

    # ⛔ THE RUNG CAP IS AN EXIT TOO, AND IT WAS THE ONLY ONE THAT SAID NOTHING.
    # Every other stop above records a reason and prints. Falling off the `for` after
    # CH24_MAX_RUNGS_PER_TRAINEE passes — each of which DID make progress — used to be silent,
    # indistinguishable from "finished" except via the caller's generic `still_below`.
    # ‼ Today the ladder needs far fewer than 12 rungs because VICTORY_ROAD_1F absorbs the tail of
    # the climb in one. That is an emergent property of the CURRENT `TRAINING_GRASS` table, not
    # something this loop guarantees: promote one of the staged `PENDING_GRASS` bands and a
    # low-starting mōn could need more. A cap that can be hit must say when it is.
    final = _ch24_level_of(pid)
    if final is not None and final < floor:
        report.setdefault("rung_cap_hit", []).append((species, final))
        console.print(f"[yellow]§Ch24 training: {species} used all "
                      f"{CH24_MAX_RUNGS_PER_TRAINEE} rung passes and is still L{final} "
                      f"(floor {floor}) — stopping. This is the CAP, not a completed climb.[/]")


def train_for_league(report=None, *, floor: int = CH24_LEVEL_FLOOR) -> Generator:
    """§Ch24 LEG 1 — bring every party member to `floor` on the per-trainee Fly ladder.

    ⭐ USER RULING 12 (2026-09-23): train ALL SIX. The party is not reduced and the two stragglers
    are not boxed. This leg exists to satisfy that ruling.

    ⛔⛔ ITS FIRST ACT IS TO LATCH §Ch24 AS OWNER OF THE RUN, AND THAT IS NOT BOOKKEEPING.
    `ch23_chapter_done()` is FLAG ∧ POSITION ∧ BAG (`victory_road.py:3315-3322`): it requires
    `_on_map(EVER_GRANDE)` AND that we are on no Victory Road floor. This leg breaks the position
    conjunct within seconds by flying to a training ground, and again later by grinding INSIDE
    Victory Road. Without the latch, the next `_play()` pass finds §Ch23 "unfinished", re-runs
    `do_victory_road_chapter()` — whose leg 4 is the OCEAN CROSSING — and then `_guard` STOPS the
    bot. `victory_road.py:3308-3313` predicted this and called it a forward dependency of §Ch24.

    SELF-SKIPS when nobody is below the floor, so it is safe to re-enter after a derail: it re-reads
    the party each pass and does only what is left.
    """
    from modules.console import console      # ‼ not module-level here — see train_one_for_league
    from modules.context import context
    from modules.story.early_game import _yield_bounded_by_frames, wait_until_truly_controllable

    report = report if report is not None else {}
    report.setdefault("readings", set())

    yield from wait_until_truly_controllable()

    # ⛔⛔ LATCH BEFORE THE SELF-SKIP, NOT AFTER IT — AND THIS ORDER WAS WRONG UNTIL 2026-09-24.
    # The latch used to sit BELOW the `if not trainees: return` below, so a run whose party was
    # ALREADY at or above the floor took the self-skip and **never latched at all**. The comment
    # right here said "latching afterwards would leave a window in which a derail re-enters §Ch23"
    # — and the code did exactly that on its own skip path.
    # ‼ BENIGN ONLY WHILE NOTHING RUNS AFTER THIS LEG, which is true today and stops being true the
    # instant the League-entry leg is wired: `_ch23_settled()` is `_ch24_owns_run or
    # ch23_chapter_done()`, and `ch23_chapter_done()` requires `_on_map(EVER_GRANDE)` — FALSE in the
    # League lobby and FALSE in HALL5. An unlatched resumed run would therefore re-enter §Ch23,
    # burn its three attempts and raise. MEASURED live by `Ch24LobbyMode`, not predicted.
    # ⇒ the latch is about OWNING THE RUN, which is true whether or not there is training left to do.
    mode = getattr(context, "bot_mode_instance", None)
    marker = getattr(mode, "mark_ch24_owns_run", None)
    if callable(marker):
        marker()
        report["latched"] = True
    else:
        # ⚠ SAY SO RATHER THAN ASSUME. A harness driver may run this leg without the StoryMode
        # instance; that is legitimate (nothing re-enters §Ch23 there) but it must be visible,
        # because in PRODUCTION a missing latch means the ocean crossing every run.
        report["latched"] = False
        console.print("[yellow]§Ch24: no StoryMode instance to latch — §Ch23 re-entry is NOT "
                      "suppressed. Expected under a standalone driver; a defect in production.[/]")

    trainees = ch24_trainees_below_floor(floor)
    report["trainees"] = [(f"{sp}#{pid:08X}", lv) for pid, sp, lv in trainees]
    if not trainees:
        console.print(f"[dim]§Ch24: every party member is already at or above L{floor} — "
                      f"skipping the training leg.[/]")
        report["skipped"] = True
        return

    console.print(f"[bold cyan]§Ch24: training {len(trainees)} mōn to L{floor} — "
                  f"{', '.join(f'{sp} L{lv}' for _p, sp, lv in trainees)}[/]")

    # ⛔ ONE OUTER PURSE ACROSS THE WHOLE LEG, on top of the per-rung one. The per-rung purse bounds
    # a single ground; this bounds the leg. Both are BACKSTOPS against a wedge, not schedulers —
    # the leg is meant to FINISH, and an expired purse is a defect to investigate, not a plan.
    def _all_trainees():
        for pid, species, _level in trainees:
            yield from train_one_for_league(pid, species, report, floor=floor)

    visited_all = yield from _yield_bounded_by_frames(_all_trainees(), CH24_TRAIN_PURSE_FRAMES)
    # ⛔⛔ THIS FIELD WAS CALLED `purse_finished` AND THAT NAME WAS A LIE — "a candidate is not an
    # attempt", in its exact classic shape. The outer purse returns True when `_all_trainees()`
    # raises StopIteration, i.e. when every trainee was *visited*. A trainee whose INNER rung purse
    # expired simply `return`s — it does not abort the outer generator — so "True" could coexist
    # with a mōn left far below the floor. A reader seeing `purse_finished=True` would reasonably
    # conclude the job was done.
    # ⇒ the flag now says only what it knows (every trainee got a turn), and the ACTUAL outcome is
    # computed from the party itself, which is the only thing that can answer "is the job done".
    report["all_trainees_visited"] = bool(visited_all)

    # ⛔ END SOMEWHERE THE NEXT LEG CAN START FROM. The last rung of the real ladder is
    # VICTORY_ROAD_1F, so a finished climb leaves the bot INSIDE a cave where Fly is refused and
    # `calculate_path` cannot even express the way out (the exit is a door warp). §Ch24's next leg
    # is the GAUNTLET, reached from Ever Grande.
    # ‼ MEASURED: the multi-rung drive ended at `VICTORY_ROAD_1F (15,39)` with
    # `fly_legal_at_end=False` and no computable path to the League anchor — a finished job that
    # left the bot parked in the one place the chapter cannot continue from.
    # ⇒ this is a POSTCONDITION of the leg, not a courtesy: "trained the party" and "left it able
    # to proceed" are different claims, and only the second one is useful to the caller.
    yield from _ch24_step_out_if_fly_illegal(report)

    left = ch24_trainees_below_floor(floor)
    report["floor_reached"] = not left
    report["still_below"] = [(f"{sp}#{pid:08X}", lv) for pid, sp, lv in left]
    if left:
        console.print(f"[yellow]§Ch24 training ended with {len(left)} mōn still below L{floor}: "
                      f"{', '.join(f'{sp} L{lv}' for _p, sp, lv in left)}[/]")
    else:
        console.print(f"[bold green]§Ch24: every party member is now at or above L{floor}.[/]")


#: The readings this leg publishes. ⛔ THE DRIVER IMPORTS THIS — it must never keep a private copy.
#: A renamed label with a private copy makes a PERFECT run report `missing=[…]`, and the obvious
#: repair is then to delete a required reading. Precedent: `LEG23_READINGS`, `ICEBEAM_READINGS`.
LEAGUE_ENTRY_READINGS = (
    "E1-LATCHED",     # the run is OWNED before a single button is pressed
    "E1-READY",       # the party satisfies the floor, decided OUTSIDE where it can still be fixed
    "E1-INSIDE",      # we are standing in the League lobby
    "E1-GUARDS",      # the guards have VACATED (9,2)/(10,2) — asserted, not assumed
    "E1-AT-DOOR",     # we stand on (9,3), facing the open door, WITHOUT having stepped through
)

#: Where the guard is talked to. One tile south of the left door tile, facing north.
LEAGUE_GUARD_TALK_TILE = (9, 3)

#: Frames to let the guard's conversation TAKE HOLD after the A press, before riding it out.
#: ⛔ LOAD-BEARING — see `prepare_and_open_the_league`. `wait_for_no_script_to_run` presses B
#: immediately, which races the script's startup if called straight after the A. 30 frames was
#: the value that worked on the first passing drive; it is a floor, not a tuned optimum.
_GUARD_SCRIPT_SETTLE_FRAMES = 30



def _ride_out_the_guard_script() -> Generator:
    """Wait out the League guard's conversation, then let the avatar settle.

    Split out so the whole sequence sits inside ONE frame bound at the call site — the helpers it
    uses (`tasks_scripts.py`) contain uncapped waits, including a bare `while True:`.
    """
    from modules.modes.util.tasks_scripts import wait_for_no_script_to_run
    from modules.modes.util.walking import wait_for_player_avatar_to_be_standing_still

    yield from wait_for_no_script_to_run("B")
    yield from wait_for_player_avatar_to_be_standing_still("B")


def prepare_and_open_the_league(report=None, *, floor: int = CH24_LEVEL_FLOOR) -> Generator:
    """§Ch24 LEG 1 — make the party gauntlet-ready, get inside, and OPEN THE DOOR. Then STOP.

    ⛔⛔ THIS LEG DELIBERATELY DOES NOT STEP ONTO `(9,1)`, AND THAT IS THE WHOLE DESIGN.
    `(9,1)`/`(10,1)` are `MB_NON_ANIMATED_DOOR` and **step-on**: arriving there IS the warp, and it
    is the point of no return — every backward warp in the interior sits on `MB_NORMAL`, which the
    warp code rejects (measured: `evidence/2026-09-24-league-return-warps.stdout.txt`).
    ‼ An earlier draft of this leg DID step through, and a design review killed it: the bot would
    have landed in `HALL5`, whose only FIRING warp is forward into Sidney's room, and the very next
    statement in `story_mode.py` sets `_reached_end_of_content = True` and hands to manual. ⇒
    **`StoryEndlessResetMode` would have scored an in-gauntlet strand as a GENUINE COMPLETION**, and
    `HALL5` would have been written into `current_state.ss1` — which the real bot resumes from.
    ⇒ **the commitment step belongs to the GAUNTLET leg, which does not exist yet.** This leg ends
    somewhere safe: the lobby has a free nurse and a reachable exit (measured, 14 waypoints).

    ⭐⭐ WHY READINESS IS DECIDED **OUTSIDE**, BEFORE THE BUILDING. All three remedies are
    non-functional from the lobby, verified one by one:
      * `heal_at_league` raises on an already-healthy party (its own anti-vacuity guard) **and** on
        `not _on_map(EG)` — from the lobby it raises either way, and its postcondition is outside;
      * `stock_for_the_elite_four`'s money guard fires before any map check (`LEAGUE_MIN_MONEY`
        54,300) and the measured post-basket wallet is ₽1,741 — a second call raises;
      * `train_for_league` needs **Fly**, and the lobby is `MAP_TYPE_INDOOR`.
    ⇒ a readiness gate that cannot remedy is just a halt. **Decide it where it can still be fixed.**

    ‼‼ AND THIS LEG DELIBERATELY DOES WHAT §Ch23 FORBIDS. `victory_road.py`'s leg 10 says, in
    capitals, *"Never press A near the guards at (9,2)/(10,2): it sets `FLAG_ENTERED_ELITE_FOUR`
    permanently"*. That prohibition is **correct for §Ch23**, whose job is to heal and shop and get
    out. Opening that door is **this chapter's objective**. ⇒ do not "fix" this leg to respect that
    rule, and do not relax the §Ch23 rule to match this one.

    IDEMPOTENT: re-entering after a derail re-reads the world and does only what is left.
    """
    from modules.console import console
    from modules.context import context
    from modules.map import get_map_objects
    from modules.memory import _event_flags, get_event_flag
    from modules.modes.util.walking import ensure_facing_direction
    from modules.modes.util.sleep import wait_for_n_frames
    from modules.story import victory_road as VR
    from modules.story.early_game import (
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

    # ⛔ VACUITY-GUARD THE FLAG NAME BEFORE IT IS EVER READ. `get_event_flag` returns **False
    # silently** for a name it does not know (`memory.py:336-338`), and NO row in
    # `event_flags/emerald.txt` carries a `FLAG_` prefix. An unguarded misspelling here would make
    # every check below a hardcoded False — the leg would talk to guards that had already moved,
    # forever. (Two live bugs of exactly this shape were found in the harness on 2026-09-24.)
    if CH24_ENTERED_FLAG not in _event_flags:
        raise BotModeError(
            f"§Ch24 leg 1: flag name {CH24_ENTERED_FLAG!r} is NOT in the event-flag table "
            f"({len(_event_flags)} entries). `get_event_flag` returns False SILENTLY for an unknown "
            f"name, so every reading in this leg would be a hardcoded False."
        )

    yield from wait_until_truly_controllable()

    # ---- LATCH FIRST, BEFORE A SINGLE BUTTON ---------------------------------------------------
    # ⛔ `_ch23_settled()` is `_ch24_owns_run or ch23_chapter_done()`, and `ch23_chapter_done()`
    # requires `_on_map(EVER_GRANDE)` — FALSE the moment we are inside the building. An unlatched
    # run that resumes in the lobby re-enters §Ch23, burns its three attempts and raises. Measured
    # live by `Ch24LobbyMode`, not predicted.
    mode = getattr(context, "bot_mode_instance", None)
    marker = getattr(mode, "mark_ch24_owns_run", None)
    if callable(marker):
        marker()
        report["latched"] = True
        _take(report, "E1-LATCHED")
    else:
        report["latched"] = False
        console.print("[yellow]§Ch24 leg 1: no StoryMode instance to latch — §Ch23 re-entry is NOT "
                      "suppressed. Expected under a standalone driver; a defect in production.[/]")

    # ---- READINESS, DECIDED OUTSIDE ------------------------------------------------------------
    # ⛔ THE FLOOR IS A PARAMETER, NOT A CONSTANT — same shape as `train_for_league`.
    # It lets a drive exercise the TRAVEL + GUARD half without first paying for a ~20 h
    # grind, and the driver's ACCEPTANCE line reports which floor it ran at so the scope
    # can never be over-read. Production callers pass nothing and get CH24_LEVEL_FLOOR.
    below = ch24_trainees_below_floor(floor)
    report["below_floor_before"] = [(f"{sp}#{pid:08X}", lv) for pid, sp, lv in below]
    if below:
        if not VR._on_map(VR.EG):
            # ⚠ REPORT, DO NOT RAISE. Being unable to train from here is a fact about POSITION, and
            # the leg can still do its other work; the gauntlet leg is what must refuse to start.
            report["train_skipped_offmap"] = str(VR._where())
            console.print("[yellow]§Ch24 leg 1: party is below the floor and we are not on EVER "
                          "GRANDE, so training cannot run here. Continuing WITHOUT training — the "
                          "gauntlet leg must refuse to start.[/]")
        else:
            console.print(f"[cyan]§Ch24 leg 1: {len(below)} mōn below L{floor} — "
                          f"training BEFORE entering, while it is still possible.[/]")
            train_report = {}
            yield from train_for_league(train_report, floor=floor)
            report["train"] = train_report
    left = ch24_trainees_below_floor(floor)
    report["below_floor_after"] = [(f"{sp}#{pid:08X}", lv) for pid, sp, lv in left]
    if not left:
        _take(report, "E1-READY")

    # ---- GET INSIDE ----------------------------------------------------------------------------
    if not VR._on_map(VR.LEAGUE_1F):
        if not VR._on_map(VR.EG):
            raise BotModeError(
                f"§Ch24 leg 1: must start on EVER_GRANDE_CITY or in the League lobby, but we are at "
                f"{VR._where()}. This leg does not navigate across the region."
            )
        yield from _yield_bounded_by_frames(
            VR._navigate_riding_out(VR.EG, VR.LEAGUE_DOOR_APRON), 200_000)
        yield from wait_until_truly_controllable()
        # ⛔ `from_map` IS THE MAP WE ARE LEAVING, NOT THE DESTINATION. The helper loops
        # `while _map_group_number() == from_map`, so passing the DESTINATION makes the condition
        # false on the first test and it returns having pressed NOTHING — silently. Caught on this
        # leg's first drive by the arrival assertion below, which is exactly what that assertion is
        # for: a helper that no-ops is indistinguishable from one that worked, until something
        # re-reads the world.
        finished = yield from _yield_bounded_by_frames(
            VR._walk_through_warp("Up", VR.EG.value), 60_000)
        report["walked_in"] = bool(finished)
        yield from wait_until_truly_controllable()
    if not VR._on_map(VR.LEAGUE_1F):
        raise BotModeError(
            f"§Ch24 leg 1: tried to enter the League but we are at {VR._where()}, not the lobby.")
    report["inside_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "E1-INSIDE")

    # ---- CLEAR THE GUARDS ----------------------------------------------------------------------
    def _guard_tiles_occupied() -> list:
        """Guard tiles occupied by a NON-PLAYER object, read LIVE.

        ‼ `get_map_objects()` returns the LIVE `ObjectEvent` (`map.py:1107`), whose coordinate
        attribute is **`current_coords`** — NOT the static `ObjectEventTemplate`'s
        `local_coordinates` (`map.py:1588`). Reading the template's API off the live object raises
        `AttributeError` for every row, which would read as "no guards" unless it is caught.
        ‼ And the list INCLUDES THE PLAYER, so it must be filtered.

        ⚠ CAMERA-RANGE LIMIT, STATED RATHER THAN GUARDED. `get_map_objects()` is a window, not a
        census, so "no object on that tile" could in principle mean "out of range". This is safe
        HERE and nowhere else: the caller stands on (9,3), one tile from both guard tiles, so they
        cannot be outside the window. ⛔ Do NOT reuse this helper from across the lobby — the
        sibling `probe_league_guards.py` reports UNKNOWN in that case, and it has to.
        """
        out = []
        for ob in get_map_objects():
            try:
                if "isPlayer" in ob.flags:
                    continue
                tile = tuple(ob.current_coords)
            except Exception as error:  # noqa: BLE001 - one unreadable object must not be read as
                # "the tile is clear"; treat it as STILL OCCUPIED and say so. Failing closed is the
                # only safe direction: a phantom clearance sends the bot at a door that is shut.
                reraise_if_aborting(error)
                out.append(("<unreadable>", type(error).__name__))
                continue
            if tile in VR.LEAGUE_GUARD_TILES:
                out.append(tile)
        return out

    already = get_event_flag(CH24_ENTERED_FLAG)
    report["flag_before"] = bool(already)

    # ⛔ FAULT ARM, READ IN PRODUCTION SO IT IS DRIVER-PROOF: `POKEBOT_CH24_FAULT_SKIPTALK=1` skips
    # the guard conversation entirely. It exists to prove the ASSERTION below is LIVE — with the
    # talk skipped, `E1-GUARDS` must FAIL. Without an arm like this, a green assertion is
    # indistinguishable from an assertion that can never fail, and this tree has shipped exactly
    # that before. Registered in `29-DISABLED-FEATURES-REGISTRY.md` (lint_docs R6).
    import os as _os

    _skip_talk = _os.environ.get("POKEBOT_CH24_FAULT_SKIPTALK") == "1"
    if _skip_talk:
        report["fault_skiptalk"] = True
        console.print("[magenta]§Ch24 leg 1: FAULT ARM SKIPTALK — not talking to the guards. The "
                      "assertion below MUST fail; if it passes, the assertion is decoration.[/]")

    if not already and not _skip_talk:
        yield from _yield_bounded_by_frames(
            VR._navigate_riding_out(VR.LEAGUE_1F, LEAGUE_GUARD_TALK_TILE), 60_000)
        yield from wait_until_truly_controllable()
        yield from ensure_facing_direction("Up")
        # ⛔⛔ ONE A, THEN RIDE THE SCRIPT OUT. DO NOT MASH.
        # ‼ MEASURED ON THIS LEG'S FIRST DRIVE, and the lesson was already written down three weeks
        # earlier at `victory_road.py:2986-2996`: a duty-cycled A-press loop reached (9,3), faced
        # north correctly, and **opened nothing** — `ENTERED_ELITE_FOUR` stayed False. The guard's
        # script is `message` / `waitmessage` / `delay 120` / two `applymovement`s / `playfanfare`
        # and only THEN `setflag`; mashing A drives msgboxes open and shut faster than that can run.
        # ⇒ *"when a proven helper exists for an interaction, copy its SHAPE, not just its intent —
        # the shape is where the timing knowledge lives."* This is the nurse sequence from
        # `victory_road.py:2995-3000`, minus its yes/no step (the guard asks no question).
        # ⛔ AND IT IS BOUNDED: `wait_for_no_script_to_run` lives in `tasks_scripts.py`, which
        # carries uncapped wait loops including a bare `while True:`.
        # ⚠ DIAGNOSTICS AT THE MOMENT OF THE PRESS. Two drives failed here with the flag still
        # False, and guessing at causes is how this project has burned whole days. Record what is
        # actually true when A is pressed, so the next failure names its own reason.
        from modules.player import get_player_avatar as _gpa
        from modules.tasks import get_global_script_context as _gsc

        try:
            _av = _gpa()
            report["talk_tile"] = tuple(_av.local_coordinates)
            report["talk_facing"] = str(_av.facing_direction)
        except Exception as error:  # noqa: BLE001 - a diagnostic must not break the leg
            reraise_if_aborting(error)
            report["talk_facing"] = f"<unreadable {type(error).__name__}>"
        report["guards_at_press"] = [tuple(o.current_coords) for o in get_map_objects()
                                     if "isPlayer" not in o.flags]

        yield
        context.emulator.press_button("A")

        # ⛔⛔ LET THE SCRIPT START BEFORE RIDING IT OUT. THIS WAIT IS LOAD-BEARING, NOT A COURTESY.
        # ‼ MEASURED, and it cost two failed drives to find: `wait_for_no_script_to_run("B")` begins
        # PRESSING B immediately. Called straight after the A, it races the guard script's own
        # startup — the conversation never takes hold and `ENTERED_ELITE_FOUR` stays False, while
        # every other reading (tile, facing, guards present) looks perfect.
        # ⭐ It was found by INSTRUMENTING rather than guessing: two rounds of "fix the A-press"
        # changed nothing, and the diagnostics then showed `script_active_after_A=True` and
        # `talk_completed=True` — i.e. the press and the ride were both already fine. The settle
        # below is what was missing, and it first appeared only as a side effect of adding those
        # diagnostics. ⇒ it is named and explained HERE so that deleting the diagnostics cannot
        # silently delete the fix.
        yield from wait_for_n_frames(_GUARD_SCRIPT_SETTLE_FRAMES)

        try:
            report["script_active_after_A"] = bool(_gsc().is_active)
        except Exception as error:  # noqa: BLE001 - same reasoning
            reraise_if_aborting(error)
            report["script_active_after_A"] = f"<unreadable {type(error).__name__}>"

        finished_talk = yield from _yield_bounded_by_frames(
            _ride_out_the_guard_script(), 60_000)
        report["talk_completed"] = bool(finished_talk)
        yield from wait_until_truly_controllable()

    # ---- ASSERT IT WORKED. THIS IS THE STEP NOTHING IN THE TREE DID BEFORE. ---------------------
    # ⛔ `ch24probe` checked only "are we on HALL5" — the CONSEQUENCE two steps later, which cannot
    # distinguish "the guards moved" from "we got lucky". Assert the ACTION: the flag AND the tiles.
    flag_now = bool(get_event_flag(CH24_ENTERED_FLAG))
    still = _guard_tiles_occupied()
    report["flag_after"] = flag_now
    report["guard_tiles_occupied"] = still
    if not flag_now:
        raise BotModeError(
            f"§Ch24 leg 1: talked to the guard but {CH24_ENTERED_FLAG} is still False at "
            f"{VR._where()}{VR._here_tile()}. The door is shut; do NOT walk at it.")
    if still:
        raise BotModeError(
            f"§Ch24 leg 1: {CH24_ENTERED_FLAG} is True but {still} is STILL OCCUPIED. The flag and "
            f"the objects disagree — refusing to treat the way as clear.")
    _take(report, "E1-GUARDS")

    # ---- END AT THE DOOR, NOT THROUGH IT -------------------------------------------------------
    if VR._here_tile() != LEAGUE_GUARD_TALK_TILE:
        yield from _yield_bounded_by_frames(
            VR._navigate_riding_out(VR.LEAGUE_1F, LEAGUE_GUARD_TALK_TILE), 40_000)
        yield from wait_until_truly_controllable()
    yield from ensure_facing_direction("Up")
    report["end_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "E1-AT-DOOR")
    console.print("[bold green]§Ch24 leg 1: the League door is OPEN and the bot stands at "
                  f"{VR._here_tile()} facing it. ⛔ STOPPING HERE — stepping onto (9,1) is the point "
                  f"of no return and belongs to the gauntlet leg.[/]")


#: The readings `fight_one_room` publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
ROOM_READINGS = (
    "R1-PREMISE",    # we start in room N, post-victory, with the NEXT room's flag still unset
    "R1-DISMISSED",  # the parked victory msgbox is cleared and we are controllable
    "R1-HEALED",     # the bag heal ran (or its failure was RECORDED — it never raises)
    "R1-INHALL",     # we reached hall N
    "R1-INROOM",     # we reached room N+1
    "R1-ENGAGED",    # a battle actually started
    "R1-WON",        # the NEXT trainer's defeat flag is now set
    "R1-CONTINUE",   # ⛔ and the exit door is OPEN in the LIVE grid — a win is not a continuable state
)

def _ch24room_fault() -> str:
    """The active `fight_one_room` fault arm, or `""`.

    ⛔ READ IN **PRODUCTION**, NOT IN THE DRIVER — that is what makes an arm driver-proof. A guard
    whose arm lives in the harness only proves the harness; this project requires the arm to
    exercise the same code path the real bot runs. Arms are registered in
    `29-DISABLED-FEATURES-REGISTRY.md` (enforced by `lint_docs.py` R6).
    """
    import os

    return os.environ.get("POKEBOT_CH24ROOM_FAULT", "").strip().lower()


#: Room-side exit door, identical in all four Elite Four rooms.
ROOM_EXIT_DOOR = (6, 2)
#: Hall-side far door, identical in all five halls.
HALL_FAR_DOOR = (5, 2)


def fight_one_room(report=None, *, from_room, hall, to_room, victory_flag,
                   dismiss_budget: int = 3_000, walk_frames: int = 40_000,
                   navigate_frames: int = 20_000, engage_frames: int = 4_000,
                   battle_frames: int = 120_000) -> Generator:
    """§Ch24 — ONE ROOM OF THE GAUNTLET: leave room N, cross hall N, beat trainer N+1.

    ⭐ THE REPEATING UNIT IS **ROOM-TO-ROOM, NOT HALL-TO-HALL.** It starts standing in `from_room`
    immediately after beating that trainer (the victory msgbox still parked) and ends standing in
    `to_room` immediately after beating the next one. The hall is crossed in the middle. This is the
    shape the three working harness drivers already use, and copying a different decomposition would
    mean re-deriving their timing knowledge.

    ⛔⛔ **SPECIES-AGNOSTIC BY REQUIREMENT, NOT BY ACCIDENT.** Nothing here names a Pokémon, a move
    or a type. The user's stated goal is that **the team lineup should vary between runs**, so a room
    loop that knew about Wailord's Ice Beam or Mightyena's Crunch would foreclose it. Type coverage
    is a READINESS question for a different predicate; this function only walks, engages, fights
    through whatever strategy is installed, and asserts the outcome.

    ⛔ **THE ZONE IS SEALED BEHIND US.** Every backward warp in the interior sits on `MB_NORMAL`,
    which the warp code rejects (measured). ⇒ **a failure in here cannot be answered by retreating**,
    and that shapes two decisions below: the heal NEVER raises, and no step ever routes backward.

    ‼ **`VAR_ELITE_4_STATE` IS RECORDED, NEVER DISPATCHED ON.** It counts rooms **ENTERED**, not
    trainers beaten, and each room's `OnFrame` fires at *exactly* the predecessor value — so it is a
    depth signal that LAGS, and branching on it would be branching on a stale number.
    """
    from modules.map import get_map_objects
    from modules.memory import get_event_flag, get_event_var
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story import victory_road as VR
    from modules.battle_state import battle_is_active
    from modules.player import player_avatar_is_controllable
    from modules.story.early_game import (
        _check_abort,
        _pass_through_door,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

    # ⛔ VACUITY-GUARD THE FLAG NAME. `get_event_flag` returns **False silently** for a name it does
    # not know (`memory.py:336-338`), so a typo would make `R1-WON` unreachable AND make the premise
    # look satisfied — the worst combination. Checked before anything moves.
    from modules.memory import _event_flags

    if victory_flag not in _event_flags:
        raise BotModeError(
            f"§Ch24 room leg: victory flag {victory_flag!r} is NOT in the event-flag table "
            f"({len(_event_flags)} entries). `get_event_flag` returns False SILENTLY for an unknown "
            f"name, so the premise below would pass and the win could never be observed."
        )

    # ---- STEP 0: PREMISE, WITH BOTH HALVES ------------------------------------------------------
    # ‼ TWO CONJUNCTS, NOT ONE. A map check alone passes on a run that has ALREADY beaten the next
    # trainer, which would make this leg report a win it did not cause. The flag half is what makes
    # the reading non-vacuous — point this leg at its own OUTPUT state and it must refuse.
    if not VR._on_map(from_room):
        raise BotModeError(
            f"§Ch24 room leg: must start in {from_room.name} (post-victory) but we are at "
            f"{VR._where()}. This leg does not navigate into the gauntlet.")
    already = bool(get_event_flag(victory_flag))
    report["start_flag"] = already
    if already:
        raise BotModeError(
            f"§Ch24 room leg: PREMISE FAILED — {victory_flag} is ALREADY set, so the next trainer is "
            f"beaten and this leg would report a win it did not cause.")
    report["start_at"] = (str(VR._where()), VR._here_tile())
    # RECORDED, NOT DISPATCHED ON — see the docstring.
    try:
        report["start_elite4_state"] = get_event_var("ELITE_4_STATE")
    except Exception as error:  # noqa: BLE001 - a telemetry read must never decide the run
        reraise_if_aborting(error)
        report["start_elite4_state"] = "<unreadable>"
    _take(report, "R1-PREMISE")

    # ---- STEP 1: DISMISS THE PARKED VICTORY MSGBOX ----------------------------------------------
    # ⛔ **B, NOT A.** The defeat speech is a plain msgbox chain; pressing A can re-open the trainer
    # interaction instead of closing it. And on a DUTY CYCLE, because holding a button every frame
    # never produces the JOY_NEW edge a Gen-3 `waitbuttonpress` needs.
    def _controllable_quiet() -> bool:
        """`player_avatar_is_controllable()` that cannot let a transition-time raise escape.

        ⛔ A LOOP-EXIT HINT, NEVER A GRADE. It is documented as FLICKERING through a transition
        (`early_game.py`), so a single True reading is not a settle — `wait_until_truly_controllable`
        immediately below is. The three proven drivers poll through exactly this wrapper
        (`story_harness.py` `_player_controllable_quiet`); calling it RAW here would let a mid-
        transition raise out of a loop whose whole job is to wait for that transition to end.
        """
        try:
            return bool(player_avatar_is_controllable())
        except Exception as error:  # noqa: BLE001 - see above; a raise here IS the "not yet" answer
            reraise_if_aborting(error)
            return False

    dismissed = False
    for frame in range(dismiss_budget):
        _check_abort()
        if get_game_state() is GameState.OVERWORLD and _controllable_quiet():
            dismissed = True
            break
        if frame % 6 == 0:
            context.emulator.press_button("B")
        yield
    report["dismissed"] = dismissed
    if not dismissed:
        raise BotModeError(
            f"§Ch24 room leg: the victory msgbox did not clear within {dismiss_budget} frames at "
            f"{VR._where()}. Walking while a script holds input would press into a locked overworld.")
    # ⛔⛔ THE SETTLE, AND IT IS LOAD-BEARING — NOT A COURTESY. The loop above exits on a SINGLE
    # controllable reading, which FLICKERS true/false through a transition; the very next
    # `navigate_to()` can still throw. Step 2 opens the BAG MENU on the strength of that reading, so
    # without this wait the heal can be driven while the avatar is still mid-transition.
    # ‼ ALL THREE PROVEN DRIVERS CALL THIS HERE (`story_harness.py:17750`, `:18227`, `:18684`) and
    # my first version of this leg DROPPED IT. A removed wait is this project's most expensive
    # recurring bug shape; it was caught by a port-fidelity review, not by a drive.
    yield from wait_until_truly_controllable()
    _take(report, "R1-DISMISSED")

    # ---- STEP 2: HEAL FROM THE BAG --------------------------------------------------------------
    # ⛔⛔ **THIS NEVER RAISES.** The zone is sealed behind us: refusing here strands the bot in a
    # room it cannot leave, which is strictly worse than entering the next fight under-healed. The
    # error is RECORDED so the grade can see it, and the leg continues.
    heal_report: dict = {}
    # ⭐⭐ FAULT ARM `healnoop` — THE ONLY ARM THAT ACTUALLY TESTS THE `heal_ready` CONJUNCT.
    # ⛔ A "skip the heal" arm does NOT test it: `R1-HEALED` would never be taken and the run fails
    # on `missing=['R1-HEALED']` with or without the conjunct. The case the conjunct exists for is
    # **"the heal RAN and left the party unready"** — `R1-HEALED` taken, `missing` EMPTY, and only
    # `heal_ready` able to fail the run.
    # ⭐ AND IT FAKES NOTHING: it calls the REAL `heal_party_from_bag` with the REAL bag and
    # `max_actions=0`. `plan_healing` breaks at `len(plan) >= max_actions`, so the plan is EMPTY,
    # `heal_actions=0`, and `heal_ready = party_is_gauntlet_ready(before)`. Same code path as the
    # treatment, bounded to do nothing. (Shape ported from `Ch24DrakeMode`, `story_harness.py:18694`.)
    # ‼ NON-VACUOUS ON `post_sidney_L75.ss1`, CHECKED: Mightyena is 187/227 = 82.4 %, and
    # `TOP_UP_BELOW = 0.90` (`overworld_items.py:55`) ⇒ unhealed, the party IS below the bar.
    _heal_kwargs: dict = {}
    if _ch24room_fault() == "healnoop":
        report["heal_noop_arm"] = True
        _heal_kwargs["max_actions"] = 0
    try:
        yield from _yield_bounded_by_frames(
            heal_party_from_bag(heal_report, **_heal_kwargs), 200_000)
    except Exception as error:  # noqa: BLE001 - see above; a sealed zone changes the calculus
        reraise_if_aborting(error)
        heal_report["error"] = f"{type(error).__name__}: {error}"
    report["heal"] = {k: v for k, v in heal_report.items() if k != "readings"}
    # ⛔⛔ `heal_ready` IS HOISTED TO THE TOP LEVEL ON PURPOSE — IT IS A GRADE CONJUNCT, NOT TELEMETRY.
    # `R1-HEALED` is taken UNCONDITIONALLY (the heal must never raise in a sealed zone), so the
    # reading set ALONE cannot fail on a heal that ran and accomplished nothing. `Ch24DrakeMode` —
    # which `04-HANDOFF.md` calls "the CURRENT TEMPLATE" — learned this from an adversarial review
    # and proved it with the `POKEBOT_CH24_FAULT_HEALNOOP=1` arm (`story_harness.py:18541`):
    # with a no-op heal the run read `heal_ready=False, missing=[], failure=None` and still PASSED.
    # ‼ The leg RECORDS it and never raises on it — a sealed zone makes refusing worse than
    # continuing under-healed — so the caller/driver is what must assert it (`:18970`, `:19286`).
    report["heal_ready"] = heal_report.get("heal_ready")
    # THE SECOND DROPPED SETTLE. The bag menu closes over several frames; walking out of a menu that
    # has not finished closing is the same flicker hazard as above. Drivers: `:17783`, `:18260`, `:18736`.
    yield from wait_until_truly_controllable()
    _take(report, "R1-HEALED")

    # ---- STEP 3: ROOM N -> HALL N ---------------------------------------------------------------
    yield from _yield_bounded_by_frames(
        _pass_through_door(ROOM_EXIT_DOOR, tuple(from_room.value)), walk_frames)
    yield from wait_until_truly_controllable()
    if not VR._on_map(hall):
        raise BotModeError(
            f"§Ch24 room leg: tried to leave {from_room.name} but we are at {VR._where()}, not "
            f"{hall.name}. ⛔ Do NOT retry backward — every return warp in here is inert.")
    report["hall_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "R1-INHALL")

    # ---- STEP 4: HALL N -> ROOM N+1 -------------------------------------------------------------
    yield from _yield_bounded_by_frames(
        _pass_through_door(HALL_FAR_DOOR, tuple(hall.value)), walk_frames)
    yield from wait_until_truly_controllable()
    if not VR._on_map(to_room):
        raise BotModeError(
            f"§Ch24 room leg: tried to enter {to_room.name} but we are at {VR._where()}.")
    # ‼ THE LANDING TILE IS RECORDED, NEVER ASSERTED. The room's entry cutscene walks the player
    # several tiles north under `lockall`, so a hardcoded arrival tile is wrong by construction.
    report["room_at"] = (str(VR._where()), VR._here_tile())
    try:
        report["room_elite4_state"] = get_event_var("ELITE_4_STATE")
    except Exception as error:  # noqa: BLE001 - telemetry only
        reraise_if_aborting(error)
        report["room_elite4_state"] = "<unreadable>"
    _take(report, "R1-INROOM")

    # ---- STEP 5: FIND THE TRAINER **LIVE**, THEN ENGAGE -----------------------------------------
    # ⛔ NEVER A HARDCODED TRAINER TILE. `map.json` puts every Elite Four member at (6,5), but the
    # entry cutscene moves the PLAYER, so the relationship between us and them is what matters.
    # Pick the visible object north of us and stand one tile south of it.
    yield from wait_until_truly_controllable()
    here = VR._here_tile()
    others = [tuple(o.current_coords) for o in get_map_objects()
              if "isPlayer" not in o.flags and tuple(o.current_coords) != here]
    report["objects_seen"] = others
    # ⭐ THE `others[0]` FALLBACK IS SAFE FOR A DOCUMENTED REASON, NOT BY LUCK: each Elite Four room
    # contains exactly ONE `object_event` — the member — at (6,5), `MOVEMENT_TYPE_FACE_DOWN`,
    # `movement_range 0/0`, and they never despawn (decomp `EverGrandeCity_<X>sRoom/map.json`; the
    # same fact is cited by `Ch24GlaciaMode`, `story_harness.py:18303-18306`). ⇒ "the first object
    # north of us" CANNOT pick the wrong NPC, because there is no other NPC to pick.
    # ‼ If a future room ever holds two objects, this fallback becomes a coin flip — re-derive it
    # rather than trusting this comment.
    target = next((t for t in others if t[1] < here[1]), others[0] if others else None)
    if target is None:
        raise BotModeError(
            f"§Ch24 room leg: no trainer object visible from {here} in {to_room.name}. "
            f"⛔ `get_map_objects()` is a camera-range window — an empty list is NOT proof of "
            f"absence, so this is reported rather than treated as 'nobody here'.")
    stand = (target[0], target[1] + 1)
    report["trainer_at"] = target
    report["stand_at"] = stand
    if VR._here_tile() != stand:
        # ‼ ITS OWN BUDGET, NOT `walk_frames`. The proven drivers use a separate 20,000 here
        # (`story_harness.py:18326`) — this is a few tiles inside one room, not a door transition.
        yield from _yield_bounded_by_frames(
            VR._navigate_riding_out(to_room, stand), navigate_frames)
        yield from wait_until_truly_controllable()
    report["stood_at"] = VR._here_tile()
    yield from ensure_facing_direction("Up")

    # ⛔⛔ THE PRESS IS UNGATED **ON PURPOSE** — AND THIS IS *NOT* THE SAME CASE AS THE LEAGUE GUARD.
    # `prepare_and_open_the_league` says "ONE A, then ride the script out. DO NOT MASH", and that is
    # correct THERE: the guard is a scripted conversation whose tail MOVES AN NPC, so mashing races
    # its startup (the `_GUARD_SCRIPT_SETTLE_FRAMES` bug). An Elite Four member is an INTERACTION
    # TRAINER — the A-press starts a battle and the battle owns input immediately afterwards.
    # The cadence below is copied VERBATIM from `Ch24GlaciaMode` (`story_harness.py:18350-18356`),
    # which took it from `Ch24PhoebeMode` → `Ch24ProbeMode` → `_talk_to_the_stair_grunt`
    # (`space_center.py`), and it has now won three Elite Four fights.
    # ‼ THE STANDALONE `A` BEFORE THE LOOP IS PART OF THE PROVEN SHAPE — do not fold it into the
    # modulo. ⛔ And the hazard an ungated-press rule exists to stop cannot happen here: the loop is
    # BOUNDED, breaks the instant a battle is live, and raises with both tiles named otherwise.
    # ⭐ FAULT ARM `noengage` — walks the ENTIRE unit and then presses NOTHING. It must FAIL with
    # `R1-ENGAGED` and `R1-WON` missing. That is what proves those two readings are earned by
    # FIGHTING, and not satisfied by merely arriving in the room.
    _noengage = _ch24room_fault() == "noengage"
    report["engage_skipped"] = _noengage

    # ⛔⛔⛔ THE DISCRIMINATOR — AND `battle_is_active()` ALONE IS **STRUCTURALLY UNOBSERVABLE** HERE.
    # MEASURED 2026-09-24, and it cost this leg its first drive: the battle began at frame 3,950 and
    # ran to 13,812, and across those 9,862 frames THIS GENERATOR EXECUTED ZERO ITERATIONS, because
    # `main.py` advances only the TOP of the controller stack and `BattleListener` sits above us.
    # ⇒ the only frames on which this loop can poll are the frames a battle is NOT running. The run
    # fought Phoebe, won exp, and then raised *"4,000 frames without starting a battle"*.
    # ‼ The three proven drivers do not hit this because `self.battles` is set by the
    # `on_battle_started` CALLBACK — a push notification that survives the suspension. Production
    # `StoryMode` has the hook (`story_mode.py:3318`) but keeps NO counter, so the leg cannot borrow
    # it. ⇒ we detect the SUSPENSION ITSELF, which needs nothing registered:
    #   * a normal `yield` advances the emulator by ~1 frame;
    #   * a `yield` that a pushed controller ran through advances it by thousands.
    # Plus the victory FLAG, which is set by the time we resume from a won fight.
    # ‼ EACH SIGNAL RECORDS ITSELF IN `engage_signal`. They were one `or` until 2026-09-24, and the
    # very first pair of drives produced a question the log could not answer: `phoebe` reported
    # `engage_suspension_frames` and `glacia` did not, so the second run broke on *one of* the other
    # two — and nothing said which. ⇒ an instrument that cannot name which of its own conjuncts
    # fired will eventually make you guess, and a guess in a write-up is how a wrong fact is born.
    _SUSPENDED = 60  # one second — far above any ordinary hiccup, far below a battle.
    engaged = False
    if not _noengage:
        _before = context.emulator.get_frame_count()
        context.emulator.press_button("A")
        yield
        # ⚠ The very first press can start the fight, so this yield is measured too — otherwise the
        # whole battle could elapse before the loop below takes its first reading.
        if context.emulator.get_frame_count() - _before > _SUSPENDED:
            engaged = True
            report["engage_signal"] = "suspension-on-first-press"
            report["engage_suspension_frames"] = context.emulator.get_frame_count() - _before
    for frame in range(engage_frames):
        if engaged:
            break
        _check_abort()
        if battle_is_active():
            engaged = True
            report["engage_signal"] = "battle_is_active"
            break
        if get_event_flag(victory_flag):
            # The fight is already over and WON — we resumed after the battle without ever
            # observing it. Recorded distinctly, because it means the press loop never saw a battle.
            engaged = True
            report["engage_signal"] = "victory_flag"
            break
        before = context.emulator.get_frame_count()
        if not _noengage:
            context.emulator.press_button("B" if frame % 3 else "A")
        yield
        jumped = context.emulator.get_frame_count() - before
        if jumped > _SUSPENDED:
            engaged = True
            report["engage_signal"] = "suspension"
            report["engage_suspension_frames"] = jumped
    report["engaged"] = engaged
    if not engaged:
        raise BotModeError(
            f"§Ch24 room leg: stood at {stand} facing {target} in {to_room.name} for "
            f"{engage_frames:,} frames without starting a battle. The trainer was located LIVE, so "
            f"this is not a stale-coordinate failure.")
    _take(report, "R1-ENGAGED")

    # ---- STEP 6: FIGHT, THEN ASSERT THE **FLAG**, NOT THE SILENCE -------------------------------
    # ⛔ "the battle ended" is not "we won" — a whiteout also ends the battle. The defeat FLAG is the
    # only signal that distinguishes them, and it is what the grade rests on.
    #
    # ⚠⚠ HONEST ACCOUNT OF WHAT THIS LOOP DOES **NOT** PROTECT AGAINST — an earlier comment here
    # claimed it was "bounded by FRAMES because what follows is a BATTLE", and that OVERSTATED it.
    # `main.py` advances only the TOP of the controller stack, so while the battle controller is
    # pushed this generator is SUSPENDED and these iterations do not tick at all (`KI-28`'s shape).
    # ⇒ this loop bounds the time we spend waiting *outside* the fight, NOT the fight itself. The
    # real backstop against an in-battle hang lives in `battle_handler.py`'s own bounded loops.
    # ‼ Kept anyway, and at the PROVEN 120,000: it is the identical shape the three drivers used to
    # beat Sidney, Phoebe, Glacia and Drake. What is fixed here is the CLAIM, not the code.
    for _ in range(battle_frames):
        _check_abort()
        if not battle_is_active():
            break
        yield
    yield from wait_until_truly_controllable()
    won = bool(get_event_flag(victory_flag))
    report["end_flag"] = won
    report["end_at"] = (str(VR._where()), VR._here_tile())
    if not won:
        raise BotModeError(
            f"§Ch24 room leg: the battle in {to_room.name} ended but {victory_flag} is still False "
            f"at {VR._where()}. ⛔ A battle ending is not a win — this is what a LOSS looks like.")
    _take(report, "R1-WON")

    # ---- STEP 7: ⛔ "AND THE BOT CAN CONTINUE" ---------------------------------------------------
    # A win is not a continuable state. ‼ §Ch15 ended four floors underground, §Ch18 on an
    # eleven-tile island and §Ch19 in a living room — **ALL THREE PASSED THEIR OWN TESTS.** This leg
    # is a LOOP UNIT: the next call's first move is to walk out through `ROOM_EXIT_DOOR`, so if the
    # victory script did not open it, the failure would surface much later as a baffling walk
    # timeout inside the NEXT room's Step 3 instead of here, where it is one line to diagnose.
    #
    # ⛔⛔ IT READS THE **LIVE** GRID, NEVER `get_map_data`. `KI-74`: the exit door is ROM-blocked and
    # runtime-OPENED (`PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles` writes
    # impassable=FALSE), while the entry tiles are ROM-open and runtime-SEALED by `WalkInCloseDoor`.
    # A static read would report the door SHUT on a perfect run.
    #
    # ⚠ SCOPE, so this is not over-read: `OnLoad` also calls `ResetAdvanceToNextRoom` whenever the
    # room's DEFEATED flag is already set, so merely RELOADING a post-victory save re-opens the
    # door. ⇒ this reading is meaningful DURING a run and would be VACUOUS on a reloaded fixture.
    #
    # ⛔ RECORDED, NOT RAISED. The zone is sealed behind us; raising here strands the bot exactly as
    # surely as continuing does, and the caller needs the reading to decide. The reading is simply
    # NOT TAKEN when the door is shut, which is what makes a grade able to fail on it.
    try:
        from modules.story.sootopolis import _live_collision_grid

        grid = _live_collision_grid(to_room)
        report["exit_door_live"] = {t: grid.get(t) for t in ((6, 1), ROOM_EXIT_DOOR)}
        door_open = all(grid.get(t) == 0 for t in ((6, 1), ROOM_EXIT_DOOR))
        report["exit_door_open_live"] = door_open
        if door_open:
            _take(report, "R1-CONTINUE")
    except Exception as error:  # noqa: BLE001 - a reading that fails must SAY so, never lie
        reraise_if_aborting(error)
        report["continue_error"] = f"{type(error).__name__}: {error}"
