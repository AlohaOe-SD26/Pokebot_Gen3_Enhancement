r"""GATE — an unreachable training ground is remembered from where it was CHOSEN, not only from where the walk died
(`#26-healmap-lavaridge` recon, 2026-09-27).

WHY: `_note_training_unreachable` keyed its memory by the map the bot stood on when the walk FAILED, while
`_training_blocked` checks the map the next pick happens on. After an ABANDON (MAINTAIN, a counter hunt) the next pick
comes from the ORIGIN, so the memory never matched. MEASURED in batch `#26-batch0926`:
- ROUTE111 (25,55) was abandoned 45 times; it is Go-Goggles-gated before Flannery.
- Run P1r7 re-walked it 19 times, each cycle then derailing on the heal, until five derails in a row ended the run.
After a RAISE (the relocation path) the re-pick is where the walk DIED, so that key must stay too.

  T1  both keys: a walk chosen from LAVARIDGE that dies on ROUTE111 ⇒ blocked from BOTH, and not from a third map.
  T2  no origin ⇒ the death key only (the old behaviour, for any caller that does not pass one); nothing
      keyable ⇒ nothing recorded.
  T3  THE P1r7 LOOP, replayed on the real methods: pick from Lavaridge, die on Route 111, note, pick again from
      Lavaridge ⇒ the ground is now REFUSED. With the old keying it is picked again.
  T4  WIRING (AST): every `self._note_training_unreachable(...)` call in story_mode.py passes `origin=<name>`, and
      that name is assigned from `self._here_map()` EARLIER in the same function.
  T5  the arm `POKEBOT_TRAINBLOCK_FAULT_DIEDKEY` is read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): the arm set (the old keying) fails T1/T3; a call site without `origin=` fails T4.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_trainblock_origin.py
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

SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_TRAINBLOCK_FAULT_DIEDKEY"
LAVARIDGE, ROUTE111, MAUVILLE = (0, 12), (0, 26), (0, 2)
GROUND = types.SimpleNamespace(value=(0, 26), name="ROUTE111")
TILE = (25, 55)
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _mode(here):
    """A StoryMode with only the memory, and `_here_map` stubbed to a mutable cell."""
    m = SM.StoryMode.__new__(SM.StoryMode)
    m._training_unreachable = set()
    m._here_map = lambda: here[0]
    return m


def behaviour(sink=None):
    here = [ROUTE111]
    m = _mode(here)
    m._note_training_unreachable(GROUND, TILE, origin=LAVARIDGE)
    blocked = {}
    for name, where in (("Lavaridge", LAVARIDGE), ("Route 111", ROUTE111), ("Mauville", MAUVILLE)):
        here[0] = where
        blocked[name] = m._training_blocked(GROUND, TILE)
    check(blocked["Lavaridge"] and blocked["Route 111"] and not blocked["Mauville"],
          f"T1 chosen from Lavaridge, died on Route 111 ⇒ blocked from both and not from Mauville ({blocked})", sink)

    here = [ROUTE111]
    m = _mode(here)
    m._note_training_unreachable(GROUND, TILE)
    here[0] = LAVARIDGE
    only_died = not m._training_blocked(GROUND, TILE)
    here[0] = ROUTE111
    check(only_died and m._training_blocked(GROUND, TILE), "T2 no origin ⇒ the death key only (the old reading)", sink)
    here = [None]
    m = _mode(here)
    m._note_training_unreachable(GROUND, TILE)
    check(m._training_unreachable == set(), "T2 nothing keyable ⇒ nothing recorded", sink)

    # T3 — the P1r7 loop: pick from Lavaridge (not blocked), walk dies on Route 111, then pick again from Lavaridge.
    here = [LAVARIDGE]
    m = _mode(here)
    first = m._training_blocked(GROUND, TILE)
    origin = m._here_map()
    here[0] = ROUTE111
    m._note_training_unreachable(GROUND, TILE, origin=origin)
    here[0] = LAVARIDGE
    again = m._training_blocked(GROUND, TILE)
    check(first is False and again is True,
          f"T3 the P1r7 loop: first pick allowed ({first}), the re-pick from Lavaridge REFUSED ({again})", sink)


def wiring(src: str, sink=None) -> None:
    tree = ast.parse(src)
    calls, bad = 0, []
    for fn in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        origins = {t.id: a.lineno for a in ast.walk(fn) if isinstance(a, ast.Assign)
                   and isinstance(a.value, ast.Call) and isinstance(a.value.func, ast.Attribute)
                   and a.value.func.attr == "_here_map"
                   for t in a.targets if isinstance(t, ast.Name)}
        for c in ast.walk(fn):
            if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                    and c.func.attr == "_note_training_unreachable" and fn.name != "_note_training_unreachable"):
                calls += 1
                kw = {k.arg: k.value for k in c.keywords}
                name = getattr(kw.get("origin"), "id", None)
                if name is None or name not in origins or origins[name] > c.lineno:
                    bad.append(f"{fn.name}:{c.lineno}")
    check(calls >= 3 and not bad,
          f"T4 every call ({calls}) passes origin=<name> assigned from self._here_map() earlier in its function "
          f"(missing: {bad})", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — an unreachable training ground is remembered from where it was CHOSEN (#26-healmap-lavaridge)")
    print("=" * 92)
    src = SRC.read_text(encoding="utf-8")
    os.environ.pop(ARM, None)
    print("\n== T1-T3 behaviour (the real methods, the map stubbed) ==")
    behaviour()
    print("\n== T4 wiring ==")
    wiring(src)
    print("\n== T5 the arm ==")
    check(f'environ.get("{ARM}") == "1"' in src and f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"),
          f"T5 {ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    os.environ[ARM] = "1"
    try:
        behaviour(sink)
    finally:
        os.environ.pop(ARM, None)
    check(bool(sink), f"FAULT the arm (the old death-only keying) FAILS T1/T3 ({len(sink)} caught)")
    sink = []
    wiring(src.replace("origin=_maint_origin)", ")", 1), sink)
    check(bool(sink), f"FAULT a call site without origin= FAILS T4 ({len(sink)} caught)")

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
