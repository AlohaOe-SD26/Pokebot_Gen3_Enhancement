r"""GATE — no live tool script may hardcode the MAIN checkout's path (2026-09-27, `#27-gaterepo`).

WHY: 22 scripts in `tools/story-dev/` hardcoded `C:\Remote Projects\Pokebot_Gen3_Enhancement` as their repo root, and
several put that checkout's `sandbox-pokebot` on `sys.path`. Run from a worktree (the project builds on worktree
branches while a batch runs on `main`), they silently graded and imported `main`, not the branch under test. An
adversarial review caught it only because `probe_citation_ranges.py` passed an inverted range citation the branch had
just introduced. A green gate that is reading another tree is worse than no gate.

  H1  No string constant in the CODE of a top-level `tools/story-dev/*.py` names the main checkout (either slash style,
      case-insensitive). Docstrings are exempt (they may explain history); comments never reach the AST.
      `evidence/` is exempt: it holds frozen historical artefacts.
  H2  Resolve the repo root from the script itself: `Path(__file__).resolve().parents[2]`.
⚠ NOT COVERED (review 2026-09-27; none exist today, verified by a whole-tree grep): the path rebuilt from
pieces (`os.path.join("C:\\", "Remote Projects", ...)`, a `+` split across the separator, bytes literals).
Grep for `Pokebot_Gen3_Enhancement` if a gate ever reads the wrong tree again.
FAULT ARMS (built in): a code literal naming the main checkout MUST be flagged; the same literal in a docstring and in
a comment must NOT be.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_no_hardcoded_repo.py
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
NEEDLE = re.compile(r"remote projects[\\/]+pokebot_gen3_enhancement", re.IGNORECASE)
failures: list = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def offenders(src: str) -> list:
    """Line numbers of code string constants naming the main checkout; docstrings excluded."""
    tree = ast.parse(src)
    doc_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None) or []
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                doc_ids.add(id(body[0].value))
    return [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_ids
            and NEEDLE.search(n.value)]


def main() -> int:
    print("=" * 92)
    print("GATE — no live tool script hardcodes the main checkout's path")
    print("=" * 92)
    bad = {}
    scanned = 0
    for f in sorted(HERE.glob("*.py")):
        scanned += 1
        try:
            hits = offenders(f.read_text(encoding="utf-8-sig"))
        except SyntaxError as error:
            bad[f.name] = [f"unparseable: {error}"]
            continue
        if hits:
            bad[f.name] = hits
    check(scanned > 100, f"H1 scanned {scanned} top-level scripts (a tiny count means the glob is wrong)")
    check(not bad, f"H1 no code literal names the main checkout {bad if bad else ''}")

    print("\n== FAULT ARMS ==")
    # ‼ The fault inputs are ASSEMBLED from parts, so this file holds no single literal naming the path (else H1 flags
    # the gate itself).
    rp, pb = "Remote Projects", "Pokebot_Gen3_Enhancement"
    bs = chr(92)
    check(offenders(f'ROOT = Path(r"C:{bs}{rp}{bs}{pb}")' + chr(10)) == [1], "FAULT a code literal (backslashes) IS flagged")
    check(offenders(f'ROOT = "C:/{rp}/{pb}/x"' + chr(10)) == [1], "FAULT a code literal (forward slashes) IS flagged")
    check(offenders(f'"""Doc: this used to hardcode C:/{rp}/{pb}."""' + chr(10) + "X = 1" + chr(10)) == [],
          "FAULT the same path in a module docstring is NOT flagged")
    check(offenders(f"X = 1  # was C:{bs}{rp}{bs}{pb}" + chr(10)) == [], "FAULT the same path in a comment is NOT flagged")
    check(offenders("def f():" + chr(10) + f'    """see C:/{rp}/{pb}"""' + chr(10) + "    return 1" + chr(10)) == [],
          "FAULT a function docstring is NOT flagged")

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
