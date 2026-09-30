"""GATE — USER RULING 26, design v2 step 10a (HK at Rustboro): the healing-kit top-off riding step 9a's heal errand
(`modules/story/stock_topoff.py`: `kit_wants`, `visit_plan`, `parse_kit_flag`, `_kit_held`, `_kit_skip_reason`, the
kit branch of `ball_topoff_errand` and `_walk_buy_return`; the heal's flag hunk in `higher_level_actions.py`).

WHY. The kit spends the same visit's money as the balls, rides the same walk, and must never change step 9a when it is
OFF, skipped or in `observe`. The spec is `ai-research-notes/2026-09-29-kittopoff-SPEC.md` (D1-D12). Each hazard has
an EXECUTING row, and each row a mutant that turns it red (step 9b's review: rows get the input SHAPE production gives
them, and a coverage check runs before the gate is trusted).

ROWS
  K1-K6   PURE `kit_wants`: Rustboro's HP line; held counts the tier AND higher tiers, never lower; Max Potion excluded;
          the status line (Full Heal to 2, else Awakening + Ice Heal, a held Full Heal counting toward each); never a
          quantity <= 0 and never a Revive/Antidote/Max Potion over a grid.
  K7-K11  PURE `visit_plan`: Rustboro's split (4 + 4 balls around 4 Super Potions, ₽70 left); the kit alone; the
          reserve phase comes FIRST when money is tight; Sootopolis's post-basket budget (1 Hyper, no Ultra); the
          refusals; a total >= 10 balls still earns a Premier; spend never exceeds the budget over a grid.
  K12-K14 `parse_kit_flag` names THIS flag; `_kit_held` subtracts the reserve (and the RAWBAG fault does not);
          `_kit_skip_reason` (kit `1` needs `POKEBOT_R27_KEYITEMS=1`).
  E1-E8   the errand EXECUTED with a recording walk: kit OFF is 9a's; kit `observe` leaves the ball purchase exactly
          9a's; kit `1` splits; kit alone; kit `1` without key items is a named skip with 9a's balls; a kit-only
          shortfall memoises ONLY the kit key; a failed walk memoises both; a ball memo leaves a kit-only walk.
  W1-W2   `_walk_buy_return` EXECUTED (the 9a stubs, with a kit line): balls and kit verified per name; a kit
          shortfall is kit_ok False with balls_ok True.
  A1      (AST) the heal parses `POKEBOT_R26_KITTOPOFF` before its first yield (the guard and call are 9a's A2).
  --- added after the ADVERSARIAL MUTANT PASS (41 plausible mutants: this gate caught 2, the 9a gate 6, 32 neither) ---
  K15-K16 `visit_plan`: the reserve phase fills to EXACTLY reserve + 1 and fires AT the reserve; the balls never exceed
          TARGET, none above TRIGGER, none when the ball flag is not `1` (grid, with an EMPTY kit too).
  K17-K19 a Mart selling Full Heal AND the specific cures buys Full Heal only; a reserve larger than the bag is 0, never
          negative; `_reserve()` is story_mode's constant (unstubbed).
  E9-E18  the errand's untested inputs: a full kit (the held view reaches the plan); key items unset with the balls OFF;
          a kit memo; a planning raise (each flag logs only its own tag); tight money (no phantom ball phase in
          `observe`); Arm 3's exact observe line; an outer close; a raising or not-back walk; an unstable exit; the
          FAULT_FLOOR lever. Lines are matched by their `[KIT-BUY]` / `[BALLS-BUY]` PREFIX, not a `why=` substring.
  W3-W5   a kit-only walk with the item already held (the DELTA, not the count); a kit line the live list drops, and a
          ball line it drops: each a SHORTFALL of its own set, never a silent ok.
  A2-A3   (AST) a kit-flag typo is REPORTED under the kit's name; the guard runs on EITHER flag and passes `kit_mode`.
  M1-M20, MA-MW4  source mutants, each with the EXACT set of rows it must turn red; N1-N3 comment-only edits (none red).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_kit_topoff.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import os
import pathlib
import sys
import types
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
SANDBOX = HERE.parents[1] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
T_PATH = SANDBOX / "modules" / "story" / "stock_topoff.py"
H_PATH = SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py"
T_NAME = "modules.story.stock_topoff"

import modules.story.stock_topoff  # noqa: E402,F401

FAILURES: list[str] = []
PRICES = {"Poké Ball": 200, "Great Ball": 600, "Ultra Ball": 1200, "Potion": 300, "Super Potion": 700,
          "Hyper Potion": 1200, "Max Potion": 2500, "Full Heal": 600, "Awakening": 250, "Ice Heal": 250,
          "Premier Ball": 200}
LIM = {"trigger": 20, "target": 30, "batch_cap": 6000}
RUSTBORO = ("Potion", "Super Potion")
SOOTOPOLIS = ("Hyper Potion", "Max Potion", "Full Heal")


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


class Patch:
    def __init__(self):
        self.saved, self.env = [], {}

    def set(self, obj, name, value):
        self.saved.append((obj, name, getattr(obj, name, None), hasattr(obj, name)))
        setattr(obj, name, value)

    def setenv(self, **kw):
        for k, v in kw.items():
            self.env.setdefault(k, os.environ.get(k))
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


def row(label, fn, tag, reds):
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if not ok:
        reds.append(label.split()[0])
    if not tag:
        check(label, ok, detail)


def t():
    return sys.modules[T_NAME]


# ------------------------------------------------------------------------------------------------ K rows (pure)
def k_rows(tag=""):
    m, reds = t(), []

    def k1():
        return m.kit_wants(RUSTBORO, {}, 4) == [("Super Potion", 4)], str(m.kit_wants(RUSTBORO, {}, 4))

    def k2():
        a = m.kit_wants(RUSTBORO, {"Super Potion": 2}, 4)
        b = m.kit_wants(RUSTBORO, {"Hyper Potion": 5}, 4)      # a higher tier counts
        c = m.kit_wants(RUSTBORO, {"Potion": 10}, 4)           # a lower tier does not
        return a == [("Super Potion", 2)] and b == [] and c == [("Super Potion", 4)], f"{a} {b} {c}"

    def k3():
        w = m.kit_wants(SOOTOPOLIS, {}, 4)
        return w == [("Hyper Potion", 4), ("Full Heal", 2)], str(w)

    def k4():
        s = ("Awakening", "Ice Heal")
        a = m.kit_wants(s, {}, 4)
        b = m.kit_wants(s, {"Full Heal": 1}, 4)
        c = m.kit_wants(s, {"Awakening": 1}, 4)
        d = m.kit_wants(("Full Heal",), {"Full Heal": 1}, 4)
        return (a == [("Awakening", 1), ("Ice Heal", 1)] and b == [] and c == [("Ice Heal", 1)]
                and d == [("Full Heal", 1)]), f"{a} {b} {c} {d}"

    def k5():
        bad = []
        for sold in (RUSTBORO, SOOTOPOLIS, ("Awakening", "Ice Heal"), ("Potion",), ()):
            for n in range(7):
                for name in ("Potion", "Super Potion", "Hyper Potion", "Full Heal", "Awakening", "Ice Heal"):
                    for it, q in m.kit_wants(sold, {name: n}, 4):
                        if q <= 0 or it in ("Max Potion", "Revive", "Antidote", "Parlyz Heal", "Burn Heal"):
                            bad.append((sold, name, n, it, q))
        return not bad, f"{len(bad)} bad: {bad[:3]}"

    def k6():
        return m.kit_wants(("Max Potion",), {}, 4) == [], str(m.kit_wants(("Max Potion",), {}, 4))

    def k17():
        s = ("Full Heal", "Awakening", "Ice Heal")
        a = m.kit_wants(s, {}, 4)
        b = m.kit_wants(s, {"Full Heal": 2}, 4)
        return a == [("Full Heal", 2)] and b == [], f"{a} {b}"

    for label, fn in (("K1 Rustboro: 4 Super Potions from an empty bag", k1),
                      ("K2 held counts the tier AND higher tiers, never lower", k2),
                      ("K3 Sootopolis: Hyper Potion (Max Potion EXCLUDED) and Full Heal x2", k3),
                      ("K4 status: Awakening + Ice Heal where no Full Heal; a held Full Heal counts toward each", k4),
                      ("K5 never a quantity <= 0, never a Revive/Antidote/Max Potion (grid)", k5),
                      ("K6 a Mart selling only Max Potion gives no HP line", k6),
                      ("K17 a Mart selling Full Heal AND the specific cures buys Full Heal only (D3 'otherwise')", k17)):
        row(label, fn, tag, reds)
    return reds


def _vp(**over):
    kw = dict(spare=7, money=9940, ball="Poké Ball", ball_price=200, stage_name="MID", floor_money=1000, lim=LIM,
              wants=[("Super Potion", 4)], prices=PRICES, reserve=10, buy_balls=True)
    kw.update(over)
    return t().visit_plan(**kw)


def vp_rows(tag=""):
    m, reds = t(), []

    def k7():
        p = _vp()
        return (p["ball_lines"] == [("Poké Ball", 8)] and p["kit"] == [("Super Potion", 4)] and p["budget"] == 4470
                and p["left"] == 70 and p["balls_qty"] == 8), str(p)

    def k8():
        p = _vp(buy_balls=False)
        return p["ball_lines"] == [] and p["kit"] == [("Super Potion", 4)] and p["left"] == 1670, str(p)

    def k8b():
        # money tight (budget 1500): the reserve phase comes FIRST (6 balls to reach 11, ₽300 left), the kit cannot
        # afford a Super Potion, and the rest phase buys 1 more ball: 7 in all, ₽100 left
        p = _vp(spare=5, money=4000)
        return (p["ball_lines"] == [("Poké Ball", 7)] and p["kit"] == [] and p["budget"] == 1500
                and p["left"] == 100), str(p)

    def k9():
        p = _vp(spare=18, money=22166, ball="Ultra Ball", ball_price=1200, stage_name="BASKET_ERA",
                floor_money=19000, wants=[("Hyper Potion", 4), ("Full Heal", 2)])
        return p["kit"] == [("Hyper Potion", 1)] and p["ball_lines"] == [] and p["left"] == 383, str(p)

    def k10():
        outs = [_vp(stage_name=None), _vp(stage_name="PRE_GYM1"), _vp(floor_money=None), _vp(money=1000)]
        return all(o["ball_lines"] == [] and o["kit"] == [] for o in outs), str([o["reason"] for o in outs])

    def k10b():
        p = _vp(spare=0, money=40000)
        return (p["ball_lines"] == [("Poké Ball", 16)] and p["kit"] == [("Super Potion", 4)]), str(p)

    def k11():
        bad = []
        for spare in (0, 5, 10, 11, 15, 20, 25):
            for money in (1500, 3000, 9940, 20000, 60000):
                for buy in (True, False):
                    p = _vp(spare=spare, money=money, buy_balls=buy, wants=[("Super Potion", 4), ("Full Heal", 2)])
                    spent = sum(PRICES[n] * q for n, q in p["ball_lines"]) + sum(PRICES[n] * q for n, q in p["kit"])
                    if spent > p["budget"] or spent != p["budget"] - p["left"]:
                        bad.append((spare, money, buy, spent, p["budget"], p["left"]))
        return not bad, f"{len(bad)} bad: {bad[:3]}"

    def k15():
        # spare 5, ₽5,800 (budget 2400): the reserve phase buys EXACTLY 6 (to 11), the kit 1 Super Potion, the rest 2;
        # spare 10 AT the reserve, ₽3,800 (budget 1400): the reserve phase still fires (1 ball), the kit 1, the rest 2
        a = _vp(spare=5, money=5800)
        b = _vp(spare=10, money=3800)
        return (a["ball_lines"] == [("Poké Ball", 8)] and a["kit"] == [("Super Potion", 1)] and a["left"] == 100
                and b["ball_lines"] == [("Poké Ball", 3)] and b["kit"] == [("Super Potion", 1)] and b["left"] == 100), \
            f"{a} {b}"

    def k16():
        bad = []
        for spare in (0, 5, 10, 11, 15, 20, 21, 25, 30, 35):
            for money in (1500, 3000, 9940, 20000, 60000):
                for buy in (True, False):
                    for wants in ([], [("Super Potion", 4), ("Full Heal", 2)]):
                        p = _vp(spare=spare, money=money, buy_balls=buy, wants=wants)
                        n = p["balls_qty"]
                        if ((n and spare + n > LIM["target"]) or (spare > LIM["trigger"] and n) or (not buy and n)
                                or n != sum(q for _, q in p["ball_lines"]) or any(q <= 0 for _, q in p["kit"])):
                            bad.append((spare, money, buy, len(wants), n, p["kit"]))
        return not bad, f"{len(bad)} bad: {bad[:3]}"

    for label, fn in (("K7 Rustboro: 4 + 4 Poké around 4 Super Potions on ONE budget of 4470, 70 left", k7),
                      ("K8 the kit alone (the ball flag not 1): 4 Super Potions, 1670 left", k8),
                      ("K8b money tight: the reserve phase FIRST (6 balls), the kit gets nothing", k8b),
                      ("K9 Sootopolis post-basket: 1 Hyper Potion, no Full Heal, no Ultra, 383 left", k9),
                      ("K10 refusals: unreadable stage or floor, PRE_GYM1, money at the floor", k10),
                      ("K10b a total >= 10 balls is ONE line set (16 Poké: a Premier is earned)", k10b),
                      ("K11 spend never exceeds the ONE budget, and left is exact (grid)", k11),
                      ("K15 the reserve phase fills to EXACTLY reserve + 1, and fires AT the reserve", k15),
                      ("K16 balls never exceed TARGET, none above TRIGGER, none unless the ball flag is 1 (grid)", k16)):
        row(label, fn, tag, reds)
    return reds


def misc_rows(tag=""):
    m, reds = t(), []

    def k12():
        mode, err = m.parse_kit_flag("yes")
        ok_vals = [m.parse_kit_flag(v) for v in (None, "", "0", "observe", "1")]
        return (mode == "" and err is not None and "POKEBOT_R26_KITTOPOFF='yes'" in err
                and [v[0] for v in ok_vals] == ["", "", "", "observe", "1"] and all(v[1] is None for v in ok_vals)), err

    def k13():
        from modules.story import league_reserve as lr

        with Patch() as p:
            p.set(lr, "_stock_by_name", lambda names: {n: {"Hyper Potion": 31, "Full Heal": 8}.get(n, 0) for n in names})
            p.set(lr, "reserved_quantities", lambda: {"Hyper Potion": 30, "Full Heal": 8, "Revive": 3})
            p.setenv(POKEBOT_R26_FAULT_RAWBAG=None)
            view = m._kit_held()
            p.setenv(POKEBOT_R26_FAULT_RAWBAG="1")
            raw = m._kit_held()
        return (view["Hyper Potion"] == 1 and view["Full Heal"] == 0 and raw["Hyper Potion"] == 31
                and raw["Full Heal"] == 8), f"view={view} raw={raw}"

    def k14():
        with Patch() as p:
            p.setenv(POKEBOT_R27_KEYITEMS=None)
            a = m._kit_skip_reason("1")
            b = m._kit_skip_reason("observe")
            p.setenv(POKEBOT_R27_KEYITEMS="1")
            c = m._kit_skip_reason("1")
        return a is not None and b is None and c is None, f"{a} {b} {c}"

    def k18():
        from modules.story import league_reserve as lr

        with Patch() as p:
            p.set(lr, "_stock_by_name", lambda names: {n: {"Hyper Potion": 10, "Full Heal": 2}.get(n, 0) for n in names})
            p.set(lr, "reserved_quantities", lambda: {"Hyper Potion": 30, "Full Heal": 8})
            p.setenv(POKEBOT_R26_FAULT_RAWBAG=None)
            view = m._kit_held()
        return view["Hyper Potion"] == 0 and view["Full Heal"] == 0 and min(view.values()) >= 0, str(view)

    def k19():
        from plugins.custom_modes.story_mode import DEX_CATCH_BALL_RESERVE

        return m._reserve() == DEX_CATCH_BALL_RESERVE, f"{m._reserve()} vs {DEX_CATCH_BALL_RESERVE}"

    for label, fn in (("K12 parse_kit_flag: a typo is OFF with an error naming POKEBOT_R26_KITTOPOFF", k12),
                      ("K13 _kit_held subtracts reserved_quantities(); the RAWBAG fault does not", k13),
                      ("K14 kit `1` without POKEBOT_R27_KEYITEMS=1 is a named skip; observe is not", k14),
                      ("K18 a reserve LARGER than the bag leaves 0 of that item, never a negative", k18),
                      ("K19 _reserve() is story_mode's DEX_CATCH_BALL_RESERVE (unstubbed)", k19)):
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------------------------------------------ E rows (the errand)
def _errand(p, *, ball_mode, kit_mode, keyitems, walk_kind="ok", memo=None, held=None, money=9940, stable=True,
            fault_floor=None, plan_raise=False, close_after=None):
    from modules import player as _player
    from modules.context import context
    from modules.map_data import PokemonCenter
    from modules.story import early_game as _eg
    from plugins.custom_modes.story_mode import StoryMode

    m = t()
    rec = {"walks": [], "emitted": [], "recover": 0}
    frames = [0]

    def walk(mart, exit_map, exit_tile, lines, live, reason, report, kit_lines=(), kit_reason=""):
        rec["walks"].append((list(lines), list(kit_lines)))
        frames[0] += 100
        yield
        if walk_kind == "loop":
            for _ in range(200):
                frames[0] += 100
                yield
            raise RuntimeError("UNBOUNDED")
        if walk_kind == "hang":                  # an OUTER close arrives mid-walk (the frame bound never expires)
            while True:
                frames[0] += 1
                yield
        if walk_kind == "raise":
            raise RuntimeError("boom in the walk")
        report.update({"bought": sum(q for _, q in lines), "premier": 0, "spare_after": 15, "money_after": 5540,
                       "returned": walk_kind != "notback", "balls_ok": True,
                       "kit_ok": walk_kind != "kitshort", "kit_got": {n: 0 for n, _ in kit_lines}})
        report["ok"] = report["balls_ok"] and report["kit_ok"]
        if walk_kind == "kitshort":
            report["kit_why"] = "kit bag delta short"

    def recover(exit_map, exit_tile, report):
        rec["recover"] += 1
        frames[0] += 100
        yield
        report["recovered_on_exit"] = True

    story = StoryMode.__new__(StoryMode)
    story._ball_topoff_failed = set(memo or ())
    p.setenv(POKEBOT_R27_KEYITEMS=keyitems, POKEBOT_R23_FAULT_FLOOR=fault_floor, POKEBOT_R26_FAULT_RAWBAG=None,
             POKEBOT_R23_FAULT_ERRANDFRAMES="250" if walk_kind == "loop" else None)

    def inputs(mode):
        if plan_raise:
            raise RuntimeError("bag unreadable")
        return {"stage": "MID", "floor": 1000, "spare": 7, "money": money, "flags": {}, "price_of": lambda n: PRICES[n]}

    p.set(m, "_emit", lambda line: rec["emitted"].append(line))
    p.set(m, "_allowed", lambda: {"Poké Ball"})
    p.set(m, "_inputs", inputs)
    p.set(m, "_kit_held", lambda names=None: dict(held or {}))
    p.set(m, "_reserve", lambda: 10)
    p.set(m, "_walk_buy_return", walk)
    p.set(m, "_recover", recover)
    p.set(_player, "get_player_avatar", lambda: SimpleNamespace(map_group_and_number=(0, 3), local_coordinates=(16, 39)))
    p.set(_eg, "reraise_if_aborting", lambda error: (_ for _ in ()).throw(error) if "ABORT" in str(error) else None)
    p.set(context, "emulator", SimpleNamespace(get_frame_count=lambda: frames[0], press_button=lambda b: None))
    p.set(context, "bot_mode_instance", story)
    gen = m.ball_topoff_errand(PokemonCenter.RustboroCity, ball_mode, stable, kit_mode=kit_mode)
    yields, out = 0, "NO END"
    try:
        while yields < 1000:
            next(gen)
            yields += 1
            if close_after is not None and yields >= close_after:
                try:
                    gen.close()
                    out = "CLOSED"
                except Exception as error:  # noqa: BLE001 - a close that raises is the row's failure, reported
                    out = f"CLOSE RAISED {error!r}"
                break
    except StopIteration as stop:
        out = stop.value
    return out, yields, rec, sorted(story._ball_topoff_failed)


NINE_A = [("Poké Ball", 10), ("Poké Ball", 12)]
BOTH = ["RustboroCity", "RustboroCity:kit"]
#: the live Arm 3 (K-OBS) line, predicted in `2026-09-29-kittopoff10a-PREDICTIONS.md`, byte for byte
ARM3 = ("[KIT-BUY] why=kit-observe mart=RustboroCity kit=[('Super Potion', 4)] bought=- money=9940->9940 "
        "wants=[('Super Potion', 4)] reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after "
        "the kit); budget 4470, 70 left")


def tags(emitted, prefix):
    """The `why=` of every line that STARTS with `prefix` (a kit line under the ball prefix is not a kit line)."""
    return [line.split()[1] for line in emitted if line.startswith(prefix)]


def e_rows(tag=""):
    reds = []

    def run(**kw):
        with Patch() as p:
            return _errand(p, **kw)

    def has(lines, needle):
        return sum(1 for line in lines if needle in line)

    def e1():
        out, y, rec, memo = run(ball_mode="", kit_mode="", keyitems="1")
        return out is False and y == 0 and rec["walks"] == [] and rec["emitted"] == [], f"{out} {y} {rec}"

    def e2():
        out, _y, rec, _m = run(ball_mode="1", kit_mode="observe", keyitems="1")
        return (rec["walks"] == [(NINE_A, [])] and has(rec["emitted"], "why=kit-observe") == 1), str(rec)

    def e3():
        out, _y, rec, memo = run(ball_mode="1", kit_mode="1", keyitems="1")
        return (out is True and rec["walks"] == [([("Poké Ball", 8)], [("Super Potion", 4)])] and memo == []), str(rec)

    def e4():
        out, _y, rec, _m = run(ball_mode="", kit_mode="1", keyitems="1")
        return (out is True and rec["walks"] == [([], [("Super Potion", 4)])]
                and has(rec["emitted"], "[BALLS-BUY]") == 0), str(rec)

    def e5():
        out, _y, rec, _m = run(ball_mode="1", kit_mode="1", keyitems=None)
        return (rec["walks"] == [(NINE_A, [])] and has(rec["emitted"], "why=kit-skip") == 1), str(rec)

    def e6():
        out, _y, rec, memo = run(ball_mode="1", kit_mode="1", keyitems="1", walk_kind="kitshort")
        return (memo == ["RustboroCity:kit"] and has(rec["emitted"], "why=kit-failed") == 1
                and has(rec["emitted"], "why=topoff-failed") == 1 and rec["recover"] == 1), f"memo={memo} {rec}"

    def e7():
        out, _y, rec, memo = run(ball_mode="1", kit_mode="1", keyitems="1", walk_kind="loop")
        return memo == ["RustboroCity", "RustboroCity:kit"] and rec["recover"] == 1, f"memo={memo}"

    def e8():
        out, _y, rec, memo = run(ball_mode="1", kit_mode="1", keyitems="1", memo={"RustboroCity"})
        return rec["walks"] == [([], [("Super Potion", 4)])] and has(rec["emitted"], "[BALLS-BUY]") == 0, str(rec)

    K, B = "[KIT-BUY]", "[BALLS-BUY]"

    def e9():
        out, _y, rec, _m = run(ball_mode="", kit_mode="1", keyitems="1", held={"Super Potion": 4})
        return (out is False and rec["walks"] == [] and tags(rec["emitted"], K) == ["why=kit-none"]
                and tags(rec["emitted"], B) == []), str(rec)

    def e10():
        out, _y, rec, _m = run(ball_mode="", kit_mode="1", keyitems=None)
        return (out is False and rec["walks"] == [] and tags(rec["emitted"], K) == ["why=kit-skip"]
                and tags(rec["emitted"], B) == []), str(rec)

    def e11():
        a = run(ball_mode="", kit_mode="1", keyitems="1", memo={"RustboroCity:kit"})
        b = run(ball_mode="1", kit_mode="1", keyitems="1", memo={"RustboroCity:kit"})
        return (a[0] is False and a[1] == 0 and a[2]["walks"] == [] and a[2]["emitted"] == []
                and b[2]["walks"] == [(NINE_A, [])] and tags(b[2]["emitted"], K) == []), f"{a} || {b}"

    def e12():
        a = run(ball_mode="1", kit_mode="1", keyitems="1", plan_raise=True)
        b = run(ball_mode="", kit_mode="1", keyitems="1", plan_raise=True)
        c = run(ball_mode="1", kit_mode="", keyitems="1", plan_raise=True)
        return (a[0] is False and a[3] == BOTH and tags(a[2]["emitted"], B) == ["why=topoff-failed"]
                and tags(a[2]["emitted"], K) == ["why=kit-failed"]
                and b[0] is False and "RustboroCity:kit" in b[3] and tags(b[2]["emitted"], B) == []
                and tags(b[2]["emitted"], K) == ["why=kit-failed"]
                and c[0] is False and c[3] == ["RustboroCity"] and tags(c[2]["emitted"], B) == ["why=topoff-failed"]
                and tags(c[2]["emitted"], K) == []), f"{a} || {b} || {c}"

    def e13():
        a = run(ball_mode="", kit_mode="1", keyitems="1", money=3000)
        b = run(ball_mode="observe", kit_mode="1", keyitems="1", money=3000)
        return (a[2]["walks"] == [([], [("Super Potion", 1)])] and b[2]["walks"] == [([], [("Super Potion", 1)])]
                and tags(b[2]["emitted"], B) == ["why=topoff-observe"]), f"{a[2]} || {b[2]}"

    def e14():
        out, _y, rec, _m = run(ball_mode="1", kit_mode="observe", keyitems="1")
        got = [line for line in rec["emitted"] if line.startswith(K)]
        return got == [ARM3], str(got)

    def e15():
        a = run(ball_mode="", kit_mode="1", keyitems="1", walk_kind="hang", close_after=3)
        b = run(ball_mode="1", kit_mode="1", keyitems="1", walk_kind="hang", close_after=3)
        return (a[0] == "CLOSED" and a[3] == BOTH and tags(a[2]["emitted"], B) == []
                and tags(a[2]["emitted"], K) == ["why=kit-closed"]
                and b[0] == "CLOSED" and b[3] == BOTH and tags(b[2]["emitted"], B) == ["why=topoff-closed"]
                and tags(b[2]["emitted"], K) == ["why=kit-closed"]), f"{a} || {b}"

    def e16():
        a = run(ball_mode="", kit_mode="1", keyitems="1", walk_kind="raise")
        b = run(ball_mode="1", kit_mode="1", keyitems="1", walk_kind="notback")
        return (a[0] is True and a[3] == BOTH and a[2]["recover"] == 1 and tags(a[2]["emitted"], B) == []
                and tags(a[2]["emitted"], K) == ["why=kit-failed", "why=kit-recovery"]
                and b[0] is True and b[3] == BOTH and b[2]["recover"] == 1
                and tags(b[2]["emitted"], B) == ["why=topoff-failed", "why=topoff-recovery"]
                and tags(b[2]["emitted"], K) == ["why=kit-failed"]), f"{a} || {b}"

    def e17():
        a = run(ball_mode="", kit_mode="1", keyitems="1", stable=False)
        b = run(ball_mode="1", kit_mode="1", keyitems="1", stable=False)
        return (a[0] is False and a[1] == 0 and a[2]["walks"] == [] and tags(a[2]["emitted"], B) == []
                and tags(a[2]["emitted"], K) == ["why=kit-skip"]
                and b[0] is False and b[2]["walks"] == [] and tags(b[2]["emitted"], B) == ["why=topoff-skip"]
                and tags(b[2]["emitted"], K) == ["why=kit-skip"]), f"{a} || {b}"

    def e18():
        out, _y, rec, _m = run(ball_mode="", kit_mode="1", keyitems="1", fault_floor="9900")
        return (out is False and rec["walks"] == [] and tags(rec["emitted"], B) == []
                and tags(rec["emitted"], K) == ["why=kit-none"]), str(rec)

    for label, fn in (("E1 both flags OFF: False, ZERO yields, nothing emitted", e1),
                      ("E2 kit `observe`: the ball purchase is EXACTLY 9a's, one kit-observe line", e2),
                      ("E3 kit `1` (key items on): 8 Poké + 4 Super Potions in one walk", e3),
                      ("E4 kit `1`, balls OFF: a kit-only walk, no [BALLS-BUY] line", e4),
                      ("E5 kit `1` WITHOUT key items: 9a's balls and ONE kit-skip line", e5),
                      ("E6 a kit-only shortfall memoises ONLY the kit key (and recovers)", e6),
                      ("E7 a failed WALK (the bound) memoises BOTH keys", e7),
                      ("E8 a ball memo leaves a kit-only walk", e8),
                      ("E9 a FULL kit (held reaches the plan): no walk, ONE [KIT-BUY] kit-none, no ball line", e9),
                      ("E10 kit `1`, balls OFF, key items UNSET: a named skip, nothing walks", e10),
                      ("E11 a kit memo blocks the kit only (balls OFF: nothing; balls 1: 9a's walk, no kit line)", e11),
                      ("E12 a planning raise: each flag logs ONLY its own tag; the kit key only when the kit is on", e12),
                      ("E13 ₽3,000: the kit alone buys 1 Super Potion, balls OFF or observe (no phantom ball phase)",
                       e13),
                      ("E14 the kit-observe line is EXACTLY Arm 3's (prefix, plan, wants, reason)", e14),
                      ("E15 an outer close mid-walk: kit-closed (+ topoff-closed only with balls), both keys, no raise",
                       e15),
                      ("E16 a failed walk (a raise; not back): both keys, recovery, each set logs only its own tags",
                       e16),
                      ("E17 an unstable exit: each flag logs ONE skip under its own prefix, nothing walks", e17),
                      ("E18 the FAULT_FLOOR lever gates the kit (floor 9900: nothing affordable, one kit-none)", e18)):
        row(label, fn, tag, reds)
    return reds


# --------------------------------------------------------------------------------- W rows (`_walk_buy_return`)
def w_rows(tag=""):
    import modules.items as _items
    import modules.mart as _mart
    import modules.modes.util as _util
    import modules.modes.util.higher_level_actions as _hla
    import modules.modes.util.tasks_scripts as _ts
    import modules.modes.util.walking as _walking
    import modules.player as _player
    from modules.context import context
    from modules.map_data import MapRSE
    from modules.story import early_game as _eg
    from modules.story import league_reserve as _lr

    m, reds, state = t(), [], {}

    def nav(dest_map, dest_tile, **_kw):
        state["map"], state["tile"] = tuple(dest_map.value), tuple(dest_tile)
        yield

    def one(*_a, **_kw):
        yield

    def face(direction):
        state["facing"] = direction
        yield

    def press(button):
        if button == "A":
            state["menu"] = True

    def buy(lines):
        for item, qty in lines:
            state["asked"].append((item.name, qty))
            got = qty - (state["short"] if item.name == "Super Potion" else 0)
            state["bag"][item.name] = state["bag"].get(item.name, 0) + got
            if item.name == "Poké Ball" and qty >= 10:
                state["bag"]["Premier Ball"] = state["bag"].get("Premier Ball", 0) + 1
        yield

    class Bag:
        def quantity_of(self, item):
            return state["bag"].get(item.name, 0)

        @property
        def number_of_balls_except_master_ball(self):
            return sum(q for n, q in state["bag"].items() if "Ball" in n)

    def walk(short, lines=(("Poké Ball", 8),), kit_lines=(("Super Potion", 4),), bag=None,
             sold=("Poké Ball", "Potion", "Super Potion")):
        with Patch() as p:
            p.set(_eg, "_navigate_riding_out", nav)
            p.set(_eg, "wait_until_truly_controllable", one)
            p.set(_eg, "_check_abort", lambda: None)
            p.set(_walking, "ensure_facing_direction", face)
            p.set(_ts, "task_is_active", lambda name: bool(state.get("menu")) and name == "Task_ShopMenu")
            p.set(_mart, "get_mart_buyable_items", lambda: [SimpleNamespace(name=n) for n in sold])
            p.set(_hla, "buy_in_shop", buy)
            p.set(_lr, "_close_shop_and_dialogs", lambda report: one())
            p.set(_items, "get_item_bag", lambda: Bag())
            p.set(_items, "get_item_by_name", lambda n: SimpleNamespace(name=n, price=PRICES.get(n, 200)))
            p.set(_player, "get_player", lambda: SimpleNamespace(money=5540))
            p.set(_player, "get_player_avatar", lambda: SimpleNamespace(map_group_and_number=state["map"],
                                                                      local_coordinates=state["tile"],
                                                                      facing_direction=state["facing"]))
            p.set(_util, "wait_for_n_frames", lambda n: one())
            p.set(m, "_emit", lambda line: state["emitted"].append(line))
            p.set(context, "emulator", SimpleNamespace(press_button=press, get_frame_count=lambda: 0))
            state.clear()
            state.update({"map": (0, 3), "tile": (16, 39), "facing": "Down", "menu": False,
                          "bag": dict(bag or {"Poké Ball": 7}), "short": short, "emitted": [], "asked": []})
            report: dict = {}
            gen = m._walk_buy_return((MapRSE.RUSTBORO_CITY_MART, (3, 3), "Left"), MapRSE.RUSTBORO_CITY, (16, 39),
                                     [tuple(x) for x in lines], {"spare": 7, "money": 9940}, "r", report,
                                     kit_lines=[tuple(x) for x in kit_lines], kit_reason="k")
            for _ in range(500):
                try:
                    next(gen)
                except StopIteration:
                    break
            return report, list(state["emitted"]), list(state["asked"])

    def w1():
        r, emitted, _a = walk(0)
        return (r.get("ok") is True and r.get("balls_ok") is True and r.get("kit_ok") is True
                and r.get("kit_got") == {"Super Potion": 4} and r.get("bought") == 8 and r.get("returned") is True
                and sum("why=topoff " in x for x in emitted) == 1 and sum("why=kit " in x for x in emitted) == 1), \
            f"{r} {emitted}"

    def w2():
        r, _e, _a = walk(1)
        return (r.get("ok") is False and r.get("balls_ok") is True and r.get("kit_ok") is False
                and r.get("kit_got") == {"Super Potion": 3}), str(r)

    def w3():
        r, emitted, asked = walk(0, lines=[], kit_lines=[("Super Potion", 2)], bag={"Poké Ball": 7, "Super Potion": 2})
        return (r.get("ok") is True and r.get("kit_got") == {"Super Potion": 2} and r.get("bought") == 0
                and r.get("returned") is True and asked == [("Super Potion", 2)] and len(emitted) == 1
                and emitted[0].startswith("[KIT-BUY] why=kit ")), f"{r} {emitted} {asked}"

    def w4():
        r, emitted, asked = walk(0, sold=("Poké Ball", "Potion"))
        return (asked == [("Poké Ball", 8)] and r.get("balls_ok") is True and r.get("kit_ok") is False
                and r.get("kit_got") == {"Super Potion": 0} and r.get("ok") is False and emitted == []), \
            f"{r} {emitted} {asked}"

    def w5():
        r, emitted, asked = walk(0, sold=("Potion", "Super Potion"))
        return (asked == [("Super Potion", 4)] and r.get("balls_ok") is False and r.get("kit_ok") is True
                and r.get("bought") == 0 and r.get("ok") is False and "bag delta 0 != planned 8" in r.get("why", "")
                and emitted == []), f"{r} {emitted} {asked}"

    for label, fn in (("W1 balls and kit verified PER NAME: ok, one topoff line and one kit line", w1),
                      ("W2 a kit shortfall: kit_ok False, balls_ok True, ok False", w2),
                      ("W3 a kit-only walk, 2 already held: the DELTA (2), ONE [KIT-BUY] line, no ball line", w3),
                      ("W4 a kit line the live list DROPS: not asked of the shop, a KIT shortfall, never a silent ok",
                       w4),
                      ("W5 a ball line the live list DROPS (kit sold): a BALL shortfall, the kit bought", w5)):
        row(label, fn, tag, reds)
    return reds


def a_rows(hsrc, tag=""):
    reds = []

    def a1():
        tree = ast.parse(hsrc)
        heal = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "heal_in_pokemon_center")
        yields = sorted(n.lineno for n in ast.walk(heal) if isinstance(n, (ast.Yield, ast.YieldFrom)))
        parse = [n for n in ast.walk(heal) if isinstance(n, ast.Assign) and "_kit_mode" in ast.unparse(n.targets[0])]
        return (len(parse) == 1 and yields and parse[0].lineno < yields[0]
                and "POKEBOT_R26_KITTOPOFF" in ast.unparse(parse[0].value)), \
            f"parse={[x.lineno for x in parse]} first yield={yields[:1]}"

    def heal_of():
        tree = ast.parse(hsrc)
        return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "heal_in_pokemon_center")

    def a2():
        heal = heal_of()
        ifs = [n for n in ast.walk(heal) if isinstance(n, ast.If) and isinstance(n.test, ast.Name)
               and n.test.id == "_kit_error"]
        calls = [c for i in ifs for c in ast.walk(i)
                 if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_piggyback_report"]
        ok = (len(ifs) == 1 and len(calls) == 1 and len(calls[0].args) >= 2
              and isinstance(calls[0].args[0], ast.Constant) and "kit" in str(calls[0].args[0].value)
              and isinstance(calls[0].args[1], ast.Name) and calls[0].args[1].id == "_kit_error")
        return ok, f"ifs={len(ifs)} calls={[ast.unparse(c) for c in calls]}"

    def a3():
        heal = heal_of()
        calls = [c for c in ast.walk(heal) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "ball_topoff_errand"]
        if len(calls) != 1:
            return False, f"{len(calls)} ball_topoff_errand calls"
        kw = [k for k in calls[0].keywords if k.arg == "kit_mode"]
        guards = [n for n in ast.walk(heal) if isinstance(n, ast.If) and any(c is calls[0] for c in ast.walk(n))]
        g = min(guards, key=lambda n: n.end_lineno - n.lineno) if guards else None
        either = (g is not None and isinstance(g.test, ast.BoolOp) and isinstance(g.test.op, ast.Or)
                  and any("_kit_mode" in ast.unparse(v) for v in g.test.values)
                  and any("_topoff_mode" in ast.unparse(v) for v in g.test.values))
        return (len(kw) == 1 and isinstance(kw[0].value, ast.Name) and kw[0].value.id == "_kit_mode" and either), \
            f"kw={[ast.unparse(k) for k in kw]} guard={ast.unparse(g.test) if g else None}"

    row("A1 (AST) the heal parses POKEBOT_R26_KITTOPOFF before its FIRST yield", a1, tag, reds)
    row("A2 (AST) a kit-flag typo is REPORTED (`if _kit_error:` -> _piggyback_report under the kit's name)", a2, tag,
        reds)
    row("A3 (AST) the errand runs on EITHER flag and is passed kit_mode=_kit_mode", a3, tag, reds)
    return reds


def all_rows(hsrc, tag):
    return set(k_rows(tag) + vp_rows(tag) + misc_rows(tag) + e_rows(tag) + w_rows(tag) + a_rows(hsrc, tag))


def main() -> int:
    hsrc = H_PATH.read_text(encoding="utf-8")
    print("K — kit_wants (pure)");                      k_rows()
    print("\nK — visit_plan (pure)");                   vp_rows()
    print("\nK — flag, held view, key-item coupling");   misc_rows()
    print("\nE — the errand, executed");                e_rows()
    print("\nW — _walk_buy_return, executed");           w_rows()
    print("\nA — the heal (AST)");                      a_rows(hsrc)

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    cases = [
        ("M1 held counts only the best tier (not higher) -> K2", T_PATH,
         "        have = sum(held.get(name, 0) for name in KIT_HP_LADDER[KIT_HP_LADDER.index(best):])\n",
         "        have = held.get(best, 0)\n", {"K2"}),
        ("M2 Max Potion joins the ladder -> K3 K5 K6", T_PATH,
         "KIT_HP_LADDER = (\"Potion\", \"Super Potion\", \"Hyper Potion\")\n",
         "KIT_HP_LADDER = (\"Potion\", \"Super Potion\", \"Hyper Potion\", \"Max Potion\")\n", {"K3", "K5", "K6"}),
        ("M3 a held Full Heal no longer counts toward the specific cures -> K4", T_PATH,
         "            short = KIT_SPECIFIC_TARGET - (held.get(name, 0) + full_heals)\n",
         "            short = KIT_SPECIFIC_TARGET - held.get(name, 0)\n", {"K4"}),
        ("M4 the HP line's <= 0 guard removed -> K2 K5", T_PATH,
         "        if hp_target - have > 0:\n            wants.append((best, hp_target - have))\n",
         "        wants.append((best, hp_target - have))\n", {"K2", "K5"}),
        ("M5 the kit is not debited from the budget -> K7 K8 K9 K10b K11 E3 K15 E14", T_PATH,
         "            kit.append((name, qty))\n            left -= qty * prices[name]\n",
         "            kit.append((name, qty))\n", {"K7", "K8", "K9", "K10b", "K11", "E3", "K15", "E14"}),
        ("M6 the kit comes BEFORE the reserve phase -> K8b K15 E14", T_PATH,
         "    if buy_balls and ball and ball_price and spare <= reserve:\n",
         "    if False:\n", {"K8b", "K15", "E14"}),
        ("M7 the two ball phases bought as separate lines (a total >= 10 loses its Premier) -> K7 K8b K10b E3 K15", T_PATH,
         "    return {\"ball_lines\": plan_lines(ball, balls_qty) if balls_qty > 0 else [], \"kit\": kit, \"balls_qty\": balls_qty,",
         "    return {\"ball_lines\": ([(ball, first)] if first else []) + ([(ball, rest)] if rest else []), \"kit\": kit, \"balls_qty\": balls_qty,",
         {"K7", "K8b", "K10b", "E3", "K15"}),
        ("M8 parse_kit_flag names the BALL flag -> K12", T_PATH,
         "        return \"\", f\"{KIT_FLAG}={value!r} is not one of {VALID_FLAG_VALUES}: treated as OFF\"",
         "        return \"\", f\"POKEBOT_R23_BALLRESTOCK={value!r} is not one of {VALID_FLAG_VALUES}: treated as OFF\"",
         {"K12"}),
        ("M9 _kit_held ignores the reserve -> K13 K18", T_PATH,
         "    reserved = reserved_quantities()\n", "    reserved = {}\n", {"K13", "K18"}),
        ("M10 the key-item coupling removed -> K14 E5 E10", T_PATH,
         "    if kit_mode == \"1\" and os.environ.get(\"POKEBOT_R27_KEYITEMS\") != \"1\":\n", "    if False:\n",
         {"K14", "E5", "E10"}),
        ("M11 an OBSERVE kit changes the balls -> E2", T_PATH,
         "            if kit_buys and flag_mode == \"1\":\n", "            if flag_mode == \"1\":\n", {"E2"}),
        ("M12 a kit-only shortfall memoises the balls too -> E6", T_PATH,
         "        if walk_failed or not report.get(\"balls_ok\", report.get(\"ok\", False)):\n",
         "        if True:\n", {"E6"}),
        ("M13 the kit verification always ok -> W2 W4", T_PATH,
         "    report[\"kit_ok\"] = report[\"kit_got\"] == kit_want\n", "    report[\"kit_ok\"] = True\n", {"W2", "W4"}),
        ("M14 the heal reads a misspelled kit flag -> A1", H_PATH,
         "    _kit_mode, _kit_error = _kit_parse(_os_hla.environ.get(\"POKEBOT_R26_KITTOPOFF\"))\n",
         "    _kit_mode, _kit_error = _kit_parse(_os_hla.environ.get(\"POKEBOT_R26_KIT\"))\n", {"A1"}),
        # --- added by the coverage check (rows no mutant could redden: K1, K10, E1, E4, E7, E8, W1); sets written
        # before gate run 2 ---
        ("M15 the HP line picks the CHEAPEST tier sold -> K1 K2 E3 E4 E8 E13 E14", T_PATH,
         "        best = tiers[-1]\n", "        best = tiers[0]\n", {"K1", "K2", "E3", "E4", "E8", "E13", "E14"}),
        ("M16 PRE_GYM1 is not refused -> K10", T_PATH,
         "        return {**nothing, \"reason\": \"before gym 1 (no kit, as no balls: the named RULING 26 gap)\"}\n",
         "        pass\n", {"K10"}),
        ("M17 OFF acts as if the ball flag were on -> E1 E4 E9-E13 E15-E18", T_PATH,
         "    if flag_mode not in (\"observe\", \"1\") and kit_mode not in (\"observe\", \"1\"):\n        return False\n"
         "    try:\n        from plugins.custom_modes.story_mode import StoryMode\n",
         "    flag_mode = flag_mode or \"1\"\n"
         "    try:\n        from plugins.custom_modes.story_mode import StoryMode\n",
         {"E1", "E4", "E9", "E10", "E11", "E12", "E13", "E15", "E16", "E17", "E18"}),
        ("M18 a failure never memoises the kit key -> E6 E7 E16", T_PATH,
         "        if kit_lines and (walk_failed or not report.get(\"kit_ok\", False)):\n            failed.add(kit_key)\n",
         "        if kit_lines and (walk_failed or not report.get(\"kit_ok\", False)):\n            pass\n", {"E6", "E7", "E16"}),
        ("M19 a ball memo blocks the kit too -> E8", T_PATH,
         "    if city in failed:\n        flag_mode = \"\"                         # the balls failed here earlier this run\n",
         "    if city in failed:\n        return False\n", {"E8"}),
        ("M20 a successful kit purchase is not logged -> W1 W3", T_PATH,
         "        if planned_kit:\n            _emit(kit_log_line(\"kit\", mart=exit_map_name(mart_map),",
         "        if False:\n            _emit(kit_log_line(\"kit\", mart=exit_map_name(mart_map),", {"W1", "W3"}),
        ("N1 a comment naming the kit flag and `_kit_mode` in the heal turns NOTHING red", H_PATH,
         "    # before any yield, and a typo is OFF WITH an error naming THIS flag.\n",
         "    # before any yield (edited: POKEBOT_R26_KITTOPOFF and _kit_mode = named in a comment only).\n", set()),
        # --- the ADVERSARIAL MUTANT PASS (2026-09-29): 32 plausible mutants neither this gate nor 9a's caught, and the
        # two it did catch (MQ0, MQB) as controls. Every set below was written BEFORE the gate's run 3. ---
        ("MA the reserve phase fills to the reserve, not reserve + 1 -> K15 E14", T_PATH,
         "        first = min(reserve + 1 - spare, left // ball_price)\n",
         "        first = min(reserve - spare, left // ball_price)\n", {"K15", "E14"}),
        ("MB the reserve phase skips spare == reserve -> K15", T_PATH,
         "    if buy_balls and ball and ball_price and spare <= reserve:\n",
         "    if buy_balls and ball and ball_price and spare < reserve:\n", {"K15"}),
        ("MC the rest phase forgets the reserve phase's balls (overshoots TARGET) -> K16", T_PATH,
         "        rest = max(0, min(lim[\"target\"] - spare - first, left // ball_price))\n",
         "        rest = max(0, min(lim[\"target\"] - spare, left // ball_price))\n", {"K16"}),
        ("MD the rest phase ignores TRIGGER -> K16", T_PATH,
         "    if buy_balls and ball and ball_price and spare <= lim[\"trigger\"]:\n",
         "    if buy_balls and ball and ball_price:\n", {"K16"}),
        ("MX the specific cures bought ALONGSIDE Full Heal -> K17", T_PATH,
         "    else:\n        for name in (KIT_SLEEP, KIT_FREEZE):\n",
         "    if True:\n        for name in (KIT_SLEEP, KIT_FREEZE):\n", {"K17"}),
        ("MT the held view can go negative (a kit-sized buy of the basket's shortfall) -> K18", T_PATH,
         "    return {name: max(0, raw.get(name, 0) - reserved.get(name, 0)) for name in names}\n",
         "    return {name: raw.get(name, 0) - reserved.get(name, 0) for name in names}\n", {"K18"}),
        ("MU _reserve() off by one -> K19", T_PATH,
         "    return DEX_CATCH_BALL_RESERVE\n", "    return DEX_CATCH_BALL_RESERVE + 1\n", {"K19"}),
        ("MW the errand ignores what is held (buys a full kit again) -> E9", T_PATH,
         "            wants = kit_wants(kit_sold, _kit_held(), kit_hp_target())\n",
         "            wants = kit_wants(kit_sold, {}, kit_hp_target())\n", {"E9"}),
        ("MAC the key-item coupling reads the BALL flag -> E10", T_PATH,
         "        kit_skip = _kit_skip_reason(kit_mode)\n", "        kit_skip = _kit_skip_reason(flag_mode)\n", {"E10"}),
        ("ME a kit memo is ignored -> E11", T_PATH,
         "    if kit_key in failed:\n        kit_mode = \"\"\n", "", {"E11"}),
        ("MF a planning failure never memoises the kit -> E12", T_PATH,
         "        if kit_mode in (\"observe\", \"1\"):          # with the kit OFF the memo is exactly step 9a's\n"
         "            failed.add(kit_key)\n", "", {"E12"}),
        ("MPF a planning failure memoises the kit even when it is OFF -> E12", T_PATH,
         "        if kit_mode in (\"observe\", \"1\"):          # with the kit OFF the memo is exactly step 9a's\n"
         "            failed.add(kit_key)\n", "        failed.add(kit_key)\n", {"E12"}),
        ("MSF1 a planning failure logs a ball line with the balls OFF (the pass's side finding) -> E12", T_PATH,
         "        if flag_mode in (\"observe\", \"1\"):\n            _emit(log_line(\"topoff-failed\", mart=city, ball=\"-\",",
         "        if True:\n            _emit(log_line(\"topoff-failed\", mart=city, ball=\"-\",", {"E12"}),
        ("MSF2 a planning failure logs no kit line -> E12", T_PATH,
         "        if kit_mode in (\"observe\", \"1\"):\n            _emit(kit_log_line(\"kit-failed\", mart=city, kit=\"-\",",
         "        if False:\n            _emit(kit_log_line(\"kit-failed\", mart=city, kit=\"-\",", {"E12"}),
        ("MP an OBSERVE ball flag runs the phantom ball phases -> E13", T_PATH,
         "buy_balls=flag_mode == \"1\")", "buy_balls=flag_mode in (\"observe\", \"1\"))", {"E13"}),
        ("MP2 the ball phases always run -> E13", T_PATH,
         "buy_balls=flag_mode == \"1\")", "buy_balls=True)", {"E13"}),
        ("MQ an OBSERVE ball flag buys the balls -> E13", T_PATH,
         "    buy_lines = lines if flag_mode == \"1\" else []\n", "    buy_lines = lines if flag_mode else []\n", {"E13"}),
        ("MR observe never plans the kit (the line says kit=- wants=-) -> E14", T_PATH,
         "        if kit_mode in (\"observe\", \"1\") and kit_skip is None:\n",
         "        if kit_mode == \"1\" and kit_skip is None:\n", {"E14"}),
        ("MS a kit `1` with nothing to buy logs nothing -> E9 E18", T_PATH,
         "    if kit_mode in (\"observe\", \"1\") and not kit_lines:\n",
         "    if (kit_mode == \"observe\" or kit_skip) and not kit_lines:\n", {"E9", "E18"}),
        ("MO the kit's lines carry the BALL prefix -> E9 E10 E12 E14 E15 E16 E17 E18 W3", T_PATH,
         "    return (f\"[KIT-BUY] why={tag}", "    return (f\"[BALLS-BUY] why={tag}",
         {"E9", "E10", "E12", "E14", "E15", "E16", "E17", "E18", "W3"}),
        ("MFF the kit plan ignores the FAULT_FLOOR lever -> E18", T_PATH,
         "floor_money=floor_money, lim=lim, wants=wants,", "floor_money=live[\"floor\"], lim=lim, wants=wants,", {"E18"}),
        ("MG1 a close logs no kit-closed line -> E15", T_PATH,
         "        if kit_lines:\n            _emit(kit_log_line(\"kit-closed\",",
         "        if False:\n            _emit(kit_log_line(\"kit-closed\",", {"E15"}),
        ("MG2 a close does not memoise the kit -> E15", T_PATH,
         "        if kit_lines:\n            failed.add(kit_key)\n        if lines:\n            _emit(log_line(\"topoff-closed\"",
         "        if lines:\n            _emit(log_line(\"topoff-closed\"", {"E15"}),
        ("MG3 a kit-only close logs a ball line -> E15", T_PATH,
         "        if lines:\n            _emit(log_line(\"topoff-closed\"", "        if True:\n            _emit(log_line(\"topoff-closed\"",
         {"E15"}),
        ("MG4 the close handler YIELDS (close() raises) -> E15", T_PATH,
         "money_after=\"?\", reason=\"an outer bound closed the heal mid-errand\"))\n        raise\n",
         "money_after=\"?\", reason=\"an outer bound closed the heal mid-errand\"))\n            yield\n        raise\n",
         {"E15"}),
        ("MY a kit-only failure recovers silently -> E16", T_PATH,
         "        else:\n            _emit(kit_log_line(\"kit-recovery\",", "        elif False:\n            _emit(kit_log_line(\"kit-recovery\",",
         {"E16"}),
        ("MZ a kit-only failure logs a ball line -> E16", T_PATH,
         "        if lines:\n            _emit(log_line(\"topoff-failed\", mart=city, ball=ball,",
         "        if True:\n            _emit(log_line(\"topoff-failed\", mart=city, ball=ball,", {"E16"}),
        ("MI `finished` unset when the walk raises -> E16", T_PATH, "    finished = False\n", "", {"E16"}),
        ("MH a walk not back on the exit tile counts as ok -> E16", T_PATH,
         "        walk_failed = not finished or \"error\" in report or not report.get(\"returned\", False)\n",
         "        walk_failed = not finished or \"error\" in report\n", {"E16"}),
        ("MV2 an unstable exit logs no kit line -> E17", T_PATH,
         "        if kit_mode in (\"observe\", \"1\"):\n            _emit(kit_log_line(\"kit-skip\", mart=city, kit=\"-\"",
         "        if False:\n            _emit(kit_log_line(\"kit-skip\", mart=city, kit=\"-\"", {"E17"}),
        ("MV3 an unstable exit logs a ball line with the balls OFF -> E17", T_PATH,
         "        if flag_mode in (\"observe\", \"1\"):\n            _emit(log_line(\"topoff-skip\",",
         "        if True:\n            _emit(log_line(\"topoff-skip\",", {"E17"}),
        ("MJ a kit-only walk reads as 'sells none' -> W3 W5", T_PATH,
         "    if not lines and not kit_lines:\n        report[\"why\"] = f\"the live list sells none",
         "    if not lines:\n        report[\"why\"] = f\"the live list sells none", {"W3", "W5"}),
        ("MM a kit-only walk never sets balls_ok (KeyError) -> W3", T_PATH,
         "    else:\n        report[\"bought\"], report[\"premier\"], report[\"balls_ok\"] = 0, 0, True\n", "", {"W3"}),
        ("MN a kit-only success logs a ball line -> W3", T_PATH,
         "        if planned_lines:\n            _emit(log_line(\"topoff\", mart=exit_map_name(mart_map)",
         "        if True:\n            _emit(log_line(\"topoff\", mart=exit_map_name(mart_map)", {"W3"}),
        ("ML the kit verified by the COUNT, not the delta -> W3", T_PATH,
         "    report[\"kit_got\"] = {name: after[name] - before[name] for name in kit_want}\n",
         "    report[\"kit_got\"] = {name: after[name] for name in kit_want}\n", {"W3"}),
        ("MK the kit line not filtered by the live list -> W4", T_PATH,
         "    kit_lines = [(n, q) for n, q in kit_lines if n in sold]\n", "", {"W4"}),
        ("MVK the kit verified against the FILTERED lines (a dropped line reads ok) -> W4", T_PATH,
         "    for name, qty in planned_kit:\n", "    for name, qty in kit_lines:\n", {"W4"}),
        ("MVB the balls verified against the FILTERED lines (a dropped line reads ok) -> W5", T_PATH,
         "    ball = planned_lines[0][0] if planned_lines else None\n    if planned_lines:\n",
         "    ball = lines[0][0] if lines else None\n    if lines:\n", {"W5"}),
        ("MQ0 (control) a zero-quantity kit line -> K8b K9 K16 E18", T_PATH,
         "        if qty > 0:\n", "        if qty >= 0:\n", {"K8b", "K9", "K16", "E18"}),
        ("MQB (control) the kit ignores the budget -> K8b K9 K11 K15 E13 E18", T_PATH,
         "        qty = min(want, left // prices[name])\n", "        qty = want\n",
         {"K8b", "K9", "K11", "K15", "E13", "E18"}),
        ("MW1 a kit-flag typo is not reported -> A2", H_PATH,
         "    if _kit_error:\n        _piggyback_report(\"the healing-kit top-off\", _kit_error, console_too=True)\n", "",
         {"A2"}),
        ("MW4 a kit-flag typo reported under the BALL's name -> A2", H_PATH,
         "_piggyback_report(\"the healing-kit top-off\", _kit_error", "_piggyback_report(\"the ball top-off\", _kit_error",
         {"A2"}),
        ("MW2 the errand is not passed kit_mode -> A3", H_PATH, "kit_mode=_kit_mode)", ")", {"A3"}),
        ("MW3 the guard runs on the BALL flag only -> A3", H_PATH,
         " or _kit_mode in (\"observe\", \"1\"):", ":", {"A3"}),
        ("N2 the kit hunk's names in a heal COMMENT turn NOTHING red", H_PATH,
         "        _topoff_moved = False\n",
         "        # (edited) if _kit_error: _piggyback_report(\"kit\", _kit_error); kit_mode=_kit_mode, a comment only\n"
         "        _topoff_moved = False\n", set()),
        ("N3 a comment in stock_topoff turns NOTHING red", T_PATH,
         "def kit_hp_target() -> int:\n",
         "# (edited) kit_mode = \"1\"; planned_kit; failed.add(kit_key), named in a comment only\n"
         "def kit_hp_target() -> int:\n", set()),
    ]
    real = sys.modules[T_NAME]
    for i, (label, path, old, new, want) in enumerate(cases):
        src = path.read_text(encoding="utf-8")
        try:
            n = src.count(old)
            if n != 1:
                raise AssertionError(f"mutant anchor found {n} times: {old[:70]!r}")
            msrc = src.replace(old, new)
            if path == T_PATH:
                mod = types.ModuleType(T_NAME)
                mod.__file__ = str(path)
                mod.__package__ = "modules.story"
                sys.modules[T_NAME] = mod
                exec(compile(msrc, f"<mutant {i}>", "exec"), mod.__dict__)
            red = all_rows(msrc if path == H_PATH else hsrc, "m")
            check(label, red == want, f"red {sorted(red)}" + ("" if red == want else f" (want {sorted(want)})"))
        except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
            check(label, False, f"{type(error).__name__}: {error}")
        finally:
            sys.modules[T_NAME] = real

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
