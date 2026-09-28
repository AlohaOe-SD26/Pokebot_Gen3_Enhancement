r"""GATE (static, no ROM) — every item name the story harness looks up is REAL, and `--set-balls` fails LOUDLY
(`#27-setballs`, 2026-09-28).

WHY: commit `4bd5bc4de` (2026-07-22) re-saved `story_harness.py` through a cp1252 round trip, turning "Poké Ball" into
its mojibake. `--set-balls` looked that name up, got a KeyError, caught it, logged `set-balls err`, and the run went ON
with the fixture's own balls, for two months. Every arm that "set" its balls measured the fixture instead. Two checks
close it:
  N1  every string literal passed to `get_item_by_name(...)` or `_ball_count(...)` in `story_harness.py` resolves
      through the real item table (offline, the same lookup the harness makes);
  N2  no line of `story_harness.py` holds cp1252 mojibake (a UTF-8 lead byte read as cp1252: 'Poke-acute' shown as 'Pok' + U+00C3 U+00A9, an em dash as U+00E2 U+20AC U+201D ...);
  L1  the `--set-balls` block's `except` RE-RAISES (a run whose lever did not apply must not continue as that arm).
FAULT ARMS (built in; each must FAIL for its own reason, except F3):
  F1  a mutant with the mojibake literal restored -> N1 and N2 fail;
  F2  a mutant whose set-balls `except` only logs -> L1 fails;
  F3  a COMMENT that mentions the bad name must NOT trip N1 (N1 reads call arguments by AST, never text).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_harness_item_names.py
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.pokemon import get_item_by_name  # noqa: E402

HARNESS = ROOT / "tools" / "story-dev" / "story_harness.py"
LOOKUPS = {"get_item_by_name", "_ball_count"}
MOJIBAKE = re.compile("[\u00c2-\u00f4][\u0080-\u00bf\u20ac\u201a-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u2122"
                      "\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013\u2014\u2018\u2019]")
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _name(func) -> str:
    return func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""


def names_resolve(src: str, sink=None):
    tree = ast.parse(src)
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _name(node.func) in LOOKUPS and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                literals.append((node.lineno, a.value))
    bad = []
    for line, name in literals:
        try:
            get_item_by_name(name)
        except Exception:  # noqa: BLE001 - an unresolvable name is exactly the finding
            bad.append((line, name))
    check(bool(literals) and not bad,
          f"N1 every literal item name looked up resolves ({len(literals)} lookups; unresolvable: {bad})", sink)


def no_mojibake(src: str, sink=None):
    hits = [(i + 1, ln.strip()[:60]) for i, ln in enumerate(src.splitlines()) if MOJIBAKE.search(ln)]
    check(not hits, f"N2 no cp1252 mojibake in the harness (hits: {hits[:3]}{' …' if len(hits) > 3 else ''})", sink)


def setballs_is_loud(src: str, sink=None):
    tree = ast.parse(src)
    handlers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and "set_balls" in ast.unparse(node.test):
            for t in ast.walk(node):
                if isinstance(t, ast.Try):
                    handlers.extend(t.handlers)
    loud = bool(handlers) and all(any(isinstance(s, ast.Raise) for s in ast.walk(h)) for h in handlers)
    check(loud, f"L1 the --set-balls failure path re-raises ({len(handlers)} handler(s))", sink)


def setballs_asserts_readback(src: str, sink=None):
    """L2: the try BODY (not a handler) raises when the save-block read-back differs from what was intended — a write
    that silently returns False must not print a stale pocket beside a claim of success."""
    tree = ast.parse(src)
    body_raises = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and "set_balls" in ast.unparse(node.test):
            for t in ast.walk(node):
                if isinstance(t, ast.Try):
                    for stmt in t.body:
                        body_raises += sum(isinstance(x, ast.Raise) for x in ast.walk(stmt))
    check(body_raises >= 1, f"L2 the --set-balls block raises on a read-back mismatch ({body_raises} raise(s))", sink)


def main() -> int:
    src = HARNESS.read_text(encoding="utf-8")
    names_resolve(src)
    no_mojibake(src)
    setballs_is_loud(src)
    setballs_asserts_readback(src)

    print("F — fault arms (each requires the unmutated harness to pass first)")
    base_ok = not failures
    bad = "Pok\u00c3\u00a9 Ball"  # the exact cp1252 mojibake of "Poke-acute Ball"
    m1 = src.replace('get_item_by_name("Poké Ball")', f'get_item_by_name("{bad}")', 1)
    sink: list = []
    names_resolve(m1, sink)
    no_mojibake(m1, sink)
    check(base_ok and m1 != src and len(sink) == 2, f"F1 the mojibake literal restored fails N1 AND N2 ({len(sink)} failed)")
    # Anchor on the set-balls block's OWN text: a bare "            raise" is also the tail of deeper-indented lines.
    m2 = src.replace('is not that arm")\n            raise\n', 'is not that arm")\n            pass\n', 1)
    sink = []
    setballs_is_loud(m2, sink)
    check(base_ok and m2 != src and bool(sink), "F2 a set-balls except that only logs fails L1")
    m3 = src.replace("\nimport ", f"\n# the old lookup get_item_by_name(\"{bad}\") is gone\nimport ", 1)
    sink = []
    names_resolve(m3, sink)
    check(base_ok and m3 != src and not sink, "F3 a COMMENT naming the bad lookup does not trip N1")
    m4 = src.replace('raise RuntimeError(f"--set-balls read-back', 'log(f"--set-balls read-back', 1)
    sink = []
    setballs_asserts_readback(m4, sink)
    check(base_ok and m4 != src and bool(sink), "F4 a read-back that is only LOGGED (not raised) fails L2")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — every harness item lookup is real, and --set-balls cannot fail silently")
    return 0


if __name__ == "__main__":
    sys.exit(main())
