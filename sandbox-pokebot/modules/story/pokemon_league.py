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

    # ⭐ RULING 21 (2026-09-27): a Fly carrier that box-first withdrew is NOT a fighter. It flies; it is not ground to
    # the floor, and it is not counted by R1 (`_ch24_carrier_key`).
    carrier = _ch24_carrier_key()
    out = []
    try:
        for mon in get_party():
            if mon is None or getattr(mon, "is_egg", False):
                continue
            if _is_ch24_carrier(mon, carrier):
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


#: ⭐ USER RULING 15 (2026-09-26): R1 lets the party into the Elite Four once AT LEAST this many members are at the
#: floor ("Enter if 4+ are L65"); stragglers ride along. Evidence the user was shown: the only party ever to win the
#: gauntlet was 4×L75 + Zigzagoon L19 + Castform L36. A party smaller than this needs every member at the floor.
CH24_MIN_AT_FLOOR = 4


def ch24_readiness_shortfall(below: list, stock: dict, *, party_size: int, floor: int = CH24_LEVEL_FLOOR,
                             basket=None) -> list:
    """`#26-ch24organic` R1 — the NAMED reasons the party may not enter the Elite Four; [] = it may.

    PURE (no emulator reads) so `probe_ch24_readiness.py` can test every branch on synthetic inputs;
    the caller supplies `below` (from `ch24_trainees_below_floor(floor)`) and `stock` (from
    `victory_road.bag_healing_stock()`).

    ⛔ TWO CONJUNCTS, BOTH MATERIAL, NEITHER ABOUT HEALTH. A whiteout heals the party for free, so a
    health-based gate would re-pass forever while nothing changed (06, 2026-09-25, RULING 12-b). The
    levels: ⭐ USER RULING 15 — at least `min(CH24_MIN_AT_FLOOR, party_size)` members at the floor (RULING 12's
    "train all six" remains the TRAINING target; this is only the entry gate); the basket is the only healing in a
    nurse-less, one-way zone (`LEAGUE_BASKET`, bought by §Ch23 leg 11).
    """
    if basket is None:
        from modules.story.victory_road import LEAGUE_BASKET as basket
    reasons = []
    need = min(CH24_MIN_AT_FLOOR, party_size)
    at_floor = party_size - len(below)
    if at_floor < need:
        reasons.append(f"{len(below)} mōn below the L{floor} floor — only {at_floor} of {party_size} at it, "
                       f"RULING 15 needs {need}: "
                       + ", ".join(f"{sp}#{pid:08X} L{lv}" for pid, sp, lv in below))
    short = [f"{name} {stock.get(name, 0)}/{qty}" for name, qty in basket if stock.get(name, 0) < qty]
    if short:
        reasons.append("League basket short: " + ", ".join(short))
    return reasons


def ch24_should_restock(reasons, on_eg_or_lobby: bool) -> bool:
    """PURE. `#24-restockleg` F1 (USER RULING 12, "Restock, then retry"): restock only when the League basket is R1's
    ONLY reason, only where the Mart is reachable (Ever Grande or the lobby), and not under
    `POKEBOT_CH24_FAULT_NORESTOCK=1`. A level shortfall is never "fixed" by shopping."""
    import os as _os_rs

    return (bool(reasons) and all(str(r).startswith("League basket short") for r in reasons) and bool(on_eg_or_lobby)
            and _os_rs.environ.get("POKEBOT_CH24_FAULT_NORESTOCK") != "1")


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


def _plateau_walkoff_refused(ground_name: str, *, on_plateau: bool, can_fly: bool) -> bool:
    """PURE — `#26-ch24organic` gap 4's return ticket. True ⇔ training this rung would WALK a no-Fly party off
    the League plateau into Victory Road, whose plateau-side (EXIT) half does not reach the grind tile (measured
    2026-09-26). ⛔ Deliberately narrow: every other ground (Granite Cave, Fiery Path, any route) is untouched —
    a general warp-blind reachability check refused them all and was rejected by review (see the call site)."""
    return (not can_fly) and on_plateau and str(ground_name).startswith("VICTORY_ROAD")


def _on_league_plateau() -> bool:
    """In the League lobby, or on EVER_GRANDE_CITY with a SAME-MAP walk to the door apron (18,6).
    ‼ Same-map `calculate_path` is reliable (no warps involved) — it is the exact check §Ch23 leg 10 makes
    (`heal_at_league`). Unreadable ⇒ False (the rule then does not fire; the walk proceeds as before)."""
    from modules.map_path import calculate_path
    from modules.story import victory_road as VR
    from modules.story.early_game import reraise_if_aborting

    try:
        if VR._on_map(VR.LEAGUE_1F):
            return True
        if not VR._on_map(VR.EG):
            return False
        if VR._here_tile() == VR.LEAGUE_DOOR_APRON:
            return True
        calculate_path((VR.EG, VR._here_tile()), (VR.EG, VR.LEAGUE_DOOR_APRON))
        return True
    except Exception as error:  # noqa: BLE001 - "no path" means the SOUTH half: not the plateau; an unreadable
        # position must not invent a refusal either, so both read as False
        reraise_if_aborting(error)
        return False


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

        # ---- `#26-ch24organic` GAP 4 — THE RETURN TICKET (no Fly ⇒ never walk off the plateau into Victory Road)
        # ⛔⛔ MEASURED 2026-09-26 (`evidence/2026-09-26-ch24gap4-OBSERVE-NOFLY-FLOOR50.txt`): a party with NO
        # Fly knower, on the League plateau, with a L47 trainee — the ground picker's oracle (`region_reach`,
        # MAP-level) calls VICTORY_ROAD_1F one hop away, which it is: through the (18,27) door into the cave's
        # EXIT half. `train_team` walked in, landed at (39,5) and raised `UnreachableDestinationError: Could not
        # reach (15, 39)` — the grind tile is in the ENTRANCE half. An unnamed crash, inside a cave, that every
        # derail re-entry repeats.
        # ⛔⛔ AND THE FIRST FIX WAS WRONG, CAUGHT BY REVIEW: it asked `calculate_path(here → (ground, tile))`,
        # which is WARP-BLIND ("not able to use warps", `map_path.py`) — it would have refused EVERY warp-gated
        # ground (Granite Cave, Fiery Path…) and it is the "invisible wrong NO" oracle the KI-24 user decision
        # (2026-07-25) already rejected for training picks. It was right on VR1F only by coincidence.
        # ⇒ THE RULE IS NOW EXACTLY WHAT WAS MEASURED (`_plateau_walkoff_refused`, pure, gated): no Fly + standing
        # on the League plateau + a VICTORY_ROAD_* ground ⇒ a named `no_ground`. Nothing else is touched.
        # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_NOWALKCHECK=1` (skip-the-fix; registered in `29-…REGISTRY.md`).
        import os as _os

        from modules.story.training_areas import can_fly_to_anchor

        if _os.environ.get("POKEBOT_CH24_FAULT_NOWALKCHECK") != "1" and not can_fly_to_anchor(heal_center):
            on_plateau = _on_league_plateau()
            if _plateau_walkoff_refused(ground.name, on_plateau=on_plateau, can_fly=False):
                report.setdefault("no_ground", []).append((species, level))
                report.setdefault("unwalkable", []).append((species, ground.name, tuple(tile), "plateau-no-fly"))
                console.print(f"[yellow]§Ch24 training: nobody can Fly and we stand on the League plateau — "
                              f"{ground.name} {tuple(tile)} is only reachable from here through Victory Road's EXIT "
                              f"half, which does not connect to that tile (measured). Not walking {species} off the "
                              f"plateau; stopping this trainee at L{level}.[/]")
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

    # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_NOTRAIN=1` (registered in `29-DISABLED-FEATURES-REGISTRY.md`),
    # read HERE so it covers BOTH call sites (`story_mode._play` and `prepare_and_open_the_league`).
    # It exists so the R1 readiness refusal can be driven at the PRODUCTION floor without paying for
    # a multi-hour grind first. AFTER the latch on purpose: owning the run is not training.
    import os as _os

    if _os.environ.get("POKEBOT_CH24_FAULT_NOTRAIN") == "1":
        report["fault_notrain"] = True
        console.print("[magenta]§Ch24: FAULT ARM NOTRAIN — training skipped; the party is left "
                      "exactly as it arrived.[/]")
        return

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


#: The readings `ensure_fly_learner` publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
FLY_TEACH_READINGS = (
    "F-KNOWN",    # someone already knew Fly — nothing taught (idempotent re-entry)
    "F-TAUGHT",   # HM02 taught, VERIFIED by PID from the world
)


def _fly_teach_plan(party, item, banned) -> "tuple[int, int | None] | None":
    """PURE: `(party_index, replace_slot)` for teaching `item` (HM02), or None if nobody qualifies.
    `replace_slot=None` means an EMPTY move slot (the game learns without asking).

    THE LEARNER: highest level first, COMPATIBLE, and able to give up a slot WITHOUT LOSING ITS LAST USABLE
    ATTACK. ⛔ NOT `hm_learner_slot` (level alone ⇒ picks a saturated four-HM mon — 5 of 6 measured 8-badge
    parties) and ⛔ NOT `teach_hm_move`'s own slot rule alone (0-power first, else weakest): the battle ban
    list (`battle.yml` — Dig, Solar Beam, Sky Attack, Fake Out, Wrap, Counter …) means the WEAKEST move can be
    the only one the bot will ever click. [Peck, Dig, Solar Beam, Sky Attack] would lose Peck and keep three
    moves it refuses to use — a battler that cannot deal damage in a nurse-less chapter (code review, 2026-09-26).

    THE SLOT, in order: (1) an empty slot; (2) a 0-power status move; (3) a BANNED damaging move (unusable
    anyway), weakest first; (4) the weakest USABLE damaging move — only if another usable one remains (HM
    attacks such as Surf/Strength count; HM slots are never replaced — Gen 3 cannot forget them).
    A mon with NO usable attack before the teach may still learn (nothing is lost by it).
    """
    def _is_hm(learned) -> bool:
        try:
            m = learned.move
            return m.tm_hm is not None and m.tm_hm.name.startswith("HM")
        except Exception:  # noqa: BLE001 - unreadable => NOT provably spendable (ensure_waterfall_learner)
            return True

    def _usable(learned) -> bool:
        try:
            return learned is not None and learned.move.base_power > 0 and learned.move.name not in banned
        except Exception:  # noqa: BLE001 - unreadable => do not count it as an attack we can rely on
            return False

    candidates = []
    for i, mon in enumerate(party):
        if mon is None or getattr(mon, "is_egg", False) or not mon.species.can_learn_tm_hm(item):
            continue
        candidates.append((mon.level, -i, i, mon))
    for _lv, _neg, i, mon in sorted(candidates, reverse=True):
        moves = list(mon.moves)
        if any(l is None for l in moves):
            return i, None
        eligible = [s for s, l in enumerate(moves) if l is not None and not _is_hm(l)]
        if not eligible:
            continue
        usable_before = sum(1 for l in moves if _usable(l))

        def _power(s):
            try:
                return moves[s].move.base_power
            except Exception:  # noqa: BLE001 - unreadable power sorts as a status move (first to go), and
                # `_usable` independently reads it as NOT an attack, so it can never be the "last usable" kept
                return 0

        status = [s for s in eligible if _power(s) == 0]
        banned_dmg = sorted((s for s in eligible if _power(s) > 0 and not _usable(moves[s])), key=_power)
        usable_dmg = sorted((s for s in eligible if _usable(moves[s])), key=_power)
        for slot in status + banned_dmg + usable_dmg:
            usable_after = usable_before - (1 if _usable(moves[slot]) else 0)
            if usable_before == 0 or usable_after >= 1:
                return i, slot
    return None


def _ch24_fly_swap() -> "dict | None":
    """RULING 21's swap record on the running mode, or None.
    Keys: `fighters` [(pid, species)] (the party before the swap), `carrier` (pid, species), `boxed` (pid, species) or
    None (no fighter was boxed: the party had room)."""
    mode = getattr(context, "bot_mode_instance", None)
    return getattr(mode, "_ch24_fly_swap", None)


def _ch24_carrier_key() -> "tuple | None":
    """(pid, species) of a Fly carrier withdrawn by box-first that is NOT one of the recorded fighters; else None."""
    sw = _ch24_fly_swap()
    if not sw or not sw.get("carrier"):
        return None
    carrier = tuple(sw["carrier"])
    return None if carrier in {tuple(f) for f in sw.get("fighters") or ()} else carrier


def _is_ch24_carrier(mon, carrier) -> bool:
    """Is `mon` the recorded Fly carrier? The same PID, and the recorded species OR AN EVOLUTION OF IT (2026-09-27, the
    review of the swap-back evolution fix): the carrier sits in the party through §Ch24 training and evolves if it
    battles and levels, and an exact `(pid, species)` key would then count it as a fighter in R1 and train it as a
    trainee. An unrelated species on the same PID (KI-78) is not the carrier. `POKEBOT_R20_FAULT_SWAPEXACT=1` restores
    the exact key."""
    import os as _os

    if carrier is None or mon.personality_value != carrier[0]:
        return False
    if _os.environ.get("POKEBOT_R20_FAULT_SWAPEXACT") == "1":
        return mon.species.name == carrier[1]
    return _same_or_evolved(carrier[1], mon.species.name)


def _record_fly_swap(before_keys: list, head: int) -> "dict | None":
    """Write RULING 21's swap record on the running mode IF the carrier `head` is now in the party: the fighters before,
    the carrier, and the fighter that left (by (PID, species); None when the party had room). Returns the record.
    ⛔ Called INSIDE the lobby errand, right after the withdraw, so no later fallible step can lose it."""
    carrier = next((m for m in get_party() if m is not None and m.personality_value == head), None)
    if carrier is None:
        return None
    after_keys = {(m.personality_value, m.species.name) for m in get_party()
                  if m is not None and not getattr(m, "is_egg", False)}
    left = [k for k in before_keys if k not in after_keys]
    swap = {"fighters": list(before_keys), "carrier": (head, carrier.species.name), "boxed": left[0] if left else None}
    mode = getattr(context, "bot_mode_instance", None)
    if mode is not None:
        mode._ch24_fly_swap = swap
    return swap


def _boxed_fly_learners(hm02, banned) -> list:
    """PIDs of BOXED mon that can take Fly NOW: one that knows it, or one `_fly_teach_plan([mon])` finds a slot on.
    Order: `boxed_hm_learner_pids` (knows it first, then level). A pure save-block read. `[]` on any read failure: a box
    we cannot read is a box we must not act on."""
    from modules.story.early_game import boxed_hm_learner_pids, reraise_if_aborting
    from modules.story.pc_trip import box_views

    try:
        order = boxed_hm_learner_pids(hm02)
        by_pid = {int(m.personality_value): m for m in (box_views()[1] or []) if m is not None}
    except Exception as error:  # noqa: BLE001 - see the docstring
        reraise_if_aborting(error)
        return []
    out = []
    for pid in order:
        mon = by_pid.get(pid)
        if mon is None:
            continue
        try:
            knows = any(l is not None and l.move.name == "Fly" for l in mon.moves)
            if knows or _fly_teach_plan([mon], hm02, banned) is not None:
                out.append(pid)
        except Exception as error:  # noqa: BLE001 - one unreadable mon must not hide the others
            reraise_if_aborting(error)
            continue
    return out


def _in_league_lobby(errand_factory, *, leave: bool) -> Generator:
    """Run `errand_factory()` (a generator) standing in the League lobby. Returns `(ok, detail, errand_result)`.

    Enters from EVER_GRANDE_CITY if needed (the apron (18,6), then a HELD Up into the door, as `heal_at_league` does);
    when `leave`, walks back out onto EVER_GRANDE_CITY afterwards (Fly is illegal indoors, so a caller that trains next
    must be outside). ⛔ Refuses, without walking, when the planned route to the apron crosses the Victory Road return
    trap (18,27), or when we are on neither map. Every walk is bounded in real frames.
    """
    from modules.map_path import calculate_path
    from modules.story import victory_road as VR
    from modules.story.early_game import _yield_bounded_by_frames

    if not VR._on_map(VR.LEAGUE_1F):
        if not VR._on_map(VR.EG):
            return False, f"not on EVER_GRANDE_CITY or in the lobby ({VR._where()})", None
        if VR._here_tile() != VR.LEAGUE_DOOR_APRON:
            try:
                crossed = [tuple(getattr(wp, "coordinates", ()))
                           for wp in calculate_path((VR.EG, VR._here_tile()), (VR.EG, VR.LEAGUE_DOOR_APRON))]
            except Exception as error:  # noqa: BLE001 - no plan is a refusal, never a blind walk
                from modules.story.early_game import reraise_if_aborting

                reraise_if_aborting(error)
                return False, f"no path to the League door apron from {VR._here_tile()}: {error}", None
            if VR.EG_VICTORY_ROAD_RETURN_TRAP in crossed:
                return False, f"the route to the apron crosses the return trap {VR.EG_VICTORY_ROAD_RETURN_TRAP}", None
            yield from _yield_bounded_by_frames(VR._navigate_riding_out(VR.EG, VR.LEAGUE_DOOR_APRON), 200_000)
            yield from wait_until_truly_controllable()
        yield from _yield_bounded_by_frames(VR._walk_through_warp("Up", VR.EG.value), 60_000)
        yield from wait_until_truly_controllable()
        if not VR._on_map(VR.LEAGUE_1F):
            return False, f"tried to enter the lobby but we are at {VR._where()}", None
    result = yield from errand_factory()
    if leave:
        yield from _yield_bounded_by_frames(VR._navigate_riding_out(VR.LEAGUE_1F, VR.LEAGUE_EXIT_TILE), 60_000)
        yield from wait_until_truly_controllable()
        yield from _yield_bounded_by_frames(VR._walk_through_warp("Down", VR.LEAGUE_1F.value), 60_000)
        yield from wait_until_truly_controllable()
        if not VR._on_map(VR.EG):
            return False, f"left the lobby but we are at {VR._where()}", result
    return True, "ok", result


def _same_or_evolved(recorded_species: str, now_species: str) -> bool:
    """True when `now_species` IS `recorded_species` or evolved FROM it (walks `evolves_from` to the base). A de-evolution
    or an unrelated line is False."""
    from modules.obtainability import evolution_chain_to_base
    from modules.pokemon import get_species_by_name

    if recorded_species == now_species:
        return True
    chain = evolution_chain_to_base(get_species_by_name(now_species).index)
    return get_species_by_name(recorded_species).index in chain[:-1]


def ch24_fighters_restored(party_keys, fighters) -> bool:
    """PURE (given species data). USER RULING 21's identity check: every recorded fighter `(pid, species)` is matched by
    exactly ONE party member with the SAME PID whose species is the recorded one OR AN EVOLUTION OF IT, and nothing else
    is in the party.
    ⛔ WHY EVOLUTION (2026-09-27, `ai-research-notes/2026-09-27-ruling20-phase2-BUILDSPEC.md` §5 F4): the swap is
    recorded BEFORE §Ch24 training, which takes the under-levelled trainees from ~L47 toward L65. Many evolve on the way.
    The PID survives an evolution and the species does not, so an exact `(pid, species)` equality REFUSED THE GUARDS on a
    party that was exactly right, and on every re-entry after it (the record persists).
    ⛔ It stays an IDENTITY check: the same PID with an UNRELATED species does not match (KI-78: Ninjask and Shedinja
    share a PID), and neither does a de-evolution. `POKEBOT_R20_FAULT_SWAPEXACT=1` restores the exact-species test."""
    import os as _os

    exact = _os.environ.get("POKEBOT_R20_FAULT_SWAPEXACT") == "1"
    left = [tuple(k) for k in party_keys]
    if len(left) != len(fighters):
        return False
    for pid, sp in (tuple(f) for f in fighters):
        hit = next((i for i, (p, s) in enumerate(left)
                    if p == pid and (s == sp if exact else _same_or_evolved(sp, s))), None)
        if hit is None:
            return False
        left.pop(hit)
    return True


def restore_ch24_fighters(report=None) -> Generator:
    """USER RULING 21 ("Yes, swap briefly"): the six fighters are restored and CHECKED BY PID before the Elite Four.

    If box-first withdrew a Fly carrier and boxed a fighter (`_ch24_fly_swap`), swap them back at the League lobby PC:
    the carrier into the box, the fighter out. Then the party's non-egg `(pid, species)` set must match the recorded
    fighters (`ch24_fighters_restored`: same PIDs, each species the recorded one or an EVOLUTION of it, since training
    runs between the record and this check), or this REFUSES by name: the Elite Four is one-way, and entering without the
    fighters is what the ruling forbids. No swap recorded ⇒ nothing to do. Production calls it in the lobby, after
    `E1-INSIDE` and before the guards are talked to (talking sets `ENTERED_ELITE_FOUR` permanently).
    `POKEBOT_R20_FAULT_NOSWAPBACK=1` skips the swap: the identity check must then refuse (it proves the check is live).
    """
    import os as _os

    from modules.console import console
    from modules.story.pc_trip import swap_party_box

    report = report if report is not None else {}
    report.setdefault("readings", set())
    sw = _ch24_fly_swap()
    if not sw or not sw.get("boxed"):
        report["swapback"] = "none_needed"
        return
    carrier, boxed = tuple(sw["carrier"]), tuple(sw["boxed"])
    if _os.environ.get("POKEBOT_R20_FAULT_NOSWAPBACK") == "1":
        report["swapback"] = "fault_skipped"
        console.print("[magenta]§Ch24: FAULT ARM NOSWAPBACK — not swapping; the identity check below must refuse.[/]")
    else:
        ok, detail, verdict = yield from _in_league_lobby(lambda: swap_party_box(carrier[0], boxed[0]), leave=False)
        report["swapback"] = {"ok": ok, "detail": detail, "verdict": list(verdict) if verdict else None}
    party_keys = sorted((m.personality_value, m.species.name) for m in get_party()
                        if m is not None and not getattr(m, "is_egg", False))
    fighters = sorted(tuple(f) for f in sw.get("fighters") or ())
    report["swapback_party"] = [f"{sp}#{pid:08X}" for pid, sp in party_keys]
    if not ch24_fighters_restored(party_keys, fighters):
        raise BotModeError(
            "§Ch24 RULING 21: the party is not the six recorded fighters before the Elite Four — party "
            f"{[f'{sp}#{pid:08X}' for pid, sp in party_keys]} vs fighters {[f'{sp}#{pid:08X}' for pid, sp in fighters]}"
            f" (swap-back: {report.get('swapback')}). Refusing to talk to the guards.")
    mode = getattr(context, "bot_mode_instance", None)
    if mode is not None:
        mode._ch24_fly_swap = None
    _take(report, "F-RESTORED")
    console.print(f"[green]§Ch24: RULING 21 — {boxed[1]} is back and {carrier[1]} is boxed; the six fighters are in.[/]")


def ensure_fly_learner(report=None) -> Generator:
    """`#26-ch24organic` GAP 3 — teach HM02 Fly from the bag if nobody in the party knows it.

    ⛔⛔ WHY IT EXISTS. Production never taught Fly (all six recon agents agreed, code-cited:
    `ai-research-notes/2026-09-26-ch24-production-fly-RECON.md`). HM02 is in every organic bag from the
    Route 119 rival on, yet with no knower `can_fly_to_anchor` is always False, so §Ch24's per-trainee Fly
    ladder could offer only WALKABLE ground — and from the League plateau that is Victory Road 1F alone
    (band 36-40), leaving every trainee under L39 `no_ground` and the return bridge unable to fly home.
    ⭐ PLACEMENT (the recon's, adopted): `_play` Segment 24, AFTER the §Ch24 latch and just before
    `train_for_league`. Teaching earlier would switch the Fly shortcut on for every MID-GAME training pick —
    a change to ground selection nothing here has measured.

    THE LEARNER — `ensure_waterfall_learner`'s rule, NOT `hm_learner_slot`'s: COMPATIBLE **and** holding a
    non-HM slot to spend (HMs cannot be forgotten in Gen 3, so a four-HM mon cannot learn anything),
    highest level first. `teach_hm_move(replace_slot=None)` then picks the slot: a 0-power move first,
    else the lowest base power, NEVER an HM (its own guard). Verified from the WORLD, BY PID.

    ⚠ NEVER RAISES FOR A MISSING LEARNER OR A MISSING HM02 — it reports and returns. Training can still use
    walkable ground, R1 refuses an under-levelled party by name, and the return bridge refuses by name if
    the party ends up off the plateau. Flyer ACQUISITION is gap 5.
    """
    import os as _os

    from modules.console import console
    from modules.items import get_item_bag
    from modules.story.early_game import teach_hm_move

    report = report if report is not None else {}
    report.setdefault("readings", set())

    knower = get_party().first_pokemon_with_move("Fly")
    if knower is not None:
        report["fly_teach"] = "already"
        report["fly_knower"] = f"{knower.species.name}#{knower.personality_value:08X}"
        _take(report, "F-KNOWN")
        return

    # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_NOFLYTEACH=1` (registered in `29-…REGISTRY.md`) — the SKIP-THE-FIX
    # arm: production before 2026-09-26, which never taught Fly.
    if _os.environ.get("POKEBOT_CH24_FAULT_NOFLYTEACH") == "1":
        report["fly_teach"] = "fault_skipped"
        console.print("[magenta]§Ch24: FAULT ARM NOFLYTEACH — not teaching Fly.[/]")
        return

    hm02 = next((s.item for s in get_item_bag().tms_hms if s.item.name == "HM02" and s.quantity > 0), None)
    if hm02 is None:
        report["fly_teach"] = "no_hm02"
        console.print("[yellow]§Ch24: HM02 (Fly) is not in the bag — cannot teach Fly.[/]")
        return

    try:
        banned = list(context.config.battle.banned_moves)
    except Exception as error:  # noqa: BLE001 - without the ban list we cannot prove an attack survives
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        banned = ["Fly", "Dive", "Dig", "Bounce", "Sky Attack", "Razor Wind", "Solar Beam"]
    plan = _fly_teach_plan(get_party(), hm02, banned)
    # ⭐ BOX-FIRST (RULING 20 Phase 1, increment B, 2026-09-27; recon `2026-09-27-ruling20-incB-RECON.md`, site "fly").
    # No party member can take Fly, but a BOXED one can: collect it at the League lobby PC (the only PC reachable from the
    # plateau without Fly), then teach it. make-room boxes one fighter (increment A's rule), and USER RULING 21 swaps it
    # back before the Elite Four (`restore_ch24_fighters`); until then the carrier is not trained and R1 does not count
    # it (`_ch24_carrier_key`). `POKEBOT_R20_FAULT_NOFLYBOX=1` skips this block.
    if plan is None and _os.environ.get("POKEBOT_R20_FAULT_NOFLYBOX") != "1":
        boxed = _boxed_fly_learners(hm02, banned)
        report["fly_boxed"] = [f"{p:08X}" for p in boxed]
        if boxed:
            from modules.story.pc_trip import withdraw_from_box

            head = boxed[0]
            before_keys = [(m.personality_value, m.species.name) for m in get_party()
                           if m is not None and not getattr(m, "is_egg", False)]
            console.print(f"[cyan]§Ch24: no party member can take Fly; collecting the boxed learner pid={head:08X} at "
                          f"the League lobby PC...[/]")
            def _collect():
                # ⛔ THE SWAP IS RECORDED HERE, RIGHT AFTER THE WITHDRAW, INSIDE THE LOBBY — never after the walk out
                # (review, 2026-09-27). The walk out can RAISE (`_navigate_riding_out` gives up after its retries), and
                # a record written after it would be lost while a fighter already sits in the box: a later re-entry
                # finds the carrier in the party, box-first never re-runs, and `restore_ch24_fighters` no-ops.
                verdict = yield from withdraw_from_box([head])
                _record_fly_swap(before_keys, head)
                return verdict

            ok, detail, verdict = yield from _in_league_lobby(_collect, leave=True)
            report["fly_box"] = {"ok": ok, "detail": detail, "verdict": list(verdict) if verdict else None}
            carrier = next((m for m in get_party() if m is not None and m.personality_value == head), None)
            swap = _ch24_fly_swap()
            if carrier is None or not swap or tuple(swap.get("carrier") or ())[:1] != (head,):
                console.print(f"[yellow]§Ch24: the boxed Fly learner pid={head:08X} did NOT arrive ({detail}; "
                              f"{report['fly_box']['verdict']}).[/]")
            else:
                report["fly_swap"] = {"carrier": f"{carrier.species.name}#{head:08X}",
                                      "boxed_fighter": (f"{swap['boxed'][1]}#{swap['boxed'][0]:08X}"
                                                        if swap["boxed"] else None)}
                _take(report, "F-BOXWITHDRAWN")
                if any(l is not None and l.move.name == "Fly" for l in carrier.moves):
                    report["fly_teach"] = "already"
                    report["fly_source"] = "box"
                    report["fly_knower"] = f"{carrier.species.name}#{head:08X}"
                    _take(report, "F-KNOWN")
                    console.print(f"[green]§Ch24: withdrew {carrier.species.name}, which already knows Fly.[/]")
                    return
                plan = _fly_teach_plan(get_party(), hm02, banned)
                if plan is not None and get_party()[plan[0]].personality_value != head:
                    # Only the withdrawn mon can qualify here: nobody in the party did before.
                    raise BotModeError(
                        f"§Ch24: withdrew pid={head:08X} but the Fly plan picked "
                        f"pid={get_party()[plan[0]].personality_value:08X} — refusing to teach the wrong mon.")
    best, replace_slot = plan if plan is not None else (None, None)
    if best is None:
        report["fly_teach"] = "no_learner"
        console.print("[yellow]§Ch24: nobody in the party can learn Fly without losing its last usable attack "
                      "(or every compatible member holds four HM moves) — continuing WITHOUT Fly. Flyer "
                      "acquisition is `#26-ch24organic` gap 5.[/]")
        return

    learner = get_party()[best]
    pid = learner.personality_value
    before = [l.move.name for l in learner.moves if l is not None]
    report["fly_learner"] = f"{learner.species.name}#{pid:08X}"
    report["fly_replace_slot"] = replace_slot
    console.print(f"[cyan]§Ch24: teaching Fly to {learner.species.name} (slot {best})…[/]")
    # ⛔ THE SLOT IS OURS, NOT `teach_hm_move`'s: its own rule (0-power, else weakest) can strip the last
    # usable attack. `None` (an empty slot) keeps its no-replace path; never an HM slot (the plan excludes them).
    yield from teach_hm_move(hm02, best, replace_slot=replace_slot)

    # ‼ VERIFY BY PID, FROM THE WORLD — never "slot `best` knows Fly" (rule 3: identity, not position).
    after_mon = next((m for m in get_party() if m is not None and m.personality_value == pid), None)
    after = [l.move.name for l in after_mon.moves if l is not None] if after_mon is not None else []
    report["fly_lost"] = [n for n in before if n not in after]
    if "Fly" not in after:
        raise BotModeError(f"§Ch24: taught HM02 to {report['fly_learner']} but it does not know Fly afterwards "
                           f"(moves now {after}).")
    report["fly_teach"] = "taught"
    _take(report, "F-TAUGHT")
    console.print(f"[green]§Ch24: {learner.species.name} learned Fly"
                  + (f" (lost {', '.join(report['fly_lost'])})" if report["fly_lost"] else "") + "[/]")


#: The reading `return_to_league_door` publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
#: ⛔⛔ NOT `BRIDGE_READINGS`: that name already belongs to `enter_the_league` (the E2-* tuple further down),
#: and a second module-level assignment is SILENTLY SHADOWED by the later one — the code review caught this
#: constant dead on arrival (2026-09-26). `probe_ch24_bridge.py` B5 now refuses any duplicate `*_READINGS`.
RETURN_BRIDGE_READINGS = (
    "B-POSITIONED",   # standing on EVER_GRANDE_CITY (18,6) — ASSERTED by tile — or already in the lobby
)

#: Frame bounds for the bridge's two ways home. Both are BACKSTOPS: a walk across the north plateau is a
#: few hundred frames and a flight a few thousand (menu + animation), so hitting either is a wedge.
BRIDGE_WALK_FRAMES = 60_000
BRIDGE_FLY_FRAMES = 60_000


def _where_name() -> str:
    """`MAP_NAME (x, y)` for humans. ‼ `_where()` is `((group, number), (x, y))` — a TUPLE, not a name
    (seafloor_cavern's transcription rule A; it cost the first R1 drive its grade)."""
    try:
        from modules.map_data import MapRSE

        return f"{MapRSE(tuple(_where()[0])).name} {_here_tile()}"
    except Exception as error:  # noqa: BLE001 - a map NAME is cosmetic; never lose a refusal to it
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        return str(_where())


def return_to_league_door(report=None) -> Generator:
    """`#26-ch24organic` GAP 2 — get back to the League door apron EVER_GRANDE_CITY (18,6), or REFUSE.

    ⛔⛔ WHY IT EXISTS. §Ch24 training ends wherever its last rung ended: a route grind tile (a Fly-anchored
    ground), EVER_GRANDE_CITY (27,49) after the Victory Road step-out — the SOUTH half, from which (18,6) is
    **NO PATH, measured in both directions** (KI-94 2026-09-06; `2026-09-18-vr-heal-roundtrip`) — or indoors
    if a purse expired mid-heal. `prepare_and_open_the_league` then simply WALKED at the door apron with
    the result ignored, and from (27,49) held Up — straight into the Poké Center door at (27,48).
    ⇒ ONE flight fixes every off-plateau case: `fly_to_destination(PokemonLeague)` lands at (18,6)
    (measured from (27,49) and from (18,42)). ⛔ But that leg asserts only that the bot MOVED, so the
    TILE is asserted here — a flight that lands anywhere else must not be followed by a walk at a door.
    ⚠ INDOORS (a Poké Center, League 2F) is NOT walked out of: `_ch24_step_out_if_fly_illegal` handles
    Victory Road 1F only, so indoors ends in the named refusal "Fly is illegal on this map" — bounded and
    loud, but not a recovery (code review, 2026-09-26; undriven).

    IN ORDER: already in the lobby or on (18,6) ⇒ no-op; on Ever Grande with a real path to (18,6) that
    avoids the Victory Road return trap (18,27) ⇒ WALK; otherwise step out of Victory Road if inside it,
    then FLY — refusing BY NAME if there is no Fly knower, no Feather Badge, the League was never visited,
    or Fly is illegal where we stand. ASSERT the tile last, whichever way we came.
    ⭐ It never trains, heals or buys: its only job is position, so a refusal here is about getting home.
    """
    import os as _os

    from modules.console import console
    from modules.map_path import calculate_path
    from modules.memory import get_event_flag
    from modules.region_map import FlyDestinationRSE
    from modules.story import victory_road as VR
    from modules.story.early_game import (
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()
    report["start"] = _where()

    if VR._on_map(VR.LEAGUE_1F):
        report["mode"] = "in_lobby"
        _take(report, "B-POSITIONED")
        return
    if VR._on_map(VR.EG) and VR._here_tile() == VR.LEAGUE_DOOR_APRON:
        report["mode"] = "already"
        _take(report, "B-POSITIONED")
        return

    # ---- 1. ON FOOT, if the north plateau connects us to the apron ------------------------------
    walked = False
    if VR._on_map(VR.EG):
        crossed = None
        try:
            plan = calculate_path((VR.EG, VR._here_tile()), (VR.EG, VR.LEAGUE_DOOR_APRON))
            crossed = [tuple(getattr(wp, "coordinates", ())) for wp in plan]
        except Exception as error:  # noqa: BLE001 - "no path" is the EXPECTED answer from the south half
            reraise_if_aborting(error)
            report["walk_refused"] = f"{type(error).__name__}: {error}"[:200]
        if crossed is not None and VR.EG_VICTORY_ROAD_RETURN_TRAP in crossed:
            # Same trap guard as §Ch23 leg 10: (18,27) is a WALKABLE door straight back into Victory Road.
            report["walk_refused"] = f"the plan crosses the Victory Road return trap {VR.EG_VICTORY_ROAD_RETURN_TRAP}"
            crossed = None
        if crossed is not None:
            report["mode"] = "walk"
            report["plan_wp"] = len(crossed)
            report["walk_finished"] = bool((yield from _yield_bounded_by_frames(
                VR._navigate_riding_out(VR.EG, VR.LEAGUE_DOOR_APRON), BRIDGE_WALK_FRAMES)))
            yield from wait_until_truly_controllable()
            walked = True

    # ---- 2. BY AIR ------------------------------------------------------------------------------
    if not walked:
        yield from _ch24_step_out_if_fly_illegal(report)
        destination = FlyDestinationRSE.PokemonLeague
        missing = []
        try:
            if get_party().first_pokemon_with_move("Fly") is None:
                missing.append("no party member knows Fly")
            if not get_event_flag("BADGE06_GET"):
                missing.append("the Feather Badge (BADGE06) is not held")
            if not get_event_flag(destination.get_flag_name()):
                missing.append(f"the Pokémon League was never visited ({destination.get_flag_name()} is unset)")
            if not fly_is_legal_from_current_map():
                missing.append("Fly is illegal on this map")
        except Exception as error:  # noqa: BLE001 - an unreadable precondition is a refusal, never a "yes"
            reraise_if_aborting(error)
            missing.append(f"a Fly precondition could not be read ({type(error).__name__})")
        report["fly_missing"] = missing
        if missing:
            raise BotModeError(
                f"§Ch24 bridge: cannot return to the League door from {_where_name()} — "
                f"{VR.LEAGUE_DOOR_APRON} is not reachable on foot from here "
                f"({report.get('walk_refused', 'not on Ever Grande')}), and flying back is impossible: "
                f"{'; '.join(missing)}.")
        # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_BRIDGEDEST=1` (registered in `29-…REGISTRY.md`): fly somewhere
        # ELSE, so the tile assertion below must fire — proving it is live, because `fly_to_destination`
        # itself would accept any landing that is not the origin.
        if _os.environ.get("POKEBOT_CH24_FAULT_BRIDGEDEST") == "1":
            destination = FlyDestinationRSE.LilycoveCity
            report["fault_bridgedest"] = True
            console.print("[magenta]§Ch24 bridge: FAULT ARM BRIDGEDEST — flying to Lilycove instead; the "
                          "tile assertion MUST fire.[/]")
        report["mode"] = "fly"
        fly: dict = {}
        report["fly"] = fly
        report["fly_finished"] = bool((yield from _yield_bounded_by_frames(
            fly_to_destination(destination, fly), BRIDGE_FLY_FRAMES)))
        yield from wait_until_truly_controllable()

    # ---- 3. ASSERT THE TILE, whichever way we came -----------------------------------------------
    report["end"] = _where()
    if not (VR._on_map(VR.EG) and VR._here_tile() == VR.LEAGUE_DOOR_APRON):
        raise BotModeError(
            f"§Ch24 bridge: expected to stand on EVER_GRANDE_CITY {VR.LEAGUE_DOOR_APRON} (the League door "
            f"apron) after the {report.get('mode')}, but we are at {_where_name()}. ⛔ Refusing to walk at a "
            f"door from the wrong place.")
    _take(report, "B-POSITIONED")
    console.print(f"[cyan]§Ch24 bridge: at the League door apron {VR.LEAGUE_DOOR_APRON} "
                  f"(by {report['mode']}).[/]")


#: The readings this leg publishes. ⛔ THE DRIVER IMPORTS THIS — it must never keep a private copy.
#: A renamed label with a private copy makes a PERFECT run report `missing=[…]`, and the obvious
#: repair is then to delete a required reading. Precedent: `LEG23_READINGS`, `ICEBEAM_READINGS`.
LEAGUE_ENTRY_READINGS = (
    "E1-LATCHED",     # the run is OWNED before a single button is pressed
    "E1-READY",       # R1 PASSED: floor AND League basket, decided OUTSIDE where it can still be fixed
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
      * `stock_for_the_elite_four`'s money guard fires before any map check and the measured post-basket
        wallet is ₽1,741 — a second call can only top up what is MISSING (USER RULING 16), never re-buy;
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

    # ---- R1: THE READINESS REFUSAL (`#26-ch24organic`) ------------------------------------------
    # ⛔⛔ UNTIL 2026-09-26 THIS WAS A READING, NOT A GATE: a below-floor party took no `E1-READY`
    # and walked in anyway. Nothing between here and `(9,1)` refused it (`enter_the_league` says "NO
    # READINESS CHECK HERE, ON PURPOSE" because it expects THIS leg to have decided), so an organic
    # party whose training fell short — every party with no Fly knower today — would have opened the
    # door and taken on a one-way, nurse-less gauntlet under-levelled.
    # ⇒ REFUSE HERE, OUTSIDE (or in the lobby on a resume — which has a nurse and an exit, so a stop
    # there strands nothing), BEFORE A GUARD IS TALKED TO: `ENTERED_ELITE_FOUR` is permanent.
    # ‼ FAILS CLOSED: an unreadable bag is a refusal. The expensive direction is walking in.
    # ⚠ At `floor=` below production (the harness's `CH24_ENTRY_FLOOR`) the LEVEL half is scoped
    # down with it; the BASKET half is not, and every pinned §Ch24 fixture holds a full basket.
    try:
        stock = VR.bag_healing_stock()
    except Exception as error:  # noqa: BLE001 - see the fail-closed note above
        reraise_if_aborting(error)
        stock = None
    if stock is None:
        reasons = ["the bag could not be read, so the League basket is unverified"]
        report["r1_party_size"] = None
    else:
        try:
            _carrier = _ch24_carrier_key()   # RULING 21: the Fly carrier is not one of the fighters R1 counts
            party_size = sum(1 for m in get_party() if m is not None and not getattr(m, "is_egg", False)
                             and not _is_ch24_carrier(m, _carrier))
        except Exception as error:  # noqa: BLE001 - an unreadable party must REFUSE (fail closed), never pass
            reraise_if_aborting(error)
            party_size = None
        if party_size is None:
            reasons = ["the party could not be read, so R1 cannot count who is at the floor"]
        else:
            reasons = ch24_readiness_shortfall(left, stock, party_size=party_size, floor=floor)
        report["r1_party_size"] = party_size
    import os as _os

    # ---- `#24-restockleg` F1 — USER RULING 12 ("Restock, then retry") -------------------------------------------------
    # ⭐ WHY (2026-09-27, `ai-research-notes/2026-09-27-ch24-basket-restock-RECON.md`): batch run P4r2 entered the Elite
    # Four, beat Sidney and lost to Phoebe. Every re-entry was then refused HERE on a short basket, though the ₽12,300 gap
    # was affordable and the lobby Mart sells all four lines. Nothing restocked: §Ch23 leg 11 is latched off in §Ch24.
    # ⇒ When the basket is R1's ONLY reason and we stand on Ever Grande or in the lobby, run leg 11's own shop ONCE (it
    # buys only what is MISSING, RULING 16; it refuses by name when cash + sellable items cannot cover it; it ends back
    # on Ever Grande), then decide R1 again. A level shortfall is never "fixed" by shopping, and an unaffordable basket
    # still refuses. `POKEBOT_CH24_FAULT_NORESTOCK=1` skips it (the old behaviour).
    if ch24_should_restock(reasons, VR._on_map(VR.EG) or VR._on_map(VR.LEAGUE_1F)):
        restock: dict = {}
        report["restock"] = restock
        console.print(f"[cyan]§Ch24 R1: the basket is short ({'; '.join(reasons)}) — restocking at the League Mart "
                      f"once (RULING 12), then deciding again.[/]")
        try:
            yield from VR.stock_for_the_elite_four(restock)
        except BotModeError as error:
            reraise_if_aborting(error)
            report["restock_error"] = str(error)[:300]
            console.print(f"[yellow]§Ch24 R1: the restock did not complete — {str(error)[:200]}[/]")
        try:
            stock = VR.bag_healing_stock()
        except Exception as error:  # noqa: BLE001 - an unreadable bag must REFUSE (fail closed), never pass
            reraise_if_aborting(error)
            stock = None
        # ⛔ The SAME party size the first decision used. Unrecorded ⇒ refuse by name: a `… or 0` default would make
        # `min(4, 0)` pass the level half (review 2026-09-27; unreachable today, since only a basket-only refusal shops).
        r1_size = report.get("r1_party_size")
        reasons = (["the bag could not be read after the restock, so the League basket is unverified"] if stock is None
                   else ["the party size was not recorded, so R1 cannot be decided again after the restock"]
                   if r1_size is None
                   else ch24_readiness_shortfall(left, stock, party_size=r1_size, floor=floor))
        report["readiness_after_restock"] = reasons
    report["readiness_refusal"] = reasons

    # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_NOREADY=1` — the SKIP-THE-FIX arm: R1 is disarmed, so a
    # below-floor party must walk in and open the door. Proves R1 is what stops it.
    if reasons and _os.environ.get("POKEBOT_CH24_FAULT_NOREADY") == "1":
        report["fault_noready"] = True
        console.print("[magenta]§Ch24 leg 1: FAULT ARM NOREADY — R1 disarmed; continuing despite: "
                      f"{'; '.join(reasons)}[/]")
    elif reasons:
        # ‼ `VR._where()` is `((group, number), (x, y))` — a TUPLE, not a map name (seafloor_cavern's
        # transcription rule A). Record it as-is for identity checks; name the map only for humans.
        report["refused_at"] = VR._where()
        try:
            from modules.map_data import MapRSE

            _here = f"{MapRSE(tuple(VR._where()[0])).name} {VR._here_tile()}"
        except Exception as error:  # noqa: BLE001 - a map NAME is cosmetic; never lose the refusal to it
            reraise_if_aborting(error)
            _here = str(VR._where())
        raise BotModeError(
            f"§Ch24 R1: REFUSING to enter the Elite Four at {_here} — "
            f"{'; '.join(reasons)}. The gauntlet is one-way with no nurse, so this is decided "
            f"BEFORE the guards are talked to ({CH24_ENTERED_FLAG} is still "
            f"{bool(get_event_flag(CH24_ENTERED_FLAG))}).")
    else:
        _take(report, "E1-READY")

    # ---- THE RETURN BRIDGE (`#26-ch24organic` gap 2) --------------------------------------------
    # ⛔ AFTER R1, ON PURPOSE: readiness does not depend on position, so a party that must be refused is
    # refused for READINESS wherever it stands — and only a ready party pays for the trip home.
    # ⛔ FAULT ARM `POKEBOT_CH24_FAULT_NOBRIDGE=1` (skip-the-fix): the pre-2026-09-26 behaviour — walk at
    # the door from wherever training ended.
    if _os.environ.get("POKEBOT_CH24_FAULT_NOBRIDGE") == "1":
        report["fault_nobridge"] = True
        console.print("[magenta]§Ch24 leg 1: FAULT ARM NOBRIDGE — not returning to the door apron.[/]")
    else:
        bridge: dict = {}
        report["bridge"] = bridge
        yield from return_to_league_door(bridge)

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

    # ---- USER RULING 21: THE SIX FIGHTERS BACK, CHECKED BY PID, BEFORE THE GUARDS -------------------------------------
    # ⛔ HERE, and not before R1: R1 is decided wherever training ended (possibly off the plateau), and only the lobby
    # has a PC reachable without Fly. R1 already counts only fighters (`_ch24_carrier_key`), and talking to the guards
    # sets `ENTERED_ELITE_FOUR` permanently, so this is the last point the swap can happen. No swap recorded ⇒ no-op.
    swapback: dict = {}
    report["swapback"] = swapback
    yield from restore_ch24_fighters(swapback)

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


def beat_the_trainer_here(report, *, to_room, victory_flag, prefix: str = "R1",
                          navigate_frames: int = 20_000, engage_frames: int = 4_000,
                          battle_frames: int = 120_000) -> Generator:
    """§Ch24 — STAND BESIDE THE TRAINER IN THIS ROOM, BEAT THEM, AND PROVE WE CAN LEAVE.

    ⭐ **EXTRACTED FROM `fight_one_room` 2026-09-25, VERBATIM AND BEHAVIOUR-PRESERVING**, because a
    SECOND caller needs exactly this and *"the same fact in two functions"* is the shape this module
    already calls out as drift (see the delegating shims at the top of this file).
    ⇒ The second caller is the LEAGUE-ENTRY BRIDGE: it arrives in SIDNEY'S ROOM having never fought
    him, which is a different PREMISE but an identical FIGHT. Duplicating this block would have
    duplicated the three-signal engage discriminator below — knowledge that cost a failed drive.

    ⛔⛔ **THE ENGAGE DISCRIMINATOR IS THE LOAD-BEARING PART, AND ALL THREE SIGNALS ARE NEEDED —
    MEASURED, NOT ARGUED (2026-09-24):**
      * `battle_is_active()` ALONE fails in EVERY room. A battle pushes `BattleListener` ABOVE the
        story generator, so across ~9,862 battle frames this loop ran **zero iterations** and raised
        *"no battle started"* while the log showed the battle being WON.
      * The SUSPENSION detector alone fails in DRAKE's room, where the fight begins during the
        approach and its frames are absorbed by `_navigate_riding_out`'s own budget.
      * The VICTORY FLAG alone cannot separate *"won"* from *"never fought"* in SIDNEY's and
        PHOEBE's rooms.
      ⇒ `engage_signal` records WHICH fired. ‼ A room leg must NEVER assume its own press caused
      the battle.

    `prefix` names the readings (`<prefix>-ENGAGED` / `-WON` / `-CONTINUE`) so each caller's grade
    can say which leg produced them.
    """
    from modules.map import get_map_objects
    from modules.memory import get_event_flag
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story import victory_road as VR
    from modules.battle_state import battle_is_active
    from modules.player import player_avatar_is_controllable  # noqa: F401 - parity with the caller
    from modules.story.early_game import (
        _check_abort,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

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
    _take(report, f"{prefix}-ENGAGED")

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
    _take(report, f"{prefix}-WON")

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
            _take(report, f"{prefix}-CONTINUE")
    except Exception as error:  # noqa: BLE001 - a reading that fails must SAY so, never lie
        reraise_if_aborting(error)
        report["continue_error"] = f"{type(error).__name__}: {error}"


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

    # ---- STEPS 5-7: LOCATE, ENGAGE, WIN, AND PROVE WE CAN LEAVE ---------------------------------
    # ⭐ EXTRACTED 2026-09-25 into `beat_the_trainer_here` so the LEAGUE-ENTRY BRIDGE can reuse it.
    # ⛔ MOVED VERBATIM — the three-signal engage discriminator in there cost a failed drive to
    # learn, and duplicating it would have duplicated the bug it fixes.
    yield from beat_the_trainer_here(
        report, to_room=to_room, victory_flag=victory_flag, prefix="R1",
        navigate_frames=navigate_frames, engage_frames=engage_frames,
        battle_frames=battle_frames)


#: ⛔⛔ **STEP-ON `MB_NON_ANIMATED_DOOR`. ARRIVING *IS* THE WARP — THERE IS NO "WALK UP AND CHECK".**
#: Two tiles wide (`(10,1)` is the twin); `(8,1)`/`(11,1)` are walls. Measured ROM == LIVE at the
#: lobby, so this is the one League door with no `KI-74` divergence.
LEAGUE_ENTRY_DOOR = (9, 1)

#: HALL5's far door into SIDNEY'S ROOM — the same `(5,2)` every hall uses (measured uniform).
HALL5_FAR_DOOR = (5, 2)

#: The readings `enter_the_league` publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
BRIDGE_READINGS = (
    "E2-LATCHED",    # the run is owned before a single button is pressed
    "E2-PREMISE",    # in the lobby, door already open, and SIDNEY NOT YET BEATEN
    "E2-COMMITTED",  # we are on HALL5 — the point of no return is now BEHIND us
    "E2-INROOM",     # SIDNEY'S ROOM, entry cutscene settled
    "E2-ENGAGED",    # a battle actually happened (see the three signals in the helper)
    "E2-WON",        # DEFEATED_ELITE_4_SIDNEY is set
    "E2-CONTINUE",   # and the exit door is OPEN in the LIVE grid
)


def enter_the_league(report=None, *, walk_frames: int = 40_000, settle_frames: int = 3_000,
                     navigate_frames: int = 20_000, engage_frames: int = 4_000,
                     battle_frames: int = 120_000) -> Generator:
    """§Ch24 — THE BRIDGE: cross the point of no return, and beat SIDNEY.

    ⭐ **WHY THIS FUNCTION EXISTS AT ALL.** `prepare_and_open_the_league()` stops ON `(9,3)` with the
    door open and deliberately does NOT step through. `fight_one_room()`'s premise is *already
    standing in room N having beaten trainer N*. ⇒ **nothing connected the two**, and a sequencer
    written as "just loop over `PAIRS`" could not have taken its first swing. This is that missing
    step, and it ends EXACTLY on `fight_one_room(from_room=SIDNEYS_ROOM, ...)`'s premise.

    ⛔⛔⛔ **THIS LEG CROSSES THE POINT OF NO RETURN, AND IT IS HARNESS-ONLY FOR THAT REASON.**
    Stepping onto `(9,1)` sets `ENTERED_ELITE_FOUR`, which is **PERMANENT AND NEVER CLEARED**. Every
    backward warp in the interior sits on `MB_NORMAL`, which the warp code REJECTS — so there is no
    walking back, no Fly (all 11 maps are `MAP_TYPE_INDOOR`), and no Escape Rope
    (`allow_escaping: false`). ‼ **DO NOT WIRE THIS INTO `_play`** until the CHAMPION leg and a
    retargeted END-OF-CONTENT banner land with it: today the statement after the gauntlet is the
    banner, which sets `_reached_end_of_content = True` — so a bot stranded in the corridor would be
    **scored as having finished the game**, and there is no wild encounter and no trainer in HALL5,
    so it cannot even white out of it.

    ⛔ **NO READINESS CHECK HERE, ON PURPOSE.** A 4-agent review MEASURED all three remedies to be
    non-functional from inside the building (`heal_at_league` raises either way; the Mart needs
    ₽54,300 against a measured ₽1,741; `train_for_league` needs Fly and the lobby is INDOOR).
    ⇒ readiness is `prepare_and_open_the_league`'s job, decided OUTSIDE on `EVER_GRANDE`.
    **A gate that cannot remedy is just a halt**, and a halt on this tile is a strand.

    ‼ **WHAT IS ALREADY MEASURED, so this is not a leap in the dark:** the whole route ran green
    once, on 2026-09-17 (`evidence/2026-09-17-ch24probe-SIDNEY-L75.txt`, `ACCEPTANCE: PASS`):
    `(9,3)` → `hall5_at=(5,12)` → `room_landing=(6,11)` → Sidney beaten → `elite4_state_after=1`.
    The pinned fixture `post_sidney_L75.ss1` was captured FROM that run. What did not exist until
    now is a production-shaped, instrumented, fault-armed version of it.
    """
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag, get_event_var
    from modules.story import victory_road as VR
    from modules.story.early_game import (
        _check_abort,
        _pass_through_door,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

    # ---- STEP 0: LATCH, BEFORE ANY BUTTON -------------------------------------------------------
    # ⛔ THE LEG'S FIRST ACT. `_ch23_settled()` is `_ch24_owns_run or ch23_chapter_done()`, and
    # `ch23_chapter_done()` requires `_on_map(EVER_GRANDE)` — FALSE in the lobby and FALSE on every
    # map beyond it. An unlatched run that resumes in here re-enters §Ch23 and burns its attempts.
    mode = getattr(context, "bot_mode_instance", None)
    marker = getattr(mode, "mark_ch24_owns_run", None)
    if callable(marker):
        marker()
        report["latched"] = True
    _take(report, "E2-LATCHED")

    # ---- STEP 1: PREMISE — AND IT MUST REFUSE WHEN POINTED AT ITS OWN OUTPUT --------------------
    # ‼ THREE CONJUNCTS. The FLAG half is what makes this non-vacuous: point this leg at
    # `post_sidney_L75.ss1` (its own output) and it MUST refuse, because reporting a win it did not
    # cause is the failure mode a premise exists to prevent.
    already_won = bool(get_event_flag("DEFEATED_ELITE_4_SIDNEY"))
    report["sidney_flag_at_start"] = already_won
    if already_won:
        raise BotModeError(
            "§Ch24 bridge: PREMISE FAILED — DEFEATED_ELITE_4_SIDNEY is ALREADY set, so this leg "
            "would report a win it did not cause. (Pointed at its own output fixture?)")
    if not VR._on_map(VR.LEAGUE_1F):
        raise BotModeError(
            f"§Ch24 bridge: must start in the League LOBBY on {LEAGUE_GUARD_TALK_TILE}, but we are "
            f"at {VR._where()}. ⛔ This leg does not navigate to the League — that is "
            f"`prepare_and_open_the_league`'s job, and it also decides READINESS (outside).")
    door_open = bool(get_event_flag(CH24_ENTERED_FLAG))
    report["door_open_at_start"] = door_open
    if not door_open:
        raise BotModeError(
            f"§Ch24 bridge: {CH24_ENTERED_FLAG} is False — the GUARDS HAVE NOT MOVED, and they "
            f"stand on (9,2)/(10,2), the ONLY two approach tiles to a two-tile door. Walking at it "
            f"now is the silent-stall shape. Run `prepare_and_open_the_league` first.")
    here = VR._here_tile()
    report["start_at"] = (str(VR._where()), here)
    if here != LEAGUE_GUARD_TALK_TILE:
        # Recorded, not fatal: the door is open, so any standable lobby tile can still reach it.
        report["start_off_talk_tile"] = here
    _take(report, "E2-PREMISE")

    # ---- STEP 2: ⛔⛔ THE COMMITMENT STEP — IRREVERSIBLE FROM HERE -------------------------------
    # ‼ `(9,1)` is STEP-ON: arriving IS the warp, so there is no "walk up to it and re-check".
    # Every check that matters happened above this line, which is the only place it CAN happen.
    yield from _yield_bounded_by_frames(
        _pass_through_door(LEAGUE_ENTRY_DOOR, tuple(VR.LEAGUE_1F.value)), walk_frames)
    yield from wait_until_truly_controllable()
    if not VR._on_map(MapRSE.EVER_GRANDE_CITY_HALL5):
        raise BotModeError(
            f"§Ch24 bridge: stepped at {LEAGUE_ENTRY_DOOR} but we are at {VR._where()}, not HALL5. "
            f"⛔ Do NOT retry backward — if we ARE past the door, every return warp behind us is "
            f"inert and a 'recovery' walks at a tile that never fires.")
    report["hall5_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "E2-COMMITTED")

    # ---- STEP 3: HALL5 -> SIDNEY'S ROOM, AND LET THE ENTRY CUTSCENE FINISH ----------------------
    yield from _yield_bounded_by_frames(
        _pass_through_door(HALL5_FAR_DOOR, tuple(MapRSE.EVER_GRANDE_CITY_HALL5.value)), walk_frames)
    yield from wait_until_truly_controllable()
    if not VR._on_map(MapRSE.EVER_GRANDE_CITY_SIDNEYS_ROOM):
        raise BotModeError(
            f"§Ch24 bridge: tried to enter SIDNEY'S ROOM but we are at {VR._where()}.")

    # ⛔⛔ **SETTLE ON THE VAR, NEVER ON A TILE.** The room's `OnFrame` script `lockall`s and walks
    # the player north (`Common_Movement_WalkUp6`), and `wait_until_truly_controllable` reads True
    # UNDER `lockall` and returns silently on timeout — which is exactly how a 2026-09-17 probe
    # sampled `(6,11)` mid-walk and recorded a tile that is not where the cutscene ends.
    # ⭐ `setvar VAR_ELITE_4_STATE, 1` runs only AFTER `WalkInCloseDoor` returns, so the VAR is the
    # honest discriminator. ‼ RECORDED, NOT ASSERTED: `VAR_ELITE_4_STATE` counts rooms ENTERED at
    # exactly the predecessor value, and a room entered out of sequence neither seals nor advances —
    # so a leg that RAISED on it would be branching on a number that legitimately lags.
    settled = False
    for _ in range(settle_frames):
        _check_abort()
        try:
            if int(get_event_var("ELITE_4_STATE")) >= 1:
                settled = True
                break
        except Exception as error:  # noqa: BLE001 - a telemetry read must never decide the run
            reraise_if_aborting(error)
        yield
    report["cutscene_settled"] = settled
    try:
        report["elite4_state_in_room"] = get_event_var("ELITE_4_STATE")
    except Exception as error:  # noqa: BLE001 - telemetry only
        reraise_if_aborting(error)
        report["elite4_state_in_room"] = "<unreadable>"
    report["room_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "E2-INROOM")

    # ---- STEP 4: BEAT SIDNEY — THE SAME PROVEN FIGHT THE ROOM LEG USES --------------------------
    # ⭐ `beat_the_trainer_here` was EXTRACTED from `fight_one_room` for this caller. Re-typing it
    # would have re-typed the three-signal engage discriminator, and ⛔ SIDNEY is exactly the room
    # where getting that wrong is invisible: he is an INTERACTION trainer (measured), so the press
    # matters here — but DRAKE's room proved the press is NOT always what starts the fight, and a
    # leg must never assume its own press caused the battle.
    yield from beat_the_trainer_here(
        report, to_room=MapRSE.EVER_GRANDE_CITY_SIDNEYS_ROOM,
        victory_flag="DEFEATED_ELITE_4_SIDNEY", prefix="E2",
        navigate_frames=navigate_frames, engage_frames=engage_frames,
        battle_frames=battle_frames)


#: ⛔⛔ STEP-ON WARP. `(5,2)` on HALL4 IS the Champion fight — arriving is committing.
CHAMPION_DOOR_TILE = (5, 2)
#: One tile short of it. `Ch24Hall4Mode` stops here deliberately, and so does the bridge upstream.
CHAMPION_STAND_TILE = (5, 3)


def _ch24_done_probe(label: str) -> dict:
    """Both completion predicates, side by side, at one instant. TELEMETRY ONLY — nothing branches
    on this; it exists so a single drive can show whether the extra conjuncts do any work."""
    from modules.memory import get_event_flag
    from modules.story import victory_road as VR
    from modules.story.early_game import reraise_if_aborting

    out = {"where": label}
    try:
        out["flags_only"] = bool(get_event_flag("IS_CHAMPION")) and bool(
            get_event_flag("SYS_GAME_CLEAR"))
    except Exception as error:  # noqa: BLE001 - telemetry must not fail a run that WON, but a
        # latched abort means the run did NOT win, and laundering it into "<unreadable>" would
        # hide a whiteout behind a diagnostic string.
        reraise_if_aborting(error)
        out["flags_only"] = "<unreadable>"
    try:
        out["gated"] = bool(ch24_chapter_done())
    except Exception as error:  # noqa: BLE001 - same reasoning as above
        reraise_if_aborting(error)
        out["gated"] = "<unreadable>"
    try:
        out["at"] = (str(VR._where()), VR._here_tile())
    except Exception as error:  # noqa: BLE001 - same reasoning as above
        reraise_if_aborting(error)
        out["at"] = "<unreadable>"
    return out


#: The readings `fight_the_champion` publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
#: (Same contract as `ROOM_READINGS`: a private copy makes a PERFECT run report readings the leg
#: never took.)
CHAMPION_READINGS = (
    "C-PREMISE",   # HALL4 (5,3), IS_CHAMPION False, ELITE_4_STATE == 4, DRAKE flag set
    "C-HEALED",    # the last bag heal in the game ran (taken UNCONDITIONALLY — see `heal_ready`)
    "C-CROSSED",   # the map became CHAMPIONS_ROOM after the one irreversible step
    "C-ENGAGED",   # `on_battle_started` fired — ⛔ NOT our press
    "C-WON",       # `on_battle_ended` latched BattleOutcome.Won
    "C-INHOF",     # the map became HALL_OF_FAME, via the SCRIPTED warp
    "C-CLEARED",   # IS_CHAMPION and SYS_GAME_CLEAR both True
    "C-REBOOTED",  # an empty party was observed — EWRAM was wiped and reloaded
    "C-HOME",      # the settle: seven conjuncts, tile (4,2)
    "C-USABLE",    # all of C-HOME RE-ASSERTED after `wait_until_truly_controllable()`
    "C-CANCONTINUE",  # ⭐ a REAL `calculate_path` from the end tile to an exit DERIVED from
    #                 #   the live map's warp table — never a hardcoded tile
)


def fight_the_champion(report=None, *, cross_frames: int = 600, intro_frames: int = 6_000,
                       battle_frames: int = 150_000, chain_frames: int = 10_000,
                       endgame_frames: int = 40_000, settle_frames: int = 3_000) -> Generator:
    """§Ch24 — ROOM 5: CROSS THE CHAMPION'S DOOR, BEAT WALLACE, AND COME OUT THE OTHER SIDE.

    ⛔⛔⛔ **THIS LEG CLEARS THE GAME. IT IS THE MOST IRREVERSIBLE THING IN THE TREE.** From
    `(5,2)` onward there is a forced battle, a forced SAVE, an unskippable credits roll and an
    in-game `SoftReset(RESET_ALL)`. There is no retreat, no Fly, no Escape Rope, and `on_whiteout`
    is the only other exit. ⇒ **every check that matters happens in S1, ABOVE the line, where a
    refusal is free.**

    ⛔⛔ **IT IS NOT AN INSTANCE OF `fight_one_room`, AND `#24-leg2spec` RULES THAT EXPLICITLY:**
    *"BUILD ROOMS 1-4 AS THE UNIT, AND BUILD ROOM 5 PLUS ITS TAIL AS A SEPARATE LEG WITH ITS OWN
    GRADE."* Room 5 has **no defeat flag, no flag guard, no A-press trigger and no door** — its exit
    is a scripted `warp`. ⇒ `beat_the_trainer_here()`'s locate-the-trainer / stand-beside / face /
    three-signal-engage steps are **DELETED, NOT PORTED**: the map script `lockall`s and walks the
    avatar into the fight itself, so `ensure_facing_direction("Up")` would press a direction at a
    LOCKED avatar, and `trainerbattle_no_intro TRAINER_WALLACE` starts the battle with no press of
    ours involved.

    ⭐⭐ **EVERY BOUND IS IN EMULATOR FRAMES, READ FROM `get_frame_count()` — NOT IN LOOP
    ITERATIONS.** This is the correction the room leg paid for: `main.py` advances only the TOP of
    the controller stack, so while `BattleListener` owns the fight THIS GENERATOR IS SUSPENDED and
    an iteration counter does not tick at all (`KI-28`; measured at ~0.2 % of frames). A loop that
    counted its own turns would believe ~300 frames had passed across a 30,000-frame battle.
    ‼ Frame-count bounds are also what make the numbers below comparable to the measured ledger.

    ⭐ **THE MEASURED LEDGER THE BOUNDS COME FROM** (2026-09-17 and re-measured 2026-09-25; every
    NON-BATTLE stage reproduced frame-for-frame across both, so these are deterministic):
    crossing **43** · intro **1,648** · fight **30,908 / 34,795** · post-battle chain **2,690** ·
    HoF→reset **14,161** · settle **426**. ⛔ The FIGHT is the one row that is NOT deterministic —
    a 12.6 % swing between two runs from the same fixture and party — which is why its bound is ~5×
    and must never be tightened toward the measured value.
    """
    # ‼ `take_pending_fault` is imported HERE, not at module level: a mode that declares battle
    # support MUST pop the pending fault every frame it holds control, or a fault sits unclaimed.
    from modules.battle_fault import take_pending_fault
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag, get_event_var, get_game_state, GameState
    from modules.pokemon_party import get_party
    from modules.story import victory_road as VR
    from modules.story.early_game import (
        _check_abort,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

    CHAMP = MapRSE.EVER_GRANDE_CITY_CHAMPIONS_ROOM
    HOF = MapRSE.EVER_GRANDE_CITY_HALL_OF_FAME
    HALL4 = MapRSE.EVER_GRANDE_CITY_HALL4
    # ‼ THE POST-GAME LANDING, MEASURED (not assumed): the Hall of Fame reboots the game and
    # returns the player to their own BEDROOM. Asserted POSITIVELY below — `not CHAMP and not
    # HOF` is a negative identity and would hold on any of ~400 other maps.
    # ‼ BOTH BEDROOMS, BECAUSE GENDER IS CONFIGURABLE. `story.yml` documents `gender: boy|girl`
    # and a GIRL save resumes in MAYS_HOUSE_2F (group 1 number 3), NOT Brendan's. Naming only
    # one would make `_settled()` never return True on a girl profile and TIME OUT a run that
    # had just cleared the game. Every profile in the repo is `boy` today — a latent bug is
    # still a bug, and this is the kind that ships.
    HOME_MAPS = (MapRSE.LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, MapRSE.LITTLEROOT_TOWN_MAYS_HOUSE_2F)
    # ✅ (4,2) HOLDS FOR **BOTH** BEDROOMS — VERIFIED 2026-09-25 by reading the decomp directly
    # (`gh api repos/pret/pokeemerald/contents/src/data/heal_locations.json`): the entries
    # HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F and ..._MAYS_HOUSE_2F BOTH read x=4, y=2.
    # It is also MEASURED LIVE for Brendan's, twice. ⇒ this conjunct is safe on either gender.
    # ⚠ WHAT IS STILL UNPROVEN is only the LIVE DRIVE: no `gender: girl` profile exists, so the
    # girl path rests on derived+decomp reasoning, never on a run. The egress TARGET is read
    # from the live warp table, so May's stairs never needed verifying at all.
    HOME_TILE = (4, 2)
    # ⭐ CROSS-CHECK ONLY, NEVER THE TARGET. The decomp puts Brendan's stairs at (7,1) and the
    # live pathfinder returned exactly 4 waypoints to it — two independent methods agreeing.
    # The TARGET is derived from the live map below, so this number can never strand a run.
    HOME_STAIRS_EXPECTED_MALE = (7, 1)

    def _frames() -> int:
        try:
            return int(context.emulator.get_frame_count())
        except Exception:  # noqa: BLE001 - a clock that fails must not decide the run
            return -1

    def _mode_attr(name, default=None):
        """Battle facts come from the MODE's callbacks, never from our own presses.

        ⛔ `on_battle_started` / `on_battle_ended` are BotMode callbacks; a generator cannot see a
        battle it is suspended through. This is the only honest channel.
        """
        return getattr(getattr(context, "bot_mode_instance", None), name, default)

    def _press_a_until(predicate, budget: int, label: str, *, forbid_naming_screen: bool = False):
        """Supply A edges and WATCH. ⛔ Bounded in EMULATOR FRAMES, never in iterations.

        ‼ The whole post-crossing leg is *"press A and observe"* — the game drives itself. Our only
        jobs are to supply button edges, to consume battle faults, and to STOP when told.
        """
        start = _frames()
        # ⛔⛔ A BOUNDED `while True`, AND THE BOUND'S LIMIT IS MEASURED, NOT ASSUMED.
        # It exits on the predicate or on `_frames() - start > budget` — a FRAME bound, because
        # iterations are meaningless here (`KI-28`: this generator is starved while a battle owns
        # the controller stack).
        # ‼ BUT MEASURED 2026-09-25: **THAT BOUND CANNOT FIRE WHILE WE ARE STARVED.** The intro call
        # blew a 6,000-frame budget to 36,457 without refusing, because it never got a turn on which
        # to evaluate the check. ⇒ this bound protects against a loop that IS RUNNING and getting
        # nowhere; it CANNOT protect against a controller above us that never yields. That case is
        # the harness/production no-progress watchdog's job, not this loop's.
        # ⇒ therefore any span that BRACKETS a battle is attributed from the on_battle_* CALLBACKS
        # (see below), never from this loop's elapsed time.
        while True:
            _check_abort()
            if predicate():
                return True, _frames() - start
            if forbid_naming_screen:
                # ⛔⛔ HARD ABORT, AND STOP PRESSING IMMEDIATELY. If flash carried no save the reboot
                # lands on NEW GAME; pressing on would begin OVERWRITING one. There is no recovery
                # worth attempting here — refusing loudly is the only safe act.
                try:
                    if get_game_state() is GameState.NAMING_SCREEN:
                        raise BotModeError(
                            "§Ch24 champion: the reboot landed on the NAMING SCREEN (NEW GAME). "
                            "⛔ STOPPED PRESSING IMMEDIATELY — continuing would overwrite a save.")
                except BotModeError:
                    raise
                except Exception as error:  # noqa: BLE001 - a state read must not decide the run
                    reraise_if_aborting(error)
            if _frames() - start > budget:
                return False, _frames() - start
            try:
                take_pending_fault()
            except Exception as error:  # noqa: BLE001 - fault draining is best-effort
                reraise_if_aborting(error)
            context.emulator.press_button("A")
            yield

    # ---- S1: PREMISE + THE LAST HEAL IN THE GAME ------------------------------------------------
    # ⭐ EVERYTHING THAT MATTERS HAPPENS HERE, because this is the last place a refusal is free.
    conj = {}
    try:
        conj["on_hall4"] = bool(VR._on_map(HALL4))
        conj["at_stand_tile"] = tuple(VR._here_tile()) == tuple(CHAMPION_STAND_TILE)
        conj["not_champion_yet"] = get_event_flag("IS_CHAMPION") is False
        conj["drake_beaten"] = get_event_flag("DEFEATED_ELITE_4_DRAKE") is True
    except Exception as error:  # noqa: BLE001
        reraise_if_aborting(error)
        raise BotModeError(f"§Ch24 champion: premise unreadable: {type(error).__name__}: {error}")
    try:
        conj["elite4_state_is_4"] = int(get_event_var("ELITE_4_STATE")) == 4
    except Exception as error:  # noqa: BLE001 - recorded; the other four carry the premise
        reraise_if_aborting(error)
        conj["elite4_state_is_4"] = "<unreadable>"
    report["premise"] = dict(conj)
    report["start_at"] = (str(VR._where()), VR._here_tile())
    if not (conj["on_hall4"] and conj["at_stand_tile"]
            and conj["not_champion_yet"] and conj["drake_beaten"]):
        raise BotModeError(
            f"§Ch24 champion: PREMISE FAILED {conj} at {VR._where()}. ⛔ Refusing ABOVE the "
            f"irreversible line — nothing was pressed. ‼ `not_champion_yet=False` means this run "
            f"has ALREADY cleared the game (pointed at its own output?).")

    # ⛔ RECORDED AND NEVER ASSERTED — the things that stop being readable the moment we step.
    try:
        report["pp_at_door"] = [
            (m.species.name, [(x.move.name, x.pp, x.total_pp) for x in m.moves if x is not None])
            for m in get_party() if not getattr(m, "is_empty", False)]
        report["hp_at_door"] = [(m.species.name, m.current_hp, m.total_hp)
                                for m in get_party() if not getattr(m, "is_empty", False)]
    except Exception as error:  # noqa: BLE001 - telemetry only
        reraise_if_aborting(error)
        report["pp_at_door"] = report["hp_at_door"] = "<unreadable>"
    # ⛔⛔ BASELINE THE BATTLE COUNTERS **BEFORE ANY PRESS**, AND ASK RELATIVE QUESTIONS AFTER.
    # `battle_started_frame` / `battle_ended_frame` are MODE-level latches set by EVERY battle.
    # Driven alone this leg sees one battle and `is not None` is sound; driven as the FIFTH leg
    # of the gauntlet, FOUR fights have already ended before it starts, so both latches are
    # pre-set and S3/S4 would fall through VACUOUSLY — the leg would believe the Champion fight
    # was over before it began. MEASURED 2026-09-25 on the first full-chain drive.
    # ‼ The fighting was never the problem: that same run logged five battles, all Won. The
    # defect was HOW THE LEG ASKED — an ABSOLUTE test where a RELATIVE one was needed.
    _battles_at_start = _mode_attr("battles", 0) or 0
    report["battles_before_leg"] = _battles_at_start
    _take(report, "C-PREMISE")

    # ⛔⛔ THE LAST HEAL IN THE GAME, AND IT NEVER RAISES. Past `(5,2)` there is no nurse, no Mart
    # and no retreat, so a refusal here strands the run — worse than fighting under-healed.
    # ‼ `C-HEALED` is taken UNCONDITIONALLY, which is exactly why `heal_ready` must be a SEPARATE
    # grade conjunct: otherwise a heal that RAN and achieved NOTHING passes (the `HEALNOOP` lesson).
    # ⚠ And HP is all it can fix: PP is unrestorable anywhere in the League — measured, the Mart
    # sells no Ether/Elixir/Leppa — so `pp_at_door` above is the diagnostic for a loss, not a gate.
    heal_report: dict = {}
    try:
        yield from _budgeted(heal_party_from_bag(heal_report), 200_000, "§Ch24 champion: last heal")
    except Exception as error:  # noqa: BLE001 - see above; a sealed zone changes the calculus
        reraise_if_aborting(error)
        heal_report["error"] = f"{type(error).__name__}: {error}"
    report["heal"] = {k: v for k, v in heal_report.items() if k != "readings"}
    report["heal_ready"] = heal_report.get("heal_ready")
    _take(report, "C-HEALED")

    # ---- S2: THE CROSSING — the one irreversible act --------------------------------------------
    # ⛔⛔ EIGHT RAW `Up` PRESSES, AND NOTHING ELSE. `navigate_to`, `_pass_through_door`,
    # `_navigate_riding_out` and `_goto_warp` are ALL FORBIDDEN here: they treat the warp as a
    # DESTINATION, which is trap T10 — and `Ch24Hall4Mode` carries a tripwire one tile earlier for
    # precisely this. `(5,2)` is step-on: ARRIVING IS THE WARP.
    report["crossed_from"] = (str(VR._where()), VR._here_tile())
    for _ in range(8):
        _check_abort()
        try:
            take_pending_fault()
        except Exception as error:  # noqa: BLE001 - draining a fault is BEST-EFFORT and must never
            # stop the crossing: we are one press from an irreversible step, and a fault-queue read
            # that fails is not a reason to abandon a run that has already committed to going.
            reraise_if_aborting(error)
        context.emulator.press_button("Up")
        yield

    # ⛔ THE READING IS THE MAP, NOT "we left HALL4". For the first ~32 frames the position still
    # reads HALL4 (5,2) — a leg that graded on leaving would fire before the warp completed.
    ok, spent = yield from _press_a_until(lambda: VR._on_map(CHAMP), cross_frames, "cross")
    report["cross_frames_spent"] = spent
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: pressed Up 8× at {CHAMPION_STAND_TILE} but the map is still "
            f"{VR._where()} after {spent} frames. The step did not take. ⛔ Do NOT retry blindly — "
            f"if we ARE across, every warp behind us is inert.")
    _take(report, "C-CROSSED")
    # ⛔ CAPTURED HERE, NOT AFTER THE INTRO LOOP. Measured the hard way 2026-09-25: taken
    # after that loop returns, this clock has already passed THROUGH the whole battle, so
    # `intro_true` came out at **-34,729** — a NEGATIVE duration, which is the tell that saved it.
    # ‼ Signed arithmetic that CAN go negative is self-checking; an unsigned or clamped version
    # of this same bug would have shipped a plausible small number.
    _cross_end = _frames()

    # ---- S3: THE APPROACH AND THE INTRO — supply edges, act on nothing --------------------------
    # The map script `lockall`s, walks the avatar (6,12)->(6,6) and prints the intro speech. Our
    # only job is to give `waitbuttonpress` the JOY_NEW edges it wants.
    ok, spent = yield from _press_a_until(
        lambda: (_mode_attr("battles", 0) or 0) > _battles_at_start, intro_frames, "intro")
    # ⛔⛔ TWO NUMBERS, AND ONLY ONE OF THEM MEANS "THE INTRO". See the note below: this loop is
    # suspended through the whole fight, so its own elapsed count swallows the battle.
    report["intro_wall_frames"] = spent
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: crossed into the Champion's room but no battle started within "
            f"{spent} frames. ⛔ We are past the point of no return with no fight — this is a "
            f"STRAND, and there is nothing to retreat to.")
    # ⭐ FROM THE CALLBACK, NEVER FROM OUR PRESS. `trainerbattle_no_intro TRAINER_WALLACE` starts
    # this fight from inside the map script; we demonstrably did not cause it.
    _take(report, "C-ENGAGED")

    # ---- S4: THE FIGHT — hold control, press, observe nothing -----------------------------------
    def _this_fight_over() -> bool:
        # ‼ NOT "an end latch exists" — four of them already did. The end must be NEWER than the
        # START of the battle this leg is actually in.
        _bs, _be = _mode_attr("battle_started_frame"), _mode_attr("battle_ended_frame")
        if _bs is None or _be is None:
            return False
        try:
            return int(_be) >= int(_bs)
        except Exception:  # noqa: BLE001 - an unreadable latch means "not yet", never "done": the
            # safe direction is to keep waiting inside a bound, not to claim a fight ended.
            return False

    ok, spent = yield from _press_a_until(_this_fight_over, battle_frames, "fight")
    report["battle_wall_frames"] = spent
    report["battle_outcome"] = repr(_mode_attr("battle_outcome"))
    # ⭐⭐ THE HONEST ATTRIBUTION, FROM THE CALLBACKS — WHICH FIRE REGARDLESS OF SUSPENSION.
    # MEASURED 2026-09-25: the first passing drive reported `intro = 36,457` (against a 6,000 bound
    # it never got a frame to enforce) and `fight = 0`, because the intro loop was starved from the
    # moment the battle began until after it ended. ⇒ loop-elapsed time CANNOT attribute a span that
    # brackets a battle, and a frame budget cannot INTERRUPT a suspension — only notice it later.
    # ‼ The `*_wall_frames` values are KEPT rather than replaced: the gap between wall and true IS
    # the measurement of how long this generator was starved, which is a fact worth having.
    _bs, _be = _mode_attr("battle_started_frame"), _mode_attr("battle_ended_frame")
    try:
        report["intro_true_frames"] = (int(_bs) - int(_cross_end)) if _bs is not None else None
        report["fight_true_frames"] = (int(_be) - int(_bs)) if (_bs is not None
                                                                and _be is not None) else None
        report["starved_frames"] = (report["battle_wall_frames"] or 0) + (
            report["intro_wall_frames"] or 0) - ((report["intro_true_frames"] or 0)
                                                 + (report["fight_true_frames"] or 0))
    except Exception as error:  # noqa: BLE001 - an arithmetic slip in TELEMETRY must never fail a
        # run that has already won the game; the raw latch frames are recorded either way.
        reraise_if_aborting(error)
        report["intro_true_frames"] = report["fight_true_frames"] = "<unreadable>"
    report["battle_started_frame"] = _bs
    report["battle_ended_frame"] = _be
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: the Wallace fight did not end within {spent} loop-observed frames "
            f"(bound {battle_frames:,}). ‼ That count EXCLUDES the frames this generator was "
            f"starved for, so the real elapsed time is larger.")
    # ⛔ "THE BATTLE ENDED" IS NOT "WE WON" — a whiteout ends it too. `BattleOutcome` is the only
    # signal that separates them, and `on_whiteout` is an independent second channel.
    outcome = _mode_attr("battle_outcome")
    won = getattr(outcome, "name", str(outcome)) == "Won"
    report["won"] = won
    if not won:
        raise BotModeError(
            f"§Ch24 champion: the fight ended with outcome {outcome!r}, not Won. ‼ THIS IS THE "
            f"ANSWER, NOT A DEFECT: the party could not beat Wallace as equipped. ⛔ Read "
            f"`pp_at_door` before blaming levels — the lead has historically arrived with its two "
            f"main attacks at ZERO PP, and PP is unrestorable past the lobby.")
    _take(report, "C-WON")

    # ---- S5: THE POST-BATTLE CHAIN AND THE SCRIPTED WARP ----------------------------------------
    # ~9-10 button-gated stops interleaved with movement blocks no button advances, then the rival
    # and Birch spawn, the dex is rated, and the script `warp`s us to the Hall of Fame.
    # ⛔ NOT gated on a text-printer state: that is blind to the raw `waitbuttonpress` in the dex
    # rating, and the number of prompts moves with dex state. Frames, not presses.
    ok, spent = yield from _press_a_until(lambda: VR._on_map(HOF), chain_frames, "chain")
    report["chain_frames_spent"] = spent
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: the post-battle chain did not reach the Hall of Fame within {spent} "
            f"frames (bound {chain_frames:,}).")
    report["hof_at"] = (str(VR._where()), VR._here_tile())
    # ⭐ The arrival tile is the scripted `warp`'s literal argument — proof the bot never walked a
    # door. ⛔ And we do NOT assert "the exit door is open": vacuous here.
    _take(report, "C-INHOF")

    # ---- S6: HALL OF FAME -> SAVE -> CREDITS -> SoftReset ---------------------------------------
    # ⛔ THE CREDITS CANNOT BE FAST-FORWARDED ON A FIRST CLEAR, BY CONSTRUCTION: the B-hold speed-up
    # is gated on `gHasHallOfFameRecords`, which is FALSE exactly when this is the first clear.
    # ⭐MEASURED: the probe A-mashed throughout and the credits still cost 10,353 frames.
    # ⇒ this bound must NOT be tightened toward the measured 14,161: a SECOND clear is materially
    # shorter, and a first clear is the only path this leg takes. There is no slack to reclaim here,
    # only risk.
    def _cleared() -> bool:
        try:
            return bool(get_event_flag("IS_CHAMPION")) and bool(get_event_flag("SYS_GAME_CLEAR"))
        except Exception:  # noqa: BLE001 - FALSE means "not cleared YET", which is the honest answer
            # to an unreadable flag during the reboot: RAM is genuinely garbage across the
            # SoftReset, so a failed read here is EXPECTED, not exceptional. ‼ Returning False can
            # only make the leg wait longer and time out loudly — it can never fake a clear.
            return False

    def _party_empty() -> bool:
        try:
            return len([m for m in get_party() if not getattr(m, "is_empty", False)]) == 0
        except Exception:  # noqa: BLE001 - the party structure is UNREADABLE by construction while
            # EWRAM is being wiped, so a throw here is the expected mid-reboot state. ⛔ Returning
            # False (rather than True) is the SAFE direction: it refuses to claim the reboot
            # happened on the strength of a failed read, so `C-REBOOTED` can only be earned by an
            # actual empty-party observation.
            return False

    seen = {"cleared": False, "rebooted": False}

    def _endgame_done() -> bool:
        if not seen["cleared"] and _cleared():
            seen["cleared"] = True
            # ⭐⭐ THE DISCRIMINATOR, SAMPLED ON THE FRAME THE FLAGS FLIP — which is MID-CHAPTER:
            # the credits have not rolled and the SoftReset has not happened. A flags-only gate
            # would declare §Ch24 finished HERE. If `gated` is also True at this instant, my extra
            # conjuncts are decoration and should be deleted — that is a RESULT, not a failure.
            # ‼ An earlier version of this probe sat next to `_take(..., "C-CLEARED")`, which is
            # AFTER this loop exits (the loop also waits for the reboot) — it sampled mid-EWRAM
            # -reload and reported `at: ((0,0), (-7,-7))`, a nonsense coordinate. Wrong instant,
            # real reading; the coordinate is what exposed it.
            report["_done_probe_at_cleared"] = _ch24_done_probe("the INSTANT the flags flip")
        # ⭐ AN EMPTY PARTY IS THE ONLY POSITIVE PROOF EWRAM WAS WIPED AND RELOADED. It is ~207
        # frames wide and unreachable at any earlier point in the leg, which is what makes it a
        # reading rather than a coincidence.
        if not seen["rebooted"] and _party_empty():
            seen["rebooted"] = True
        return seen["cleared"] and seen["rebooted"]

    ok, spent = yield from _press_a_until(
        _endgame_done, endgame_frames, "endgame", forbid_naming_screen=True)
    report["endgame_frames_spent"] = spent
    report["saw_cleared"] = seen["cleared"]
    report["saw_rebooted"] = seen["rebooted"]
    if seen["cleared"]:
        _take(report, "C-CLEARED")
    if seen["rebooted"]:
        _take(report, "C-REBOOTED")
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: the endgame did not complete within {spent} frames "
            f"(cleared={seen['cleared']} rebooted={seen['rebooted']}, bound {endgame_frames:,}).")

    # ---- S7: THE SETTLE — the only place this leg may return from -------------------------------
    # ⭐⭐ SEVEN CONJUNCTS, AND `script_idle` IS THE ONE DOING THE WORK. The global script context
    # reads ACTIVE for ~12,651 frames across the HoF screen and the whole credits roll, because
    # `releaseall` sits AFTER `special GameClear`, which swaps the main callback before the script
    # runner reaches it. It therefore covers exactly the `lockall` window that controllability does
    # NOT. ⛔ Conversely: never WAIT for script-idle earlier — it would block for those 12,651 frames.
    def _settled() -> bool:
        try:
            from modules.player import player_avatar_is_controllable
            from modules.tasks import get_global_script_context

            if get_game_state() is not GameState.OVERWORLD:
                return False
            if not player_avatar_is_controllable():
                return False
            if get_global_script_context().is_active:
                return False
            if VR._on_map(CHAMP) or VR._on_map(HOF):
                return False
            # ‼ POSITIVE identity. The two lines above only say where we are NOT.
            if not any(VR._on_map(m) for m in HOME_MAPS):
                return False
            # ⛔ A NON-EMPTY PARTY IS THE POSITIVE PROOF EWRAM CAME BACK. Without it the ~206-frame
            # post-reload window passes three of the other conjuncts and reads as HOME.
            if len([m for m in get_party() if not getattr(m, "is_empty", False)]) == 0:
                return False
            return tuple(VR._here_tile()) == tuple(HOME_TILE)
        except Exception:  # noqa: BLE001 - "not settled yet" is the honest answer to a failed read
            return False

    ok, spent = yield from _press_a_until(_settled, settle_frames, "settle")
    report["settle_frames_spent"] = spent
    report["end_at"] = (str(VR._where()), VR._here_tile())
    if not ok:
        raise BotModeError(
            f"§Ch24 champion: the game cleared but never settled to a usable overworld within "
            f"{spent} frames. end_at={report['end_at']}")
    _take(report, "C-HOME")

    # ⭐ AND THE SECOND READING, AFTER THE SETTLE — BECAUSE THE FIRST `True` IS UNTRUSTWORTHY.
    # `player_avatar_is_controllable` debounces `Task_ExitDoor` and `sub_8080B9C` but NOT
    # `Task_ExitNonDoor`, which is exactly the task present on the first post-CONTINUE overworld
    # frame. ⇒ re-assert everything after a real settle, or the grade rests on a flicker.
    yield from wait_until_truly_controllable()
    if not _settled():
        raise BotModeError(
            f"§Ch24 champion: C-HOME held but C-USABLE did not re-assert after "
            f"`wait_until_truly_controllable()` at {VR._where()} — the first controllable frame "
            f"was a flicker, which is the exact failure this second reading exists to catch.")
    report["usable_at"] = (str(VR._where()), VR._here_tile())
    _take(report, "C-USABLE")

    # ---- S8: AND THE BOT CAN CONTINUE ------------------------------------------------------------
    # ⭐⭐ THE READING THAT THREE SHIPPED CHAPTERS DID NOT HAVE. §Ch15 ended four floors
    # underground, §Ch18 on an eleven-tile island and §Ch19 in a living room — ALL THREE PASSED
    # THEIR OWN TESTS, because "controllable" is not "can go somewhere". This chapter ends in a
    # BEDROOM, which is the same shape, so the proof is a real path to the only exit.
    # ⛔ NOT a four-neighbour probe (what `R-CONTINUE` does on the Fly landing): in a bedroom every
    # neighbour is floor, so it would pass while the bot was sealed in. The STAIRS are the question.
    import os as _os

    from modules.map import get_map_data_for_current_position
    from modules.map_path import PathFindingError, calculate_path

    here = tuple(VR._here_tile())
    # ⛔⛔ DERIVE THE TARGET FROM THE MAP THE RUN ACTUALLY REACHED — NEVER A HARDCODED TILE.
    # The project's own rule, and it has teeth here: a GIRL save lands in a DIFFERENT bedroom, whose
    # stairs I have not measured. Reading the warp table off the live map is correct on both, and on
    # any future map this leg is ever pointed at.
    try:
        _md = get_map_data_for_current_position()
        _here_map = _md.map_group_and_number
        exits = [tuple(w.local_coordinates) for w in (_md.warps or [])]
    except Exception as error:  # noqa: BLE001 - an unreadable map is a refusal, never a pass
        reraise_if_aborting(error)
        raise BotModeError(
            f"§Ch24 champion: the game is CLEARED but the map at {VR._where()} could not be read to "
            f"find its exits: {type(error).__name__}: {error}")
    # ⛔ FAULT ARM — read IN PRODUCTION so it is DRIVER-PROOF. Replaces the real exits with a tile
    # that cannot be reached, proving this check can actually FAIL. A guard never seen to fail is
    # decoration, and this one guards the shape that shipped THREE chapters stranded.
    if _os.environ.get("POKEBOT_CH24_FAULT_NOEGRESS") == "1":
        exits = [(0, 0)]  # the map's top-left corner — solid wall, and never a warp
        report["egress_fault_armed"] = True
    report["egress_exits"] = exits
    report["egress_expected_male_stairs"] = tuple(HOME_STAIRS_EXPECTED_MALE)
    if not exits:
        raise BotModeError(
            f"§Ch24 champion: the game is CLEARED and the bot stands on {here} in {VR._where()}, "
            f"but the map declares NO WARPS AT ALL — there is no way out of this room.")

    reached, waypoints, refusals = None, None, []
    for tile in exits:
        try:
            # ‼ `calculate_path` will not route THROUGH a warp, but the DESTINATION may BE one and
            # it follows it (`map_path.py`) — which is exactly an exit tile.
            path = calculate_path((_here_map, here), (_here_map, tile))
        except PathFindingError as error:
            # ⛔ CAUGHT BY NAME. `PathFindingError` is a bare `RuntimeError`, so an unguarded call
            # would escape every `except BotModeError` handler as a raw traceback.
            refusals.append((tile, f"{type(error).__name__}: {str(error)[:60]}"))
            continue
        reached = tile
        try:
            waypoints = len(path)
        except TypeError:  # an unsized path object is still a PATH — the absence of a raise is the
            # reading; the length is only telemetry.
            waypoints = "<unsized>"
        break
    report["egress_reached"] = reached
    report["egress_waypoints"] = waypoints
    report["egress_refusals"] = refusals
    if reached is None:
        raise BotModeError(
            f"§Ch24 champion: the game is CLEARED and the bot stands on {here} in {VR._where()}, "
            f"but NONE of the map's {len(exits)} exit(s) {exits} can be reached — it cannot leave "
            f"the room. ‼ That is a landing, not an arrival: §Ch15, §Ch18 and §Ch19 all shipped "
            f"STRANDED while passing their own tests. refusals={refusals}")
    _take(report, "C-CANCONTINUE")

    # ⭐ THE DISCRIMINATOR, POINT 2: the chapter is genuinely finished. Compare with point 1 — if
    # `gated` is False there and True here while `flags_only` is True at BOTH, the extra conjuncts
    # are load-bearing and the simpler predicate would have mis-fired mid-chapter.
    report["_done_probe_at_end"] = _ch24_done_probe("at the end (chapter complete)")



def ch24_chapter_done() -> bool:
    """§Ch24 complete: the game is CLEARED **and the bot is out the other side**.

    ⛔⛔ **THE TWO FLAGS ALONE WOULD BE WRONG, AND THE DECOMP SAYS SO.** `setflag FLAG_IS_CHAMPION`
    is in `EverGrandeCity_HallOfFame_EventScript_SetGameClearFlags` and `FLAG_SYS_GAME_CLEAR` is set
    by `special GameClear` a few instructions later — **both inside the Hall of Fame script, BEFORE
    the credits and BEFORE the `SoftReset`** (verified 2026-09-25 by reading
    `data/scripts/hall_of_fame.inc` and `src/post_battle_event_funcs.c` directly).
    ⇒ a flags-only gate reads True for the whole HoF cutscene, the save, ~12,651 frames of credits,
    the reset AND the CONTINUE menu — a window in which the bot is mid-chapter and un-resumable.
    ‼ **THAT IS EXACTLY §Ch23's LESSON** (`victory_road.py`): *"the flag is set at LEG 5 OF 11 …
    grading the GATE on it would hand §Ch24 a run buried two floors underground."*
    ⇒ the READOUT answers *"which chapter is this run in"*; the GATE answers *"may the next segment
    start"*. Both are correct. Do not collapse them.

    THE CONJUNCTS:
      1. `IS_CHAMPION`     — RAM.
      2. `SYS_GAME_CLEAR`  — RAM.
      3. NOT standing on the Champion's room or the Hall of Fame — this is the conjunct that
         excludes the mid-chapter window above.
      4. A NON-EMPTY PARTY — the ~207-frame EWRAM wipe-and-reload window satisfies 1-3 and is not
         a finished chapter. Cheap, and it closes the one gap the others leave.

    ⛔⛔ **THERE IS DELIBERATELY NO `GameState.OVERWORLD` CONJUNCT, AND THAT IS A REVERSAL.** The
    first cut had one. It has NO discriminating power here and it opens a FALSE-NEGATIVE path: the
    post-game bot spends much of its life IN BATTLE (dex hunting), where `GameState` is not
    OVERWORLD — so the dispatch would read "chapter NOT done" on a CLEARED save.
    ‼ **AND A FALSE `False` IS THE EXPENSIVE DIRECTION HERE, NOT THE SAFE ONE.** `train_for_league`
    does NOT self-skip on a cleared game — only when nobody is below the floor — and the §Ch24 party
    carries mon under L65, so a false `False` GRINDS FOR HOURS and then re-enters a gauntlet the run
    has already won. That is precisely the hazard the dispatch's short-circuit exists to prevent.
    ⭐ The standing ruling was *"neither a bare flash read nor a SINGLE OVERWORLD conjunct"* — which
    forbids relying on OVERWORLD ALONE; it never required including it. The conjunct that actually
    discriminates is (3), and the arm proved it: at the instant the flags flip the bot is ON
    `EVER_GRANDE_CITY_HALL_OF_FAME`.
    ⚠ What OVERWORLD would have covered is already covered: the credits window is excluded by (3)
    (the bot is on the Hall of Fame map), and the SoftReset window is excluded because the FLAGS
    THEMSELVES read False mid-EWRAM-wipe — measured, accidentally, by a mis-placed probe.

    ⛔ **RAM, NEVER FLASH.** MEASURED on all five §Ch24 fixtures: RAM and flash DISAGREE
    (`SYS_GAME_CLEAR`/`IS_CHAMPION` RAM=False FLASH=True, with controls that agree), because the
    cartridge's save file carries a PREVIOUS cleared playthrough. A flash-backed gate would declare
    the chapter finished on a save that has never entered the League.

    ⚠ **DELIBERATELY NO POSITION CONJUNCT BEYOND (3).** §Ch23's predicate requires a POSITION and a
    BAG ITEM because both are its work product. §Ch24's end position is the player's BEDROOM and is
    **TRANSIENT** — the bot walks out of it into the post-game immediately ⇒ a "must be in the
    bedroom" conjunct would flip back to False the moment the next chapter took a step, re-entering
    a finished, unrepeatable chapter. The work product here is the CLEARED GAME itself, which is
    permanent (no `clearflag` for either flag exists anywhere in the decomp).
    """
    # ‼ ALL LOCAL. This module has no module-level `MapRSE` or `reraise_if_aborting`, and
    # `repro_undefined_names.py` caught both on the first pass — the same shape `victory_road.py`
    # records, where a missing module-level import became a NameError SWALLOWED by a broad except.
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag
    from modules.pokemon_party import get_party
    from modules.story import victory_road as VR
    from modules.story.early_game import reraise_if_aborting

    #: The maps §Ch24 is still INSIDE. Standing on one means the chapter is RUNNING, whatever the
    #: flags say — both are reached AFTER `IS_CHAMPION` has already been set.
    endgame_maps = (
        MapRSE.EVER_GRANDE_CITY_CHAMPIONS_ROOM,
        MapRSE.EVER_GRANDE_CITY_HALL_OF_FAME,
    )

    try:
        if not get_event_flag("IS_CHAMPION"):
            return False
        if not get_event_flag("SYS_GAME_CLEAR"):
            return False
        # (3) the conjunct that excludes the pre-reboot window the flags are already True in
        if any(VR._on_map(m) for m in endgame_maps):
            return False
        # (4) the EWRAM reload window
        if not [m for m in get_party() if m is not None and not getattr(m, "is_empty", False)]:
            return False
        return True
    except Exception as error:  # noqa: BLE001 - an unreadable state is NOT a finished chapter
        # ⚠ FALSE here is the CONSERVATIVE answer, not a free one: it re-enters §Ch24, and
        # `train_for_league` will GRIND any mon under the floor. It is still the right default for
        # an UNREADABLE state — claiming a cleared game on a failed read would skip the one chapter
        # in the tree that cannot be repeated — but do not write this off as harmless.
        reraise_if_aborting(error)
        return False

#: The readings `cross_to_the_champions_door` publishes. ⛔ THE DRIVER IMPORTS THIS.
CROSS_READINGS = (
    "X-PREMISE",    # in DRAKE'S ROOM, Drake beaten, not yet Champion
    "X-DISMISSED",  # the parked victory msgbox is cleared and we are controllable
    "X-INHALL4",    # through Drake's exit door onto HALL4
    "X-ATDOOR",     # standing on (5,3) — ONE TILE SHORT of the Champion's door
)


def cross_to_the_champions_door(report=None, *, dismiss_budget: int = 3_000,
                                walk_frames: int = 40_000,
                                approach_frames: int = 60_000) -> Generator:
    """§Ch24 — DRAKE'S ROOM → HALL4 `(5,3)`: the last leg that can still be undone.

    ⭐ **IT ENDS ONE TILE SHORT OF THE POINT OF NO RETURN, AND THAT IS THE WHOLE DESIGN.**
    `fight_one_room` leaves the bot in DRAKE'S ROOM post-victory; `fight_the_champion` begins at
    HALL4 `(5,3)`. This is the join, and it deliberately stops where a refusal is still free.

    ⛔⛔ **IT DOES NOT HEAL.** The last heal in the game belongs to `fight_the_champion`'s S1, at the
    door, because that is the latest possible moment — healing here would waste the window on
    whatever the 31-tile walk costs. ‼ One heal, one place, and the champion leg owns it.

    ⛔ **TWO DIFFERENT MOVEMENT PRIMITIVES, AND THE DIFFERENCE IS LOAD-BEARING:**
    * Drake's exit door is crossed with `_pass_through_door` — that door is one we WANT to cross,
      and the helper works by making the warp the navigation TARGET.
    * The approach to `(5,3)` uses `navigate_to`, which is MEASURED at 30 waypoints ending
      `is_warp=False` and whose own docstring states that warps will not be used as intermediate
      steps. ⇒ it cannot wander onto `(5,2)`.
    ‼ Using `_pass_through_door` for the second hop would make the CHAMPION'S DOOR a destination —
    the exact trap the tripwire below exists for.

    ⚠ HALL4 is **31 tiles**, roughly 3× every other hall, which is why the approach budget is large.
    """
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag
    from modules.modes.util.walking import navigate_to
    from modules.player import player_avatar_is_controllable
    from modules.story import victory_road as VR
    from modules.story.early_game import (
        _check_abort,
        _pass_through_door,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    report = report if report is not None else {}
    report.setdefault("readings", set())

    DRAKE = MapRSE.EVER_GRANDE_CITY_DRAKES_ROOM
    HALL4 = MapRSE.EVER_GRANDE_CITY_HALL4

    # ---- STEP 0: THE TRIPWIRE -------------------------------------------------------------------
    # ⛔⛔ A CONSTANT-EDIT GUARD, PORTED FROM `Ch24Hall4Mode`. If someone ever "simplifies" the two
    # tiles into one, this leg would walk the bot straight through the point of no return with
    # nothing built to catch it. The check is free; the failure it prevents is unrecoverable.
    if tuple(CHAMPION_STAND_TILE) == tuple(CHAMPION_DOOR_TILE):
        raise BotModeError(
            f"§Ch24 cross: CHAMPION_STAND_TILE {CHAMPION_STAND_TILE} has been set equal to "
            f"CHAMPION_DOOR_TILE {CHAMPION_DOOR_TILE}. ⛔ Stepping there starts an unavoidable, "
            f"un-fleeable Champion fight. Refusing before a single button.")

    # ---- STEP 1: PREMISE ------------------------------------------------------------------------
    # ‼ THREE CONJUNCTS. `not IS_CHAMPION` is what makes this non-vacuous: pointed at a run that has
    # already cleared the game it must REFUSE rather than claim a crossing it did not make.
    conj = {}
    try:
        conj["in_drakes_room"] = bool(VR._on_map(DRAKE))
        conj["drake_beaten"] = get_event_flag("DEFEATED_ELITE_4_DRAKE") is True
        conj["not_champion_yet"] = get_event_flag("IS_CHAMPION") is False
    except Exception as error:  # noqa: BLE001 - an unreadable premise is a refusal, not a guess
        reraise_if_aborting(error)
        raise BotModeError(f"§Ch24 cross: premise unreadable: {type(error).__name__}: {error}")
    report["premise"] = dict(conj)
    report["start_at"] = (str(VR._where()), VR._here_tile())
    if not all(conj.values()):
        raise BotModeError(
            f"§Ch24 cross: PREMISE FAILED {conj} at {VR._where()}. This leg joins "
            f"`fight_one_room`'s end state to `fight_the_champion`'s premise; it does not navigate "
            f"into the gauntlet.")
    _take(report, "X-PREMISE")

    # ---- STEP 2: DISMISS DRAKE'S PARKED VICTORY MSGBOX ------------------------------------------
    # ⛔ **B, NOT A** — the defeat speech is a plain msgbox chain and A can re-open the interaction.
    # On a DUTY CYCLE, because holding a button every frame never produces the JOY_NEW edge a Gen-3
    # `waitbuttonpress` needs.
    dismissed = False
    for frame in range(dismiss_budget):
        _check_abort()
        try:
            controllable = bool(player_avatar_is_controllable())
        except Exception as error:  # noqa: BLE001 - a raise mid-transition IS the "not yet" answer
            reraise_if_aborting(error)
            controllable = False
        if get_game_state() is GameState.OVERWORLD and controllable:
            dismissed = True
            break
        if frame % 6 == 0:
            context.emulator.press_button("B")
        yield
    report["dismissed"] = dismissed
    if not dismissed:
        raise BotModeError(
            f"§Ch24 cross: Drake's victory msgbox did not clear within {dismiss_budget} frames at "
            f"{VR._where()}. Walking while a script holds input presses into a locked overworld.")
    # ‼ THE SETTLE IS LOAD-BEARING. The loop above exits on a SINGLE controllable reading, which
    # FLICKERS through a transition — and the very next step drives a door.
    yield from wait_until_truly_controllable()
    _take(report, "X-DISMISSED")

    # ---- STEP 3: DRAKE'S ROOM -> HALL4 ----------------------------------------------------------
    yield from _yield_bounded_by_frames(
        _pass_through_door(ROOM_EXIT_DOOR, tuple(DRAKE.value)), walk_frames)
    yield from wait_until_truly_controllable()
    if not VR._on_map(HALL4):
        raise BotModeError(
            f"§Ch24 cross: tried to leave DRAKE'S ROOM but we are at {VR._where()}, not HALL4. "
            f"⛔ Do NOT retry backward — every return warp in the interior is inert.")
    report["hall4_landing"] = (str(VR._where()), VR._here_tile())
    _take(report, "X-INHALL4")

    # ---- STEP 4: THE 31-TILE APPROACH, STOPPING ONE TILE SHORT ----------------------------------
    yield from _yield_bounded_by_frames(
        navigate_to(HALL4, tuple(CHAMPION_STAND_TILE)), approach_frames)
    yield from wait_until_truly_controllable()
    # ‼ ASSERT BOTH HALVES. "On HALL4" alone would pass while standing anywhere in a 31-tile hall,
    # including — catastrophically — on `(5,2)`. The TILE is the half that matters.
    here = tuple(VR._here_tile())
    report["end_at"] = (str(VR._where()), here)
    if not VR._on_map(HALL4) or here != tuple(CHAMPION_STAND_TILE):
        raise BotModeError(
            f"§Ch24 cross: meant to stop on HALL4 {CHAMPION_STAND_TILE} but we are at "
            f"{VR._where()} {here}. ⛔ If that tile is {CHAMPION_DOOR_TILE} the run has ALREADY "
            f"committed to the Champion fight and this refusal is far too late — read it as a bug "
            f"in the approach, not as a recoverable state.")
    _take(report, "X-ATDOOR")


#: ⭐ THE ROOM PAIRS, IN PRODUCTION — `(from_room, hall, to_room, victory_flag)`.
#: ⛔ THIS TABLE LIVED IN THE HARNESS DRIVER UNTIL 2026-09-25, WHICH MEANT THE ORDER OF THE ELITE
#: FOUR WAS A TEST-ONLY FACT. A sequencer cannot import its own route from a test file.
#: ‼ THREE ENTRIES, NOT FOUR: the fourth fight (Drake) is won by the THIRD pair, and ROOM 5 IS NOT
#: IN HERE AT ALL — `#24-leg2spec` rules that the Champion is a separate leg with its own grade.
GAUNTLET_PAIRS = (
    ("sidney", "EVER_GRANDE_CITY_SIDNEYS_ROOM", "EVER_GRANDE_CITY_HALL1",
     "EVER_GRANDE_CITY_PHOEBES_ROOM", "DEFEATED_ELITE_4_PHOEBE"),
    ("phoebe", "EVER_GRANDE_CITY_PHOEBES_ROOM", "EVER_GRANDE_CITY_HALL2",
     "EVER_GRANDE_CITY_GLACIAS_ROOM", "DEFEATED_ELITE_4_GLACIA"),
    ("glacia", "EVER_GRANDE_CITY_GLACIAS_ROOM", "EVER_GRANDE_CITY_HALL3",
     "EVER_GRANDE_CITY_DRAKES_ROOM", "DEFEATED_ELITE_4_DRAKE"),
)

#: The readings `run_the_gauntlet` publishes. ⛔ THE DRIVER IMPORTS THIS.
GAUNTLET_READINGS = (
    "G-PREPARED",  # ready OUTSIDE, inside the lobby, guards moved, standing on (9,3)
    "G-ENTERED",   # crossed (9,1), beat SIDNEY, standing in his room post-victory
    "G-PAIR1",     # SIDNEY -> PHOEBE
    "G-PAIR2",     # PHOEBE -> GLACIA
    "G-PAIR3",     # GLACIA -> DRAKE
    "G-ATDOOR",    # HALL4 (5,3), one tile short of the Champion
    "G-CLEARED",   # WALLACE beaten, the game cleared, and the bot is usable again
)


def run_the_gauntlet(report=None, *, floor: int = CH24_LEVEL_FLOOR,
                     skip_prepare: bool = False) -> Generator:
    """§Ch24 — THE WHOLE CHAPTER: from outside the League to a cleared game, in ONE run.

    ⭐⭐ **THIS IS WHAT "THE BOT COMPLETES THE ELITE FOUR" ACTUALLY MEANS.** Five legs existed and
    every seam between them had been proven pairwise — but *"each piece works"* is not *"the chain
    works"*, and this project has been burned before by exactly that distinction. Nothing before
    this function ever ran lobby → Sidney → three pairs → Champion as a single trajectory.

    THE CHAIN, and each step's own leg owns its premise, its bounds and its refusal:
      1. `prepare_and_open_the_league(floor=)` — get ready **OUTSIDE**, walk in, talk the guards
         aside, stop on `(9,3)`. ⛔ Readiness is decided out here because all three remedies are
         MEASURED non-functional from inside the lobby.
      2. `enter_the_league()` — cross `(9,1)` (**the point of no return**) and beat SIDNEY.
      3. `fight_one_room()` ×3 over `GAUNTLET_PAIRS` — Phoebe, Glacia, Drake.
      4. `cross_to_the_champions_door()` — the 31-tile HALL4 walk, stopping one tile short.
      5. `fight_the_champion()` — Wallace, the Hall of Fame, the save, the credits, the reboot.

    ⛔⛔ **IT DOES NOT CATCH, RETRY OR RECOVER, AND THAT IS DELIBERATE.** From step 2 onward the zone
    is SEALED: every backward warp is inert, there is no Fly, no Escape Rope and no nurse. A
    sequencer that swallowed a leg's failure would convert a clean, named refusal into a bot
    standing still in a corridor it cannot leave. ⇒ **every failure propagates**, and the only
    recovery worth having is the one that happens BEFORE step 2.
    ‼ Re-entry after a loss is `#24-restockleg`'s job (USER RULING 12: restock, then retry) and it
    is UNBUILT — so today a loss ends the run, loudly.

    ⚠ **`floor` IS THE READINESS BAR, AND AT PRODUCTION'S 65 STEP 1 CAN TRAIN FOR HOURS.** Drive it
    at a low floor to test the CHAIN; the training half is proven separately by `--driver ch24train`.
    """
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag
    from modules.story import victory_road as VR
    from modules.story.early_game import _check_abort, reraise_if_aborting

    report = report if report is not None else {}
    report.setdefault("readings", set())
    report["pairs"] = []

    def _merge(sub: dict, key: str) -> None:
        """Keep every sub-leg's readings, but NEVER let them collide.

        ⛔ `fight_one_room` publishes `R1-*` and runs THREE times, so a flat merge would show one
        `R1-WON` whether one pair ran or all three — a set cannot count. ⇒ the sub-readings are
        stored PER STAGE under `key`, and only the stage's own `G-*` reading is taken.
        """
        report[key] = {k: v for k, v in sub.items() if k != "readings"}
        report.setdefault("sub_readings", {})[key] = sorted(sub.get("readings", set()))

    # ---- 1. READY OUTSIDE, THEN INTO THE LOBBY --------------------------------------------------
    if not skip_prepare:
        _check_abort()
        prep: dict = {}
        yield from prepare_and_open_the_league(prep, floor=floor)
        _merge(prep, "prepare")
    _take(report, "G-PREPARED")

    # ---- 2. THE POINT OF NO RETURN, AND SIDNEY --------------------------------------------------
    _check_abort()
    bridge: dict = {}
    yield from enter_the_league(bridge)
    _merge(bridge, "bridge")
    _take(report, "G-ENTERED")

    # ---- 3. THE ROOM LOOP — THREE PAIRS ---------------------------------------------------------
    # ⭐ A LOOP, NOT THREE BESPOKE BRANCHES: `(6,2)` and `(5,2)` are MEASURED uniform across every
    # room and hall, and all three pairs have been driven through this same function.
    for index, (name, from_room, hall, to_room, flag) in enumerate(GAUNTLET_PAIRS, start=1):
        _check_abort()
        pair: dict = {}
        yield from fight_one_room(
            pair,
            from_room=getattr(MapRSE, from_room),
            hall=getattr(MapRSE, hall),
            to_room=getattr(MapRSE, to_room),
            victory_flag=flag,
        )
        _merge(pair, f"pair{index}_{name}")
        report["pairs"].append({"name": name, "flag": flag,
                                "won": pair.get("end_flag"), "at": pair.get("end_at")})
        _take(report, f"G-PAIR{index}")

    # ---- 4. THE APPROACH -------------------------------------------------------------------------
    _check_abort()
    cross: dict = {}
    yield from cross_to_the_champions_door(cross)
    _merge(cross, "cross")
    _take(report, "G-ATDOOR")

    # ---- 5. WALLACE, AND THE END OF THE GAME -----------------------------------------------------
    _check_abort()
    champ: dict = {}
    yield from fight_the_champion(champ)
    _merge(champ, "champion")
    report["heal_ready"] = champ.get("heal_ready")

    # ⛔ THE FINAL ASSERTION IS ON THE FLAGS, NOT ON "the champion leg returned". That leg already
    # asserts its own ten readings — but this one is the CHAPTER's claim, and a chapter that says
    # "done" while `IS_CHAMPION` is False would poison every downstream predicate.
    try:
        cleared = bool(get_event_flag("IS_CHAMPION")) and bool(get_event_flag("SYS_GAME_CLEAR"))
    except Exception as error:  # noqa: BLE001 - an unreadable flag is NOT a licence to claim a win
        reraise_if_aborting(error)
        cleared = False
    report["cleared"] = cleared
    report["end_at"] = (str(VR._where()), VR._here_tile())
    if not cleared:
        raise BotModeError(
            f"§Ch24 gauntlet: the champion leg returned but IS_CHAMPION/SYS_GAME_CLEAR do not both "
            f"read True at {VR._where()}. ⛔ Refusing to report a cleared chapter on flags that say "
            f"otherwise.")
    _take(report, "G-CLEARED")
