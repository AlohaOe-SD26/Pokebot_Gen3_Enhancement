r"""GATE — §Ch24 GAP 3, TEACH FLY IN PRODUCTION: the learner rule, `_play`'s order, and the driver's mirror of it.

WHY THIS EXISTS (`#26-ch24organic`, 2026-09-26)
-----------------------------------------------
Production never taught Fly, so §Ch24's per-trainee Fly ladder could offer only walkable ground and the return
bridge could not fly home. `ensure_fly_learner` now teaches HM02 in `_play` — after the §Ch24 latch, before
`train_for_league`. What must not regress:

  F1  `StoryMode._play`: `self.mark_ch24_owns_run()` < `ensure_fly_learner(...)` < the next `train_for_league(...)`.
  F2  `--driver ch24handoff` runs the SAME order (latch < teach < train < `prepare_and_open_the_league`), so the
      drive that proves the chain cannot silently drift from production.
  F3  `_fly_learner_slot` (PURE) picks the highest-level COMPATIBLE mon that still holds a non-HM slot — never a
      saturated four-HM mon (`hm_learner_slot`'s level-only rule picks exactly that), never an egg, None if nobody.
  F4  `POKEBOT_CH24_FAULT_NOFLYTEACH` is read in `ensure_fly_learner` (comments stripped) and registered.

FAULT ARMS (run every time): a level-only picker FAILS F3; a `_play` that teaches AFTER training FAILS F1.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_flyteach.py
"""
from __future__ import annotations

import ast
import io
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

from modules.story import pokemon_league as PL  # noqa: E402

STORY_SRC = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"
HARNESS_SRC = Path(__file__).resolve().parent / "story_harness.py"
LEAGUE_SRC = SANDBOX / "modules" / "story" / "pokemon_league.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


# ---- synthetic party ------------------------------------------------------------------------------
HM02 = object()


def _learned(name: str, hm: bool):
    return types.SimpleNamespace(move=types.SimpleNamespace(
        name=name, tm_hm=types.SimpleNamespace(name="HM05" if hm else "TM40") if hm else None))


def mon(level: int, compat: bool, moves, egg: bool = False):
    return types.SimpleNamespace(level=level, is_egg=egg, moves=moves,
                                 species=types.SimpleNamespace(can_learn_tm_hm=lambda item, c=compat: c))


FOUR_HM = [_learned("Surf", True), _learned("Strength", True), _learned("Rock Smash", True), _learned("Dive", True)]
FREE = [_learned("Peck", False), _learned("Aerial Ace", False), None, None]
FULL_BATTLER = [_learned("Peck", False), _learned("Wing Attack", False), _learned("Aerial Ace", False),
                _learned("Quick Attack", False)]


def f3(pick, sink=None):
    check(pick([mon(50, True, FOUR_HM), mon(40, True, FREE)], HM02) == 1,
          "F3 a L50 four-HM mon is SKIPPED for a L40 with a slot to spend", sink)
    check(pick([mon(50, True, FULL_BATTLER), mon(40, True, FREE)], HM02) == 0,
          "F3 highest level wins among spendable learners (four battle moves ARE spendable)", sink)
    check(pick([mon(60, False, FREE), mon(30, True, FOUR_HM)], HM02) is None,
          "F3 incompatible + saturated ⇒ None (report, never a doomed teach)", sink)
    check(pick([None, mon(70, True, FREE, egg=True)], HM02) is None, "F3 an empty slot and an egg ⇒ None", sink)


def _calls(fn, attr):
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if (f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)) == attr:
                out.append(n.lineno)
    return sorted(out)


def _method(tree, cls, meth):
    c = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return next(n for n in c.body if isinstance(n, ast.FunctionDef) and n.name == meth)


def f1(src, sink=None):
    fn = _method(ast.parse(src), "StoryMode", "_play")
    teach = _calls(fn, "ensure_fly_learner")
    check(len(teach) == 1, f"F1 exactly one ensure_fly_learner call in StoryMode._play (found {len(teach)})", sink)
    if len(teach) != 1:
        return
    latch = [ln for ln in _calls(fn, "mark_ch24_owns_run") if ln < teach[0]]
    train = [ln for ln in _calls(fn, "train_for_league") if ln > teach[0]]
    check(bool(latch), f"F1 the §Ch24 latch precedes the teach (line {teach[0]})", sink)
    check(bool(train), f"F1 train_for_league follows the teach (lines after {teach[0]}: {train[:1]})", sink)
    before_train = [ln for ln in _calls(fn, "train_for_league") if ln < teach[0]]
    # the teach must precede EVERY §Ch24 train call in _play (there is exactly one today)
    check(not before_train, f"F1 no train_for_league runs BEFORE the teach ({before_train})", sink)


def f2(src, sink=None):
    fn = _method(ast.parse(src), "Ch24HandoffMode", "run")
    lines = {k: _calls(fn, k) for k in ("mark_ch24_owns_run", "ensure_fly_learner", "train_for_league",
                                         "prepare_and_open_the_league")}
    firsts = [v[0] if v else None for v in lines.values()]
    check(None not in firsts and firsts == sorted(firsts),
          f"F2 the driver mirrors _play: latch < teach < train < prepare ({firsts})", sink)


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def main() -> int:
    print("=" * 92)
    print("GATE — §Ch24 teach Fly in production (`#26-ch24organic` gap 3)")
    print("=" * 92)
    story = STORY_SRC.read_text(encoding="utf-8")
    harness = HARNESS_SRC.read_text(encoding="utf-8")
    league = LEAGUE_SRC.read_text(encoding="utf-8")

    print("\n== F1 _play's order ==")
    f1(story)
    print("\n== F2 the hand-off driver mirrors it ==")
    f2(harness)
    print("\n== F3 the learner rule (pure) ==")
    f3(PL._fly_learner_slot)
    print("\n== F4 the arm ==")
    fn = next(n for n in ast.parse(league).body if isinstance(n, ast.FunctionDef) and n.name == "ensure_fly_learner")
    seg = _strip_comments(ast.get_source_segment(league, fn) or "")
    check('"POKEBOT_CH24_FAULT_NOFLYTEACH") == "1"' in seg, "F4 NOFLYTEACH is READ in ensure_fly_learner")
    check("`POKEBOT_CH24_FAULT_NOFLYTEACH`" in REGISTRY.read_text(encoding="utf-8"), "F4 NOFLYTEACH is registered")
    check("_fly_learner_slot(" in seg, "F4 ensure_fly_learner uses the gated picker, not a private copy")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []

    def level_only(party, item):
        best, lv = None, -1
        for i, m in enumerate(party):
            if m is not None and not m.is_egg and m.species.can_learn_tm_hm(item) and m.level > lv:
                best, lv = i, m.level
        return best
    f3(level_only, sink)
    check(bool(sink), f"FAULT a level-only picker (hm_learner_slot's rule) FAILS F3 ({len(sink)} caught)")

    anchor_teach = "            yield from ensure_fly_learner(_ch24_fly_report)\n"
    anchor_train = "            yield from train_for_league(_ch24_train_report)\n"
    assert story.count(anchor_teach) == 1 and story.count(anchor_train) == 1, "mutation anchors moved — update the gate"
    swapped = story.replace(anchor_teach, "").replace(anchor_train, anchor_train + anchor_teach)
    sink = []
    f1(swapped, sink)
    check(bool(sink), f"FAULT a _play that teaches AFTER training FAILS F1 ({len(sink)} caught)")

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
