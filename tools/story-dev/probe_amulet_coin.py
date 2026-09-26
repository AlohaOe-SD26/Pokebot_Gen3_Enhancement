r"""GATE — USER RULING 17: Mom's Amulet Coin after badge 5, held by a battler (`#26-ch23money`, 2026-09-26).

WHY: 3 of 3 organic runs that reached §Ch23 leg 11 were refused on money; the coin doubles every later trainer
prize. The leg is `modules/story/amulet_coin.py`; `_play` runs it as Segment 12d. This gate pins what a drive cannot
keep true by itself:

  G1  WIRING — `_play` calls `run_ch12d(_ac_report, _at_petalburg, badge06=_done("BADGE06_GET"))` AFTER the Surf
      guard and BEFORE Segment 13a, and guards the END POSITION only when the errand ran;
  G2  THE DRIVER DRIVES PRODUCTION — `AmuletCoinMode` calls `run_ch12d`, and its Petalburg map set equals `_play`'s
      `_at_petalburg` map set exactly (drift here would grade a different gate than production's);
  G3  `pick_holder` (PURE) — top level wins; a level tie prefers an EMPTY held slot; never an egg; empty ⇒ None;
  G4  ONE COPY OF THE READINGS — the driver imports `AMULET_COIN_READINGS` and spells no reading itself;
  G5  `_houses_state` REFUSES an unreadable var (`get_event_var` returns -1 for an unknown name, which would read as
      "below 3" and walk into a post-game multichoice); the leg refuses at state 3+;
  G6  both fault arms are read in production and registered in `29`.
FAULT ARMS (built in, each must turn its check red): the errand moved after 13a; a driver missing one Petalburg
map; a lowest-level `pick_holder`; a `_houses_state` that passes -1 through.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_amulet_coin.py
"""
from __future__ import annotations

import ast
import io
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

from modules.story import amulet_coin as AC  # noqa: E402

STORY = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"
MODULE = SANDBOX / "modules" / "story" / "amulet_coin.py"
HARNESS = ROOT / "tools" / "story-dev" / "story_harness.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
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


def _play_src(story_src: str) -> str:
    """`_play`'s body, comments stripped — a mention in a comment must not satisfy the gate."""
    tree = ast.parse(story_src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_play")
    return _strip_comments(ast.get_source_segment(story_src, fn) or "")


CALL = 'yield from run_ch12d(_ac_report, _at_petalburg, badge06=_done("BADGE06_GET"))'
SURF_GUARD = '_guard("Teach Surf (Ch12c)", _party_knows_surf)'
SEG_13A = "fight_route119_rival_and_get_fly,"


def g1(play: str, sink=None):
    i_surf, i_call, i_13a = play.find(SURF_GUARD), play.find(CALL), play.find(SEG_13A)
    check(-1 not in (i_surf, i_call, i_13a) and i_surf < i_call < i_13a,
          f"G1 `_play` calls run_ch12d AFTER the Surf guard and BEFORE Segment 13a ({i_surf} < {i_call} < {i_13a})",
          sink)
    guard = re.search(r'if _ac_report\.get\("ran"\):\s*_guard\("Amulet Coin errand ends in Petalburg \(Ch12d\)", '
                      r"_at_petalburg\)", play)
    check(guard is not None and i_call < guard.start() < i_13a,
          "G1 the END-POSITION guard runs only when the errand ran, before 13a", sink)
    check(play.count("run_ch12d(") == 1, "G1 exactly one call site", sink)


def _petalburg_maps_in_play(play: str) -> "set[str]":
    m = re.search(r"_at_petalburg = lambda: _cur_map\(\) in \((.*?)\)\n", play, re.S)
    return set(re.findall(r"MapRSE\.([A-Z0-9_]+)\.value", m.group(1))) if m else set()


def _driver_class(harness_src: str) -> "ast.ClassDef":
    return next(n for n in ast.parse(harness_src).body if isinstance(n, ast.ClassDef) and n.name == "AmuletCoinMode")


def _driver_maps(cls: "ast.ClassDef") -> "set[str]":
    for node in cls.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "PETALBURG_MAPS" for t in node.targets):
            return {e.value for e in node.value.elts}
    return set()


def g2(play: str, harness_src: str, cls_maps=None, sink=None):
    cls = _driver_class(harness_src)
    code = _strip_comments(ast.get_source_segment(harness_src, cls) or "")
    check("yield from run_ch12d(rep, at_petalburg, badge06=" in code, "G2 the driver calls run_ch12d itself", sink)
    prod = _petalburg_maps_in_play(play)
    drv = _driver_maps(cls) if cls_maps is None else cls_maps
    check(bool(prod) and prod == drv, f"G2 driver Petalburg maps == `_play`'s _at_petalburg ({sorted(prod)} vs "
                                      f"{sorted(drv)})", sink)


def _mon(level, held=None, egg=False):
    return types.SimpleNamespace(level=level, held_item=held, is_egg=egg)


def g3(pick, sink=None):
    berry = types.SimpleNamespace(name="Oran Berry")
    check(pick([_mon(20), _mon(36), _mon(30)]) == 1, "G3 the top level wins", sink)
    check(pick([_mon(36, berry), _mon(36)]) == 1, "G3 a level tie prefers the EMPTY held slot", sink)
    check(pick([_mon(36), _mon(36, berry)]) == 0, "G3 … in either order", sink)
    check(pick([_mon(50, egg=True), _mon(10)]) == 1, "G3 never an egg (even a 'higher' one)", sink)
    check(pick([None, _mon(12)]) == 1, "G3 an empty slot is skipped", sink)
    check(pick([]) is None and pick([_mon(5, egg=True)]) is None, "G3 no eligible member ⇒ None", sink)


def g4(harness_src: str, sink=None):
    cls = _driver_class(harness_src)
    code = _strip_comments(ast.get_source_segment(harness_src, cls) or "")
    check("AMULET_COIN_READINGS" in code, "G4 the driver imports AMULET_COIN_READINGS", sink)
    check(not re.search(r"""["']AC-(HOUSE|REGISTERED|RECEIVED|GIVEN|BACK)["']""", code),
          "G4 the driver spells no reading of its own", sink)


def g5(houses_state, module_src: str, sink=None):
    import modules.memory as memory

    real = getattr(memory, "get_event_var", None)
    try:
        memory.get_event_var = lambda name: -1
        check(houses_state() is None, "G5 an unknown var (-1) reads as UNREADABLE (None), not as 'below 3'", sink)
        memory.get_event_var = lambda name: 2
        check(houses_state() == (2, 2), "G5 a readable var is returned as read", sink)
    finally:
        memory.get_event_var = real
    fetch = next(n for n in ast.parse(module_src).body if isinstance(n, ast.FunctionDef) and n.name == "fetch_amulet_coin")
    code = _strip_comments(ast.get_source_segment(module_src, fetch) or "")
    check('report["houses_state"] is None or max(report["houses_state"]) >= 3' in code,
          "G5 the leg refuses an unreadable state and any state 3+", sink)


def g6(module_src: str):
    registry = REGISTRY.read_text(encoding="utf-8")
    code = _strip_comments(module_src)
    for arm in ("POKEBOT_AMULET_FAULT_ONETALK", "POKEBOT_AMULET_FAULT_NOGIVE"):
        check(f'os.environ.get("{arm}") == "1"' in code and f"`{arm}`" in registry,
              f"G6 {arm} is read in production and registered in 29")
    check('int(os.environ.get("POKEBOT_AMULET_FAULT_BUDGET") or AMULET_COIN_BUDGET)' in code
          and "`POKEBOT_AMULET_FAULT_BUDGET`" in registry,
          "G6 POKEBOT_AMULET_FAULT_BUDGET overrides the budget in production (default unchanged) and is registered")
    check("if report.get(\"finished\") is False:" in code and "_yield_bounded_by_frames(_leave_menus(), 3_000)" in code,
          "G6 an expired budget closes any open menu (bounded) before the fallback walk")


def main() -> int:
    print("=" * 92)
    print("GATE — USER RULING 17: the Amulet Coin errand (Segment 12d)")
    print("=" * 92)
    story_src = STORY.read_text(encoding="utf-8")
    module_src = MODULE.read_text(encoding="utf-8")
    harness_src = HARNESS.read_text(encoding="utf-8")
    play = _play_src(story_src)
    print("\n== G1 wiring ==")
    g1(play)
    print("\n== G2 the driver drives production ==")
    g2(play, harness_src)
    print("\n== G3 pick_holder (pure) ==")
    g3(AC.pick_holder)
    print("\n== G4 one copy of the readings ==")
    g4(harness_src)
    print("\n== G5 the post-game house state is refused ==")
    g5(AC._houses_state, module_src)
    print("\n== G6 fault arms ==")
    g6(module_src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    moved = play.replace(CALL, "pass").replace(SEG_13A, SEG_13A + "\n" + CALL)
    g1(moved, sink)
    check(bool(sink), f"FAULT the errand moved AFTER Segment 13a FAILS G1 ({len(sink)} caught)")
    sink = []
    g2(play, harness_src, cls_maps=_driver_maps(_driver_class(harness_src)) - {"PETALBURG_CITY_MART"}, sink=sink)
    check(bool(sink), f"FAULT a driver missing one Petalburg map FAILS G2 ({len(sink)} caught)")
    sink = []
    g3(lambda party: min((i for i, m in enumerate(party) if m is not None and not m.is_egg),
                         key=lambda i: party[i].level, default=None), sink)
    check(bool(sink), f"FAULT a lowest-level pick_holder FAILS G3 ({len(sink)} caught)")
    sink = []

    def passthrough():
        from modules.memory import get_event_var

        return get_event_var("LITTLEROOT_HOUSES_STATE_MAY"), get_event_var("LITTLEROOT_HOUSES_STATE_BRENDAN")

    g5(passthrough, module_src, sink)
    check(bool(sink), f"FAULT a _houses_state that passes -1 through FAILS G5 ({len(sink)} caught)")
    sink = []
    g4(harness_src.replace("_HOUSE, REGISTERED, RECEIVED, GIVEN, BACK = AMULET_COIN_READINGS",
                           'REGISTERED = "AC-REGISTERED"'), sink)
    check(bool(sink), f"FAULT a driver that spells a reading itself FAILS G4 ({len(sink)} caught)")
    sink = []
    g6_fault = []
    unread = module_src.replace('os.environ.get("POKEBOT_AMULET_FAULT_NOGIVE") == "1"', "False")
    for arm in ("POKEBOT_AMULET_FAULT_ONETALK", "POKEBOT_AMULET_FAULT_NOGIVE"):
        check(f'os.environ.get("{arm}") == "1"' in _strip_comments(unread), f"{arm} read", g6_fault)
    check(bool(g6_fault), f"FAULT an arm no longer read in production FAILS G6 ({len(g6_fault)} caught)")
    sink = []
    # A commented-out call placed INSIDE `_play` (raw source, then re-stripped) must not count as a second site.
    commented = story_src.replace(SURF_GUARD, SURF_GUARD + "\n        # " + CALL, 1)
    g1(_play_src(commented), sink)
    check(commented != story_src and len(sink) == 0,
          "NO FALSE POSITIVE: a commented-out call inside `_play` does not change G1's verdict")

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
