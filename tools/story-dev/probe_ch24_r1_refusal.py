r"""GATE — §Ch24 R1, THE READINESS REFUSAL: the decision, its PLACE in the leg, and its two arms.

WHY THIS EXISTS (`#26-ch24organic`, 2026-09-26)
-----------------------------------------------
Until 2026-09-26 nothing refused an under-levelled party before the one-way, nurse-less Elite Four:
`prepare_and_open_the_league` only RECORDED `below_floor_after` (no `E1-READY`) and walked in anyway, and
`enter_the_league` says "NO READINESS CHECK HERE, ON PURPOSE" because it expects that leg to decide. R1
now raises there. What makes it worth anything is WHERE it sits, so that is what this gate pins:

  G1  `ch24_readiness_shortfall` (PURE): [] exactly when nobody is below the floor AND every basket line
      is met; otherwise one NAMED reason per conjunct (PIDs for levels, `have/need` per short line).
  G2  In `prepare_and_open_the_league`: the R1 raise comes AFTER the training call and BEFORE the leg's
      first move toward the door (`_navigate_riding_out(..., LEAGUE_DOOR_APRON)`, `_walk_through_warp`)
      and before the guard talk (`press_button`) — `ENTERED_ELITE_FOUR` is permanent, so a refusal after
      the talk would be too late.
  G3  The R1 block adds NO `yield` ⇒ a READY party's trajectory is unchanged by construction (no frames).
  G4  Both production arms are read where they claim (`NOTRAIN` in `train_for_league`, `NOREADY` in
      `prepare_and_open_the_league`), comments stripped so a MENTION cannot satisfy it; both registered.

FAULT ARMS (run every time; a gate that cannot fail is decoration — CLAUDE.md rule 6): a decision that
ignores the basket must FAIL G1; a door walk inserted before R1 must FAIL G2; a `yield` inserted into the
R1 block must FAIL G3; a renamed refusal must FAIL G2 (not be silently "not found ⇒ ok").

(Not to be confused with `probe_ch24_readiness.py`, an older READ-ONLY emulator probe of party stats and
bag, or `probe_ch24_readiness_inputs.py`, the observe-only probe of R1's inputs per fixture.)

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_r1_refusal.py
"""
from __future__ import annotations

import ast
import io
import sys
import tokenize
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.story import pokemon_league as PL  # noqa: E402
from modules.story import victory_road as VR  # noqa: E402

LEAGUE_SRC = SANDBOX / "modules" / "story" / "pokemon_league.py"
MARKER = "§Ch24 R1: REFUSING"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


FULL = {name: qty for name, qty in VR.LEAGUE_BASKET}
ZIG = (0x33CB74C3, "Zigzagoon", 19)
CAST = (0xC978D14E, "Castform", 36)


WAIL = (0xFA51ECF3, "Wailord", 47)


def g1(decide, sink=None) -> None:
    """`decide(below, stock, *, party_size, floor=65)` — USER RULING 15: enter once min(4, size) are at the floor."""
    check(decide([], dict(FULL), party_size=6) == [], "G1 nobody below + exact basket ⇒ [] (enter)", sink)
    check(decide([], {**FULL, "Potion": 1, "Nugget": 2}, party_size=6) == [], "G1 extra bag items change nothing", sink)
    r = decide([ZIG, CAST], dict(FULL), party_size=6)
    check(r == [], f"G1 RULING 15: two below, FOUR at the floor ⇒ [] (the proven-winning shape enters): {r}", sink)
    r = decide([ZIG, CAST, WAIL], dict(FULL), party_size=6)
    check(len(r) == 1 and "below the L65 floor" in r[0] and "only 3 of 6" in r[0] and "needs 4" in r[0]
          and "Zigzagoon#33CB74C3 L19" in r[0] and "Wailord#FA51ECF3 L47" in r[0],
          f"G1 RULING 15: three below, only THREE at the floor ⇒ ONE level reason naming the PIDs: {r}", sink)
    r = decide([ZIG], dict(FULL), party_size=3)
    check(len(r) == 1 and "only 2 of 3" in r[0] and "needs 3" in r[0],
          f"G1 a 3-mon party needs all three (min(4, size)): {r}", sink)
    r = decide([], {**FULL, "Hyper Potion": 29}, party_size=6)
    check(r == ["League basket short: Hyper Potion 29/30"], f"G1 one short line ⇒ exactly it: {r}", sink)
    r = decide([], {k: v for k, v in FULL.items() if k != "Revive"}, party_size=6)
    check(r == ["League basket short: Revive 0/3"], f"G1 a MISSING line reads as 0/need: {r}", sink)
    r = decide([ZIG, CAST, WAIL], {}, party_size=6)
    check(len(r) == 2 and "below" in r[0] and r[1].startswith("League basket short:"),
          f"G1 both conjuncts fail ⇒ two reasons, levels first: {r}", sink)
    r = decide([ZIG, CAST, WAIL], dict(FULL), party_size=6, floor=40)
    check(len(r) == 1 and "below the L40 floor" in r[0], f"G1 the floor PARAMETER is what the reason names: {r}",
          sink)


def _prepare(tree: ast.Module) -> ast.FunctionDef:
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "prepare_and_open_the_league")


def _calls(fn, attr: str) -> list:
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if name == attr:
                out.append(n)
    return out


def g2_g3(src: str, sink=None) -> None:
    tree = ast.parse(src)
    fn = _prepare(tree)
    raises = [n for n in ast.walk(fn) if isinstance(n, ast.Raise)
              and MARKER in (ast.get_source_segment(src, n) or "")]
    check(len(raises) == 1, f"G2 exactly one R1 raise ('{MARKER}') in prepare_and_open_the_league "
          f"(found {len(raises)})", sink)
    if len(raises) != 1:
        return
    r_line = raises[0].lineno
    train = [c.lineno for c in _calls(fn, "train_for_league")]
    door = [c.lineno for c in _calls(fn, "_navigate_riding_out")
            if "LEAGUE_DOOR_APRON" in (ast.get_source_segment(src, c) or "")]
    walk = [c.lineno for c in _calls(fn, "_walk_through_warp")]
    press = [c.lineno for c in _calls(fn, "press_button")]
    check(bool(train) and max(train) < r_line, f"G2 training (line {train}) runs BEFORE R1 (line {r_line})", sink)
    moves = door + walk + press
    first_move = min(moves) if moves else None
    check(first_move is not None and r_line < first_move,
          f"G2 R1 (line {r_line}) precedes the first door walk / warp / guard press (line {first_move})", sink)
    # G3 — the statements from `left = ch24_trainees_below_floor(...)` through the R1 `if` add no yield.
    body = fn.body
    i_left = next(i for i, s in enumerate(body) if isinstance(s, ast.Assign)
                  and "ch24_trainees_below_floor" in (ast.get_source_segment(src, s) or "")
                  and any(getattr(t, "id", None) == "left" for t in s.targets))
    i_r1 = next(i for i, s in enumerate(body) if s.lineno <= r_line <= s.end_lineno)
    yields = [n.lineno for s in body[i_left:i_r1 + 1] for n in ast.walk(s)
              if isinstance(n, (ast.Yield, ast.YieldFrom))]
    check(not yields, f"G3 the R1 block (lines {body[i_left].lineno}-{body[i_r1].end_lineno}) adds no yield "
          f"{yields or ''}", sink)


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def g4(src: str) -> None:
    tree = ast.parse(src)
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for fn_name, arm in (("train_for_league", "POKEBOT_CH24_FAULT_NOTRAIN"),
                         ("prepare_and_open_the_league", "POKEBOT_CH24_FAULT_NOREADY")):
        seg = _strip_comments(ast.get_source_segment(src, fns[fn_name]) or "")
        check(f'"{arm}") == "1"' in seg, f"G4 {arm} is READ in {fn_name} (code, not a comment)")
    reg = (Path(__file__).resolve().parents[2] / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md")
    text = reg.read_text(encoding="utf-8")
    for arm in ("POKEBOT_CH24_FAULT_NOTRAIN", "POKEBOT_CH24_FAULT_NOREADY"):
        check(f"`{arm}`" in text, f"G4 {arm} is registered in 29-DISABLED-FEATURES-REGISTRY.md")


def main() -> int:
    print("=" * 92)
    print("GATE — §Ch24 R1 readiness refusal (`#26-ch24organic`)")
    print("=" * 92)
    src = LEAGUE_SRC.read_text(encoding="utf-8")

    print("\n== G1 the decision (pure) ==")
    g1(PL.ch24_readiness_shortfall)
    print("\n== G2/G3 where R1 sits, and that it adds no frames ==")
    g2_g3(src)
    print("\n== G4 the two production arms ==")
    g4(src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    g1(lambda below, stock, party_size, floor=65, basket=None:
       PL.ch24_readiness_shortfall(below, dict(FULL), party_size=party_size, floor=floor), sink)
    check(bool(sink), f"FAULT a decision that ignores the basket FAILS G1 ({len(sink)} case(s) caught)")

    def strict_all_six(below, stock, party_size, floor=65, basket=None):
        """The pre-RULING-15 rule: any member below the floor refuses."""
        r = [] if not below else [f"{len(below)} mōn below the L{floor} floor — only {party_size - len(below)} of "
                                  f"{party_size} at it, RULING 15 needs 4: x"]
        return r + [x for x in PL.ch24_readiness_shortfall([], stock, party_size=party_size, floor=floor)]
    sink = []
    g1(strict_all_six, sink)
    check(bool(sink), f"FAULT the pre-RULING-15 strict all-six rule FAILS G1 ({len(sink)} case(s) caught)")

    anchor = "    # ---- R1: THE READINESS REFUSAL"
    assert src.count(anchor) == 1, "mutation anchor moved — update the gate"
    for label, mutated in (
        ("a door walk inserted BEFORE R1",
         src.replace(anchor, "    VR._navigate_riding_out(VR.EG, VR.LEAGUE_DOOR_APRON)\n" + anchor)),
        ("a yield inserted INTO the R1 block",
         src.replace("    report[\"readiness_refusal\"] = reasons\n",
                     "    yield\n    report[\"readiness_refusal\"] = reasons\n")),
        ("the refusal renamed (not found must FAIL, not pass)", src.replace(MARKER, "§Ch24 R1: renamed")),
    ):
        assert mutated != src, f"mutation '{label}' did not apply — update the gate"
        sink = []
        g2_g3(mutated, sink)
        check(bool(sink), f"FAULT {label} FAILS G2/G3 ({len(sink)} caught)")

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
