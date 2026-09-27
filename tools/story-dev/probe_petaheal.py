r"""GATE — the Norman heal falls back to the story's own Petalburg road when the generic walk fails from the Rustboro side
(`#26-healmap-lavaridge`, the Petalburg family, 2026-09-27).

WHY: 53 of 53 Norman heals that derailed "BLOCKED" in batch `#26-batch0926` started on Route 116/117 after the prep's
training top-up. The generic walk bounced off Rustboro Flat1 and raised; the derail's recovery then re-ran
`travel_lavaridge_to_petalburg` and arrived 53 of 53 times.

  P1  WIRING: `StoryMode._play` calls `yield from heal_at_petalburg()`, and no longer a bare
      `yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)`.
  P2  `PETALBURG_ROAD_MAPS` is EXACTLY `travel_lavaridge_to_petalburg`'s own `order` list minus Petalburg (read by AST),
      so the fallback cannot start the road from a map the road does not know.
  P3  BEHAVIOUR (collaborators stubbed):
      - the generic heal succeeds ⇒ nothing else happens;
      - it raises `HealWalkFailedError` on a road map ⇒ release held input, THEN the road, THEN heal;
      - it raises off the road (Route 102) ⇒ re-raised, with no road;
      - the arm set ⇒ re-raised.
  P4  the arm `POKEBOT_PETAHEAL_FAULT_GENERIC` is read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): the segment reverted to the bare heal (P1); a road set missing ROUTE116 (P2); a
fallback without the held-input release (P3 — KI-106's lesson: a raise abandons the walker mid-step).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_petaheal.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.early_game as EG  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.modes.util.higher_level_actions import HealWalkFailedError  # noqa: E402

SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
EG_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_PETAHEAL_FAULT_GENERIC"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def p1(src: str, sink=None):
    code = ast.unparse(next(n for n in ast.walk(ast.parse(src))
                            if isinstance(n, ast.FunctionDef) and n.name == "_play"))
    check("yield from heal_at_petalburg()" in code
          and "yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)" not in code,
          "P1 `_play` heals for Norman through `heal_at_petalburg()`, not the bare generic heal", sink)


def _road_order(src: str) -> set:
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "travel_lavaridge_to_petalburg")
    assign = next(a for a in ast.walk(fn) if isinstance(a, ast.Assign)
                  and any(getattr(t, "id", None) == "order" for t in a.targets))
    return {getattr(MapRSE, e.value.attr).value for e in assign.value.elts}


def p2(road, src: str, sink=None):
    want = _road_order(src) - {MapRSE.PETALBURG_CITY.value}
    check(set(road) == want and MapRSE.ROUTE116.value in road,
          f"P2 PETALBURG_ROAD_MAPS is exactly the road's own order minus Petalburg ({len(want)} maps)", sink)


def p3(fn, sink=None):
    """Run `fn` (heal_at_petalburg or a faulted copy) with stubs; return the call log per case."""
    calls: list = []
    saved = (EG._map_group_number, EG.heal_in_pokemon_center, EG.travel_lavaridge_to_petalburg, EG.context.emulator)
    mode = {"fail": False}

    def _heal(_c):
        calls.append("heal")
        if mode["fail"] and calls.count("heal") == 1:
            raise HealWalkFailedError("the walk to PetalburgCity is BLOCKED (stub)")
        yield

    def _road():
        calls.append("road")
        yield

    EG.heal_in_pokemon_center, EG.travel_lavaridge_to_petalburg = _heal, _road
    EG.context.emulator = types.SimpleNamespace(reset_held_buttons=lambda: calls.append("release") or 0x42)
    out = {}
    try:
        for case, where, fail, arm in (("ok", MapRSE.PETALBURG_CITY.value, False, False),
                                       ("road", MapRSE.RUSTBORO_CITY.value, True, False),
                                       ("offroad", MapRSE.ROUTE102.value, True, False),
                                       ("arm", MapRSE.RUSTBORO_CITY.value, True, True)):
            calls.clear()
            mode["fail"] = fail
            EG._map_group_number = lambda w=where: w
            if arm:
                os.environ[ARM] = "1"
            raised = None
            try:
                for _ in fn():
                    pass
            except HealWalkFailedError as error:
                raised = type(error).__name__
            finally:
                os.environ.pop(ARM, None)
            out[case] = (list(calls), raised)
    finally:
        EG._map_group_number, EG.heal_in_pokemon_center, EG.travel_lavaridge_to_petalburg, EG.context.emulator = saved
    check(out["ok"] == (["heal"], None), f"P3 generic heal succeeds ⇒ nothing else ({out['ok']})", sink)
    check(out["road"] == (["heal", "release", "road", "heal"], None),
          f"P3 BLOCKED on the road ⇒ release, then the road, then heal ({out['road']})", sink)
    check(out["offroad"] == (["heal"], "HealWalkFailedError"),
          f"P3 BLOCKED off the road (Route 102) ⇒ re-raised, no road ({out['offroad']})", sink)
    check(out["arm"] == (["heal"], "HealWalkFailedError"), f"P3 the arm ⇒ re-raised ({out['arm']})", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — the Norman heal falls back to the Petalburg road from the Rustboro side (#26-healmap-lavaridge)")
    print("=" * 92)
    sm, eg = SM_SRC.read_text(encoding="utf-8"), EG_SRC.read_text(encoding="utf-8")
    os.environ.pop(ARM, None)
    print("\n== P1 wiring ==")
    p1(sm)
    print("\n== P2 the road set ==")
    p2(EG.PETALBURG_ROAD_MAPS, eg)
    print("\n== P3 behaviour (collaborators stubbed) ==")
    p3(EG.heal_at_petalburg)
    print("\n== P4 the arm ==")
    check(f'environ.get("{ARM}") == "1"' in eg and f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"),
          f"P4 {ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    p1(sm.replace("yield from heal_at_petalburg()", "yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)", 1),
       sink)
    check(bool(sink), f"FAULT the segment reverted to the bare heal FAILS P1 ({len(sink)} caught)")
    sink = []
    p2(EG.PETALBURG_ROAD_MAPS - {MapRSE.ROUTE116.value}, eg, sink)
    check(bool(sink), f"FAULT a road set missing ROUTE116 FAILS P2 ({len(sink)} caught)")
    sink = []
    fn_src = ast.get_source_segment(eg, next(n for n in ast.walk(ast.parse(eg))
                                             if isinstance(n, ast.FunctionDef) and n.name == "heal_at_petalburg"))
    mutated = fn_src.replace("_released = context.emulator.reset_held_buttons()", "_released = 0", 1)
    ns: dict = {}
    exec(compile(mutated, "<no-release>", "exec"), EG.__dict__, ns)  # noqa: S102 - the gate's own fault injection
    p3(ns["heal_at_petalburg"], sink)
    check(bool(sink), f"FAULT a fallback without the held-input release FAILS P3 ({len(sink)} caught)")

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
