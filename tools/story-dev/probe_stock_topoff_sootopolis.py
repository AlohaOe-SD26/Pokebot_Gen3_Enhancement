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
  O1-O8   `sootopolis_ball_forecast` EXECUTED with stubs: OFF (unset, `0`) reads NOTHING and returns None; a typo is
          OFF with a 9b-specific `why=topoff-flag` line; `observe` never walks; `1` walks; a memo hit and a failed
          forecast BLOCK (no walk, no counter phase) and a failure is memoised; an abort is re-raised; the live floor
          lever reaches the forecast.
  P1-P9   `sootopolis_ball_phase` EXECUTED with a fake bag, a fake shop and a stub `buy_in_shop`, given the report shape
          production gives it (R18's keys plus a STALE forecast of 5 in `report["balls"]`): success buys the LIVE plan
          (1, not the stale 5); EVERY row asserts the whole report minus `balls` unchanged; a short delta; an empty live
          plan (no buy, no yield); the BALLRAISE fault and a raising `buy_in_shop` (both swallowed and memoised); an
          abort (re-raised); a close mid-buy (logged, memoised, R18's keys untouched); the live floor lever; and a
          ball-only visit that finds nothing to buy (memoised).
  S1-S14  `league_reserve` EXECUTED with stubs: OFF + complete basket = "nothing missing" with no `balls` key and no
          yield; `1` walks for balls alone ("balls only", no EB-PLANNED); `observe` and an empty forecast do not walk;
          `_shop` OFF still raises on a Mart selling none of the basket; a ball-only `_shop` skips the basket and runs
          the phase; a blocked forecast skips the phase; basket-then-balls order; F1: a second `stock_basket_early`
          on the same dict starts CLEAN; a BASKET visit to a Mart selling none of it raises even with a buying
          forecast; OFF and `observe` basket visits buy only the basket; OFF's plan reaches `_shop` with EB-PLANNED
          and no `balls` key; `1` carries the POST-basket forecast into `_shop`.
  A1-A4   by AST Call/Assign nodes (a comment, docstring or string literal can neither satisfy nor break them): the
          forecast is called with (plan, money, prices) before the early return, before the walk; the phase is called
          only from `_shop`; no `yield` inside the phase's GeneratorExit handler; the driver assigns the balls' end
          state ONCE, before the restore, and grades through `ball_grade`.
  D1-D3   the driver's ball grade (`ball_grade.py`) EXECUTED: the delta, the cost without Premier, the forecast check.
  M1-M39  source mutants, each with the EXACT set of rows it must turn red; N1, N1b and N2 comment/string-only edits
          (none red). M26-M39 and the re-derived sets of M1, M2, M5, M11, M12, M19, M24 came from the three-lens
          review (G1-G5, BB9B-1/2) and were written before gate run 4. Every
          row except F2, F3, F5 and F6 is reddened by at least one mutant; those four are VALUE rows on the real
          numbers, and the arithmetic they exercise (`ball_topoff_plan`, `stage`) is pinned by 9a's gate (L-rows,
          mutants M3-M6 of `probe_stock_topoff.py`).
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
BG_PATH = HERE / "ball_grade.py"
T_NAME = "modules.story.stock_topoff"
LR_NAME = "modules.story.league_reserve"
BG_NAME = "ball_grade"
sys.path.insert(0, str(HERE))

import ball_grade  # noqa: E402,F401
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

    p.setenv(POKEBOT_R23_BALLRESTOCK=flag, POKEBOT_R23_FAULT_FLOOR=None,   # 10b: the kit's env isolated (E10)
             POKEBOT_R26_KITTOPOFF=None, POKEBOT_R27_KEYITEMS=None, POKEBOT_R26_FAULT_RAWBAG=None,
             POKEBOT_RESERVE_FAULT_RAISE=None)

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

    def o8():
        emitted: list = []
        with Patch() as p:
            _o_env(p, t, lr, flag="1", emitted=emitted)
            p.setenv(POKEBOT_R23_FAULT_FLOOR="1000")
            out = t.sootopolis_ball_forecast(PLAN, 67466, BASKET_PRICES)
        return (out["forecast"] == [("Ultra Ball", 5)] and out["floor"] == 1000 and out["walk"] is True,
                f"out={out}")

    for label, fn in (("O1 OFF (unset) reads NOTHING and returns None", off(None)),
                      ("O2 OFF (`0`) reads NOTHING and returns None", off("0")),
                      ("O3 a typo is OFF with ONE 9b-specific `why=topoff-flag mart=SootopolisCity` line", o3),
                      ("O4 `observe` forecasts 1 Ultra and never walks", mode("observe", False, "topoff-observe")),
                      ("O5 `1` forecasts 1 Ultra and walks", mode("1", True, "topoff-forecast")),
                      ("O6 a memo hit BLOCKS (no walk, no counter phase)", o6),
                      ("O7 a failed forecast BLOCKS and is memoised; an abort is re-raised", o7),
                      ("O8 the forecast honours the live floor lever (1,000): 5 Ultras, walks", o8)):
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
    p.setenv(POKEBOT_R23_FAULT_FLOOR=floor_env, POKEBOT_R23_FAULT_BALLRAISE=raise_env, POKEBOT_R23_BALLRESTOCK="1",
             POKEBOT_R26_KITTOPOFF=None, POKEBOT_R27_KEYITEMS=None, POKEBOT_R26_FAULT_RAWBAG=None,
             POKEBOT_RESERVE_FAULT_RAISE=None)

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
            "order": ["EB-PLANNED", "EB-MART", "EB-BOUGHT"], "early_basket": "bought", "crossed": True,
            "route_back": ["wp1", "wp2"], "frame_start": 0}
#: ⛔ The phase is given the report shape production gives it: `_stock_basket_early` leaves the FORECAST in
#: `report["balls"]`. A STALE one (5 Ultras) is seeded so a phase that buys the forecast instead of re-planning live
#: goes red (the 9b review, G2).
STALE_BALLS = {"mode": "1", "walk": True, "blocked": False, "forecast": [("Ultra Ball", 5)]}


def _seed(early="bought"):
    import copy

    report = copy.deepcopy(R18_KEYS)
    report["early_basket"] = early
    report["balls"] = copy.deepcopy(STALE_BALLS)
    return report


def _root(report):
    """Everything R18 owns: the whole report minus the phase's own `balls` key (the 9b review, G3: the WHOLE dict,
    not a key subset, so a stray `returned`/`route_back`/`early_basket` write is caught)."""
    import copy

    return copy.deepcopy({k: v for k, v in report.items() if k != "balls"})


def p_rows(tag=""):
    t, _lr = mods()
    reds: list = []

    def run(early="bought", **kw):
        emitted, memo, calls = [], set(), []
        report = _seed(early)
        before = _root(report)
        with Patch() as p:
            _p_env(p, t, emitted=emitted, memo=memo, calls=calls, **kw)
            value, yields = drain(t.sootopolis_ball_phase(report))
        return report, emitted, memo, calls, yields, _root(report) == before

    def p1():
        report, emitted, memo, calls, _y, iso = run()
        b = report["balls"]
        lines = [ln for ln in emitted if "why=topoff " in ln]
        return (b["ok"] is True and b["bought"] == 1 and b["premier"] == 0 and b["money_after"] == 20966
                and calls == [("buy", [("Ultra Ball", 1)])] and iso and not memo and len(lines) == 1
                and "bought=1" in lines[0] and "spare=18->19" in lines[0]), \
            f"balls={b} calls={calls} iso={iso} emitted={emitted}"

    def p2():
        report, emitted, memo, _c, _y, iso = run(buy="short")
        b = report["balls"]
        return (b["ok"] is False and "SootopolisCity" in memo and iso
                and len([ln for ln in emitted if "why=topoff-failed" in ln]) == 1), f"balls={b} memo={memo} iso={iso}"

    def p3():
        report, emitted, memo, calls, yields, iso = run(money=20966)
        b = report["balls"]
        return (b["phase"] == "none" and calls == [] and yields == 0 and not memo and iso
                and len([ln for ln in emitted if "why=topoff-none" in ln]) == 1), f"balls={b} calls={calls} y={yields}"

    def failing(**kw):
        def fn():
            report, emitted, memo, calls, _y, iso = run(**kw)
            b = report["balls"]
            return (b["phase"] == "failed" and "SootopolisCity" in memo and iso
                    and len([ln for ln in emitted if "why=topoff-failed" in ln]) == 1
                    and (calls == [] if kw.get("raise_env") else len(calls) == 1)), f"balls={b} memo={memo} iso={iso}"
        return fn

    def p6():
        try:
            run(buy="abort")
        except RuntimeError as error:
            return "ABORT" in str(error), f"re-raised {error!r}"
        return False, "abort swallowed"

    def p7():
        emitted, memo, calls = [], set(), []
        report = _seed()                                  # R18's keys: crossed=True and NO `returned`
        before = _root(report)
        with Patch() as p:
            _p_env(p, t, buy="forever", emitted=emitted, memo=memo, calls=calls)
            gen = t.sootopolis_ball_phase(report)
            for _ in range(3):
                next(gen)
            gen.close()                                   # RuntimeError here if the handler yields
        iso = _root(report) == before                     # a `returned` written here would skip R18's retry walk back
        return (report["balls"]["phase"] == "closed" and "SootopolisCity" in memo and iso
                and len([ln for ln in emitted if "why=topoff-closed" in ln]) == 1), f"balls={report.get('balls')} iso={iso}"

    def p8():
        report, emitted, _m, calls, _y, iso = run(floor_env="1000")
        return (calls == [("buy", [("Ultra Ball", 5)])] and report["balls"]["bought"] == 5 and iso,
                f"calls={calls} iso={iso}")

    def p9():
        report, emitted, memo, calls, yields, iso = run(early="balls only", money=20966)
        lines = [ln for ln in emitted if "why=topoff-none" in ln]
        return (report["balls"]["phase"] == "none" and calls == [] and "SootopolisCity" in memo and iso
                and len(lines) == 1 and "found nothing to buy (memoised)" in lines[0]), f"memo={memo} lines={lines}"

    for label, fn in (("P1 success: 1 Ultra, verified by the bag delta; R18's report keys untouched", p1),
                      ("P2 a short delta is not ok, memoised, one topoff-failed line", p2),
                      ("P3 an empty live plan: topoff-none, no buy, ZERO yields", p3),
                      ("P4 the BALLRAISE fault is swallowed, memoised, nothing bought", failing(raise_env="1")),
                      ("P5 a raising buy_in_shop is swallowed and memoised", failing(buy="raise")),
                      ("P6 an abort inside the phase is re-raised", p6),
                      ("P7 an outer close mid-buy: logged, memoised, closes cleanly", p7),
                      ("P8 the live floor lever (1,000) plans 5 Ultras", p8),
                      ("P9 a BALL-ONLY visit that finds nothing to buy is memoised (no re-walk next attempt)", p9)):
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
             POKEBOT_RESERVE_FAULT_FLOOR=None, POKEBOT_R26_KITTOPOFF=None, POKEBOT_R27_KEYITEMS=None, POKEBOT_R26_FAULT_RAWBAG=None,
             POKEBOT_RESERVE_FAULT_RAISE=None)
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

    def s10():
        # BB9B-1: a BASKET visit (non-empty caller plan) whose Mart sells none of the basket must raise by name even
        # with a buying forecast, and must not run the phase.
        calls: list = []
        try:
            with Patch() as p:
                report = shop_env(p, calls, balls={"mode": "1", "walk": True, "blocked": False}, sold=["Ultra Ball"])
                drain(lr._shop(report, [("Revive", 3)], ["Revive", "Full Heal", "Hyper Potion"], {}, 22166,
                               lambda r: report["order"].append(r)))
        except Exception as error:  # noqa: BLE001 - the expected BotModeError is the pass condition
            return "sells none" in str(error) and calls == [], f"raised {error}; calls={calls}"
        return False, f"no raise; calls={calls}"

    def basket_visit(balls):
        def fn():
            # G1: OFF (no `balls` key) and `observe` on a BASKET visit buy the basket and never run the phase.
            calls = run_shop(balls, [("Revive", 3)], ["Revive", "Ultra Ball"])
            return calls == [("basket", [("Revive", 3)])], f"calls={calls}"
        return fn

    def s13():
        # G1: OFF on a basket visit through `_stock_basket_early`: the plan reaches `_shop`, EB-PLANNED is taken, and
        # the report gains no `balls` key.
        report, calls, _y, emitted = visit(None, 67466, EMPTY_BASKET)
        shops = [c for c in calls if isinstance(c, tuple) and c[0] == "shop"]
        return (len(shops) == 1 and shops[0][1] == PLAN and shops[0][2] == {} and "EB-PLANNED" in report["order"]
                and "balls" not in report and emitted == []), f"shops={shops} report_keys={sorted(report)}"

    def s14():
        # `1` on a basket visit: the forecast the visit carries to `_shop` is the POST-basket one (1 Ultra from
        # 22,166 against 19,000), so a forecast that ignored the basket plan (0 Ultras) goes red here too.
        report, calls, _y, _e = visit("1", 67466, EMPTY_BASKET)
        shops = [c for c in calls if isinstance(c, tuple) and c[0] == "shop"]
        return (len(shops) == 1 and shops[0][1] == PLAN and shops[0][2].get("forecast") == [("Ultra Ball", 1)]
                and shops[0][2].get("walk") is True and "EB-PLANNED" in report["order"]), f"shops={shops}"

    for label, fn in (("S1 OFF + complete basket: nothing missing, no `balls` key, zero yields, no walk", s1),
                      ("S2 `1` + complete basket + a buying forecast: a ball-only walk ('balls only')", s2),
                      ("S3 `observe` + complete basket: no walk", no_walk("observe", 22166)),
                      ("S4 `1` + complete basket + an empty forecast (20,966): no walk", no_walk("1", 20966)),
                      ("S5 `_shop` OFF on a Mart selling none of the basket still raises", s5),
                      ("S6 a ball-only `_shop` skips the basket and runs the phase", s6),
                      ("S7 a BLOCKED forecast: the basket is bought, the phase does not run", s7),
                      ("S8 basket first, then the phase", s8),
                      ("S9 F1: a second errand on the SAME dict starts clean; the first is archived", s9),
                      ("S10 a BASKET visit to a Mart selling none of it raises by name even with a buying forecast", s10),
                      ("S11 `_shop` OFF on a basket visit: the basket only, no phase", basket_visit(None)),
                      ("S12 `_shop` observe on a basket visit: the basket only, no phase",
                       basket_visit({"mode": "observe", "walk": False, "blocked": False})),
                      ("S13 `_stock_basket_early` OFF on a basket visit: the plan reaches `_shop`, EB-PLANNED, no "
                       "`balls` key", s13),
                      ("S14 `1` on a basket visit carries the POST-basket forecast (1 Ultra) to `_shop`", s14)):
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


def _calls(node, func_name):
    """AST Call nodes to `func_name` (a bare name) under `node`: a mention in a comment, a docstring or any string
    literal is never a Call (the 9b review, G5: the old substring checks passed on a string)."""
    return [c for c in ast.walk(node) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
            and c.func.id == func_name]


def a_rows(tsrc, lrsrc, hsrc, tag=""):
    reds: list = []

    def a1():
        node, _code = _fn_src(lrsrc, "_stock_basket_early")
        calls = _calls(node, "sootopolis_ball_forecast")
        args_ok = len(calls) == 1 and [ast.unparse(a) for a in calls[0].args] == ["plan", "money", "prices"]
        # Step 10b (design E3) re-derived this row BEFORE the gate's first 10b run: the early return is now on the
        # EFFECTIVE ball walk and the kit walk, and the effective walk must be 9b's `balls.walk` unless the kit buys.
        early = [n for n in ast.walk(node) if isinstance(n, ast.If)
                 and ast.unparse(n.test) == "not plan and (not ball_walk) and (not kit_walk)"]
        eff = [n for n in ast.walk(node) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "ball_walk"
               and ast.unparse(n.value) == ("bool(kit.get('split_balls')) if kit_buys_here(kit) else "
                                            "bool(balls and balls.get('walk'))")]
        walked = [n for n in ast.walk(node) if isinstance(n, ast.Assign)
                  and ast.unparse(n.targets[0]) == "report['walked']" and ast.unparse(n.value) == "True"]
        ok = (args_ok and len(early) == 1 and len(eff) == 1 and len(walked) == 1
              and calls[0].lineno < eff[0].lineno < early[0].lineno < walked[0].lineno)
        return ok, (f"forecast calls={[ast.unparse(c) for c in calls]} early={[e.lineno for e in early]} "
                    f"walked={[w.lineno for w in walked]}")

    def a2():
        uses = sorted({f.name for f in ast.walk(ast.parse(lrsrc)) if isinstance(f, ast.FunctionDef)
                       and _calls(f, "sootopolis_ball_phase")})
        return uses == ["_shop"], f"called from {uses}"

    def a3():
        node, _code = _fn_src(tsrc, "sootopolis_ball_phase")
        handlers = [h for n in ast.walk(node) if isinstance(n, ast.Try) for h in n.handlers
                    if isinstance(h.type, ast.Name) and h.type.id == "GeneratorExit"]
        yields = [y for h in handlers for y in ast.walk(h) if isinstance(y, (ast.Yield, ast.YieldFrom))]
        raises = [r for h in handlers for r in ast.walk(h) if isinstance(r, ast.Raise) and r.exc is None]
        return len(handlers) == 1 and not yields and len(raises) == 1, f"handlers={len(handlers)} yields={len(yields)}"

    def a4():
        # AST, not text (the 9b review, G4): exactly ONE assignment of the balls' end state, BEFORE the fixture
        # restore (a second read after it would zero every delta); the grade goes through `ball_grade` (the D rows
        # execute it) with the driver's OWN reads and the unconditional set; and `production_forecast_ok` is exactly
        # the `ball_grade` call, never a constant.
        node, _code = _fn_src(hsrc, "run", cls="EarlyBasketMode")
        ends = [n for n in ast.walk(node) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "R['balls_end']"]
        restores = [c for c in ast.walk(node) if isinstance(c, ast.Call) and ast.unparse(c.func)
                    == "context.emulator.load_save_state"]
        action = _calls(node, "ball_action")
        action_ok = (len(action) == 1 and [ast.unparse(a) for a in action[0].args]
                     == ["R.get('balls_start', {})", "R.get('balls_end', {})", "R.get('balls_expected')", "ball_prices",
                         "BB.UNCONDITIONAL"])
        fok = [n for n in ast.walk(node) if isinstance(n, ast.Assign)
               and ast.unparse(n.targets[0]) == "production_forecast_ok"]
        fok_ok = (len(fok) == 1 and isinstance(fok[0].value, ast.Call) and ast.unparse(fok[0].value.func) == "_forecast_ok")
        ok = (len(ends) == 1 and len(restores) == 1 and ends[0].lineno < restores[0].lineno and action_ok and fok_ok)
        return ok, (f"end reads={[e.lineno for e in ends]} restores={[r.lineno for r in restores]} "
                    f"action_ok={action_ok} forecast_ok_call={fok_ok}")

    for label, fn in (("A1 (AST) the forecast is called with (plan, money, prices), before the early return, before "
                       "the walk", a1),
                      ("A2 (AST) the ball phase is called only from `_shop` (inside the shop's try)", a2),
                      ("A3 (AST) the phase's GeneratorExit handler never yields and re-raises", a3),
                      ("A4 (AST) the driver reads the balls ONCE, BEFORE the restore, and grades through `ball_grade`",
                       a4)):
        row(label, fn, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------------------------- D rows
def d_rows(tag=""):
    """The driver's ball grade (`tools/story-dev/ball_grade.py`) EXECUTED (the 9b review, G4)."""
    bg = sys.modules[BG_NAME]
    reds: list = []
    uncond = ("Ultra Ball", "Great Ball", "Poké Ball", "Net Ball", "Nest Ball", "Dive Ball", "Repeat Ball",
              "Timer Ball", "Luxury Ball")

    def d1():
        a = bg.ball_action({"Ultra Ball": 0, "Premier Ball": 1, "Poké Ball": 16},
                           {"Ultra Ball": 1, "Premier Ball": 1, "Poké Ball": 16}, [("Ultra Ball", 1)], PRICES, uncond)
        return (a["bought"] == {"Ultra Ball": 1} and a["cost"] == 1200 and a["expected"] == {"Ultra Ball": 1}
                and a["delta"] == {"Ultra Ball": 1}), str(a)

    def d2():
        a = bg.ball_action({"Poké Ball": 16, "Premier Ball": 1}, {"Poké Ball": 36, "Premier Ball": 3},
                           [("Poké Ball", 10), ("Poké Ball", 10)], PRICES, uncond)
        return (a["bought"] == {"Poké Ball": 20} and a["cost"] == 4000 and a["delta"] == {"Poké Ball": 20,
                "Premier Ball": 2} and a["expected"] == {"Poké Ball": 20}), str(a)

    def d3():
        cases = [(bg.production_forecast_ok(True, [("Ultra Ball", 1)], {"balls": {"forecast": [("Ultra Ball", 1)]}}),
                  True),
                 (bg.production_forecast_ok(True, [("Ultra Ball", 1)], {"balls": {"forecast": [("Ultra Ball", 5)]}}),
                  False),
                 (bg.production_forecast_ok(False, [], {"plan": []}), True),
                 (bg.production_forecast_ok(False, [], {"balls": {"mode": ""}}), False)]
        return all(got is want for got, want in cases), str(cases)

    for label, fn in (("D1 ball_action: the driver's own delta, 1 Ultra = 1200", d1),
                      ("D2 ball_action: a Premier bonus is in the delta but NEVER in the cost", d2),
                      ("D3 production_forecast_ok: equal forecasts pass, different fail; OFF passes only with NO "
                       "`balls` key", d3)):
        row(label, fn, tag, reds)
    return reds


def all_rows(tsrc, lrsrc, hsrc, tag):
    return set(f_rows(tag) + k_rows(tag) + o_rows(tag) + p_rows(tag) + s_rows(tag) + a_rows(tsrc, lrsrc, hsrc, tag)
               + d_rows(tag))


def main() -> int:
    tsrc = T_PATH.read_text(encoding="utf-8")
    lrsrc = LR_PATH.read_text(encoding="utf-8")
    hsrc = HARNESS.read_text(encoding="utf-8")
    print("F — the pure forecast");                          f_rows()
    print("\nK — the memo key");                             k_rows()
    print("\nO — the forecast, executed");                   o_rows()
    print("\nP — the counter phase, executed");              p_rows()
    print("\nS — league_reserve's visit, executed");         s_rows()
    print("\nA — structure (AST Call/Assign nodes)");        a_rows(tsrc, lrsrc, hsrc)
    print("\nD — the driver's ball grade, executed");        d_rows()

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    cases = [
        # ⚠ Sets re-derived for gate run 4 (the review's rows S10-S14, P9, D1-D3 widen some): written before the run.
        ("M1 the forecast uses the PRE-basket wallet -> F1 O4 O5 S14", T_PATH,
         "    money_after = int(money) - sum(basket_prices[name] * qty for name, qty in basket_plan)\n",
         "    money_after = int(money)\n", {"F1", "O4", "O5", "S14"}),
        ("M2 the forecast's floor ignores the basket plan -> F1 O4 O5 S14", T_PATH,
         "    for name, qty in basket_plan:\n        post[name] = post.get(name, 0) + qty\n", "",
         {"F1", "O4", "O5", "S14"}),
        ("M3 the early return ignores the balls (the old `if not plan:`) -> S2 A1", LR_PATH,
         '    if not plan and not ball_walk and not kit_walk:\n', "    if not plan:\n", {"S2", "A1"}),  # 10b: re-anchored
        ("M4 `observe` walks -> O4 S3", T_PATH,
         '               walk=mode == "1" and bool(forecast["lines"]))\n',
         '               walk=bool(forecast["lines"]))\n', {"O4", "S3"}),
        ("M5 `_shop` raises on an empty basket plan whatever the balls -> S6", LR_PATH,
         '    if not plan and not topoff_only:\n', "    if not plan:\n", {"S6"}),   # 10b: re-anchored (E4)
        ("M6 a blocked forecast still runs the phase -> S7", LR_PATH,
         '    if balls.get("mode") == "1" and not balls.get("blocked"):\n', '    if balls.get("mode") == "1":\n',
         {"S7"}),
        ("M7 the phase lets a failure escape -> P4 P5", T_PATH,
         "        reraise_if_aborting(error)\n        _memo_add()\n        balls[\"phase\"] = \"failed\"\n",
         "        raise\n", {"P4", "P5"}),
        ("M8 no GeneratorExit handler in the phase -> P7 A3", T_PATH,
         "    except GeneratorExit:  # a close reached the phase mid-purchase (R18's EARLY_BASKET_BUDGET, or a stop from "
         "above)\n",
         "    except ZeroDivisionError:  # mutant\n", {"P7", "A3"}),
        ("M9 a short delta is not memoised -> P2", T_PATH,
         "        if not balls[\"ok\"]:\n            _memo_add()\n", "        if not balls[\"ok\"]:\n", {"P2"}),
        ("M10 F1's archive removed (a second errand inherits the first's keys) -> S9", LR_PATH,
         "    if any(key != \"previous_errands\" for key in report):\n", "    if False:\n", {"S9"}),
        ("M11 OFF returns a dict (adds a `balls` key) -> O1 O2 O3 S1 S13 (a typo IS OFF: it shares the branch)", T_PATH,
         "    if mode not in (\"observe\", \"1\"):\n        return None\n    out = ",
         "    if mode not in (\"observe\", \"1\"):\n        return {\"mode\": mode, \"walk\": False}\n    out = ",
         {"O1", "O2", "O3", "S1", "S13"}),
        ("M12 the phase writes into R18's report root -> P1 P2 P3 P4 P5 P7 P8 P9", T_PATH,
         "    balls = report.setdefault(\"balls\", {})\n    balls[\"phase\"] = \"started\"\n",
         "    balls = report\n    balls[\"phase\"] = \"started\"\n", {"P1", "P2", "P3", "P4", "P5", "P7", "P8", "P9"}),
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
        # --- added after gate run 2 by a coverage check (every row needs a mutant that reddens it); the sets were
        # written BEFORE gate run 3 ---
        ("M17 the memo is never consulted -> O6", T_PATH,
         "    if failed is not None and sootopolis_key() in failed:\n", "    if False:\n", {"O6"}),
        ("M18 `1` walks on an EMPTY forecast -> S4", T_PATH,
         "               walk=mode == \"1\" and bool(forecast[\"lines\"]))\n", "               walk=mode == \"1\")\n",
         {"S4"}),
        ("M19 `_shop` never raises on a Mart selling none of the basket -> S5 S10", LR_PATH,
         "        raise BotModeError(f\"early basket: this Mart sells none of {list(BUY_ORDER)} ({sorted(sold)}).\")\n",
         "        pass\n", {"S5", "S10"}),
        ("M20 mode `1` skips the BASKET -> S7 S8", LR_PATH,
         "    if plan:\n        yield from _buy_basket_lines(",
         "    if plan and balls.get(\"mode\") != \"1\":\n        yield from _buy_basket_lines(", {"S7", "S8"}),
        ("M21 the forecast ignores the live floor lever -> O8", T_PATH,
         "            fault_floor=_fault_floor())\n", "            fault_floor=None)\n", {"O8"}),
        ("M22 the phase ignores the live floor lever -> P8", T_PATH,
         "        floor_money = _fault_floor()\n        if floor_money is None:\n",
         "        floor_money = None\n        if floor_money is None:\n", {"P8"}),
        ("M23 forecast_after_basket ignores its fault_floor -> F4 O8", T_PATH,
         "    floor_money = fault_floor if fault_floor is not None else floor(stage_name, missing)\n",
         "    floor_money = floor(stage_name, missing)\n", {"F4", "O8"}),
        ("M24 the memo key drifts from the enum name -> K1 O3 O6 O7 P2 P4 P5 P7 P9", T_PATH,
         "    return PokemonCenter.SootopolisCity.name\n", "    return \"Sootopolis\"\n",
         {"K1", "O3", "O6", "O7", "P2", "P4", "P5", "P7", "P9"}),
        ("M25 the phase is also called from `_stock_basket_early` (outside `_shop`'s try) -> A2", LR_PATH,
         "    from modules.story.stock_topoff import sootopolis_ball_forecast\n",
         "    from modules.story.stock_topoff import sootopolis_ball_forecast, sootopolis_ball_phase\n"
         "    if False:\n        sootopolis_ball_phase(report)\n", {"A2"}),
        # --- added after the three-lens review (G1-G5, BB9B-1/2); the sets were written BEFORE gate run 4 ---
        ("M26 (G2) the phase buys the STALE forecast instead of re-planning live -> P1 P3 P9", T_PATH,
         "        balls.update(lines=lines, live_reason=reason, live_floor=floor_money)\n",
         "        lines = balls.get(\"forecast\") or lines\n"
         "        balls.update(lines=lines, live_reason=reason, live_floor=floor_money)\n", {"P1", "P3", "P9"}),
        ("M27 (G3) a short delta overwrites R18's outcome -> P2", T_PATH,
         "            balls[\"why\"] = f\"bag delta {balls['bought']} != planned {planned}\"\n",
         "            balls[\"why\"] = f\"bag delta {balls['bought']} != planned {planned}\"\n"
         "            report[\"early_basket\"] = balls[\"why\"]\n", {"P2"}),
        ("M28 (G3) a close writes `returned` (R18's retry walk back is skipped) -> P7", T_PATH,
         "        balls[\"phase\"] = \"closed\"\n", "        balls[\"phase\"] = \"closed\"\n        report[\"returned\"] = True\n",
         {"P7"}),
        ("M29 (G3) a finished purchase clears R18's stored route back -> P1 P2 P8", T_PATH,
         "        balls[\"phase\"] = \"done\"\n", "        balls[\"phase\"] = \"done\"\n        report[\"route_back\"] = []\n",
         {"P1", "P2", "P8"}),
        ("M30 (BB9B-2) a wasted ball-only visit is not memoised -> P9", T_PATH,
         "            if wasted:\n                _memo_add()\n", "            if wasted:\n                pass\n", {"P9"}),
        ("M31 (BB9B-1) ball-only keyed on the forecast's `walk` alone -> S10", LR_PATH,
         "    ball_only = not plan and bool(balls.get(\"walk\"))\n", "    ball_only = bool(balls.get(\"walk\"))\n", {"S10"}),
        ("M32 (G1) the phase runs whenever not blocked (OFF and observe too) -> S11 S12", LR_PATH,
         "    if balls.get(\"mode\") == \"1\" and not balls.get(\"blocked\"):\n", "    if not balls.get(\"blocked\"):\n",
         {"S11", "S12"}),
        ("M33 (G1) `observe` runs the phase -> S12", LR_PATH,
         "    if balls.get(\"mode\") == \"1\" and not balls.get(\"blocked\"):\n",
         "    if balls.get(\"mode\") in (\"1\", \"observe\") and not balls.get(\"blocked\"):\n", {"S12"}),
        ("M34 (G1) OFF drops R18's EB-PLANNED reading -> S13", LR_PATH,
         "    if plan:\n        _take(\"EB-PLANNED\")\n", "    if plan and balls is not None:\n        _take(\"EB-PLANNED\")\n",
         {"S13"}),
        ("M35 (G5) the forecast ignores the basket plan, its old call kept only in a STRING -> A1 S14", LR_PATH,
         "    balls = sootopolis_ball_forecast(plan, money, prices)\n",
         "    _why = \"was: sootopolis_ball_forecast(plan, money, prices)\"\n"
         "    balls = sootopolis_ball_forecast([], money, prices)\n", {"A1", "S14"}),
        ("M36 (G4) production_forecast_ok always True -> D3", BG_PATH,
         "        return (report.get(\"balls\") or {}).get(\"forecast\") == driver_forecast\n", "        return True\n",
         {"D3"}),
        ("M37 (G4) the Premier bonus is priced into the cost -> D2", BG_PATH,
         "    bought = {n: q for n, q in delta.items() if n in unconditional}\n", "    bought = dict(delta)\n", {"D2"}),
        ("M38 (G4) the driver's forecast check hollowed to a constant -> A4", HARNESS,
         "        production_forecast_ok = _forecast_ok(bool(R.get(\"balls_forecast_made\")), R.get(\"balls_forecast\"), "
         "rep)\n", "        production_forecast_ok = True\n", {"A4"}),
        ("M39 (G4) the driver re-reads the balls AFTER the restore -> A4", HARNESS,
         "        # ⛔ The ball grade is the PURE `ball_grade` module",
         "        R[\"balls_end\"] = _stock_by_name(BALLS)\n        # ⛔ The ball grade is the PURE `ball_grade` module",
         {"A4"}),
        ("N1b (G5) a COMMENT in `_stock_basket_early` naming both calls turns NOTHING red", LR_PATH,
         "    from modules.story.stock_topoff import sootopolis_ball_forecast\n",
         "    # (edited) sootopolis_ball_phase(report) and sootopolis_ball_forecast([], money, prices), in a comment\n"
         "    from modules.story.stock_topoff import sootopolis_ball_forecast\n", set()),
        ("N2 (G5) a STRING in `_stock_basket_early` naming both calls turns NOTHING red", LR_PATH,
         "    from modules.story.stock_topoff import sootopolis_ball_forecast\n",
         "    _note = \"sootopolis_ball_phase(report); sootopolis_ball_forecast([], money, prices)\"\n"
         "    from modules.story.stock_topoff import sootopolis_ball_forecast\n", set()),
        ("N1 a comment edit naming the phase and `blocked` turns NOTHING red", LR_PATH,
         "        # RULINGS 23 + 26 (design v2 step 9b): after the basket, on the same open menu",
         "        # (edited) sootopolis_ball_phase( and blocked named in a comment only; after the basket, same menu",
         set()),
    ]
    real = {T_NAME: sys.modules[T_NAME], LR_NAME: sys.modules[LR_NAME], BG_NAME: sys.modules[BG_NAME]}
    for i, (label, path, old, new, want) in enumerate(cases):
        src = path.read_text(encoding="utf-8")
        try:
            n = src.count(old)
            if n != 1:
                raise AssertionError(f"mutant anchor found {n} times: {old[:70]!r}")
            msrc = src.replace(old, new)
            if path in (T_PATH, LR_PATH, BG_PATH):
                name = {T_PATH: T_NAME, LR_PATH: LR_NAME, BG_PATH: BG_NAME}[path]
                mod = types.ModuleType(name)
                mod.__file__ = str(path)
                mod.__package__ = "modules.story" if path != BG_PATH else ""
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
