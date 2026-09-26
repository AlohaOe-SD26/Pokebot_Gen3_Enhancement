r"""GATE — §Ch24 THE RETURN BRIDGE (`#26-ch24organic` gap 2): where it sits, what it asserts, that it is bounded.

WHY THIS EXISTS (2026-09-26)
----------------------------
§Ch24 training ends wherever its last rung ended — a route, Ever Grande's SOUTH half (27,49) after the
Victory Road step-out (NO PATH to the door, measured both ways), or indoors. `prepare_and_open_the_league`
used to walk at the door from there regardless. `return_to_league_door` now walks when it can and flies
when it must, and ASSERTS THE TILE, because `fly_to_destination` accepts any landing that is not the origin.

  B1  In `prepare_and_open_the_league` the bridge call comes AFTER the R1 refusal and BEFORE the leg's first
      move toward the door (`_navigate_riding_out(..., LEAGUE_DOOR_APRON)`, `_walk_through_warp`,
      `press_button`).
  B2  `return_to_league_door` ends with a TILE assertion (`_here_tile() == …LEAGUE_DOOR_APRON`, raising
      "§Ch24 bridge: expected to stand on …") that comes AFTER its last walk and its flight.
  B3  Both ways home are BOUNDED: every `_navigate_riding_out` / `fly_to_destination` call inside the bridge
      is an argument of `_yield_bounded_by_frames`.
  B4  Its arms are read in production (`NOBRIDGE` in `prepare_and_open_the_league`, `BRIDGEDEST` in
      `return_to_league_door`), comments stripped, and registered.
  B5  NO `*_READINGS` NAME IS ASSIGNED TWICE at module scope in `pokemon_league.py` — a second assignment
      is silently shadowed by the later one. (Added after the code review found this gate's own subject,
      then called `BRIDGE_READINGS`, dead on arrival behind `enter_the_league`'s constant of that name.)

FAULT ARMS (run every time): a door walk inserted before the bridge FAILS B1; the tile assertion renamed
away FAILS B2; an unbounded flight FAILS B3.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_bridge.py
"""
from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEAGUE_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "pokemon_league.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
R1_MARKER = "§Ch24 R1: REFUSING"
ASSERT_MARKER = "§Ch24 bridge: expected to stand on"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _fn(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _calls(fn, attr):
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if (f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)) == attr:
                out.append(n)
    return out


def _raises_with(fn, src, marker):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Raise) and marker in (ast.get_source_segment(src, n) or "")]


def b1(src, sink=None):
    fn = _fn(ast.parse(src), "prepare_and_open_the_league")
    r1 = _raises_with(fn, src, R1_MARKER)
    bridge = [c.lineno for c in _calls(fn, "return_to_league_door")]
    door = [c.lineno for c in _calls(fn, "_navigate_riding_out") if "LEAGUE_DOOR_APRON" in (ast.get_source_segment(src, c) or "")]
    moves = door + [c.lineno for c in _calls(fn, "_walk_through_warp")] + [c.lineno for c in _calls(fn, "press_button")]
    check(len(bridge) == 1, f"B1 exactly one bridge call in prepare_and_open_the_league (found {len(bridge)})", sink)
    if len(bridge) != 1 or not r1 or not moves:
        check(False, f"B1 prerequisites present (R1 raise {len(r1)}, door moves {len(moves)})", sink)
        return
    check(r1[0].lineno < bridge[0] < min(moves),
          f"B1 R1 (line {r1[0].lineno}) < bridge (line {bridge[0]}) < first door walk/warp/press (line {min(moves)})", sink)


def b2_b3(src, sink=None):
    fn = _fn(ast.parse(src), "return_to_league_door")
    asserts = _raises_with(fn, src, ASSERT_MARKER)
    check(len(asserts) == 1, f"B2 exactly one tile-assert raise ('{ASSERT_MARKER}') (found {len(asserts)})", sink)
    moving = _calls(fn, "_navigate_riding_out") + _calls(fn, "fly_to_destination")
    if asserts:
        a = asserts[0]
        # the `if` guarding it must test the TILE, not merely the map
        parent_if = next((n for n in ast.walk(fn) if isinstance(n, ast.If) and a in ast.walk(n)), None)
        test_src = ast.get_source_segment(src, parent_if.test) if parent_if else ""
        check("_here_tile()" in test_src and "LEAGUE_DOOR_APRON" in test_src,
              f"B2 the assertion tests the TILE: `{test_src}`", sink)
        check(bool(moving) and a.lineno > max(c.lineno for c in moving),
              f"B2 the assertion (line {a.lineno}) comes after every walk/flight (last line "
              f"{max((c.lineno for c in moving), default=None)})", sink)
    bounded_args = set()
    for call in _calls(fn, "_yield_bounded_by_frames"):
        for arg in call.args:
            bounded_args.add(id(arg))
    unbounded = [c.lineno for c in moving if id(c) not in bounded_args]
    check(bool(moving) and not unbounded,
          f"B3 every walk/flight in the bridge is bounded by _yield_bounded_by_frames (unbounded: {unbounded})", sink)


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def b4(src):
    tree = ast.parse(src)
    for fn_name, arm in (("prepare_and_open_the_league", "POKEBOT_CH24_FAULT_NOBRIDGE"),
                         ("return_to_league_door", "POKEBOT_CH24_FAULT_BRIDGEDEST")):
        seg = _strip_comments(ast.get_source_segment(src, _fn(tree, fn_name)) or "")
        check(f'"{arm}") == "1"' in seg, f"B4 {arm} is READ in {fn_name} (code, not a comment)")
        check(f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"), f"B4 {arm} is registered")


def b5(src, sink=None):
    seen: dict = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.endswith("_READINGS"):
                    seen.setdefault(t.id, []).append(node.lineno)
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    check(not dupes, f"B5 every module-level *_READINGS name is assigned once ({len(seen)} names; dupes {dupes})", sink)
    check("RETURN_BRIDGE_READINGS" in seen, "B5 RETURN_BRIDGE_READINGS exists", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — §Ch24 return bridge (`#26-ch24organic` gap 2)")
    print("=" * 92)
    src = LEAGUE_SRC.read_text(encoding="utf-8")
    print("\n== B1 where the bridge sits ==")
    b1(src)
    print("\n== B2/B3 the tile assertion, and the bounds ==")
    b2_b3(src)
    print("\n== B4 the arms ==")
    b4(src)
    print("\n== B5 no shadowed *_READINGS ==")
    b5(src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    anchor = "    # ---- THE RETURN BRIDGE (`#26-ch24organic` gap 2)"
    fly_bounded = "fly_to_destination(destination, fly), BRIDGE_FLY_FRAMES)))"
    assert src.count(anchor) == 1 and src.count(ASSERT_MARKER) == 1 and src.count(fly_bounded) == 1, \
        "mutation anchors moved — update the gate"
    for label, mutated, fn in (
        ("a door walk inserted BEFORE the bridge FAILS B1",
         src.replace(anchor, "    VR._navigate_riding_out(VR.EG, VR.LEAGUE_DOOR_APRON)\n" + anchor), b1),
        ("the tile assertion renamed away FAILS B2", src.replace(ASSERT_MARKER, "§Ch24 bridge: somewhere"), b2_b3),
        ("a SECOND `RETURN_BRIDGE_READINGS` assignment FAILS B5",
         src + "\nRETURN_BRIDGE_READINGS = ()\n", b5),
        ("an UNBOUNDED flight FAILS B3",
         src.replace("report[\"fly_finished\"] = bool((yield from _yield_bounded_by_frames(\n            " + fly_bounded,
                     "report[\"fly_finished\"] = bool((yield from fly_to_destination(destination, fly)))"), b2_b3),
    ):
        assert mutated != src, f"mutation '{label}' did not apply — update the gate"
        sink: list = []
        fn(mutated, sink)
        check(bool(sink), f"FAULT {label} ({len(sink)} caught)")

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
