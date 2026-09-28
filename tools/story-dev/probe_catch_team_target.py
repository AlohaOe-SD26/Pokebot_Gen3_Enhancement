r"""GATE (pure) — USER RULING 20 Phase 2 P2-a: the pre-gym-1 team target is ONE value, read by BOTH readers, and flag-gated
(2026-09-28). This closes the build spec's gap R-a: no gate asserted the target at all.

WHY: the target was raised to 6 once (`#24-partycap`, 2026-08-05) and reverted the same day (finish rate 52.0% → 15.8%),
so it must stay 4 unless `POKEBOT_R20_TEAM6=1`. The fence (`decide_dex_catch`, via `party_target=`) and the team loop
(`catch_starter_team(...)`) each read it; if they disagreed, the fence would admit catches the loop never makes (or the
reverse) with no error anywhere.
  A1  flag OFF: `_catch_team_target == 4` and `_team_loop_target() == 4` (the ordinary case, byte-identical).
  A2  flag ON:  both are 6.
  A3  wiring, by AST (comments cannot satisfy it): the fence call passes `party_target=self._catch_team_target`, and the
      team-loop call is `catch_starter_team(self._team_loop_target())`.
  A4  `_team_admissible_left` (the none_left helper) on a stubbed dex/party/table: unowned-and-not-in-party only; None
      (keep looping) when the table is unreadable.
FAULT ARMS (built in; each must FAIL; the unmutated subject must pass first):
  F1  `POKEBOT_R20_FAULT_TARGETLOOP=1` with the flag ON: the loop target (4) differs from the fence's (6) -> A2 fails;
  F2  a source mutant whose loop call reads a literal 4 -> A3 fails.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_catch_team_target.py
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

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAGS = ("POKEBOT_R20_TEAM6", "POKEBOT_R20_FAULT_TARGETLOOP")
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def targets(**env):
    saved = {k: os.environ.get(k) for k in FLAGS}
    try:
        for k in FLAGS:
            os.environ.pop(k, None)
        os.environ.update(env)
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        return m._catch_team_target, m._team_loop_target()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def wiring(src: str, sink=None):
    tree = ast.parse(src)
    fence_ok = loop_ok = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for kw in node.keywords:
            if kw.arg == "party_target" and ast.unparse(kw.value) == "self._catch_team_target":
                fence_ok = True
        if name == "catch_starter_team" and node.args and ast.unparse(node.args[0]) == "self._team_loop_target()":
            loop_ok = True
    check(fence_ok and loop_ok, f"A3 the fence reads self._catch_team_target ({fence_ok}) and the loop is "
          f"catch_starter_team(self._team_loop_target()) ({loop_ok})", sink)


def admissible():
    S = types.SimpleNamespace
    sp = {n: S(name=n, national_dex_number=d) for n, d in (("Abra", 63), ("Skitty", 300), ("Taillow", 276),
                                                           ("Nincada", 290), ("Whismur", 293))}
    enc = S(land_encounters=[S(species=sp[n]) for n in sp])
    party = [S(species=sp["Nincada"], is_egg=False), S(species=sp["Skitty"], is_egg=True), None]
    import modules.map as MAP
    import modules.pokedex as DEX

    saved = (MAP.get_wild_encounters_for_map, DEX.get_pokedex, EG.get_party)
    try:
        MAP.get_wild_encounters_for_map = lambda *a: enc
        DEX.get_pokedex = lambda: S(owned_species=[sp["Whismur"], sp["Abra"]])
        EG.get_party = lambda: party
        got = EG._team_admissible_left(S(value=(0, 31)))
        MAP.get_wild_encounters_for_map = lambda *a: None
        unreadable = EG._team_admissible_left(S(value=(0, 31)))
    finally:
        MAP.get_wild_encounters_for_map, DEX.get_pokedex, EG.get_party = saved
    check(got == {"Skitty", "Taillow"} and unreadable is None,
          f"A4 admissible = unowned and not in party, an EGG not counting as in party ({got}); an unreadable table -> "
          f"None ({unreadable})")


def main() -> int:
    off = targets()
    check(off == (4, 4), f"A1 flag OFF: target and loop target are 4 (got {off})")
    on = targets(POKEBOT_R20_TEAM6="1")
    check(on == (6, 6), f"A2 flag ON: target and loop target are 6 (got {on})")
    src = SM_PATH.read_text(encoding="utf-8")
    wiring(src)
    admissible()
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(all(f in reg for f in FLAGS), f"A5 {FLAGS} are registered in 29-DISABLED-FEATURES-REGISTRY.md")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    fault = targets(POKEBOT_R20_TEAM6="1", POKEBOT_R20_FAULT_TARGETLOOP="1")
    sink: list = []
    check(fault == (6, 6), f"A2 under the fault arm (got {fault})", sink)
    check(base_ok and bool(sink), f"F1 POKEBOT_R20_FAULT_TARGETLOOP=1 splits the loop target from the fence ({fault})")
    mutant = src.replace("catch_starter_team(self._team_loop_target())", "catch_starter_team(4)", 1)
    sink = []
    wiring(mutant, sink)
    check(base_ok and mutant != src and bool(sink), "F2 a loop call reading a literal 4 fails A3")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — one pre-gym-1 team target, read by both readers, 4 unless POKEBOT_R20_TEAM6=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
