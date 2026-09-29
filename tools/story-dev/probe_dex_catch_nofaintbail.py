r"""GATE (stub-driven) — USER RULING 24 step 5: with `POKEBOT_R24_NOFAINTBAIL=1` a post-gym-1 DEX catch no longer bails
when a team member faints — on BOTH faint-bail paths — while the reserve bail and the trapped-and-empty fight stay
(2026-09-29).

WHY: the user ruled (`06`, 2026-09-28): *"If the bot whites out or the training pokemon faints, thats ok … catching has a
bit higher priority"*. `StoryDexCatchStrategy` bailed on a faint in TWO places: (a) `should_flee_after_faint` returned
True, and (b) it set `_fainted_this_battle`, so `decide_turn`'s `dex_catch_bail_reason` fled on the NEXT turn. Changing
(a) alone still flees a turn later (the design's C5 finding) — so N1 drives `decide_turn` AFTER the faint.
Measured discriminator (step 4's M0, seed 1): a Gulpin catch on Route 110 bailed "a team member fainted" at f359393.
  N1  ON + a faint: `should_flee_after_faint` → False, `_fainted_this_battle` stays False, and the NEXT `decide_turn`
      (spare above the reserve) is the parent's turn, with no bail reason.
  N2  ON + a faint logs exactly one `[DEXCATCH-NOBAIL]` line and no `[DEXCATCH-BAIL]` line (the ACTION, rule 7).
  N3  ON at the reserve (no faint): still RUN AWAY, reason recorded.
  N4  ON trapped: with no ball left it FIGHTS (strongest move); after a faint it takes the parent's answer (False).
  N5  OFF + a faint: bails on both paths (`True`, then RUN AWAY next turn) and logs NO `[DEXCATCH-NOBAIL]` line.
  N6  the constructor reads the RUNNING mode's `_r24_nofaintbail` (ON → True, OFF → False, no mode → False).
  A1  `reset_per_run_state` reads the flag.   A2 both flags are registered in 29.
  A3  one source: the env name `POKEBOT_R24_NOFAINTBAIL` is read exactly once in story_mode.py's CODE (comments and
      docstrings excluded) — in `reset_per_run_state`, never inside the strategy.
FAULT ARMS (built in; the unmutated subject must pass first; each must turn EXACTLY its own set red):
  F1  `POKEBOT_R24_FAULT_HALFBAIL=1` (production): only path (a) changes → {N1}.
  F2  a source mutant dropping EVERY bail when the flag is on (the design's BAILWIDE, as a mutant) → {N3, N4}.
  F3  a source mutant logging the NOBAIL line before the flag check (telemetry without its guard) → {N5}.
  F4  a source mutant ignoring the flag (the skip-the-fix arm) → {N1, N2}.
  F5  a source mutant that also reads the env inside the strategy → A3 red.
  F6  (NEGATIVE) a comment that quotes the env read must leave A3 GREEN (the gate must not fire on mentions).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dex_catch_nofaintbail.py
"""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys
import tokenize
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.battle_strategies.default as DEFAULT  # noqa: E402
import modules.items as ITEMS  # noqa: E402
import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules.battle_strategies import TurnAction  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG, FAULT = "POKEBOT_R24_NOFAINTBAIL", "POKEBOT_R24_FAULT_HALFBAIL"
failures: list = []
PARENT = ("PARENT", None)


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


@contextlib.contextmanager
def env(**kv):
    saved = {k: os.environ.get(k) for k in (FLAG, FAULT)}
    try:
        for k in (FLAG, FAULT):
            os.environ.pop(k, None)
        os.environ.update(kv)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class _Bag:
    def __init__(self, n):
        self.number_of_balls_except_master_ball = n


@contextlib.contextmanager
def stubs(mod, bag_n):
    """The parent's turn is a sentinel, the bag holds `bag_n` balls, logs are captured, `context` is a namespace."""
    logs: list = []
    saved = (mod.StoryCatchStrategy.decide_turn, ITEMS.get_item_bag, mod._log_story_event, mod.context)
    try:
        mod.StoryCatchStrategy.decide_turn = lambda self, bs: PARENT
        ITEMS.get_item_bag = lambda: _Bag(bag_n)
        mod._log_story_event = lambda text, cat="": logs.append(text)
        mod.context = types.SimpleNamespace(message="", bot_mode_instance=None)
        yield logs
    finally:
        (mod.StoryCatchStrategy.decide_turn, ITEMS.get_item_bag, mod._log_story_event, mod.context) = saved


def make(mod, no_faint_bail: bool):
    """An instance WITHOUT the base constructor (it reads the live party), as `probe_dexcatch_bail.py` builds it."""
    obj = mod.StoryDexCatchStrategy.__new__(mod.StoryDexCatchStrategy)
    obj._fainted_this_battle = False
    obj.bail_reason = None
    obj._no_faint_bail = no_faint_bail
    return obj


def cases(mod=SM, sink=None, fault=False) -> set:
    red: set = set()
    R = mod.DEX_CATCH_BALL_RESERVE
    kv = {FAULT: "1"} if fault else {}

    def rec(tag, ok, msg):
        if not ok:
            red.add(tag)
        check(ok, f"{tag} {msg}", sink)

    with env(**kv), contextlib.redirect_stdout(io.StringIO()):
        # N1 — ON + a faint: no flee now, no flee next turn.
        with stubs(mod, R + 5):
            s = make(mod, True)
            fled = s.should_flee_after_faint(None)
            nxt = s.decide_turn(None)
        n1 = (fled, s._fainted_this_battle, nxt == PARENT, s.bail_reason)
        # N2 — ON + a faint: one NOBAIL line, no BAIL line.
        with stubs(mod, R + 5) as logs:
            s = make(mod, True)
            s.should_flee_after_faint(None)
        n2 = [t for t in logs if "DEXCATCH-" in t]
        # N3 — ON at the reserve: still bails.
        with stubs(mod, R):
            s = make(mod, True)
            n3 = (s.decide_turn(None) == TurnAction.run_away(), s.bail_reason)
        # N4 — ON trapped.
        import modules.battle_strategies as BS

        class _Trapped:
            def __init__(self, state):
                pass

            def get_best_escape_method(self):
                return None

            def get_strongest_move_against(self, ours, theirs):
                return 2

        class _State:
            own_side = types.SimpleNamespace(active_battler=None)
            opponent = types.SimpleNamespace(active_battler=None)

        real_bsu, real_ball = BS.BattleStrategyUtil, mod.StoryDexCatchStrategy._get_best_poke_ball
        try:
            BS.BattleStrategyUtil = _Trapped
            mod.StoryDexCatchStrategy._get_best_poke_ball = lambda self, bs: None
            with stubs(mod, R):
                s = make(mod, True)
                n4_fight = s.decide_turn(_State()) == TurnAction.use_move(2)
            with stubs(mod, R + 5):
                s = make(mod, True)
                n4_faint = s.should_flee_after_faint(_State()) is False
        finally:
            BS.BattleStrategyUtil, mod.StoryDexCatchStrategy._get_best_poke_ball = real_bsu, real_ball
        # N5 — OFF + a faint: both paths bail; no NOBAIL line.
        with stubs(mod, R + 5) as logs:
            s = make(mod, False)
            off_fled = s.should_flee_after_faint(None)
            off_next = s.decide_turn(None)
        n5 = (off_fled, off_next == TurnAction.run_away(), [t for t in logs if "DEXCATCH-NOBAIL" in t],
              any("DEXCATCH-BAIL" in t for t in logs))

    rec("N1", n1 == (False, False, True, None),
        f"ON + a faint: flee={n1[0]}, _fainted_this_battle={n1[1]}, next turn is the parent's={n1[2]}, "
        f"bail_reason={n1[3]!r} (want False, False, True, None)")
    rec("N2", len(n2) == 1 and "DEXCATCH-NOBAIL" in n2[0], f"ON + a faint logs exactly one NOBAIL line and no BAIL line ({n2})")
    rec("N3", n3[0] and n3[1] is not None and "reserve" in n3[1], f"ON at the reserve still runs away ({n3})")
    rec("N4", n4_fight and n4_faint, f"ON trapped: no ball ⇒ fight ({n4_fight}); a faint ⇒ the parent's answer ({n4_faint})")
    rec("N5", n5[0] is True and n5[1] and not n5[2] and n5[3],
        f"OFF + a faint: flee={n5[0]}, next turn runs={n5[1]}, NOBAIL lines={n5[2]}, BAIL line={n5[3]}")
    return red


def ctor_reads_running_mode(sink=None):
    """N6: the real constructor, with the party read stubbed (as `probe_dex_catch_training.py` does)."""
    fake_party = types.SimpleNamespace(first_non_fainted=types.SimpleNamespace(index=0))
    saved = (DEFAULT.get_party, SM.context)
    got = []
    try:
        DEFAULT.get_party = lambda: fake_party
        for mode in (types.SimpleNamespace(_r24_nofaintbail=True, _r24_catchtrain=False),
                     types.SimpleNamespace(_r24_nofaintbail=False, _r24_catchtrain=False), None):
            SM.context = types.SimpleNamespace(message="", bot_mode_instance=mode)
            got.append(SM.StoryDexCatchStrategy()._no_faint_bail)
    finally:
        DEFAULT.get_party, SM.context = saved
    check(got == [True, False, False], f"N6 the constructor reads the running mode's flag (ON, OFF, no mode → {got})", sink)


def code_only(src: str) -> str:
    """The source with comments and string tokens that are docstrings/comments removed, keeping string LITERALS used
    as arguments: we drop COMMENT tokens and any STRING token that stands alone as an expression statement."""
    out = []
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    for i, tok in enumerate(toks):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING:
            prev = next((t for t in reversed(toks[:i]) if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                                                                            tokenize.DEDENT, tokenize.COMMENT)), None)
            if prev is None or prev.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT) or \
                    (prev.type == tokenize.OP and prev.string == ":"):
                continue  # a docstring / bare string statement
        out.append(tok.string)
    return " ".join(out)


def one_source(src: str, sink=None):
    code = code_only(src)
    n = code.count(f'"{FLAG}"') + code.count(f"'{FLAG}'")
    check(n == 1, f"A3 the env name {FLAG} is read exactly once in code ({n})", sink)


def mutant_module(src: str):
    mod = types.ModuleType("story_mode_mutant")
    mod.__file__ = str(SM_PATH)
    exec(compile(src, "story_mode_mutant", "exec"), mod.__dict__)
    return mod


def main() -> int:
    print("N — the dex strategy's faint handling (stubbed)")
    cases()
    ctor_reads_running_mode()
    with env():
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        off = m._r24_nofaintbail
    with env(**{FLAG: "1"}):
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        on = m._r24_nofaintbail
    check(off is False and on is True, f"A1 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(FLAG in reg and FAULT in reg, f"A2 {FLAG} and {FAULT} are registered in 29")
    src = SM_PATH.read_text(encoding="utf-8")
    one_source(src)

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    nl = "\r\n" if "\r\n" in src else "\n"
    red = cases(SM, [], fault=True)
    check(base_ok and red == {"N1"}, f"F1 {FAULT}=1 turns exactly {{N1}} red (red: {sorted(red)})")

    def mutate(old, new):
        old, new = old.replace("\n", nl), new.replace("\n", nl)
        return src.replace(old, new, 1) if src.count(old) == 1 else None

    dt_anchor = ("    def decide_turn(self, battle_state):\n"
                 "        import os as _os_bail\n")
    m2 = mutate(dt_anchor, dt_anchor + "        if getattr(self, \"_no_faint_bail\", False):\n"
                                       "            return super().decide_turn(battle_state)\n")
    red = cases(mutant_module(m2), []) if m2 else {"(anchor missing)"}
    check(base_ok and red == {"N3", "N4"}, f"F2 a mutant dropping every bail under the flag turns exactly {{N3, N4}} red "
                                           f"(red: {sorted(red)})")
    guard = "        if getattr(self, \"_no_faint_bail\", False):\n"
    inner = "            _r24_nofaintbail_log()\n".replace("\n", nl)
    m3 = mutate(guard, "        _r24_nofaintbail_log()\n" + guard)  # MOVE the call out of the guard (not a copy)
    m3 = m3.replace(inner, "", 1) if m3 and m3.count(inner) == 1 else None
    red = cases(mutant_module(m3), []) if m3 else {"(anchor missing)"}
    check(base_ok and red == {"N5"}, f"F3 a NOBAIL log before the flag check turns exactly {{N5}} red (red: {sorted(red)})")
    m4 = mutate(guard, "        if False:\n")
    red = cases(mutant_module(m4), []) if m4 else {"(anchor missing)"}
    check(base_ok and red == {"N1", "N2"}, f"F4 a strategy ignoring the flag turns exactly {{N1, N2}} red "
                                           f"(red: {sorted(red)})")
    m5 = mutate(guard, "        if getattr(self, \"_no_faint_bail\", False) or _os_bail.environ.get(\"" + FLAG +
                "\") == \"1\":\n")
    sink: list = []
    if m5:
        one_source(m5, sink)
    check(base_ok and m5 is not None and bool(sink), f"F5 a second env read inside the strategy turns A3 red "
                                                     f"(anchored={m5 is not None})")
    m6 = mutate(guard, "        # a mention only: _os_bail.environ.get(\"" + FLAG + "\")\n" + guard)
    sink = []
    if m6:
        one_source(m6, sink)
    check(base_ok and m6 is not None and not sink, f"F6 (negative) a COMMENT quoting the env read leaves A3 green "
                                                   f"(anchored={m6 is not None}, red={bool(sink)})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — POKEBOT_R24_NOFAINTBAIL removes BOTH faint bails from a dex catch; the reserve bail and the trapped fight "
          "stay; OFF is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
