r"""GATE (pure) — USER RULING 24 step 3: with `POKEBOT_R24_CATCHTRAIN=1` a post-gym-1 dex catch starts during a TRAINING
grind, and a dex catch started during swap-training keeps the trainee as lead (2026-09-29).

WHY: the user ruled (`06`, 2026-09-28): *"catching should always be available … even in training"*. The fence refused
every post-gym-1 catch while `train_team` ran. The lift must remove THAT refusal only. And because the catch strategy
inherits the default `choose_new_lead_after_battle` (it rotates when the lead has FAINTED) while `train_team` picks its
trainee by SLOT, a faint in such a catch would rotate a slot-based grind onto the wrong mon (the KI-84 early exit) — so a
dex catch started during swap-training keeps the lead (C3).
  T1  OFF, training: refused "a training grind is in progress" (the old behaviour).
  T2  ON, training: admitted.
  T3  ON, training AND hurt, with the health lift OFF: still refused "not at full strength" (one gate wide).
  T4  ON, training, spare at the reserve: still refused on the reserve.   T5 ON, training, hunt armed: refused.
  T6  ON, training, before gym 1: team building, unchanged.
  A1  by AST: the adapter passes `lift_training=self._r24_catchtrain`.   A2 `reset_per_run_state` reads the flag.
  A3  both flags are registered in 29.
  L1  `StoryDexCatchStrategy` built while swap-training with the running mode's flag ON returns None from
      `choose_new_lead_after_battle`; with the flag OFF, or when not training, it returns the parent's answer.
FAULT ARMS (built in; the unmutated subject must pass first; each must FAIL):
  F1  `POKEBOT_R24_FAULT_ROTATE=1` (in production code) restores the rotation: L1 fails.
  F2  an adapter passing `lift_training=False` fails A1; F3 the keyword kept only in a COMMENT still fails A1.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dex_catch_training.py
"""
from __future__ import annotations

import ast
import contextlib
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.battle_strategies.default as DEFAULT  # noqa: E402
import modules.story.early_game as EG  # noqa: E402
import plugins.custom_modes.story_mode as SM  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG, FAULT = "POKEBOT_R24_CATCHTRAIN", "POKEBOT_R24_FAULT_ROTATE"
failures: list = []

BASE = dict(
    is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=False,
    party_slots_used=6, battler_count=6, party_target=4, resource_block=None,
    spare_balls=SM.DEX_CATCH_BALL_RESERVE + 20, hunt_armed=False, training=True, boxed_count=0,
    party_healthy=True, species_dex=276, owned_dex=frozenset({1}), party_dex=frozenset({2}),
    attempts=0, expected_throws=2.0,
)
ON = dict(lift_training=True)
CASES = [
    ("T1", dict(), False, "training"),
    ("T2", ON, True, "PC box"),
    ("T3", dict(ON, party_healthy=False), False, "full strength"),
    ("T4", dict(ON, spare_balls=SM.DEX_CATCH_BALL_RESERVE), False, "dex reserve"),
    ("T5", dict(ON, hunt_armed=True), False, "hunt is armed"),
    ("T6", dict(ON, pre_badge1=True, party_slots_used=2, battler_count=2), True, "pre-gym-1"),
]


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


def keeps_lead(flag_on: bool, training: bool) -> "int | None":
    """`choose_new_lead_after_battle` of a real `StoryDexCatchStrategy` built under a stubbed party, a stubbed running
    mode and a stubbed swap-training state. The parent is stubbed to answer 3 (\"rotate to slot 3\")."""
    fake_party = types.SimpleNamespace(first_non_fainted=types.SimpleNamespace(index=0))
    saved = (DEFAULT.get_party, EG._SWAP_TRAIN, getattr(SM.context, "bot_mode_instance", None),
             DEFAULT.DefaultBattleStrategy.choose_new_lead_after_battle)
    try:
        DEFAULT.get_party = lambda: fake_party
        EG._SWAP_TRAIN = training
        SM.context.bot_mode_instance = types.SimpleNamespace(_r24_catchtrain=flag_on)
        DEFAULT.DefaultBattleStrategy.choose_new_lead_after_battle = lambda self: 3
        strat = SM.StoryDexCatchStrategy()
        return strat.choose_new_lead_after_battle()
    finally:
        (DEFAULT.get_party, EG._SWAP_TRAIN, SM.context.bot_mode_instance,
         DEFAULT.DefaultBattleStrategy.choose_new_lead_after_battle) = saved


def lead(sink=None):
    on_tr, off_tr, on_idle = keeps_lead(True, True), keeps_lead(False, True), keeps_lead(True, False)
    check(on_tr is None and off_tr == 3 and on_idle == 3,
          f"L1 keep the lead: flag ON + training -> {on_tr} (want None); flag OFF + training -> {off_tr} (want 3); "
          f"flag ON, not training -> {on_idle} (want 3)", sink)


def wiring(src: str, sink=None):
    ok = False
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "decide_dex_catch":
            ok = ok or any(kw.arg == "lift_training" and ast.unparse(kw.value) == "self._r24_catchtrain"
                           for kw in node.keywords)
    check(ok, f"A1 the adapter passes lift_training=self._r24_catchtrain ({ok})", sink)


def main() -> int:
    print("T — the pure predicate")
    with env():
        for tag, over, want, why in CASES:
            got, reason = SM.decide_dex_catch(**dict(BASE, **over))
            check(got is want and why.lower() in reason.lower(), f"{tag} catch={got} reason={reason!r} (want {want}, {why!r})")
        src = SM_PATH.read_text(encoding="utf-8")
        wiring(src)
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        off = m._r24_catchtrain
    with env(**{FLAG: "1"}):
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        on = m._r24_catchtrain
    check(off is False and on is True, f"A2 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(FLAG in reg and FAULT in reg, f"A3 {FLAG} and {FAULT} are registered in 29")
    print("L — keep the trainee as lead (C3)")
    with env():
        lead()

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    sink: list = []
    with env(**{FAULT: "1"}):
        lead(sink)
    check(base_ok and bool(sink), f"F1 {FAULT}=1 restores the rotation: L1 fails")
    sink = []
    wiring(src.replace("lift_training=self._r24_catchtrain,", "lift_training=False,", 1), sink)
    check(base_ok and bool(sink), "F2 an adapter passing lift_training=False fails A1")
    sink = []
    wiring(src.replace("lift_training=self._r24_catchtrain,", "# lift_training=self._r24_catchtrain,", 1), sink)
    check(base_ok and bool(sink), "F3 the keyword kept only in a COMMENT still fails A1")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — POKEBOT_R24_CATCHTRAIN lifts only the training refusal, and a training catch keeps the trainee as lead")
    return 0


if __name__ == "__main__":
    sys.exit(main())
