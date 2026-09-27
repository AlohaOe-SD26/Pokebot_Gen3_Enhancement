r"""GATE — the Flannery heal takes the cable car when the prep left us BELOW Lavaridge (`#26-healmap-lavaridge` F4, 2026-09-27).

WHY: before Flannery, Route 112's one-way ledges leave the generic heal walk no route into Lavaridge from Route 111/117,
Mauville or the Fiery Path exit. The only way in is the scripted cable car plus the one-way Jagged Pass descent.
MEASURED in batch `#26-batch0926`: 54 of 54 such Flannery heals derailed "BLOCKED"; the derail's recovery
(`do_jagged_descent`) then reached Lavaridge 53 times, and the 54th ended run P1r7.

  W1  WIRING: in `StoryMode._play`, the statement right before `yield from do_lavaridge_gym()` is
      `yield from heal_at_lavaridge()`, not the generic `heal_in_pokemon_center(PokemonCenter.LavaridgeTown)`.
  W2  `LAVARIDGE_MAPS` is EXACTLY Lavaridge Town plus every interior: it is compared with the MapRSE members named
      LAVARIDGE_TOWN*, so a new or forgotten interior (the Poké Center!) cannot silently send a caller back up the cable car.
  W3  BEHAVIOUR (collaborators stubbed): outside Lavaridge ⇒ `do_jagged_descent()` and NO generic heal; inside ANY
      Lavaridge map ⇒ the generic heal and NO descent; with the arm set ⇒ the generic heal even from outside.
  W4  the arm `POKEBOT_LAVAHEAL_FAULT_GENERIC` is read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): the segment reverted to the generic heal (W1); a set missing the Poké Center (W2);
the arm set (W3's outside case).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_lavaheal.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.early_game as EG  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402

SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
EG_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_LAVAHEAL_FAULT_GENERIC"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _call_name(stmt):
    """`yield from f(...)` → 'f(<first positional arg source>)' (or '' when it is not that shape)."""
    v = getattr(stmt, "value", None)
    if isinstance(v, ast.YieldFrom) and isinstance(v.value, ast.Call):
        c = v.value
        fn = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "?")
        arg = ast.unparse(c.args[0]) if c.args else ""
        return f"{fn}({arg})"
    return ""


def w1(src: str, sink=None):
    tree = ast.parse(src)
    before = []
    for body in (getattr(n, "body", None) for n in ast.walk(tree)):
        if not isinstance(body, list):
            continue
        for i, stmt in enumerate(body):
            if _call_name(stmt) == "do_lavaridge_gym()" and i > 0:
                before.append(_call_name(body[i - 1]))
    check(before == ["heal_at_lavaridge()"],
          f"W1 the statement before `do_lavaridge_gym()` is `heal_at_lavaridge()` (found {before})", sink)


def w2(maps, sink=None):
    expected = {m.value for m in MapRSE if m.name == "LAVARIDGE_TOWN" or m.name.startswith("LAVARIDGE_TOWN_")}
    check(set(maps) == expected and MapRSE.LAVARIDGE_TOWN_POKEMON_CENTER_1F.value in maps,
          f"W2 LAVARIDGE_MAPS is exactly the town + its {len(expected) - 1} interiors (incl. the Poké Center)", sink)


def w3(sink=None):
    calls: list = []
    saved = (EG._map_group_number, EG.do_jagged_descent, EG.heal_in_pokemon_center)

    def _descent():
        calls.append("descent")
        yield

    def _heal(_center):
        calls.append("heal")
        yield

    EG.do_jagged_descent, EG.heal_in_pokemon_center = _descent, _heal
    try:
        def run_from(where):
            calls.clear()
            EG._map_group_number = lambda: where
            for _ in EG.heal_at_lavaridge():
                pass
            return list(calls)

        out = run_from(MapRSE.ROUTE111.value)
        check(out == ["descent"], f"W3 from ROUTE111 ⇒ the cable car + descent, no generic heal ({out})", sink)
        inside = {MapRSE(m).name: run_from(m) for m in EG.LAVARIDGE_MAPS}
        check(all(v == ["heal"] for v in inside.values()),
              f"W3 from every Lavaridge map ⇒ the plain heal, no descent ({sorted(k for k, v in inside.items() if v != ['heal'])} wrong)",
              sink)
        os.environ[ARM] = "1"
        try:
            armed = run_from(MapRSE.ROUTE111.value)
        finally:
            os.environ.pop(ARM, None)
        return armed
    finally:
        EG._map_group_number, EG.do_jagged_descent, EG.heal_in_pokemon_center = saved


def main() -> int:
    print("=" * 92)
    print("GATE — the Flannery heal takes the cable car from below Lavaridge (#26-healmap-lavaridge F4)")
    print("=" * 92)
    sm = SM_SRC.read_text(encoding="utf-8")
    os.environ.pop(ARM, None)
    print("\n== W1 wiring ==")
    w1(sm)
    print("\n== W2 the Lavaridge set ==")
    w2(EG.LAVARIDGE_MAPS)
    print("\n== W3 behaviour (collaborators stubbed) ==")
    armed = w3()
    check(armed == ["heal"], f"W3 with {ARM}=1 ⇒ the generic heal even from ROUTE111 (the old behaviour) ({armed})")
    print("\n== W4 the arm ==")
    check(f'environ.get("{ARM}") != "1"' in EG_SRC.read_text(encoding="utf-8")
          and f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"), f"W4 {ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    w1(sm.replace("yield from heal_at_lavaridge()\n", "yield from heal_in_pokemon_center(PokemonCenter.LavaridgeTown)\n", 1),
       sink)
    check(bool(sink), f"FAULT the segment reverted to the generic heal FAILS W1 ({len(sink)} caught)")
    sink = []
    w2(EG.LAVARIDGE_MAPS - {MapRSE.LAVARIDGE_TOWN_POKEMON_CENTER_1F.value}, sink)
    check(bool(sink), f"FAULT a set missing the Poké Center FAILS W2 ({len(sink)} caught)")
    sink = []
    os.environ[ARM] = "1"
    try:
        calls: list = []
        saved = (EG._map_group_number, EG.do_jagged_descent, EG.heal_in_pokemon_center)
        EG._map_group_number = lambda: MapRSE.ROUTE111.value

        def _d():
            calls.append("descent")
            yield

        def _h(_c):
            calls.append("heal")
            yield

        EG.do_jagged_descent, EG.heal_in_pokemon_center = _d, _h
        try:
            for _ in EG.heal_at_lavaridge():
                pass
        finally:
            EG._map_group_number, EG.do_jagged_descent, EG.heal_in_pokemon_center = saved
        check(calls == ["descent"], "(the outside case under the arm)", sink)
    finally:
        os.environ.pop(ARM, None)
    check(bool(sink), f"FAULT the arm set FAILS W3's outside case ({len(sink)} caught)")

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
