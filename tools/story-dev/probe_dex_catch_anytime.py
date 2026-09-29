r"""GATE (pure) — USER RULING 24 step 2: with `POKEBOT_R24_CATCHHURT=1` a post-gym-1 dex catch is started even while the
party is HURT, and a LOST dex catch battle is filed apart from the map's defeat counters (C4) (2026-09-29).

WHY: the user ruled (`06`, 2026-09-28): *"catching should always be available … even in training and wounded pokemon. If
the bot whites out or the training pokemon faints, thats ok"*. The fence refused every post-gym-1 catch while any battler
was below full HP. The lift must remove THAT refusal only. And because the ruling accepts losing such a battle, its loss
must not count toward survival mode (3+ defeats on a map ⇒ flee every wild, wanted ones included) or a boss's loss
history on that map.
  A1  OFF, hurt: refused "not at full strength" (the old behaviour).
  A2  ON, hurt: admitted.
  A3-A7 ON, hurt, one later gate tripped each: training, the reserve, a full PC, the attempt cap, expected throws —
      each still refuses for its own reason.
  A8  ON, hurt, a hunt armed: refused (checked earlier).        A9  ON, a resource block: refused, verbatim.
  A10 ON, before gym 1, hurt: team building, unchanged.        A12 ON, party 4 (no open fence), hurt: still "runway".
  A11 by AST: the adapter passes `lift_health=self._r24_catchhurt`.
  A13 `reset_per_run_state` reads the flag.                    A14 the four flags are registered in 29.
  D1  a stubbed `on_battle_ended(Lost)` on an open `dex` catch: ON files it in `_catch_defeat_counts` and leaves
      `_defeat_counts` alone; OFF adds 1 to `_defeat_counts`.
  D2  the same with a `team` catch: `_defeat_counts` +1 in BOTH arms (pre-gym-1 accounting unchanged).
  D3  the same with no catch open (an ordinary loss), ON: `_defeat_counts` +1.
  D4-D6 the same with an `hm`, `counter` or `shiny` catch open, ON: `_defeat_counts` +1 (C4 files DEX losses only).
FAULT ARMS (built in; the unmutated subject must pass first; each must FAIL):
  F1  `POKEBOT_R24_FAULT_LIFTEARLY=1`: EXACTLY A3-A7 go red (the admit moved before the later gates).
  F2  `POKEBOT_R24_FAULT_KINDLATE=1`: D1 goes red (the kind read after `_r20_catch_end` cleared it).
  F3  `POKEBOT_R24_FAULT_TEAMLOSS=1`: D2 goes red.
  F4  an adapter passing `lift_health=False` fails A11; F5 the keyword kept only in a COMMENT still fails A11.
  F6  a source mutant whose C4 files `hm` losses too (the review's mutant) fails D4.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dex_catch_anytime.py
"""
from __future__ import annotations

import ast
import contextlib
import io
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules.battle_state import BattleOutcome  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG = "POKEBOT_R24_CATCHHURT"
FAULTS = ("POKEBOT_R24_FAULT_LIFTEARLY", "POKEBOT_R24_FAULT_KINDLATE", "POKEBOT_R24_FAULT_TEAMLOSS")
failures: list = []

#: Post-gym-1, a FULL party (the box path), everything clear except the health. Each case overrides a few fields.
BASE = dict(
    is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=False,
    party_slots_used=6, battler_count=6, party_target=4, resource_block=None,
    spare_balls=SM.DEX_CATCH_BALL_RESERVE + 21, hunt_armed=False, training=False, boxed_count=0,
    party_healthy=False, species_dex=353, owned_dex=frozenset({1}), party_dex=frozenset({2}),
    attempts=0, expected_throws=3.0,
)
ON = dict(lift_health=True)
CASES = [
    ("A1", dict(), False, "full strength"),
    ("A2", ON, True, "PC box"),
    ("A3", dict(ON, training=True), False, "training"),
    ("A4", dict(ON, spare_balls=SM.DEX_CATCH_BALL_RESERVE), False, "dex reserve"),
    ("A5", dict(ON, boxed_count=SM.PC_STORAGE_SLOTS), False, "PC storage is full"),
    ("A6", dict(ON, attempts=SM.DEX_CATCH_MAX_ATTEMPTS), False, "already attempted"),
    ("A7", dict(ON, expected_throws=SM.DEX_CATCH_MAX_EXPECTED_THROWS + 1), False, "expected throws"),
    ("A8", dict(ON, hunt_armed=True), False, "hunt is armed"),
    ("A9", dict(ON, resource_block="no spare Poké Balls (the last ball is reserved)"), False, "last ball is reserved"),
    ("A10", dict(ON, pre_badge1=True, party_slots_used=2, battler_count=2), True, "pre-gym-1"),
    ("A12", dict(ON, party_slots_used=4, battler_count=4), False, "runway"),
]
LATER_GATES = {"A3", "A4", "A5", "A6", "A7"}


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


@contextlib.contextmanager
def env(**kv):
    names = (FLAG,) + FAULTS
    saved = {k: os.environ.get(k) for k in names}
    try:
        for k in names:
            os.environ.pop(k, None)
        os.environ.update(kv)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run_cases(sink=None) -> set:
    red = set()
    for tag, over, want, why in CASES:
        got, reason = SM.decide_dex_catch(**dict(BASE, **over))
        ok = got is want and why.lower() in reason.lower()
        if not ok:
            red.add(tag)
        check(ok, f"{tag} catch={got} reason={reason!r} (want {want}, {why!r})", sink)
    return red


def fresh_mode(mod=SM):
    m = mod.StoryMode.__new__(mod.StoryMode)
    mod.StoryMode.reset_per_run_state(m)
    return m


def lost_battle(kind, mod=SM):
    """Counts after a stubbed LOST battle with a `kind` catch open (None = no catch). Output of the hook is silenced."""
    m = fresh_mode(mod)
    m._location_key = lambda: (0, 25)
    m._boss_battle = None
    if kind is not None:
        m._catch_ctx = {"kind": kind}
    with contextlib.redirect_stdout(io.StringIO()):
        mod.StoryMode.on_battle_ended(m, BattleOutcome.Lost)
    return m._defeat_counts.get((0, 25), 0), getattr(m, "_catch_defeat_counts", {}).get((0, 25), 0)


def accounting(sink=None, mod=SM) -> set:
    red = set()
    with env(**{FLAG: "1", **{k: os.environ[k] for k in FAULTS if os.environ.get(k)}}):
        on_dex = lost_battle("dex", mod)
        on_team = lost_battle("team", mod)
        on_none = lost_battle(None, mod)
        on_other = {k: lost_battle(k, mod) for k in ("hm", "counter", "shiny")}
    off_dex = lost_battle("dex")
    off_team = lost_battle("team")
    ok = on_dex == (0, 1) and off_dex == (1, 0)
    if not ok:
        red.add("D1")
    check(ok, f"D1 a lost DEX catch: ON (defeats, catch_losses)={on_dex} want (0, 1); OFF {off_dex} want (1, 0)", sink)
    ok = on_team == (1, 0) and off_team == (1, 0)
    if not ok:
        red.add("D2")
    check(ok, f"D2 a lost TEAM catch counts as a defeat in both arms: ON {on_team}, OFF {off_team} (want (1, 0))", sink)
    ok = on_none == (1, 0)
    if not ok:
        red.add("D3")
    check(ok, f"D3 an ordinary loss, ON: {on_none} (want (1, 0))", sink)
    # review 2026-09-29: C4 must file DEX losses only. Without these, a mutant filing `hm` losses apart passed the gate
    # (an HM hunt losing on one map would stop feeding survival mode).
    for tag, kind in (("D4", "hm"), ("D5", "counter"), ("D6", "shiny")):
        ok = on_other[kind] == (1, 0)
        if not ok:
            red.add(tag)
        check(ok, f"{tag} a lost {kind.upper()} catch still counts as a map defeat, ON: {on_other[kind]} (want (1, 0))", sink)
    return red


def mutant_module(src: str, edited: bool):
    """`story_mode` compiled from a MUTATED COPY of its source (the file is never touched)."""
    import types

    assert edited, "the mutant's anchor was not found in the source"
    mod = types.ModuleType("story_mode_mutant")
    mod.__file__ = str(SM_PATH)
    exec(compile(src, "story_mode_mutant", "exec"), mod.__dict__)
    return mod


def wiring(src: str, sink=None):
    ok = False
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "decide_dex_catch":
            ok = ok or any(kw.arg == "lift_health" and ast.unparse(kw.value) == "self._r24_catchhurt" for kw in node.keywords)
    check(ok, f"A11 the adapter passes lift_health=self._r24_catchhurt ({ok})", sink)


def main() -> int:
    print("A — the pure predicate")
    with env():
        run_cases()
    src = SM_PATH.read_text(encoding="utf-8")
    wiring(src)
    with env():
        off = fresh_mode()._r24_catchhurt
    with env(**{FLAG: "1"}):
        on = fresh_mode()._r24_catchhurt
    check(off is False and on is True, f"A13 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(all(f in reg for f in (FLAG,) + FAULTS), f"A14 {FLAG} and its three fault arms are registered in 29")
    print("D — catch-loss accounting (C4)")
    with env():
        accounting()

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    sink: list = []
    with env(POKEBOT_R24_FAULT_LIFTEARLY="1"):
        red = run_cases(sink)
    check(base_ok and red == LATER_GATES, f"F1 LIFTEARLY reddens EXACTLY the later gates: {sorted(red)}")
    for tag, fault, want in (("F2", "POKEBOT_R24_FAULT_KINDLATE", "D1"), ("F3", "POKEBOT_R24_FAULT_TEAMLOSS", "D2")):
        sink = []
        with env(**{fault: "1"}):
            red = accounting(sink)
        check(base_ok and want in red, f"{tag} {fault}=1 reddens {want}: red={sorted(red)}")
    sink = []
    old = '_c4_kinds = {"dex", "team"} if _os_c4.environ.get("POKEBOT_R24_FAULT_TEAMLOSS") == "1" else {"dex"}'
    with env():
        red = accounting(sink, mutant_module(src.replace(old, '_c4_kinds = {"dex", "hm"}', 1), old in src))
    check(base_ok and "D4" in red, f"F6 a C4 that also files HM losses fails D4: red={sorted(red)}")
    sink = []
    wiring(src.replace("lift_health=self._r24_catchhurt,", "lift_health=False,", 1), sink)
    check(base_ok and bool(sink), "F4 an adapter passing lift_health=False fails A11")
    sink = []
    wiring(src.replace("lift_health=self._r24_catchhurt,", "# lift_health=self._r24_catchhurt,", 1), sink)
    check(base_ok and bool(sink), "F5 the keyword kept only in a COMMENT still fails A11")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — POKEBOT_R24_CATCHHURT lifts only the health refusal, and a lost dex catch is not a map defeat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
