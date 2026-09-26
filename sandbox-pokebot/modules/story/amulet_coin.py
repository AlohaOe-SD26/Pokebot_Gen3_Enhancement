"""USER RULING 17 (2026-09-26): fetch Mom's AMULET COIN after badge 5 and give it to a battler.

WHY. 3 of 3 organic runs that reached §Ch23's League shop on 2026-09-26 were refused on money (₽21,940 / ₽33,492 /
₽41,412 against the ₽54,300 basket; whiteouts halve the wallet) — `ai-research-notes/2026-09-26-ch23money-RECON.md`.
The Amulet Coin doubles trainer prize money for the rest of the game. The user ruled: fetch it after badge 5, and let a
battler that actually ENTERS battles hold it.

THE MECHANICS (decomp, read 2026-09-26 — `data/scripts/players_house.inc` `PlayersHouse_1F_EventScript_Mom`):
  * `VAR_LITTLEROOT_HOUSES_STATE_{MAY,BRENDAN} == 4` ⇒ "don't push yourself" and nothing else. ⭐ That value (and the
    S.S.-Ticket/Lati-TV on-frame scene at state 3, which holds a B-proof MULTICHOICE) is set only by
    `data/scripts/hall_of_fame.inc` ⇒ post-game ONLY; at badge 5 neither fires. The leg still READS the var and
    refuses at 3 or 4 rather than walking into a multichoice it cannot answer.
  * `FLAG_HAS_MATCH_CALL` set ⇒ `TryRegisterMom`: with `FLAG_ENABLE_MOM_MATCH_CALL` UNSET the first talk only
    registers Mom (two msgboxes + a fanfare) and sets it — no coin yet;
  * with it SET: `FLAG_BADGE05_GET` ∧ ¬`FLAG_RECEIVED_AMULET_COIN` ⇒ `giveitem ITEM_AMULET_COIN` then
    `setflag FLAG_RECEIVED_AMULET_COIN` (a full bag shows "bag is full" and the flag stays unset);
  * otherwise Mom heals. No yes/no prompt anywhere ⇒ riding the dialog with B is safe.
  * the ×2 (`src/battle_util.c:3294-3296`): `HOLD_EFFECT_DOUBLE_PRIZE` sets `moneyMultiplier = 2` only when a
    PLAYER-side holder switches in (a lead counts) ⇒ the holder must be a mon that is sent out.

THE HOLDER (v1): the highest-level battler — the mon most often sent out (recon replay: 55 % of won battles, 47/58
bosses vs 27 % for the badge-5 lead); ties prefer an empty held slot. Keyed by PID + species (Shedinja shares
Ninjask's PID). ⚠ A static holder was measured SHORT of the basket on one whiteout-heavy replay (the recon's
adversarial angle) — RULINGS 16 and 18 are the other halves; "move the coin to the entrant" is a separate item.

FAILS SOFT: a coin problem logs a named `report["amulet_coin"]` reason and returns — a coin is worth money, not a
run. The caller keeps its own guard on the END POSITION (Petalburg, where Segment 13a's walk starts).
"""
from __future__ import annotations

import os
from typing import Generator

from modules.context import context
from modules.modes._interface import BotModeError

#: The readings this leg publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
AMULET_COIN_READINGS = (
    "AC-HOUSE",       # standing inside the player's own house
    "AC-REGISTERED",  # ENABLE_MOM_MATCH_CALL set (by this leg's talk, or already)
    "AC-RECEIVED",    # RECEIVED_AMULET_COIN set AND the bag's coin count went UP (both, not either)
    "AC-GIVEN",       # the planned holder (PID + species) holds the Amulet Coin — read back from the party
    "AC-BACK",        # in Petalburg City again
)

#: Real-emulator-frame budgets (`_yield_bounded_by_frames`, so battles on the way count).
AMULET_COIN_BUDGET = 40_000   # the whole errand; the recon estimates 7-16k
TALK_BUDGET = 6_000           # one approach + one dialog
GIVE_BUDGET = 4_000
RETURN_BUDGET = 30_000
#: Register, receive, and two spares for a missed A (a spare talk after the coin only heals — harmless).
MAX_TALKS = 4
#: `LOCALID_PLAYERS_HOUSE_1F_MOM` — the same id in both houses (the recon read both 1F `map.json`s).
MOM_LOCAL_ID = 1
#: Littleroot's two house doors (the decomp's LittlerootTown warps; the recon's map read).
HOUSE_DOOR = {"male": (5, 8), "female": (14, 8)}
#: `gBagPosition.pocket` value of the ITEMS pocket (`include/item_menu.h` ITEMS_POCKET = 0).
ITEMS_POCKET_INDEX = 0
FLAGS = ("HAS_MATCH_CALL", "ENABLE_MOM_MATCH_CALL", "RECEIVED_AMULET_COIN", "BADGE05_GET")
PETALBURG_ARRIVAL = (20, 18)   # `travel_to_petalburg`'s own proven target


def _flag(name: str) -> bool:
    from modules.memory import _event_flags, get_event_flag

    # ⛔ `get_event_flag` returns False FOREVER for a phantom name (`memory.py`), which would make this leg talk to
    # Mom until the cap and then report "Mom did not hand it over". Raise instead; the call site catches.
    if name not in _event_flags:
        raise BotModeError(f"amulet coin: flag {name!r} is not in the event-flag table")
    return bool(get_event_flag(name))


def _houses_state() -> "tuple[int, int] | None":
    """Both Littleroot house-state vars, or None if either is unreadable. ⛔ `get_event_var` returns -1 for an
    unknown name, which would read as "below 3" — so -1 is refused as unreadable, never passed as a value."""
    try:
        from modules.memory import get_event_var

        pair = get_event_var("LITTLEROOT_HOUSES_STATE_MAY"), get_event_var("LITTLEROOT_HOUSES_STATE_BRENDAN")
    except Exception:  # noqa: BLE001 - an unreadable var is REPORTED (None) and refused by the caller, not assumed
        return None
    return None if min(pair) < 0 else pair


def _coin():
    from modules.items import get_item_by_name

    return get_item_by_name("Amulet Coin")


def _bag_coins() -> int:
    from modules.items import get_item_bag

    return get_item_bag().quantity_of(_coin())


def coin_holder() -> "tuple[int, str] | None":
    """`(pid, species)` of the party member holding the Amulet Coin, or None."""
    from modules.pokemon_party import get_party

    for mon in get_party():
        if mon is None or getattr(mon, "is_egg", False):
            continue
        held = getattr(mon, "held_item", None)
        if held is not None and getattr(held, "name", "") == "Amulet Coin":
            return mon.personality_value, mon.species.name
    return None


def pick_holder(party) -> "int | None":
    """PURE: the party index to hold the coin — highest level, ties prefer an EMPTY held slot, never an egg."""
    best, key = None, None
    for i, mon in enumerate(party):
        if mon is None or getattr(mon, "is_egg", False):
            continue
        k = (mon.level, getattr(mon, "held_item", None) is None)
        if key is None or k > key:
            best, key = i, k
    return best


def amulet_coin_pending() -> bool:
    """Anything left to do? Badge 5 held AND (the coin not received, OR received but in the bag, not held)."""
    if not _flag("BADGE05_GET"):
        return False
    if not _flag("RECEIVED_AMULET_COIN"):
        return True
    return coin_holder() is None and _bag_coins() > 0


def _items_cursor() -> "tuple[int, int]":
    """(pocket, slot) the bag cursor is on, from `gBagPosition` — the offsets `pokemon_league._bag_cursor_slot`
    already reads. (-1, -1) if unreadable; the caller refuses on that."""
    try:
        from modules.memory import read_symbol, unpack_uint16

        pocket_index = read_symbol("gBagPosition", offset=0x05, size=1)[0]
        cursor = unpack_uint16(read_symbol("gBagPosition", offset=8 + (pocket_index * 2), size=2))
        scroll = unpack_uint16(read_symbol("gBagPosition", offset=18 + (pocket_index * 2), size=2))
        return pocket_index, cursor + scroll
    except Exception:  # noqa: BLE001 - (-1, -1) makes the caller REFUSE; it never passes silently
        return -1, -1


def _scroll_to_items_pocket_verified(item) -> Generator:
    """Put the bag cursor on `item` (ITEMS pocket) and PROVE it before anything presses A.

    ⛔ `scroll_to_item_in_bag` was MEASURED leaving the cursor on the wrong item in the TM pocket (2026-09-05,
    `pokemon_league.scroll_to_tm_verified`). Pressing GIVE on the wrong item would hand a battler a Potion — so the
    same closed-loop correction, against `get_item_bag().items`.
    """
    from modules.items import get_item_bag
    from modules.modes.util.items import scroll_to_item_in_bag

    yield from scroll_to_item_in_bag(item)
    names = [s.item.name for s in get_item_bag().items]
    if item.name not in names:
        raise BotModeError(f"give: {item.name} is not in the ITEMS pocket ({names}).")
    want = names.index(item.name)
    for _ in range(120):
        pocket, slot = _items_cursor()
        if pocket != ITEMS_POCKET_INDEX or slot < 0:
            raise BotModeError(f"give: the bag cursor reads pocket {pocket} slot {slot}, not the ITEMS pocket.")
        if slot == want:
            return
        context.emulator.press_button("Down" if slot < want else "Up")
        yield
        yield
        yield
    raise BotModeError(f"give: could not put the bag cursor on {item.name} (slot {want}); it reads "
                       f"{_items_cursor()}. Refusing to press A on an unverified item.")


def _leave_menus() -> Generator:
    """Back out to a controllable overworld from anywhere in the bag / party menu / a message. Bounded."""
    from modules.memory import GameState, get_game_state
    from modules.menuing import is_fade_active
    from modules.modes.util.sleep import wait_for_n_frames
    from modules.modes.util.tasks_scripts import wait_for_task_to_start_and_finish
    from modules.story.early_game import wait_until_truly_controllable
    from modules.tasks import task_is_active

    for _ in range(60):
        state = get_game_state()
        if state is GameState.OVERWORLD and not is_fade_active() and not task_is_active("Task_ShowStartMenu"):
            break
        if state is GameState.BAG_MENU and not is_fade_active():
            # ⭐ The proven exit (`pokemon_league.heal_party_from_bag`): B until the start menu, B until it closes.
            yield from wait_for_task_to_start_and_finish("Task_ShowStartMenu", "B")
            continue
        context.emulator.press_button("B")
        yield from wait_for_n_frames(8)
    yield from wait_until_truly_controllable()


def give_item_to_party_member(item, party_index: int, report: dict) -> Generator:
    """GIVE `item` (ITEMS pocket) to the party member at `party_index`, from the overworld, via the BAG.

    THE CHAIN (decomp, read 2026-09-26):
      `sContextMenuItems_ItemsPocket` (`src/item_menu.c:286`) is the 2×2 grid {USE, GIVE / TOSS, CANCEL}, cursor on
      USE; DPAD_RIGHT moves it only from an even index (`:1741`), so a second Right is a no-op ⇒ pressing it twice is
      safe. A runs `ItemMenu_Give` (`:1921`) → `CB2_ChooseMonToGiveItem` (`src/party_menu.c:5359`,
      `Task_HandleChooseMonInput`, exit `CB2_ReturnToBagMenu`) → A on the slot → `TryGiveItemOrMailToSelectedMon`
      (`:5366`): an empty slot gives at once; an occupied one asks to switch — `Task_HandleSwitchItemsFromBagYesNoInput`
      (`:5478`), cursor on YES — and either way the party menu closes back to the BAG.
    ⭐ The party menu opening PROVES GIVE was chosen: USE on an Amulet Coin (`ItemUseOutOfBattle_CannotUse`) never
    opens it. ⛔ A sibling of `pokemon_league.use_item_on_party_member`, NOT an edit of it — that function's USE wait
    is a measured-fragile line (`#24-itemcontextplural`).
    """
    from modules.items import get_item_bag
    from modules.memory import GameState, get_game_state
    from modules.menuing import StartMenuNavigator, is_fade_active
    from modules.modes.util.sleep import wait_for_n_frames
    from modules.story.pokemon_league import CHOOSE_MON_TASK, ITEM_CONTEXT_TASKS, _slot_cursor
    from modules.tasks import get_tasks, task_is_active

    if get_item_bag().quantity_of(item) <= 0:
        raise BotModeError(f"give: the bag holds no {item.name}.")
    if get_game_state() is not GameState.BAG_MENU:
        yield from StartMenuNavigator("BAG").step()
    yield from _scroll_to_items_pocket_verified(item)

    # ---- open the context menu (the teach path's proven START-only loop, `pokemon_league` ~:560) ----------------
    opened = None
    for _ in range(75):
        opened = next((t for t in ITEM_CONTEXT_TASKS if task_is_active(t)), None)
        if opened:
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)
    report["give_context_task"] = opened
    if opened != "Task_ItemContext_MultipleRows":
        raise BotModeError(f"give: the {item.name} context task is {opened!r}, not the 2x2 grid "
                           f"(live tasks {[k.symbol for k in get_tasks()]}). Refusing to press on an unverified menu.")

    # ---- Right, Right (idempotent) → GIVE → A ------------------------------------------------------------------
    for _ in range(2):
        context.emulator.press_button("Right")
        yield from wait_for_n_frames(6)
    context.emulator.press_button("A")
    yield
    chose_mon = False
    for _ in range(300):
        if task_is_active(CHOOSE_MON_TASK):
            chose_mon = True
            break
        yield
    report["give_party_menu"] = chose_mon
    if not chose_mon:
        raise BotModeError(f"give: `{CHOOSE_MON_TASK}` never opened after GIVE on {item.name} — the cursor was not on "
                           f"GIVE (USE on this item opens no party menu).")

    # ---- cursor to the slot (closed loop, bounded) then A ------------------------------------------------------
    for _ in range(60):
        cursor = _slot_cursor()
        if cursor == party_index:
            break
        context.emulator.press_button("Down" if cursor < party_index else "Up")
        yield from wait_for_n_frames(4)
    else:
        raise BotModeError(f"give: could not move the party cursor to slot {party_index} (it reads {_slot_cursor()}).")
    report["give_slot_cursor"] = _slot_cursor()
    context.emulator.press_button("A")
    yield from wait_for_n_frames(4)

    # ---- the "given to hold" text, or the switch yes/no (A = YES, the default) — until the BAG is back ----------
    for _ in range(300):
        if task_is_active("Task_HandleSwitchItemsFromBagYesNoInput"):
            report["give_switched"] = True
        if get_game_state() is GameState.BAG_MENU and not is_fade_active() and not task_is_active(CHOOSE_MON_TASK):
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)
    else:
        raise BotModeError(f"give: never returned to the bag after giving {item.name}.")


def fetch_amulet_coin(report: "dict | None" = None) -> Generator:
    """RULING 17's leg: Petalburg → Littleroot → Mom (register, then the coin) → give it → back to Petalburg.

    Never raises for a coin problem: records `report["amulet_coin"]` and returns. Every step is frame-bounded; the
    caller bounds the whole leg by `AMULET_COIN_BUDGET` and re-checks Petalburg afterwards.
    """
    from modules.console import console
    from modules.map_data import MapRSE
    from modules.modes.util.global_navigation import navigate_to_anywhere
    from modules.modes.util.higher_level_actions import talk_to_npc
    from modules.player import get_player
    from modules.pokemon_party import get_party
    from modules.story.early_game import (
        _enter_warp_by_navigation,
        _navigate_leg,
        _ride_out_scripted_scene,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )
    from modules.story.victory_road import _on_map, _where

    report = report if report is not None else {}
    report.setdefault("readings", set())
    report.setdefault("order", [])

    def _take(reading: str) -> None:
        if reading not in report["readings"]:
            report["order"].append(reading)
        report["readings"].add(reading)

    def _soft(reason: str) -> None:
        report["amulet_coin"] = reason
        console.print(f"[yellow]Story: Amulet Coin — {reason} Continuing without it (RULING 17 fails soft).[/]")

    def _flags() -> dict:
        return {f: _flag(f) for f in FLAGS}

    yield from wait_until_truly_controllable()
    report["frame_start"] = context.emulator.get_frame_count()
    report["flags_start"] = _flags()
    report["coins_start"] = _bag_coins()
    report["holder_start"] = coin_holder()
    report["houses_state"] = _houses_state()
    if report["holder_start"] is not None:
        report["amulet_coin"] = "already held"
        _take("AC-GIVEN")
        return
    if not report["flags_start"]["BADGE05_GET"]:
        _soft("badge 5 is not held yet.")
        return

    need_coin = not report["flags_start"]["RECEIVED_AMULET_COIN"]
    if need_coin:
        if not report["flags_start"]["HAS_MATCH_CALL"]:
            _soft("FLAG_HAS_MATCH_CALL is unset, so Mom would only heal (decomp gate).")
            return
        if report["houses_state"] is None or max(report["houses_state"]) >= 3:
            # ⛔ state 3 arms the S.S.-Ticket scene's B-proof multichoice; 4 makes Mom say one line. Post-game only.
            _soft(f"the Littleroot houses state is {report['houses_state']} (3+ is post-game; Mom gives nothing).")
            return
        from modules.items import get_item_bag

        if not get_item_bag().has_space_for(_coin()):
            _soft("the ITEMS pocket has no room for the coin (Mom would say the bag is full).")
            return

        # ---- the walk south. ⛔ Per-leg: the global navigator LOOPS on Route 101 (`travel_to_petalburg`). ------
        gender = get_player().gender
        report["gender"] = gender
        house = (MapRSE.LITTLEROOT_TOWN_BRENDANS_HOUSE_1F if gender == "male"
                 else MapRSE.LITTLEROOT_TOWN_MAYS_HOUSE_1F)
        try:
            if not _on_map(house):
                if not (_on_map(MapRSE.LITTLEROOT_TOWN) or _on_map(MapRSE.ROUTE101)):
                    yield from navigate_to_anywhere(MapRSE.OLDALE_TOWN, (6, 9))
                if not _on_map(MapRSE.LITTLEROOT_TOWN):
                    yield from _navigate_leg(MapRSE.ROUTE101, (9, 9))
                    yield from _navigate_leg(MapRSE.LITTLEROOT_TOWN, (6, 9))
                yield from _enter_warp_by_navigation(lambda: _on_map(house), MapRSE.LITTLEROOT_TOWN,
                                                     HOUSE_DOOR[gender], tries=6, label="player's house")
            yield from wait_until_truly_controllable()
        except Exception as error:  # noqa: BLE001 - a failed walk is a NAMED soft failure; the caller re-checks Petalburg
            reraise_if_aborting(error)
            _soft(f"could not reach the house ({type(error).__name__}: {str(error)[:120]}).")
            yield from _return_to_petalburg(report, _take)
            return
        if not _on_map(house):
            _soft(f"expected to be inside {house.name} but at {_where()}.")
            yield from _return_to_petalburg(report, _take)
            return
        _take("AC-HOUSE")

        # ---- the talks: each outcome PREDICTED from the flags before talking --------------------------------------
        max_talks = 1 if os.environ.get("POKEBOT_AMULET_FAULT_ONETALK") == "1" else MAX_TALKS
        talks = report.setdefault("talks", [])
        for _ in range(max_talks):
            before = _flags()
            if before["RECEIVED_AMULET_COIN"]:
                break
            coins_before = _bag_coins()
            predicted = "register" if not before["ENABLE_MOM_MATCH_CALL"] else "coin"
            try:
                finished = yield from _yield_bounded_by_frames(
                    _talk_to_mom(talk_to_npc, _ride_out_scripted_scene, wait_until_truly_controllable), TALK_BUDGET)
            except Exception as error:  # noqa: BLE001 - a failed approach is recorded per talk; the flags decide
                reraise_if_aborting(error)
                finished = f"{type(error).__name__}: {str(error)[:100]}"
            after = _flags()
            talks.append({"predicted": predicted, "finished": finished, "coins": (coins_before, _bag_coins()),
                          "registered": (before["ENABLE_MOM_MATCH_CALL"], after["ENABLE_MOM_MATCH_CALL"]),
                          "received": (before["RECEIVED_AMULET_COIN"], after["RECEIVED_AMULET_COIN"])})
            if after["ENABLE_MOM_MATCH_CALL"]:
                _take("AC-REGISTERED")
        final = _flags()
        report["flags_after_talks"] = final
        report["coins_after_talks"] = _bag_coins()
        if final["ENABLE_MOM_MATCH_CALL"]:
            _take("AC-REGISTERED")
        if not (final["RECEIVED_AMULET_COIN"] and report["coins_after_talks"] > report["coins_start"]):
            _soft(f"Mom did not hand over the coin after {len(talks)} talk(s) (RECEIVED="
                  f"{final['RECEIVED_AMULET_COIN']}, bag coins {report['coins_start']}→{report['coins_after_talks']}).")
            yield from _return_to_petalburg(report, _take)
            return
        _take("AC-RECEIVED")

    # ---- give it to the holder ------------------------------------------------------------------------------------
    party = get_party()
    idx = pick_holder(party)
    if idx is None:
        _soft("no party member can hold it.")
        yield from _return_to_petalburg(report, _take)
        return
    mon = party[idx]
    pid, species = mon.personality_value, mon.species.name
    report["frames_at_give"] = context.emulator.get_frame_count() - report["frame_start"]
    report["holder_planned"] = {"slot": idx, "mon": f"{species}#{pid:08X}", "level": mon.level,
                                "held_before": getattr(getattr(mon, "held_item", None), "name", None)}
    if os.environ.get("POKEBOT_AMULET_FAULT_NOGIVE") == "1":
        report["fault_nogive"] = True
        console.print("[magenta]Story: FAULT ARM POKEBOT_AMULET_FAULT_NOGIVE — not giving the Amulet Coin.[/]")
    else:
        try:
            report["give_finished"] = bool((yield from _yield_bounded_by_frames(
                give_item_to_party_member(_coin(), idx, report), GIVE_BUDGET)))
        except Exception as error:  # noqa: BLE001 - a failed give is NAMED below; the coin stays in the bag
            reraise_if_aborting(error)
            report["give_error"] = f"{type(error).__name__}: {str(error)[:200]}"
        yield from _leave_menus()
    holder = coin_holder()
    report["holder_end"] = None if holder is None else f"{holder[1]}#{holder[0]:08X}"
    if holder == (pid, species):
        _take("AC-GIVEN")
        report["amulet_coin"] = "given"
        console.print(f"[green]Story: {species} now holds the Amulet Coin (prize money x2 whenever it is sent out).[/]")
    else:
        _soft(f"the give did not land (holder now {report['holder_end']}; error {report.get('give_error')}).")

    yield from _return_to_petalburg(report, _take)


def _talk_to_mom(talk_to_npc, ride, controllable) -> Generator:
    """Approach Mom, press A, ride her script out. The caller bounds it (`TALK_BUDGET`)."""
    yield from talk_to_npc(MOM_LOCAL_ID)
    yield from ride("B")
    yield from controllable()


def _return_to_petalburg(report: dict, take) -> Generator:
    """End where Segment 13a starts — from ANY point of the errand, one stage per map actually reached.

    ⛔ Not `travel_to_petalburg()` whole: its first step aims at Littleroot, which from Route 102 would walk the run
    back SOUTH. Each stage below runs only if we are on the map it starts from; the Route 101 stretch is per-leg
    because the global navigator loops there.
    """
    from modules.map_data import MapRSE
    from modules.modes.util.global_navigation import navigate_to_anywhere
    from modules.story.early_game import (
        _navigate_leg,
        _yield_bounded_by_frames,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )
    from modules.story.victory_road import _on_map

    def _stages() -> Generator:
        if any(_on_map(m) for m in (MapRSE.LITTLEROOT_TOWN_BRENDANS_HOUSE_1F, MapRSE.LITTLEROOT_TOWN_MAYS_HOUSE_1F)):
            yield from navigate_to_anywhere(MapRSE.LITTLEROOT_TOWN, (6, 9))
        if _on_map(MapRSE.LITTLEROOT_TOWN):
            yield from _navigate_leg(MapRSE.ROUTE101, (9, 9))
        if _on_map(MapRSE.ROUTE101):
            yield from _navigate_leg(MapRSE.OLDALE_TOWN, (6, 9))
        yield from navigate_to_anywhere(MapRSE.PETALBURG_CITY, PETALBURG_ARRIVAL)

    if not _on_map(MapRSE.PETALBURG_CITY):
        try:
            report["return_finished"] = bool((yield from _yield_bounded_by_frames(_stages(), RETURN_BUDGET)))
        except Exception as error:  # noqa: BLE001 - the caller's guard on Petalburg reports this loudly
            reraise_if_aborting(error)
            report["return_error"] = f"{type(error).__name__}: {str(error)[:200]}"
        yield from wait_until_truly_controllable()
    if _on_map(MapRSE.PETALBURG_CITY):
        take("AC-BACK")


def run_ch12d(report: dict, at_petalburg, *, badge06: bool) -> Generator:
    """`_play`'s Segment 12d, whole — the gate, the bounded errand, a fallback walk back, and the telemetry line.

    ⭐ ONE FUNCTION SO THE DRIVER DRIVES PRODUCTION: `--driver amuletcoin` calls exactly this, and `_play` calls
    exactly this; `probe_amulet_coin.py` pins that `_play` does. `report["ran"]` tells the caller whether to guard.
    ⛔ GATED TO THE PETALBURG ERA (`not badge06` ∧ `at_petalburg()`): a post-Fortree re-entry must never walk back
    south — that is KI-97's shape. Not pending (coin already held, or badge 5 missing) ⇒ it does nothing.
    """
    from modules import debug_logger
    from modules.console import console
    from modules.story.early_game import _yield_bounded_by_frames, reraise_if_aborting

    report["ran"] = False
    if badge06 or not at_petalburg():
        report["amulet_coin"] = "out of era" if badge06 else "not in Petalburg"
        return
    try:
        if not amulet_coin_pending():
            report["amulet_coin"] = "nothing pending"
            return
        report["ran"] = True
        # `POKEBOT_AMULET_FAULT_BUDGET=<frames>` shrinks the budget so it EXPIRES mid-errand — the only way to drive
        # the two recovery steps below, which a healthy errand never reaches (registered in 29).
        budget = int(os.environ.get("POKEBOT_AMULET_FAULT_BUDGET") or AMULET_COIN_BUDGET)
        report["budget"] = budget
        report["finished"] = yield from _yield_bounded_by_frames(fetch_amulet_coin(report), budget)
    except Exception as error:  # noqa: BLE001 - RULING 17 fails soft; the caller's Petalburg guard stays hard
        reraise_if_aborting(error)
        report["error"] = f"{type(error).__name__}: {str(error)[:200]}"
    if report.get("finished") is False:
        # ⛔ An expired budget CLOSES the errand from outside — `fetch_amulet_coin`'s own `_leave_menus()` never runs,
        # so the bag or party menu can still be open (adversarial review, 2026-09-26). Close it, bounded, before any
        # walking: navigation cannot start from inside a menu.
        report["budget_expired"] = True
        try:
            yield from _yield_bounded_by_frames(_leave_menus(), 3_000)
        except Exception as error:  # noqa: BLE001 - recorded; the fallback walk and the caller's guard judge the rest
            reraise_if_aborting(error)
            report["leave_menus_error"] = f"{type(error).__name__}: {str(error)[:160]}"
    if report["ran"] and not at_petalburg():
        # The errand's budget can expire mid-walk (it closes the generator, return trip and all) — one more
        # bounded, map-aware walk back before the caller's guard judges the position.
        report["retry_return"] = True
        yield from _return_to_petalburg(report, lambda _reading: None)
    try:
        debug_logger.event(
            f"outcome={report.get('amulet_coin')!r} order={report.get('order')} "
            f"holder={report.get('holder_end') or report.get('holder_start')} talks={len(report.get('talks', []))} "
            f"finished={report.get('finished')} "
            f"error={report.get('error') or report.get('give_error') or report.get('return_error')}",
            category="AMULET_COIN")
    except Exception:  # noqa: BLE001 - telemetry must never break the story; a missing line is visible
        pass
    console.print(f"[dim]Story: Amulet Coin errand — {report.get('amulet_coin')}.[/]")
