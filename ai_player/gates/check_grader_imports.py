"""TEST SIDE (build step 5.3, stage A1-2: the G-3 rule): the step-5 GRADERS take no value from the AI's code.

    py -3.12 ai_player/gates/check_grader_imports.py      exit 0 = PASS, 1 = FAIL, 2 = could not run

WHY (B1, the Goodhart gate; `2026-10-22-B1-grader-recon.md` §4): `rate_step5.py` imported the AI's ERRANDS, ERRAND_KINDS,
ASIDE and MAX_LOSSES, and `live_step5.py` its GENERIC_BUSY and its personality chooser, so an edit of the code under test
moved the grader's own bounds and expectations, with no change to anything registered. A rule on DIRECT imports is not
enough (critic Q4): `live_step5` reached the AI's ERRANDS through `rate_step5.train_steps_min`, a gates function whose body
imported it. So this gate walks VALUES, not files:
  * every import ANYWHERE in a grader (module level or inside a function) is judged;
  * an `ai_player` module is allowed only by the ALLOW-LIST (`host.launcher`, the `options.ENV_*` names) or when it is a
    `gates` module; any other (`brain`, `personality`, `mode`, `hands`, `eyes`, `world`, ...) is a breach;
  * a name taken from a `gates` module is followed INTO that module: the name's own definition (its body, its default
    values, the module-level names and imports it reads, and theirs, transitively, across gates modules) must reach no
    breach. A gates module that imports the AI for its OWN use (`play_harness.play` runs the AI) does not taint a name
    the grader takes from it that never reads that import (`play_harness.steps_counted`).
A mention in a comment, a docstring or a string is no import (the walk reads the syntax tree; rule 6: a gate with false
positives teaches people to bypass it). `run`/`--json` print every chain from a grader to the breach.
"""

from __future__ import annotations

import ast
import fnmatch
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
#: the graders this rule protects
#: (2026-11-05) live_chain, the New Game chain held-out (USER RULING 55), walked on every lane run (its spec section 9)
GRADERS = ("ai_player.gates.rate_step5", "ai_player.gates.live_step5", "ai_player.gates.live_chain")
#: the package whose modules are walked into (a name taken from one is followed to its definition)
WALKED = "ai_player.gates"
#: (module, name pattern) a grader may take from the AI's package without a walk: the launcher's plumbing and the
#: options' environment-variable NAMES (strings that name a setting, never a value the AI computes)
ALLOW = (("ai_player.host.launcher", "*"), ("ai_player.host", "launcher"), ("ai_player.options", "ENV_*"))


@dataclass
class Definitions:
    """One module's syntax, as the walk needs it: its top-level names -> the nodes that define them; its module-level
    imports name -> (module, attribute or None for a module object)."""
    path: Path
    tree: ast.Module
    defs: dict[str, list[ast.AST]] = field(default_factory=dict)
    imports: dict[str, tuple[str, str | None]] = field(default_factory=dict)


def _module_path(root: Path, module: str) -> Path | None:
    base = root.joinpath(*module.split("."))
    for path in (base.with_suffix(".py"), base / "__init__.py"):
        if path.is_file():
            return path
    return None


def _resolve_from(node: ast.ImportFrom, module: str) -> str:
    """The absolute module of a `from X import ...` (relative imports resolved against `module`, a module's own name)."""
    if not node.level:
        return node.module or ""
    parts = module.split(".")[:-node.level]
    return ".".join(parts + ([node.module] if node.module else []))


def _imports_in(nodes, module: str) -> dict[str, tuple[str, str | None]]:
    """Every name an import among `nodes` (walked deep) binds -> (module, attribute or None)."""
    out: dict[str, tuple[str, str | None]] = {}
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.ImportFrom):
                source = _resolve_from(sub, module)
                for alias in sub.names:
                    out[alias.asname or alias.name] = (source, alias.name)
            elif isinstance(sub, ast.Import):
                for alias in sub.names:
                    if alias.asname:
                        out[alias.asname] = (alias.name, None)
                    else:
                        out[alias.name.split(".")[0]] = (alias.name, None)
    return out


def _loaded_names(nodes) -> set[str]:
    """Every name a node reads (`Name` in a load context, and the base of every attribute chain)."""
    names: set[str] = set()
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Load, ast.Del)):
                names.add(sub.id)
    return names


def _definitions(root: Path, module: str, cache: dict) -> Definitions | None:
    if module in cache:
        return cache[module]
    path = _module_path(root, module)
    if path is None:
        cache[module] = None
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = Definitions(path, tree)
    for node in tree.body:
        targets: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            targets = [node.name]
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                targets += [n.id for n in ast.walk(target) if isinstance(n, ast.Name)]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            found.imports.update(_imports_in([node], module))
            continue
        for name in targets:
            found.defs.setdefault(name, []).append(node)
    # an import inside an `if`/`try` at module level binds a module-level name too
    for node in tree.body:
        if isinstance(node, (ast.If, ast.Try, ast.With)):
            found.imports.update(_imports_in([node], module))
    cache[module] = found
    return found


def allowed(module: str, name: str | None) -> bool:
    """On the allow-list: a launcher module, or an `options.ENV_*` name."""
    return any(module == mod and fnmatch.fnmatchcase(name or "", pattern) for mod, pattern in ALLOW) \
        or any(module == mod and pattern == "*" for mod, pattern in ALLOW)


def classify(module: str, name: str | None) -> str:
    """'walk' (a gates module: follow the name), 'ok' (outside the AI's package, or allow-listed), or 'breach'."""
    if module == WALKED or module.startswith(WALKED + "."):
        return "walk"
    if module != "ai_player" and not module.startswith("ai_player."):
        return "ok"
    if module == "ai_player" and name is not None and name != "gates":
        # `from ai_player import X`: X is a module of the package
        return classify(f"ai_player.{name}", None)
    if module == "ai_player" and name == "gates":
        return "walk"
    return "ok" if allowed(module, name) else "breach"


class Walk:
    """The value walk of one tree (`root`): `breaches_of(module, name)` -> the chains from that name to the AI's code."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.cache: dict[str, Definitions | None] = {}
        self.memo: dict[tuple[str, str | None], list[list[str]]] = {}
        self.active: set[tuple[str, str | None]] = set()

    def _import_target(self, module: str, name: str | None) -> tuple[str, str | None]:
        """`from ai_player.gates import live_step2` binds a MODULE: the walk follows it whole."""
        if name is not None and _module_path(self.root, f"{module}.{name}") is not None:
            return f"{module}.{name}", None
        return module, name

    def through_import(self, source: tuple[str, str | None], label: str) -> list[list[str]]:
        module, name = source
        kind = classify(module, name)
        where = f"{module}.{name}" if name else module
        if kind == "ok":
            return []
        if kind == "breach":
            return [[f"{label} <- {where}"]]
        module, name = self._import_target(module, name)
        return [[label] + chain for chain in self.breaches_of(module, name)]

    def breaches_of(self, module: str, name: str | None) -> list[list[str]]:
        """The chains by which `module.name` (`name` None: the whole module) reaches a breach."""
        key = (module, name)
        if key in self.memo:
            return self.memo[key]
        if key in self.active:
            return []  # a cycle: its breaches are found on the first visit
        self.active.add(key)
        try:
            found = self._breaches(module, name)
        finally:
            self.active.discard(key)
        self.memo[key] = found
        return found

    def _breaches(self, module: str, name: str | None) -> list[list[str]]:
        defs = _definitions(self.root, module, self.cache)
        if defs is None:
            return []
        label = f"{module}.{name}" if name else module
        if name is None:
            nodes = list(defs.tree.body)
        elif name in defs.defs:
            nodes = defs.defs[name]
        elif name in defs.imports:
            return self.through_import(defs.imports[name], label)
        else:
            return []  # a name the module does not define (a dynamic attribute): nothing to follow
        out: list[list[str]] = []
        local = _imports_in(nodes, module)
        for bound, source in sorted(local.items()):
            out += self.through_import(source, f"{label} (imports {bound})")
        for used in sorted(_loaded_names(nodes) - set(local)):
            if name is not None and used == name:
                continue
            if used in defs.defs and name is not None:
                out += [[label] + chain for chain in self.breaches_of(module, used)]
            elif used in defs.imports:
                out += self.through_import(defs.imports[used], f"{label} (reads {used})")
        return out


def scan(root: Path = REPO, graders: tuple[str, ...] = GRADERS) -> list[str]:
    """Every chain by which a grader reaches the AI's code, as text ("" list: PASS). A grader is judged WHOLE: every import
    in it, at any depth; a gates module it takes a name from is followed by that name only."""
    walk = Walk(root)
    problems: list[str] = []
    for grader in graders:
        defs = _definitions(root, grader, walk.cache)
        if defs is None:
            problems.append(f"{grader}: no such module under {root}")
            continue
        for bound, (module, name) in sorted(_imports_in([defs.tree], grader).items()):
            for chain in walk.through_import((module, name), f"{grader} (imports {bound})"):
                problems.append(" -> ".join(chain))
    return sorted(set(problems))


def report(problems: list[str]) -> str:
    """The gate's one line (and, on a FAIL, one indented line per chain)."""
    if not problems:
        return (f"GRADER IMPORTS: PASS (G-3: {', '.join(g.rsplit('.', 1)[1] for g in GRADERS)} take no value from the AI's "
                f"code, directly or through a gates module)")
    return "GRADER IMPORTS: FAIL (G-3)\n" + "\n".join(f"  {p}" for p in problems)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        problems = scan()
    except (OSError, SyntaxError) as error:
        print(f"GRADER IMPORTS: could not run ({error})")
        return 2
    print(report(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
