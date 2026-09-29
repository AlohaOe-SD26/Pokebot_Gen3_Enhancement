r"""GATE (pure) — USER RULING 20 Phase 2 P2-c: with `POKEBOT_R20_HUNTFIRST=1`, before gym 1 an ARMED or WALKING hunt is
checked BEFORE team building (2026-09-28).

WHY: `decide_dex_catch`'s team-building branch returns before its hunt-armed check, so before gym 1 a team catch was
admitted while a counter hunt spun for its target. `counter_hunt.catch_confirmed`'s party path is species-blind, so such
a catch ENDS the spin and the hunt "found nothing" (measured live with `--driver huntfirst`: an Abra admitted as a team
catch three times while the hunt was armed; `ai-research-notes/2026-09-28-r20P2c-PREDICTIONS.md`).
  H1  OFF, pre-gym-1, armed: admitted as team building (the old order, byte-identical).
  H2  ON, pre-gym-1, armed: refused, "hunt is armed".
  H3  ON, pre-gym-1, a hunt WALKING (`#27-enroutejoin`): refused, "walking".
  H4  ON, pre-gym-1, no hunt: admitted as team building (the ordinary case is unchanged).
  H5  OFF, pre-gym-1, walking: admitted (the flag is what changes it).
  H6  ON, post-gym-1, full party, armed: refused "hunt is armed", as with the flag OFF.
  H7  ON, post-gym-1, full party, walking, not armed: "goes to the PC box" (the flag changes nothing after gym 1).
  H8/H9 ON, post-gym-1, party 3, armed / walking: still refused as "runway" FIRST (the new checks need `pre_badge1`).
  A1  `reset_per_run_state` reads the flag: unset -> `_hunt_first is False`; `=1` -> True.
  A2  by AST: the adapter passes `hunt_first=self._hunt_first`.
  A3  `POKEBOT_R20_HUNTFIRST` is registered in `29-DISABLED-FEATURES-REGISTRY.md`.
FAULT ARMS (built in; the unmutated subject must pass first; each must FAIL):
  F1  the new checks moved AFTER the pre-gym-1 branch (the old order, with the flag still read): H2 fails.
  F2  an adapter passing `hunt_first=False` fails A2; F3 the keyword kept only in a COMMENT still fails A2.
  F4  `pre_badge1` dropped from the armed check (the review's mutant) fails H8.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_hunt_first.py
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

import plugins.custom_modes.story_mode as SM  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG = "POKEBOT_R20_HUNTFIRST"
failures: list = []

#: Before gym 1, party of 2 below the team target of 4, everything clear. Each case overrides a few fields.
BASE = dict(
    is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=True,
    party_slots_used=2, battler_count=2, party_target=4, resource_block=None,
    spare_balls=SM.DEX_CATCH_BALL_RESERVE + 15, hunt_armed=False, training=False, boxed_count=0,
    party_healthy=True, species_dex=63, owned_dex=frozenset({258}), party_dex=frozenset({258, 261}),
    attempts=0, expected_throws=2.0,
)
POST = dict(pre_badge1=False, party_slots_used=6, battler_count=6)
POST3 = dict(pre_badge1=False, party_slots_used=3, battler_count=3)
CASES = [
    ("H1", dict(hunt_armed=True), True, "pre-gym-1"),
    ("H2", dict(hunt_armed=True, hunt_first=True), False, "hunt is armed"),
    ("H3", dict(hunt_walking=True, hunt_first=True), False, "walking"),
    ("H4", dict(hunt_first=True), True, "pre-gym-1"),
    ("H5", dict(hunt_walking=True), True, "pre-gym-1"),
    ("H6", dict(POST, hunt_armed=True, hunt_first=True), False, "hunt is armed"),
    ("H7", dict(POST, hunt_walking=True, hunt_first=True), True, "PC box"),
    # review 2026-09-28: after gym 1 BELOW a full party the flag must leave the runway refusal first. Without these two,
    # an edit dropping `pre_badge1` from one new check changed only a reason and shipped unseen.
    ("H8", dict(POST3, hunt_armed=True, hunt_first=True), False, "runway"),
    ("H9", dict(POST3, hunt_walking=True, hunt_first=True), False, "runway"),
]


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def run_cases(fn, sink=None):
    for tag, over, want, why in CASES:
        got, reason = fn(**dict(BASE, **over))
        check(got is want and why.lower() in reason.lower(),
              f"{tag} catch={got} reason={reason!r} (want {want}, {why!r})", sink)


def per_run_flag(env: dict):
    saved = os.environ.pop(FLAG, None)
    try:
        os.environ.update(env)
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        return m._hunt_first
    finally:
        os.environ.pop(FLAG, None)
        if saved is not None:
            os.environ[FLAG] = saved


def wiring(src: str, sink=None):
    ok = False
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "decide_dex_catch":
            ok = ok or any(kw.arg == "hunt_first" and ast.unparse(kw.value) == "self._hunt_first" for kw in node.keywords)
    check(ok, f"A2 the adapter passes hunt_first=self._hunt_first ({ok})", sink)


def mutant_predicate(src: str, old: str, new: str):
    """The predicate with one source edit, compiled from a COPY of the source (the file is never touched)."""
    assert src.count(old) == 1, old
    mod = types.ModuleType("story_mode_mutant")
    mod.__file__ = str(SM_PATH)
    exec(compile(src.replace(old, new, 1), "story_mode_mutant", "exec"), mod.__dict__)
    return mod.decide_dex_catch


def old_order_predicate(src: str):
    """The predicate with the two new checks moved AFTER the pre-gym-1 branch — the old order, flag still read."""
    block_start = "    if hunt_first and pre_badge1 and hunt_armed:"
    i = src.index(block_start)
    j = src.index("    # ---- PRE-GYM-1: organic team building", i)
    block = src[i:j]
    k = src.index("    # ---- POST-GYM-1: THE DEX FENCE", j)
    mutant = src[:i] + src[i + len(block):k] + block + src[k:]
    mod = types.ModuleType("story_mode_old_order")
    mod.__file__ = str(SM_PATH)
    exec(compile(mutant, "story_mode_old_order", "exec"), mod.__dict__)
    return mod.decide_dex_catch


def main() -> int:
    print("H — the pure predicate")
    run_cases(SM.decide_dex_catch)
    off, on = per_run_flag({}), per_run_flag({FLAG: "1"})
    check(off is False and on is True, f"A1 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    src = SM_PATH.read_text(encoding="utf-8")
    wiring(src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(FLAG in reg, f"A3 {FLAG} is registered in 29-DISABLED-FEATURES-REGISTRY.md")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    sink: list = []
    run_cases(old_order_predicate(src), sink)
    check(base_ok and any(s.startswith("H2") for s in sink),
          f"F1 the checks moved after the pre-gym-1 branch fail H2 (red: {[s.split()[0] for s in sink]})")
    sink = []
    run_cases(mutant_predicate(src, "if hunt_first and pre_badge1 and hunt_armed:", "if hunt_first and hunt_armed:"), sink)
    check(base_ok and any(s.startswith("H8") for s in sink),
          f"F4 pre_badge1 dropped from the armed check fails H8 (red: {[s.split()[0] for s in sink]})")
    sink = []
    wiring(src.replace("hunt_first=self._hunt_first,", "hunt_first=False,", 1), sink)
    check(base_ok and bool(sink), "F2 an adapter passing hunt_first=False fails A2")
    sink = []
    wiring(src.replace("hunt_first=self._hunt_first,", "# hunt_first=self._hunt_first,", 1), sink)
    check(base_ok and bool(sink), "F3 the keyword kept only in a COMMENT still fails A2")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — before gym 1 an armed or walking hunt comes before team building, only with POKEBOT_R20_HUNTFIRST=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
