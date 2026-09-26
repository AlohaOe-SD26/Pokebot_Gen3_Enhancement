r"""GATE — §Ch24 GAP 3, TEACH FLY IN PRODUCTION: the learner rule, `_play`'s order, and the driver's mirror of it.

WHY THIS EXISTS (`#26-ch24organic`, 2026-09-26)
-----------------------------------------------
Production never taught Fly, so §Ch24's per-trainee Fly ladder could offer only walkable ground and the return
bridge could not fly home. `ensure_fly_learner` now teaches HM02 in `_play` — after the §Ch24 latch, before
`train_for_league`. What must not regress:

  F1  `StoryMode._play`: `self.mark_ch24_owns_run()` < `ensure_fly_learner(...)` < the next `train_for_league(...)`.
  F2  `--driver ch24handoff` runs the SAME order (latch < teach < train < `prepare_and_open_the_league`), so the
      drive that proves the chain cannot silently drift from production.
  F2b ...and it installs production's battle strategies in `on_battle_started` (SwapTrain / StoryItem). Without
      that hook the harness FLEES every wild battle — the first H1/K drives banked 0 EXP in ~500k frames.
  F3  `_fly_teach_plan` (PURE) picks the highest-level COMPATIBLE mon that can give up a slot WITHOUT losing its
      last USABLE attack (battle ban list respected; status first, then banned, then weakest usable) — never a
      saturated four-HM mon (`hm_learner_slot`'s level-only rule picks exactly that), never an egg, None if nobody.
  F4  `POKEBOT_CH24_FAULT_NOFLYTEACH` is read in `ensure_fly_learner` (comments stripped) and registered.
  F5  GENERAL: EVERY driver class in `story_harness.py` that trains (`train_team` / `train_for_league` /
      `train_for_victory_road` / `train_one_for_league`) defines `on_battle_started` — itself or an ancestor.

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


POWER = {"Surf": 95, "Strength": 80, "Rock Smash": 40, "Dive": 80, "Flash": 0, "Peck": 35, "Aerial Ace": 60,
         "Wing Attack": 60, "Quick Attack": 40, "Growl": 0, "Dig": 60, "Solar Beam": 120, "Sky Attack": 140}
#: The shape of `battle.yml`'s ban list that matters here (the real list is longer).
BANNED = ["None", "Dive", "Fly", "Dig", "Solar Beam", "Sky Attack"]


def _learned(name: str, hm: bool):
    return types.SimpleNamespace(move=types.SimpleNamespace(
        name=name, base_power=POWER[name],
        tm_hm=types.SimpleNamespace(name="HM05" if hm else "TM40") if hm else None))


def mon(level: int, compat: bool, moves, egg: bool = False):
    return types.SimpleNamespace(level=level, is_egg=egg, moves=moves,
                                 species=types.SimpleNamespace(can_learn_tm_hm=lambda item, c=compat: c))


FOUR_HM = [_learned("Surf", True), _learned("Strength", True), _learned("Rock Smash", True), _learned("Dive", True)]
FREE = [_learned("Peck", False), _learned("Aerial Ace", False), None, None]
FULL_BATTLER = [_learned("Peck", False), _learned("Wing Attack", False), _learned("Aerial Ace", False),
                _learned("Quick Attack", False)]
#: The code review's shape: the weakest move is the ONLY one the bot will ever click.
LAST_USABLE_IS_WEAKEST = [_learned("Peck", False), _learned("Dig", False), _learned("Solar Beam", False),
                          _learned("Sky Attack", False)]
#: Its only spendable slot is its only usable attack (Flash 0, Dive banned, Rock Smash HM but see BANNED_RS).
ONLY_SLOT_IS_LAST_ATTACK = [_learned("Peck", False), _learned("Flash", True), _learned("Dive", True),
                            _learned("Rock Smash", True)]
WITH_STATUS = [_learned("Growl", False), _learned("Peck", False), _learned("Wing Attack", False),
               _learned("Aerial Ace", False)]


def f3(plan, sink=None):
    """`plan(party, item, banned) -> (index, replace_slot) | None` — `_fly_teach_plan`'s contract."""
    def idx(party, banned=BANNED):
        p = plan(party, HM02, banned)
        return None if p is None else p[0]

    check(idx([mon(50, True, FOUR_HM), mon(40, True, FREE)]) == 1,
          "F3 a L50 four-HM mon is SKIPPED for a L40 with a slot to spend", sink)
    check(plan([mon(40, True, FREE)], HM02, BANNED) == (0, None), "F3 an EMPTY move slot is used (no replace)", sink)
    check(plan([mon(50, True, FULL_BATTLER), mon(40, True, FREE)], HM02, BANNED) == (0, 0),
          "F3 highest level wins; four usable attacks ⇒ the weakest (Peck, slot 0) goes — H1's measured choice", sink)
    check(idx([mon(60, False, FREE), mon(30, True, FOUR_HM)]) is None,
          "F3 incompatible + saturated ⇒ None (report, never a doomed teach)", sink)
    check(idx([None, mon(70, True, FREE, egg=True)]) is None, "F3 an empty slot and an egg ⇒ None", sink)
    check(plan([mon(55, True, WITH_STATUS)], HM02, BANNED) == (0, 0), "F3 a 0-power status move goes FIRST", sink)
    check(plan([mon(55, True, LAST_USABLE_IS_WEAKEST)], HM02, BANNED) == (0, 1),
          "F3 [Peck, Dig, Solar Beam, Sky Attack]: a BANNED move (Dig, slot 1) goes — never Peck, the last usable "
          "attack (the code review's shape)", sink)
    banned_rs = BANNED + ["Rock Smash"]   # synthetic: make its HM attack unusable too
    check(idx([mon(55, True, ONLY_SLOT_IS_LAST_ATTACK)], banned_rs) is None,
          "F3 a mon whose only spendable slot is its last usable attack is SKIPPED ⇒ None", sink)
    check(idx([mon(55, True, ONLY_SLOT_IS_LAST_ATTACK), mon(30, True, FREE)], banned_rs) == 1,
          "F3 ...and the next compatible learner is taken instead", sink)


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
    cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "Ch24HandoffMode")
    hook = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "on_battle_started"), None)
    seg = ast.get_source_segment(src, hook) if hook else ""
    check(hook is not None and "SwapTrainBattleStrategy()" in seg and "StoryItemBattleStrategy()" in seg,
          "F2b the hand-off driver installs production's battle strategies (else the harness flees)", sink)


TRAIN_CALLS = {"train_team", "train_for_league", "train_for_victory_road", "train_one_for_league"}


def f5(src, sink=None):
    """GENERAL: every harness driver class that TRAINS must define `on_battle_started` (itself or an in-file
    ancestor). Written because the new hand-off driver lacked it and the harness silently fled every battle."""
    classes = {n.name: n for n in ast.parse(src).body if isinstance(n, ast.ClassDef)}

    def has_hook(c, seen=()):
        if any(isinstance(m, ast.FunctionDef) and m.name == "on_battle_started" for m in c.body):
            return True
        return any(getattr(b, "id", None) in classes and getattr(b, "id") not in seen
                   and has_hook(classes[b.id], seen + (b.id,)) for b in c.bases)

    trainers, missing = [], []
    for name, c in classes.items():
        calls = {getattr(n.func, "attr", getattr(n.func, "id", None)) for n in ast.walk(c) if isinstance(n, ast.Call)}
        if calls & TRAIN_CALLS:
            trainers.append(name)
            if not has_hook(c):
                missing.append(name)
    check(bool(trainers) and not missing,
          f"F5 every training driver defines on_battle_started ({len(trainers)} trainers; missing {missing})", sink)


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
    print("\n== F5 every training driver has a battle hook ==")
    f5(harness)
    print("\n== F3 the learner rule (pure) ==")
    f3(PL._fly_teach_plan)
    print("\n== F4 the arm ==")
    fn = next(n for n in ast.parse(league).body if isinstance(n, ast.FunctionDef) and n.name == "ensure_fly_learner")
    seg = _strip_comments(ast.get_source_segment(league, fn) or "")
    check('"POKEBOT_CH24_FAULT_NOFLYTEACH") == "1"' in seg, "F4 NOFLYTEACH is READ in ensure_fly_learner")
    check("`POKEBOT_CH24_FAULT_NOFLYTEACH`" in REGISTRY.read_text(encoding="utf-8"), "F4 NOFLYTEACH is registered")
    check("_fly_teach_plan(" in seg and "replace_slot=replace_slot" in seg,
          "F4 ensure_fly_learner uses the gated plan AND hands its slot to teach_hm_move (not teach_hm_move's own rule)")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []

    def level_only(party, item, banned):
        best, lv = None, -1
        for i, m in enumerate(party):
            if m is not None and not m.is_egg and m.species.can_learn_tm_hm(item) and m.level > lv:
                best, lv = i, m.level
        return None if best is None else (best, None)
    f3(level_only, sink)
    check(bool(sink), f"FAULT a level-only picker (hm_learner_slot's rule) FAILS F3 ({len(sink)} caught)")

    def teach_hm_moves_own_rule(party, item, banned):
        """The pre-review behaviour: learner = compatible with a non-HM slot, slot = 0-power else WEAKEST."""
        best, lv = None, -1
        for i, m in enumerate(party):
            if m is None or m.is_egg or not m.species.can_learn_tm_hm(item):
                continue
            if any(l is None or l.move.tm_hm is None for l in m.moves) and m.level > lv:
                best, lv = i, m.level
        if best is None:
            return None
        moves = party[best].moves
        if any(l is None for l in moves):
            return best, None
        elig = [s for s, l in enumerate(moves) if l.move.tm_hm is None]
        zero = [s for s in elig if moves[s].move.base_power == 0]
        return best, (zero[0] if zero else min(elig, key=lambda s: moves[s].move.base_power))
    sink = []
    f3(teach_hm_moves_own_rule, sink)
    check(bool(sink), f"FAULT the pre-review slot rule (weakest move, ban list ignored) FAILS F3 ({len(sink)} caught)")

    hook_def = "    def on_battle_started(self, encounter):\n        \"\"\"⛔⛔ THE PRODUCTION STRATEGIES"
    assert harness.count(hook_def) == 1, "hook anchor moved — update the gate"
    sink = []
    f2(harness.replace(hook_def, hook_def.replace("on_battle_started", "_no_hook")), sink)
    check(bool(sink), f"FAULT a hand-off driver WITHOUT on_battle_started FAILS F2b ({len(sink)} caught)")
    sink = []
    f5(harness.replace(hook_def, hook_def.replace("on_battle_started", "_no_hook")), sink)
    check(bool(sink), f"FAULT a training driver WITHOUT on_battle_started FAILS F5 ({len(sink)} caught)")

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
