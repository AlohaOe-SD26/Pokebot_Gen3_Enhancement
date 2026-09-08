# -*- coding: utf-8 -*-
"""GATE — a function must not LOAD a name that nothing in its scope chain BINDS.

⛔⛔ WHY THIS EXISTS. On 2026-09-08 the same mistake shipped THREE times in one session, each time
costing an emulator run to find, because a `NameError` only fires on the branch nobody drives:

    `os`      — `story_harness.py` binds it as `_os` at module scope. A new function wrote `os.environ`.
                My check was `grep -c "^import os"` -> 2 -> "available". WRONG.
    `console` — `victory_road.py` imports it FUNCTION-LOCALLY (`:865`), never at module scope. A new
                function wrote `console.print(...)`.
                My check was `grep -c "console.print"` -> 3 -> "available". WRONG.

⭐ THE LESSON THE GATE ENCODES: **a usage grep cannot see WHERE a name is BOUND.** Both checks
counted appearances of the name and concluded availability; neither could distinguish "bound at
module scope" from "bound inside some other function". Only scope analysis can.

WHAT IT CHECKS. For every function, the set of names it LOADS must be covered by:
builtins + module-level bindings + its own bindings (params, assignments, imports, except-as,
comprehension targets, nested defs) + **every enclosing function's bindings** (closures are legal).

⛔ WHAT IT DELIBERATELY DOES NOT DO — and says so rather than guessing:
A module containing `from x import *` is UNANALYSABLE statically (the star's contents are unknown
without importing, and importing a bot module here would need a ROM). Such files are SKIPPED and
COUNTED, never silently passed. 5 files in `sandbox-pokebot` are in that state today, all GUI.
‼ This is why the gate reports "analysed N, skipped M": a gate that quietly ignores what it cannot
read is indistinguishable from one that found nothing wrong.

⭐ MEASURED BEFORE SHIPPING, because a noisy gate teaches people to bypass it (CLAUDE.md rule 6):
    3,271 functions across 201 files -> **0 findings**.
Three earlier drafts were NOT shipped: v1 flagged 32 (missed lambda args), v2 flagged 8 (missed
closures). Only the version with a real scope chain reached zero.

Bare invocation scans both forks. Exit 0 = PASS.
"""
import ast
import builtins
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent

#: Names Python provides that are not `builtins` members.
_MODULE_DUNDERS = {"__file__", "__name__", "__doc__", "__package__", "__builtins__", "__spec__"}


def _has_star_import(tree: ast.AST) -> bool:
    return any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names)
               for n in ast.walk(tree))


def _bindings(node: ast.AST) -> "set[str]":
    """Every name `node` BINDS, at any depth. Deliberately over-inclusive: a false NEGATIVE costs
    nothing here, a false POSITIVE costs the gate its credibility."""
    out: "set[str]" = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.arg):                      # incl. lambda parameters
            out.add(sub.arg)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                out.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
            out.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(sub.name)
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            out.add(sub.name)
        elif isinstance(sub, (ast.Global, ast.Nonlocal)):
            out.update(sub.names)
    return out


def _module_bindings(tree: ast.AST) -> "set[str]":
    """Names bound at MODULE level — ⛔ NOT descending into function or class bodies.

    ‼‼ THIS DISTINCTION IS THE WHOLE GATE, and the first draft got it wrong. Using the generic
    `_bindings(tree)` here walks the entire file, so an import written INSIDE some other function
    counts as module scope — which is exactly `victory_road.py`'s shape (`from modules.console
    import console` at `:865`, inside a function). With that bug the gate reported 0 findings over
    6,540 functions **and would have missed the very NameError it was built for**. Its own self-test
    arm caught it.
    ⇒ descend through `if TYPE_CHECKING:` / `try: import ...` blocks (those DO bind at module level)
    but stop at every `def` and `class`.
    """
    out: "set[str]" = set()

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(child.name)          # the NAME binds; its BODY does not
                continue
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    out.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                out.add(child.id)
            elif isinstance(child, ast.ExceptHandler) and child.name:
                out.add(child.name)
            walk(child)

    walk(tree)
    return out


def unresolved(tree: ast.AST) -> "dict[str, list[str]]":
    """{function_name: [names it loads that nothing in scope binds]}."""
    module_scope = set(dir(builtins)) | _MODULE_DUNDERS | _module_bindings(tree)
    found: "dict[str, list[str]]" = {}

    def walk(node: ast.AST, enclosing: "set[str]") -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = enclosing | _bindings(child)      # ⭐ closures inherit enclosing bindings
                missing = sorted({n.id for n in ast.walk(child)
                                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                                  and n.id not in scope})
                if missing:
                    found[child.name] = missing
                walk(child, scope)
            elif isinstance(child, ast.ClassDef):
                walk(child, enclosing | _bindings(child))
            else:
                walk(child, enclosing)

    walk(tree, module_scope)
    return found


def self_test() -> "list[str]":
    """⛔ A GUARD NEVER SEEN TO FAIL IS NOT A GUARD. Both real bugs, and both legal shapes."""
    import tempfile
    failures = []
    ARMS = [
        ("FAULT: console used but only bound in ANOTHER function",
         "def other():\n    from modules.console import console\n"
         "def f():\n    console.print('x')\n", True),
        ("FAULT: module binds `_os`, function writes `os`",
         "import os as _os\ndef f():\n    return os.environ\n", True),
        ("NO-FIRE: a legitimate function-local import",
         "def f():\n    from modules.console import console\n    console.print('x')\n", False),
        ("NO-FIRE: a legitimate CLOSURE over an enclosing variable",
         "def outer(v):\n    def inner():\n        return v\n    return inner\n", False),
        ("NO-FIRE: lambda parameters and comprehension targets",
         "def f(d):\n    return sorted(d, key=lambda kv: kv[1]) + [c for c in d]\n", False),
    ]
    tmp = pathlib.Path(tempfile.gettempdir()) / "_probe_name_resolution_arm.py"
    for label, src, should_fire in ARMS:
        tmp.write_text(src, encoding="utf-8")
        hit = bool(unresolved(ast.parse(tmp.read_text(encoding="utf-8"))))
        if hit != should_fire:
            failures.append(f"{'DID NOT FIRE' if should_fire else 'FALSE POSITIVE'}: {label}")
    return failures


def main() -> int:
    print("=" * 92)
    print("GATE — no function may LOAD a name nothing in its scope chain BINDS")
    print("=" * 92)

    arm_failures = self_test()
    print(f"\n  self-test: {'PASS — 5 arms (2 fault, 3 no-fire)' if not arm_failures else 'FAILED'}")
    for f in arm_failures:
        print(f"    ⛔ {f}")

    scanned = skipped = functions = 0
    hits: "list[str]" = []
    for fork in ("sandbox-pokebot", "custom-pokebot"):
        base = ROOT / fork
        if not base.exists():
            continue
        for path in sorted(list((base / "modules").rglob("*.py"))
                           + list((base / "plugins").rglob("*.py"))):
            if "__pycache__" in str(path):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            if _has_star_import(tree):
                skipped += 1
                continue
            scanned += 1
            functions += sum(1 for n in ast.walk(tree)
                             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            for fn, names in unresolved(tree).items():
                hits.append(f"{path.relative_to(ROOT)}::{fn} -> {names[:6]}")

    print(f"  scanned  : {scanned} files, {functions} functions")
    print(f"  skipped  : {skipped} file(s) containing `from x import *` — statically unanalysable,")
    print( "             reported rather than silently passed")
    print(f"  findings : {len(hits)}")
    for h in hits[:25]:
        print(f"    {h}")
    if len(hits) > 25:
        print(f"    ... and {len(hits) - 25} more")

    print("\n" + "-" * 92)
    if arm_failures or hits:
        print("FAILED — a NameError only fires on the branch nobody drives; fix the binding.")
        print("=" * 92)
        return 1
    print("✅ PASS — every loaded name is bound somewhere in its scope chain, and all 5 arms behave.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
