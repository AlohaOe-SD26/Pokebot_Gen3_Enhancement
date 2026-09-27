r"""GATE — USER RULING 18: buy the League basket early, and RESERVE it until the Elite Four (`#26-ch23money`, 2026-09-26).

WHY: whiteouts halve the wallet and never touch the bag, so cash carried into the Juan attempts is cash at risk. The
module is `modules/story/league_reserve.py`. This gate pins what a drive cannot keep true by itself — and every check
here is a shape the adversarial recon named as a way the ruling could BACKFIRE:

  R1  THE RESERVE LIVES ONLY IN THE BATTLE STRATEGY: `_maybe_use_item` filters `medicine` BEFORE `options` is derived
      and before either policy runs (a veto after the policy would lose the Super-Potion fallback), inside a try that
      falls through UNLOCKED; and NO bag reader (`bag_healing_stock`, `basket_to_buy`, `ch23_chapter_done`, R1's
      `ch24_readiness_shortfall`, `heal_party_from_bag`, `plan_healing`) references the reserve;
  R2  `apply_reserve` (PURE) subtracts, drops exhausted lines, leaves other items untouched and in order;
  R3  `reserve_active` is STATE-DERIVED: off before the Juan era; on in it; off once `ENTERED_ELITE_FOUR` or
      `IS_CHAMPION` is set or on a sealed §Ch24 map; and a BROKEN reserve read fails UNLOCKED (input unchanged);
  R4  `early_basket_plan` (PURE): the missing quantities only, cheapest-to-leak first, the floor kept, 99 capped,
      unsold lines skipped;
  R5  §Ch22 L1 runs `heal_and_stock_before_the_gym` before `enter_gym`; it heals, buys, and re-heals only if the trip
      walked; the driver calls the same function;
  R6  the five fault arms are read in production and registered in `29`.
FAULT ARMS (built in, each must turn its check red): the filter moved after `options`; an `apply_reserve` that
filters nothing; a `reserve_active` that ignores `ENTERED_ELITE_FOUR`; a filter that lets the error escape; a plan
that ignores the floor; the purchase moved after `enter_gym`.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_league_reserve.py
"""
from __future__ import annotations

import ast
import io
import os
import re
import sys
import tokenize
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.story import league_reserve as LR  # noqa: E402

STORY = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"
GYM = SANDBOX / "modules" / "story" / "sootopolis_gym.py"
MODULE = SANDBOX / "modules" / "story" / "league_reserve.py"
HARNESS = ROOT / "tools" / "story-dev" / "story_harness.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
BAG_READERS = {
    SANDBOX / "modules" / "story" / "victory_road.py": ("bag_healing_stock", "basket_to_buy", "ch23_chapter_done",
                                                       "stock_for_the_elite_four"),
    SANDBOX / "modules" / "story" / "pokemon_league.py": ("ch24_readiness_shortfall", "heal_party_from_bag"),
    SANDBOX / "modules" / "story" / "overworld_items.py": ("plan_healing",),
}
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def _fn(src: str, name: str) -> str:
    fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name)
    return _strip_comments(ast.get_source_segment(src, fn) or "")


FILTER_CALL = "medicine = _league_reserve_filter(medicine)"
OPTIONS = "options = [opt for opt in medicine if opt[2] > 0]"


def r1(story_src: str, readers: dict, sink=None):
    code = _fn(story_src, "_maybe_use_item")
    i_filter, i_options = code.find(FILTER_CALL), code.find(OPTIONS)
    i_hp, i_status = code.find("choose_healing_item("), code.find("choose_status_or_revive_item(")
    check(-1 not in (i_filter, i_options, i_hp, i_status) and i_filter < i_options < i_hp < i_status,
          "R1 the reserve filters `medicine` BEFORE `options` and before both policies", sink)
    window = code[max(0, i_filter - 400):i_filter + 200]
    check("try:" in window and "except Exception:" in window[window.find(FILTER_CALL):],
          "R1 … inside a try whose except falls through (fail UNLOCKED, even on an import error)", sink)
    check(code.count("_league_reserve_filter(") == 1, "R1 exactly one filter call in the strategy", sink)
    for path, fns in readers.items():
        src = path.read_text(encoding="utf-8") if isinstance(path, Path) else path
        for fn in fns:
            body = _fn(src, fn)
            check("league_reserve" not in body and "reserved_quantities" not in body and "apply_reserve" not in body,
                  f"R1 bag reader `{fn}` reads the RAW bag (no reserve)", sink)


class _Item:
    def __init__(self, name):
        self.name = name


def r2(apply, sink=None):
    hp, fh, sp, rv, fr = (_Item("Hyper Potion"), _Item("Full Heal"), _Item("Super Potion"), _Item("Revive"),
                          _Item("Full Restore"))
    med = [(sp, 5, 50), (hp, 36, 200), (fh, 8, 0), (rv, 2, 0), (fr, 4, 255)]
    out = apply(med, {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Full Restore": 3})
    check(out == [(sp, 5, 50), (hp, 6, 200), (fr, 1, 255)],
          f"R2 subtract (Full Restore too), drop exhausted, keep others in order: {out}", sink)
    check(apply(med, {}) == med, "R2 an empty reserve changes nothing", sink)
    check(apply([(hp, 30, 200)], {"Hyper Potion": 30}) == [], "R2 exactly the reserve ⇒ none usable", sink)


def r3(module, sink=None):
    real_flag, real_sealed = module._flag, module._on_sealed_map

    def world(flags, sealed=False):
        module._flag = lambda name: bool(flags.get(name, False))
        module._on_sealed_map = lambda: sealed

    try:
        world({})
        check(module.reserve_active() is False, "R3 before the Juan era ⇒ OFF", sink)
        world({"SOOTOPOLIS_ARCHIE_MAXIE_LEAVE": True})
        check(module.reserve_active() is True, "R3 in the Juan era (through Victory Road and §Ch24 training) ⇒ ON", sink)
        world({"SOOTOPOLIS_ARCHIE_MAXIE_LEAVE": True, "ENTERED_ELITE_FOUR": True})
        check(module.reserve_active() is False, "R3 ENTERED_ELITE_FOUR ⇒ OFF (persists across whiteouts)", sink)
        world({"SOOTOPOLIS_ARCHIE_MAXIE_LEAVE": True, "IS_CHAMPION": True})
        check(module.reserve_active() is False, "R3 IS_CHAMPION ⇒ OFF", sink)
        world({"SOOTOPOLIS_ARCHIE_MAXIE_LEAVE": True}, sealed=True)
        check(module.reserve_active() is False, "R3 on a sealed §Ch24 map ⇒ OFF (covers the harness E4 drivers)", sink)
        world({"SOOTOPOLIS_ARCHIE_MAXIE_LEAVE": True})
        hp = _Item("Hyper Potion")
        med = [(hp, 12, 200)]
        os.environ["POKEBOT_RESERVE_FAULT_RAISE"] = "1"
        try:
            got = module.filter_medicine_for_reserve(med)
            check(got == med, "R3 a BROKEN reserve read fails UNLOCKED (input returned unchanged)", sink)
        except Exception as error:  # noqa: BLE001 - that IS the failure this check exists to catch
            check(False, f"R3 a broken reserve read ESCAPED the filter ({type(error).__name__})", sink)
        finally:
            os.environ.pop("POKEBOT_RESERVE_FAULT_RAISE", None)
    finally:
        module._flag, module._on_sealed_map = real_flag, real_sealed


PRICES = {"Hyper Potion": 1200, "Full Heal": 600, "Revive": 1500, "Full Restore": 3000}


def r4(plan, sink=None):
    check(plan({}, 67_466, PRICES) == [("Revive", 3), ("Full Heal", 8), ("Hyper Potion", 30)],
          "R4 a rich wallet buys the whole early basket, cheapest-to-leak first", sink)
    check(plan({}, 38_333, PRICES) == [("Revive", 3), ("Full Heal", 8), ("Hyper Potion", 23)],
          "R4 a smaller wallet fills Hyper Potion with what is left above the floor", sink)
    check(plan({}, 5_000, PRICES) == [("Revive", 2), ("Full Heal", 1)],
          "R4 floor ₽1,000 kept: ₽4,000 buys two Revives, and the ₽1,000 left buys one Full Heal", sink)
    check(plan({"Revive": 3, "Full Heal": 8, "Hyper Potion": 25}, 67_466, PRICES) == [("Hyper Potion", 5)],
          "R4 only the MISSING quantities", sink)
    check(plan({"Revive": 3, "Full Heal": 8, "Hyper Potion": 40}, 67_466, PRICES) == [],
          "R4 nothing missing ⇒ nothing bought", sink)
    check(plan({}, 900, PRICES) == [], "R4 below the floor ⇒ nothing bought", sink)
    check(all(n != "Full Restore" for n, _q in plan({}, 99_999, PRICES)), "R4 never Full Restore (League-only)", sink)
    check(plan({}, 67_466, PRICES, sold_here={"Hyper Potion"}) == [("Hyper Potion", 30)],
          "R4 lines the shop does not sell are skipped", sink)


def r5(gym_src: str, harness_src: str, sink=None):
    chapter = _fn(gym_src, "do_sootopolis_gym_chapter")
    i_stock, i_enter = chapter.find("yield from heal_and_stock_before_the_gym(report)"), chapter.find(
        "yield from enter_gym()")
    check(-1 not in (i_stock, i_enter) and i_stock < i_enter, "R5 L1 heals + stocks BEFORE entering the gym", sink)
    fn = _fn(gym_src, "heal_and_stock_before_the_gym")
    a, b, c = (fn.find("yield from _heal_before_the_gym(report)"), fn.find("yield from stock_basket_early(early)"),
               fn.rfind("yield from _heal_before_the_gym(report)"))
    check(-1 not in (a, b, c) and a < b < c and 'if early.get("walked"):' in fn[b:c],
          "R5 heal → buy → re-heal ONLY if the trip walked", sink)
    cls = next(n for n in ast.parse(harness_src).body if isinstance(n, ast.ClassDef) and n.name == "EarlyBasketMode")
    drv = _strip_comments(ast.get_source_segment(harness_src, cls) or "")
    check("yield from heal_and_stock_before_the_gym(ch22)" in drv and "yield from enter_gym()" in drv,
          "R5 the driver calls the same two functions", sink)


def r7(module_src: str, sink=None):
    """R7 — NEVER STRAND THE BOT ON THE MART SIDE (measured 2026-09-26: from there the planner finds no way back)."""
    tree = ast.parse(module_src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_stock_basket_early")
    code = _strip_comments(ast.get_source_segment(module_src, fn) or "")
    i_back = code.find("back = calculate_path((city, SOOTOPOLIS_MART_FRONT), (city, SOOTOPOLIS_MART_WAYPOINT))")
    i_cross = code.find('report["crossed"] = True')
    i_go = code.find("yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY_MART, stand)")
    check(-1 not in (i_back, i_cross, i_go) and i_back < i_cross < i_go,
          "R7 the WAY BACK is planned from the PC side BEFORE crossing", sink)
    top_level_calls = [ast.get_source_segment(module_src, st) for st in fn.body if isinstance(st, ast.Expr)]
    check(any("return_across_from_the_mart(report)" in (c or "") for c in top_level_calls),
          "R7 the walk back runs at the function's top level — OUTSIDE the shop's try, so a shop error still returns",
          sink)
    ret = _strip_comments(ast.get_source_segment(module_src, next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "return_across_from_the_mart")) or "")
    i_none, i_plan, i_follow = (ret.find("if remaining is None:"),
                                ret.find("yield from _navigate_riding_out(city, SOOTOPOLIS_MART_WAYPOINT)"),
                                ret.find("yield from follow_waypoints(remaining)"))
    check(-1 not in (i_none, i_plan, i_follow) and i_none < i_plan < i_follow,
          "R7 the walk back FOLLOWS the stored path; the planner is only the off-path last resort", sink)
    outer = _strip_comments(ast.get_source_segment(module_src, next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stock_basket_early")) or "")
    check('if report.get("crossed") and not report.get("returned"):' in outer
          and "return_across_from_the_mart(report)" in outer,
          "R7 an expired budget on the far side still triggers one bounded walk back", sink)
    i_close, i_wait = ret.find("yield from _close_shop_and_dialogs(report)"), ret.find(
        "yield from wait_until_truly_controllable()")
    check(-1 not in (i_close, i_wait) and i_close < i_wait,
          "R7 the walk back CLOSES an open shop menu / dialog before waiting for control", sink)
    i_tel, i_raise = outer.find("debug_logger.event("), outer.find("STRANDED on the Mart side")
    check(-1 not in (i_tel, i_raise) and i_tel < i_raise,
          "R7 a bot still stranded after the retry fails BY NAME, after its telemetry line", sink)


ARMS = ("POKEBOT_RESERVE_FAULT_NOLOCK", "POKEBOT_RESERVE_FAULT_RAISE", "POKEBOT_RESERVE_FAULT_FORCEON",
        "POKEBOT_RESERVE_FAULT_NOBUY", "POKEBOT_RESERVE_FAULT_FLOOR", "POKEBOT_RESERVE_FAULT_BUDGET")


def r6(module_src: str):
    code = _strip_comments(module_src)
    registry = REGISTRY.read_text(encoding="utf-8")
    for arm in ARMS:
        check(f'os.environ.get("{arm}")' in code and f"`{arm}`" in registry,
              f"R6 {arm} is read in production and registered in 29")


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 18: the early League basket and its reserve")
    print("=" * 92)
    story_src = STORY.read_text(encoding="utf-8")
    gym_src = GYM.read_text(encoding="utf-8")
    module_src = MODULE.read_text(encoding="utf-8")
    harness_src = HARNESS.read_text(encoding="utf-8")
    print("\n== R1 the reserve lives only in the battle strategy ==")
    r1(story_src, BAG_READERS)
    print("\n== R2 apply_reserve (pure) ==")
    r2(LR.apply_reserve)
    print("\n== R3 state-derived arming + fail unlocked ==")
    r3(LR)
    print("\n== R4 early_basket_plan (pure) ==")
    r4(LR.early_basket_plan)
    print("\n== R5 §Ch22 L1 wiring ==")
    r5(gym_src, harness_src)
    print("\n== R6 fault arms ==")
    r6(module_src)
    print("\n== R7 never strand the bot on the Mart side ==")
    r7(module_src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    moved = story_src.replace(FILTER_CALL, "pass", 1).replace(OPTIONS, OPTIONS + "\n        " + FILTER_CALL, 1)
    r1(moved, {}, sink)
    check(bool(sink), f"FAULT the filter moved AFTER `options` FAILS R1 ({len(sink)} caught)")
    sink = []
    r2(lambda med, reserved: list(med), sink)
    check(bool(sink), f"FAULT an apply_reserve that filters nothing FAILS R2 ({len(sink)} caught)")
    sink = []
    real_active, real_filter = LR.reserve_active, LR.filter_medicine_for_reserve

    def ignores_entered():
        if not LR._flag(LR.RESERVE_ERA_FLAG):
            return False
        return not LR._on_sealed_map()

    try:
        LR.reserve_active = ignores_entered
        r3(LR, sink)
    finally:
        LR.reserve_active = real_active
    check(bool(sink), f"FAULT a reserve_active that ignores ENTERED_ELITE_FOUR FAILS R3 ({len(sink)} caught)")
    sink = []

    def escapes(medicine):
        return LR.apply_reserve(medicine, LR.reserved_quantities())

    try:
        LR.filter_medicine_for_reserve = escapes
        r3(LR, sink)
    finally:
        LR.filter_medicine_for_reserve = real_filter
    check(bool(sink), f"FAULT a filter that lets the error escape FAILS R3 ({len(sink)} caught)")
    sink = []
    r4(lambda stock, money, prices, **kw: LR.early_basket_plan(stock, money, prices, floor=0,
                                                               sold_here=kw.get("sold_here")), sink)
    check(bool(sink), f"FAULT a plan that ignores the floor FAILS R4 ({len(sink)} caught)")
    sink = []
    swapped = gym_src.replace("                yield from heal_and_stock_before_the_gym(report)\n"
                              "                yield from enter_gym()\n",
                              "                yield from enter_gym()\n"
                              "                yield from heal_and_stock_before_the_gym(report)\n", 1)
    r5(swapped, harness_src, sink)
    check(swapped != gym_src and bool(sink), f"FAULT the purchase moved after enter_gym FAILS R5 ({len(sink)} caught)")
    sink = []
    inside = module_src.replace("        shop_error = error\n",
                                "        shop_error = error\n        yield from return_across_from_the_mart(report)\n", 1)
    inside = inside.replace("    yield from return_across_from_the_mart(report)\n    if shop_error is not None:",
                            "    if shop_error is not None:", 1)
    r7(inside, sink)
    check(inside != module_src and bool(sink),
          f"FAULT the walk back moved INSIDE the shop's except FAILS R7 ({len(sink)} caught)")
    sink = []
    late = module_src.replace(
        "        back = calculate_path((city, SOOTOPOLIS_MART_FRONT), (city, SOOTOPOLIS_MART_WAYPOINT))\n",
        "        back = []\n", 1)
    r7(late, sink)
    check(late != module_src and bool(sink),
          f"FAULT a way back that is not planned before crossing FAILS R7 ({len(sink)} caught)")
    sink = []
    commented = story_src.replace(OPTIONS, OPTIONS + "\n        # " + FILTER_CALL, 1)
    r1(commented, {}, sink)
    check(commented != story_src and len(sink) == 0,
          "NO FALSE POSITIVE: a commented-out filter call does not change R1's verdict")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
