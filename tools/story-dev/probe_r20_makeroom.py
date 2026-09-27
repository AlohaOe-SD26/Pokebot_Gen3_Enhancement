r"""GATE — RULING 20 Phase 1, increment A: ONE deposit-victim rule for every LIVE make-room path (2026-09-27).

WHY (`ai-research-notes/2026-09-27-ruling20-phase1-DESIGN.md`): with catching always on the party fills to 6, and
`#24-partycap` lost 10 of its 16 runs to "no Surf learner and no free slot". Today's live make-room paths:
- could box a counter hunted for the very next boss (only the OFF rotation path read the protected set);
- gave up entirely on a level-even team, so the HM errand raised "party is full" and derailed.

  M1  `make_room_victim` (PURE):
      - dead weight first, the lowest level first (unchanged);
      - never a protected or excluded PID;
      - for a REQUIRED errand with no dead weight: the lowest-level unprotected member, never an egg, never the sole
        carrier of an HM, never the last living battler;
      - not required ⇒ None (the old decline);
      - everyone protected ⇒ None.
  M2  `deposit_protected_pids`: a counter registered at badge count N is protected while the count is N, and ordinary
      once it passes N; a PID with no recorded count stays protected; the arms NOPROTECT / NOEXPIRE restore the old sets.
  M3  WIRING (AST):
      - `deposit_one_dead_weight` asks `make_room_victim(..., required=required, protected=deposit_protected_pids())`;
      - `withdraw_from_box` asks it with `required=True`, `exclude_pids` and `protected=deposit_protected_pids()`;
      - the `_needs_party_slot` piggyback passes `required=True`;
      - `story_mode` records `_hunted_counter_badges[pid] = badge_count()` and resets it per run.
  M4  the three arms are read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): NOREQUIRED (M1's level-even case), NOPROTECT (M1's protected-counter case),
NOEXPIRE (M2's expiry case), a withdraw asking without `protected=` (M3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_makeroom.py
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

import modules.story.pc_trip as PT  # noqa: E402

PT_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "pc_trip.py"
HLA_SRC = ROOT / "sandbox-pokebot" / "modules" / "modes" / "util" / "higher_level_actions.py"
SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARMS = ("POKEBOT_R20_FAULT_NOREQUIRED", "POKEBOT_R20_FAULT_NOPROTECT", "POKEBOT_R20_FAULT_NOEXPIRE")
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def mon(pid, species, level, moves=(("Tackle", 40),), *, egg=False, hp=10):
    learned = [types.SimpleNamespace(move=types.SimpleNamespace(name=n, base_power=bp)) for n, bp in moves]
    return types.SimpleNamespace(personality_value=pid, species=types.SimpleNamespace(name=species), level=level,
                                 moves=learned, is_egg=egg, current_hp=hp)


def m1(fn, sink=None):
    even = [mon(1, "A", 30), mon(2, "B", 31), mon(3, "C", 30), mon(4, "D", 32), mon(5, "E", 33), mon(6, "F", 34)]
    dead = [mon(1, "A", 30), mon(2, "B", 30), mon(3, "Weak", 10), mon(4, "D", 30), mon(5, "E", 30), mon(6, "F", 30)]
    pick = lambda r: (r[0].personality_value if r else None)  # noqa: E731
    check(pick(fn(dead)) == 3, "M1 dead weight first: the L10 among L30s (the unchanged rule)", sink)
    check(fn(even) is None, "M1 a level-even team, NOT required ⇒ None (the old decline)", sink)
    check(pick(fn(even, required=True)) == 1,
          "M1 a level-even team, REQUIRED ⇒ the lowest-level unprotected member (pid 1, L30, first of the ties)", sink)
    check(pick(fn(dead, protected={3})) is None,
          "M1 the only dead weight is a protected counter, not required ⇒ None — never box the counter", sink)
    check(pick(fn(dead, protected={3}, required=True)) not in (None, 3),
          "M1 ... REQUIRED ⇒ someone else, never the protected counter", sink)
    check(pick(fn(even, required=True, exclude_pids={1})) == 3,
          "M1 an excluded PID (the mon this visit collects) is skipped ⇒ the next lowest (pid 3)", sink)
    surf = [mon(1, "Surfer", 20, (("Surf", 90),)), mon(2, "B", 31), mon(3, "C", 30), mon(4, "D", 32),
            mon(5, "E", 33), mon(6, "F", 34)]
    check(pick(fn(surf, required=True)) not in (None, 1),
          "M1 the party's sole Surf carrier (even at the lowest level) is never the required victim", sink)
    eggy = [mon(1, "Egg", 1, (), egg=True), mon(2, "B", 31), mon(3, "C", 30), mon(4, "D", 32), mon(5, "E", 33),
            mon(6, "F", 34)]
    check(pick(fn(eggy, required=True)) == 3, "M1 an egg is never the victim (the next lowest, pid 3, goes)", sink)
    last = [mon(1, "Alive", 20), mon(2, "B", 40, hp=0), mon(3, "C", 40, hp=0), mon(4, "D", 40, hp=0),
            mon(5, "E", 40, hp=0), mon(6, "F", 40, hp=0)]
    check(pick(fn(last, required=True)) not in (None, 1),
          "M1 the last living battler is never the victim (the game refuses that deposit)", sink)
    check(fn(even, required=True, protected={1, 2, 3, 4, 5, 6}) is None, "M1 everyone protected ⇒ None", sink)


def m2(sink=None):
    mode = types.SimpleNamespace(_hunted_counter_pids={10, 11, 12}, _hunted_counter_badges={10: 3, 11: 2})
    saved = PT.badge_count
    try:
        PT.badge_count = lambda: 3
        at3 = PT.deposit_protected_pids(mode)
        PT.badge_count = lambda: 4
        at4 = PT.deposit_protected_pids(mode)
    finally:
        PT.badge_count = saved
    check(at3 == {10, 12}, f"M2 at 3 badges: pid 10 (registered at 3) and 12 (no record) protected; 11 (at 2) not ({at3})",
          sink)
    check(at4 == {12}, f"M2 at 4 badges: pid 10's badge is earned ⇒ ordinary; 12 (no record) still protected ({at4})", sink)


def wiring(pt: str, hla: str, sm: str, sink=None):
    def fn_src(src, name):
        n = next(x for x in ast.walk(ast.parse(src)) if isinstance(x, ast.FunctionDef) and x.name == name)
        return ast.unparse(n)

    dep, wd = fn_src(pt, "deposit_one_dead_weight"), fn_src(pt, "withdraw_from_box")
    check("make_room_victim(party, required=required, protected=deposit_protected_pids())" in dep,
          "M3 deposit_one_dead_weight asks the ONE rule with required + the protected set", sink)
    check("make_room_victim(party, exclude_pids=pids or (), required=True, protected=deposit_protected_pids())" in wd,
          "M3 withdraw_from_box asks it with required=True, exclude_pids and the protected set", sink)
    check("yield from deposit_one_dead_weight(required=True)" in ast.unparse(ast.parse(hla)),
          "M3 the _needs_party_slot piggyback passes required=True", sink)
    sm_code = ast.unparse(ast.parse(sm))
    check("self._hunted_counter_badges[pid] = badge_count()" in sm_code
          and "self._hunted_counter_badges: dict = {}" in sm_code,
          "M3 story_mode records the badge count per counter and resets it per run", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 20 Phase 1 (A): one deposit-victim rule for every live make-room path")
    print("=" * 92)
    for a in ARMS:
        os.environ.pop(a, None)
    pt, hla, sm = (p.read_text(encoding="utf-8") for p in (PT_SRC, HLA_SRC, SM_SRC))
    print("\n== M1 the victim rule ==")
    m1(PT.make_room_victim)
    print("\n== M2 the protected set and its expiry ==")
    m2()
    print("\n== M3 wiring ==")
    wiring(pt, hla, sm)
    print("\n== M4 the arms ==")
    reg = REGISTRY.read_text(encoding="utf-8")
    for a in ARMS:
        check(f'environ.get("{a}") == "1"' in pt and f"`{a}`" in reg, f"M4 {a} is read in production and registered")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    for arm, part in (("POKEBOT_R20_FAULT_NOREQUIRED", "m1"), ("POKEBOT_R20_FAULT_NOPROTECT", "m1+m2"),
                      ("POKEBOT_R20_FAULT_NOEXPIRE", "m2")):
        sink: list = []
        os.environ[arm] = "1"
        try:
            if arm.endswith("NOPROTECT"):
                # NOPROTECT empties the protected set at its SOURCE: route it through the real function.
                m1(lambda party, **kw: PT.make_room_victim(
                    party, **{**kw, "protected": PT.deposit_protected_pids(types.SimpleNamespace(
                        _hunted_counter_pids=set(kw.get("protected", ())), _hunted_counter_badges={}))}), sink)
            elif part == "m1":
                m1(PT.make_room_victim, sink)
            else:
                m2(sink)
        finally:
            os.environ.pop(arm, None)
        check(bool(sink), f"FAULT {arm} FAILS {part} ({len(sink)} caught)")
    sink = []
    import re

    mutated, n = re.subn(r"required=True,\s*protected=deposit_protected_pids\(\)\)", "required=True)", pt, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once)")
    wiring(mutated, hla, sm, sink)
    check(bool(sink), f"FAULT a withdraw asking without protected= FAILS M3 ({len(sink)} caught)")

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
