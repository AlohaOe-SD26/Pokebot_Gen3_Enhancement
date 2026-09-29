r"""GATE — a DISCRETIONARY Pokédex catch must stop at the ball reserve and on a faint (`#24-dexcatch-battlebail`,
USER RULING 20 Phase 0, 2026-09-26).

WHY: the fence (`decide_dex_catch`) guards only ENTRY. A catch battle never fights back and throws until caught or empty —
MEASURED: one Absol took 23 balls in 26,615 frames and the run later died "Cannot hunt a Dive learner: no Poké Balls and
no money". Before RULING 20 opens the fence, the catch itself must stop spending the mandatory hunts' balls.

  D1  `dex_catch_bail_reason` (PURE): a faint ⇒ bail; spare balls AT the reserve ⇒ bail (the boundary is exact); one
      above the reserve and no faint ⇒ keep throwing;
  D2  WIRING: only the fence's post-gym-1 call site returns `StoryDexCatchStrategy`; pre-gym-1 keeps
      `StoryCatchStrategy`; the MANDATORY catches (the HM learner, the boss counter) still return `StoryCatchStrategy`;
      `StoryShinyCatchStrategy` still inherits `StoryCatchStrategy` (the user's shiny rule is untouched);
  D3  BEHAVIOUR (stubbed bag and parent): at the reserve `decide_turn` RUNS AWAY and records the reason; above it the
      parent's turn is taken; after a faint it flees; an UNREADABLE bag keeps the old behaviour (throw) — never a silent
      bail; `should_flee_after_faint` is True;
  D4  the skip-the-fix arm `POKEBOT_DEXCATCH_FAULT_NOBAIL` restores the old behaviour, is read in production and is
      registered in `29`.
FAULT ARMS (built in): a rule that ignores the reserve (D1); the fence site wired to the plain strategy (D2); a
`decide_turn` that bails on an unreadable bag (D3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dexcatch_bail.py
"""
from __future__ import annotations

import ast
import io
import os
import pathlib
import sys
import tokenize
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules.battle_strategies import TurnAction  # noqa: E402

STORY = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
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


def d1(rule, sink=None):
    R = SM.DEX_CATCH_BALL_RESERVE
    check(rule(30, R, True) is not None, "D1 a faint this battle ⇒ bail", sink)
    check(rule(R, R, False) is not None, f"D1 spare balls AT the reserve ({R}) ⇒ bail (the boundary is exact)", sink)
    check(rule(R + 1, R, False) is None, f"D1 one above the reserve ({R + 1}) and no faint ⇒ keep throwing", sink)
    check(rule(0, R, False) is not None, "D1 no balls at all ⇒ bail", sink)


def _method_src(src: str, cls: str, name: str) -> str:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    return _strip_comments(ast.get_source_segment(src, item) or "")
    return ""


def d2(src: str, sink=None):
    code = _strip_comments(src)
    check("return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()" in code,
          "D2 the fence's call site: post-gym-1 ⇒ the dex-only class, pre-gym-1 ⇒ the plain one", sink)
    obs = _method_src(src, "StoryMode", "on_battle_started")
    # The fence's commit moved into `StoryMode._dex_catch_commit` (USER RULING 24 step 4, 2026-09-29), which
    # `on_battle_started` calls (`probe_dex_catch_oversurvival.py` A2); the count spans the two, so a second dex-only
    # site in EITHER still turns this red.
    commit = _method_src(src, "StoryMode", "_dex_catch_commit")
    check(commit.count("StoryDexCatchStrategy()") + obs.count("StoryDexCatchStrategy()") == 1,
          "D2 exactly one site returns the dex-only class (on_battle_started + _dex_catch_commit)", sink)
    check(obs.count("return StoryCatchStrategy()") >= 2,
          "D2 the MANDATORY catches (HM learner, boss counter) still return the plain strategy", sink)
    tree = ast.parse(src)
    shiny = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StoryShinyCatchStrategy")
    check([b.id for b in shiny.bases if isinstance(b, ast.Name)] == ["StoryCatchStrategy"],
          "D2 the shiny strategy still inherits the PLAIN strategy (the user's shiny rule is untouched)", sink)


class _Bag:
    def __init__(self, n):
        self.number_of_balls_except_master_ball = n


def _make(cls):
    """An instance WITHOUT the base constructor (it reads the live party); only the two fields the subclass adds."""
    obj = cls.__new__(cls)
    obj._fainted_this_battle = False
    obj.bail_reason = None
    return obj


def d3(cls, sink=None):
    import modules.items as items

    real_bag = items.get_item_bag
    parent_turn = SM.StoryCatchStrategy.decide_turn
    sentinel = ("PARENT", None)
    try:
        SM.StoryCatchStrategy.decide_turn = lambda self, bs: sentinel
        items.get_item_bag = lambda: _Bag(SM.DEX_CATCH_BALL_RESERVE)
        s = _make(cls)
        check(s.decide_turn(None) == TurnAction.run_away() and s.bail_reason is not None,
              "D3 at the reserve: RUN AWAY, and the reason is recorded", sink)
        items.get_item_bag = lambda: _Bag(SM.DEX_CATCH_BALL_RESERVE + 5)
        s = _make(cls)
        check(s.decide_turn(None) == sentinel and s.bail_reason is None, "D3 above the reserve: the parent's turn", sink)
        check(s.should_flee_after_faint(None) is True, "D3 `should_flee_after_faint` is True", sink)
        check(s.decide_turn(None) == TurnAction.run_away(), "D3 after a faint: RUN AWAY on the next turn", sink)

        def broken():
            raise RuntimeError("bag unreadable")

        items.get_item_bag = broken
        s = _make(cls)
        check(s.decide_turn(None) == sentinel and s.bail_reason is None,
              "D3 an UNREADABLE bag keeps the old behaviour (throw) — never a silent bail", sink)

        # TRAPPED (Shadow Tag / Arena Trap / Mean Look / Wrap): escape is impossible ⇒ never choose Run forever.
        import modules.battle_strategies as BS

        real_bsu = BS.BattleStrategyUtil

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

        real_ball = SM.StoryDexCatchStrategy._get_best_poke_ball
        try:
            BS.BattleStrategyUtil = _Trapped
            items.get_item_bag = lambda: _Bag(SM.DEX_CATCH_BALL_RESERVE)
            SM.StoryDexCatchStrategy._get_best_poke_ball = lambda self, bs: "a ball"
            s = _make(cls)
            check(s.decide_turn(_State()) == sentinel and s.bail_reason is None,
                  "D3 TRAPPED at the reserve with a ball left: keep throwing (the parent's turn), never Run forever", sink)
            check(s.should_flee_after_faint(_State()) is False,
                  "D3 TRAPPED after a faint: the parent's answer (send the next mon), not a flee that cannot happen", sink)
            SM.StoryDexCatchStrategy._get_best_poke_ball = lambda self, bs: None
            s = _make(cls)
            check(s.decide_turn(_State()) == TurnAction.use_move(2) and s.bail_reason is not None,
                  "D3 TRAPPED with NO ball left: FIGHT with the strongest move (the parent would pick an impossible Run)",
                  sink)
        finally:
            BS.BattleStrategyUtil = real_bsu
            SM.StoryDexCatchStrategy._get_best_poke_ball = real_ball
    finally:
        items.get_item_bag = real_bag
        SM.StoryCatchStrategy.decide_turn = parent_turn


def d4(src: str):
    code = _strip_comments(src)
    arm = "POKEBOT_DEXCATCH_FAULT_NOBAIL"
    check(f'.environ.get("{arm}") != "1"' in code and f'.environ.get("{arm}") == "1"' in code
          and f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"),
          f"D4 {arm} is read in production (both hooks) and registered in 29")
    import modules.items as items

    real_bag = items.get_item_bag
    parent_turn = SM.StoryCatchStrategy.decide_turn
    try:
        os.environ[arm] = "1"
        SM.StoryCatchStrategy.decide_turn = lambda self, bs: ("PARENT", None)
        items.get_item_bag = lambda: _Bag(0)
        check(_make(SM.StoryDexCatchStrategy).decide_turn(None) == ("PARENT", None),
              "D4 with the arm set, the old behaviour returns (no bail at the reserve)")
    finally:
        os.environ.pop(arm, None)
        items.get_item_bag = real_bag
        SM.StoryCatchStrategy.decide_turn = parent_turn


def main() -> int:
    print("=" * 92)
    print("GATE — the discretionary Pokédex catch bails at the ball reserve and on a faint")
    print("=" * 92)
    src = STORY.read_text(encoding="utf-8")
    print("\n== D1 the pure rule ==")
    d1(SM.dex_catch_bail_reason)
    print("\n== D2 wiring ==")
    d2(src)
    print("\n== D3 behaviour (stubbed) ==")
    d3(SM.StoryDexCatchStrategy)
    print("\n== D4 the skip-the-fix arm ==")
    d4(src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    d1(lambda spare, reserve, fainted: "fainted" if fainted else None, sink)
    check(bool(sink), f"FAULT a rule that ignores the reserve FAILS D1 ({len(sink)} caught)")
    sink = []
    d2(src.replace("return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()",
                   "return StoryCatchStrategy()", 1), sink)
    check(bool(sink), f"FAULT the fence site wired to the plain strategy FAILS D2 ({len(sink)} caught)")
    sink = []
    d2(src.replace("return StoryCatchStrategy()", "return StoryDexCatchStrategy()", 1), sink)
    check(bool(sink), f"FAULT a mandatory site (on_battle_started) given the dex-only class FAILS D2 ({len(sink)} caught)")
    sink = []

    class _BailsOnError(SM.StoryDexCatchStrategy):
        def decide_turn(self, battle_state):
            try:
                import modules.items as items

                items.get_item_bag()
            except Exception:
                self.bail_reason = "unreadable"
                return TurnAction.run_away()
            return super().decide_turn(battle_state)

    d3(_BailsOnError, sink)
    check(bool(sink), f"FAULT a strategy that bails on an unreadable bag FAILS D3 ({len(sink)} caught)")

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
