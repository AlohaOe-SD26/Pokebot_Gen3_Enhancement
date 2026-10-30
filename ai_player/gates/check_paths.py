"""TEST SIDE (R1 + R2, build spec 2026-10-29 D8; backlog DP1): NO MACHINE PATH IN THE AI'S CODE but the one resolver.

    py -3.12 ai_player/gates/check_paths.py [--package DIR]      exit 0 = PASS, 1 = FAIL, 2 = could not run

WHY: the AI's user data (`memory.jsonl`, `launches.jsonl`) has ONE resolver, `ai_player/paths.py` `AppPaths`, and the
framework folder has one dev default, `host/launcher.py` `resolve_build_root`. A path written into any other string of
the AI's code is a second resolver: it works on this PC and silently points somewhere else on the next one (a deployed
AI has no `sandbox-pokebot` beside it). A rule in prose would not hold (CLAUDE.md rule 6), so this gate refuses, in every
STRING CONSTANT of the package outside those two places:
  * the folder names `sandbox-pokebot` and `Remote Projects` (this repo's layout), and
  * a drive path, `C:/` or `C:\\` (either case).
An f-string's text counts (`f"C:/{x}"` is a path all the same). Docstrings and comments never fire: the syntax tree has no
comments, and a string STATEMENT (a docstring, or any bare string) is skipped, so a module may DESCRIBE the dev default.

SCOPE: the package minus `gates/` (the test side). KNOWN LIMIT, stated so nobody over-reads a PASS: the test side holds
about 20 such lines in 16 files (recon-refute W10: drivers and probes that name the dev build root); they are a later
pass, and a test-side path never reaches a deployed AI. The gate reads text, not values: a path built from pieces
(`"C:" + "/"`) is not seen.

`gates/test_saving.py` PathsTests proves both directions: a planted literal FAILS (in a plain string, an f-string, and in
`host/launcher.py` outside `resolve_build_root`), and the same words in a docstring or a comment PASS.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
#: The test side: not scanned (the known limit in the docstring).
TEST_SIDE = "gates/"
#: The one resolver of user data, exempt whole.
RESOLVER_FILES = frozenset({"paths.py"})
#: (file, function) whose strings are exempt: the framework folder's dev default.
RESOLVER_FUNCTIONS = frozenset({("host/launcher.py", "resolve_build_root")})
#: What a machine path looks like (each with the reason it is refused).
FORBIDDEN: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"sandbox-pokebot", re.IGNORECASE), "this repo's framework folder (the dev build root)"),
    (re.compile(r"remote projects", re.IGNORECASE), "this PC's projects folder"),
    (re.compile(r"(?<![A-Za-z])c:[\\/]", re.IGNORECASE), "a drive path"),
)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """The ids of every string STATEMENT's constant (docstrings and bare strings): never judged."""
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out.add(id(node.value))
    return out


def _exempt_nodes(tree: ast.AST, rel: str) -> set[int]:
    """The ids of every node inside an exempt resolver function of `rel`."""
    out: set[int] = set()
    names = {function for file, function in RESOLVER_FUNCTIONS if file == rel}
    if not names:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            out.update(id(sub) for sub in ast.walk(node))
    return out


def scan_source(rel: str, source: str) -> list[str]:
    """The findings of one file (`rel`: its path under the package, `/`-separated): one line each, `rel:line: why`."""
    if rel in RESOLVER_FILES:
        return []
    tree = ast.parse(source, filename=rel)
    skip = _docstring_nodes(tree) | _exempt_nodes(tree, rel)
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or id(node) in skip:
            continue
        value = node.value
        if isinstance(value, bytes):
            value = value.decode("latin-1")
        if not isinstance(value, str):
            continue
        for pattern, why in FORBIDDEN:
            hit = pattern.search(value)
            if hit:
                findings.append(f"{rel}:{node.lineno}: the string {value[:60]!r} holds {hit.group(0)!r} ({why}); "
                                f"resolve paths through ai_player/paths.py AppPaths or host/launcher.py resolve_build_root")
                break
    return findings


def files_of(package: Path) -> list[tuple[str, Path]]:
    out = []
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package).as_posix()
        if rel.startswith(TEST_SIDE) or "__pycache__" in rel.split("/"):
            continue
        out.append((rel, path))
    return out


def check(package: Path = PACKAGE) -> tuple[bool, list[str], int]:
    """(passed, findings, files scanned)."""
    findings: list[str] = []
    files = files_of(package)
    for rel, path in files:
        findings += scan_source(rel, path.read_bytes().decode("utf-8"))
    return not findings, findings, len(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--package", type=Path, default=PACKAGE, help="the ai_player package to scan (default: this one)")
    args = parser.parse_args(argv)
    try:
        ok, findings, scanned = check(args.package.resolve())
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        print(f"PATHS GATE: COULD NOT RUN ({error})")
        return 2
    for line in findings:
        print(line)
    if scanned == 0:
        print(f"PATHS GATE: COULD NOT RUN (no .py file under {args.package})")
        return 2
    print(f"PATHS GATE: {'PASS' if ok else 'FAIL'} ({scanned} files, {len(findings)} findings)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
