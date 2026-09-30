"""GATE — USER RULINGS 23 + 26, design v2 step 9b (BB consumer b): the ball top-off inside RULING 18's Sootopolis
League-basket visit (`modules/story/stock_topoff.py` `forecast_after_basket` / `sootopolis_ball_forecast` /
`sootopolis_ball_phase`, called from `modules/story/league_reserve.py` `_stock_basket_early` and `_shop`), and the
`--driver earlybasket` grade that measures it.

WHY. This consumer spends money inside a visit that must NEVER strand the bot on the Mart side of Sootopolis (KI-103),
and inside RULING 18's purchase, whose own outcome must not change. The ways it can hurt: forecasting from the wrong
wallet or the wrong floor (step 0 measured 5 Ultras and 0 Ultras against the right 1); walking for balls in `observe`;
changing anything when OFF; letting a ball failure change the basket's outcome or escape; losing an outer close
silently; and — found by the 9b recon (F1) — a SECOND errand on the same report dict skipping the walk back, because
§Ch22 passes one dict to every Juan attempt. Each has an EXECUTING row here, and each row has a mutant that turns it red.

ROWS
  F1-F6   PURE `forecast_after_basket`: the post_hm07 numbers (1 Ultra), the complete-basket visit (1), its own output
          (0, the floor binds), the live floor lever (5), above the trigger, and an unreadable stage (fail closed).
  K1      the memo key is `PokemonCenter.SootopolisCity.name` and Sootopolis is NOT in step 9a's whitelist.
  O1-O7   `sootopolis_ball_forecast` EXECUTED with stubs: OFF (unset, `0`) reads NOTHING and returns None; a typo is
          OFF with a 9b-specific `why=topoff-flag` line; `observe` never walks; `1` walks; a memo hit and a failed
          forecast BLOCK (no walk, no counter phase) and a failure is memoised; an abort is re-raised.
  P1-P8   `sootopolis_ball_phase` EXECUTED with a fake bag, a fake shop and a stub `buy_in_shop`: success (and R18's
          report keys untouched: it writes only under `report["balls"]`); a short delta; an empty live plan (no buy, no
          yield); the BALLRAISE fault and a raising `buy_in_shop` (both swallowed and memoised); an abort (re-raised); an
          outer close mid-buy (logged, memoised, closes cleanly); the live floor lever.
  S1-S9   `league_reserve` EXECUTED with stubs: OFF + complete basket = "nothing missing" with no `balls` key and no
          yield; `1` walks for balls alone ("balls only", no EB-PLANNED); `observe` and an empty forecast do not walk;
          `_shop` OFF still raises on a Mart selling none of the basket; a ball-only `_shop` skips the basket and runs
          the phase; a blocked forecast skips the phase; basket-then-balls order; and F1: a second `stock_basket_early`
          on the same dict starts CLEAN (the first errand archived, not discarded).
  A1-A4   by AST (comments stripped): the forecast precedes the early return, which precedes the walk; the phase is
          called only from `_shop`; no `yield` inside the phase's GeneratorExit handler; the driver reads the balls'
          end state BEFORE restoring the fixture, prices only unconditional balls, and checks production's forecast.
  M1-M16  source mutants, each with the EXACT set of rows it must turn red; N1 a comment-only edit (none red).
          ⚠ Gate run 1 (after the predictions) FAILED two written sets: M7 (the abort stubs synthesized a NEW
          exception, which the real `reraise_if_aborting` never does; fixed) and M11 (a typo shares the OFF branch,
          so O3 is red too; the set was incomplete). M15/M16 were then added: no mutant covered P6 or O7's abort.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_stock_topoff_sootopolis.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import io
import os
import pathlib
import sys
import tokenize
import types
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
T_PATH = SANDBOX / "modules" / "story" / "stock_topoff.py"
LR_PATH = SANDBOX / "modules" / "story" / "league_reserve.py"
HARNESS = HERE / "story_harness.py"
T_NAME = "modules.story.stock_topoff"
LR_NAME = "modules.story.league_reserve"

import modules.story.league_reserve  # noqa: E402,F401
import modules.story.stock_topoff  # noqa: E402,F401

FAILURES: list[str] = []
PRICES = {"Ultra Ball": 1200, "Great Ball": 600, "Poké Ball": 200, "Premier Ball": 200, "Revive": 1500,
          "Full Heal": 600, "Hyper Potion": 1200, "Full Restore": 3000}
ERA = {"champion": False, "entered_e4": False, "reserve_era": True, "badge1": True}
PLAN = [("Revive", 3), ("Full Heal", 8), ("Hyper Potion", 30)]
BASKET_PRICES = {"Revive": 1500, "Full Heal": 600, "Hyper Potion": 1200}
EMPTY_BASKET = {"Hyper Potion": 0, "Full Restore": 0, "Full Heal": 0, "Revive": 0}
FULL_BASKET = {"Hyper Potion": 30, "Full Restore": 0, "Full Heal": 8, "Revive": 3}
ALL_BALLS = {"Ultra Ball", "Great Ball", "Poké Ball", "Premier Ball", "Net Ball", "Nest Ball", "Dive Ball",
             "Repeat Ball", "Timer Ball", "Luxury Ball"}


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def mods():
    return sys.modules[T_NAME], sys.modules[LR_NAME]


def _strip_comments(src: str) -> str:
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and tok.string.startswith(('"""', "'''")):
            continue
        out.append(tok)
    return tokenize.untokenize(out)


class Patch:
    """Set attributes and env vars; restore everything on exit."""

    def __init__(self):
        self.saved = []
        self.env = {}

    def set(self, obj, name, value):
        self.saved.append((obj, name, getattr(obj, name, None), hasattr(obj, name)))
        setattr(obj, name, value)

    def setenv(self, **kw):
        for k, v in kw.items():
            if k not in self.env:
                self.env[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        for obj, name, value, had in reversed(self.saved):
            if had:
                setattr(obj, name, value)
            else:
                try:
                    delattr(obj, name)
                except AttributeError:
                    pass
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def drain(gen, limit=1000):
    """Run a generator to completion; (return value, yields)."""
    n = 0
    try:
        while True:
            next(gen)
            n += 1
            if n > limit:
                raise RuntimeError("generator did not finish")
    except StopIteration as stop:
        return stop.value, n


def row(label, fn, tag, reds):
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if tag:
        if not ok:
            reds.append(label.split()[0])
    else:
        check(label, ok, detail)
        if not ok:
            reds.append(label.split()[0])


def _lim():
    return {"trigger": 20, "target": 30, "batch_cap": 6000}


def _forecast(t, **over):
    kw = dict(raw_basket_stock=dict(EMPTY_BASKET), basket_plan=list(PLAN), basket_prices=BASKET_PRICES,
              league_prices=PRICES, money=67466, spare=18, flags=dict(ERA), sold=("Ultra Ball",), allowed=ALL_BALLS,
              ball_prices={"Ultra Ball": 1200}, lim=_lim(), fault_floor=None)
    kw.update(over)
    return t.forecast_after_basket(**kw)


# ---------------------------------------------------------------------------------------------------------- F rows
def f_rows(tag=""):
    t, _lr = mods()
    reds: list = []

    def f1():
        r = _forecast(t)
        return (r["lines"] == [("Ultra Ball", 1)] and r["money_after_basket"] == 22166 and r["floor"] == 19000,
                f"{r['lines']} money_after={r['money_after_basket']} floor={r['floor']}")

    def f2():
        r = _forecast(t, raw_basket_stock=dict(FULL_BASKET), basket_plan=[], money=22166)
        return r["lines"] == [("Ultra Ball", 1)] and r["floor"] == 19000, f"{r['lines']} floor={r['floor']}"

    def f3():
        r = _forecast(t, raw_basket_stock=dict(FULL_BASKET), basket_plan=[], money=20966, spare=19)
        return (r["lines"] == [] and r["reason"].startswith("cannot afford one Ultra Ball (budget 983"),
                f"{r['lines']} {r['reason']}")

    def f4():
        r = _forecast(t, fault_floor=1000)
        return r["lines"] == [("Ultra Ball", 5)] and r["floor"] == 1000, f"{r['lines']}"

    def f5():
        r = _forecast(t, spare=21)
        return r["lines"] == [] and r["reason"] == "spare 21 > trigger 20", r["reason"]

    def f6():
        r = _forecast(t, flags={"champion": False, "entered_e4": False, "badge1": True})
        return r["lines"] == [] and r["reason"] == "stage unreadable (fail closed)", r["reason"]

    for label, fn in (("F1 post_hm07: 1 Ultra from the POST-basket wallet (22,166) and floor (19,000)", f1),
                      ("F2 a complete basket at 22,166, spare 18: 1 Ultra (the ball-only visit)", f2),
                      ("F3 its own output (20,966, spare 19): nothing, the floor binds (budget 983)", f3),
                      ("F4 the live floor lever (1,000): 5 Ultras", f4),
                      ("F5 spare 21 > trigger: nothing", f5),
                      ("F6 a missing stage flag: nothing (fail closed)", f6)):
        row(label, fn, tag, reds)
    return reds


def k_rows(tag=""):
    t, _lr = mods()
    reds: list = []
    from modules.map_data import PokemonCenter

    def k1():
        wl = {c.name for c in t._whitelist()}
        return (t.sootopolis_key() == PokemonCenter.SootopolisCity.name and t.sootopolis_key() not in wl,
                f"key={t.sootopolis_key()} whitelist={sorted(wl)}")

    row("K1 the memo key is the enum name, and Sootopolis is not in 9a's whitelist", k1, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------------------------- O rows
def _o_env(p, t, lr, *, flag, inputs_raise=None, memo=None, emitted=None):
    from modules.context import context
    from modules.story import early_game as eg

    p.setenv(POKEBOT_R23_BALLRESTOCK=flag, POKEBOT_R23_FAULT_FLOOR=None)

    def inputs(_mode):
        if inputs_raise:
            raise inputs_raise
        return {"stage": "BASKET_ERA", "floor": 109600, "spare": 18, "money": 67466, "flags": dict(ERA),
                "price_of": lambda n: PRICES[n]}

    def reraise(error):
        # FAITHFUL to `early_game.reraise_if_aborting`: it re-raises the error it was GIVEN, never a synthesized one
        # (a stub that raised a new exception made mutant M7 look like it broke abort propagation: gate run 1).
        if "ABORT" in str(error):
            raise error

    p.set(t, "_inputs", inputs)
    p.set(t, "_allowed", lambda: set(ALL_BALLS))
    p.set(t, "_emit", lambda line: emitted.append(line))
    p.set(lr, "_stock_by_name", lambda names: {n: EMPTY_BASKET.get(n, 0) for n in names})
    p.set(eg, "reraise_if_aborting", reraise)
    p.set(context, "bot_mode_instance", SimpleNamespace(_ball_topoff_failed=memo if memo is not None else set()))


def o_rows(tag=""):
    t, lr = mods()
    reds: list = []

    def off(flag):
        def fn():
            emitted: list = []
            with Patch() as p:
                _o_env(p, t, lr, flag=flag, emitted=emitted)

                def boom(*_a, **_k):
                    raise AssertionError("read while OFF")

                p.set(t, "_inputs", boom)
                p.set(t, "_allowed", boom)
                p.set(t, "limits", boom)
                p.set(lr, "_stock_by_name", boom)
                out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
            return out is None and emitted == [], f"out={out} emitted={emitted}"
        return fn

    def o3():
        emitted: list = []
        with Patch() as p:
            _o_env(p, t, lr, flag="yes", emitted=emitted)
            out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
        lines = [ln for ln in emitted if "why=topoff-flag" in ln and "mart=SootopolisCity" in ln]
        return out is None and len(lines) == 1 and len(emitted) == 1, f"out={out} emitted={emitted}"

    def mode(flag, want_walk, want_tag):
        def fn():
            emitted: list = []
            with Patch() as p:
                _o_env(p, t, lr, flag=flag, emitted=emitted)
                out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
            lines = [ln for ln in emitted if f"why={want_tag} " in ln]
            return (out is not None and out["walk"] is want_walk and out["blocked"] is False
                    and out["forecast"] == [("Ultra Ball", 1)] and len(lines) == 1 and len(emitted) == 1
                    and f"walk={want_walk}" in lines[0]), f"out={out} emitted={emitted}"
        return fn

    def o6():
        emitted: list = []
        with Patch() as p:
            _o_env(p, t, lr, flag="1", emitted=emitted, memo={"SootopolisCity"})
            out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
        return (out["walk"] is False and out["blocked"] is True and out["forecast"] == []
                and len([ln for ln in emitted if "why=topoff-skip" in ln]) == 1), f"out={out} emitted={emitted}"

    def o7():
        emitted: list = []
        memo: set = set()
        with Patch() as p:
            _o_env(p, t, lr, flag="1", emitted=emitted, memo=memo, inputs_raise=RuntimeError("bag unreadable"))
            out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
            aborted = False
            try:
                _o_env(p, t, lr, flag="1", emitted=emitted, memo=set(), inputs_raise=RuntimeError("ABORT"))
                t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
            except RuntimeError as error:
                aborted = "ABORT" in str(error)
        return (out["walk"] is False and out["blocked"] is True and "SootopolisCity" in memo and aborted
                and len([ln for ln in emitted if "why=topoff-failed" in ln]) == 1), f"out={out} memo={memo} abort={aborted}"

    for label, fn in (("O1 OFF (unset) reads NOTHING and returns None", off(None)),
                      ("O2 OFF (`0`) reads NOTHING and returns None", off("0")),
                      ("O3 a typo is OFF with ONE 9b-specific `why=topoff-flag mart=SootopolisCity` line", o3),
                      ("O4 `observe` forecasts 1 Ultra and never walks", mode("observe", False, "topoff-observe")),
                      ("O5 `1` forecasts 1 Ultra and walks", mode("1", True, "topoff-forecast")),
                      ("O6 a memo hit BLOCKS (no walk, no counter phase)", o6),
                      ("O7 a failed forecast BLOCKS and is memoised; an abort is re-raised", o7)):
        row(label, fn, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------------------------- P rows
class FakeBag:
    def __init__(self, counts):
        self.counts = dict(counts)

    def quantity_of(self, item):
        return self.counts.get(item.name, 0)

    @property
    def number_of_balls_except_master_ball(self):
        return sum(q for n, q in self.counts.items() if n in ALL_BALLS)


def _p_env(p, t, *, money=22166, buy="ok", emitted, memo, floor_env=None, raise_env=None, calls):
    from modules import items as _items
    from modules import mart as _mart
    from modules import player as _player
    from modules.context import context
    from modules.modes.util import higher_level_actions as _hla
    from modules.story import early_game as eg

    bag = FakeBag({"Poké Ball": 16, "Premier Ball": 1, "Great Ball": 1, "Ultra Ball": 0})
    wallet = {"money": money}
    p.setenv(POKEBOT_R23_FAULT_FLOOR=floor_env, POKEBOT_R23_FAULT_BALLRAISE=raise_env, POKEBOT_R23_BALLRESTOCK="1")

    def inputs(_mode):
        return {"stage": "BASKET_ERA", "floor": 19000, "spare": bag.number_of_balls_except_master_ball,
                "money": wallet["money"], "flags": dict(ERA), "price_of": lambda n: PRICES[n]}

    def buy_in_shop(shopping):
        calls.append(("buy", [(i.name, q) for i, q in shopping]))
        yield
        if buy == "raise":
            raise RuntimeError("Task_ShopMenu is not active")
        if buy == "abort":
            raise RuntimeError("ABORT")
        if buy == "forever":
            while True:
                yield
        for item, qty in shopping:
            got = qty if buy == "ok" else 0
            bag.counts[item.name] = bag.counts.get(item.name, 0) + got
            wallet["money"] -= got * PRICES[item.name]

    def reraise(error):
        # FAITHFUL to `early_game.reraise_if_aborting` (see `_o_env`).
        if "ABORT" in str(error):
            raise error

    p.set(t, "_inputs", inputs)
    p.set(t, "_allowed", lambda: set(ALL_BALLS))
    p.set(t, "_emit", lambda line: emitted.append(line))
    p.set(_mart, "get_mart_buyable_items", lambda: [SimpleNamespace(name=n) for n in ("Ultra Ball", "Hyper Potion",
                                                                                         "Revive", "Full Heal")])
    p.set(_items, "get_item_bag", lambda: bag)
    p.set(_items, "get_item_by_name", lambda n: SimpleNamespace(name=n, price=PRICES[n]))
    p.set(_player, "get_player", lambda: SimpleNamespace(money=wallet["money"]))
    p.set(_hla, "buy_in_shop", buy_in_shop)
    p.set(eg, "reraise_if_aborting", reraise)
    p.set(context, "bot_mode_instance", SimpleNamespace(_ball_topoff_failed=memo))
    return bag


R18_KEYS = {"bought": {"Revive": 3}, "money_after": 22166, "readings": {"EB-PLANNED", "EB-MART", "EB-BOUGHT"},
            "order": ["EB-PLANNED", "EB-MART", "EB-BOUGHT"], "early_basket": "bought", "crossed": True}


def p_rows(tag=""):
    t, _lr = mods()
    reds: list = []

    def run(**kw):
        emitted, memo, calls = [], set(), []
        report = {k: (set(v) if isinstance(v, set) else list(v) if isinstance(v, list) else dict(v)
                      if isinstance(v, dict) else v) for k, v in R18_KEYS.items()}
        with Patch() as p:
            _p_env(p, t, emitted=emitted, memo=memo, calls=calls, **kw)
            value, yields = drain(t.sootopolis_ball_phase(report))
        return report, emitted, memo, calls, yields

    def p1():
        report, emitted, memo, calls, _y = run()
        untouched = all(report.get(k) == v for k, v in R18_KEYS.items()) and "returned" not in report
        b = report["balls"]
        lines = [ln for ln in emitted if "why=topoff " in ln]
        return (b["ok"] is True and b["bought"] == 1 and b["premier"] == 0 and b["money_after"] == 20966
                and untouched and not memo and len(lines) == 1 and "bought=1" in lines[0]
                and "spare=18->19" in lines[0]), f"balls={b} untouched={untouched} emitted={emitted}"

    def p2():
        report, emitted, memo, _c, _y = run(buy="short")
        b = report["balls"]
        return (b["ok"] is False and "SootopolisCity" in memo
                and len([ln for ln in emitted if "why=topoff-failed" in ln]) == 1), f"balls={b} memo={memo}"

    def p3():
        report, emitted, memo, calls, yields = run(money=20966)
        b = report["balls"]
        return (b["phase"] == "none" and calls == [] and yields == 0 and not memo
                and len([ln for ln in emitted if "why=topoff-none" in ln]) == 1), f"balls={b} calls={calls} y={yields}"

    def failing(**kw):
        def fn():
            report, emitted, memo, calls, _y = run(**kw)
            b = report["balls"]
            untouched = all(report.get(k) == v for k, v in R18_KEYS.items())
            return (b["phase"] == "failed" and "SootopolisCity" in memo and untouched
                    and len([ln for ln in emitted if "why=topoff-failed" in ln]) == 1
                    and (calls == [] if kw.get("raise_env") else len(calls) == 1)), f"balls={b} memo={memo}"
        return fn

    def p6():
        try:
            run(buy="abort")
        except RuntimeError as error:
            return "ABORT" in str(error), f"re-raised {error!r}"
        return False, "abort swallowed"

    def p7():
        emitted, memo, calls = [], set(), []
        report: dict = {}
        with Patch() as p:
            _p_env(p, t, buy="forever", emitted=emitted, memo=memo, calls=calls)
            gen = t.sootopolis_ball_phase(report)
            for _ in range(3):
                next(gen)
            gen.close()                                   # RuntimeError here if the handler yields
        return (report["balls"]["phase"] == "closed" and "SootopolisCity" in memo
                and len([ln for ln in emitted if "why=topoff-closed" in ln]) == 1), f"balls={report.get('balls')}"

    def p8():
        report, emitted, _m, calls, _y = run(floor_env="1000")
        return calls == [("buy", [("Ultra Ball", 5)])] and report["balls"]["bought"] == 5, f"calls={calls}"

    for label, fn in (("P1 success: 1 Ultra, verified by the bag delta; R18's report keys untouched", p1),
                      ("P2 a short delta is not ok, memoised, one topoff-failed line", p2),
                      ("P3 an empty live plan: topoff-none, no buy, ZERO yields", p3),
                      ("P4 the BALLRAISE fault is swallowed, memoised, nothing bought", failing(raise_env="1")),
                      ("P5 a raising buy_in_shop is swallowed and memoised", failing(buy="raise")),
                      ("P6 an abort inside the phase is re-raised", p6),
                      ("P7 an outer close mid-buy: logged, memoised, closes cleanly", p7),
                      ("P8 the live floor lever (1,000) plans 5 Ultras", p8)):
        row(label, fn, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------------------------- S rows
def _s_env(p, t, lr, *, flag, money, stock, emitted, calls, memo=None):
    from modules import console as _console
    from modules import map_path as _mp
    from modules import player as _player
    from modules.context import context
    from modules.map_data import MapRSE
    from modules.modes.util import walking as _walking
    from modules.story import early_game as eg
    from modules.story import sootopolis as _soot
    from modules.story import victory_road as vr

    def gen_stub(name):
        def g(*_a, **_k):
            calls.append(name)
            yield
        return g

    def shop(report, plan, names, before, money_, _take):
        calls.append(("shop", list(plan), dict(report.get("balls") or {})))
        _take("EB-MART")
        yield

    def back(report):
        calls.append("back")
        report["returned"] = True
        yield

    def inputs(_mode):
        return {"stage": "BASKET_ERA", "floor": 0, "spare": 18, "money": money, "flags": dict(ERA),
                "price_of": lambda n: PRICES[n]}

    p.setenv(POKEBOT_R23_BALLRESTOCK=flag, POKEBOT_R23_FAULT_FLOOR=None, POKEBOT_RESERVE_FAULT_NOBUY=None,
             POKEBOT_RESERVE_FAULT_FLOOR=None)
    p.set(lr, "in_early_basket_era", lambda: True)
    p.set(lr, "_stock_by_name", lambda names: {n: stock.get(n, 0) for n in names})
    p.set(lr, "_shop", shop)
    p.set(lr, "return_across_from_the_mart", back)
    p.set(t, "_inputs", inputs)
    p.set(t, "_allowed", lambda: set(ALL_BALLS))
    p.set(t, "_emit", lambda line: emitted.append(line))
    p.set(vr, "_on_map", lambda m: m == MapRSE.SOOTOPOLIS_CITY)
    p.set(vr, "_where", lambda: "stub")
    p.set(vr, "_navigate_riding_out", gen_stub("nav"))
    p.set(eg, "wait_until_truly_controllable", gen_stub("wait"))
    p.set(_soot, "_pin_planner_to_live_layout", lambda city: "pinned")
    p.set(_mp, "calculate_path", lambda a, b: [SimpleNamespace(coordinates=(1, 1))] * 3)
    p.set(_walking, "ensure_facing_direction", gen_stub("face"))
    p.set(_player, "get_player", lambda: SimpleNamespace(money=money))
    p.set(_console, "console", SimpleNamespace(print=lambda *a, **k: None))
    p.set(context, "emulator", SimpleNamespace(get_frame_count=lambda: 0))
    p.set(context, "bot_mode_instance", SimpleNamespace(_ball_topoff_failed=memo if memo is not None else set()))


def s_rows(tag=""):
    t, lr = mods()
    reds: list = []

    def visit(flag, money, stock):
        emitted, calls = [], []
        report: dict = {"readings": set(), "order": [], "walked": False}
        with Patch() as p:
            _s_env(p, t, lr, flag=flag, money=money, stock=stock, emitted=emitted, calls=calls)
            _v, yields = drain(lr._stock_basket_early(report))
        return report, calls, yields, emitted

    def s1():
        report, calls, yields, emitted = visit(None, 22166, FULL_BASKET)
        return (report.get("early_basket") == "nothing missing" and "balls" not in report and yields == 0
                and calls == [] and emitted == []), f"report={report} calls={calls} y={yields}"

    def s2():
        report, calls, _y, _e = visit("1", 22166, FULL_BASKET)
        shops = [c for c in calls if isinstance(c, tuple) and c[0] == "shop"]
        return (report.get("early_basket") == "balls only" and report.get("walked") is True
                and "EB-PLANNED" not in report["order"] and len(shops) == 1 and shops[0][1] == []
                and shops[0][2].get("walk") is True and "back" in calls), f"report={report} calls={calls}"

    def no_walk(flag, money):
        def fn():
            report, calls, yields, _e = visit(flag, money, FULL_BASKET)
            return (report.get("early_basket") == "nothing missing" and report.get("walked") is False
                    and "balls" in report and report["balls"]["walk"] is False and calls == [] and yields == 0), \
                f"report={report} calls={calls}"
        return fn

    def shop_env(p, calls, *, balls, sold):
        from modules import mart as _mart
        from modules.context import context
        from modules.modes.util import tasks_scripts as _ts
        from modules.story import victory_road as vr

        def basket_lines(report, plan, names, before, money, _take):
            calls.append(("basket", list(plan)))
            yield

        def phase(report):
            calls.append("phase")
            yield

        p.set(_ts, "task_is_active", lambda name: True)
        p.set(_mart, "get_mart_buyable_items", lambda: [SimpleNamespace(name=n) for n in sold])
        p.set(vr, "_where", lambda: "stub")
        p.set(context, "emulator", SimpleNamespace(get_frame_count=lambda: 0, press_button=lambda b: None))
        p.set(lr, "_buy_basket_lines", basket_lines)
        p.set(t, "sootopolis_ball_phase", phase)
        report = {"readings": set(), "order": [], "frame_start": 0}
        if balls is not None:
            report["balls"] = balls
        return report

    def run_shop(balls, plan, sold):
        calls: list = []
        with Patch() as p:
            report = shop_env(p, calls, balls=balls, sold=sold)
            _take = (lambda r: report["order"].append(r))
            drain(lr._shop(report, plan, ["Revive", "Full Heal", "Hyper Potion"], {}, 22166, _take))
        return calls

    def s5():
        try:
            run_shop(None, [("Revive", 3)], ["Ultra Ball"])
        except Exception as error:  # noqa: BLE001 - the expected BotModeError is the pass condition
            return "sells none" in str(error), f"raised {error}"
        return False, "no raise"

    def s6():
        calls = run_shop({"mode": "1", "walk": True, "blocked": False}, [], ["Ultra Ball"])
        return calls == ["phase"], f"calls={calls}"

    def s7():
        calls = run_shop({"mode": "1", "walk": False, "blocked": True}, [("Revive", 3)], ["Revive", "Ultra Ball"])
        return calls == [("basket", [("Revive", 3)])], f"calls={calls}"

    def s8():
        calls = run_shop({"mode": "1", "walk": False, "blocked": False}, [("Revive", 3)], ["Revive", "Ultra Ball"])
        return calls == [("basket", [("Revive", 3)]), "phase"], f"calls={calls}"

    def s9():
        from modules.story import early_game as eg

        entries: list = []

        def errand(report):
            entries.append(sorted(k for k in report if k != "previous_errands"))
            report["crossed"] = True
            report["returned"] = True
            report["route_back"] = ["x"]
            yield

        def bounded(gen, _frames):
            _v, _n = drain(gen)
            return True
            yield  # pragma: no cover - makes this a generator

        report: dict = {}
        with Patch() as p:
            p.set(lr, "_stock_basket_early", errand)
            p.set(eg, "_yield_bounded_by_frames", bounded)
            drain(lr.stock_basket_early(report))
            drain(lr.stock_basket_early(report))
        second = entries[1] if len(entries) > 1 else None
        prev = report.get("previous_errands") or []
        return (second is not None and "crossed" not in second and "returned" not in second and len(prev) == 1
                and prev[0].get("crossed") is True), f"entries={entries} previous={prev}"

    for label, fn in (("S1 OFF + complete basket: nothing missing, no `balls` key, zero yields, no walk", s1),
                      ("S2 `1` + complete basket + a buying forecast: a ball-only walk ('balls only')", s2),
                      ("S3 `observe` + complete basket: no walk", no_walk("observe", 22166)),
                      ("S4 `1` + complete basket + an empty forecast (20,966): no walk", no_walk("1", 20966)),
                      ("S5 `_shop` OFF on a Mart selling none of the basket still raises", s5),
                      ("S6 a ball-only `_shop` skips the basket and runs the phase", s6),
                      ("S7 a BLOCKED forecast: the basket is bought, the phase does not run", s7),
                      ("S8 basket first, then the phase", s8),
                      ("S9 F1: a second errand on the SAME dict starts clean; the first is archived", s9)):
        row(label, fn, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------------------------- A rows
def _fn_src(src, name, cls=None):
    tree = ast.parse(src)
    body = tree.body
    if cls:
        body = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    node = next(n for n in ast.walk(ast.Module(body=body, type_ignores=[]))
                if isinstance(n, ast.FunctionDef) and n.name == name)
    return node, _strip_comments(ast.get_source_segment(src, node) or "")


def a_rows(tsrc, lrsrc, hsrc, tag=""):
    reds: list = []

    def a1():
        _n, code = _fn_src(lrsrc, "_stock_basket_early")
        i_f = code.find("sootopolis_ball_forecast(plan, money, prices)")
        i_r = code.find('if not plan and not (balls and balls.get("walk")):')
        i_w = code.find('report["walked"] = True')
        return -1 not in (i_f, i_r, i_w) and i_f < i_r < i_w, f"{i_f} {i_r} {i_w}"

    def a2():
        uses = [n.name for n in ast.walk(ast.parse(lrsrc)) if isinstance(n, ast.FunctionDef)
                and "sootopolis_ball_phase(" in _strip_comments(ast.get_source_segment(lrsrc, n) or "")]
        return uses == ["_shop"], f"called from {uses}"

    def a3():
        node, _code = _fn_src(tsrc, "sootopolis_ball_phase")
        handlers = [h for n in ast.walk(node) if isinstance(n, ast.Try) for h in n.handlers
                    if isinstance(h.type, ast.Name) and h.type.id == "GeneratorExit"]
        yields = [y for h in handlers for y in ast.walk(h) if isinstance(y, (ast.Yield, ast.YieldFrom))]
        raises = [r for h in handlers for r in ast.walk(h) if isinstance(r, ast.Raise) and r.exc is None]
        return len(handlers) == 1 and not yields and len(raises) == 1, f"handlers={len(handlers)} yields={len(yields)}"

    def a4():
        _n, code = _fn_src(hsrc, "run", cls="EarlyBasketMode")
        i_end = code.find('R["balls_end"] = _stock_by_name(BALLS)')
        i_restore = code.find("context.emulator.load_save_state(_fixture_bytes)")
        unconditional = "bought_balls = {n: q for n, q in ball_delta.items() if n in BB.UNCONDITIONAL}" in code
        forecast = '"production_forecast": production_forecast_ok' in code
        return (-1 not in (i_end, i_restore) and i_end < i_restore and unconditional and forecast,
                f"end={i_end} restore={i_restore} unconditional={unconditional} forecast={forecast}")

    for label, fn in (("A1 the forecast precedes the early return, which precedes the walk", a1),
                      ("A2 the ball phase is called only from `_shop` (inside the shop's try)", a2),
                      ("A3 the phase's GeneratorExit handler never yields and re-raises", a3),
                      ("A4 the driver reads the balls BEFORE restoring the fixture, prices only unconditional "
                       "balls, and checks production's forecast", a4)):
        row(label, fn, tag, reds)
    return reds


def all_rows(tsrc, lrsrc, hsrc, tag):
    return set(f_rows(tag) + k_rows(tag) + o_rows(tag) + p_rows(tag) + s_rows(tag) + a_rows(tsrc, lrsrc, hsrc, tag))


def main() -> int:
    tsrc = T_PATH.read_text(encoding="utf-8")
    lrsrc = LR_PATH.read_text(encoding="utf-8")
    hsrc = HARNESS.read_text(encoding="utf-8")
    print("F — the pure forecast");                          f_rows()
    print("\nK — the memo key");                             k_rows()
    print("\nO — the forecast, executed");                   o_rows()
    print("\nP — the counter phase, executed");              p_rows()
    print("\nS — league_reserve's visit, executed");         s_rows()
    print("\nA — structure (AST, comments stripped)");       a_rows(tsrc, lrsrc, hsrc)

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    cases = [
        ("M1 the forecast uses the PRE-basket wallet -> F1 O4 O5", T_PATH,
         "    money_after = int(money) - sum(basket_prices[name] * qty for name, qty in basket_plan)\n",
         "    money_after = int(money)\n", {"F1", "O4", "O5"}),
        ("M2 the forecast's floor ignores the basket plan -> F1 O4 O5", T_PATH,
         "    for name, qty in basket_plan:\n        post[name] = post.get(name, 0) + qty\n", "", {"F1", "O4", "O5"}),
        ("M3 the early return ignores the balls (the old `if not plan:`) -> S2 A1", LR_PATH,
         '    if not plan and not (balls and balls.get("walk")):\n', "    if not plan:\n", {"S2", "A1"}),
        ("M4 `observe` walks -> O4 S3", T_PATH,
         '               walk=mode == "1" and bool(forecast["lines"]))\n',
         '               walk=bool(forecast["lines"]))\n', {"O4", "S3"}),
        ("M5 `_shop` raises on an empty basket plan whatever the balls -> S6", LR_PATH,
         '    if not plan and not balls.get("walk"):\n', "    if not plan:\n", {"S6"}),
        ("M6 a blocked forecast still runs the phase -> S7", LR_PATH,
         '    if balls.get("mode") == "1" and not balls.get("blocked"):\n', '    if balls.get("mode") == "1":\n',
         {"S7"}),
        ("M7 the phase lets a failure escape -> P4 P5", T_PATH,
         "        reraise_if_aborting(error)\n        _memo_add()\n        balls[\"phase\"] = \"failed\"\n",
         "        raise\n", {"P4", "P5"}),
        ("M8 no GeneratorExit handler in the phase -> P7 A3", T_PATH,
         "    except GeneratorExit:  # an OUTER bound (R18's EARLY_BASKET_BUDGET) closed the visit mid-purchase\n",
         "    except ZeroDivisionError:  # mutant\n", {"P7", "A3"}),
        ("M9 a short delta is not memoised -> P2", T_PATH,
         "        if not balls[\"ok\"]:\n            _memo_add()\n", "        if not balls[\"ok\"]:\n", {"P2"}),
        ("M10 F1's archive removed (a second errand inherits the first's keys) -> S9", LR_PATH,
         "    if any(key != \"previous_errands\" for key in report):\n", "    if False:\n", {"S9"}),
        ("M11 OFF returns a dict (adds a `balls` key) -> O1 O2 O3 S1 (a typo IS OFF: it shares the branch)", T_PATH,
         "    if mode not in (\"observe\", \"1\"):\n        return None\n    out = ",
         "    if mode not in (\"observe\", \"1\"):\n        return {\"mode\": mode, \"walk\": False}\n    out = ",
         {"O1", "O2", "O3", "S1"}),
        ("M12 the phase writes into R18's report root -> P1 P2 P3 P4 P5 P7 P8", T_PATH,
         "    balls = report.setdefault(\"balls\", {})\n    balls[\"phase\"] = \"started\"\n",
         "    balls = report\n    balls[\"phase\"] = \"started\"\n", {"P1", "P2", "P3", "P4", "P5", "P7", "P8"}),
        ("M13 a failed forecast does not block -> O7", T_PATH,
         "        _memo_add()\n        out[\"blocked\"] = True\n        out[\"reason\"] = f\"the forecast raised",
         "        _memo_add()\n        out[\"reason\"] = f\"the forecast raised", {"O7"}),
        ("M14 the driver reads the balls AFTER restoring the fixture -> A4", HARNESS,
         "                R[\"balls_end\"] = _stock_by_name(BALLS)\n", "", {"A4"}),
        ("M15 the phase SWALLOWS an abort -> P6", T_PATH,
         "        reraise_if_aborting(error)\n        _memo_add()\n        balls[\"phase\"] = \"failed\"\n",
         "        _memo_add()\n        balls[\"phase\"] = \"failed\"\n", {"P6"}),
        ("M16 the forecast SWALLOWS an abort -> O7", T_PATH,
         "        reraise_if_aborting(error)\n        _memo_add()\n        out[\"blocked\"] = True\n",
         "        _memo_add()\n        out[\"blocked\"] = True\n", {"O7"}),
        ("N1 a comment edit naming the phase and `blocked` turns NOTHING red", LR_PATH,
         "        # RULINGS 23 + 26 (design v2 step 9b): after the basket, on the same open menu",
         "        # (edited) sootopolis_ball_phase( and blocked named in a comment only; after the basket, same menu",
         set()),
    ]
    real = {T_NAME: sys.modules[T_NAME], LR_NAME: sys.modules[LR_NAME]}
    for i, (label, path, old, new, want) in enumerate(cases):
        src = path.read_text(encoding="utf-8")
        try:
            n = src.count(old)
            if n != 1:
                raise AssertionError(f"mutant anchor found {n} times: {old[:70]!r}")
            msrc = src.replace(old, new)
            if path in (T_PATH, LR_PATH):
                name = T_NAME if path == T_PATH else LR_NAME
                mod = types.ModuleType(name)
                mod.__file__ = str(path)
                mod.__package__ = "modules.story"
                sys.modules[name] = mod
                exec(compile(msrc, f"<mutant {i}>", "exec"), mod.__dict__)
            red = all_rows(msrc if path == T_PATH else tsrc, msrc if path == LR_PATH else lrsrc,
                           msrc if path == HARNESS else hsrc, "m")
            check(label, red == want, f"red {sorted(red)}" + ("" if red == want else f" (want {sorted(want)})"))
        except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
            check(label, False, f"{type(error).__name__}: {error}")
        finally:
            sys.modules.update(real)

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
