r"""GATE — RULING 20 Phase 1, increment B (counters): box-first before the hunt, and the heal withdraws only OWED counters.

WHY (recon note `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, site "counter"):
- a counter the run already OWNS in the PC was invisible to the ladder, which hunted a new one (or stopped honestly);
- `box_counter_pid` (lenient, first box-order match, pinned by a parity gate) would spend the ladder's one action on a
  Rock Smash or Mud-Slap carrier;
- the heal's counter withdraw read the never-cleared registry, so after increment A lets make-room box an EXPIRED counter,
  the next heal collects it again (and `find_in_box`'s box order can pick it over the counter owed now: hazard H1).

  C1  `counter_hunt.box_counter_choice` (PURE with `mons=`): own type, or a damaging move of a needed type scoring
      base power × 2 × STAB >= 75; never a party PID, an egg, or a gym-TM-taught (pid, move) pair; ranked by credible
      move, score, type, level — not box order; None when nothing needed.
  C2  `pc_trip.owed_counter_pids`: owed while the badge count is the registration count; no record ⇒ owed; unaffected
      by the deposit arms (`NOPROTECT` must not switch withdraws off); `deposit_protected_pids` still honours its arms.
  C3  WIRING (AST):
      - the heal's counter withdraw source is `owed_counter_pids(...)`, the full registry only under the arm
        `POKEBOT_R20_FAULT_ALLCOUNTERS`;
      - `_counter_ladder` asks `box_counter_choice` AFTER the "started" mark and BEFORE `find_counter_candidates` and
        `resource_blocker`, unless `POKEBOT_R20_FAULT_NOBOXCOUNTER`, and registers through `_register_counter`;
      - `_register_counter` overwrites the badge count (`=`, never `setdefault`), so an expired counter becomes owed again.
  C4  both arms are registered in 29.
FAULT ARMS (built in; each must FAIL): box-order ranking (C1), the full-registry withdraw (C3), box-first after the
planner (C3), setdefault registration (C3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_counterbox.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.counter_hunt as CH  # noqa: E402
import modules.story.pc_trip as PT  # noqa: E402

CH_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "counter_hunt.py"
HLA_SRC = ROOT / "sandbox-pokebot" / "modules" / "modes" / "util" / "higher_level_actions.py"
SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARMS = ("POKEBOT_R20_FAULT_NOBOXCOUNTER", "POKEBOT_R20_FAULT_ALLCOUNTERS")
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def mon(pid, species, level, types_, moves, egg=False):
    """moves: [(name, type, base_power)]"""
    return types.SimpleNamespace(
        personality_value=pid, level=level, is_egg=egg,
        species=types.SimpleNamespace(name=species, types=[types.SimpleNamespace(name=t) for t in types_]),
        moves=[types.SimpleNamespace(move=types.SimpleNamespace(name=n, base_power=bp, type=types.SimpleNamespace(name=t)))
               for n, t, bp in moves])


WINONA = ["Rock", "Ice", "Dragon"]


def c1(fn, sink=None):
    smash = mon(1, "Makuhita", 20, ["Fighting"], [("Rock Smash", "Fighting", 40), ("Rock Tomb", "Rock", 50)])
    rs_only = mon(2, "Zigzagoon", 30, ["Normal"], [("Rock Smash", "Fighting", 40), ("Headbutt", "Normal", 70)])
    mudslap = mon(3, "Marshtomp", 25, ["Water", "Ground"], [("Mud-Slap", "Ground", 20)])
    slugma = mon(4, "Slugma", 15, ["Fire"], [("Rock Throw", "Rock", 50), ("Ember", "Fire", 40)])
    snorunt = mon(5, "Snorunt", 20, ["Ice"], [("Icy Wind", "Ice", 55)])
    geodude = mon(6, "Geodude", 15, ["Rock", "Ground"], [("Tackle", "Normal", 35)])
    weak_rock = mon(7, "Nosepass", 30, ["Rock"], [("Tackle", "Normal", 35)])
    pick = lambda r: (r[0] if r else None)  # noqa: E731
    check(pick(fn(WINONA, mons=[rs_only])) is None,
          "C1 a mon whose only needed-type move is below the floor (Rock Smash is Fighting; no Rock move) is rejected", sink)
    check(pick(fn(["Ground"], mons=[mudslap])) == 3,
          "C1 own type is enough (Marshtomp is Ground for a Ground need) even with a weak move", sink)
    check(pick(fn(["Ground"], mons=[mon(8, "Zigzagoon", 30, ["Normal"], [("Mud-Slap", "Ground", 20)])])) is None,
          "C1 a Mud-Slap-only non-Ground mon is rejected (20 × 2 = 40 < 75)", sink)
    check(pick(fn(WINONA, mons=[slugma, snorunt])) == 5,
          "C1 ranking, not box order: Snorunt's STAB Icy Wind (165) beats the earlier Slugma's Rock Throw (100)", sink)
    check(pick(fn(WINONA, mons=[geodude, weak_rock, slugma])) == 4,
          "C1 a credible move outranks an own-type match with no credible move", sink)
    check(pick(fn(WINONA, mons=[slugma], exclude_pids=frozenset({4}))) is None, "C1 a party PID is never picked", sink)
    check(pick(fn(WINONA, mons=[mon(9, "Egg", 1, ["Rock"], [], egg=True)])) is None, "C1 an egg is never picked", sink)
    check(pick(fn(WINONA, mons=[smash], taught={(1, "Rock Tomb")})) is None,
          "C1 a gym-TM-taught (pid, move) pair is not evidence of an answer (RULING 19)", sink)
    check(pick(fn(WINONA, mons=[smash])) == 1, "C1 ... the same mon with Rock Tomb NOT taught by a gym TM is accepted", sink)
    check(fn([], mons=[slugma]) is None, "C1 nothing needed ⇒ None", sink)


def c2(sink=None):
    mode = types.SimpleNamespace(_hunted_counter_pids={10, 11, 12}, _hunted_counter_badges={10: 5, 11: 4})
    saved = PT.badge_count
    try:
        PT.badge_count = lambda: 5
        owed = PT.owed_counter_pids(mode)
        os.environ["POKEBOT_R20_FAULT_NOPROTECT"] = "1"
        try:
            owed_np, dep_np = PT.owed_counter_pids(mode), PT.deposit_protected_pids(mode)
        finally:
            os.environ.pop("POKEBOT_R20_FAULT_NOPROTECT", None)
        os.environ["POKEBOT_R20_FAULT_NOEXPIRE"] = "1"
        try:
            dep_ne = PT.deposit_protected_pids(mode)
        finally:
            os.environ.pop("POKEBOT_R20_FAULT_NOEXPIRE", None)
        dep = PT.deposit_protected_pids(mode)
    finally:
        PT.badge_count = saved
    check(owed == {10, 12}, f"C2 owed at 5 badges: 10 (registered at 5) and 12 (no record); 11 (at 4) expired ({owed})", sink)
    check(owed_np == {10, 12} and dep_np == set(),
          f"C2 NOPROTECT empties the DEPOSIT protection only; the withdraw's owed set is unchanged ({owed_np}, {dep_np})",
          sink)
    check(dep == owed and dep_ne == {10, 11, 12},
          f"C2 deposit_protected_pids = the owed set; NOEXPIRE = the whole registry ({dep}, {dep_ne})", sink)


def fn_src(src, name):
    return ast.unparse(next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name))


def c3(hla: str, sm: str, sink=None):
    heal = fn_src(hla, "heal_in_pokemon_center")
    check("_owed_counters(_ctx.bot_mode_instance)" in heal and "POKEBOT_R20_FAULT_ALLCOUNTERS" in heal
          and "withdraw_pid_source(getattr(_ctx.bot_mode_instance, '_wanted_hm_learner_pids', None), _counter_src)" in heal,
          "C3 the heal's counter withdraw source is owed_counter_pids (full registry only under ALLCOUNTERS)", sink)
    ladder = fn_src(sm, "_counter_ladder")
    i_started = ladder.find("self._counter_hunts[key] = 'started'")
    i_box = ladder.find("counter_hunt.box_counter_choice(")
    i_plan = ladder.find("counter_plan.find_counter_candidates(")
    i_res = ladder.find("counter_hunt.resource_blocker()")
    check(-1 < i_started < i_box < i_plan and i_box < i_res,
          f"C3 box-first comes after the 'started' mark and before the planner and the ball check "
          f"(started={i_started} box={i_box} planner={i_plan} resource={i_res})", sink)
    check("POKEBOT_R20_FAULT_NOBOXCOUNTER" in ladder and ladder.count("self._register_counter(") >= 2,
          "C3 the NOBOXCOUNTER arm is read in the ladder; both the box-first and the hunt paths register via "
          "_register_counter", sink)
    reg_node = next(n for n in ast.walk(ast.parse(sm)) if isinstance(n, ast.FunctionDef) and n.name == "_register_counter")
    # ‼ Inspect CALLS, not text: the docstring itself says "never `setdefault`" (rule 6: a gate must not fire on a mention).
    calls_setdefault = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "setdefault"
                           for n in ast.walk(reg_node))
    check("self._hunted_counter_badges[pid] = badge_count()" in ast.unparse(reg_node) and not calls_setdefault,
          "C3 _register_counter OVERWRITES the badge count, so an expired counter becomes owed again", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 20 Phase 1 (B): box-first counters + the owed-only withdraw")
    print("=" * 92)
    for a in ARMS + ("POKEBOT_R20_FAULT_NOPROTECT", "POKEBOT_R20_FAULT_NOEXPIRE"):
        os.environ.pop(a, None)
    hla, sm, ch = (p.read_text(encoding="utf-8") for p in (HLA_SRC, SM_SRC, CH_SRC))
    print("\n== C1 box_counter_choice ==")
    c1(CH.box_counter_choice)
    print("\n== C2 owed_counter_pids ==")
    c2()
    print("\n== C3 wiring ==")
    c3(hla, sm)
    print("\n== C4 the arms ==")
    reg = REGISTRY.read_text(encoding="utf-8")
    for a in ARMS:
        check(a in (hla + sm) and f"`{a}`" in reg, f"C4 {a} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    node = next(n for n in ast.walk(ast.parse(ch)) if isinstance(n, ast.FunctionDef) and n.name == "box_counter_choice")
    src = ast.get_source_segment(ch, node)
    mutated, n = re.subn(r"if best is None or key > best\[0\]:", "if best is None:", src, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once: box-order ranking)")
    ns: dict = {}
    exec(compile(mutated, "<mutated box_counter_choice>", "exec"), dict(CH.__dict__), ns)  # noqa: S102 - gate fault arm
    sink: list = []
    c1(ns["box_counter_choice"], sink)
    check(bool(sink), f"FAULT box-order ranking FAILS C1 ({len(sink)} caught)")
    for label, text, pat, rep in (
            ("the full-registry withdraw", hla, r"else _owed_counters\(_ctx\.bot_mode_instance\)",
             'else getattr(_ctx.bot_mode_instance, "_hunted_counter_pids", None)'),
            ("setdefault registration", sm, r"self\._hunted_counter_badges\[pid\] = badge_count\(\)",
             "self._hunted_counter_badges.setdefault(pid, badge_count())")):
        mutated, n = re.subn(pat, rep, text, count=1)
        check(n == 1, f"(fault-arm mutation applied exactly once: {label})")
        sink = []
        c3(mutated if text is hla else hla, mutated if text is sm else sm, sink)
        check(bool(sink), f"FAULT {label} FAILS C3 ({len(sink)} caught)")
    # Box-first moved AFTER the planner: swap the two blocks' order by moving the planner call above the started mark.
    ladder_node = next(n for n in ast.walk(ast.parse(sm)) if isinstance(n, ast.FunctionDef) and n.name == "_counter_ladder")
    lsrc = ast.get_source_segment(sm, ladder_node)
    moved = lsrc.replace("counter_hunt.box_counter_choice(", "counter_hunt.box_counter_choice_DISABLED(", 1) + (
        "\n        counter_hunt.box_counter_choice(needed)\n")
    sink = []
    c3(hla, sm.replace(lsrc, moved, 1), sink)
    check(bool(sink), f"FAULT box-first after the planner FAILS C3 ({len(sink)} caught)")

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
