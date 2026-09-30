"""GATE — USER RULING 26, design v2 step 10b (HK at Sootopolis): the healing kit inside RULING 18's League-basket visit
(`modules/story/stock_topoff.py`: `kit_held_after_basket`, `kit_buys_here`, `sootopolis_kit_forecast`,
`sootopolis_topoff_phase`; `modules/story/league_reserve.py`: the effective walk and `_shop`'s dispatch) and the
`--driver earlybasket` kit grade (`kit_grade.py`).

WHY. The design (`ai-research-notes/2026-09-29-kittopoff10b-DESIGN.md`, E1-E11, after a recon AND an adversarial
review) says the kit and the basket buy the SAME names here, so they are separated by TIME; that 9b's ball forecast is
never overwritten; that each set is logged and memoised by its own verdict; and that a kit failure never costs the
balls. Built with 10a's lessons applied up front: the input dimensions are TABULATED below and each value has a row;
every expected line is derived from the DESIGN, never copied from the code's output; lines are matched by PREFIX;
the stubs keep the contracts of what they replace (`reserved_quantities` can raise; the fake buy can short either set).

INPUT DIMENSIONS (a row per value; ⚠ CORRECTED after the adversarial pass: the first version of this table named
dimensions the rows did NOT exercise, e.g. `_phase` always had a walking kit, never `observe` balls, never a raise
or close with the balls off, and 9b's `_s_env` pinned spare 18 so no S-row could produce both walks. 23 mutants
passed through those holes; each value below now names the row that REALLY sets it.)
  kit flag: unset/`0`/typo (O1) | observe (O2, S5) | `1` (O3...) | `1` without key items (O4, S6)
  ball flag: OFF (O10, S2, P9b, P12, P17a, P18) | observe (S11, P16, P17b) | `1` (most) | `1` blocked (O10d, S12,
             P9c, P14)
  memo: none | the kit key (O5, S7) | the ball key (O5, S12)
  kit reads: fine | raise (O6, P9, P22) | abort (O7, P8)
  held view: reserve (O2) | RAWBAG (O8) | above the reserve (H1) | converged, nothing to buy (S11, S12, P19-P21)
  money/floor: post_hm07 (O3) | complete basket (O11) | floor lever (O9, O13, P13, P15, P16) | spare (O10d, O12, S13)
  kit quantities above one unit: HP target 4, Full Heal 2 (O13)
  visit: basket (S9) | kit only (S2) | both walks (S13) | 9b's walk, the kit's split empty (S3) | BB9B-1 (S8)
  counter: both sets bought (P4) | one set short either way (P3, P4) | nothing to buy (P10, P20) | a kit that did
           not walk (P19, P21) | the live list vs the static list (P15, and the BALL list: P25) | raise (P5, P17) |
           BALLRAISE (P6) | close (P7, P18) | abort (P8) | the kit's own read raising (P9, P22, and on a BASKET visit:
           P24) | the ball flag OFF (P12) | a SHORT basket, so a live floor above the forecast's (P23) | a spare that
           DROPPED between the forecast and the counter (P26) | the wallet differing from the forecast's (P2)
  money on the lines: a set that planned nothing reads X->X (P1 the balls, P15 the kit)
  telemetry: the `[EARLY_BASKET]` kit suffix (S14)
  ⚠ ADDED after the THREE-LENS REVIEW (KT2-STUB1): `_phase`'s kit dict now carries EVERY key production's forecast
  writes (`FORECAST_KEYS`), and its `_inputs` floor follows the fake bag as the real one does. Before, a counter that
  read the forecast's floor, wallet or wants passed every row, because no row could make them differ from live.

ROWS: H1-H3 (pure), G1-G8 (`kit_grade.py`, executed), O1-O13 (the forecast, executed), S1-S14 (the visit,
executed), P1-P26 (the counter phase, executed), A1-A5 (AST), then mutants with EXACT red sets. The stubs keep the
contracts they replace: the kit-read fault is raised in `reserved_quantities` (the ONLY live lever,
`POKEBOT_RESERVE_FAULT_RAISE`, raises there), the fake `buy_in_shop` refuses up front exactly where the real one does
(an unsold item, a quantity outside 1-99, a total above the wallet), and `_inputs` reads the live wallet and derives
the live floor from the League basket still missing in the fake bag.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_kit_topoff_sootopolis.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import copy
import os
import pathlib
import sys
import types
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_stock_topoff_sootopolis as g9  # noqa: E402  (the 9b harnesses: Patch, drain, FakeBag, constants)

T_PATH, LR_PATH, HARNESS = g9.T_PATH, g9.LR_PATH, g9.HARNESS
KG_PATH = HERE / "kit_grade.py"
T_NAME, LR_NAME, KG_NAME = g9.T_NAME, g9.LR_NAME, "kit_grade"
import kit_grade  # noqa: E402,F401

FAILURES: list[str] = []
PRICES = dict(g9.PRICES, **{"Potion": 300, "Super Potion": 700, "Max Potion": 2500, "Awakening": 250,
                            "Ice Heal": 250})
PLAN = list(g9.PLAN)                                             # [Revive 3, Full Heal 8, Hyper Potion 30]
TARGET = {"Hyper Potion": 30, "Full Restore": 3, "Full Heal": 8, "Revive": 3}   # the armed reserve (the basket)
KIT_KEY, BALL_KEY = "SootopolisCity:kit", "SootopolisCity"
HYPER1 = [("Hyper Potion", 1)]
#: ⛔ The rest of the kit dict production's forecast writes (the review's KT2-STUB1), at the values it writes for
#: post_hm07's counter state. The counter must re-plan from the LIVE floor, wallet and list, so a row whose live state
#: differs (P2's wallet, P15/P19-P21's list or held view, P23's short basket) catches a counter that reads these.
FORECAST_KEYS = {"floor": 19000, "money_after_basket": 22166, "wants": [("Hyper Potion", 4), ("Full Heal", 2)],
                 "reason": "the forecast's reason (the counter re-plans; it must never read these keys)"}


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def row(label, fn, tag, reds):
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if not ok:
        reds.append(label.split()[0])
    if not tag:
        check(label, ok, detail)


def mods():
    return sys.modules[T_NAME], sys.modules[LR_NAME]


def tags(emitted, prefix):
    return [line.split()[1] for line in emitted if line.startswith(prefix)]


K, B = "[KIT-BUY]", "[BALLS-BUY]"


# ------------------------------------------------------------------------------------------------ H rows (pure)
def h_rows(tag=""):
    t, lr = mods()
    reds: list = []

    def h1():
        a = t.kit_held_after_basket({}, PLAN, TARGET, False)
        b = t.kit_held_after_basket({}, PLAN, {}, True)
        c = t.kit_held_after_basket({"Hyper Potion": 31}, [], TARGET, False)
        d = t.kit_held_after_basket({"Hyper Potion": 10, "Full Heal": 2}, [], TARGET, False)
        return (a["Hyper Potion"] == 0 and a["Full Heal"] == 0 and b["Hyper Potion"] == 30 and b["Full Heal"] == 8
                and c["Hyper Potion"] == 1 and d["Hyper Potion"] == 0 and d["Full Heal"] == 0
                and min(a.values()) >= 0 and min(d.values()) >= 0), f"{a} {b} {c} {d}"

    def h2():
        cases = [None, {"mode": "observe"}, {"mode": "1", "skip": "x"}, {"mode": "1", "blocked": True},
                 {"mode": "1"}]
        got = [t.kit_buys_here(c) for c in cases]
        return got == [False, False, False, False, True], str(got)

    def h3():
        return (t.SOOTOPOLIS_STATIC_KIT_SOLD == ("Hyper Potion", "Full Heal") and t.sootopolis_kit_key() == KIT_KEY
                and lr.TOPOFF_ONLY_OUTCOMES == ("balls only", "kit only", "balls and kit only")), \
            f"{t.SOOTOPOLIS_STATIC_KIT_SOLD} {t.sootopolis_kit_key()} {lr.TOPOFF_ONLY_OUTCOMES}"

    for label, fn in (("H1 the held view projects the basket, subtracts the reserve (RAWBAG: not), never negative", h1),
                      ("H2 the kit BUYS only in mode 1, not skipped, not blocked", h2),
                      ("H3 the static kit list, the kit key, the exported top-off outcomes ('balls only' first)", h3)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------------- G rows (kit_grade)
def g_rows(tag=""):
    kg = sys.modules[KG_NAME]
    reds: list = []
    start = {"Hyper Potion": 0, "Full Heal": 0, "Revive": 0, "Potion": 1, "Max Potion": 0}

    def g1():   # S-ON: the bag shows the SUM (31 Hyper), the kit part is 1, priced 1200
        end = {"Hyper Potion": 31, "Full Heal": 8, "Revive": 3, "Potion": 1, "Max Potion": 0}
        a = kg.kit_action(start, end, PLAN, HYPER1, PRICES)
        return (a["delta"] == {"Hyper Potion": 31, "Full Heal": 8, "Revive": 3} and a["kit"] == {"Hyper Potion": 1}
                and a["expected"] == {"Revive": 3, "Full Heal": 8, "Hyper Potion": 31} and a["kit_cost"] == 1200
                and a["kit_expected"] == {"Hyper Potion": 1}), str(a)

    def g2():   # kit-only, and a no-op kit, and a short basket (never a negative kit), and a Max Potion
        only = kg.kit_action({"Hyper Potion": 30}, {"Hyper Potion": 31}, [], HYPER1, PRICES)
        noop = kg.kit_action(start, {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3}, PLAN, HYPER1, PRICES)
        short = kg.kit_action(start, {"Hyper Potion": 29, "Full Heal": 8, "Revive": 3}, PLAN, [], PRICES)
        maxp = kg.kit_action(start, {"Max Potion": 1}, [], [], PRICES)
        return (only["kit"] == {"Hyper Potion": 1} and noop["kit"] == {} and noop["kit"] != noop["kit_expected"]
                and short["kit"] == {} and maxp["kit"] == {"Max Potion": 1} and maxp["kit"] != maxp["kit_expected"]), \
            f"{only['kit']} {noop['kit']} {short['kit']} {maxp['kit']}"

    def g3():
        rep = {"kit": {"forecast": HYPER1, "split_balls": []}}
        return (kg.production_kit_forecast_ok(True, HYPER1, [], rep)
                and not kg.production_kit_forecast_ok(True, [], [], rep)
                and not kg.production_kit_forecast_ok(True, HYPER1, [("Ultra Ball", 1)], rep)
                and kg.production_kit_forecast_ok(False, [], [], {"balls": {}})
                and not kg.production_kit_forecast_ok(False, [], [], rep)
                # the review's KT2-Z1: a MADE forecast with NO kit dict, or an empty one, is never agreement (the D2
                # skip and RESERVE_FAULT_RAISE make the driver's forecast [] while production must still write the key)
                and not kg.production_kit_forecast_ok(True, [], [], {"balls": {}})
                and not kg.production_kit_forecast_ok(True, [], [], {"kit": {}})), "made/unmade/forecast/split/missing"

    def g4():
        good = {"kit": {"got": {"Hyper Potion": 1}, "ok": True}}
        return (kg.kit_attributed(good, {"Hyper Potion": 1}) and not kg.kit_attributed(good, {"Full Heal": 1})
                and not kg.kit_attributed({"kit": {"got": {"Hyper Potion": 1}, "ok": False}}, {"Hyper Potion": 1})
                and not kg.kit_attributed({}, {"Hyper Potion": 1})), "got/ok"

    def g5():   # the kit's `before` was read AFTER the basket (PRE 0 + plan 30 = 30), not before it (0)
        after = {"kit": {"before": {"Hyper Potion": 30}}}
        before = {"kit": {"before": {"Hyper Potion": 0}}}
        mixed = {"kit": {"before": {"Hyper Potion": 30, "Full Heal": 0}}}      # right for one item only
        return (kg.kit_before_after_basket(after, {"Hyper Potion": 0}, PLAN)
                and not kg.kit_before_after_basket(before, {"Hyper Potion": 0}, PLAN)
                and not kg.kit_before_after_basket({"kit": {}}, {"Hyper Potion": 0}, PLAN)
                and not kg.kit_before_after_basket(mixed, {"Hyper Potion": 0, "Full Heal": 0}, PLAN)), \
            "after/before/empty/mixed"

    def g6():   # the summed kit lines, and the per-name total when the names overlap
        a = kg.kit_action(start, start, PLAN, [("Hyper Potion", 1), ("Full Heal", 1)], PRICES)
        return (a["kit_expected"] == {"Hyper Potion": 1, "Full Heal": 1}
                and a["expected"] == {"Revive": 3, "Full Heal": 9, "Hyper Potion": 31}), str(a)

    def g7():   # S-RAW's end state: no kit bought although one was expected -> the MEASURED kit costs 0
        end = {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Potion": 1, "Max Potion": 0}
        a = kg.kit_action(start, end, PLAN, HYPER1, PRICES)
        return a["kit"] == {} and a["kit_cost"] == 0, str(a)

    def g8():   # a CONSUMED stack shows in the delta (Potion -1), so "the medicine delta equals the kit" fails
        a = kg.kit_action({"Potion": 1, "Hyper Potion": 0}, {"Potion": 0, "Hyper Potion": 1}, [], HYPER1, PRICES)
        return (a["delta"] == {"Hyper Potion": 1, "Potion": -1} and a["kit"] == {"Hyper Potion": 1}
                and a["delta"] != a["kit_expected"]), str(a)

    for label, fn in (("G1 S-ON: the bag's SUM is 31, the kit part 1, priced 1200", g1),
                      ("G2 kit-only; a no-op kit fails; a short basket is never a negative kit; a Max Potion shows", g2),
                      ("G3 production's kit forecast AND split must equal the driver's; unmade = no kit key", g3),
                      ("G4 the attribution: production's got equals the kit and says ok", g4),
                      ("G5 the kit's before was read AFTER the basket", g5),
                      ("G6 overlapping names sum per name", g6),
                      ("G7 the kit is priced from the MEASURED delta (none bought -> 0)", g7),
                      ("G8 a consumed stack stays in the delta", g8)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------ O rows (the kit forecast)
def _f_env(p, t, lr, *, ball, kit, keyitems="1", rawbag=None, rraise=None, floor=None, stock=None, memo=None,
           spare=18, emitted, spy):
    from modules.context import context
    from modules.story import early_game as eg

    p.setenv(POKEBOT_R23_BALLRESTOCK=ball, POKEBOT_R26_KITTOPOFF=kit, POKEBOT_R27_KEYITEMS=keyitems,
             POKEBOT_R26_FAULT_RAWBAG=rawbag, POKEBOT_RESERVE_FAULT_RAISE=None, POKEBOT_R23_FAULT_FLOOR=floor)
    raw = dict(g9.EMPTY_BASKET if stock is None else stock)

    def inputs(_mode):
        spy.append("inputs")
        return {"stage": "BASKET_ERA", "floor": 109600, "spare": spare, "money": 67466, "flags": dict(g9.ERA),
                "price_of": lambda n: PRICES[n]}

    def reserved():
        spy.append("reserved")
        if rraise:
            raise rraise
        return dict(TARGET)

    def reraise(error):        # FAITHFUL: re-raises the error it was GIVEN
        if "ABORT" in str(error):
            raise error

    p.set(t, "_inputs", inputs)
    p.set(t, "_allowed", lambda: set(g9.ALL_BALLS))
    p.set(t, "_emit", lambda line: emitted.append(line))
    p.set(lr, "_stock_by_name", lambda names: {n: raw.get(n, 0) for n in names})
    p.set(lr, "reserved_quantities", reserved)
    p.set(eg, "reraise_if_aborting", reraise)
    p.set(context, "bot_mode_instance", SimpleNamespace(_ball_topoff_failed=memo if memo is not None else set()))


def o_rows(tag=""):
    t, lr = mods()
    reds: list = []

    def fc(*, balls=None, plan=PLAN, money=67466, **env):
        emitted, spy = [], []
        with g9.Patch() as p:
            _f_env(p, t, lr, emitted=emitted, spy=spy, **env)
            out = t.sootopolis_kit_forecast(plan, money, g9.BASKET_PRICES, balls)
        return out, emitted, spy

    ON = {"mode": "1", "walk": True, "blocked": False, "forecast": [("Ultra Ball", 1)]}

    def o1():
        a = fc(ball="1", kit=None)
        b = fc(ball="1", kit="0")
        c = fc(ball="1", kit="yes")
        return (a[0] is None and b[0] is None and c[0] is None and a[2] == [] and b[2] == [] and c[2] == []
                and a[1] == [] and tags(c[1], K) == ["why=kit-flag"]), f"{a} {b} {c}"

    def o2():
        out, emitted, _ = fc(ball="1", kit="observe", balls=copy.deepcopy(ON))
        return (out["forecast"] == HYPER1 and out["split_balls"] == [] and out["walk"] is False
                and tags(emitted, K) == ["why=kit-observe"] and "kit=[('Hyper Potion', 1)]" in emitted[0]), \
            f"{out} {emitted}"

    def o3():
        out, emitted, _ = fc(ball="1", kit="1", balls=copy.deepcopy(ON))
        return (out["forecast"] == HYPER1 and out["split_balls"] == [] and out["walk"] is True
                and tags(emitted, K) == ["why=kit-forecast"] and "split_balls=[]" in emitted[0]
                and "walk=True" in emitted[0]), f"{out} {emitted}"

    def o4():
        out, emitted, spy = fc(ball="1", kit="1", keyitems=None, balls=copy.deepcopy(ON))
        return (out["skip"] and out["forecast"] == [] and out["walk"] is False and tags(emitted, K) == ["why=kit-skip"]
                and spy == []), f"{out} {emitted} {spy}"

    def o5():
        a = fc(ball="1", kit="1", memo={KIT_KEY}, balls=copy.deepcopy(ON))
        b = fc(ball="1", kit="1", memo={BALL_KEY}, balls=copy.deepcopy(ON))
        return (a[0]["blocked"] is True and a[0]["walk"] is False and a[2] == []
                and b[0]["blocked"] is False and b[0]["forecast"] == HYPER1), f"{a} || {b[0]}"

    def o6():
        balls = copy.deepcopy(ON)
        memo: set = set()
        out, emitted, _ = fc(ball="1", kit="1", balls=balls, memo=memo, rraise=RuntimeError("reserve read broken"))
        return (out["blocked"] is True and out["walk"] is False and tags(emitted, K) == ["why=kit-failed"]
                and memo == {KIT_KEY} and balls == ON and tags(emitted, B) == []), f"{out} {memo} {emitted}"

    def o7():
        try:
            fc(ball="1", kit="1", balls=copy.deepcopy(ON), rraise=RuntimeError("ABORT"))
        except RuntimeError as error:
            return "ABORT" in str(error), f"re-raised {error!r}"
        return False, "swallowed the abort"

    def o8():
        out, _e, _ = fc(ball="1", kit="1", rawbag="1", balls=copy.deepcopy(ON))
        return out["forecast"] == [] and out["split_balls"] == [("Ultra Ball", 1)], str(out)

    def o9():
        out, _e, _ = fc(ball="1", kit="1", floor="30000", balls=copy.deepcopy(ON))
        return out["forecast"] == [] and out["split_balls"] == [] and out["walk"] is False, str(out)

    def o10():
        blocked = dict(ON, blocked=True)
        a = fc(ball="1", kit="1", balls=blocked)[0]
        b = fc(ball=None, kit="1", balls=None)[0]
        # spare 10 with the balls OFF: NO reserve phase may eat the budget (buy_balls False), so the kit gets Hyper 1
        c = fc(ball=None, kit="1", spare=10, balls=None)[0]
        # spare 10 with the balls BLOCKED: the same (added after gate run 2: MA's set was derived against this case,
        # which the first edit of this row left out; the set stands, disclosed in the REVIEW-GATE evidence)
        d = fc(ball="1", kit="1", spare=10, balls=dict(ON, blocked=True))[0]
        return (a["split_balls"] == [] and b["split_balls"] == [] and b["forecast"] == HYPER1
                and c["forecast"] == HYPER1 and d["forecast"] == HYPER1 and d["split_balls"] == []), \
            f"{a} {b} {c} {d}"

    def o11():
        full = dict(g9.FULL_BASKET)
        a = fc(ball="1", kit="1", stock=full, plan=[], money=22166, balls=copy.deepcopy(ON))[0]
        b = fc(ball=None, kit="1", stock=full, plan=[], money=22166, balls=None)[0]
        return (a["forecast"] == HYPER1 and a["split_balls"] == [] and a["walk"] is True
                and b["forecast"] == HYPER1 and b["walk"] is True), f"{a} {b}"

    def o12():
        s10 = fc(ball="1", kit="1", spare=10, balls=copy.deepcopy(ON))[0]
        s11 = fc(ball="1", kit="1", spare=11, balls=copy.deepcopy(ON))[0]
        return (s10["forecast"] == [] and s10["split_balls"] == [("Ultra Ball", 1)]
                and s11["forecast"] == HYPER1 and s11["split_balls"] == []), f"{s10} {s11}"

    def o13():  # the review's KT2-X4: the forecast's kit QUANTITIES above one unit (D5: HP to 4, Full Heal to 2)
        # (a) Hyper 32 / Full Heal 10 held: 2 above the reserve each -> wants Hyper 2 only; ₽1,583 buys one
        a = fc(ball=None, kit="1", stock={"Hyper Potion": 32, "Full Restore": 0, "Full Heal": 10, "Revive": 3},
               plan=[], money=22166, balls=None)[0]
        # (b) post_hm07's plan with the floor lever at 1,000: the budget is the ₽6,000 cap -> Hyper 4 + Full Heal 2
        b = fc(ball=None, kit="1", floor="1000", balls=None)[0]
        return (a["wants"] == [("Hyper Potion", 2)] and a["forecast"] == HYPER1 and a["walk"] is True
                and b["wants"] == [("Hyper Potion", 4), ("Full Heal", 2)]
                and b["forecast"] == [("Hyper Potion", 4), ("Full Heal", 2)] and b["walk"] is True), f"{a} || {b}"

    for label, fn in (("O1 OFF (unset, 0, a typo) returns None and reads NOTHING; a typo is one kit-flag line", o1),
                      ("O2 observe: plans Hyper 1, never walks, one kit-observe line", o2),
                      ("O3 kit 1: Hyper 1, the split is [] (the kit takes the budget), walks; the line shows the split",
                       o3),
                      ("O4 kit 1 WITHOUT key items: a named skip, reads nothing", o4),
                      ("O5 the KIT memo blocks the kit (no reads); the BALL memo does not", o5),
                      ("O6 a raise in the kit's OWN read: kit blocked, only the kit key, the ball forecast untouched",
                       o6),
                      ("O7 an abort in the kit's read is re-raised", o7),
                      ("O8 RAWBAG: raw 30/8 wants nothing, the split is 9b's Ultra", o8),
                      ("O9 the floor lever (30000) reaches the kit: nothing affordable", o9),
                      ("O10 balls blocked or OFF: no split (the kit alone)", o10),
                      ("O11 a complete basket (eb_after_M0a): Hyper 1 with or without the balls", o11),
                      ("O12 the spare threshold: 10 gives the reserve Ultra and no kit, 11 gives Hyper 1", o12),
                      ("O13 kit quantities above one: wants Hyper 2 (2 held); the ₽6,000 cap buys Hyper 4 + Full Heal 2",
                       o13)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------ S rows (the visit)
def s_rows(tag=""):
    t, lr = mods()
    reds: list = []

    def visit(*, ball, kit, keyitems="1", stock, money, memo=None, plan_raw=None, spare=18):
        emitted, calls = [], []
        # the keys `stock_basket_early` sets before calling `_stock_basket_early` (production's shape)
        report = {"readings": set(), "order": [], "walked": False}
        with g9.Patch() as p:
            g9._s_env(p, t, lr, flag=ball, money=money, stock=stock, emitted=emitted, calls=calls, memo=memo)
            p.setenv(POKEBOT_R26_KITTOPOFF=kit, POKEBOT_R27_KEYITEMS=keyitems)
            p.set(lr, "reserved_quantities", lambda: dict(TARGET))
            # the adversarial pass: 9b's `_s_env` pins spare 18, so no S-row could ever produce BOTH walks
            p.set(t, "_inputs", lambda _m: {"stage": "BASKET_ERA", "floor": 0, "spare": spare, "money": money,
                                            "flags": dict(g9.ERA), "price_of": lambda n: PRICES[n]})

            def shop(report_, plan, names, before, money_, _take):
                calls.append(("shop", list(plan), copy.deepcopy(report_.get("balls")),
                              copy.deepcopy(report_.get("kit"))))
                _take("EB-MART")
                yield

            p.set(lr, "_shop", shop)
            g9.drain(lr._stock_basket_early(report))
        return report, emitted, calls

    FULL, EMPTY = dict(g9.FULL_BASKET), dict(g9.EMPTY_BASKET)

    def s1():   # kit OFF, complete basket, balls OFF: 9b's "nothing missing", no kit key
        rep, _e, calls = visit(ball=None, kit=None, stock=FULL, money=22166)
        return rep.get("early_basket") == "nothing missing" and "kit" not in rep and "balls" not in rep, str(rep)

    def s2():   # kit-only walk, balls OFF: no crash, "kit only", no balls key
        rep, _e, calls = visit(ball=None, kit="1", stock=FULL, money=22166)
        shops = [c for c in calls if isinstance(c, tuple) and c[0] == "shop"]
        return (rep.get("early_basket") == "kit only" and "balls" not in rep and rep.get("walked") is True
                and len(shops) == 1), str(rep.get("early_basket"))

    def s3():   # S-BOTHKIT: 9b's forecast walks (Ultra 1) but the EFFECTIVE ball walk is the empty split
        rep, _e, _c = visit(ball="1", kit="1", stock=FULL, money=22166)
        return (rep.get("early_basket") == "kit only" and rep["balls"]["forecast"] == [("Ultra Ball", 1)]
                and rep["balls"]["walk"] is True and rep["kit"]["split_balls"] == []), \
            f"{rep.get('early_basket')} {rep.get('balls')} {rep.get('kit')}"

    def s4():   # the kit buys but wants nothing (held above the reserve): the split is 9b's balls, "balls only"
        rich = dict(FULL, **{"Hyper Potion": 34, "Full Heal": 10})
        rep, _e, _c = visit(ball="1", kit="1", stock=rich, money=22166)
        return (rep.get("early_basket") == "balls only" and rep["kit"]["forecast"] == []
                and rep["kit"]["split_balls"] == [("Ultra Ball", 1)]), f"{rep.get('early_basket')} {rep.get('kit')}"

    def s5():   # kit observe: 9b's walk decides ("balls only")
        rep, _e, _c = visit(ball="1", kit="observe", stock=FULL, money=22166)
        return rep.get("early_basket") == "balls only" and rep["kit"]["walk"] is False, str(rep.get("early_basket"))

    def s6():   # kit 1 without key items, balls OFF, complete basket: "nothing missing", a skip in the kit key
        rep, _e, _c = visit(ball=None, kit="1", keyitems=None, stock=FULL, money=22166)
        return (rep.get("early_basket") == "nothing missing" and rep.get("kit", {}).get("skip")
                and rep.get("walked") is False), str(rep)

    def s7():   # the kit memoised, balls 1: 9b's walk and label exactly
        rep, _e, _c = visit(ball="1", kit="1", stock=FULL, money=22166, memo={KIT_KEY})
        return (rep.get("early_basket") == "balls only" and rep["kit"]["blocked"] is True), str(rep.get("kit"))

    def s9():   # a BASKET visit with the kit ON: EB-PLANNED, and the report carries both forecasts into `_shop`
        rep, _e, calls = visit(ball="1", kit="1", stock=EMPTY, money=67466)
        shops = [c for c in calls if isinstance(c, tuple) and c[0] == "shop"]
        return (len(shops) == 1 and shops[0][1] == PLAN and shops[0][3]["forecast"] == HYPER1
                and shops[0][2]["forecast"] == [("Ultra Ball", 1)] and "EB-PLANNED" in rep.get("order", [])), \
            str(shops)

    # --- `_shop`
    def run_shop(*, balls, kit, plan, sold):
        calls: list = []
        with g9.Patch() as p:
            from modules import mart as _mart
            from modules.context import context
            from modules.modes.util import tasks_scripts as _ts
            from modules.story import victory_road as vr

            def basket_lines(report, plan_, names, before, money, _take):
                calls.append(("basket", list(plan_)))
                yield

            def ball_phase(report):
                calls.append("ball_phase")
                yield

            def topoff_phase(report):
                calls.append("topoff_phase")
                yield

            p.set(_ts, "task_is_active", lambda name: True)
            p.set(_mart, "get_mart_buyable_items", lambda: [SimpleNamespace(name=n) for n in sold])
            p.set(vr, "_where", lambda: "stub")
            p.set(context, "emulator", SimpleNamespace(get_frame_count=lambda: 0, press_button=lambda b: None))
            p.set(lr, "_buy_basket_lines", basket_lines)
            p.set(t, "sootopolis_ball_phase", ball_phase)
            p.set(t, "sootopolis_topoff_phase", topoff_phase)
            report = {"readings": set(), "order": [], "frame_start": 0}
            if balls is not None:
                report["balls"] = balls
            if kit is not None:
                report["kit"] = kit
            try:
                g9.drain(lr._shop(report, plan, ["Revive", "Full Heal", "Hyper Potion"], {}, 22166,
                                  lambda r: report["order"].append(r)))
            except Exception as error:  # noqa: BLE001 - the raise itself is what some rows assert
                calls.append(("raised", str(error)))
        return calls

    SOLD = ["Ultra Ball", "Hyper Potion", "Revive", "Full Heal"]
    KIT_BUYS = {"mode": "1", "walk": True, "forecast": HYPER1, "split_balls": []}
    BALLS_ON = {"mode": "1", "walk": True, "blocked": False, "forecast": [("Ultra Ball", 1)]}

    def s8():   # BB9B-1 with a buying kit: a BASKET visit whose Mart sells none of the basket still raises
        calls = run_shop(balls=None, kit=dict(KIT_BUYS), plan=PLAN, sold=["Ultra Ball"])
        return (any(isinstance(c, tuple) and c[0] == "raised" and "sells none" in c[1] for c in calls)
                and "topoff_phase" not in calls), str(calls)

    def s10():  # the dispatch: kit buys -> the topoff phase ONLY; kit observe / OFF -> 9b's ball phase; kit-only visit
        a = run_shop(balls=dict(BALLS_ON), kit=dict(KIT_BUYS), plan=PLAN, sold=SOLD)
        b = run_shop(balls=dict(BALLS_ON), kit={"mode": "observe", "walk": False}, plan=PLAN, sold=SOLD)
        c = run_shop(balls=dict(BALLS_ON), kit=None, plan=PLAN, sold=SOLD)
        d = run_shop(balls=None, kit=dict(KIT_BUYS), plan=[], sold=SOLD)
        e = run_shop(balls=dict(BALLS_ON), kit={"mode": "1", "skip": "no key items", "walk": False}, plan=PLAN,
                     sold=SOLD)
        f = run_shop(balls=dict(BALLS_ON), kit={"mode": "1", "blocked": True, "walk": False}, plan=PLAN, sold=SOLD)
        return (a == [("basket", PLAN), "topoff_phase"] and b == [("basket", PLAN), "ball_phase"]
                and c == [("basket", PLAN), "ball_phase"] and d == ["topoff_phase"]
                and e == [("basket", PLAN), "ball_phase"] and f == [("basket", PLAN), "ball_phase"]), \
            f"{a} {b} {c} {d} {e} {f}"

    # --- added after the ADVERSARIAL MUTANT PASS (its MA, MC2, ML, MK, MJ): each row's expectation is from the design
    RICH = dict(g9.FULL_BASKET, **{"Hyper Potion": 34, "Full Heal": 10})     # a converged kit: nothing to buy

    def s11():  # E2: `observe` balls are OFF for the split: a converged kit + observe balls = "nothing missing"
        rep, _e, _c = visit(ball="observe", kit="1", stock=RICH, money=22166)
        return rep.get("early_basket") == "nothing missing" and rep.get("walked") is False, str(rep.get("early_basket"))

    def s12():  # E2: BLOCKED balls are OFF for the split: the ball memo + a converged kit = "nothing missing"
        rep, _e, _c = visit(ball="1", kit="1", stock=RICH, money=22166, memo={BALL_KEY})
        return rep.get("early_basket") == "nothing missing" and rep.get("walked") is False, str(rep.get("early_basket"))

    def s13():  # E3: BOTH effective walks: spare 5, ₽30,000 (budget 5,500: 4 Ultras to the reserve, then Full Heal 1)
        rep, _e, _c = visit(ball="1", kit="1", stock=FULL, money=30000, spare=5)
        return (rep.get("early_basket") == "balls and kit only" and rep["kit"]["forecast"] == [("Full Heal", 1)]
                and rep["kit"]["split_balls"] == [("Ultra Ball", 4)]), f"{rep.get('early_basket')} {rep.get('kit')}"

    def telemetry(keys):
        events = []
        with g9.Patch() as p:
            from modules import debug_logger as _dl
            from modules.context import context

            p.setenv(POKEBOT_RESERVE_FAULT_BUDGET=None)

            def fake(report):
                report.update(copy.deepcopy(keys))
                yield

            p.set(lr, "_stock_basket_early", fake)
            p.set(_dl, "event", lambda message, category="STORY": events.append((category, message)))
            p.set(context, "emulator", SimpleNamespace(get_frame_count=lambda: 0))
            g9.drain(lr.stock_basket_early({}))
        return [m for c, m in events if c == "EARLY_BASKET"]

    def s14():  # E3 [R14]: the `[EARLY_BASKET]` line carries ` kit=` ONLY when the kit reported; kit OFF = 9b's line
        balls = {"mode": "1", "walk": True, "forecast": [("Ultra Ball", 1)]}
        off = telemetry({"early_basket": "balls only", "balls": balls})
        on = telemetry({"early_basket": "kit only", "kit": {"mode": "1", "walk": True, "forecast": HYPER1}})
        return (len(off) == 1 and " balls=" in off[0] and " kit=" not in off[0]
                and len(on) == 1 and " kit={" in on[0] and " balls=" not in on[0]), f"{off} || {on}"

    for label, fn in (("S1 kit OFF: 9b's 'nothing missing', no kit key", s1),
                      ("S2 a kit-only walk with the balls OFF: no crash, 'kit only', no balls key", s2),
                      ("S3 S-BOTHKIT: the effective ball walk is the EMPTY split: 'kit only'; 9b's forecast kept", s3),
                      ("S4 the kit buys nothing: the split is 9b's Ultra, 'balls only'", s4),
                      ("S5 kit observe: 9b decides the walk ('balls only')", s5),
                      ("S6 a D2 skip, balls OFF, complete basket: 'nothing missing', no walk", s6),
                      ("S7 the kit memoised: 9b's 'balls only' walk", s7),
                      ("S8 BB9B-1 holds with a buying kit forecast (a basket Mart selling none raises)", s8),
                      ("S9 a basket visit carries BOTH forecasts into _shop", s9),
                      ("S10 _shop dispatches: kit buys -> the top-off phase alone; observe/OFF -> 9b's phase", s10),
                      ("S11 observe balls are OFF for the split: a converged kit walks nowhere", s11),
                      ("S12 BLOCKED balls are OFF for the split: a converged kit walks nowhere", s12),
                      ("S13 both effective walks: 'balls and kit only' (4 Ultras to the reserve, Full Heal 1)", s13),
                      ("S14 the [EARLY_BASKET] line: ' kit=' only when the kit reported (kit OFF = 9b's line)", s14)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------ P rows (the counter phase)
def _phase(*, ball="1", kit_mode="1", bag=None, money=22166, buy="ok", short=None, memo=None, floor_env=None,
           raise_env=None, early="bought", held_raise=None, sold=None, kit_extra=None, close_after=None,
           ball_blocked=False):
    """Runs `sootopolis_topoff_phase` with 9b's phase fakes, a post-basket bag, and a FAITHFUL `_kit_held` (the real
    one, over stubbed reads). `short` = {name: n} shorts that name's purchase by n (either set)."""
    t, lr = mods()
    emitted, calls = [], []
    memo = set() if memo is None else memo
    report = copy.deepcopy(g9.R18_KEYS)
    report["early_basket"] = early
    if ball is not None:
        report["balls"] = {"mode": ball, "walk": True, "blocked": ball_blocked, "forecast": [("Ultra Ball", 5)]}
    report["kit"] = dict({"mode": kit_mode, "walk": True, "blocked": False, "forecast": [("Hyper Potion", 9)],
                          "split_balls": [], **copy.deepcopy(FORECAST_KEYS)}, **(kit_extra or {}))
    root = copy.deepcopy({k: v for k, v in report.items() if k not in ("balls", "kit")})
    out = None
    with g9.Patch() as p:
        fbag = g9._p_env(p, sys.modules[T_NAME], money=money, buy="ok", emitted=emitted, memo=memo,
                         floor_env=floor_env, raise_env=raise_env, calls=calls)
        fbag.counts.update(bag if bag is not None else {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Potion": 1})
        p.setenv(POKEBOT_R23_BALLRESTOCK=ball, POKEBOT_R26_KITTOPOFF=kit_mode, POKEBOT_R27_KEYITEMS="1")
        from modules import mart as _mart
        from modules import player as _player
        from modules.modes.util import higher_level_actions as _hla

        wallet = {"money": money}
        p.set(_player, "get_player", lambda: SimpleNamespace(money=wallet["money"]))

        def buy_in_shop(shopping):
            # FAITHFUL to the real `buy_in_shop`'s up-front refusals (the pass's stub finding 5)
            sold_now = {i.name for i in _mart.get_mart_buyable_items()}
            if (any(i.name not in sold_now for i, _q in shopping) or any(not 1 <= q <= 99 for _i, q in shopping)
                    or sum(PRICES[i.name] * q for i, q in shopping) > wallet["money"]):
                raise RuntimeError("BotModeError: buy_in_shop refuses up front (an unsold item, a bad quantity or "
                                   "the wallet)")
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
                got = qty - (short or {}).get(item.name, 0)
                fbag.counts[item.name] = fbag.counts.get(item.name, 0) + got
                wallet["money"] -= got * PRICES[item.name]

        p.set(_hla, "buy_in_shop", buy_in_shop)
        if sold is not None:
            p.set(_mart, "get_mart_buyable_items", lambda: [SimpleNamespace(name=n) for n in sold])

        def stock(names):
            return {n: fbag.counts.get(n, 0) for n in names}

        def reserved():
            # The ONE live lever for a kit-only read failure, POKEBOT_RESERVE_FAULT_RAISE, raises HERE (through
            # `reserve_active`), never in `_stock_by_name`, which 9b's own `_inputs` reads too (the pass's finding 6).
            if held_raise:
                raise held_raise
            return dict(TARGET)

        p.set(lr, "_stock_by_name", stock)
        p.set(lr, "reserved_quantities", reserved)
        from modules.story.victory_road import LEAGUE_BASKET, basket_to_buy

        def live_floor():
            # FAITHFUL to the real `_inputs`: CASH_FLOOR + 2 x the League basket still MISSING in the bag, so a SHORT
            # basket raises it (the review's KT2-STUB1: a constant ₽19,000 equalled every forecast's floor)
            missing = basket_to_buy({n: fbag.counts.get(n, 0) for n, _q in LEAGUE_BASKET})
            return sys.modules[T_NAME].floor("BASKET_ERA", sum(PRICES[n] * q for n, q in missing))

        # `_inputs` reads the LIVE wallet (9b's `_p_env` kept a private one the fake buy never debited: finding 4)
        p.set(sys.modules[T_NAME], "_inputs", lambda _m: {"stage": "BASKET_ERA", "floor": live_floor(),
                                                         "spare": fbag.number_of_balls_except_master_ball,
                                                         "money": wallet["money"], "flags": dict(g9.ERA),
                                                         "price_of": lambda n: PRICES[n]})
        t = sys.modules[T_NAME]
        gen = t.sootopolis_topoff_phase(report)
        try:
            n = 0
            while True:
                next(gen)
                n += 1
                if close_after is not None and n >= close_after:
                    try:
                        gen.close()
                        out = "CLOSED"
                    except Exception as error:  # noqa: BLE001 - a close that raises is the row's failure
                        out = f"CLOSE RAISED {error!r}"
                    break
                if n > 500:
                    out = "NO END"
                    break
        except StopIteration:
            out = "done"
    rest = {k: v for k, v in report.items() if k not in ("balls", "kit")}
    return SimpleNamespace(out=out, report=report, emitted=emitted, calls=calls, memo=memo, bag=fbag.counts,
                           isolated=rest == root)


def p_rows(tag=""):
    reds: list = []

    def buys(r):
        return [c[1] for c in r.calls if isinstance(c, tuple) and c[0] == "buy"]

    def p1():   # S-ON's counter: Hyper 1, no ball; the kit's before = 30 (after the basket); both lines, per set
        r = _phase()
        kf = [x for x in r.emitted if x.startswith(K + " why=kit ")]
        bl = [x for x in r.emitted if x.startswith(B)]
        # the review's DC2: the ball set planned nothing, so ITS line reads the wallet unchanged (never the kit's ₽1,200)
        return (buys(r) == [HYPER1] and r.report["kit"]["got"] == {"Hyper Potion": 1} and r.report["kit"]["ok"]
                and r.report["kit"]["before"] == {"Hyper Potion": 30} and tags(r.emitted, B) == ["why=topoff-none"]
                and tags(r.emitted, K) == ["why=kit"] and "bought={'Hyper Potion': 1}" in kf[0]
                and " money=22166->22166 " in bl[0] and r.report["balls"]["money_after"] == 22166
                and r.memo == set() and r.isolated), f"{buys(r)} {r.report['kit']} {r.emitted}"

    def p2():   # S-FH's counter (money 20,966, a Hyper already above the reserve): 1 Full Heal
        r = _phase(money=20966, bag={"Hyper Potion": 31, "Full Heal": 8, "Revive": 3, "Ultra Ball": 1})
        return buys(r) == [[("Full Heal", 1)]] and r.report["kit"]["ok"] and r.isolated, f"{buys(r)} {r.emitted}"

    def p3():   # the kit short, the balls not bought: only the kit key; the kit's own failed line
        r = _phase(short={"Hyper Potion": 1})
        return (r.memo == {KIT_KEY} and tags(r.emitted, K) == ["why=kit-failed"]
                and tags(r.emitted, B) == ["why=topoff-none"] and r.isolated), f"{r.memo} {r.emitted}"

    def p4():   # BOTH sets bought (spare 8: the reserve phase) and the BALLS short: only the ball key, the kit's line ok
        bag = {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Poké Ball": 5, "Premier Ball": 1, "Great Ball": 1,
               "Ultra Ball": 1}
        r = _phase(bag=bag, floor_env="1000", short={"Ultra Ball": 1})
        b = buys(r)
        return (len(b) == 1 and any(n == "Ultra Ball" for n, _q in b[0]) and any(n == "Hyper Potion" for n, _q in b[0])
                and r.memo == {BALL_KEY} and tags(r.emitted, B) == ["why=topoff-failed"]
                and tags(r.emitted, K) == ["why=kit"] and r.isolated), f"{b} {r.memo} {r.emitted}"

    def p5():   # a raising buy: both active keys, both failed lines, R18's keys untouched
        r = _phase(buy="raise")
        return (r.memo == {KIT_KEY, BALL_KEY} and tags(r.emitted, B) == ["why=topoff-failed"]
                and tags(r.emitted, K) == ["why=kit-failed"] and r.out == "done" and r.isolated), f"{r.memo} {r.emitted}"

    def p6():   # BALLRAISE fires with the balls on (both keys), never with the balls OFF
        a = _phase(raise_env="1")
        b = _phase(ball=None, raise_env="1")
        return (a.memo == {KIT_KEY, BALL_KEY} and buys(a) == [] and b.memo == set() and buys(b) == [HYPER1]), \
            f"{a.memo} {buys(a)} || {b.memo} {buys(b)}"

    def p7():   # a close mid-buy: both keys, topoff-closed + kit-closed, the close itself does not raise
        r = _phase(buy="forever", close_after=3)
        return (r.out == "CLOSED" and r.memo == {KIT_KEY, BALL_KEY} and tags(r.emitted, B) == ["why=topoff-closed"]
                and tags(r.emitted, K) == ["why=kit-closed"] and r.isolated), f"{r.out} {r.memo} {r.emitted}"

    def p8():
        try:
            _phase(buy="abort")
        except RuntimeError as error:
            return "ABORT" in str(error), f"re-raised {error!r}"
        return False, "swallowed the abort"

    def p9():   # a raise in the KIT's own read: only the kit key, then 9b's ball phase ONLY if the balls are on
        broken = RuntimeError("reserve read broken")
        a = _phase(money=67466 - 45300, held_raise=broken, floor_env="1000")
        b = _phase(ball=None, held_raise=broken, floor_env="1000")          # balls OFF: nothing bought, no balls key
        c = _phase(ball_blocked=True, held_raise=broken)                     # balls BLOCKED: nothing bought
        return (KIT_KEY in a.memo and BALL_KEY not in a.memo and tags(a.emitted, K) == ["why=kit-failed"]
                and any(n == "Ultra Ball" for x in buys(a) for n, _q in x)
                and buys(b) == [] and "balls" not in b.report and b.memo == {KIT_KEY}
                and buys(c) == [] and c.memo == {KIT_KEY}), f"{a.memo} {buys(a)} || {buys(b)} {b.memo} || {buys(c)}"

    def p10():  # a 'kit only' visit whose counter finds no kit to buy: the kit key alone is memoised as wasted
        r = _phase(ball=None, early="kit only", sold=["Ultra Ball", "Revive"])
        return (r.memo == {KIT_KEY} and buys(r) == [] and tags(r.emitted, K) == ["why=kit-none"]
                and "(memoised)" in r.emitted[-1]), f"{r.memo} {r.emitted}"

    def p11():  # S-BOTHKIT's counter: the split was empty, so the ball set is NOT wasted (no ball key)
        r = _phase(early="kit only", kit_extra={"split_balls": []})
        return (buys(r) == [HYPER1] and BALL_KEY not in r.memo and r.memo == set()), f"{r.memo} {buys(r)}"

    def p12():  # the ball flag OFF: no `balls` key created, no ball line
        r = _phase(ball=None)
        return ("balls" not in r.report and tags(r.emitted, B) == [] and buys(r) == [HYPER1] and r.isolated), \
            f"{sorted(r.report)} {r.emitted}"

    def p13():  # the live floor lever reaches the counter: floor 30000 buys nothing
        r = _phase(floor_env="30000")
        return (buys(r) == [] and tags(r.emitted, K) == ["why=kit-none"] and r.memo == set()), f"{buys(r)} {r.emitted}"

    def p14():  # the balls BLOCKED (their forecast failed or a memo hit): no ball line, the ball dict untouched
        r = _phase(ball_blocked=True)
        return (tags(r.emitted, B) == [] and buys(r) == [HYPER1] and r.memo == set()
                and r.report["balls"] == {"mode": "1", "walk": True, "blocked": True,
                                          "forecast": [("Ultra Ball", 5)]}), f"{r.report['balls']} {r.emitted}"

    # --- added after the ADVERSARIAL MUTANT PASS (its MB, MC, ME, MF, MG, MZ, MH, MI and PD1); expectations from E5
    RICH_BAG = {"Hyper Potion": 34, "Full Heal": 10, "Revive": 3}           # a converged kit: nothing to buy
    QUIET_KIT = {"walk": False, "forecast": [], "split_balls": [("Ultra Ball", 1)]}

    def p15():  # E5: the counter plans the kit from the LIVE list (a Mart without the kit's items buys the balls)
        r = _phase(sold=["Ultra Ball", "Revive"], floor_env="1000")
        kl = [x for x in r.emitted if x.startswith(K)]
        # the review's DC2, the kit's half: the kit planned nothing, so ITS line reads the wallet unchanged
        return (buys(r) == [[("Ultra Ball", 5)]] and tags(r.emitted, B) == ["why=topoff"]
                and tags(r.emitted, K) == ["why=kit-none"] and " money=22166->22166 " in kl[0]
                and r.report["kit"]["money_after"] == 22166 and r.memo == set()), f"{buys(r)} {r.emitted} {r.memo}"

    def p16():  # E5: `observe` balls are OFF at the counter: the whole budget goes to the kit, no ball line
        r = _phase(ball="observe", bag={"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Poké Ball": 2},
                   floor_env="1000")
        return (buys(r) == [[("Hyper Potion", 4), ("Full Heal", 2)]] and tags(r.emitted, B) == []
                and r.memo == set()), f"{buys(r)} {r.emitted} {r.memo}"

    def p17():  # E5 [R15]: a raise with the balls OFF or observe memoises the KIT key alone, and logs no ball line
        a = _phase(ball=None, buy="raise")
        b = _phase(ball="observe", buy="raise")
        return (a.memo == {KIT_KEY} and tags(a.emitted, B) == [] and tags(a.emitted, K) == ["why=kit-failed"]
                and b.memo == {KIT_KEY} and tags(b.emitted, B) == []), f"{a.memo} {a.emitted} || {b.memo}"

    def p18():  # E5 [R15]: a close with the balls OFF: the kit key alone, no ball line
        r = _phase(ball=None, buy="forever", close_after=3)
        return (r.out == "CLOSED" and r.memo == {KIT_KEY} and tags(r.emitted, B) == []
                and tags(r.emitted, K) == ["why=kit-closed"]), f"{r.out} {r.memo} {r.emitted}"

    def p19():  # E5: a kit that did NOT walk is never 'wasted' on a 'balls only' visit (the balls buy their 1)
        r = _phase(early="balls only", kit_extra=dict(QUIET_KIT), bag=RICH_BAG)
        return (buys(r) == [[("Ultra Ball", 1)]] and r.memo == set() and tags(r.emitted, B) == ["why=topoff"]
                and tags(r.emitted, K) == ["why=kit-none"]), f"{buys(r)} {r.memo} {r.emitted}"

    def p20():  # E5 [R15]: 'balls only' IS top-off-only: its empty live ball plan memoises the BALL key (wasted)
        r = _phase(early="balls only", kit_extra=dict(QUIET_KIT), bag=RICH_BAG,
                   sold=["Hyper Potion", "Revive", "Full Heal"])
        bl = [x for x in r.emitted if x.startswith(B)]
        return (buys(r) == [] and r.memo == {BALL_KEY} and len(bl) == 1 and "(memoised)" in bl[0]),             f"{buys(r)} {r.memo} {r.emitted}"

    def p21():  # E5: a converged kit still lets the balls buy (one call for both sets, each judged on its own)
        r = _phase(bag=RICH_BAG, floor_env="1000", kit_extra={"walk": False, "forecast": []})
        return (buys(r) == [[("Ultra Ball", 5)]] and tags(r.emitted, B) == ["why=topoff"] and r.memo == set()),             f"{buys(r)} {r.memo} {r.emitted}"

    def p22():  # PD1: a kit-read raise on a 'balls and kit only' visit whose live ball plan is empty memoises BOTH
        r = _phase(early="balls and kit only", kit_extra={"split_balls": [("Ultra Ball", 1)]},
                   held_raise=RuntimeError("reserve read broken"), sold=["Hyper Potion", "Revive", "Full Heal"])
        return r.memo == {KIT_KEY, BALL_KEY} and buys(r) == [], f"{r.memo} {buys(r)} {r.emitted}"

    # --- added after the THREE-LENS REVIEW (its KT2-X2, KT2-X1, KT2-X5 and LI-2); expectations from E5, derived by hand
    def p23():  # KT2-X2: a SHORT basket (Hyper 20 of 30) leaves ₽12,000 more missing: the LIVE floor is ₽43,000
        r = _phase(early="partial", bag={"Hyper Potion": 20, "Full Heal": 8, "Revive": 3, "Potion": 1}, money=34166)
        return (buys(r) == [] and r.memo == set() and r.report["kit"]["live_floor"] == 43000
                and tags(r.emitted, K) == ["why=kit-none"] and tags(r.emitted, B) == ["why=topoff-none"]), \
            f"{buys(r)} {r.memo} {r.report['kit'].get('live_floor')} {r.emitted}"

    def p24():  # KT2-X1: PD1's negative twin: a kit-read raise on a BASKET visit wasted no walk: the kit key alone
        r = _phase(early="bought", kit_extra={"split_balls": [("Ultra Ball", 1)]},
                   held_raise=RuntimeError("reserve read broken"), sold=["Hyper Potion", "Revive", "Full Heal"])
        return (r.memo == {KIT_KEY} and buys(r) == [] and tags(r.emitted, B) == ["why=topoff-none"]
                and tags(r.emitted, K) == ["why=kit-failed"]), f"{r.memo} {buys(r)} {r.emitted}"

    def p25():  # KT2-X5: no ball on the LIVE list at spare 8 (<= the reserve): the kit keeps the budget
        r = _phase(early="kit only", sold=["Hyper Potion", "Revive", "Full Heal"],
                   bag={"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Potion": 1, "Poké Ball": 6})
        return (buys(r) == [HYPER1] and r.memo == set() and tags(r.emitted, K) == ["why=kit"]), \
            f"{buys(r)} {r.memo} {r.emitted}"

    def p26():  # LI-2: a spare that DROPPED to 10 on the crossing: the reserve Ultra takes the budget, the kit's wants
        # stand, so the kit is NOT memoised as wasted (the next forecast re-plans from the new spare)
        r = _phase(early="kit only", bag={"Hyper Potion": 30, "Full Heal": 8, "Revive": 3, "Potion": 1, "Poké Ball": 8})
        kl = [x for x in r.emitted if x.startswith(K)]
        return (buys(r) == [[("Ultra Ball", 1)]] and r.memo == set() and tags(r.emitted, K) == ["why=kit-none"]
                and tags(r.emitted, B) == ["why=topoff"] and "(memoised)" not in kl[0]), f"{buys(r)} {r.memo} {r.emitted}"

    for label, fn in (("P1 S-ON's counter: Hyper 1, before=30 (after the basket), a line per set, R18 untouched", p1),
                      ("P2 S-FH's counter: 1 Full Heal", p2),
                      ("P3 the kit short: only the kit key, kit-failed, the balls' own line", p3),
                      ("P4 both bought, the BALLS short: only the ball key, the kit's line ok", p4),
                      ("P5 a raising buy: both keys, both failed lines, R18's keys untouched", p5),
                      ("P6 BALLRAISE only with the balls on", p6),
                      ("P7 a close: both keys, both closed lines, no raise from close()", p7),
                      ("P8 an abort is re-raised", p8),
                      ("P9 a raise in the kit's OWN read: only the kit key; 9b's ball phase only with the balls ON",
                       p9),
                      ("P10 a 'kit only' visit that finds no kit: the kit key alone (wasted)", p10),
                      ("P11 S-BOTHKIT: the ball set is not 'wasted' (its effective walk was the empty split)", p11),
                      ("P12 the ball flag OFF: no balls key, no ball line", p12),
                      ("P13 the floor lever at the counter: nothing bought", p13),
                      ("P14 the balls blocked: the kit alone, no ball line, the ball dict untouched", p14),
                      ("P15 the counter plans the kit from the LIVE list", p15),
                      ("P16 observe balls are OFF at the counter: the kit takes the budget, no ball line", p16),
                      ("P17 a raise with the balls OFF/observe: the kit key alone, no ball line", p17),
                      ("P18 a close with the balls OFF: the kit key alone, no ball line", p18),
                      ("P19 a kit that did not walk is never 'wasted'", p19),
                      ("P20 'balls only' is top-off-only: an empty live ball plan memoises the ball key", p20),
                      ("P21 a converged kit still lets the balls buy", p21),
                      ("P22 PD1: a kit-read raise + an empty ball plan on 'balls and kit only' memoises both", p22),
                      ("P23 a SHORT basket: the live floor (₽43,000) is not the forecast's, nothing bought", p23),
                      ("P24 PD1's twin: a kit-read raise on a BASKET visit memoises the kit key alone", p24),
                      ("P25 no ball on the live list at spare 8: the kit keeps the budget, nothing memoised", p25),
                      ("P26 a spare drop on the crossing: the reserve Ultra, and the kit NOT memoised as wasted", p26)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------ A rows (AST)
_TREES: dict = {}


def _parsed(src):
    """`ast.parse`, once per distinct source text (every mutant that leaves a file alone reuses its tree)."""
    if src not in _TREES:
        _TREES[src] = ast.parse(src)
    return _TREES[src]


def _class_source(src, cls):
    """The text of TOP-LEVEL class `cls`: from its `class` line to the next column-0 statement (a column-0 comment does
    not end it). Raises if the class is missing, so a row can never pass on an empty tree."""
    import re

    start = src.index(f"\nclass {cls}(") + 1
    nxt = re.compile(r"^(?=[^\s#])", re.M).search(src, src.index("\n", start) + 1)
    return src[start:nxt.start() if nxt else len(src)]


def a_rows(tsrc, lrsrc, hsrc, tag=""):
    reds: list = []

    def fn(src, name, cls=None):
        if cls:
            # ⛔ Parse the CLASS, not the file: `ast.parse` of the 30,000-line harness took ~5 s, and A4 and A5 did it
            # for every mutant, so the gate took 15 min against run_gates' 300 s FAST timeout (08, 2026-09-30).
            src = _class_source(src, cls)
        tree = _parsed(src)
        if cls:
            tree = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
        return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)

    def calls(node, name):
        return [c for c in ast.walk(node) if isinstance(c, ast.Call)
                and (getattr(c.func, "id", None) == name or getattr(c.func, "attr", None) == name)]

    def a1():   # `_shop`: topoff_only keeps BB9B-1's precedence, and the kit dispatch returns BEFORE 9b's
        node = fn(lrsrc, "_shop")
        topo = [n for n in ast.walk(node) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "topoff_only"]
        disp = [n for n in ast.walk(node) if isinstance(n, ast.If) and ast.unparse(n.test) == "kit_buys_here(kit)"]
        ball = [n for n in ast.walk(node) if isinstance(n, ast.If)
                and ast.unparse(n.test) == "balls.get('mode') == '1' and (not balls.get('blocked'))"]
        ok = (len(topo) == 1 and ast.unparse(topo[0].value) == "ball_only or (not plan and bool(kit.get('walk')))"
              and len(disp) == 1 and len(ball) == 1 and disp[0].lineno < ball[0].lineno
              and any(isinstance(s, ast.Return) for s in disp[0].body)
              and calls(disp[0], "sootopolis_topoff_phase"))
        return ok, f"topo={[ast.unparse(x.value) for x in topo]} disp={len(disp)} ball={len(ball)}"

    def a2():   # the kit forecast is called after 9b's, before the early return
        node = fn(lrsrc, "_stock_basket_early")
        ball_fc = calls(node, "sootopolis_ball_forecast")
        kit_fc = calls(node, "sootopolis_kit_forecast")
        early = [n for n in ast.walk(node) if isinstance(n, ast.If)
                 and ast.unparse(n.test) == "not plan and (not ball_walk) and (not kit_walk)"]
        ok = (len(kit_fc) == 1 and [ast.unparse(a) for a in kit_fc[0].args] == ["plan", "money", "prices", "balls"]
              and len(ball_fc) == 1 and len(early) == 1 and ball_fc[0].lineno < kit_fc[0].lineno < early[0].lineno)
        return ok, f"kit={[ast.unparse(c) for c in kit_fc]} early={len(early)}"

    def a3():   # no yield in the top-off phase's GeneratorExit handler
        node = fn(tsrc, "sootopolis_topoff_phase")
        handlers = [h for n in ast.walk(node) if isinstance(n, ast.Try) for h in n.handlers
                    if isinstance(h.type, ast.Name) and h.type.id == "GeneratorExit"]
        yields = [y for h in handlers for y in ast.walk(h) if isinstance(y, (ast.Yield, ast.YieldFrom))]
        return len(handlers) == 1 and not yields, f"handlers={len(handlers)} yields={len(yields)}"

    def a4():   # the driver: its kit forecast never calls production's held view / reserve; the memo is set; kit_end once
        run = fn(hsrc, "run", cls="EarlyBasketMode")
        kf = next(n for n in ast.walk(run) if isinstance(n, ast.FunctionDef) and n.name == "kit_forecast")
        forbidden = calls(kf, "_kit_held") + calls(kf, "reserved_quantities")
        memo = [n for n in ast.walk(run) if isinstance(n, ast.Assign)
                and ast.unparse(n.targets[0]) == "self._ball_topoff_failed" and ast.unparse(n.value) == "set()"]
        kit_end = [n for n in ast.walk(run) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "R['kit_end']"]
        uses = calls(run, "kit_action")
        return (not forbidden and len(memo) == 1 and len(kit_end) == 1 and len(uses) == 1), \
            f"forbidden={len(forbidden)} memo={len(memo)} kit_end={len(kit_end)} kit_action={len(uses)}"

    def a5():   # the driver's lever rule and grade, pinned (the pass's DA-DF)
        run = fn(hsrc, "run", cls="EarlyBasketMode")
        assigns = {}
        for n in ast.walk(run):
            if isinstance(n, ast.Assign) and len(n.targets) == 1:
                assigns.setdefault(ast.unparse(n.targets[0]), []).append(n)
        def one(target):
            got = assigns.get(target, [])
            return ast.unparse(got[0].value) if len(got) == 1 else None
        entries = {}
        for d in ast.walk(run):
            if isinstance(d, ast.Dict):
                for k, v in zip(d.keys, d.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        entries.setdefault(k.value, []).append(v)
        pkf = entries.get("production_kit_forecast", [])
        memo_clean = entries.get("memo_clean", [])
        restore = [c for c in ast.walk(run) if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "load_save_state"]
        kit_end = assigns.get("R['kit_end']", [])
        checks = {
            "kfc models no RAWBAG": "kit_forecast(False)" in (one("kfc") or ""),
            "the raw view is printed": (one("R['kit_forecast_raw']") or "").startswith("kit_forecast(True)"),
            "blocked models RESERVE_FAULT_RAISE": "POKEBOT_RESERVE_FAULT_RAISE" in (one("R['kit_blocked']") or ""),
            "kit_buys": one("R['kit_buys']") == "R['kit_mode'] == '1' and kfc is not None",
            "kit_expected": one("R['kit_expected']") == "R['kit_forecast'] if R['kit_buys'] and (not R['kit_ballraise']) else []",
            "production_kit_forecast is the call": (len(pkf) == 1 and isinstance(pkf[0], ast.Call)
                                                    and getattr(pkf[0].func, "id", None) == "production_kit_forecast_ok"),
            "memo_clean": len(memo_clean) == 1 and ast.unparse(memo_clean[0]) == "not R.get('memo_end')",
            "kit_end before the restore": (len(kit_end) == 1 and len(restore) == 1
                                           and kit_end[0].lineno < restore[0].lineno),
        }
        # --- the THREE-LENS REVIEW: DC1 (the lever rule models BALLRAISE; `kit_as_forecast` everywhere but a budget
        # close; a kit-aware ballfail), KT2-D1 (the kit's attribution) and KT2-D2 (the outcome label is the driver's)
        def body_of(test):
            got = [n for n in ast.walk(run) if isinstance(n, ast.If) and ast.unparse(n.test) == test]
            return got[0].body if len(got) == 1 else []

        def texts(key):
            return [ast.unparse(v) for v in entries.get(key, [])]

        kaf = assigns.get("conj['kit_as_forecast']", [])
        both = assigns.get("conj['both_keys_memoised']", [])
        attributed = assigns.get("conj['kit_attributed']", [])
        checks.update({
            "kit_ballraise models BALLRAISE": one("R['kit_ballraise']") == (
                "R['kit_buys'] and R['bb_mode'] == '1' and (_os.environ.get('POKEBOT_R23_FAULT_BALLRAISE') == '1')"),
            "kit_walk is the kit's own walk": one("R['kit_walk']") == "R['kit_buys'] and bool(R['kit_forecast'])",
            "kit_as_forecast only outside a budget close": (
                len(kaf) == 1 and kaf[0] in body_of("EXPECT != 'budget'") and not entries.get("kit_as_forecast")
                and ast.unparse(kaf[0].value) == "kact['kit'] == kact['kit_expected']"),
            "ballfail with the kit: both keys": (
                len(both) == 1 and both[0] in body_of("R.get('kit_ballraise')")
                and ast.unparse(both[0].value)
                == "R.get('memo_end') == sorted([BB.sootopolis_key(), BB.sootopolis_kit_key()])"),
            "the kit's attribution (buy branch and kit branch)": (
                len(attributed) == 1 and ast.unparse(attributed[0].value) == "kit_attributed(rep, kact['kit_expected'])"
                and texts("kit_attributed") == ["kit_attributed(rep, kact['kit_expected'])"]),
            "the outcome label is the driver's": (
                one("topoff_label") == "TOPOFF_ONLY_OUTCOMES[2 if ball_walk and kit_walk else 1 if kit_walk else 0]"
                and one("(ball_walk, kit_walk)") == "(bool(R.get('balls_expected')), bool(R.get('kit_walk')))"
                and texts("topoff_only_visit")
                == ["rep.get('early_basket') == topoff_label and (not plan) and (order == [AT_MART])"]
                and texts("basket_outcome_kept") == ["rep.get('early_basket') == ('bought' if basket_visit else topoff_label)"]),
        })
        return all(checks.values()), str({k: v for k, v in checks.items() if not v})

    for label, f in (("A1 (AST) _shop: topoff_only keeps BB9B-1's precedence; the kit dispatch returns BEFORE 9b's", a1),
                     ("A2 (AST) the kit forecast is called (plan, money, prices, balls) after 9b's, before the return",
                      a2),
                     ("A3 (AST) no yield in the top-off phase's GeneratorExit handler", a3),
                     ("A4 (AST) the driver's kit forecast never calls _kit_held/reserved_quantities; memo set; kit_end",
                      a4),
                     ("A5 (AST) the driver's lever rule and kit grade are pinned (RAWBAG never modelled; the kit reads "
                      "before the restore)", a5)):
        row(label, f, tag, reds)
    return reds


def all_rows(tsrc, lrsrc, hsrc, tag):
    return set(h_rows(tag) + g_rows(tag) + o_rows(tag) + s_rows(tag) + p_rows(tag) + a_rows(tsrc, lrsrc, hsrc, tag))


#: The mutants. Each set was derived row by row from the DESIGN and written BEFORE the gate's first mutant run.
CASES: list = [
    # --- stock_topoff: the held view, the dispatch predicate, the constants
    ("T1 the held view forgets the basket plan -> H1 O8", T_PATH,
     "    for item, count in basket_plan:\n        projected[item] = projected.get(item, 0) + count\n", "",
     {"H1", "O8"}),
    ("T2 the held view can go negative -> H1", T_PATH,
     "    return {name: max(0, projected.get(name, 0) - reserved.get(name, 0)) for name in KIT_NAMES}\n",
     "    return {name: projected.get(name, 0) - reserved.get(name, 0) for name in KIT_NAMES}\n", {"H1"}),
    ("T3 a SKIPPED kit counts as buying -> H2 S10", T_PATH,
     'and not kit.get("skip") and not kit.get("blocked")', 'and not kit.get("blocked")', {"H2", "S10"}),
    ("T4 a BLOCKED kit counts as buying -> H2 S7 S10", T_PATH,
     'and not kit.get("skip") and not kit.get("blocked")', 'and not kit.get("skip")', {"H2", "S7", "S10"}),
    ("T5 OFF is not OFF (the forecast runs with the kit unset) -> O1 S1", T_PATH,
     '    if mode == "":                           # OFF', '    if mode == "0":                          # OFF',
     {"O1", "S1"}),
    ("KEY the kit's memo key is the BALL key -> H3 O5 O6 S7 P3 P5 P6 P7 P9 P10 P17 P18 P22 P24", T_PATH,
     '    return f"{sootopolis_key()}:kit"', "    return sootopolis_key()",
     {"H3", "O5", "O6", "S7", "P3", "P5", "P6", "P7", "P9", "P10", "P17", "P18", "P22", "P24"}),
    ("CONST Max Potion in the static kit list -> H3", T_PATH,
     'SOOTOPOLIS_STATIC_KIT_SOLD = ("Hyper Potion", "Full Heal")',
     'SOOTOPOLIS_STATIC_KIT_SOLD = ("Hyper Potion", "Max Potion", "Full Heal")', {"H3"}),
    # --- stock_topoff: the forecast
    ("T6 the rejected design: 9b's ball forecast REBOUND to the split -> S3 S9", T_PATH,
     '    out.update(forecast=plan["kit"], split_balls=',
     '    if ball_on:\n        balls["forecast"] = plan["ball_lines"]\n    out.update(forecast=plan["kit"], split_balls=',
     {"S3", "S9"}),
    ("T8 the forecast always runs the ball phases (a reserve phase with the balls OFF) -> O10", T_PATH,
     "                          buy_balls=ball_on)\n    except Exception as error:  # noqa: BLE001 - the kit's forecast",
     "                          buy_balls=True)\n    except Exception as error:  # noqa: BLE001 - the kit's forecast",
     {"O10"}),
    ("T9 a kit-forecast raise is not memoised -> O6", T_PATH,
     "        reraise_if_aborting(error)\n        _memo_add_kit()\n        out.update(blocked=True",
     "        reraise_if_aborting(error)\n        out.update(blocked=True", {"O6"}),
    ("T10 a kit-forecast raise memoises the BALL key -> O6", T_PATH,
     "        reraise_if_aborting(error)\n        _memo_add_kit()\n        out.update(blocked=True",
     "        reraise_if_aborting(error)\n        _memo_add()\n        out.update(blocked=True", {"O6"}),
    ("T11 a kit-forecast raise blocks the balls too -> O6", T_PATH,
     "        out.update(blocked=True, reason=f\"the kit's forecast raised",
     "        if balls:\n            balls[\"blocked\"] = True\n"
     "        out.update(blocked=True, reason=f\"the kit's forecast raised", {"O6"}),
    ("T12 the D2 skip removed from the forecast -> O4 S6", T_PATH,
     "    skip = _kit_skip_reason(mode)\n", "    skip = None\n", {"O4", "S6"}),
    ("T13 the forecast's memo check reads the BALL key -> O5 S7", T_PATH,
     "    if failed is not None and sootopolis_kit_key() in failed:",
     "    if failed is not None and sootopolis_key() in failed:", {"O5", "S7"}),
    ("T14 observe walks -> O2 S5", T_PATH,
     '               walk=mode == "1" and bool(plan["kit"]))', '               walk=bool(plan["kit"]))', {"O2", "S5"}),
    ("T15 observe logs the kit-forecast tag -> O2", T_PATH,
     '    _emit(kit_log_line("kit-observe" if mode == "observe" else "kit-forecast",',
     '    _emit(kit_log_line("kit-forecast",', {"O2"}),
    ("T16 the forecast ignores RAWBAG -> O8", T_PATH,
     '        rawbag = os.environ.get("POKEBOT_R26_FAULT_RAWBAG") == "1"\n', "        rawbag = False\n", {"O8"}),
    ("T17 the forecast ignores the floor lever -> O9 O13", T_PATH,
     "            fault_floor=lever)", "            fault_floor=None)", {"O9", "O13"}),
    # --- stock_topoff: the counter phase
    ("T19 'wasted balls' keyed on 9b's walk, not the split -> P11 P25", T_PATH,
     '        wasted_balls = topoff_only and ball_on and bool(kit.get("split_balls")) and not ball_lines',
     '        wasted_balls = topoff_only and ball_on and bool((report.get("balls") or {}).get("walk")) '
     'and not ball_lines', {"P11", "P25"}),
    ("T20 'wasted kit' on a basket visit too -> P13 P15 P23", T_PATH,
     '        wasted_kit = topoff_only and bool(kit.get("walk")) and not kit_lines',
     '        wasted_kit = bool(kit.get("walk")) and not kit_lines', {"P13", "P15", "P23"}),
    ("T21 a kit shortfall memoises the balls too (10a's R1 again) -> P3", T_PATH,
     '        if not kit["ok"]:\n            _memo_add_kit()\n',
     '        if not kit["ok"]:\n            _memo_add_kit()\n            _memo_add()\n', {"P3"}),
    ("T22 the counter ignores the balls' block -> P9 P14", T_PATH,
     '    ball_on = (report.get("balls") or {}).get("mode") == "1" and not (report.get("balls") or {}).get("blocked")',
     '    ball_on = (report.get("balls") or {}).get("mode") == "1"', {"P9", "P14"}),
    ("T23 the counter creates a balls key with the ball flag OFF -> P9 P12", T_PATH,
     '    balls = report["balls"] if ball_on else {}          # ⛔ never create a `balls` key with the ball flag off',
     '    balls = report.setdefault("balls", {})', {"P9", "P12"}),
    ("T24 a close memoises only the kit -> P7", T_PATH,
     '            failed.update(active)\n        kit["phase"] = "closed"',
     '            failed.add(sootopolis_kit_key())\n        kit["phase"] = "closed"', {"P7"}),
    ("T25 a raise memoises only the kit -> P5 P6", T_PATH,
     '            failed.update(active)\n        kit.update(phase="failed", error=repr(error))',
     '            failed.add(sootopolis_kit_key())\n        kit.update(phase="failed", error=repr(error))', {"P5", "P6"}),
    ("T26 BALLRAISE fires with the balls OFF -> P6", T_PATH,
     '        if ball_on and os.environ.get("POKEBOT_R23_FAULT_BALLRAISE") == "1":',
     '        if os.environ.get("POKEBOT_R23_FAULT_BALLRAISE") == "1":', {"P6"}),
    ("T27 a kit-read raise drops the balls (no fallback to 9b's phase) -> P9 P22 P24", T_PATH,
     "        if ball_on:\n            yield from sootopolis_ball_phase(report)\n            # 9b's phase memoises",
     "        if False:\n            yield from sootopolis_ball_phase(report)\n            # 9b's phase memoises",
     {"P9", "P22", "P24"}),
    ("T28 a kit-read raise memoises the balls too -> P9 P24", T_PATH,
     '        reraise_if_aborting(error)\n        _memo_add_kit()\n        kit.update(phase="failed", error=repr(error))',
     '        reraise_if_aborting(error)\n        _memo_add_kit()\n        _memo_add()\n'
     '        kit.update(phase="failed", error=repr(error))', {"P9", "P24"}),
    ("T29 the kit verified by the COUNT, not the delta -> P1 P2 P4 P6 P11 P14 P16 P25", T_PATH,
     '        kit["got"] = {name: after[name] - before[name] for name in kit_want}',
     '        kit["got"] = {name: after[name] for name in kit_want}', {"P1", "P2", "P4", "P6", "P11", "P14", "P16", "P25"}),
    ("T30 the counter buys the STALE forecast, not the live plan -> P1 P2 P6 P11 P12 P13 P14 P16 P23 P25 P26", T_PATH,
     '        kit_lines = [(n, q) for n, q in plan["kit"] if n in sold]',
     '        kit_lines = [(n, q) for n, q in kit.get("forecast", []) if n in sold]',
     {"P1", "P2", "P6", "P11", "P12", "P13", "P14", "P16", "P23", "P25", "P26"}),
    # --- league_reserve
    ("L1 the precedence slip: a kit walk swallows BB9B-1's raise -> S8 A1", LR_PATH,
     '    topoff_only = ball_only or (not plan and bool(kit.get("walk")))',
     '    topoff_only = ball_only or bool(kit.get("walk"))', {"S8", "A1"}),
    ("L2 the kit dispatch falls through to 9b's phase -> S10 A1", LR_PATH,
     "        yield from sootopolis_topoff_phase(report)\n        return\n",
     "        yield from sootopolis_topoff_phase(report)\n", {"S10", "A1"}),
    ("L3 any kit dict dispatches the top-off phase -> S10 A1", LR_PATH,
     "    if kit_buys_here(kit):\n", "    if kit:\n", {"S10", "A1"}),
    ("L4 the effective ball walk is always 9b's -> S3", LR_PATH,
     '    ball_walk = bool(kit.get("split_balls")) if kit_buys_here(kit) else bool(balls and balls.get("walk"))',
     '    ball_walk = bool(balls and balls.get("walk"))', {"S3"}),
    ("L5 the early return ignores the kit walk -> S2 S3 A2", LR_PATH,
     "    if not plan and not ball_walk and not kit_walk:", "    if not plan and not ball_walk:", {"S2", "S3", "A2"}),
    ("L6 the kit forecast is not stored in the report -> S3 S4 S5 S6 S7 S9 S13", LR_PATH,
     '    if kit is not None:\n        report["kit"] = kit\n', "", {"S3", "S4", "S5", "S6", "S7", "S9", "S13"}),
    ("L7 a kit walk is labelled 'balls only' -> S2 S3", LR_PATH,
     '        report["early_basket"] = TOPOFF_ONLY_OUTCOMES[2 if ball_walk and kit_walk else (1 if kit_walk else 0)]',
     '        report["early_basket"] = TOPOFF_ONLY_OUTCOMES[2 if ball_walk and kit_walk else 0]', {"S2", "S3"}),
    # --- kit_grade
    ("KG1 the kit part is not net of the basket -> G1 G2 G7", KG_PATH,
     "    kit = {n: delta.get(n, 0) - basket.get(n, 0) for n in sorted(set(delta) | set(basket))}",
     "    kit = {n: delta.get(n, 0) for n in sorted(set(delta) | set(basket))}", {"G1", "G2", "G7"}),
    ("KG2 a short basket reads as a negative kit -> G2 G8", KG_PATH,
     "    kit = {n: q for n, q in kit.items() if q > 0}", "    kit = {n: q for n, q in kit.items() if q}", {"G2", "G8"}),
    ("KG3 the expected total is not summed per name -> G1 G6", KG_PATH,
     "        expected[name] = expected.get(name, 0) + qty", "        expected[name] = qty", {"G1", "G6"}),
    ("KG4 the forecast check ignores the split -> G3", KG_PATH,
     ' and kit.get("split_balls") == driver_split', "", {"G3"}),
    ("KG5 an unmade forecast passes with a kit key -> G3", KG_PATH,
     '    return "kit" not in report', "    return True", {"G3"}),
    ("KG6 the attribution ignores production's ok -> G4", KG_PATH,
     ' and kit.get("ok") is True', "", {"G4"}),
    ("KG7 the kit's before is not checked against the basket -> G5", KG_PATH,
     "before[n] == meds_start.get(n, 0) + basket.get(n, 0)", "before[n] == meds_start.get(n, 0)", {"G5"}),
    # --- the driver
    ("D1 the driver's kit forecast calls production's held view -> A4", HARNESS,
     'held = BB.kit_held_after_basket(_stock_by_name(list(BB.KIT_NAMES)), R["plan_predicted"],\n'
     '                                            dict(LEAGUE_BASKET), rawbag)', "held = BB._kit_held()", {"A4"}),
    ("D2 the driver forgets the memo -> A4", HARNESS, "        self._ball_topoff_failed = set()\n", "", {"A4"}),
    # --- the ADVERSARIAL MUTANT PASS on this gate (2026-09-30): 23 mutants no gate caught, and PD1. Every set below
    # was written BEFORE the gate's run 2.
    ("MA the forecast ignores the balls' block -> O10 S12", T_PATH,
     '    ball_on = bool(balls) and balls.get("mode") == "1" and not balls.get("blocked")',
     '    ball_on = bool(balls) and balls.get("mode") == "1"', {"O10", "S12"}),
    ("MC2 the forecast counts observe balls as on -> S11", T_PATH,
     '    ball_on = bool(balls) and balls.get("mode") == "1" and not balls.get("blocked")',
     '    ball_on = bool(balls) and balls.get("mode") in ("observe", "1") and not balls.get("blocked")', {"S11"}),
    ("ML both walks labelled 'kit only' -> S13", LR_PATH,
     '        report["early_basket"] = TOPOFF_ONLY_OUTCOMES[2 if ball_walk and kit_walk else (1 if kit_walk else 0)]',
     '        report["early_basket"] = TOPOFF_ONLY_OUTCOMES[1 if kit_walk else 0]', {"S13"}),
    ("MB the counter plans the kit from the STATIC list -> P15", T_PATH,
     "        wants = kit_wants(sold, held, kit_hp_target())",
     "        wants = kit_wants(SOOTOPOLIS_STATIC_KIT_SOLD, held, kit_hp_target())", {"P15"}),
    ("MC the counter counts observe balls as on -> P16 P17", T_PATH,
     '    ball_on = (report.get("balls") or {}).get("mode") == "1" and not (report.get("balls") or {}).get("blocked")',
     '    ball_on = (report.get("balls") or {}).get("mode") in ("observe", "1") and not '
     '(report.get("balls") or {}).get("blocked")', {"P16", "P17"}),
    ("MD1 the kit-read fallback runs 9b's phase with the balls OFF or blocked -> P9", T_PATH,
     "        if ball_on:\n            yield from sootopolis_ball_phase(report)\n            # 9b's phase memoises",
     "        if True:\n            yield from sootopolis_ball_phase(report)\n            # 9b's phase memoises", {"P9"}),
    ("MD2 the kit-read fallback forgets the balls' block -> P9", T_PATH,
     "        if ball_on:\n            yield from sootopolis_ball_phase(report)\n            # 9b's phase memoises",
     '        if (report.get("balls") or {}).get("mode") == "1":\n            yield from sootopolis_ball_phase(report)\n'
     "            # 9b's phase memoises", {"P9"}),
    ("PDF the PD1 fix removed (a wasted 'balls and kit only' ball walk after a kit-read raise) -> P22", T_PATH,
     '            if (report.get("early_basket") == TOPOFF_ONLY_OUTCOMES[2] and report["balls"].get("phase") == "none"',
     '            if (False and report["balls"].get("phase") == "none"', {"P22"}),
    ("ME the active keys always include the ball key -> P17 P18", T_PATH,
     "    active = [sootopolis_kit_key()] + ([sootopolis_key()] if ball_on else [])",
     "    active = [sootopolis_kit_key(), sootopolis_key()]", {"P17", "P18"}),
    ("MF 'wasted kit' ignores the kit's own walk -> P19 P20", T_PATH,
     '        wasted_kit = topoff_only and bool(kit.get("walk")) and not kit_lines',
     "        wasted_kit = topoff_only and not kit_lines", {"P19", "P20"}),
    ("MG 'top-off only' excludes 'balls only' -> P20", T_PATH,
     '        topoff_only = report.get("early_basket") in TOPOFF_ONLY_OUTCOMES\n',
     '        topoff_only = report.get("early_basket") in TOPOFF_ONLY_OUTCOMES[1:]\n', {"P20"}),
    ("MZ the counter buys only when the kit has lines -> P15 P19 P21 P26", T_PATH,
     "        if ball_lines or kit_lines:\n", "        if kit_lines:\n", {"P15", "P19", "P21", "P26"}),
    ("MH a raise logs a ball line with the balls OFF -> P17", T_PATH,
     '        if ball_on:\n            balls.update(phase="failed", error=repr(error))',
     '        if balls is not None:\n            balls.update(phase="failed", error=repr(error))', {"P17"}),
    ("MI a close logs a ball line with the balls OFF -> P18", T_PATH,
     '        if ball_on:\n            balls.update(phase="closed")',
     '        if balls is not None:\n            balls.update(phase="closed")', {"P18"}),
    ("MK the kit suffix keyed on 'balls' (the telemetry line vanishes) -> S14", LR_PATH,
     '''+ (f" kit={_kit_summary(report['kit'])}" if "kit" in report else ""),''',
     '''+ (f" kit={_kit_summary(report['kit'])}" if "balls" in report else ""),''', {"S14"}),
    ("MJ the kit suffix always present (a kit-OFF line is no longer 9b's) -> S14", LR_PATH,
     '''+ (f" kit={_kit_summary(report['kit'])}" if "kit" in report else ""),''',
     '''+ f" kit={_kit_summary(report.get('kit') or {})}",''', {"S14"}),
    ("MM the kit priced from the EXPECTED kit -> G7", KG_PATH,
     '"kit_cost": sum(prices[n] * q for n, q in kit.items())}',
     '"kit_cost": sum(prices[n] * q for n, q in kit_expected.items())}', {"G7"}),
    ("MN the delta drops consumed stacks -> G8", KG_PATH,
     "    delta = {n: q for n, q in delta.items() if q}", "    delta = {n: q for n, q in delta.items() if q > 0}",
     {"G8"}),
    ("MN2 the kit's before checked with any(), not all() -> G5", KG_PATH,
     "return bool(before) and all(before[n] == ", "return bool(before) and any(before[n] == ", {"G5"}),
    ("DA the driver models RAWBAG -> A5", HARNESS,
     "            kfc = (kit_forecast(False) if",
     '            kfc = (kit_forecast(_os.environ.get("POKEBOT_R26_FAULT_RAWBAG") == "1") if', {"A5"}),
    ("DB production_kit_forecast hollowed -> A5", HARNESS,
     '"production_kit_forecast": production_kit_forecast_ok(', '"production_kit_forecast": True or production_kit_forecast_ok(',
     {"A5"}),
    ("DC memo_clean hollowed -> A5", HARNESS,
     '"memo_clean": not R.get("memo_end"),', '"memo_clean": True,', {"A5"}),
    ("DD the driver ignores RESERVE_FAULT_RAISE -> A5", HARNESS,
     'and _os.environ.get("POKEBOT_RESERVE_FAULT_RAISE") == "1")', "and False)", {"A5"}),
    ("DE observe expects a purchase -> A5", HARNESS,
     'R["kit_expected"] = R["kit_forecast"] if R["kit_buys"] and not R["kit_ballraise"] else []',
     'R["kit_expected"] = R["kit_forecast"] if R["kit_forecast_made"] and not R["kit_ballraise"] else []', {"A5"}),
    ("DF the kit's end read after the fixture restore -> A5", HARNESS,
     '                R["kit_end"] = _stock_by_name(MEDS)\n'
     '                R["memo_end"] = sorted(getattr(self, "_ball_topoff_failed", set()))\n'
     '            except Exception as read_error:  # noqa: BLE001 - an unreadable end state FAILS the grade\n'
     '                reraise_if_aborting(read_error)\n'
     '                R["read_error"] = f"<unreadable {type(read_error).__name__}: {read_error}>"\n'
     '            try:\n'
     '                if _fixture_bytes:\n'
     '                    context.emulator.load_save_state(_fixture_bytes)\n',
     '                R["memo_end"] = sorted(getattr(self, "_ball_topoff_failed", set()))\n'
     '            except Exception as read_error:  # noqa: BLE001 - an unreadable end state FAILS the grade\n'
     '                reraise_if_aborting(read_error)\n'
     '                R["read_error"] = f"<unreadable {type(read_error).__name__}: {read_error}>"\n'
     '            try:\n'
     '                if _fixture_bytes:\n'
     '                    context.emulator.load_save_state(_fixture_bytes)\n'
     '                    R["kit_end"] = _stock_by_name(MEDS)\n', {"A5"}),
    # --- the THREE-LENS REVIEW (2026-09-30): its confirmed gate misses (KT2-X1..X6, Z1, D1, D2) and the fixes to DC1,
    # DC2 and LI-2. Every set below was derived row by row from the design and written BEFORE the gate's run.
    ("X1 the PD1 fix without its outcome guard (a BASKET visit memoises the balls) -> P24", T_PATH,
     '            if (report.get("early_basket") == TOPOFF_ONLY_OUTCOMES[2] and report["balls"].get("phase") == "none"',
     '            if (report["balls"].get("phase") == "none"', {"P24"}),
    ("X2 the counter plans against the FORECAST's floor -> P23", T_PATH,
     '        floor_money = live["floor"] if lever is None else lever',
     '        floor_money = kit.get("floor", live["floor"]) if lever is None else lever', {"P23"}),
    ("X3 the counter re-uses the FORECAST's wants -> P15 P19 P20 P21", T_PATH,
     "        wants = kit_wants(sold, held, kit_hp_target())",
     '        wants = kit.get("wants") or kit_wants(sold, held, kit_hp_target())', {"P15", "P19", "P20", "P21"}),
    ("X4 the forecast's HP target is 1, not kit_hp_target() -> O13", T_PATH,
     "        wants = kit_wants(SOOTOPOLIS_STATIC_KIT_SOLD, held, kit_hp_target())",
     "        wants = kit_wants(SOOTOPOLIS_STATIC_KIT_SOLD, held, KIT_SPECIFIC_TARGET)", {"O13"}),
    ("X5 the counter picks its ball from the STATIC list -> P25", T_PATH,
     '        ball = (best_ball(sold, _allowed(), {name: live["price_of"](name) for name in sold if name in UNCONDITIONAL})',
     '        ball = (best_ball(SOOTOPOLIS_STATIC_SOLD, _allowed(), {name: live["price_of"](name) '
     'for name in SOOTOPOLIS_STATIC_SOLD})', {"P25"}),
    ("X6 the counter plans against the FORECAST's wallet -> P2", T_PATH,
     '        plan = visit_plan(spare=live["spare"], money=live["money"], ball=ball,',
     '        plan = visit_plan(spare=live["spare"], money=kit.get("money_after_basket", live["money"]), ball=ball,',
     {"P2"}),
    ("WASTE LI-2 reverted: a kit whose wants stand is memoised when a spare drop took its budget -> P26", T_PATH,
     " and not kit_lines and (not wants or not ball_lines)", " and not kit_lines", {"P26"}),
    ("MONEYB DC2 reverted for the balls: a no-ball line carries the kit's cost -> P1", T_PATH,
     '        ball_money_after = money_after if ball_lines else live["money"]', "        ball_money_after = money_after",
     {"P1"}),
    ("MONEYK DC2 reverted for the kit: a no-kit line carries the balls' cost -> P15", T_PATH,
     '        kit_money_after = money_after if kit_lines else live["money"]', "        kit_money_after = money_after",
     {"P15"}),
    ("Z1 production_kit_forecast_ok normalises a missing forecast to [] -> G3", KG_PATH,
     '    return kit.get("forecast") == driver_kit and kit.get("split_balls") == driver_split',
     '    return (kit.get("forecast") or []) == (driver_kit or []) and (kit.get("split_balls") or []) == '
     '(driver_split or [])', {"G3"}),
    ("DG kit_as_forecast graded under a budget close too -> A5", HARNESS,
     '        if EXPECT != "budget":\n            # step 10b: no medicine moved beyond the basket plan',
     '        if True:\n            # step 10b: no medicine moved beyond the basket plan', {"A5"}),
    ("DH the driver ignores BALLRAISE for the kit -> A5", HARNESS,
     '                                  and _os.environ.get("POKEBOT_R23_FAULT_BALLRAISE") == "1")',
     "                                  and False)", {"A5"}),
    ("DJ ballfail's both-keys check hollowed -> A5", HARNESS,
     '                conj["both_keys_memoised"] = R.get("memo_end") == sorted([BB.sootopolis_key(), '
     'BB.sootopolis_kit_key()])',
     '                conj["both_keys_memoised"] = True', {"A5"}),
    ("DK1 the buy branch's kit_attributed hollowed -> A5", HARNESS,
     '                conj["kit_attributed"] = kit_attributed(rep, kact["kit_expected"])',
     '                conj["kit_attributed"] = True', {"A5"}),
    ("DK1b the kit branch's kit_attributed hollowed -> A5", HARNESS,
     '                "kit_attributed": kit_attributed(rep, kact["kit_expected"]),',
     '                "kit_attributed": True,', {"A5"}),
    ("DK2 the outcome label taken from production -> A5", HARNESS,
     "        topoff_label = TOPOFF_ONLY_OUTCOMES[2 if ball_walk and kit_walk else (1 if kit_walk else 0)]",
     '        topoff_label = rep.get("early_basket")', {"A5"}),
    ("DW the kit's walk read from the expected PURCHASE (BALLRAISE mislabels) -> A5", HARNESS,
     '            R["kit_walk"] = R["kit_buys"] and bool(R["kit_forecast"])',
     '            R["kit_walk"] = bool(R.get("kit_expected"))', {"A5"}),
    # --- comment-only edits: NOTHING red
    ("N1 a comment in stock_topoff naming the kit's code turns NOTHING red", T_PATH,
     "#: The kit items the Sootopolis Mart sells",
     "# (edited) kit_buys_here(kit) and sootopolis_topoff_phase(report), a comment only\n"
     "#: The kit items the Sootopolis Mart sells", set()),
    ("N2 a comment in league_reserve turns NOTHING red", LR_PATH,
     "#: The outcomes of a visit made for the top-off alone",
     "#: (edited: topoff_only = ball_only or bool(kit.get(\"walk\")), a comment only)\n"
     "#: The outcomes of a visit made for the top-off alone", set()),
    ("N3 a comment in the driver turns NOTHING red", HARNESS,
     "        # step 10b (design R5): `stock_topoff._memo()` looks for exactly this set",
     "        # (edited) held = BB._kit_held() named in a comment only\n"
     "        # step 10b (design R5): `stock_topoff._memo()` looks for exactly this set", set()),
]


def main() -> int:
    tsrc = T_PATH.read_text(encoding="utf-8")
    lrsrc = LR_PATH.read_text(encoding="utf-8")
    hsrc = HARNESS.read_text(encoding="utf-8")
    print("H — pure");                       h_rows()
    print("\nG — kit_grade.py, executed");    g_rows()
    print("\nO — the kit forecast");          o_rows()
    print("\nS — the visit");                 s_rows()
    print("\nP — the counter phase");         p_rows()
    print("\nA — AST");                       a_rows(tsrc, lrsrc, hsrc)
    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    real = {name: sys.modules[name] for name in (T_NAME, LR_NAME, KG_NAME)}
    paths = {T_PATH: T_NAME, LR_PATH: LR_NAME, KG_PATH: KG_NAME}
    for i, (label, path, old, new, want) in enumerate(CASES):
        try:
            src = path.read_text(encoding="utf-8")
            n = src.count(old)
            if n != 1:
                raise AssertionError(f"mutant anchor found {n} times: {old[:80]!r}")
            msrc = src.replace(old, new)
            if path != HARNESS:
                name = paths[path]
                mod = types.ModuleType(name)
                mod.__file__ = str(path)
                mod.__package__ = "modules.story" if name != KG_NAME else ""
                sys.modules[name] = mod
                exec(compile(msrc, f"<mutant {i}>", "exec"), mod.__dict__)
            red = all_rows(msrc if path == T_PATH else tsrc, msrc if path == LR_PATH else lrsrc,
                           msrc if path == HARNESS else hsrc, "m")
            check(label, red == want, f"red {sorted(red)}" + ("" if red == want else f" (want {sorted(want)})"))
        except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
            check(label, False, f"{type(error).__name__}: {error}")
        finally:
            for name, module in real.items():
                sys.modules[name] = module
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
