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
  C4  every arm is registered in 29.
  C5  KI-118 / USER RULING 30 (`#27-boxfirsttype`, 2026-10-02): a TYPE-ONLY box pick is a FALLBACK. The REAL
      `StoryMode._counter_ladder` is DRIVEN with fakes (planner, ball check, hunt, box choice, party, badge count) on a
      production `StoryMode` shell — a guard in a loop is tested by driving it, never by reading it:
      - a credible pick is still registered at once (no planner);
      - a type-only pick is held; the planner and the hunt run; the pick is registered only where the ladder would
        otherwise give up (the planner raises, a resource blocker, no shortlist, the hunt finds nothing, no destination
        reachable), AFTER the hunt, and the record names it; a hunted catch wins and the held pick is NOT registered;
      - the once-per-boss latch: a second call registers nothing and plans nothing;
      - `POKEBOT_KI118_FAULT_TYPEONLYFIRST=1` restores the old immediate registration; `POKEBOT_R20_FAULT_NOBOXCOUNTER=1`
        still skips the box (nothing held, nothing registered);
      - the coupling the ladder relies on: the REAL `box_counter_choice` writes "own type" (exactly) for a type-only
        pick and "<move> scores N…" for a credible one.
FAULT ARMS (built in; each must FAIL): box-order ranking (C1), the full-registry withdraw (C3), box-first after the
planner (C3), setdefault registration (C3); and for C5, mutants of the REAL ladder source: a type-only pick taken at
once, a credible pick deferred, the fallback never registered, the fallback registered over a hunted catch, the fault
switch ignored, and the planner-failure point dropped.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_counterbox.py
"""
from __future__ import annotations

import ast
import inspect
import os
import pathlib
import re
import sys
import textwrap
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
ARMS = ("POKEBOT_R20_FAULT_NOBOXCOUNTER", "POKEBOT_R20_FAULT_ALLCOUNTERS", "POKEBOT_KI118_FAULT_TYPEONLYFIRST")
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


# ---------------------------------------------------------------------------------------------------------------------
# C5 — KI-118 / USER RULING 30: the type-only FALLBACK, by DRIVING the real `_counter_ladder` with fakes.
# ‼ Why a drive and not an AST read: the fallback is a guard at FIVE give-up points inside a loop, and its whole claim
# is about ORDER (planner, then hunt, then the fallback). A text check would pass a ladder that registers the pick at
# the top. The live counterpart is `--driver normanboxfirst` (arms XF, XF-CAUGHT, X13F, YF, XFAULT, WATTSON-F).
# ---------------------------------------------------------------------------------------------------------------------
NORMAN_CFG = {"keys": [(8, 1), (0, 0)], "name": "Norman", "ace_types": ("Normal",)}
KEY = (8, 1)
TYPE_ONLY = (0x0A0A0008, "Makuhita", 8, "own type")
CREDIBLE = (0x0A0A0013, "Makuhita", 13, "Vital Throw scores 210, own type")
FALLBACK_WHERE = "PC box (type-only fallback)"


def _cand(species, map_name, tile):
    """A planner candidate as the ladder reads it (`map_enum.name`/`.value`, `hunt_tile`, `huntable`)."""
    return {"species_name": species, "map_enum": types.SimpleNamespace(name=map_name, value=(24, len(map_name))),
            "hunt_tile": tile, "huntable": True}


MACHOP_C = _cand("Machop", "FIERY_PATH", (18, 19))
OTHER_C = _cand("Numel", "ROUTE112", (5, 5))


def _drive(gen):
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value


def run_ladder(ladder_fn, *, pick, planner_raises=False, candidates=(MACHOP_C,), resource=None, hunt_result=None,
               unreachable=(), env=None, mode=None):
    """ONE call of `ladder_fn(mode, NORMAN_CFG, 8, ['Fighting'])` with every collaborator faked, on a production
    `StoryMode` shell (`__new__`; the class constants and the REAL `_register_counter`, `_training_blocked`,
    `_note_training_unreachable` and `_here_map`). Returns (returned, mode, calls); `calls` is the ORDER of actions:
    'planner', 'hunt <map>', 'register <pid> <where>'. Every patch and env var is restored in `finally`."""
    import modules.pokemon_party as PP
    import modules.story.counter_plan as CP
    import plugins.custom_modes.story_mode as SM
    from modules.story.early_game import UnreachableDestinationError

    calls: list = []
    if mode is None:
        mode = SM.StoryMode.__new__(SM.StoryMode)
        mode._counter_hunts, mode._hunted_counter_pids, mode._hunted_counter_badges = {}, set(), {}
        mode._gym_tm_taught_moves, mode._training_unreachable = {}, set()

    def rec_register(pid, where):
        calls.append(f"register {pid:08X} {where}")
        SM.StoryMode._register_counter(mode, pid, where)

    def fake_find(needed, allow=None, max_results=5):
        calls.append("planner")
        if planner_raises:
            raise RuntimeError("planner exploded")
        return [dict(c) for c in candidates]

    def fake_hunt(candidate, needed):
        calls.append(f"hunt {candidate['map_enum'].name}")
        if candidate["map_enum"].name in unreachable:
            raise UnreachableDestinationError(f"cannot reach {candidate['map_enum'].name}")
        return hunt_result
        yield  # a generator, like the real hunt

    saved = (CH.box_counter_choice, CP.find_counter_candidates, CH.resource_blocker, CH.hunt, PP.get_party,
             PT.badge_count)
    saved_env = {k: os.environ.get(k) for k in ARMS}
    try:
        CH.box_counter_choice = lambda needed, exclude_pids=frozenset(), taught=None, mons=None: pick
        CP.find_counter_candidates = fake_find
        CH.resource_blocker = lambda: resource
        CH.hunt = fake_hunt
        PP.get_party = lambda: [types.SimpleNamespace(personality_value=0x341D550A)]
        PT.badge_count = lambda: 4
        for k in ARMS:
            os.environ.pop(k, None)
        os.environ.update(env or {})
        mode._register_counter = rec_register
        returned = _drive(ladder_fn(mode, NORMAN_CFG, 8, ["Fighting"]))
    finally:
        (CH.box_counter_choice, CP.find_counter_candidates, CH.resource_blocker, CH.hunt, PP.get_party,
         PT.badge_count) = saved
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        mode.__dict__.pop("_register_counter", None)
    return returned, mode, calls


def c5(ladder_fn, sink=None):
    pid, cred = f"{TYPE_ONLY[0]:08X}", f"{CREDIBLE[0]:08X}"
    fb = f"register {pid} {FALLBACK_WHERE}"
    r, m, calls = run_ladder(ladder_fn, pick=CREDIBLE)
    check(r is True and calls == [f"register {cred} PC box (box-first)"],
          f"C5 a CREDIBLE box pick is still registered at once: no planner, no hunt ({r}, {calls})", sink)
    r, m, calls = run_ladder(ladder_fn, pick=TYPE_ONLY)
    rec = m._counter_hunts.get(KEY, "")
    check(r is True and calls == ["planner", "hunt FIERY_PATH", fb],
          f"C5 a TYPE-ONLY pick is HELD: the planner, then the hunt, THEN the fallback registration ({r}, {calls})", sink)
    check("Machop@FIERY_PATH: none found" in rec and "fallback" in rec and f"pid={pid}" in rec,
          f"C5 ... and the record names the failed hunt and the fallback ({rec!r})", sink)
    r2, m, calls2 = run_ladder(ladder_fn, pick=TYPE_ONLY, mode=m)
    check(r2 is False and calls2 == [] and m._counter_hunts.get(KEY) == rec,
          f"C5 the once-per-boss latch holds: a second call plans and registers nothing ({r2}, {calls2})", sink)
    for label, kw, hunts in (
            ("the planner raises", dict(planner_raises=True), []),
            ("a resource blocker", dict(resource="no spare Poké Balls (the last ball is reserved)"), []),
            ("no shortlist", dict(candidates=()), []),
            ("no destination reachable", dict(candidates=(MACHOP_C, OTHER_C), unreachable={"FIERY_PATH", "ROUTE112"}),
             ["hunt FIERY_PATH", "hunt ROUTE112"])):
        r, m, calls = run_ladder(ladder_fn, pick=TYPE_ONLY, **kw)
        check(r is True and calls == ["planner", *hunts, fb] and "fallback" in m._counter_hunts.get(KEY, ""),
              f"C5 {label}: the held pick is registered as the fallback, last ({r}, {calls}, {m._counter_hunts})", sink)
    r, m, calls = run_ladder(ladder_fn, pick=TYPE_ONLY, hunt_result={"slot": None, "pid": 0x00C0FFEE})
    check(r is True and calls == ["planner", "hunt FIERY_PATH", "register 00C0FFEE PC box"]
          and TYPE_ONLY[0] not in m._hunted_counter_pids,
          f"C5 a hunted catch WINS: the catch is registered and the held type-only pick is NOT ({r}, {calls})", sink)
    r, m, calls = run_ladder(ladder_fn, pick=None)
    check(r is False and calls == ["planner", "hunt FIERY_PATH"]
          and m._counter_hunts.get(KEY) == "Machop@FIERY_PATH: none found",
          f"C5 no box pick: unchanged — the hunt finds nothing and the ladder gives up ({r}, {calls})", sink)
    r, m, calls = run_ladder(ladder_fn, pick=TYPE_ONLY, env={"POKEBOT_KI118_FAULT_TYPEONLYFIRST": "1"})
    check(r is True and calls == [f"register {pid} PC box (box-first)"],
          f"C5 POKEBOT_KI118_FAULT_TYPEONLYFIRST=1 restores the old behaviour: the type-only pick at once ({r}, {calls})",
          sink)
    r, m, calls = run_ladder(ladder_fn, pick=TYPE_ONLY, env={"POKEBOT_R20_FAULT_NOBOXCOUNTER": "1"})
    check(r is False and calls == ["planner", "hunt FIERY_PATH"],
          f"C5 POKEBOT_R20_FAULT_NOBOXCOUNTER=1 still skips the box: nothing held, nothing registered ({r}, {calls})",
          sink)


def c5_why(fn, sink=None):
    """The coupling the ladder relies on: the REAL `box_counter_choice` writes `why` == "own type" EXACTLY for a type-only
    pick and "<move> scores N…" for a credible one. If its wording changes, the ladder's credibility test changes."""
    mak8 = mon(21, "Makuhita", 8, ["Fighting"],
               [("Tackle", "Normal", 35), ("Focus Energy", "Normal", 0), ("Sand-attack", "Ground", 0)])
    mak13 = mon(22, "Makuhita", 13, ["Fighting"], [("Arm Thrust", "Fighting", 15), ("Vital Throw", "Fighting", 70)])
    w8, w13 = fn(["Fighting"], mons=[mak8]), fn(["Fighting"], mons=[mak13])
    check(bool(w8) and w8[3] == "own type", f"C5 a type-only pick's why is exactly 'own type' ({w8})", sink)
    check(bool(w13) and " scores " in w13[3] and w13[3].startswith("Vital Throw scores 210"),
          f"C5 a credible pick's why names its scoring move ({w13})", sink)


def ladder_source() -> str:
    import plugins.custom_modes.story_mode as SM

    return textwrap.dedent(inspect.getsource(SM.StoryMode._counter_ladder))


def compile_ladder(src: str):
    import plugins.custom_modes.story_mode as SM

    ns: dict = {}
    exec(compile(src, "<mutated _counter_ladder>", "exec"), dict(vars(SM)), ns)  # noqa: S102 - gate fault arm
    return ns["_counter_ladder"]


#: (label, pattern, replacement) mutants of the REAL ladder source; C5 must FAIL on each.
C5_MUTANTS = (
    ("a type-only pick taken at once", r'" scores " in str\(_why\)', "True"),
    ("a credible pick deferred too", r'" scores " in str\(_why\)', "False"),
    ("the fallback never registered", r"if _fallback is None:", "if True:"),
    ("the fallback registered over a hunted catch",
     r"(\n[ \t]+)(self\._counter_hunts\[key\] = f\"caught )", r"\1_stop_or_fall_back('caught')\1\2"),
    ("the fault switch ignored", r'"POKEBOT_KI118_FAULT_TYPEONLYFIRST"\) == "1"',
     '"POKEBOT_KI118_FAULT_TYPEONLYFIRST") == "never"'),
    ("the planner-failure point dropped", r'(\n[ \t]+)return _stop_or_fall_back\("planner failed"\)',
     r'\1self._counter_hunts[key] = "planner failed"\1return False'),
)


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
    print("\n== C5 the KI-118 type-only fallback (the REAL _counter_ladder, DRIVEN with fakes) ==")
    import plugins.custom_modes.story_mode as SM

    c5(SM.StoryMode._counter_ladder)
    c5_why(CH.box_counter_choice)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    lsrc5 = ladder_source()
    for label, pat, rep in C5_MUTANTS:
        mutated, n = re.subn(pat, rep, lsrc5, count=1)
        check(n == 1, f"(fault-arm mutation applied exactly once: {label})")
        sink = []
        c5(compile_ladder(mutated), sink)
        check(bool(sink), f"FAULT {label} FAILS C5 ({len(sink)} caught)")
    sink = []
    c5(compile_ladder(lsrc5), sink)
    check(not sink, f"(control: the UNMUTATED source, compiled the same way, PASSES C5 — {sink})")
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
