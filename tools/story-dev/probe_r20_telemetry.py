r"""GATE (pure) — USER RULING 20 Phase 2 step T: the per-catch telemetry is LOG-ONLY. It classifies honestly, and it
can never cost a catch, a defeat count or a whiteout abort (2026-09-28).

WHY: the four catch branches in `StoryMode.on_battle_started` each end in `except Exception: pass`, so a raise in a
log line before `return <catch strategy>` would silently CANCEL THE CATCH; `on_battle_ended` has no outer guard, so a
raise there skips defeat counting; `catch_starter_team` is a generator whose `finally` runs while a whiteout's
`StoryAbort` is in flight, so a raise there REPLACES the abort. Every emit is therefore its own `try`. This gate
proves the properties, not the text:

  T1  `_r20_catch_end` classifies `end=` (caught / lost / bail / out_of_balls / fled / foe_fled) and DERIVES `dest`
      (party / box / box-by-count / ?) from the new PID, closes the context, and is silent under
      `POKEBOT_R20_FAULT_NOCATCHEND=1` and with no open context.
  T2  `StoryMode.on_battle_ended(stub, Lost)` still counts the defeat when the logger RAISES.
  T3  `_r20_catch_start` / `_r20_mark` never raise on a stand-in `self` or an unset bot mode.
  T4  `catch_starter_team` reports WHY it stopped (target / no_balls / abort), and a `StoryAbort` from
      `_check_abort` still propagates out of it unchanged.
  T5  the run header carries `env-all:` with every `POKEBOT_*` variable.
  W   every catch-strategy `return` in `on_battle_started` is IMMEDIATELY preceded by an `_r20_catch_start(...)` call
      (a deleted start site would silently lose a whole kind); and the fault arm is registered in 29.
FAULT ARMS (built in; each must FAIL for its own reason):
  F1  an UNGUARDED `_r20_catch_end` (raises)  -> T2 goes red;
  F2  a `_catchteam_exit` that raises          -> T4's abort check goes red;
  F3  a source mutant with one start call removed -> W goes red; a comment mentioning `_r20_catch_start` must not
      satisfy W (AST reading).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_telemetry.py
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
import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules import debug_logger as DL  # noqa: E402
from modules.battle_state import BattleOutcome  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_R20_FAULT_NOCATCHEND"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


class Patch:
    """Set module attributes for the duration of a `with`, restoring them after."""

    def __init__(self, mod, **attrs):
        self.mod, self.attrs, self.saved = mod, attrs, {}

    def __enter__(self):
        for k, v in self.attrs.items():
            self.saved[k] = getattr(self.mod, k)
            setattr(self.mod, k, v)

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(self.mod, k, v)
        return False


def _ctx(**over):
    c = {"kind": "dex", "sp": "Oddish#43", "party": 6, "ppids": {1, 2, 3, 4, 5, 6}, "box": 0,
         "bpids": frozenset(), "spare": 17, "badges": 6, "frame": 100}
    c.update(over)
    return c


def _now(**over):
    n = {"party": 6, "ppids": {1, 2, 3, 4, 5, 6}, "box": 0, "bpids": frozenset(), "spare": 17, "badges": 6,
         "frame": 300}
    n.update(over)
    return n


def run_end(ctx, now, outcome, env=None):
    lines = []
    mode = types.SimpleNamespace(_catch_ctx=ctx)
    saved = os.environ.get(ARM)
    if env is not None:
        os.environ[ARM] = env
    try:
        with Patch(SM, _r20_levels=lambda: now, _log_story_event=lambda m, c="STORY": lines.append((c, m))):
            SM._r20_catch_end(mode, outcome)
    finally:
        if env is not None:
            if saved is None:
                os.environ.pop(ARM, None)
            else:
                os.environ[ARM] = saved
    return mode, [m for c, m in lines if c == "CATCH"]


def t1():
    print("T1 — end= / dest= classification")
    table = [
        ("caught into the box, PID new", _ctx(), _now(box=1, bpids=frozenset({0xABC}), spare=16), BattleOutcome.Caught,
         ["end=caught", "res=Caught", "thrown=1", "dest=box", "pid=00000ABC", "box=1", "bail=-"]),
        ("caught into the party, PID new", _ctx(party=5, ppids={1, 2, 3, 4, 5}), _now(party=6, spare=15),
         BattleOutcome.Caught, ["end=caught", "dest=party", "pid=00000006", "thrown=2"]),
        ("caught, box grew but PIDs unreadable", _ctx(), _now(box=1), BattleOutcome.Caught,
         ["end=caught", "dest=box", "pid=-"]),
        ("caught, nothing new anywhere", _ctx(), _now(), BattleOutcome.Caught, ["end=caught", "dest=?"]),
        ("out-of-balls flee", _ctx(end="out_of_balls"), _now(spare=0), BattleOutcome.RanAway,
         ["end=out_of_balls", "res=RanAway", "dest=none"]),
        ("dex bail at the reserve", _ctx(bail="reserve"), _now(spare=10), BattleOutcome.RanAway,
         ["end=bail", "bail=reserve"]),
        ("plain flee", _ctx(), _now(), BattleOutcome.RanAway, ["end=fled"]),
        ("foe fled", _ctx(), _now(), BattleOutcome.OpponentFled, ["end=foe_fled"]),
        ("lost", _ctx(), _now(), BattleOutcome.Lost, ["end=lost", "res=Lost"]),
    ]
    for name, c, n, oc, want in table:
        mode, out = run_end(c, n, oc)
        ok = len(out) == 1 and out[0].startswith("end ") and all(w in out[0].split() for w in want) \
            and mode._catch_ctx is None
        check(ok, f"T1 {name}: {want} (got {out})")
    mode, out = run_end(_ctx(), _now(box=1, bpids=frozenset({7})), BattleOutcome.Caught, env="1")
    check(out == [] and mode._catch_ctx is None, f"T1 {ARM}=1 suppresses the end line (got {out})")
    mode, out = run_end(None, _now(), BattleOutcome.Won)
    check(out == [], f"T1 no open context -> no end line (got {out})")
    _, out = run_end(_ctx(), _now(), BattleOutcome.Won)
    check(len(out) == 1 and "end=other" in out[0].split(), f"T1 an unexpected outcome -> end=other (got {out})")


def _lost_stub():
    return types.SimpleNamespace(_location_key=lambda: (0, 8), _defeat_counts={}, _last_defeat_key=None, _loss_seq=0,
                                 _loss_ko_history={}, _catch_ctx=_ctx(), _boss_battle=None)


def _boom(*_a, **_k):
    raise RuntimeError("telemetry exploded")


def t2(sink=None, end_fn=None):
    stub = _lost_stub()
    raised = None
    attrs = {"_log_story_event": _boom}
    if end_fn is not None:
        attrs["_r20_catch_end"] = end_fn
    with Patch(SM, **attrs):
        try:
            SM.StoryMode.on_battle_ended(stub, BattleOutcome.Lost)
        except Exception as error:  # noqa: BLE001 - the gate reports it
            raised = error
    check(raised is None and stub._defeat_counts.get((0, 8)) == 1,
          f"T2 a raising logger still counts the defeat (raised={raised!r}, counts={stub._defeat_counts})", sink)


def t3():
    print("T3 — never raise on stand-ins")
    for name, fn in (("start on object()", lambda: SM._r20_catch_start(object(), "dex", None, dex=5)),
                     ("start on a bare namespace", lambda: SM._r20_catch_start(types.SimpleNamespace(), "hm", None)),
                     ("mark with no bot mode", lambda: SM._r20_mark("end", "out_of_balls")),
                     ("bail mark with a None reason", lambda: SM._r20_mark_bail(None)),
                     ("levels with no emulator", SM._r20_levels)):
        try:
            fn()
            ok = True
        except Exception:  # noqa: BLE001 - the gate reports it
            ok = False
        check(ok, f"T3 {name} does not raise")
    # A mark must land in the context the START opened (it is written through `context.bot_mode_instance`).
    from modules.context import context as _ctx_t3

    saved = _ctx_t3.bot_mode_instance
    mode = types.SimpleNamespace(_catch_ctx=_ctx())
    _ctx_t3.bot_mode_instance = mode
    try:
        SM._r20_mark_bail("a team member fainted")
        SM._r20_mark_bail("only 9 spare balls left")  # only the FIRST mark sticks
    finally:
        _ctx_t3.bot_mode_instance = saved
    check(mode._catch_ctx.get("bail") == "faint",
          f"T3 a bail mark lands in the open catch context, first one wins (got {mode._catch_ctx.get('bail')!r})")


def _team_run(party, balls, abort=False, exit_fn=None):
    events = []
    fake_ctx = types.SimpleNamespace(config=types.SimpleNamespace(battle=types.SimpleNamespace(hp_threshold=20)),
                                     emulator=types.SimpleNamespace(get_frame_count=lambda: 1000), message="")

    def check_abort():
        if abort:
            raise EG.StoryAbort("probe: whiteout unwind")

    def no_restock(mart=None):
        return iter(())

    attrs = dict(context=fake_ctx, _party_size=lambda: party, _total_poke_balls=lambda: balls,
                 _check_abort=check_abort, provision_poke_balls=no_restock)
    if exit_fn is not None:
        attrs["_catchteam_exit"] = exit_fn
    raised = None
    with Patch(EG, **attrs), Patch(DL, event=lambda m, category=None, **_k: events.append((category, m))):
        try:
            for _ in EG.catch_starter_team(target_size=4):
                pass
        except BaseException as error:  # noqa: BLE001 - the gate reports what escaped
            raised = error
    return raised, [m for c, m in events if c == "CATCHTEAM"]


def t4(sink=None, exit_fn=None):
    raised, ev = _team_run(party=1, balls=10, abort=True, exit_fn=exit_fn)
    check(isinstance(raised, EG.StoryAbort) and (exit_fn is not None or any("reason=abort" in e for e in ev)),
          f"T4 a StoryAbort propagates out of catch_starter_team unchanged, reason=abort logged "
          f"(raised={type(raised).__name__}, events={ev})", sink)


def t4_reasons():
    print("T4 — why the team loop stopped")
    raised, ev = _team_run(party=4, balls=10)
    check(raised is None and len(ev) == 1 and "reason=target" in ev[0] and "loops=0" in ev[0],
          f"T4 party already at target -> reason=target loops=0 (raised={raised!r}, events={ev})")
    raised, ev = _team_run(party=1, balls=1)
    check(raised is None and len(ev) == 1 and "reason=no_balls" in ev[0],
          f"T4 out of balls, restock failed -> reason=no_balls (raised={raised!r}, events={ev})")
    t4()


def t5():
    print("T5 — env-all")
    out = []
    saved_arm = os.environ.get(ARM)
    os.environ[ARM] = "1"  # the registered fault-arm name doubles as the marker (lint R6: no unregistered flags)
    real = DL._raw
    DL._raw = lambda s: out.append(s)
    try:
        DL._write_run_header()
    finally:
        DL._raw = real
        if saved_arm is None:
            os.environ.pop(ARM, None)
        else:
            os.environ[ARM] = saved_arm
    env_all = [ln for ln in out if "env-all:" in ln]
    check(len(env_all) == 1 and ARM in env_all[0],
          f"T5 the header's env-all: line names every POKEBOT_* variable (got {env_all})")
    check(any(ln.lstrip().startswith("env:") for ln in out), "T5 the curated env: line is still there")


def _is_catch_return(node) -> bool:
    if not isinstance(node, ast.Return) or node.value is None:
        return False
    names = {n.func.id for n in ast.walk(node.value) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return bool(names & {"StoryCatchStrategy", "StoryShinyCatchStrategy", "StoryDexCatchStrategy"})


def _is_start_call(node) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
        and isinstance(node.value.func, ast.Name) and node.value.func.id == "_r20_catch_start"


def wiring(src: str, sink=None):
    tree = ast.parse(src)
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StoryMode")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "on_battle_started")
    returns, covered = 0, 0
    for node in ast.walk(fn):
        for field in ("body", "orelse", "finalbody"):
            body = getattr(node, field, None)
            if not isinstance(body, list):
                continue
            for i, stmt in enumerate(body):
                if _is_catch_return(stmt):
                    returns += 1
                    covered += i > 0 and _is_start_call(body[i - 1])
    check(returns >= 4 and covered == returns,
          f"W every catch-strategy return in on_battle_started is preceded by _r20_catch_start ({covered}/{returns})",
          sink)


def main() -> int:
    t1()
    print("T2 — defeat counting survives a raising logger")
    t2()
    t3()
    t4_reasons()
    t5()
    print("W — wiring")
    src = SM_PATH.read_text(encoding="utf-8")
    wiring(src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(ARM in reg, f"W {ARM} is registered in 29-DISABLED-FEATURES-REGISTRY.md")

    print("F — fault arms (each must FAIL for its own reason; the unmutated subject passed above)")
    base_ok = not failures
    sink: list = []
    t2(sink=sink, end_fn=_boom)
    check(base_ok and bool(sink), "F1 an UNGUARDED _r20_catch_end turns T2 red")
    sink = []
    t4(sink=sink, exit_fn=_boom)
    check(base_ok and bool(sink), "F2 a raising _catchteam_exit turns the abort check red (it replaces the StoryAbort)")
    lines = src.splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.strip().startswith('_r20_catch_start(self, "hm"'))
    mutant = lines[:idx] + [lines[idx].replace('_r20_catch_start(self, "hm", encounter)',
                                               '# _r20_catch_start(self, "hm", encounter)  (removed)')] + lines[idx + 1:]
    sink = []
    wiring("\n".join(mutant), sink)
    check(base_ok and bool(sink), "F3 removing one start call (leaving only a COMMENT that mentions it) turns W red")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — the catch telemetry is log-only: it classifies honestly and cannot cost a catch, a defeat or an abort")
    return 0


if __name__ == "__main__":
    sys.exit(main())
