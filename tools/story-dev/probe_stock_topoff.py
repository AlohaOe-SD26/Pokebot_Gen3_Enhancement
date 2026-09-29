"""GATE — USER RULINGS 23 + 26, design v2 step 9a (BB): the ball top-off (`modules/story/stock_topoff.py`) and its
piggyback on `heal_in_pokemon_center` (`modules/modes/util/higher_level_actions.py`, an UPSTREAM-derived file).

WHY. The top-off spends money on every eligible heal, so the ways it can hurt are: spending below a floor (RULING 18's
League basket), a stage guessed low when a flag read fails, a negative or over-max quantity (`buy_in_shop` raises on
one and never ends on the other), and — because it rides an upstream heal every chapter uses — changing an OFF heal at
all, or ending a heal off its exit tile. Each has rows here.

ROWS
  L1-L8   PURE: the limits (and that they come from the source constants), `best_ball`, `stage` (order and fail-closed),
          `floor`, `ball_topoff_plan` (including below-floor, the fault floor and the in-game max), `plan_lines`
          (Premier-preserving merge), the hysteresis bound, `parse_flag`.
  A1-A6   the heal's three hunks by AST (the flag parsed before the first yield; the errand inside the flag branch with an
          abort-aware loud handler, given `stable >= 20`; the second stable wait ONLY under `_topoff_moved`), the
          whitelist (Rustboro only), the memo reset per run, and no `buy_poke_balls*` in the errand.
  E1      the errand EXECUTED with stubs: OFF, a non-story mode, a non-whitelisted city, a failed city, an unstable exit
          and `observe` all return False with ZERO yields; `observe` and an empty plan log one line each.
  M1-M9   source mutants, each with the EXACT set of rows it must turn red; N1 a comment-only edit (none red).

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
    f = dict(IS_CHAMPION=False, ENTERED_ELITE_FOUR=False, SOOTOPOLIS_ARCHIE_MAXIE_LEAVE=False, BADGE01_GET=True)
    st = [t.stage(f), t.stage(dict(f, BADGE01_GET=False)), t.stage(dict(f, SOOTOPOLIS_ARCHIE_MAXIE_LEAVE=True)),
          t.stage(dict(f, SOOTOPOLIS_ARCHIE_MAXIE_LEAVE=True, ENTERED_ELITE_FOUR=True)),
          t.stage(dict(f, ENTERED_ELITE_FOUR=True, IS_CHAMPION=True)), t.stage({"BADGE01_GET": True})]
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
        "in-game max": (plan(spare=0, money=1100, floor_money=0), [("Poké Ball", 2)], "top off 2"),
    }
    bad = {k: (got, want) for k, (got, want, why) in cases.items() if got[0] != want or why not in got[1]}
    row("L5", "ball_topoff_plan over 10 literal cases (the A1 case, the control, both fault floors, below the floor, "
        "fail-closed, no ball, Great, the in-game max)", not bad, str(bad) if bad else "")
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
    branch = [n for n in ifs if ast.unparse(n.test) == "_topoff_mode in ('observe', '1')"]
    ok2 = False
    if len(branch) == 1:
        body = ast.unparse(branch[0])
        tries = [n for n in ast.walk(branch[0]) if isinstance(n, ast.Try)]
        handler = tries[0].handlers[0] if tries and tries[0].handlers else None
        hsrc_h = ast.unparse(handler) if handler else ""
        ok2 = ("ball_topoff_errand(pokemon_center_door_location, _topoff_mode, stable >= 20)" in body
               and handler is not None and ast.unparse(handler.type) == "Exception"
               and hsrc_h.index("reraise_if_aborting(error)") < hsrc_h.index("_piggyback_report("))
    row("A2", "the errand runs ONLY inside `if _topoff_mode in ('observe', '1')`, given `stable >= 20`, under an "
        "`except Exception` that re-raises an abort FIRST and then reports", ok2)
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

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    cases = [
        # (label, file, anchor, replacement, expected red set)
        ("M1 the second stable wait made unconditional -> A3", H_PATH,
         "        if _topoff_moved:\n", "        if True:  # _topoff_moved\n", {"A3"}),
        ("M2 the errand called whatever the flag -> A2", H_PATH,
         "        if _topoff_mode in (\"observe\", \"1\"):\n", "        if True:  # _topoff_mode\n", {"A2"}),
        ("M3 stage fails OPEN (MID on an unreadable flag) -> L3", T_PATH,
         "    except Exception:  # noqa: BLE001 - an unreadable flag is \"no purchase\", never a stage guessed low\n        return None",
         "    except Exception:  # noqa: BLE001 - an unreadable flag is \"no purchase\", never a stage guessed low\n        return \"MID\"",
         {"L3"}),
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
        ("M9 the errand buys with buy_poke_balls -> A6", T_PATH,
         "    yield from buy_in_shop([(get_item_by_name(n), q) for n, q in lines])",
         "    from modules.story.early_game import buy_poke_balls\n    yield from buy_poke_balls(sum(q for _, q in lines))",
         {"A6"}),
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
                red |= set(l_rows(mod, "m")) | set(e_rows(mod, "m"))
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
