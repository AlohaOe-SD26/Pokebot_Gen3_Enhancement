"""GATE — USER RULINGS 23 + 26, design v2 step 9a (BB): the ball top-off (`modules/story/stock_topoff.py`) and its
piggyback on `heal_in_pokemon_center` (`modules/modes/util/higher_level_actions.py`, an UPSTREAM-derived file).

WHY. The top-off spends money on every eligible heal, so the ways it can hurt are: spending below a floor (RULING 18's
League basket), a stage guessed low when a flag read fails, a negative or over-max quantity (`buy_in_shop` raises on
one and never ends on the other), and — because it rides an upstream heal every chapter uses — changing an OFF heal at
all, or ending a heal off its exit tile. Each has rows here.

ROWS
  L1-L9   PURE: the limits (and that they come from the source constants), `best_ball`, `stage` (order and fail-closed),
          `floor`, `ball_topoff_plan` (below-floor, the fault floors, fail-closed), `plan_lines` (Premier-preserving
          merge), the hysteresis bound (L7, L7b), `parse_flag`, and L9: the in-game-max invariant over a grid (no clamp is
          written for it, because it cannot bind; the step 9a review found the old clamp dead and its row mislabelled).
  A1-A6   the heal's three hunks by AST (the flag parsed before the first yield; the errand inside the flag branch with an
          abort-aware loud handler, given `stable >= 20`; the second stable wait ONLY under `_topoff_moved`), the
          whitelist (Rustboro only), the memo reset per run, and no `buy_poke_balls*` in the errand.
  E1      the errand EXECUTED with stubs: OFF, a non-story mode, a non-whitelisted city, a failed city, an unstable exit
          and `observe` all return False with ZERO yields; `observe` and an empty plan log one line each.
  E2      the errand's ACTION path EXECUTED with a stub walk, a stub recovery and a fake frame counter (the review: seven
          mutants of this path were invisible): success; a short bag delta; not back on the exit tile; the bound expiring;
          the walk raising; an abort (re-raised); an OUTER close mid-errand (logged + memoised); planning raising.
  E3      `_inputs` EXECUTED with a flag missing from the event-flag table: the stage fails CLOSED (None), not MID.
  E4      `_walk_buy_return` EXECUTED with every emulator call stubbed and a fake avatar that the stub walks MOVE: a
          planned delta is ok and back on the exit tile facing Down; a short delta is not ok.
  M1-M20  source mutants, each with the EXACT set of rows it must turn red; N1 a comment-only edit (none red).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_stock_topoff.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import pathlib
import sys
import types
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
T_PATH = SANDBOX / "modules" / "story" / "stock_topoff.py"
H_PATH = SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py"
SM_PATH = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"

import modules.story.stock_topoff as T  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


PRICES = {"Poké Ball": 200, "Great Ball": 600, "Ultra Ball": 1200, "Timer Ball": 1000, "Repeat Ball": 1000,
          "Nest Ball": 1000, "Net Ball": 1000, "Dive Ball": 1000}
ALL = set(PRICES)


def l_rows(t, tag=""):
    failed: list[str] = []

    def row(key, label, ok, detail=""):
        if not ok:
            failed.append(key)
        if not tag:
            check(f"{key} {label}", ok, detail)

    lim = t.limits()
    from modules.story.early_game import MAX_BALLS_PER_TRIP, POKE_BALL_PRICE
    from plugins.custom_modes.story_mode import DEX_CATCH_BALL_RESERVE, DEX_CATCH_MAX_EXPECTED_THROWS

    row("L1", "limits = trigger 20 / target 30 / batch cap 6000, from the source constants",
        lim == {"trigger": DEX_CATCH_BALL_RESERVE + DEX_CATCH_MAX_EXPECTED_THROWS, "target": MAX_BALLS_PER_TRIP,
                "batch_cap": MAX_BALLS_PER_TRIP * POKE_BALL_PRICE} == {"trigger": 20, "target": 30, "batch_cap": 6000},
        str(lim))
    bb = [t.best_ball(["Poké Ball"], ALL, PRICES), t.best_ball(["Poké Ball", "Great Ball"], ALL, PRICES),
          t.best_ball(["Great Ball", "Ultra Ball"], ALL, PRICES),
          t.best_ball(["Poké Ball", "Timer Ball", "Repeat Ball"], ALL, PRICES),
          t.best_ball(["Great Ball", "Nest Ball"], ALL, PRICES),
          t.best_ball(["Great Ball", "Ultra Ball"], ALL - {"Ultra Ball"}, PRICES),
          t.best_ball(["Poké Ball"], set(), PRICES)]
    row("L2", "best_ball: Poké; Great; Ultra; Rustboro-expanded -> Poké (tie, cheapest); Verdanturf -> Great; Ultra "
        "disallowed -> Great; nothing allowed -> None",
        bb == ["Poké Ball", "Great Ball", "Ultra Ball", "Poké Ball", "Great Ball", "Great Ball", None], str(bb))
    f = dict(champion=False, entered_e4=False, reserve_era=False, badge1=True)
    st = [t.stage(f), t.stage(dict(f, badge1=False)), t.stage(dict(f, reserve_era=True)),
          t.stage(dict(f, reserve_era=True, entered_e4=True)),
          t.stage(dict(f, entered_e4=True, champion=True)), t.stage({"badge1": True})]
    row("L3", "stage: MID, PRE_GYM1, BASKET_ERA, LEAGUE, POSTGAME in priority order; a missing flag -> None (fail closed)",
        st == ["MID", "PRE_GYM1", "BASKET_ERA", "LEAGUE", "POSTGAME", None], str(st))
    fl = [t.floor("MID", None), t.floor("POSTGAME", None), t.floor("BASKET_ERA", 54300), t.floor("LEAGUE", 0),
          t.floor("BASKET_ERA", None), t.floor("PRE_GYM1", 0), t.floor(None, 0)]
    row("L4", "floor: MID/POSTGAME 1000; BASKET_ERA 1000 + 2x missing; LEAGUE likewise; unreadable -> None",
        fl == [1000, 1000, 109600, 1000, None, None, None], str(fl))

    def plan(**kw):
        base = dict(spare=7, money=9940, ball="Poké Ball", price=200, stage_name="MID", floor_money=1000, lim=lim)
        base.update(kw)
        return t.ball_topoff_plan(**base)

    cases = {
        "A1 case": (plan(), [("Poké Ball", 10), ("Poké Ball", 12)], "top off 22"),
        "control": (plan(spare=27), [], "spare 27 > trigger 20"),
        "fault floor 9600": (plan(floor_money=9600), [], "cannot afford"),
        "fault floor 8940": (plan(floor_money=8940), [("Poké Ball", 2)], "top off 2"),
        "below floor": (plan(money=500, stage_name="BASKET_ERA", floor_money=109600), [], "at or below the floor"),
        "stage unreadable": (plan(stage_name=None), [], "stage unreadable"),
        "pre gym 1": (plan(stage_name="PRE_GYM1"), [], "before gym 1"),
        "no ball": (plan(ball=None, price=None), [], "no allowed ball"),
        "Great 10": (plan(spare=0, money=20000, ball="Great Ball", price=600), [("Great Ball", 10)], "top off 10"),
        "budget binds": (plan(spare=0, money=1100, floor_money=0), [("Poké Ball", 2)], "top off 2"),
    }
    bad = {k: (got, want) for k, (got, want, why) in cases.items() if got[0] != want or why not in got[1]}
    row("L5", "ball_topoff_plan over 10 literal cases (the A1 case, the control, both fault floors, below the floor, "
        "fail-closed, no ball, Great, the budget binding)", not bad, str(bad) if bad else "")
    pl = [t.plan_lines("Poké Ball", 22), t.plan_lines("Poké Ball", 30), t.plan_lines("Poké Ball", 7),
          t.plan_lines("Poké Ball", 10), t.plan_lines("Great Ball", 12), t.plan_lines("Poké Ball", 0)]
    row("L6", "plan_lines: 22 -> 10+12 (2 Premiers, no ball dropped); 30 -> 3x10; 7; 10; Great 12 in one line; 0 -> []",
        pl == [[("Poké Ball", 10), ("Poké Ball", 12)], [("Poké Ball", 10)] * 3, [("Poké Ball", 7)],
               [("Poké Ball", 10)], [("Great Ball", 12)], []], str(pl))
    def visits(ball, price, spare):
        """How many successive heals (money to spare) until spare is ABOVE the trigger."""
        n = 0
        while spare <= lim["trigger"] and n < 50:
            lines, _ = t.ball_topoff_plan(spare=spare, money=999_999, ball=ball, price=price, stage_name="MID",
                                          floor_money=1000, lim=lim)
            if not lines:
                break
            spare += sum(q for _, q in lines) + sum(1 for n_, q in lines if n_ == "Poké Ball" and q >= 10)
            n += 1
        return n

    poke = [visits("Poké Ball", 200, s) for s in range(0, lim["trigger"] + 1)]
    row("L7", "hysteresis for the Poké Ball (the ONLY ball step 9a buys): with money to spare, ONE purchase from any "
        "spare 0..20 ends above the trigger", poke == [1] * (lim["trigger"] + 1), str(poke))
    # ⚠ FOUND BUILDING THIS ROW: the ₽6,000 batch cap buys at most 10 Great or 5 Ultra, so those need MORE than one visit
    # from a low spare (the recon's "for Great/Ultra the result is 30" assumed the cap did not bind). Pinned, not hidden:
    # it matters from step 9b (the first Great/Ultra city), and it is the user's Q1 to weigh.
    gu = (visits("Great Ball", 600, 0), visits("Ultra Ball", 1200, 0), visits("Ultra Ball", 1200, 20))
    row("L7b", "from spare 0 the Great Ball takes 3 visits and the Ultra Ball 5 (the ₽6,000 cap binds); from 20, one",
        gu == (3, 5, 1), str(gu))
    pf = [t.parse_flag(None), t.parse_flag(""), t.parse_flag("0"), t.parse_flag("observe"), t.parse_flag("1"),
          t.parse_flag("yes")]
    row("L8", "parse_flag: unset/''/0 -> OFF; observe; 1; a typo -> OFF WITH an error",
        [p[0] for p in pf] == ["", "", "", "observe", "1", ""] and [p[1] is None for p in pf] == [True] * 5 + [False],
        str(pf))
    over = []
    for money in (0, 1, 199, 200, 1000, 1001, 2500, 9940, 20000, 999_999):
        for floor_money in (0, 1000, 9600, 109_600):
            for spare in (0, 7, 20):
                for ball, price in (("Poké Ball", 200), ("Great Ball", 600), ("Ultra Ball", 1200)):
                    lines, _ = t.ball_topoff_plan(spare=spare, money=money, ball=ball, price=price, stage_name="MID",
                                                  floor_money=floor_money, lim=lim)
                    total = sum(q for _, q in lines) * price
                    if any(q > min(money // price, 99) for _, q in lines) or total > money:
                        over.append((money, floor_money, spare, ball, lines))
    row("L9", "the in-game max per line, min(money // price, 99), and the total cost never exceed what the formula "
        "allows, over a 360-case grid (so no clamp is needed; the old one was dead)", not over, str(over[:3]))
    return failed


def a_rows(hsrc, tsrc, smsrc, tag=""):
    failed: list[str] = []

    def row(key, label, ok, detail=""):
        if not ok:
            failed.append(key)
        if not tag:
            check(f"{key} {label}", ok, detail)

    tree = ast.parse(hsrc)
    heal = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "heal_in_pokemon_center"), None)
    yields = sorted(n.lineno for n in ast.walk(heal) if isinstance(n, (ast.Yield, ast.YieldFrom))) if heal else []
    parse = [n for n in ast.walk(heal) if isinstance(n, ast.Assign) and "_topoff_mode" in ast.unparse(n.targets[0])] if heal else []
    row("A1", "the heal parses POKEBOT_R23_BALLRESTOCK before its FIRST yield",
        len(parse) == 1 and yields and parse[0].lineno < yields[0]
        and "POKEBOT_R23_BALLRESTOCK" in ast.unparse(parse[0].value), f"parse@{parse[0].lineno if parse else None} "
        f"first yield@{yields[0] if yields else None}")
    ifs = [n for n in ast.walk(heal) if isinstance(n, ast.If)] if heal else []
    # Step 10a widened the guard to the kit's flag too (`_kit_mode`, parsed next to the ball flag) and passes it on.
    branch = [n for n in ifs if ast.unparse(n.test)
              == "_topoff_mode in ('observe', '1') or _kit_mode in ('observe', '1')"]
    ok2 = False
    if len(branch) == 1:
        body = ast.unparse(branch[0])
        tries = [n for n in ast.walk(branch[0]) if isinstance(n, ast.Try)]
        handler = tries[0].handlers[0] if tries and tries[0].handlers else None
        hsrc_h = ast.unparse(handler) if handler else ""
        ok2 = ("ball_topoff_errand(pokemon_center_door_location, _topoff_mode, stable >= 20, kit_mode=_kit_mode)"
               in body and handler is not None and ast.unparse(handler.type) == "Exception"
               and hsrc_h.index("reraise_if_aborting(error)") < hsrc_h.index("_piggyback_report("))
    row("A2", "the errand runs ONLY inside `if _topoff_mode in (…) or _kit_mode in (…)`, given `stable >= 20`, under "
        "an `except Exception` that re-raises an abort FIRST and then reports", ok2)
    waits = [n for n in ast.walk(heal) if isinstance(n, ast.While) and ast.unparse(n.test) == "stable < 20 and waited < 300"] if heal else []
    guarded = [n for n in ifs if ast.unparse(n.test) == "_topoff_moved"]
    inside = [w for w in waits for g in guarded if any(w is x for x in ast.walk(g))]
    row("A3", "the SECOND stable wait sits inside `if _topoff_moved:` (an unconditional copy would change every OFF heal)",
        len(waits) == 2 and len(guarded) == 1 and len(inside) == 1, f"waits={len(waits)} guarded={len(inside)}")
    wl = [n for n in ast.walk(ast.parse(tsrc)) if isinstance(n, ast.FunctionDef) and n.name == "_whitelist"]
    ret = [ast.unparse(n.value) for n in ast.walk(wl[0]) if isinstance(n, ast.Return)] if wl else []
    row("A4", "the whitelist is Rustboro ONLY (never Sootopolis or the League in step 9a)",
        ret == ["{PokemonCenter.RustboroCity: RUSTBORO_MART}"], str(ret))
    reset = next((n for n in ast.walk(ast.parse(smsrc)) if isinstance(n, ast.FunctionDef) and n.name == "reset_per_run_state"), None)
    row("A5", "the failed-walk memo is reset per run in StoryMode.reset_per_run_state",
        reset is not None and "self._ball_topoff_failed: set = set()" in ast.get_source_segment(smsrc, reset))
    names = {n.id for n in ast.walk(ast.parse(tsrc)) if isinstance(n, ast.Name)} | \
            {n.attr for n in ast.walk(ast.parse(tsrc)) if isinstance(n, ast.Attribute)}
    row("A6", "the errand buys only through `buy_in_shop`, never `buy_poke_balls`/`buy_poke_balls_in_tens`",
        "buy_in_shop" in names and not ({"buy_poke_balls", "buy_poke_balls_in_tens"} & names))
    return failed


def e_rows(t, tag=""):
    """E1: execute the errand with stubs and count its yields."""
    failed: list[str] = []
    from modules.context import context
    from modules.map_data import PokemonCenter
    from plugins.custom_modes.story_mode import StoryMode

    emitted: list = []
    saved = (t._emit, t._inputs, t._allowed, getattr(context, "bot_mode_instance", None))
    t._emit = lambda line: emitted.append(line)
    t._allowed = lambda: {"Poké Ball"}

    def inputs(spare):
        return lambda mode: {"stage": "MID", "floor": 1000, "spare": spare, "money": 9940, "flags": {},
                             "price_of": lambda n: PRICES[n]}

    def drive(mode_obj, center, flag, stable=True, spare=7):
        t._inputs = inputs(spare)
        context.bot_mode_instance = mode_obj
        emitted.clear()
        gen = t.ball_topoff_errand(center, flag, stable)
        try:
            next(gen)
            return "YIELDED", list(emitted)
        except StopIteration as stop:
            return stop.value, list(emitted)
        except Exception as error:  # noqa: BLE001 - a raise here means the errand went past a precondition (a red row)
            return f"RAISED {type(error).__name__}", list(emitted)

    story = StoryMode.__new__(StoryMode)
    story._ball_topoff_failed = set()
    failed_city = StoryMode.__new__(StoryMode)
    failed_city._ball_topoff_failed = {"RustboroCity"}
    try:
        runs = {
            "off": drive(story, PokemonCenter.RustboroCity, ""),
            "not story": drive(SimpleNamespace(), PokemonCenter.RustboroCity, "1"),
            "not whitelisted": drive(story, PokemonCenter.SootopolisCity, "1"),
            "failed city": drive(failed_city, PokemonCenter.RustboroCity, "1"),
            "unstable exit": drive(story, PokemonCenter.RustboroCity, "1", stable=False),
            "observe": drive(story, PokemonCenter.RustboroCity, "observe"),
            "empty plan": drive(story, PokemonCenter.RustboroCity, "1", spare=27),
        }
    finally:
        t._emit, t._inputs, t._allowed = saved[0], saved[1], saved[2]
        context.bot_mode_instance = saved[3]
    quiet = all(r[0] is False for r in runs.values())
    lines_ok = (runs["off"][1] == [] and runs["not story"][1] == [] and runs["not whitelisted"][1] == []
                and runs["failed city"][1] == [] and len(runs["unstable exit"][1]) == 1
                and "why=topoff-skip" in runs["unstable exit"][1][0]
                and len(runs["observe"][1]) == 1 and "why=topoff-observe" in runs["observe"][1][0]
                and "top off 22 x Poké Ball" in runs["observe"][1][0]
                and len(runs["empty plan"][1]) == 1 and "why=topoff-none" in runs["empty plan"][1][0])
    ok = quiet and lines_ok
    if not ok:
        failed.append("E1")
    if not tag:
        check("E1 the errand, EXECUTED: OFF / not Story / not whitelisted / failed city / unstable exit / observe / "
              "empty plan each return False with ZERO yields; the last three log one named line each", ok,
              "" if ok else str({k: (v[0], [x[:60] for x in v[1]]) for k, v in runs.items()}))
    return failed


class _Abort(Exception):
    """Stands for the story abort `reraise_if_aborting` re-raises."""


def e2_rows(t, tag=""):
    """E2: the errand's ACTION path, executed with a stub walk, a stub recovery and a fake frame counter."""
    failed: list[str] = []
    from modules import player as _player
    from modules.context import context
    from modules.map_data import PokemonCenter
    from modules.story import early_game as _eg
    from plugins.custom_modes.story_mode import StoryMode

    frames = [0]
    calls = {"recover": 0}
    emitted: list = []

    def fake_walk(kind):
        def walk(mart, exit_map, exit_tile, lines, live, reason, report, **_kit):   # step 10a: kit_lines/kit_reason
            if kind == "loop":
                for _ in range(200):          # a bound that is IGNORED hits this cap and raises instead of hanging
                    frames[0] += 100
                    yield
                raise RuntimeError("UNBOUNDED: the errand's frame bound never fired")
            frames[0] += 100
            yield
            if kind == "raise":
                raise RuntimeError("walk failed")
            if kind == "abort":
                raise RuntimeError("ABORT")
            frames[0] += 100
            yield
            report.update({"bought": 22, "premier": 2, "spare_after": 31, "money_after": 5540,
                           "ok": kind != "short", "returned": kind != "notback"})
            if kind == "short":
                report["why"] = "bag delta 20 != planned 22"
        return walk

    def fake_recover(exit_map, exit_tile, report):
        calls["recover"] += 1
        frames[0] += 100
        yield
        report["recovered_on_exit"] = True

    def reraise(error):
        if "ABORT" in str(error):
            raise _Abort(str(error))

    saved = [(t, "_emit", t._emit), (t, "_inputs", t._inputs), (t, "_allowed", t._allowed),
             (t, "_walk_buy_return", t._walk_buy_return), (t, "_recover", t._recover),
             (_player, "get_player_avatar", _player.get_player_avatar), (_eg, "reraise_if_aborting", _eg.reraise_if_aborting),
             (context, "bot_mode_instance", getattr(context, "bot_mode_instance", None)),
             (context, "emulator", getattr(context, "emulator", None))]
    import os as _os
    saved_env = _os.environ.get("POKEBOT_R23_FAULT_ERRANDFRAMES")
    results = {}
    try:
        t._emit = lambda line: emitted.append(line)
        t._allowed = lambda: {"Poké Ball"}
        t._recover = fake_recover
        _player.get_player_avatar = lambda: SimpleNamespace(map_group_and_number=(0, 3), local_coordinates=(16, 39))
        _eg.reraise_if_aborting = reraise
        context.emulator = SimpleNamespace(get_frame_count=lambda: frames[0], press_button=lambda b: None)
        good_inputs = lambda mode: {"stage": "MID", "floor": 1000, "spare": 7, "money": 9940, "flags": {},  # noqa: E731
                                    "price_of": lambda n: PRICES[n]}

        def run(kind, inputs=good_inputs, close_after_first=False, bound=None):
            story = StoryMode.__new__(StoryMode)
            story._ball_topoff_failed = set()
            context.bot_mode_instance = story
            t._inputs = inputs
            t._walk_buy_return = fake_walk(kind)
            if bound is None:
                _os.environ.pop("POKEBOT_R23_FAULT_ERRANDFRAMES", None)
            else:
                _os.environ["POKEBOT_R23_FAULT_ERRANDFRAMES"] = str(bound)
            emitted.clear()
            calls["recover"] = 0
            gen = t.ball_topoff_errand(PokemonCenter.RustboroCity, "1", True)
            out = None
            try:
                steps = 0
                next(gen)
                steps += 1
                if close_after_first:
                    gen.close()
                    out = "CLOSED"
                else:
                    while steps < 1000:
                        next(gen)
                        steps += 1
            except StopIteration as stop:
                out = stop.value
            except _Abort:
                out = "ABORT"
            except Exception as error:  # noqa: BLE001 - a raise out of the errand is a red row, reported
                out = f"RAISED {type(error).__name__}: {error}"
            return out, sorted(story._ball_topoff_failed), list(emitted), calls["recover"]

        def planning_raises(mode):
            raise RuntimeError("inputs failed")

        results = {
            "E2a": run("ok"),
            "E2b": run("short"),
            "E2c": run("notback"),
            "E2d": run("loop", bound=250),
            "E2e": run("raise"),
            "E2f": run("abort"),
            "E2g": run("ok", close_after_first=True),
        }
        # E2h: planning raises BEFORE anything moves (no yield at all)
        story = StoryMode.__new__(StoryMode)
        story._ball_topoff_failed = set()
        context.bot_mode_instance = story
        t._inputs = planning_raises
        emitted.clear()
        gen = t.ball_topoff_errand(PokemonCenter.RustboroCity, "1", True)
        try:
            next(gen)
            results["E2h"] = ("YIELDED", sorted(story._ball_topoff_failed), list(emitted), 0)
        except StopIteration as stop:
            results["E2h"] = (stop.value, sorted(story._ball_topoff_failed), list(emitted), 0)
        except Exception as error:  # noqa: BLE001 - a raise out of the errand is a red row, reported
            results["E2h"] = (f"RAISED {type(error).__name__}", sorted(story._ball_topoff_failed), list(emitted), 0)
    finally:
        for obj, name, value in saved:
            setattr(obj, name, value)
        if saved_env is None:
            _os.environ.pop("POKEBOT_R23_FAULT_ERRANDFRAMES", None)
        else:
            _os.environ["POKEBOT_R23_FAULT_ERRANDFRAMES"] = saved_env

    def has(lines, needle):
        return any(needle in line for line in lines)

    R = "RustboroCity"
    expect = {
        "E2a": lambda r: r[0] is True and r[1] == [] and r[3] == 0 and not has(r[2], "topoff-failed"),
        "E2b": lambda r: r[0] is True and r[1] == [R] and r[3] == 1 and has(r[2], "reason=bag delta 20 != planned 22")
        and has(r[2], "why=topoff-recovery"),
        "E2c": lambda r: r[0] is True and r[1] == [R] and r[3] == 1 and has(r[2], "reason=not back on the exit tile"),
        "E2d": lambda r: r[0] is True and r[1] == [R] and r[3] == 1 and has(r[2], "reason=the errand's frame bound expired"),
        "E2e": lambda r: r[0] is True and r[1] == [R] and r[3] == 1 and has(r[2], "walk failed"),
        "E2f": lambda r: r[0] == "ABORT",
        "E2g": lambda r: r[0] == "CLOSED" and r[1] == [R] and has(r[2], "why=topoff-closed"),
        "E2h": lambda r: r[0] is False and r[1] == [R] and has(r[2], "planning raised"),
    }
    labels = {
        "E2a": "success: moved (True), no memo, no recovery",
        "E2b": "a short bag delta: memoised, logged with its reason, recovered (and the recovery logged)",
        "E2c": "bought but not back on the exit tile: memoised, logged, recovered",
        "E2d": "the frame bound expires: memoised, logged, recovered",
        "E2e": "the walk raises: memoised, logged, recovered",
        "E2f": "an abort is RE-RAISED, never swallowed",
        "E2g": "an OUTER close mid-errand: logged `topoff-closed` and memoised",
        "E2h": "planning raises: NOT moved (False), memoised, logged, zero yields",
    }
    for key in sorted(expect):
        ok = key in results and expect[key](results[key])
        if not ok:
            failed.append(key)
        if not tag:
            r = results.get(key)
            check(f"{key} {labels[key]}", ok, "" if ok else f"got {(r[0], r[1], [x[:70] for x in r[2]], r[3]) if r else None}")
    return failed


def e3_rows(t, tag=""):
    """E3: `_inputs` with a flag missing from the event-flag table must fail closed (stage None), not guess MID."""
    failed: list[str] = []
    import modules.items as _items
    import modules.memory as _memory
    import modules.player as _player

    names = t.flag_names()
    saved = [(_memory, "_event_flags", _memory._event_flags), (_memory, "get_event_flag", _memory.get_event_flag),
             (_items, "get_item_bag", _items.get_item_bag), (_items, "get_item_by_name", _items.get_item_by_name),
             (_player, "get_player", _player.get_player)]
    try:
        _memory.get_event_flag = lambda name: name == names["badge1"]
        _items.get_item_bag = lambda: SimpleNamespace(number_of_balls_except_master_ball=7)
        _items.get_item_by_name = lambda n: SimpleNamespace(name=n, price=PRICES.get(n, 200))
        _player.get_player = lambda: SimpleNamespace(money=9940)
        _memory._event_flags = {n: 0 for n in names.values()}
        full = t._inputs(None)["stage"]
        _memory._event_flags = {n: 0 for k, n in names.items() if k != "champion"}
        missing = t._inputs(None)["stage"]
    finally:
        for obj, name, value in saved:
            setattr(obj, name, value)
    ok = (full, missing) == ("MID", None)
    if not ok:
        failed.append("E3")
    if not tag:
        check("E3 `_inputs`: every flag in the table -> MID; one flag missing from the table -> stage None (fail closed)",
              ok, f"{(full, missing)}")
    return failed


def e4_rows(t, tag=""):
    """E4: `_walk_buy_return` with every emulator call stubbed; the stub walks MOVE a fake avatar."""
    failed: list[str] = []
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

    state = {}

    def nav(dest_map, dest_tile, **_kw):
        state["map"] = tuple(dest_map.value)
        state["tile"] = tuple(dest_tile)
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
            state["bag"][item.name] = state["bag"].get(item.name, 0) + qty - state["short_by"]
            state["short_by"] = 0
            if item.name == "Poké Ball" and qty >= 10:
                state["bag"]["Premier Ball"] = state["bag"].get("Premier Ball", 0) + 1
        yield

    class Bag:
        def quantity_of(self, item):
            return state["bag"].get(item.name, 0)

        @property
        def number_of_balls_except_master_ball(self):
            return sum(state["bag"].values())

    saved = [(_eg, "_navigate_riding_out", _eg._navigate_riding_out),
             (_eg, "wait_until_truly_controllable", _eg.wait_until_truly_controllable),
             (_eg, "_check_abort", _eg._check_abort), (_walking, "ensure_facing_direction", _walking.ensure_facing_direction),
             (_ts, "task_is_active", _ts.task_is_active), (_mart, "get_mart_buyable_items", _mart.get_mart_buyable_items),
             (_hla, "buy_in_shop", _hla.buy_in_shop), (_lr, "_close_shop_and_dialogs", _lr._close_shop_and_dialogs),
             (_items, "get_item_bag", _items.get_item_bag), (_items, "get_item_by_name", _items.get_item_by_name),
             (_player, "get_player", _player.get_player), (_player, "get_player_avatar", _player.get_player_avatar),
             (_util, "wait_for_n_frames", _util.wait_for_n_frames), (t, "_emit", t._emit),
             (context, "emulator", getattr(context, "emulator", None))]
    results = {}
    try:
        _eg._navigate_riding_out = nav
        _eg.wait_until_truly_controllable = one
        _eg._check_abort = lambda: None
        _walking.ensure_facing_direction = face
        _ts.task_is_active = lambda name: bool(state.get("menu")) and name == "Task_ShopMenu"
        _mart.get_mart_buyable_items = lambda: [SimpleNamespace(name="Poké Ball")]
        _hla.buy_in_shop = buy
        _lr._close_shop_and_dialogs = lambda report: one()
        _items.get_item_bag = lambda: Bag()
        _items.get_item_by_name = lambda n: SimpleNamespace(name=n, price=PRICES.get(n, 200))
        _player.get_player = lambda: SimpleNamespace(money=9940 - 4400)
        _player.get_player_avatar = lambda: SimpleNamespace(map_group_and_number=state["map"],
                                                            local_coordinates=state["tile"],
                                                            facing_direction=state["facing"])
        _util.wait_for_n_frames = lambda n: one()
        t._emit = lambda line: state["emitted"].append(line)
        context.emulator = SimpleNamespace(press_button=press, get_frame_count=lambda: 0)
        for key, short_by in (("E4a", 0), ("E4b", 2)):
            state.clear()
            state.update({"map": (0, 3), "tile": (16, 39), "facing": "Down", "menu": False,
                          "bag": {"Poké Ball": 7}, "short_by": short_by, "emitted": []})
            report: dict = {}
            gen = t._walk_buy_return((MapRSE.RUSTBORO_CITY_MART, (3, 3), "Left"), MapRSE.RUSTBORO_CITY, (16, 39),
                                     [("Poké Ball", 10), ("Poké Ball", 12)], {"spare": 7, "money": 9940}, "r", report)
            for _ in range(500):
                try:
                    next(gen)
                except StopIteration:
                    break
                except Exception as error:  # noqa: BLE001 - a raise is recorded as the row's reading (a red row)
                    report["raised"] = repr(error)
                    break
            results[key] = (dict(report), list(state["emitted"]), dict(state))
    finally:
        for obj, name, value in saved:
            setattr(obj, name, value)
    a, b = results.get("E4a"), results.get("E4b")
    ok_a = (a is not None and a[0].get("ok") is True and a[0].get("returned") is True and a[0].get("bought") == 22
            and a[0].get("premier") == 2 and a[2]["tile"] == (16, 39) and a[2]["facing"] == "Down"
            and any("why=topoff " in line for line in a[1]))
    ok_b = (b is not None and b[0].get("ok") is False and "bag delta 20 != planned 22" in b[0].get("why", ""))
    for key, ok, label, got in (("E4a", ok_a, "a planned delta: ok, bought 22 + 2 Premier, back on (16,39) facing Down, "
                                 "one `why=topoff` line", a), ("E4b", ok_b, "a delta 2 short: NOT ok, with its reason", b)):
        if not ok:
            failed.append(key)
        if not tag:
            check(f"{key} `_walk_buy_return` executed: {label}", ok, "" if ok else f"got {got[0] if got else None}")
    return failed


def mutant_module(path, name, old, new, modname):
    src = path.read_text(encoding="utf-8")
    n = src.count(old)
    if n != 1:
        raise AssertionError(f"mutant anchor for {name!r} found {n} times: {old!r}")
    msrc = src.replace(old, new)
    mod = types.ModuleType(modname)
    mod.__file__ = str(path)
    sys.modules[modname] = mod
    exec(compile(msrc, f"<mutant {name}>", "exec"), mod.__dict__)
    return mod, msrc


def main() -> int:
    hsrc = H_PATH.read_text(encoding="utf-8")
    tsrc = T_PATH.read_text(encoding="utf-8")
    smsrc = SM_PATH.read_text(encoding="utf-8")
    print("L — pure planning")
    l_rows(T)
    print("\nA — the heal's hunks, the whitelist, the memo")
    a_rows(hsrc, tsrc, smsrc)
    print("\nE — the errand, executed with stubs")
    e_rows(T)
    e2_rows(T)
    e3_rows(T)
    e4_rows(T)

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    cases = [
        # (label, file, anchor, replacement, expected red set)
        ("M1 the second stable wait made unconditional -> A3", H_PATH,
         "        if _topoff_moved:\n", "        if True:  # _topoff_moved\n", {"A3"}),
        # ⚠ Step 10a moved the anchors of M2, M9, M10, M12 and M15 (the kit rides the errand); their RED SETS are
        # unchanged from step 9a's and must stay exactly these.
        ("M2 the errand called whatever the flag -> A2", H_PATH,
         "        if _topoff_mode in (\"observe\", \"1\") or _kit_mode in (\"observe\", \"1\"):\n",
         "        if True:  # _topoff_mode\n", {"A2"}),
        ("M3 stage fails OPEN (MID on an unreadable flag) -> L3 and E3", T_PATH,
         "    except Exception:  # noqa: BLE001 - an unreadable flag is \"no purchase\", never a stage guessed low\n        return None",
         "    except Exception:  # noqa: BLE001 - an unreadable flag is \"no purchase\", never a stage guessed low\n        return \"MID\"",
         {"L3", "E3"}),
        ("M4 the basket floor dropped (CASH_FLOOR in the reserve era) -> L4", T_PATH,
         "        return CASH_FLOOR + 2 * int(missing_basket_cost)", "        return CASH_FLOOR", {"L4"}),
        ("M5 no below-the-floor refusal -> L5 (its reason becomes 'cannot afford')", T_PATH,
         "    if money <= floor_money:\n", "    if False:\n", {"L5"}),
        ("M6 the spec's round-down (the remainder dropped) -> L5 (the A1 case) and L6", T_PATH,
         "    if rest:\n        lines[-1] = (ball, 10 + rest)\n", "", {"L5", "L6"}),
        ("M7 Sootopolis whitelisted -> A4 and E1 (a non-whitelisted city now walks)", T_PATH,
         "    return {PokemonCenter.RustboroCity: RUSTBORO_MART}",
         "    return {PokemonCenter.RustboroCity: RUSTBORO_MART, PokemonCenter.SootopolisCity: RUSTBORO_MART}",
         {"A4", "E1"}),
        ("M8 a typo silently OFF (no error) -> L8", T_PATH,
         "        return \"\", f\"POKEBOT_R23_BALLRESTOCK={value!r} is not one of {VALID_FLAG_VALUES}: treated as OFF\"",
         "        return \"\", None", {"L8"}),
        ("M9 the errand buys with buy_poke_balls -> A6, E4a, E4b", T_PATH,
         "    yield from buy_in_shop([(get_item_by_name(n), q) for n, q in list(lines) + list(kit_lines)])",
         "    from modules.story.early_game import buy_poke_balls\n    yield from buy_poke_balls(sum(q for _, q in lines))",
         {"A6", "E4a", "E4b"}),
        # --- the step 9a review's invisible mutants of the ACTION path (its X1-X7), now each red on E2/E4 ---
        ("M10 a failed errand is not memoised -> E2b E2c E2d E2e", T_PATH,
         "        if balls_failed:\n            failed.add(city)\n",       # step 10a review: the anchor moved
         "        if balls_failed:\n            pass\n",                   # (the set is unchanged, re-proven)
         {"E2b", "E2c", "E2d", "E2e"}),
        ("M11 the errand swallows an abort -> E2f", T_PATH,
         "        reraise_if_aborting(error)\n        report[\"error\"] = repr(error)",
         "        report[\"error\"] = repr(error)", {"E2f"}),
        ("M12 the bag-delta check always ok -> E4b", T_PATH,
         "        report[\"balls_ok\"] = report[\"bought\"] == planned", "        report[\"balls_ok\"] = True", {"E4b"}),
        ("M13 the recovery removed -> E2b E2c E2d E2e", T_PATH,
         "        recovered = yield from _yield_bounded_by_frames(_recover(exit_map, exit_tile, report), RECOVERY_FRAMES)",
         "        recovered = None", {"E2b", "E2c", "E2d", "E2e"}),
        ("M14 the errand says 'not moved' after moving (no second stable wait) -> E2a-E2e", T_PATH,
         "    return True\n\n\ndef _walk_buy_return", "    return False\n\n\ndef _walk_buy_return",
         {"E2a", "E2b", "E2c", "E2d", "E2e"}),
        ("M15 the walk back removed -> E4a", T_PATH,
         "    yield from _navigate_riding_out(exit_map, exit_tile)\n    yield from wait_until_truly_controllable()\n"
         "    yield from ensure_facing_direction(\"Down\")                   # OFF leaves the PC facing Down\n",
         "", {"E4a"}),
        ("M16 the errand's frame bound ignored -> E2d", T_PATH,
         "        bound = int(_os_bb2.environ.get(\"POKEBOT_R23_FAULT_ERRANDFRAMES\", \"\") or ERRAND_FRAMES)",
         "        bound = 10 ** 12", {"E2d"}),
        ("M17 no GeneratorExit handler (an outer close goes silent again) -> E2g", T_PATH,
         "    except GeneratorExit:\n", "    except ZeroDivisionError:\n", {"E2g"}),
        ("M18 a planning failure escapes the errand -> E2h", T_PATH,
         "        reraise_if_aborting(error)\n        if flag_mode in (\"observe\", \"1\"):         # the ball key",
         "        raise\n        if flag_mode in (\"observe\", \"1\"):         # the ball key", {"E2h"}),  # anchor moved (10a review)
        ("M19 `_inputs` reads a flag missing from the table as False -> E3", T_PATH,
         "for key, name in flag_names().items() if name in _event_flags}", "for key, name in flag_names().items()}",
         {"E3"}),
        ("M20 success no longer requires being back on the exit tile -> E2c", T_PATH,
         "        moved_ok = finished and report.get(\"ok\", False) and report.get(\"returned\", False)",
         "        moved_ok = finished and report.get(\"ok\", False)", {"E2c"}),
        ("N1 a comment edit in the heal hunk turns NOTHING red", H_PATH,
         "        # The heal's LAST act stays a stable-controllable wait",
         "        # (edited) _topoff_moved and stable < 20 named in a comment only; the heal's LAST act stays a wait",
         set()),
    ]
    for i, (label, path, old, new, want) in enumerate(cases):
        try:
            if path == H_PATH:   # the heal file uses relative imports: its rows are AST-only, so it is never exec'd
                if hsrc.count(old) != 1:
                    raise AssertionError(f"mutant anchor found {hsrc.count(old)} times: {old!r}")
                mod, msrc = None, hsrc.replace(old, new)
            else:
                mod, msrc = mutant_module(path, f"m{i}", old, new, f"mut_bb_{i}")
            h = msrc if path == H_PATH else hsrc
            tt = msrc if path == T_PATH else tsrc
            red = set(a_rows(h, tt, smsrc, "m"))
            if path == T_PATH:
                red |= (set(l_rows(mod, "m")) | set(e_rows(mod, "m")) | set(e2_rows(mod, "m")) | set(e3_rows(mod, "m"))
                        | set(e4_rows(mod, "m")))
            check(label, red == want, f"red {sorted(red)}" + ("" if red == want else f" (want {sorted(want)})"))
        except Exception as error:  # noqa: BLE001
            check(label, False, f"{type(error).__name__}: {error}")

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
