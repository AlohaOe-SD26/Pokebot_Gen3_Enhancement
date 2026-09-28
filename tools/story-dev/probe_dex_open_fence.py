r"""GATE (pure) — USER RULING 20 Phase 2 P2-b: with `POKEBOT_R20_OPENFENCE=1` a post-gym-1 dex catch below a full party
JOINS THE PARTY, and every other gate of `decide_dex_catch` still applies (2026-09-28).

WHY: before P2-b the fence refused every post-gym-1 catch below six as "runway" (`#24-partycap`: the empty slots are
where HM/counter catches land; filling them once cost 36 points of finish rate). The user's RULING 20 asks for a full
team caught along the way, so P2-b lifts that ONE refusal behind a flag, default OFF. The dangerous way to build it is
an "open" branch that returns True at once: it would skip the hunt, training, reserve, health, attempt and catch-rate
gates together, and a catch battle never fights back (`catch.py`), so a hurt party would be caught out. This gate
proves the lift is exactly one refusal wide.
  O0  flag OFF (the default): post-gym-1 at party 1 is refused as runway (the ordinary case, unchanged).
  O1  ON, party 1, everything clear: admitted, and the reason says "joins the party".
  O2  ON, party 5: admitted, "joins the party".
  O3  ON, party 6: admitted, "goes to the PC box" (the full-party path is unchanged).
  O3e ON, 5 mons + 1 EGG (six raw slots): "goes to the PC box" (the game counts the egg's slot).
  O4-O10 ON, party 1, one later gate tripped each: an armed hunt, training, spare balls AT the reserve, a hurt party,
      the attempt cap, too many expected throws, a full PC. Each is still refused, for its own reason.
  O11 ON, before gym 1: unchanged team building (the pre-gym-1 branch returns before the fence).
  A1  `reset_per_run_state` reads the flag: unset -> `_open_fence is False`; `=1` -> True.
  A2  wiring, by AST: the adapter's `decide_dex_catch(...)` call passes `open_fence=self._open_fence`.
  A3  both flags are registered in `29-DISABLED-FEATURES-REGISTRY.md`.
FAULT ARMS (built in; the unmutated subject must pass first; each must FAIL):
  F1  `POKEBOT_R20_FAULT_OPENEARLY=1` (in production code) returns "joins the party" before the later gates: EXACTLY
      O4-O10 go red. Equality, not a subset: an arm that also fired at a full party would redden O3/O3e as well.
  F2  the same fault arm leaves O0 (flag OFF) green: it reaches only the open branch.
  F3  a source mutant passing `open_fence=False` fails A2.
  F4  a mutant that drops the keyword but keeps it in a COMMENT still fails A2 (a mention cannot satisfy the gate).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dex_open_fence.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import plugins.custom_modes.story_mode as SM  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG, FAULT = "POKEBOT_R20_OPENFENCE", "POKEBOT_R20_FAULT_OPENEARLY"
failures: list = []

#: Post-gym-1, party of ONE (the P2-b fixture's shape), everything else clear. Each case overrides one field.
BASE = dict(
    is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=False,
    party_slots_used=1, battler_count=1, party_target=4, resource_block=None,
    spare_balls=SM.DEX_CATCH_BALL_RESERVE + 21, hunt_armed=False, training=False, boxed_count=0,
    party_healthy=True, species_dex=304, owned_dex=frozenset({258, 259}), party_dex=frozenset({259}),
    attempts=0, expected_throws=2.0,
)

ON = dict(open_fence=True)
CASES = [
    ("O0", dict(), False, "runway"),
    ("O1", ON, True, "joins the party"),
    ("O2", dict(ON, party_slots_used=5, battler_count=5), True, "joins the party"),
    ("O3", dict(ON, party_slots_used=6, battler_count=6), True, "PC box"),
    ("O3e", dict(ON, party_slots_used=6, battler_count=5), True, "PC box"),
    ("O4", dict(ON, hunt_armed=True), False, "hunt is armed"),
    ("O5", dict(ON, training=True), False, "training"),
    ("O6", dict(ON, spare_balls=SM.DEX_CATCH_BALL_RESERVE), False, "dex reserve"),
    ("O7", dict(ON, party_healthy=False), False, "full strength"),
    ("O8", dict(ON, attempts=SM.DEX_CATCH_MAX_ATTEMPTS), False, "already attempted"),
    ("O9", dict(ON, expected_throws=SM.DEX_CATCH_MAX_EXPECTED_THROWS + 1), False, "expected throws"),
    ("O10", dict(ON, boxed_count=SM.PC_STORAGE_SLOTS), False, "PC storage is full"),
    ("O11", dict(ON, pre_badge1=True), True, "pre-gym-1"),
]
LATER_GATES = {"O4", "O5", "O6", "O7", "O8", "O9", "O10"}


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def run_cases(sink=None) -> set:
    red = set()
    for tag, over, want, why in CASES:
        got, reason = SM.decide_dex_catch(**dict(BASE, **over))
        ok = got is want and why.lower() in reason.lower()
        if not ok:
            red.add(tag)
        check(ok, f"{tag} catch={got} reason={reason!r} (want {want}, {why!r})", sink)
    return red


def with_env(env: dict, fn):
    saved = {k: os.environ.get(k) for k in (FLAG, FAULT)}
    try:
        for k in (FLAG, FAULT):
            os.environ.pop(k, None)
        os.environ.update(env)
        return fn()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def per_run_flag(env: dict):
    def read():
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        return m._open_fence
    return with_env(env, read)


def wiring(src: str, sink=None):
    ok = False
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "decide_dex_catch":
            for kw in node.keywords:
                if kw.arg == "open_fence" and ast.unparse(kw.value) == "self._open_fence":
                    ok = True
    check(ok, f"A2 the adapter's decide_dex_catch(...) call passes open_fence=self._open_fence ({ok})", sink)


def main() -> int:
    print("O — the pure predicate, flag OFF and ON")
    with_env({}, run_cases)
    off, on = per_run_flag({}), per_run_flag({FLAG: "1"})
    check(off is False and on is True, f"A1 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    src = SM_PATH.read_text(encoding="utf-8")
    wiring(src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(FLAG in reg and FAULT in reg, f"A3 {FLAG} and {FAULT} are registered in 29-DISABLED-FEATURES-REGISTRY.md")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    sink: list = []
    red = with_env({FAULT: "1"}, lambda: run_cases(sink))
    # ⛔ EQUALITY, not a subset (review 2026-09-28): a fault arm that also fired at a FULL party would turn O3/O3e red
    # too, and a subset check passed it (proved by a mutant that dropped the arm's `< PARTY_CAPACITY` guard).
    check(base_ok and red == LATER_GATES, f"F1 {FAULT}=1 knocks over exactly the later gates, and nothing at a full "
                                          f"party: red={sorted(red)}")
    check(base_ok and "O0" not in red, f"F2 {FAULT}=1 leaves the flag-OFF case O0 green (it reaches only the open "
                                       f"branch)")
    mutant = src.replace("open_fence=self._open_fence,", "open_fence=False,", 1)
    sink = []
    wiring(mutant, sink)
    check(base_ok and mutant != src and bool(sink), "F3 an adapter passing open_fence=False fails A2")
    mutant = src.replace("open_fence=self._open_fence,", "# open_fence=self._open_fence,", 1)
    sink = []
    wiring(mutant, sink)
    check(base_ok and mutant != src and bool(sink), "F4 the keyword kept only in a COMMENT still fails A2")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — POKEBOT_R20_OPENFENCE lifts exactly the runway refusal; every later gate still applies; OFF unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
