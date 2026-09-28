r"""GATE (pure) — `#27-enroutejoin`: an HM-learner or counter hunt's WALK runs under `early_game.hunt_walk`, and the dex
fence reads the marker (2026-09-28).

WHY: both hunts arm only on ARRIVAL, so the dex fence could not see their walk. With RULING 20 P2-b's
`POKEBOT_R20_OPENFENCE` a new species met there JOINED THE PARTY. `ensure_hm_learner` then compared its spin against the
party count it took at ENTRY, stopped on the first frame and raised "never caught one" having hunted nothing; a counter
could be pushed into the box untrained (`ai-research-notes/2026-09-28-enroutejoin-AUDIT.md`). The fence's side (a party
join is refused while `hunt_walking`) is `probe_dex_open_fence.py` O12; THIS gate proves the marker is true exactly
during the walks and that every walk is wrapped.
  W1  during a wrapped walk `hunt_walk_active()` is True; after it, False; the walk's return value passes through.
  W2  a walk that RAISES restores False, and the error propagates.
  W3  a walk CLOSED mid-way (a whiteout unwind closes the generator) restores False.
  W4  nested walks restore the OUTER value (True) when the inner one ends.
  A1  by AST (comments cannot satisfy it): inside `early_game.ensure_hm_learner` and `counter_hunt.hunt`, every call to
      `_navigate_riding_out` and `provision_poke_balls` is the argument of `hunt_walk(...)`, and each function has both.
  A2  the adapter passes `hunt_walking=bool(_eg.hunt_walk_active())` to `decide_dex_catch`.
  A3  `POKEBOT_ENROUTE_FAULT_NOWALK` is registered in `29-DISABLED-FEATURES-REGISTRY.md`.
FAULT ARMS (built in; the unmutated subject must pass first; each must FAIL):
  F1  `POKEBOT_ENROUTE_FAULT_NOWALK=1` (read in production code): W1 fails (the marker reads False during a walk).
  F2  a source mutant that unwraps the HM hunt's `_navigate_riding_out` fails A1; F3 the same for the counter hunt.
  F4  the wrapped call kept only in a COMMENT, with the real call unwrapped, still fails A1.
  F5  an adapter passing `hunt_walking=False` fails A2.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_hunt_walk.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.early_game as EG  # noqa: E402

SB = ROOT / "sandbox-pokebot"
EG_PATH = SB / "modules" / "story" / "early_game.py"
CH_PATH = SB / "modules" / "story" / "counter_hunt.py"
SM_PATH = SB / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FAULT = "POKEBOT_ENROUTE_FAULT_NOWALK"
WALKS = ("_navigate_riding_out", "provision_poke_balls")
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _walk(seen: list, *, steps=3, boom=False, result="arrived"):
    for _ in range(steps):
        seen.append(EG.hunt_walk_active())
        yield
    if boom:
        raise RuntimeError("walk failed")
    return result


def _drain(gen):
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value


def marker(sink=None):
    EG._HUNT_WALK = False
    seen: list = []
    got = _drain(EG.hunt_walk(_walk(seen)))
    check(seen == [True] * 3 and not EG.hunt_walk_active() and got == "arrived",
          f"W1 True during the walk {seen}, False after ({EG.hunt_walk_active()}), return passed through ({got!r})", sink)
    seen = []
    try:
        _drain(EG.hunt_walk(_walk(seen, boom=True)))
        raised = False
    except RuntimeError:
        raised = True
    check(raised and not EG.hunt_walk_active(), f"W2 a raising walk restores False ({EG.hunt_walk_active()}) and the "
                                                f"error propagates ({raised})", sink)
    seen = []
    g = EG.hunt_walk(_walk(seen, steps=5))
    next(g)
    mid = EG.hunt_walk_active()
    g.close()
    check(mid and not EG.hunt_walk_active(), f"W3 a walk closed mid-way restores False (mid {mid}, after "
                                             f"{EG.hunt_walk_active()})", sink)

    def outer():
        inner_seen: list = []
        yield from EG.hunt_walk(_walk(inner_seen, steps=1))
        return EG.hunt_walk_active()

    after_inner = _drain(EG.hunt_walk(outer()))
    check(after_inner is True and not EG.hunt_walk_active(),
          f"W4 nested: the outer walk is still marked after the inner ends ({after_inner}); False after both "
          f"({EG.hunt_walk_active()})", sink)


def wrapped_walks(src: str, func: str) -> "tuple[int, int, int]":
    """(wrapped, unwrapped, distinct walk names seen) for the walk calls inside `func`."""
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef,)) and n.name == func), None)
    if fn is None:
        return 0, 0, 0
    parents = {}
    for node in ast.walk(fn):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    wrapped = unwrapped = 0
    names = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") in WALKS:
            names.add(node.func.id)
            par = parents.get(node)
            if isinstance(par, ast.Call) and getattr(par.func, "id", "") == "hunt_walk" and node in par.args:
                wrapped += 1
            else:
                unwrapped += 1
    return wrapped, unwrapped, len(names)


def wiring(eg_src: str, ch_src: str, sink=None):
    hm = wrapped_walks(eg_src, "ensure_hm_learner")
    ch = wrapped_walks(ch_src, "hunt")
    check(hm[1] == 0 and hm[2] == 2 and ch[1] == 0 and ch[2] == 2,
          f"A1 every walk call is wrapped: ensure_hm_learner (wrapped, unwrapped, kinds)={hm}; counter_hunt.hunt {ch}", sink)


def adapter(src: str, sink=None):
    ok = False
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "decide_dex_catch":
            ok = ok or any(kw.arg == "hunt_walking" and ast.unparse(kw.value) == "bool(_eg.hunt_walk_active())"
                           for kw in node.keywords)
    check(ok, f"A2 the adapter passes hunt_walking=bool(_eg.hunt_walk_active()) ({ok})", sink)


def main() -> int:
    saved = os.environ.pop(FAULT, None)
    try:
        print("W — the marker")
        marker()
        eg_src, ch_src, sm_src = (p.read_text(encoding="utf-8") for p in (EG_PATH, CH_PATH, SM_PATH))
        print("A — the wiring")
        wiring(eg_src, ch_src)
        adapter(sm_src)
        reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
        check(FAULT in reg, f"A3 {FAULT} is registered in 29-DISABLED-FEATURES-REGISTRY.md")

        print("F — fault arms (each requires the unmutated subject to pass first)")
        base_ok = not failures
        os.environ[FAULT] = "1"
        sink: list = []
        marker(sink)
        os.environ.pop(FAULT, None)
        check(base_ok and bool(sink), f"F1 {FAULT}=1 makes the marker read False during a walk ({len(sink)} W-check(s) red)")
        hm_call = "yield from hunt_walk(_navigate_riding_out(map_enum, tile))"
        ch_call = "yield from hunt_walk(_navigate_riding_out(map_enum, tile, tries=24))"
        sink = []
        wiring(eg_src.replace(hm_call, "yield from _navigate_riding_out(map_enum, tile)", 1), ch_src, sink)
        check(base_ok and hm_call in eg_src and bool(sink), "F2 an unwrapped HM-hunt walk fails A1")
        sink = []
        wiring(eg_src, ch_src.replace(ch_call, "yield from _navigate_riding_out(map_enum, tile, tries=24)", 1), sink)
        check(base_ok and ch_call in ch_src and bool(sink), "F3 an unwrapped counter-hunt walk fails A1")
        sink = []
        wiring(eg_src.replace(hm_call, f"# {hm_call}\n    yield from _navigate_riding_out(map_enum, tile)", 1), ch_src,
               sink)
        check(base_ok and bool(sink), "F4 the wrapped call kept only in a COMMENT still fails A1")
        sink = []
        adapter(sm_src.replace("hunt_walking=bool(_eg.hunt_walk_active()),", "hunt_walking=False,", 1), sink)
        check(base_ok and bool(sink), "F5 an adapter passing hunt_walking=False fails A2")
    finally:
        EG._HUNT_WALK = False
        if saved is not None:
            os.environ[FAULT] = saved

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — every HM/counter hunt walk runs under hunt_walk, the marker is exact, and the fence reads it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
