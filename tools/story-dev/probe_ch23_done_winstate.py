# -*- coding: utf-8 -*-
"""GATE #74 — A **WINNING** RUN MUST NOT MAKE `ch23_chapter_done()` READ FALSE.

⛔⛔ THE BUG THIS EXISTS TO PREVENT — AND IT IS THE ONE WHERE **SUCCESS IS THE FAILURE CASE**.
`ch23_chapter_done()` gates §Ch23 dispatch. Until 2026-09-24 its only position conjunct was
`_on_map(EVER_GRANDE)`. But the Hall of Fame sequence returns the player to
`LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` — MEASURED by `--driver ch24tailprobe`
(`ai-research-notes/2026-09-17-ch24-legB-TAIL-MEASURED.md` Q8) — which is **not** Ever Grande.

⇒ after a WIN the predicate read **False**, and the consequences were traced line by line:
  1. `ch23_chapter_done()` False ⇒ §Ch23 runs again;
  2. legs 1-3 self-skip (`_PRE_DEPARTURE_MAPS` does not contain Littleroot);
  3. ‼ **LEG 4 FIRES** — `if not inside_vr and not at_ever_grande_top()`, and both terms are False
     from a bedroom;
  4. ⇒ **THE BOT ATTEMPTS AN OCEAN CROSSING FROM A BEDROOM**, burns the chapter's three attempts,
     and raises.
**A completed game became a hard §Ch23 failure.**

────────────────────────────────────────────────────────────────────────────────────────────────────
WHAT THIS GATE CHECKS — STRUCTURE, NOT A LIVE RUN
────────────────────────────────────────────────────────────────────────────────────────────────────
Reading the real predicate requires a live emulator and a *winning* save state, which this tree does
not hold. So this gate asserts the SOURCE has the two properties the fix depends on, and that they
cannot be quietly removed:

  1. `CH24_SEALED_MAPS` exists, and contains the eleven maps past the point of no return.
  2. ⛔ It does **NOT** contain `POKEMON_LEAGUE_1F` or `POKEMON_LEAGUE_2F`. This is the whole reason
     the tuple exists rather than reusing `inside_league()`: **§Ch23's own heal (leg 10) and shop
     (leg 11) legs stand in that lobby**, so a marker that matched it would make §Ch23 declare
     itself finished in the middle of its own work.
  3. `CH24_GAME_CLEAR_FLAG` resolves in the event-flag table — `get_event_flag` returns **False
     silently** for an unknown name (`memory.py:336-338`), so a typo here would restore the exact
     bug this gate exists to prevent, invisibly.
  4. Both disjuncts appear in `ch23_chapter_done` **before** its `wally_beaten()` guard, because
     each is sufficient alone and the old conjuncts are all False from a bedroom.

⭐ WHY `IS_CHAMPION` AND NOT THE OBVIOUS ALTERNATIVES. It is **monotone**: set in exactly one decomp
file (`data/scripts/hall_of_fame.inc`) and cleared nowhere. `VAR_ELITE_4_STATE` and the four
`FLAG_DEFEATED_ELITE_4_*` are wiped by `ResetEliteFour` **on the winning path as well as the losing
one**, so none of them can tell a win from a loss.

FAULT ARMS (a gate that cannot go red is decoration):
    --fault lobby      pretend the lobby is in CH24_SEALED_MAPS   → must FAIL
    --fault badflag    pretend the flag name is misspelled        → must FAIL
    --fault order      pretend the disjuncts sit after wally      → must FAIL
    --fault noimport   pretend `get_event_flag` is not imported     → must FAIL
                       ‼ THIS IS THE ARM THAT MATTERS. The first version of the fix shipped in
                       exactly that state: the NameError was swallowed by the function's own broad
                       `except`, the disjunct silently never fired, and THIS GATE SAID PASS because
                       the text was present and correctly ordered. Text order is not behaviour.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

_BUILD = ("custom" if "--build" in sys.argv
          and sys.argv.index("--build") + 1 < len(sys.argv)
          and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox")
ROOT = REPO / f"{_BUILD}-pokebot"
VR = ROOT / "modules" / "story" / "victory_road.py"
FLAGS = ROOT / "modules" / "data" / "event_flags" / "emerald.txt"

#: The eleven maps past the commitment point.
WANT_SEALED = {
    "EVER_GRANDE_CITY_HALL1", "EVER_GRANDE_CITY_HALL2", "EVER_GRANDE_CITY_HALL3",
    "EVER_GRANDE_CITY_HALL4", "EVER_GRANDE_CITY_HALL5",
    "EVER_GRANDE_CITY_SIDNEYS_ROOM", "EVER_GRANDE_CITY_PHOEBES_ROOM",
    "EVER_GRANDE_CITY_GLACIAS_ROOM", "EVER_GRANDE_CITY_DRAKES_ROOM",
    "EVER_GRANDE_CITY_CHAMPIONS_ROOM", "EVER_GRANDE_CITY_HALL_OF_FAME",
}
#: ⛔ MUST NEVER BE IN THE TUPLE — §Ch23's own legs stand there.
FORBIDDEN_SEALED = {"EVER_GRANDE_CITY_POKEMON_LEAGUE_1F", "EVER_GRANDE_CITY_POKEMON_LEAGUE_2F"}


def flag_table() -> set[str]:
    out = set()
    for line in FLAGS.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            out.add(parts[1])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fault", choices=["lobby", "badflag", "order", "noimport"])
    ap.add_argument("--build", choices=["sandbox", "custom"], default="sandbox")
    args = ap.parse_args()

    bar = "=" * 100
    print(bar)
    print("GATE #74 — A WINNING RUN MUST NOT MAKE `ch23_chapter_done()` READ FALSE")
    print(bar)
    print(f"  build: {_BUILD}-pokebot")

    if not VR.exists():
        print(f"  ⛔ cannot find {VR}")
        return 1
    src = VR.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []

    # ---- 1/2. the tuple, and what it must NOT contain -----------------------------------------
    tree = ast.parse(src)
    sealed: set[str] = set()
    flag_name = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == "CH24_SEALED_MAPS" and isinstance(node.value, ast.Tuple):
                for el in node.value.elts:
                    if isinstance(el, ast.Attribute):
                        sealed.add(el.attr)
            elif name == "CH24_GAME_CLEAR_FLAG" and isinstance(node.value, ast.Constant):
                flag_name = node.value.value

    if args.fault == "lobby":
        sealed = sealed | {"EVER_GRANDE_CITY_POKEMON_LEAGUE_1F"}
    if args.fault == "badflag":
        flag_name = "FLAG_IS_CHAMPION"

    if not sealed:
        problems.append("CH24_SEALED_MAPS is missing or not a tuple of MapRSE members")
    else:
        missing = WANT_SEALED - sealed
        if missing:
            problems.append(f"CH24_SEALED_MAPS is missing {sorted(missing)} — a bot standing there "
                            f"would still make a WON run look unfinished")
        bad = FORBIDDEN_SEALED & sealed
        if bad:
            problems.append(
                f"⛔ CH24_SEALED_MAPS contains {sorted(bad)} — the LOBBY/2F, where §Ch23's OWN heal "
                f"(leg 10) and shop (leg 11) legs stand. §Ch23 would declare itself done in the "
                f"middle of its own work. This is exactly why the tuple exists instead of "
                f"`inside_league()`.")
    print(f"  CH24_SEALED_MAPS: {len(sealed)} map(s)")

    # ---- 3. the flag name must RESOLVE ---------------------------------------------------------
    table = flag_table()
    print(f"  flag table: {len(table)} name(s); CH24_GAME_CLEAR_FLAG = {flag_name!r}")
    if not flag_name:
        problems.append("CH24_GAME_CLEAR_FLAG is missing")
    elif flag_name not in table:
        problems.append(
            f"CH24_GAME_CLEAR_FLAG {flag_name!r} is NOT in the event-flag table. `get_event_flag` "
            f"returns False SILENTLY for an unknown name, so the win-disjunct would be a hardcoded "
            f"False and the bug would be back, invisibly.")

    # ---- 4. ORDER: both disjuncts must precede the wally guard ---------------------------------
    body = src[src.index("def ch23_chapter_done"):]
    i_flag = body.find("get_event_flag(CH24_GAME_CLEAR_FLAG)")
    i_maps = body.find("for m in CH24_SEALED_MAPS")
    i_wally = body.find("if not wally_beaten()")
    if args.fault == "order":
        i_flag, i_maps = (i_wally + 10, i_wally + 20)
    for label, idx in (("IS_CHAMPION disjunct", i_flag), ("sealed-map disjunct", i_maps)):
        if idx < 0:
            problems.append(f"{label} is absent from ch23_chapter_done")
        elif 0 <= i_wally < idx:
            problems.append(
                f"{label} sits AFTER the `wally_beaten()` guard. Each disjunct is sufficient ALONE, "
                f"and from a bedroom every later conjunct is False — so ordering it late restores "
                f"the bug for any state where the earlier guard fails.")

    # ---- 5. ⛔⛔ THE NAMES MUST RESOLVE, NOT MERELY APPEAR ---------------------------------------
    # THIS CHECK EXISTS BECAUSE THIS GATE ONCE PASSED OVER A BROKEN PREDICATE. The first version of
    # the fix called `get_event_flag(...)` in a module that does not import it. The NameError was
    # swallowed by the function's own broad `except`, so the disjunct silently never fired — and
    # this gate said PASS, because the text was present and correctly ordered.
    # ⇒ text order is not behaviour. Compile the function and check every global it references is
    # actually reachable: a name that is neither a module global, a local import, nor a builtin is a
    # NameError waiting for the branch that reaches it.
    try:
        mod = ast.parse(src)
        fn = next(n for n in ast.walk(mod)
                  if isinstance(n, ast.FunctionDef) and n.name == "ch23_chapter_done")
        module_names = {t.id for n in mod.body if isinstance(n, ast.Assign)
                        for t in n.targets if isinstance(t, ast.Name)}
        module_names |= {n.name for n in mod.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        for n in ast.walk(mod):
            if isinstance(n, (ast.Import, ast.ImportFrom)) and n.col_offset == 0:
                module_names |= {a.asname or a.name.split(".")[0] for a in n.names}
        local_names = {a.asname or a.name for n in ast.walk(fn)
                       if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        if args.fault == "noimport":
            # ‼ THE ARM THAT PROVES THIS CHECK IS LIVE. Pretend the local `from modules.memory
            # import get_event_flag` is absent — which is EXACTLY the state the first version of the
            # fix shipped in, and which this gate passed over.
            local_names = local_names - {"get_event_flag"}
            module_names = module_names - {"get_event_flag"}
        local_names |= {t.id for n in ast.walk(fn) if isinstance(n, ast.Assign)
                        for t in n.targets if isinstance(t, ast.Name)}
        import builtins
        called = {n.func.id for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        for name in sorted(called):
            if name not in module_names and name not in local_names and not hasattr(builtins, name):
                problems.append(
                    f"⛔ `ch23_chapter_done` calls {name}(), which is NOT a module global, NOT a "
                    f"local import, and NOT a builtin. It is a NameError — and the function's own "
                    f"broad `except` would SWALLOW it, making the disjunct silently never fire. "
                    f"This exact bug shipped once and this gate passed over it.")
    except StopIteration:
        problems.append("ch23_chapter_done not found in the source")

    print()
    if problems:
        print("  ⛔ FAILED:")
        for q in problems:
            print(f"      {q}")
        print(bar)
        return 1
    if args.fault:
        print(f"  ⛔ FAULT ARM `{args.fault}` FAILED — it was supposed to turn this gate RED and the "
              f"gate stayed green. An unfaulted gate is decoration.")
        print(bar)
        return 1
    print("  ✅ PASS — a won run is recognised: the game-clear flag resolves, the sealed-map tuple")
    print("     covers the eleven committed maps and excludes the lobby, and both disjuncts are")
    print("     evaluated BEFORE the conjuncts that a bedroom would fail.")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
