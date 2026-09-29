"""
USER RULINGS 23 + 26, design v2 step 9a (BB): top off the BALL stock with the best ball the mart sells, in BOUNDED
batches, as a piggyback on a Pokémon Center heal. Behind `POKEBOT_R23_BALLRESTOCK` (default OFF; `observe` plans and
logs without walking; `1` buys).

RULING 23 (06, 2026-09-29): no per-run spending ceiling; purchases in bounded batches, topped off periodically the way
healing items are; the BEST ball the current shop sells; RULING 18's League basket and reserve still stand.
RULING 26: stock is maintained all game.

WHAT THIS FILE IS
  * PURE planning (`limits`, `best_ball`, `stage`, `floor`, `ball_topoff_plan`, `plan_lines`), importable with no
    emulator and gated by `tools/story-dev/probe_stock_topoff.py`.
  * The emulator ERRAND (`ball_topoff_errand`), called from ONE place: the end of `heal_in_pokemon_center`
    (`modules/modes/util/higher_level_actions.py`), after the heal's own stable-exit wait.

THE NUMBERS (a bounded DEFAULT; the batch size is the user's Q1, shown to them — v2 note §4):
  * TRIGGER = DEX_CATCH_BALL_RESERVE + DEX_CATCH_MAX_EXPECTED_THROWS = 20: top off exactly when the bot can no longer
    pay for one maximum-admissible dex catch above the reserve the in-battle bail enforces.
  * TARGET = MAX_BALLS_PER_TRIP = 30: the record's own purchase unit (`DEX_CATCH_MAX_EXPECTED_THROWS` was "sized so the
    30-ball Rustboro purchase covers ~3 hard catches").
  * BATCH_CAP = MAX_BALLS_PER_TRIP × POKE_BALL_PRICE = ₽6,000 per visit, and never more than HALF of (money − floor):
    one whiteout halves the money, so a batch can never be what makes the next heal unaffordable.
  * floor = CASH_FLOOR, plus 2 × the League basket's missing cost once the reserve era starts (RULING 18 stands).
  Each is IMPORTED at call time, never copied, so a change to the source constant moves this with it.

⛔ SAFETY PROPERTIES (each has a gate row)
  * OFF reads nothing and yields nothing; `observe` and an empty plan yield nothing either. The heal's extra stable
    wait runs ONLY when the errand actually moved the avatar.
  * `stage()` and `floor()` FAIL CLOSED: an unreadable flag means NO purchase, with a named reason (a stage that fell
    back to MID would drop the basket floor to ₽1,000 — exactly the failure RULING 18 exists to prevent).
  * The quantity is clamped at 0 (below the floor Python's // would go NEGATIVE, and `buy_in_shop` raises on it), and
    at the in-game max min(money // price, 99) (`shop.c:1046-1051`; `buy_in_shop`'s quantity loop never ends above it).
  * A city whose errand fails — walk, bound, OR a bag delta that is not the plan — goes into the run's failed-walk
    memo (`StoryMode._ball_topoff_failed`, reset per run) and is not walked again this run.
  * Whitelist: Rustboro only (step 9a). Its mart sells Poké Balls from the start (`RustboroCity_Mart/scripts.inc`).
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
FLAG_NAMES = ("IS_CHAMPION", "ENTERED_ELITE_FOUR", "SOOTOPOLIS_ARCHIE_MAXIE_LEAVE", "BADGE01_GET")
MAX_PER_LINE = 99
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
    """PURE. The game stage from the four flags, checked in this order: IS_CHAMPION → POSTGAME; ENTERED_ELITE_FOUR →
    LEAGUE (entered and lost; nothing clears it); the reserve-era flag → BASKET_ERA; no BADGE01 → PRE_GYM1; else MID.
    None (NO purchase) if any flag is missing — fail closed."""
    try:
        if flags["IS_CHAMPION"]:
            return "POSTGAME"
        if flags["ENTERED_ELITE_FOUR"]:
            return "LEAGUE"
        if flags["SOOTOPOLIS_ARCHIE_MAXIE_LEAVE"]:
            return "BASKET_ERA"
        if not flags["BADGE01_GET"]:
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
    qty = min(lim["target"] - spare, budget // price, money // price, MAX_PER_LINE * 10)
    if qty <= 0:
        return [], f"cannot afford one {ball} (budget {budget}, price {price})"
    lines = plan_lines(ball, qty)
    if any(q > min(money // price, MAX_PER_LINE) for _, q in lines):
        return [], f"a line exceeds the in-game max ({lines})"
    return lines, f"top off {qty} x {ball} (spare {spare} <= trigger {lim['trigger']}; budget {budget})"


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
    """Live reads for the plan. Any failure propagates to the errand's caller (the heal's guarded piggyback)."""
    from modules.items import get_item_bag, get_item_by_name
    from modules.memory import get_event_flag
    from modules.player import get_player

    flags = {name: bool(get_event_flag(name)) for name in FLAG_NAMES}
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
        moved_ok = finished and report.get("ok", False)
    except Exception as error:  # noqa: BLE001 - reported below; an abort is re-raised first
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        report["error"] = repr(error)
    if not moved_ok:
        failed.add(city)
        _emit(log_line("topoff-failed", mart=city, ball=ball, bought=report.get("bought", 0),
                       premier=report.get("premier", 0), spare_before=live["spare"], spare_after=report.get("spare_after", "?"),
                       money_before=live["money"], money_after=report.get("money_after", "?"),
                       reason=report.get("error") or report.get("why") or "the errand's frame bound expired"))
        yield from _yield_bounded_by_frames(_recover(exit_map, exit_tile, report), RECOVERY_FRAMES)
    return True


def _walk_buy_return(mart, exit_map, exit_tile, lines, live, reason, report) -> Generator:
    """Walk to the clerk, buy `lines` (re-planned against the LIVE list), verify by the bag delta, walk back."""
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
    if report["ok"]:
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

    yield from _close_shop_and_dialogs(report)
    yield from _navigate_riding_out(exit_map, exit_tile)
    yield from wait_until_truly_controllable()
