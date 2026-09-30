"""USER RULING 18 (2026-09-26): buy the League basket's Sootopolis-sold lines EARLY, and RESERVE the basket until the
Elite Four.

WHY. 3 of 3 organic runs that reached §Ch23 leg 11 were refused on money (₽21,940 / ₽33,492 / ₽41,412 vs ₽54,300).
Every whiteout halves the wallet (`src/overworld.c:361`) and NOTHING in the bag (`DoWhiteOut` makes no bag call) —
so cash carried into the Juan attempts is cash at risk, and items are not. The user ruled "buy early with a reserve
lock" (`06`, RULING 18).

TWO PARTS, deliberately independent:

1. THE PURCHASE (`stock_basket_early`) — at the Sootopolis Mart, inside §Ch22's L1 AFTER the Poké Center heal (the
   only point where the bot is GUARANTEED to be in Sootopolis) and before the gym; the caller re-heals if the trip
   walked. Decomp (read by the recon; prices re-checked in `items.json`): Sootopolis sells Hyper Potion ₽1,200, Full
   Heal ₽600, Revive ₽1,500 — no badge gating; Full Restore is League-only. It buys only what is MISSING (RULING 16's
   rule), cheapest-to-leak first (Revive and Full Heal are never spent in battle today), keeps `CASH_FLOOR`, and
   FAILS OPEN: any problem is a named reason and the chapter continues to the heal and the gym exactly as before.
   It runs on every Juan attempt, so a whiteout's leftover cash is converted on the next attempt.

2. THE RESERVE (`filter_medicine_for_reserve`) — the in-battle item strategy sees `quantity − reserved` for every
   `LEAGUE_BASKET` line. ⛔ It lives ONLY at `StoryItemBattleStrategy._maybe_use_item`'s medicine list — NEVER in
   `bag_healing_stock` / `basket_to_buy` / `ch23_chapter_done` / R1 / `heal_party_from_bag`, which must keep reading
   the RAW bag (the adversarial recon: a reserve there makes leg 11 re-buy the basket, R1 refuse forever, and the
   Elite Four's between-room healing starve). Filtering BEFORE the policy (not vetoing its pick) keeps today's
   fallback to Super Potion intact.
   ⭐ STATE-DERIVED, NEVER A LATCH: armed iff `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` (the Juan era — the gym door opens with
   it) and NOT `ENTERED_ELITE_FOUR`, NOT `IS_CHAMPION`, NOT on a sealed §Ch24 map. Survives restarts and resumes,
   cannot leak into the next ENDLESS run (a new save clears the flags), and releases for every Elite Four battle
   (the Elite-Four progress vars are NOT used: every whiteout resets them).
   ⛔ FAILS UNLOCKED: a broken reserve must never silently disable item use — `decide_turn` swallows exceptions from
   `_maybe_use_item`, which once turned ALL item use off with every gate green.

SCOPE NOTE (my reading of the ruling, flagged to the user): the ruling's words were "locked so gym battles cannot
spend it"; the reserve holds for EVERY trainer battle until the Elite Four, because the recon found the bot spent
0 items on Juan in every log — a gym-only lock would protect nothing, while Victory Road trainers are where a held
Hyper Potion would actually be spent. Today's bot carries no Hyper Potions there, so the reserve reproduces today's
fights exactly. Switching to gym-only is one predicate.
"""
from __future__ import annotations

import os
from typing import Generator

from modules.context import context
from modules.modes._interface import BotModeError

#: The flag that opens the Juan era (decomp: the Sootopolis gym door unlocks with it; set when Maxie and Archie leave).
RESERVE_ERA_FLAG = "SOOTOPOLIS_ARCHIE_MAXIE_LEAVE"
#: Any of these RELEASES the reserve (state, never a latch).
RELEASE_FLAGS = ("ENTERED_ELITE_FOUR", "IS_CHAMPION")
#: Bought early in this order: never-spent-in-battle lines first, so a partial purchase cannot leak.
BUY_ORDER = ("Revive", "Full Heal", "Hyper Potion")
#: Cash kept back for Poké Balls (`early_game.MONEY_RESERVE` ₽500 + two balls) — the only other sink before leg 11.
CASH_FLOOR = 1_000
#: `LAYOUT_MART` (Sootopolis Mart shares Rustboro's layout; `early_game.RUSTBORO_MART` is the proven stand).
SOOTOPOLIS_MART_STAND = ((3, 3), "Left")
SOOTOPOLIS_PC_FRONT = (43, 32)
#: ⛔ MEASURED 2026-09-26 (E1 FAILED here): from the PC front (43,32) the planner finds NO path to the Mart, while from
#: (31,34) it finds one (23 steps). `calculate_path` treats the TEMPLATE tile of any object it cannot currently see as
#: blocked, and `get_map_objects()` is a CAMERA WINDOW. Object 7's template is (20,36) — the land bridge west — but a
#: script moved it to (29,33): visible from (31,34) (so its template is ignored), invisible from (43,32) (so the bridge
#: is "blocked"). ⇒ walk to this waypoint first; from here the planner sees the object and the bridge is open.
#: Probe: `ai-research-notes/2026-09-26-ruling18-reserve-GRADED.md` (E1).
SOOTOPOLIS_MART_WAYPOINT = (31, 34)
#: The Mart door (decomp `SootopolisCity/map.json` warp 1) and the tile a door exit steps onto.
SOOTOPOLIS_MART_DOOR = (17, 29)
SOOTOPOLIS_MART_FRONT = (17, 30)
EARLY_BASKET_BUDGET = 20_000

#: The readings the purchase publishes. ⛔ THE DRIVER IMPORTS THIS — never a private copy.
EARLY_BASKET_READINGS = (
    "EB-PLANNED",   # a non-empty plan was computed from the bag and the wallet
    "EB-MART",      # standing at the Sootopolis Mart clerk, `Task_ShopMenu` open
    "EB-BOUGHT",    # the bag's per-line delta equals the plan
)

_warned: set = set()


def _warn_once(key: str, message: str) -> None:
    if key in _warned:
        return
    _warned.add(key)
    try:
        from modules import debug_logger

        debug_logger.event(message, category="RESERVE")
    except Exception:  # noqa: BLE001 - a telemetry failure must not become a reserve failure
        pass


def _flag(name: str) -> bool:
    from modules.memory import _event_flags, get_event_flag

    if name not in _event_flags:
        raise BotModeError(f"league reserve: flag {name!r} is not in the event-flag table")
    return bool(get_event_flag(name))


def _on_sealed_map() -> bool:
    from modules.story.victory_road import CH24_SEALED_MAPS, _on_map

    return any(_on_map(m) for m in CH24_SEALED_MAPS)


def basket() -> "dict[str, int]":
    """`LEAGUE_BASKET` as {name: qty}. ⛔ The ONE source of the quantities — never a hand copy."""
    from modules.story.victory_road import LEAGUE_BASKET

    return dict(LEAGUE_BASKET)


def reserve_active() -> bool:
    """Is the League reserve armed right now? Pure function of game state (see the module docstring)."""
    if os.environ.get("POKEBOT_RESERVE_FAULT_RAISE") == "1":
        raise RuntimeError("POKEBOT_RESERVE_FAULT_RAISE: the reserve read is broken on purpose")
    if os.environ.get("POKEBOT_RESERVE_FAULT_FORCEON") == "1":
        return True
    if not _flag(RESERVE_ERA_FLAG):
        return False
    if any(_flag(f) for f in RELEASE_FLAGS):
        return False
    return not _on_sealed_map()


def reserved_quantities() -> "dict[str, int]":
    """{item name: quantity held back from in-battle use}; {} when the reserve is not armed."""
    if not reserve_active():
        return {}
    if os.environ.get("POKEBOT_RESERVE_FAULT_FORCEON") == "1":
        # Test-only: reserve the WHOLE bag stock of each basket line, so a lock is visible on an Elite Four fixture
        # whose bag exceeds the basket (every one does: 35-37 Hyper Potions). The quantities themselves are proven by
        # the pure gate; this arm proves the filter sits on the path a real battle uses.
        from modules.items import get_item_bag, get_item_by_name

        bag = get_item_bag()
        return {name: max(qty, bag.quantity_of(get_item_by_name(name))) for name, qty in basket().items()}
    return basket()


def apply_reserve(medicine: list, reserved: "dict[str, int]") -> list:
    """PURE: `medicine` is `[(item, quantity, parameter), …]`; return it with each reserved quantity subtracted and
    exhausted lines dropped. Items not in `reserved` pass through untouched, in their original order."""
    out = []
    for item, qty, param in medicine:
        usable = qty - reserved.get(getattr(item, "name", ""), 0)
        if usable > 0:
            out.append((item, usable, param))
    return out


def filter_medicine_for_reserve(medicine: list) -> list:
    """The ONE call `_maybe_use_item` makes. NEVER raises: any failure returns `medicine` UNCHANGED (fail unlocked)
    and logs once. `POKEBOT_RESERVE_FAULT_NOLOCK=1` bypasses the reserve (the skip-the-fix arm)."""
    if os.environ.get("POKEBOT_RESERVE_FAULT_NOLOCK") == "1":
        return medicine
    try:
        reserved = reserved_quantities()
        if not reserved:
            return medicine
        filtered = apply_reserve(medicine, reserved)
    except Exception as error:  # noqa: BLE001 - FAIL UNLOCKED: a broken reserve must never disable item use
        _warn_once("fail-unlocked", f"reserve read FAILED ({type(error).__name__}: {str(error)[:120]}) — "
                                    f"items used WITHOUT the reserve (fail unlocked)")
        return medicine
    if filtered != medicine:
        held = {getattr(i, "name", "?"): q for i, q, _p in medicine
                if getattr(i, "name", "") in reserved}
        _warn_once(f"held:{sorted(held.items())}", f"reserve holding back {reserved} from bag {held} "
                                                    f"(RULING 18; released on entering the Elite Four)")
    return filtered


# --------------------------------------------------------------------------------------------------------------------
# THE PURCHASE
# --------------------------------------------------------------------------------------------------------------------

def early_basket_plan(stock: "dict[str, int]", money: int, prices: "dict[str, int]", *,
                      sold_here: "set[str] | None" = None, floor: int = CASH_FLOOR) -> "list[tuple[str, int]]":
    """PURE: what to buy now — `[(name, qty), …]` in `BUY_ORDER`.

    Each line buys at most its MISSING quantity (`LEAGUE_BASKET` target − `stock`), at most 99, and only what
    `money − floor` still covers after the lines before it. Lines the shop does not sell are skipped.
    """
    target = basket()
    budget = max(0, money - floor)
    plan: "list[tuple[str, int]]" = []
    for name in BUY_ORDER:
        if name not in target or (sold_here is not None and name not in sold_here):
            continue
        missing = max(0, target[name] - stock.get(name, 0))
        price = prices.get(name, 0)
        if missing <= 0 or price <= 0:
            continue
        qty = min(missing, 99, budget // price)
        if qty > 0:
            plan.append((name, qty))
            budget -= qty * price
    return plan


def _stock_by_name(names) -> "dict[str, int]":
    """Summed across stacks (`victory_road.bag_healing_stock` keys by name, so a second stack overwrites the first)."""
    from modules.items import get_item_bag, get_item_by_name

    bag = get_item_bag()
    return {name: bag.quantity_of(get_item_by_name(name)) for name in names}


def in_early_basket_era() -> bool:
    return _flag(RESERVE_ERA_FLAG) and not _flag("BADGE08_GET")


def stock_basket_early(report: dict) -> Generator:
    """RULING 18's purchase. Never raises for a shopping problem (fail OPEN); `report["walked"]` tells the caller to
    re-heal. Frame-bounded by `EARLY_BASKET_BUDGET`."""
    from modules.story.early_game import _yield_bounded_by_frames, reraise_if_aborting

    # ⛔ ONE ERRAND PER CALL. §Ch22 passes the SAME dict on every Juan attempt (`heal_and_stock_before_the_gym` does
    # `report.setdefault("early_basket", {})` on a report made once, above the attempt loop), and
    # `return_across_from_the_mart` returns at once when `returned` is already True: a SECOND walk would skip the walk
    # back and strand the bot on the Mart side with the menu open (KI-103). Latent in RULING 18 (attempt 2 rarely has a
    # basket plan); reachable once step 9b walks for balls on a later attempt (found by the 9b recon, F1). ARCHIVED, never
    # discarded, as §Ch22 archives its own per-attempt readings.
    if any(key != "previous_errands" for key in report):
        previous = {key: report.pop(key) for key in list(report) if key != "previous_errands"}
        report.setdefault("previous_errands", []).append(previous)
    report.setdefault("readings", set())
    report.setdefault("order", [])
    report["walked"] = False
    try:
        # `POKEBOT_RESERVE_FAULT_BUDGET=<frames>` shrinks the budget so it EXPIRES mid-errand — the only way to drive the
        # recovery below, which a healthy errand never reaches (adversarial review, 2026-09-26; registered in 29).
        budget = int(os.environ.get("POKEBOT_RESERVE_FAULT_BUDGET") or EARLY_BASKET_BUDGET)
        report["budget"] = budget
        report["finished"] = yield from _yield_bounded_by_frames(_stock_basket_early(report), budget)
    except Exception as error:  # noqa: BLE001 - FAIL OPEN: the chapter continues to the heal and the gym as before
        reraise_if_aborting(error)
        report["early_basket"] = f"failed open: {type(error).__name__}: {str(error)[:200]}"
    if report.get("crossed") and not report.get("returned"):
        # ⛔ The budget closed the leg on the Mart side (or the walk back raised): one more bounded walk back along the
        # stored path — the pre-gym heal cannot plan from over there.
        report["retry_return"] = True
        try:
            yield from _yield_bounded_by_frames(return_across_from_the_mart(report), 6_000)
        except Exception as error:  # noqa: BLE001 - recorded; judged by `returned` just below
            reraise_if_aborting(error)
            report["retry_return_error"] = f"{type(error).__name__}: {str(error)[:160]}"
        report["stranded"] = not report.get("returned")
    try:
        from modules import debug_logger

        debug_logger.event(f"outcome={report.get('early_basket')!r} plan={report.get('plan')} "
                           f"bought={report.get('bought')} money={report.get('money_before')}->"
                           f"{report.get('money_after')} walked={report['walked']} finished={report.get('finished')} "
                           f"crossed={report.get('crossed')} returned={report.get('returned')} "
                           f"stranded={report.get('stranded')}"
                           + (f" balls={_balls_summary(report['balls'])}" if "balls" in report else ""),
                           category="EARLY_BASKET")
    except Exception:  # noqa: BLE001 - telemetry must never break the chapter; a missing line is visible
        pass
    if report.get("stranded"):
        # ⛔ The ONE case that is not fail-open: the pre-gym heal cannot plan from the Mart side either, so continuing
        # would only fail later with a misleading "BLOCKED". Fail NOW, by name (after the telemetry line).
        raise BotModeError(f"early basket: STRANDED on the Mart side of Sootopolis after the retry "
                           f"({report.get('retry_return_error')}); the planner cannot see the bridge from there "
                           f"(KI-103).")


def _balls_summary(balls: dict) -> dict:
    """The ball top-off's part of the `[EARLY_BASKET]` line (design v2 step 9b; present only with the flag set)."""
    keys = ("mode", "walk", "forecast", "phase", "lines", "bought", "premier", "ok", "money_after", "error")
    return {key: balls[key] for key in keys if key in balls}


def _stock_basket_early(report: dict) -> Generator:
    from modules.console import console
    from modules.items import get_item_by_name
    from modules.map_data import MapRSE
    from modules.modes.util.walking import ensure_facing_direction
    from modules.player import get_player
    from modules.story.early_game import wait_until_truly_controllable
    from modules.story.victory_road import _navigate_riding_out, _on_map, _where

    def _take(reading: str) -> None:
        if reading not in report["readings"]:
            report["order"].append(reading)
        report["readings"].add(reading)

    report["frame_start"] = context.emulator.get_frame_count()
    if os.environ.get("POKEBOT_RESERVE_FAULT_NOBUY") == "1":
        report["early_basket"] = "fault NOBUY"
        return
    if not in_early_basket_era():
        report["early_basket"] = "out of era"
        return
    city = MapRSE.SOOTOPOLIS_CITY
    if not (_on_map(city) or _on_map(MapRSE.SOOTOPOLIS_CITY_POKEMON_CENTER_1F)):
        report["early_basket"] = f"not in Sootopolis ({_where()})"
        return

    names = list(BUY_ORDER)
    before = _stock_by_name(names)
    money = get_player().money
    prices = {name: get_item_by_name(name).price for name in names}
    # `POKEBOT_RESERVE_FAULT_FLOOR=<₽>` raises the cash floor — the only way to drive a PARTIAL purchase on a fixture
    # whose wallet covers the whole early basket (registered in 29).
    floor = int(os.environ.get("POKEBOT_RESERVE_FAULT_FLOOR") or CASH_FLOOR)
    report["floor"] = floor
    plan = early_basket_plan(before, money, prices, floor=floor)
    report.update(stock_before=before, money_before=money, plan=plan)
    # ---- RULINGS 23 + 26 (design v2 step 9b): the ball top-off rides this visit. ⛔ With `POKEBOT_R23_BALLRESTOCK`
    # unset the forecast reads nothing but that variable and returns None: no report key, no yield, no move. In mode `1`
    # a complete basket no longer ends the visit by itself: a forecast that buys walks for the balls alone
    # (`stock_topoff.sootopolis_ball_forecast`).
    from modules.story.stock_topoff import sootopolis_ball_forecast

    balls = sootopolis_ball_forecast(plan, money, prices)
    if balls is not None:
        report["balls"] = balls
    if not plan and not (balls and balls.get("walk")):
        missing = {n: q - before.get(n, 0) for n, q in basket().items() if n in names and before.get(n, 0) < q}
        report["early_basket"] = "nothing missing" if not missing else f"cannot afford one unit (₽{money:,})"
        return
    if plan:
        _take("EB-PLANNED")
        console.print(f"[cyan]Story: RULING 18 — buying {plan} at the Sootopolis Mart (₽{money:,}, floor "
                      f"₽{CASH_FLOOR:,}).[/]")
    else:
        report["early_basket"] = "balls only"
        console.print(f"[cyan]Story: RULING 23 — the basket is complete; a ball-only visit to the Sootopolis Mart for "
                      f"{balls.get('forecast')} (₽{money:,}).[/]")


    # ---- to the waypoint on the PC side. ⛔ Re-pin the live layout first: §Ch21 pins the LEGENDS layout into the
    # process-global cache, and the lake it changed (x15-49, y24-56) is exactly the crossing to the Mart (17,29).
    report["walked"] = True
    if _on_map(MapRSE.SOOTOPOLIS_CITY_POKEMON_CENTER_1F):
        yield from _navigate_riding_out(city, SOOTOPOLIS_PC_FRONT)
        yield from wait_until_truly_controllable()
    if not _on_map(city):
        raise BotModeError(f"early basket: expected SOOTOPOLIS_CITY after leaving the PC, at {_where()}.")
    from modules.story.sootopolis import _pin_planner_to_live_layout

    report["layout_pin"] = _pin_planner_to_live_layout(city)
    yield from _navigate_riding_out(city, SOOTOPOLIS_MART_WAYPOINT)
    yield from wait_until_truly_controllable()
    report["waypoint_reached"] = _where()

    # ---- PLAN THE ROUND TRIP HERE, BEFORE CROSSING. ⛔ From the Mart side the planner cannot see object 7, so it would
    # find NO way back (measured: E1' bought everything, then the re-heal was "BLOCKED" and the run stranded). Both
    # legs are planned from this waypoint, where it can; if either fails, we do not cross at all.
    from modules.map_path import PathFindingError, calculate_path

    try:
        report["route_out_len"] = len(calculate_path((city, SOOTOPOLIS_MART_WAYPOINT), (city, SOOTOPOLIS_MART_DOOR)))
        back = calculate_path((city, SOOTOPOLIS_MART_FRONT), (city, SOOTOPOLIS_MART_WAYPOINT))
    except PathFindingError as error:  # noqa: BLE001 - the named outcome below; we do NOT cross, L1 continues as before
        report["early_basket"] = f"no planned round trip from {SOOTOPOLIS_MART_WAYPOINT}: {str(error)[:160]}"
        return
    report["route_back_len"] = len(back)
    report["route_back"] = back
    report["frames_at_cross"] = context.emulator.get_frame_count() - report["frame_start"]

    stand, face = SOOTOPOLIS_MART_STAND
    report["crossed"] = True
    shop_error = None
    try:
        yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY_MART, stand)
        yield from wait_until_truly_controllable()
        yield from ensure_facing_direction(face)
        yield from _shop(report, plan, names, before, money, _take)
    except Exception as error:  # noqa: BLE001 - recorded and re-raised AFTER the walk back: never strand the bot west
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        shop_error = error
    # ⛔ ALWAYS come back across once we have crossed — success, partial purchase or a shop error alike.
    yield from return_across_from_the_mart(report)
    if shop_error is not None:
        raise shop_error


def _shop(report: dict, plan, names, before, money, _take) -> Generator:
    """At the clerk: open the Mart, buy the plan and verify it by the bag delta (`_buy_basket_lines`), then, in
    `POKEBOT_R23_BALLRESTOCK=1`, top off the balls (design v2 step 9b). Raises on a menu problem, and on a Mart that
    sells none of the basket unless this is a ball-only visit."""
    from modules.mart import get_mart_buyable_items
    from modules.modes.util import wait_for_n_frames
    from modules.modes.util.tasks_scripts import task_is_active
    from modules.story.early_game import _check_abort
    from modules.story.victory_road import _where

    opened = False
    for _ in range(60):
        _check_abort()
        if task_is_active("Task_ShopMenu"):
            opened = True
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(10)
    report["shop_menu_open"] = opened
    if not opened:
        raise BotModeError(f"early basket: at {_where()} the clerk's `Task_ShopMenu` never opened.")
    report["frames_at_shop_open"] = context.emulator.get_frame_count() - report.get("frame_start", 0)
    _take("EB-MART")

    sold = {item.name for item in get_mart_buyable_items()}
    report["sold_here"] = sorted(sold)
    balls = report.get("balls") or {}
    # ⛔ A ball-only visit is decided by the CALLER's plan (empty) and the forecast, BEFORE the live filter: a basket
    # visit whose Mart sells none of the basket must still raise by name, whatever the forecast says (the 9b review,
    # BB9B-1: keyed on `walk` alone, a buying forecast silently swallowed this raise and left the outcome unset).
    ball_only = not plan and bool(balls.get("walk"))
    plan = [(n, q) for n, q in plan if n in sold]
    if not plan and not ball_only:
        raise BotModeError(f"early basket: this Mart sells none of {list(BUY_ORDER)} ({sorted(sold)}).")
    if plan:
        yield from _buy_basket_lines(report, plan, names, before, money, _take)
    if balls.get("mode") == "1" and not balls.get("blocked"):
        # RULINGS 23 + 26 (design v2 step 9b): after the basket, on the same open menu (`buy_in_shop` ends on the shop's
        # main menu). It raises only an abort or a close; on a normal return the caller closes the menu and walks back.
        from modules.story.stock_topoff import sootopolis_ball_phase

        yield from sootopolis_ball_phase(report)


def _buy_basket_lines(report: dict, plan, names, before, money, _take) -> Generator:
    """RULING 18's lines on the open Mart menu: buy them, then verify by the bag delta. Moved out of `_shop` UNCHANGED by
    design v2 step 9b, so a ball-only visit can skip it."""
    from modules.console import console
    from modules.items import get_item_by_name
    from modules.modes.util.higher_level_actions import buy_in_shop
    from modules.player import get_player
    from modules.story.early_game import wait_until_truly_controllable

    yield from buy_in_shop([(get_item_by_name(name), qty) for name, qty in plan])
    yield from wait_until_truly_controllable()

    after = _stock_by_name(names)
    report["stock_after"] = after
    report["money_after"] = get_player().money
    bought = {n: after.get(n, 0) - before.get(n, 0) for n in names}
    report["bought"] = {n: q for n, q in bought.items() if q}
    short = {n: q - bought.get(n, 0) for n, q in plan if bought.get(n, 0) != q}
    if short:
        # ⛔ `buy_in_shop` continues silently after "no more room" (`shop.c:1105-1112`) — the bag delta is the truth.
        report["early_basket"] = f"partial: planned {plan}, bag delta {report['bought']}"
        return
    _take("EB-BOUGHT")
    report["early_basket"] = "bought"
    console.print(f"[green]Story: RULING 18 — bought {report['bought']}; ₽{money:,} → ₽{report['money_after']:,}. "
                  f"Reserved until the Elite Four.[/]")


def return_across_from_the_mart(report: dict) -> Generator:
    """Walk back to the PC-side waypoint along the path PLANNED FROM THAT SIDE (`report["route_back"]`).

    ⛔ Never re-plan from the Mart side: the planner blocks the bridge there (see `SOOTOPOLIS_MART_WAYPOINT`). Resumes
    from wherever on the stored path we stand (a wild battle or a bumped NPC times a waypoint out), bounded, and only
    as a last resort asks the planner again. Idempotent: returns at once if already back on the PC side.
    """
    from modules.map_data import MapRSE
    from modules.modes.util.walking import TimedOutTryingToReachWaypointError, follow_waypoints
    from modules.player import get_player_location
    from modules.story.early_game import reraise_if_aborting, wait_until_truly_controllable
    from modules.story.victory_road import _navigate_riding_out, _on_map, _where

    city = MapRSE.SOOTOPOLIS_CITY
    back = report.get("route_back") or []
    if report.get("returned") or not report.get("crossed"):
        return
    # ⛔ An expired budget can leave the Mart menu / the clerk's dialog OPEN (the review's scenario): the avatar is not
    # controllable there, so close it first — B on a duty cycle, bounded.
    yield from _close_shop_and_dialogs(report)
    yield from wait_until_truly_controllable()
    if not _on_map(city):
        # Inside the Mart (or its doorway): out to the tile the stored path starts from. A one-step plan on this side
        # never touches the bridge.
        yield from _navigate_riding_out(city, SOOTOPOLIS_MART_FRONT)
        yield from wait_until_truly_controllable()
    for attempt in range(4):
        here = tuple(get_player_location()[1]) if _on_map(city) else None
        if here == SOOTOPOLIS_MART_WAYPOINT:
            break
        coords = [tuple(w.coordinates) for w in back]
        if here == SOOTOPOLIS_MART_FRONT:
            remaining = back
        elif here in coords:
            remaining = back[coords.index(here) + 1:]
        else:
            remaining = None
        report.setdefault("return_attempts", []).append({"from": here, "remaining": None if remaining is None
                                                         else len(remaining)})
        try:
            if remaining is None:
                # Off the stored path: the planner is the last resort — the waypoint works from the PC side (or with the
                # object in view); failing that, the Mart front is a WEST-side plan that never needs the bridge, and the
                # next pass then follows the stored path from there.
                try:
                    yield from _navigate_riding_out(city, SOOTOPOLIS_MART_WAYPOINT)
                except Exception as error:  # noqa: BLE001 - expected from the Mart side; fall back to the Mart front
                    reraise_if_aborting(error)
                    report.setdefault("return_errors", []).append(f"waypoint: {type(error).__name__}")
                    yield from _navigate_riding_out(city, SOOTOPOLIS_MART_FRONT)
            else:
                yield from follow_waypoints(remaining)
        except TimedOutTryingToReachWaypointError as error:  # noqa: BLE001 - recorded; the loop re-reads the position and resumes the stored path
            report.setdefault("return_timeouts", []).append(str(error)[:120])
        except Exception as error:  # noqa: BLE001 - recorded; the loop re-reads the position and tries again
            reraise_if_aborting(error)
            report.setdefault("return_errors", []).append(f"{type(error).__name__}: {str(error)[:120]}")
        yield from wait_until_truly_controllable()
    report["returned"] = _on_map(city) and tuple(get_player_location()[1]) == SOOTOPOLIS_MART_WAYPOINT
    report["return_at"] = _where()
    if not report["returned"]:
        raise BotModeError(f"early basket: could NOT walk back across from the Mart (at {_where()}); the pre-gym heal "
                           f"will plan from here and may find no path.")


def _close_shop_and_dialogs(report: dict) -> Generator:
    """Close an open Mart menu, the clerk's dialog, or a message box: B on a duty cycle (a held button is not a press),
    until the avatar is controllable with no script running. Bounded (~720 frames)."""
    from modules.modes.util import wait_for_n_frames
    from modules.player import player_avatar_is_controllable
    from modules.tasks import get_global_script_context

    presses = 0
    for _ in range(60):
        if player_avatar_is_controllable() and not get_global_script_context().is_active:
            break
        context.emulator.press_button("B")
        presses += 1
        yield from wait_for_n_frames(12)
    report["close_presses"] = presses

