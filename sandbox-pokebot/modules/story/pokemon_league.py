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
