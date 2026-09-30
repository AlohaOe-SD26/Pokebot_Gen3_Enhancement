"""
USER RULINGS 23 + 26, design v2 step 9 (BB): top off the BALL stock with the best ball the mart sells, in BOUNDED
batches: as a piggyback on a Rustboro Pokémon Center heal (9a), and inside RULING 18's Sootopolis League-basket visit
(9b). Behind `POKEBOT_R23_BALLRESTOCK` (default OFF; `observe` plans and logs without walking; `1` buys).

RULING 23 (06, 2026-09-29): no per-run spending ceiling; purchases in bounded batches, topped off periodically the way
healing items are; the BEST ball the current shop sells; RULING 18's League basket and reserve still stand.
RULING 26: stock is maintained all game.

WHAT THIS FILE IS
  * PURE planning (`limits`, `best_ball`, `stage`, `floor`, `ball_topoff_plan`, `plan_lines`), importable with no
    emulator and gated by `tools/story-dev/probe_stock_topoff.py`.
  * Consumer (a), step 9a: the emulator ERRAND (`ball_topoff_errand`), called from ONE place: the end of
    `heal_in_pokemon_center` (`modules/modes/util/higher_level_actions.py`), after the heal's own stable-exit wait.
  * Consumer (b), step 9b: RULING 18's Sootopolis League-basket visit (`league_reserve._stock_basket_early` and
    `_shop`) calls `sootopolis_ball_forecast` before any walk and `sootopolis_ball_phase` at the counter. It walks for
    the balls alone only when the basket is complete and the forecast buys; OFF, it reads nothing but the flag.

THE NUMBERS (a bounded DEFAULT; the batch size is the user's Q1, shown to them — v2 note §4):
  * TRIGGER = DEX_CATCH_BALL_RESERVE + DEX_CATCH_MAX_EXPECTED_THROWS = 20: top off exactly when the bot can no longer
    pay for one maximum-admissible dex catch above the reserve the in-battle bail enforces.
  * TARGET = MAX_BALLS_PER_TRIP = 30: the record's own purchase unit (`DEX_CATCH_MAX_EXPECTED_THROWS` was "sized so the
    30-ball Rustboro purchase covers ~3 hard catches").
  * BATCH_CAP = MAX_BALLS_PER_TRIP × POKE_BALL_PRICE = ₽6,000 per visit, and never more than HALF of (money − floor):
    a visit spends at most half of what is spendable, so repeated visits approach the floor geometrically instead of
    hitting it. ⚠ It does NOT guarantee the floor survives a whiteout (a whiteout halves ALL the money; with money
    below 3 × floor a purchase followed by a whiteout ends below the floor), and heals are free in Emerald: the floor
    protects later mandatory purchases (the League basket), not heals (corrected by the step 9a review).
  * floor = CASH_FLOOR, plus 2 × the League basket's missing cost once the reserve era starts (RULING 18 stands).
  Each is IMPORTED at call time, never copied, so a change to the source constant moves this with it.

⛔ SAFETY PROPERTIES (each has a gate row)
  * OFF reads nothing and yields nothing; `observe` and an empty plan yield nothing either. The heal's extra stable
    wait runs ONLY when the errand actually moved the avatar (a planning failure reports and memoises WITHOUT moving).
  * `stage()` and `floor()` FAIL CLOSED: an unreadable flag means NO purchase, with a named reason (a stage that fell
    back to MID would drop the basket floor to ₽1,000). `_inputs` leaves out a flag missing from the event-flag table,
    because `get_event_flag` would read it as False.
  * The quantity is refused below the floor (Python's // would go NEGATIVE, and `buy_in_shop` raises on it). The
    in-game max per line, min(money // price, 99), cannot bind under this formula; gate row L9 proves it.
  * A city whose errand fails — planning, walk, bound, a bag delta that is not the plan, or not back on the exit tile —
    goes into the run's failed-walk memo (`StoryMode._ball_topoff_failed`, reset per run) and is not walked again this
    run. An OUTER bound that closes the heal mid-errand is logged (`topoff-closed`) and memoised too; no recovery can
    run while a generator is closing, so the avatar may be left in the Mart for the caller's next navigate.
  * Whitelist: Rustboro only (step 9a). Its mart sells Poké Balls from the start (`RustboroCity_Mart/scripts.inc`).
    Sootopolis is NOT whitelisted (KI-103): it is consumer (b), which rides RULING 18's round trip.
  * Consumer (b) (gate `probe_stock_topoff_sootopolis.py`): OFF reads nothing but the flag and adds no report key; the
    forecast plans from the POST-basket wallet and floor; the ball phase re-plans live, never raises (the basket's own
    outcome stands), memoises a failure, and logs an outer close; `observe` never walks for balls.
  * ⚠ No minimum batch: a money-limited purchase can buy 1-2 balls and re-walk at the next eligible heal (bounded:
    each walk's budget halves). Part of the user's Q1.
"""

from __future__ import annotations

from typing import Generator

#: Unconditional catch multipliers (`sBallCatchBonuses` + the special-ball handlers, `battle_script_commands.c`): a
#: conditional ball (Nest, Net, Dive, Repeat, Timer) counts as 1.0 here, so the "best" ball is the best on ANY target.
#: ⚠ This NARROWS 06:8069 ("the best ball the shop sells") where a conditional ball wins on some targets: Q2, put to
#: the user (v2 note §4). Premier is a purchase BONUS, never bought.
UNCONDITIONAL = {"Ultra Ball": 2.0, "Great Ball": 1.5, "Poké Ball": 1.0, "Net Ball": 1.0, "Nest Ball": 1.0,
                 "Dive Ball": 1.0, "Repeat Ball": 1.0, "Timer Ball": 1.0, "Luxury Ball": 1.0}

STAGES = ("PRE_GYM1", "MID", "BASKET_ERA", "LEAGUE", "POSTGAME")
MAX_PER_LINE = 99


def flag_names() -> dict:
    """{stage key: event-flag name}. The reserve-era flag is IMPORTED from `league_reserve`, never copied."""
    from modules.story.league_reserve import RESERVE_ERA_FLAG

    return {"champion": "IS_CHAMPION", "entered_e4": "ENTERED_ELITE_FOUR", "reserve_era": RESERVE_ERA_FLAG,
            "badge1": "BADGE01_GET"}
VALID_FLAG_VALUES = ("", "0", "observe", "1")


def limits() -> dict:
    """TRIGGER / TARGET / BATCH_CAP, from the source constants (imported, never copied)."""
    from modules.story.early_game import MAX_BALLS_PER_TRIP, POKE_BALL_PRICE
    from plugins.custom_modes.story_mode import DEX_CATCH_BALL_RESERVE, DEX_CATCH_MAX_EXPECTED_THROWS

    return {"trigger": DEX_CATCH_BALL_RESERVE + DEX_CATCH_MAX_EXPECTED_THROWS,
            "target": MAX_BALLS_PER_TRIP,
            "batch_cap": MAX_BALLS_PER_TRIP * POKE_BALL_PRICE}


def parse_flag(raw) -> "tuple[str, str | None]":
    """(`mode`, `error`). `mode` is '' (OFF), 'observe' or '1'. ⛔ A value outside the vocabulary is NOT silently OFF
    (a mistyped arm that reads as tested — the lesson recorded at `victory_road.py:735-743`): it is OFF WITH an error
    the caller prints."""
    value = (raw or "").strip()
    if value not in VALID_FLAG_VALUES:
        return "", f"POKEBOT_R23_BALLRESTOCK={value!r} is not one of {VALID_FLAG_VALUES}: treated as OFF"
    return ("" if value == "0" else value), None


def best_ball(sold, allowed, prices: dict) -> "str | None":
    """The ball with the highest UNCONDITIONAL multiplier that is both sold and allowed; ties go to the cheapest."""
    candidates = [name for name in sold if name in UNCONDITIONAL and name in allowed and name in prices]
    if not candidates:
        return None
    return max(candidates, key=lambda name: (UNCONDITIONAL[name], -prices[name], name))


def stage(flags: dict) -> "str | None":
    """PURE. The game stage from the four `flag_names()` keys, checked in this order: champion → POSTGAME; entered_e4 →
    LEAGUE (entered and lost; nothing clears it); reserve_era → BASKET_ERA; no badge1 → PRE_GYM1; else MID.
    None (NO purchase) if any key is missing — fail closed. ⛔ `_inputs` OMITS a flag whose name is not in the event-flag
    table (`get_event_flag` would read an unknown name as False, which guesses the stage LOW: the step 9a review)."""
    try:
        if flags["champion"]:
            return "POSTGAME"
        if flags["entered_e4"]:
            return "LEAGUE"
        if flags["reserve_era"]:
            return "BASKET_ERA"
        if not flags["badge1"]:
            return "PRE_GYM1"
        return "MID"
    except Exception:  # noqa: BLE001 - an unreadable flag is "no purchase", never a stage guessed low
        return None


def floor(stage_name: "str | None", missing_basket_cost: "int | None") -> "int | None":
    """The money the top-off never spends below. None (NO purchase) when it cannot be computed — fail closed."""
    from modules.story.league_reserve import CASH_FLOOR

    if stage_name in (None, "PRE_GYM1"):
        return None
    if stage_name in ("BASKET_ERA", "LEAGUE"):
        if missing_basket_cost is None:
            return None
        return CASH_FLOOR + 2 * int(missing_basket_cost)
    return CASH_FLOOR


def plan_lines(ball: str, qty: int) -> "list[tuple[str, int]]":
    """Purchase lines. Poké Balls in lines of 10 with the remainder MERGED into the last line (one Premier per
    transaction of 10+, `shop.c:1150-1155`: 22 → [10, 12] earns 2 Premiers and wastes no affordable ball); every other
    ball in one line."""
    if qty <= 0:
        return []
    if ball != "Poké Ball" or qty < 10:
        return [(ball, qty)]
    lines = [(ball, 10) for _ in range(qty // 10)]
    rest = qty % 10
    if rest:
        lines[-1] = (ball, 10 + rest)
    return lines


def ball_topoff_plan(*, spare: int, money: int, ball: "str | None", price: "int | None", stage_name: "str | None",
                     floor_money: "int | None", lim: dict) -> "tuple[list[tuple[str, int]], str]":
    """PURE. (`lines`, `reason`): what to buy, and a NAMED reason for every outcome (an empty plan included)."""
    if stage_name is None:
        return [], "stage unreadable (fail closed)"
    if stage_name == "PRE_GYM1":
        return [], "before gym 1 (the pre-gym-1 contingency stays; RULING 26 gap named for later)"
    if spare > lim["trigger"]:
        return [], f"spare {spare} > trigger {lim['trigger']}"
    if ball is None or not price:
        return [], "no allowed ball sold here"
    if floor_money is None:
        return [], "floor unreadable (fail closed)"
    if money <= floor_money:
        return [], f"money {money} at or below the floor {floor_money}"
    budget = min(lim["batch_cap"], (money - floor_money) // 2)
    # ⚠ The in-game max per line is min(money // price, 99) (`shop.c:1046-1051`; `buy_in_shop`'s quantity loop never
    # ends above it). It cannot bind here: budget <= (money - floor) // 2 < money, and qty <= TARGET = 30 < 99. So no
    # clamp is written for it; gate row L9 proves the invariant over a grid instead (the review: a clamp that could
    # never bind, under a row that claimed to test it, was a false protection).
    qty = min(lim["target"] - spare, budget // price)
    if qty <= 0:
        return [], f"cannot afford one {ball} (budget {budget}, price {price})"
    return plan_lines(ball, qty), f"top off {qty} x {ball} (spare {spare} <= trigger {lim['trigger']}; budget {budget})"


def log_line(tag: str, *, mart: str, ball, bought, premier, spare_before, spare_after, money_before, money_after,
             reason: str, extra: str = "") -> str:
    """`[BALLS-BUY] why=<tag> …` — one line per errand (`topoff`, `topoff-failed`), plan (`topoff-observe`,
    `topoff-none`) or skip (`topoff-skip`)."""
    return (f"[BALLS-BUY] why={tag} mart={mart} ball={ball} bought={bought} premier={premier} "
            f"spare={spare_before}->{spare_after} money={money_before}->{money_after}{extra} reason={reason}")


# ================================================================================================ the emulator errand
#: Cities whose Pokémon Center heal may start the errand, with (mart map, stand tile, facing). Step 9a: Rustboro only.
def _whitelist() -> dict:
    from modules.map_data import PokemonCenter
    from modules.story.early_game import RUSTBORO_MART

    return {PokemonCenter.RustboroCity: RUSTBORO_MART}


ERRAND_FRAMES = 8_000
RECOVERY_FRAMES = 6_000


def _emit(line: str) -> None:
    try:
        from modules import debug_logger
        from modules.console import console

        console.print(f"[cyan]{line}[/]")
        debug_logger.event(line, category="BALLS")
    except Exception as error:  # noqa: BLE001 - telemetry never breaks a heal; say so on stdout instead
        print(f"[BALLS-BUY] log failed ({error!r}): {line}")


def _inputs(mode) -> dict:
    """Live reads for the plan. A raise is caught by the errand (reported, memoised, not moved)."""
    from modules.items import get_item_bag, get_item_by_name
    from modules.memory import _event_flags, get_event_flag
    from modules.player import get_player

    # ⛔ A name missing from the event-flag table is LEFT OUT, so `stage()` fails closed; `get_event_flag` alone would
    # read it as False and guess the stage low (the step 9a review measured `memory.py:336-338`).
    flags = {key: bool(get_event_flag(name)) for key, name in flag_names().items() if name in _event_flags}
    st = stage(flags)
    missing = None
    if st in ("BASKET_ERA", "LEAGUE"):
        from modules.story.league_reserve import _stock_by_name
        from modules.story.victory_road import LEAGUE_BASKET, basket_cost, basket_to_buy

        missing = basket_cost(basket_to_buy(_stock_by_name([name for name, _ in LEAGUE_BASKET])))
    bag = get_item_bag()
    return {"stage": st, "floor": floor(st, missing), "spare": int(bag.number_of_balls_except_master_ball),
            "money": int(get_player().money), "flags": flags, "price_of": lambda n: get_item_by_name(n).price}


def _allowed() -> set:
    from modules.catch_balls import allowed_ball_names

    return set(allowed_ball_names())


def _static_sold(center) -> list:
    """What the whitelisted mart sells, for the GO/NO-GO decision only (the live list is re-read at the counter)."""
    return ["Poké Ball"]   # Rustboro: basic and expanded lists both start with the Poké Ball (decomp scripts.inc)


def ball_topoff_errand(center, flag_mode: str, first_wait_stable: bool) -> Generator:
    """Called at the END of `heal_in_pokemon_center`. Returns True iff the avatar MOVED (then the heal runs its stable
    wait again). ⛔ Returns False with ZERO yields unless every precondition holds."""
    from modules.context import context
    from modules.map_data import MapRSE

    if flag_mode not in ("observe", "1"):
        return False
    try:
        from plugins.custom_modes.story_mode import StoryMode
    except Exception:  # noqa: BLE001 - no StoryMode, no errand (a non-story bot never tops off)
        return False
    mode = context.bot_mode_instance
    if not isinstance(mode, StoryMode):
        return False
    wl = _whitelist()
    if center not in wl:
        return False
    city = center.name
    failed = getattr(mode, "_ball_topoff_failed", None)
    if failed is None:
        failed = mode._ball_topoff_failed = set()
    if city in failed:
        return False
    if not first_wait_stable:
        _emit(log_line("topoff-skip", mart=city, ball="-", bought=0, premier=0, spare_before="?", spare_after="?",
                       money_before="?", money_after="?", reason="the heal's exit never became stable"))
        return False
    try:
        lim = limits()
        live = _inputs(mode)
        ball = best_ball(_static_sold(center), _allowed(), {n: live["price_of"](n) for n in UNCONDITIONAL
                                                             if n in _static_sold(center)})
        price = live["price_of"](ball) if ball else None
        floor_money = live["floor"]
        import os as _os_bb
        _fault_floor = _os_bb.environ.get("POKEBOT_R23_FAULT_FLOOR", "").strip()
        if _fault_floor:
            floor_money = int(_fault_floor)   # FAULT ARM: a synthetic floor, to prove the floor gates the purchase live
        lines, reason = ball_topoff_plan(spare=live["spare"], money=live["money"], ball=ball, price=price,
                                         stage_name=live["stage"], floor_money=floor_money, lim=lim)
    except Exception as error:  # noqa: BLE001 - a planning failure moved nothing: report it, memoise, no extra wait
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        failed.add(city)
        _emit(log_line("topoff-failed", mart=city, ball="-", bought=0, premier=0, spare_before="?", spare_after="?",
                       money_before="?", money_after="?", reason=f"planning raised {error!r} (nothing moved)"))
        return False
    if flag_mode == "observe" or not lines:
        _emit(log_line("topoff-observe" if flag_mode == "observe" else "topoff-none", mart=city, ball=ball or "-",
                       bought=0, premier=0, spare_before=live["spare"],
                       spare_after=live["spare"], money_before=live["money"], money_after=live["money"],
                       reason=reason))
        return False

    from modules.player import get_player_avatar
    from modules.story.early_game import _yield_bounded_by_frames

    avatar = get_player_avatar()
    exit_map, exit_tile = MapRSE(avatar.map_group_and_number), avatar.local_coordinates
    report: dict = {}
    mart = wl[center]
    moved_ok = False
    try:
        import os as _os_bb2
        bound = int(_os_bb2.environ.get("POKEBOT_R23_FAULT_ERRANDFRAMES", "") or ERRAND_FRAMES)
        finished = yield from _yield_bounded_by_frames(
            _walk_buy_return(mart, exit_map, exit_tile, lines, live, reason, report), bound)
        # ⛔ SUCCESS means bought as planned AND back on the recorded exit tile (the review: `back=` was logged, never
        # compared).
        moved_ok = finished and report.get("ok", False) and report.get("returned", False)
    except GeneratorExit:
        # ⛔ An OUTER bound closed the heal mid-errand (maintenance's `_yield_bounded(train_team(...))` reaches a Rustboro
        # heal in a DEFAULT run). Nothing may yield here, so no recovery can run: record it loudly, memoise the city so
        # the next heal does not walk into the same close, and let the close proceed (the review measured this path
        # silent before).
        failed.add(city)
        _emit(log_line("topoff-closed", mart=city, ball=ball, bought=report.get("bought", 0),
                       premier=report.get("premier", 0), spare_before=live["spare"], spare_after="?",
                       money_before=live["money"], money_after="?",
                       reason="an outer bound closed the heal mid-errand (no recovery can run while closing)"))
        raise
    except Exception as error:  # noqa: BLE001 - reported below; an abort is re-raised first
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        report["error"] = repr(error)
    if not moved_ok:
        failed.add(city)
        why = (report.get("error") or report.get("why")
               or ("not back on the exit tile" if report.get("ok") else "the errand's frame bound expired"))
        _emit(log_line("topoff-failed", mart=city, ball=ball, bought=report.get("bought", 0),
                       premier=report.get("premier", 0), spare_before=live["spare"],
                       spare_after=report.get("spare_after", "?"), money_before=live["money"],
                       money_after=report.get("money_after", "?"), reason=why))
        recovered = yield from _yield_bounded_by_frames(_recover(exit_map, exit_tile, report), RECOVERY_FRAMES)
        _emit(log_line("topoff-recovery", mart=city, ball=ball, bought=report.get("bought", 0), premier=0,
                       spare_before="-", spare_after="-", money_before="-", money_after="-",
                       reason=f"finished={recovered} back_on_exit={report.get('recovered_on_exit')}"))
    return True


def _walk_buy_return(mart, exit_map, exit_tile, lines, live, reason, report) -> Generator:
    """Walk to the clerk, buy `lines` (FILTERED against the live list: quantities and the ball are not recomputed),
    verify by the bag delta, walk back to the exit tile and face Down."""
    from modules.context import context
    from modules.items import get_item_bag, get_item_by_name
    from modules.mart import get_mart_buyable_items
    from modules.modes.util import wait_for_n_frames
    from modules.modes.util.higher_level_actions import buy_in_shop
    from modules.modes.util.tasks_scripts import task_is_active
    from modules.modes.util.walking import ensure_facing_direction
    from modules.player import get_player
    from modules.story.early_game import _check_abort, _navigate_riding_out, wait_until_truly_controllable
    from modules.story.league_reserve import _close_shop_and_dialogs

    mart_map, stand, face = mart
    yield from _navigate_riding_out(mart_map, stand)
    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction(face)
    opened = False
    for _ in range(60):
        _check_abort()
        if task_is_active("Task_ShopMenu"):
            opened = True
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(10)
    if not opened:
        report["why"] = "the clerk's Task_ShopMenu never opened"
        yield from _close_shop_and_dialogs(report)
        return
    sold = {item.name for item in get_mart_buyable_items()}   # ⛔ read ONLY with the menu open (sMartInfo is stale after)
    lines = [(n, q) for n, q in lines if n in sold]
    if not lines:
        report["why"] = f"the live list sells none of the plan ({sorted(sold)})"
        yield from _close_shop_and_dialogs(report)
        return
    names = sorted({n for n, _ in lines} | {"Premier Ball"})
    before = {n: get_item_bag().quantity_of(get_item_by_name(n)) for n in names}
    yield from buy_in_shop([(get_item_by_name(n), q) for n, q in lines])
    yield from _close_shop_and_dialogs(report)                 # close BEFORE any controllable-wait (recon)
    yield                                                        # the bag cache is per frame
    after = {n: get_item_bag().quantity_of(get_item_by_name(n)) for n in names}
    ball = lines[0][0]
    report["bought"] = after[ball] - before[ball]
    report["premier"] = after.get("Premier Ball", 0) - before.get("Premier Ball", 0) if ball != "Premier Ball" else 0
    report["spare_after"] = int(get_item_bag().number_of_balls_except_master_ball)
    report["money_after"] = int(get_player().money)
    planned = sum(q for _, q in lines)
    report["ok"] = report["bought"] == planned
    if not report["ok"]:
        report["why"] = f"bag delta {report['bought']} != planned {planned}"
    yield from _navigate_riding_out(exit_map, exit_tile)
    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction("Down")                   # OFF leaves the PC facing Down
    from modules.player import get_player_avatar

    av = get_player_avatar()
    back = (f" exit={exit_tile[0]},{exit_tile[1]} back={av.local_coordinates[0]},{av.local_coordinates[1]} "
            f"facing={av.facing_direction}")
    report["back"] = back
    report["returned"] = (tuple(av.map_group_and_number) == tuple(exit_map.value)
                          and tuple(av.local_coordinates) == tuple(exit_tile) and av.facing_direction == "Down")
    if report["ok"] and report["returned"]:
        _emit(log_line("topoff", mart=exit_map_name(mart_map), ball=ball, bought=report["bought"],
                       premier=report["premier"], spare_before=live["spare"], spare_after=report["spare_after"],
                       money_before=live["money"], money_after=report["money_after"], reason=reason, extra=back))


def exit_map_name(mart_map) -> str:
    try:
        return f"{mart_map.value[0]},{mart_map.value[1]}"
    except Exception:  # noqa: BLE001 - a label only
        return str(mart_map)


def _recover(exit_map, exit_tile, report) -> Generator:
    """After a failed or expired errand: close any open menu, then walk back to where the heal left the avatar."""
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable
    from modules.story.league_reserve import _close_shop_and_dialogs

    from modules.modes.util.walking import ensure_facing_direction
    from modules.player import get_player_avatar

    report["recovered_on_exit"] = False
    yield from _close_shop_and_dialogs(report)
    yield from _navigate_riding_out(exit_map, exit_tile)
    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction("Down")
    av = get_player_avatar()
    report["recovered_on_exit"] = (tuple(av.map_group_and_number) == tuple(exit_map.value)
                                   and tuple(av.local_coordinates) == tuple(exit_tile))


# ================================================================================ consumer (b): Sootopolis (step 9b)
# RULING 18's League-basket visit to the Sootopolis Mart (`league_reserve._stock_basket_early`, §Ch22 L1, on every Juan
# attempt) also tops off the balls: in the SAME visit when the basket needs a walk, and as a BALL-ONLY walk when the
# basket is complete and the forecast buys. The early return there used to fire on "nothing missing" alone, so lines
# merely appended to the basket would be bought about once per run, not "topped off periodically" (v2 `[A-S9]`).
# Whitelisting Sootopolis in consumer (a) is wrong on purpose (KI-103: the planner cannot see the bridge from the Mart
# side), so this rides R18's proven round trip instead.

#: The balls the Sootopolis Mart sells: recorded live by RULING 18's drives (`sold_here`, e.g.
#: `evidence/2026-09-26-earlybasket-E1c-BUY.txt`). Used for the GO/NO-GO forecast only; the counter re-reads the live
#: list with the menu open.
SOOTOPOLIS_STATIC_SOLD = ("Ultra Ball",)


def sootopolis_key() -> str:
    """This consumer's key in the run's failed-walk memo and the `mart=` label of its lines: the Pokémon Center's
    enum name, exactly as step 9a keys a city (`center.name`), so the two consumers can never share or miss a key."""
    from modules.map_data import PokemonCenter

    return PokemonCenter.SootopolisCity.name


def forecast_after_basket(*, raw_basket_stock: dict, basket_plan, basket_prices: dict, league_prices: dict, money: int,
                          spare: int, flags: dict, sold, allowed, ball_prices: dict, lim: dict,
                          fault_floor: "int | None" = None) -> dict:
    """PURE. The ball plan for the moment AFTER RULING 18's `basket_plan` is bought: the wallet minus that plan's cost,
    and the floor from the League basket still MISSING once the plan is in the bag.

    ⛔ Both halves matter, and step 0 measured each on `post_hm07.ss1`: the wallet BEFORE the basket with the right
    floor forecasts 5 Ultras (₽67,466), a floor read from the bag before the basket forecasts 0 (₽1,000 + 2 × ₽54,300
    is above any wallet here), and the right pair forecasts 1 (₽22,166 against a floor of ₽19,000)."""
    from modules.story.victory_road import basket_to_buy

    post = dict(raw_basket_stock)
    for name, qty in basket_plan:
        post[name] = post.get(name, 0) + qty
    money_after = int(money) - sum(basket_prices[name] * qty for name, qty in basket_plan)
    stage_name = stage(flags)
    missing = None
    if stage_name in ("BASKET_ERA", "LEAGUE"):
        missing = sum(league_prices[name] * qty for name, qty in basket_to_buy(post))
    floor_money = fault_floor if fault_floor is not None else floor(stage_name, missing)
    ball = best_ball(sold, allowed, ball_prices)
    price = ball_prices.get(ball) if ball else None
    lines, reason = ball_topoff_plan(spare=spare, money=money_after, ball=ball, price=price, stage_name=stage_name,
                                     floor_money=floor_money, lim=lim)
    return {"lines": lines, "reason": reason, "money_after_basket": money_after, "floor": floor_money,
            "stage": stage_name, "ball": ball, "spare": spare}


def _fault_floor() -> "int | None":
    """`POKEBOT_R23_FAULT_FLOOR=<₽>`: the live floor lever, honoured by consumer (b) exactly as by consumer (a)."""
    import os

    raw = os.environ.get("POKEBOT_R23_FAULT_FLOOR", "").strip()
    return int(raw) if raw else None


def _memo() -> "set | None":
    """The run's failed-walk memo (`StoryMode._ball_topoff_failed`, reset per run), or None outside a StoryMode run (a
    harness driver makes one visit, so it needs none)."""
    from modules.context import context

    failed = getattr(context.bot_mode_instance, "_ball_topoff_failed", None)
    return failed if isinstance(failed, set) else None


def _memo_add() -> None:
    failed = _memo()
    if failed is not None:
        failed.add(sootopolis_key())


def sootopolis_ball_forecast(basket_plan, money: int, basket_prices: dict) -> "dict | None":
    """Called by `league_reserve._stock_basket_early` BEFORE any walk, with RULING 18's basket plan.

    Returns None when `POKEBOT_R23_BALLRESTOCK` is OFF, having read nothing but that variable: the OFF path gains no
    report key, no yield and no move. Otherwise a dict whose `walk` is True only in mode `1` with a non-empty forecast:
    the caller may then walk for the balls alone. `observe` logs the forecast and never walks for it. Never raises: a
    failed forecast is a named `topoff-failed` line, memoised, and no ball walk.
    ⛔ `blocked` (a memo hit, or this forecast failing) stops the COUNTER phase too, not only the ball-only walk: a
    failure at Sootopolis is not retried in the same run, even on a visit the basket makes anyway (the 9b recon, F8)."""
    import os

    mode, error = parse_flag(os.environ.get("POKEBOT_R23_BALLRESTOCK"))
    if error:
        _emit(f"[BALLS-BUY] why=topoff-flag mart={sootopolis_key()} reason={error}")
    if mode not in ("observe", "1"):
        return None
    out = {"mode": mode, "walk": False, "blocked": False, "forecast": [], "reason": ""}
    failed = _memo()
    if failed is not None and sootopolis_key() in failed:
        out["reason"] = "a ball phase failed here earlier this run (memo)"
        out["blocked"] = True
        _emit(log_line("topoff-skip", mart=sootopolis_key(), ball="-", bought=0, premier=0, spare_before="?",
                       spare_after="?", money_before="?", money_after="?", reason=out["reason"]))
        return out
    try:
        from modules.story.league_reserve import _stock_by_name
        from modules.story.victory_road import LEAGUE_BASKET

        live = _inputs(None)
        names = [name for name, _ in LEAGUE_BASKET]
        forecast = forecast_after_basket(
            raw_basket_stock=_stock_by_name(names), basket_plan=basket_plan, basket_prices=basket_prices,
            league_prices={name: live["price_of"](name) for name in names}, money=money, spare=live["spare"],
            flags=live["flags"], sold=SOOTOPOLIS_STATIC_SOLD, allowed=_allowed(),
            ball_prices={name: live["price_of"](name) for name in SOOTOPOLIS_STATIC_SOLD}, lim=limits(),
            fault_floor=_fault_floor())
    except Exception as error:  # noqa: BLE001 - a forecast failure moves nothing: it is reported, memoised, no ball walk
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        _memo_add()
        out["blocked"] = True
        out["reason"] = f"the forecast raised {error!r} (nothing moved)"
        _emit(log_line("topoff-failed", mart=sootopolis_key(), ball="-", bought=0, premier=0, spare_before="?",
                       spare_after="?", money_before="?", money_after="?", reason=out["reason"]))
        return out
    out.update(forecast=forecast["lines"], reason=forecast["reason"], floor=forecast["floor"],
               spare=forecast["spare"], money_after_basket=forecast["money_after_basket"],
               walk=mode == "1" and bool(forecast["lines"]))
    _emit(log_line("topoff-observe" if mode == "observe" else "topoff-forecast", mart=sootopolis_key(),
                   ball=forecast["ball"] or "-", bought=0, premier=0, spare_before=forecast["spare"],
                   spare_after=forecast["spare"], money_before=forecast["money_after_basket"],
                   money_after=forecast["money_after_basket"], reason=forecast["reason"],
                   extra=f" plan={forecast['lines']} floor={forecast['floor']} walk={out['walk']}"))
    return out


def sootopolis_ball_phase(report: dict) -> Generator:
    """At the Sootopolis clerk, on the shop's main menu, AFTER RULING 18's basket lines (or instead of them, on a
    ball-only visit). Mode `1` only; the caller decides that.

    Re-plans from the LIVE wallet, bag and stock list (so a short basket purchase, which leaves more of the basket
    missing, raises the floor by itself), buys through `buy_in_shop`, and verifies by the bag delta of the ball bought.
    ⛔ It writes ONLY under `report["balls"]`: R18's keys (`returned`, `bought`, `money_after`, the readings) drive the
    walk back and the basket's grade, and step 9a's errand pattern writes those very names (the 9b recon, F3).
    ⛔ NEVER raises: a failure is a `topoff-failed` line and a memo entry, and the basket's own outcome stands. The caller
    (`_stock_basket_early`) always closes the menu and walks back across afterwards. An outer close mid-purchase is
    logged (`topoff-closed`) and memoised, then allowed to proceed."""
    import os

    from modules.items import get_item_bag, get_item_by_name
    from modules.mart import get_mart_buyable_items
    from modules.modes.util.higher_level_actions import buy_in_shop

    balls = report.setdefault("balls", {})
    balls["phase"] = "started"
    live = None
    try:
        if os.environ.get("POKEBOT_R23_FAULT_BALLRAISE") == "1":
            raise RuntimeError("POKEBOT_R23_FAULT_BALLRAISE: the ball phase raises on purpose (menu open, nothing bought)")
        live = _inputs(None)
        floor_money = _fault_floor()
        if floor_money is None:
            floor_money = live["floor"]
        sold = [item.name for item in get_mart_buyable_items()]   # ⛔ the menu is open: `sMartInfo` is current
        ball = best_ball(sold, _allowed(), {name: live["price_of"](name) for name in sold if name in UNCONDITIONAL})
        price = live["price_of"](ball) if ball else None
        lines, reason = ball_topoff_plan(spare=live["spare"], money=live["money"], ball=ball, price=price,
                                         stage_name=live["stage"], floor_money=floor_money, lim=limits())
        balls.update(lines=lines, live_reason=reason, live_floor=floor_money)
        if not lines:
            balls["phase"] = "none"
            _emit(log_line("topoff-none", mart=sootopolis_key(), ball=ball or "-", bought=0, premier=0,
                           spare_before=live["spare"], spare_after=live["spare"], money_before=live["money"],
                           money_after=live["money"], reason=reason, extra=f" floor={floor_money}"))
            return
        counted = sorted({ball, "Premier Ball"})
        before = {name: get_item_bag().quantity_of(get_item_by_name(name)) for name in counted}
        shopping = [(get_item_by_name(name), qty) for name, qty in lines]
        yield from buy_in_shop(shopping)
        yield                                                        # the bag cache is per frame
        after = {name: get_item_bag().quantity_of(get_item_by_name(name)) for name in counted}
        planned = sum(qty for _, qty in lines)
        balls["bought"] = after[ball] - before[ball]
        balls["premier"] = after["Premier Ball"] - before["Premier Ball"] if ball != "Premier Ball" else 0
        balls["spare_after"] = int(get_item_bag().number_of_balls_except_master_ball)
        from modules.player import get_player

        balls["money_after"] = int(get_player().money)
        balls["ok"] = balls["bought"] == planned
        balls["phase"] = "done"
        if not balls["ok"]:
            _memo_add()
            balls["why"] = f"bag delta {balls['bought']} != planned {planned}"
        _emit(log_line("topoff" if balls["ok"] else "topoff-failed", mart=sootopolis_key(), ball=ball,
                       bought=balls["bought"], premier=balls["premier"], spare_before=live["spare"],
                       spare_after=balls["spare_after"], money_before=live["money"], money_after=balls["money_after"],
                       reason=reason if balls["ok"] else balls["why"], extra=f" floor={floor_money}"))
    except GeneratorExit:  # an OUTER bound (R18's EARLY_BASKET_BUDGET) closed the visit mid-purchase
        _memo_add()
        balls["phase"] = "closed"
        _emit(log_line("topoff-closed", mart=sootopolis_key(), ball="-", bought="?", premier="?",
                       spare_before=live["spare"] if live else "?", spare_after="?",
                       money_before=live["money"] if live else "?", money_after="?",
                       reason="the basket visit's budget closed the ball phase mid-purchase (R18 walks back)"))
        raise
    except Exception as error:  # noqa: BLE001 - the basket's outcome stands; the failure is logged and memoised
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        _memo_add()
        balls["phase"] = "failed"
        balls["error"] = repr(error)
        _emit(log_line("topoff-failed", mart=sootopolis_key(), ball="-", bought=0, premier=0,
                       spare_before=live["spare"] if live else "?", spare_after="?",
                       money_before=live["money"] if live else "?", money_after="?",
                       reason=f"the ball phase raised {error!r}; the basket's outcome stands"))
