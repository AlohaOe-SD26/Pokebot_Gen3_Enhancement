"""TEST SIDE (build step 5.2, G3): THE CALL-SITE CENSUS of the AI code changed since a base (default: HEAD).

    py -3.12 ai_player/gates/call_census.py [--since HEAD] [--verbose]     exit 0 = every site covered or waived

WHY (2026-10-14, `08-MISTAKES.md`; the lessons draft, PF-2): two step-5 fixes were DEAD and passed every test of their body:
`battle_rest` was asked only `if self.battle_limit is not None` (G36), and losses were counted on the main path only (G46).
"For every new hook, write the mutant that deletes its CALL, not just its body: a call that is never made passes every
test of the body." Each mutant was written CASE BY CASE, when a reviewer happened to look; nothing listed the hooks a
round added, so a new hook with a body-only mutant passed review. This census lists them:
  1. every FUNCTION of the AI code (`ai_player/` but the test side `gates/`) ADDED or CHANGED since the base (its own code,
     by AST: a comment, a docstring or a nested function's change is not its change), and every CALL ADDED to a changed
     function (a call to an AI function the caller makes more often than at the base: the G46 shape, a hook asked from a
     new place);
  2. for each, its CALL SITES in the AI code (a call by its name, `f(...)`, `obj.f(...)`, `yield from f(...)`; a function
     handed on as a value, `give_way=self.f`, is a reference site; a property's sites are its reads; `__init__`'s are its
     class's calls); a function with NO site is listed as UNCALLED (dead, or called by the framework: say which);
  3. each site must be COVERED by a revert mutant (`MUTANT_SOURCES`, e.g. `revert_step5.MUTANTS`) one of whose edits'
     ANCHOR holds the site and whose edit DELETES the call there (the caller's live calls to it drop: removed, or made dead
     code, `if False:`) or GUARDS it off (the conditions the call runs under change: G36's shape, the rest asked only with
     a battle limit set), or be WAIVED (`census_waivers.json`, with a reason of at least `WAIVER_MIN` characters). A mutant
     that edits only the function's BODY, or only an ARGUMENT of the call, covers no site.
MENTIONS NEVER COUNT: a site is an AST call or reference, so a comment or a docstring naming the function is none; a
mutant whose anchor holds only a comment that names it deletes no call.
The census is a gate on the WORKING TREE against HEAD: it is run before the commit that ends a work item (run_units), and is
empty right after one. `--since <rev>` censuses a range (a report: a whole step's hooks). Read-only git (`diff`,
`ls-files`, `show`).
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "ai_player"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
#: the registries of revert mutants (module in ai_player.gates, its dict of name -> (prediction, what, edits, ...))
#: (R1 + R2, build stage 4) `revert_r1` too: R1's census sites are closed by its mutants (orchestrator ruling 4)
MUTANT_SOURCES = ("revert_step5", "revert_r1",
                  # (boss preparation BP-1, 2026-11-09) its wiring mutants delete the calls the slice added
                  "revert_bossprep",
                  # (P11-1, 2026-11-11) its wiring mutants delete the calls the way through a dark cave added
                  "revert_p11")
WAIVERS = Path(__file__).resolve().parent / "census_waivers.json"
WAIVER_MIN = 20
#: never the AI code: the test side and the run output
SKIP_PARTS = ("gates", "evidence", "__pycache__")
#: an ADDED call to one of these names is not traced to an AI function of the same name: `seen.add(x)` is a set's (the
#: methods of the builtin containers and strings); the function's OWN sites are still listed when it changes
BUILTIN_METHODS = frozenset(name for kind in (dict, list, set, frozenset, str, tuple, bytes, int, float) for name in dir(kind))


# ---------------------------------------------------------------------- functions and their own code
def _owners(tree: ast.AST) -> dict[int, str]:
    owner: dict[int, str] = {}

    def visit(node: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            inner = name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = child.name if name == "<module>" else f"{name}.{child.name}"
            owner[id(child)] = inner
            visit(child, inner)

    visit(tree, "<module>")
    return owner


def functions(source: str) -> dict[str, ast.AST]:
    """Every function of a module by its qualname (Class.method, outer.inner), the way `_owners` names the owner of a
    site. (Build step 5.2, found by the census of 5.2's own code: a function defined inside an `if`, a loop or a `try` of
    another, `GoalRunner._pursue.done`, was named as a site's caller by `_owners` and missing here, so no mutant could
    ever cover its sites: the walk now goes through EVERY statement, as `_owners` does.)"""
    out: dict[str, ast.AST] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{child.name}" if prefix else child.name
                if not isinstance(child, ast.ClassDef):
                    out[name] = child
                visit(child, name)
            else:
                visit(child, prefix)

    visit(_analysis(source)[0], "")
    return out


def own_code(node: ast.AST) -> str:
    """A function's OWN code: its decorators, arguments and body by AST, the docstring and nested functions left out."""
    import copy

    clone = copy.deepcopy(node)
    body = list(clone.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    clone.body = [ast.Pass() if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else s for s in body] \
        or [ast.Pass()]
    for sub in ast.walk(clone):
        if hasattr(sub, "body") and sub is not clone and isinstance(getattr(sub, "body"), list):
            sub.body = [ast.Pass() if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else s
                        for s in sub.body]
    return ast.dump(clone, include_attributes=False)


def _callee_name(qualname: str) -> str:
    parts = qualname.split(".")
    return parts[-2] if parts[-1] == "__init__" and len(parts) >= 2 else parts[-1]


def _is_property(node: ast.AST) -> bool:
    return any((isinstance(d, ast.Name) and d.id in ("property", "cached_property"))
               or (isinstance(d, ast.Attribute) and d.attr in ("setter", "getter")) for d in node.decorator_list)


# ---------------------------------------------------------------------- sites
@dataclass
class Site:
    file: str
    caller: str
    line: int
    kind: str  # call, ref, read
    start: int  # character offsets of the node in its file's text
    end: int

    def key(self) -> str:
        return f"{self.file}:{self.line} in {self.caller} [{self.kind}]"


def _offsets(source: str) -> list[int]:
    out, at = [0], 0
    for line in source.splitlines(keepends=True):
        at += len(line)
        out.append(at)
    return out


_ANALYSES: dict[str, tuple] = {}


def _analysis(source: str) -> tuple:
    """(tree, owners, line offsets, the ids of call functions, the ids of values handed to a call), once per text."""
    found = _ANALYSES.get(source)
    if found is None:
        tree = ast.parse(source)
        funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        handed: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                handed.update(id(a) for a in node.args)
                handed.update(id(k.value) for k in node.keywords)
        found = (tree, _owners(tree), _offsets(source), funcs, handed)
        if len(_ANALYSES) > 400:
            _ANALYSES.clear()
        _ANALYSES[source] = found
    return found


def sites_of(name: str, rel: str, source: str, prop: bool = False) -> list[Site]:
    """Every site in one file where `name` is called (or, `prop`, read), or handed on as a value."""
    if name not in source:
        return []
    tree, owner, starts, funcs, handed = _analysis(source)
    out: list[Site] = []

    def site(node: ast.AST, kind: str) -> Site:
        begin = starts[node.lineno - 1] + node.col_offset
        end = starts[node.end_lineno - 1] + node.end_col_offset
        return Site(rel, owner.get(id(node), "<module>"), node.lineno, kind, begin, end)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == name) or (isinstance(func, ast.Attribute) and func.attr == name):
                out.append(site(node, "call"))
        elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(getattr(node, "ctx", None), ast.Load) \
                and id(node) not in funcs:
            named = node.id if isinstance(node, ast.Name) else node.attr
            if named != name:
                continue
            if id(node) in handed:
                out.append(site(node, "ref"))
            elif prop and isinstance(node, ast.Attribute):
                out.append(site(node, "read"))
    return out


def live_calls(source: str, caller: str) -> list[tuple[str, int, tuple[str, ...]]]:
    """(name, line, guards) of EVERY live call in function `caller` (nested functions are their own callers)."""
    out: list[tuple[str, int, tuple[str, ...]]] = []
    _live_walk(source, caller, lambda node: True, lambda node, guards: out.append((_called(node), node.lineno, guards)))
    return sorted(out, key=lambda c: c[1])


def _called(node: ast.Call) -> str:
    f = node.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""


def live_sites(source: str, caller: str, name: str, kinds: Iterable[str] = ("call",)) -> list[tuple[str, ...]]:
    """The GUARDS of every LIVE call of `name` in function `caller` (each: the conditions it runs under, by AST, outermost
    first). Statically dead code has no live call: an `if False:` body, an `if True:` else, a `while False:` body, an
    operand after a constant False in an `and` (or a constant True in an `or`)."""
    found: list[tuple[str, ...]] = []
    _live_walk(source, caller, lambda node: _called(node) == name, lambda node, guards: found.append(guards))
    return found


def _live_walk(source: str, caller: str, wanted, record) -> None:
    """Walk function `caller`'s LIVE code; `record(call, guards)` for every call `wanted(call)` accepts."""
    target = functions(source).get(caller)
    if target is None:
        return

    def is_call(node: ast.AST) -> bool:
        return isinstance(node, ast.Call) and wanted(node)

    def each(items) -> list:
        return items if isinstance(items, list) else [items]

    def walk(node: ast.AST, guards: tuple[str, ...]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node is not target:
            return
        if isinstance(node, (ast.If, ast.While, ast.IfExp)):
            walk(node.test, guards)
            test = ast.dump(node.test, include_attributes=False)
            if isinstance(node.test, ast.Constant):
                for child in each(node.body if node.test.value else node.orelse):
                    walk(child, guards)
                return
            for child in each(node.body):
                walk(child, (*guards, f"if {test}"))
            for child in each(node.orelse):
                walk(child, (*guards, f"else {test}"))
            return
        if isinstance(node, ast.BoolOp):
            before: list[str] = []
            for value in node.values:
                walk(value, (*guards, f"{type(node.op).__name__} after {before}") if before else guards)
                if isinstance(value, ast.Constant) and bool(value.value) == isinstance(node.op, ast.Or):
                    break
                before.append(ast.dump(value, include_attributes=False))
            return
        if isinstance(node, ast.Try):
            for child in node.body:
                walk(child, (*guards, "try"))
            for child in [*node.handlers, *node.orelse, *node.finalbody]:
                walk(child, (*guards, "try-other"))
            return
        if is_call(node):
            record(node, guards)
        for child in ast.iter_child_nodes(node):
            walk(child, guards)

    walk(target, ())


# ---------------------------------------------------------------------- mutants and waivers
def load_mutants(sources: Iterable[str] = MUTANT_SOURCES) -> dict[str, list[tuple[str, str, str]]]:
    """name -> its edits (file relative to ai_player/, old, new), from every registry."""
    import importlib

    out: dict[str, list[tuple[str, str, str]]] = {}
    for source in sources:
        module = importlib.import_module(f"ai_player.gates.{source}")
        for name, spec in module.MUTANTS.items():
            out[f"{source}:{name}"] = list(spec[2])
    return out


def load_waivers(path: Path = WAIVERS) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("waivers", [])


def covering(site: Site, callee: str, source: str, mutants: dict[str, list[tuple[str, str, str]]]) -> tuple[str, str] | None:
    """(mutant, how) of the first mutant whose anchor holds the site and that DELETES or GUARDS OFF the call there."""
    before = live_sites(source, site.caller, callee, ("call",)) if site.kind == "call" else None
    for name, edits in mutants.items():
        mine = [(old, new) for rel, old, new in edits if rel == site.file]
        if not mine:
            continue
        holds = False
        for old, _ in mine:
            at = source.find(old)
            if at >= 0 and at <= site.start and site.end <= at + len(old):
                holds = True
        if not holds:
            continue
        mutated = source
        for old, new in mine:
            mutated = mutated.replace(old, new, 1)
        try:
            ast.parse(mutated)
        except SyntaxError:
            continue
        if site.kind != "call":
            # a reference or a property read: the mutant must remove the name from the anchor's code
            after = [s for s in sites_of(callee, site.file, mutated, prop=site.kind == "read") if s.caller == site.caller
                     and s.kind == site.kind]
            here = [s for s in sites_of(callee, site.file, source, prop=site.kind == "read") if s.caller == site.caller
                    and s.kind == site.kind]
            if len(after) < len(here):
                return name, "deletes the reference"
            continue
        after = live_sites(mutated, site.caller, callee, ("call",))
        if len(after) < len(before):
            return name, "deletes the call"
        if sorted(after) != sorted(before):
            return name, "guards the call off (the conditions it runs under changed)"
    return None


def waived(callee_key: str, site: Site | None, waivers: list[dict]) -> str | None:
    for waiver in waivers:
        if waiver.get("callee") != callee_key:
            continue
        caller = waiver.get("caller", "*")
        if caller == "*" or (site is not None and caller == f"{site.file}:{site.caller}"):
            reason = str(waiver.get("reason") or "")
            return reason if len(reason.strip()) >= WAIVER_MIN else None
    return None


# ---------------------------------------------------------------------- the census
@dataclass
class Finding:
    callee: str  # file:qualname
    why: str  # added, changed, a new call from <caller>
    sites: list[tuple[str, str]] = field(default_factory=list)  # (site, COVERED by .. | WAIVED: .. | MISSING)

    @property
    def missing(self) -> int:
        return sum(1 for _, status in self.sites if status.startswith(("MISSING", "UNCALLED")))


def census(files: dict[str, str], base: Callable[[str], str | None], changed: Iterable[str],
           mutants: dict[str, list[tuple[str, str, str]]], waivers: list[dict]) -> list[Finding]:
    """`files`: every AI file now (relative path -> text); `base(rel)`: its text at the base (None: new); `changed`: the
    files that differ from the base."""
    defined: dict[str, list[str]] = {}
    for rel, text in files.items():
        for qualname in functions(text):
            defined.setdefault(_callee_name(qualname), []).append(f"{rel}:{qualname}")
    findings: list[Finding] = []
    for rel in sorted(set(changed)):
        if rel not in files:
            continue
        now = functions(files[rel])
        old_text = base(rel)
        old = functions(old_text) if old_text is not None else {}
        for qualname, node in now.items():
            if qualname.split(".")[-1].startswith("__") and qualname.split(".")[-1] != "__init__":
                continue  # called by Python itself, at no site of ours
            status = "added" if qualname not in old else ("changed" if own_code(node) != own_code(old[qualname]) else None)
            if status is not None:
                name = _callee_name(qualname)
                finding = Finding(f"{rel}:{qualname}", status)
                prop = _is_property(node)
                sites = [s for other, text in files.items() for s in sites_of(name, other, text, prop=prop)]
                if not sites:
                    reason = waived(finding.callee, None, waivers)
                    finding.sites.append(("(no site)", f"WAIVED: {reason}" if reason else
                                          "UNCALLED: no call site in the AI code (dead, or called by the framework: "
                                          "waive it with the reason)"))
                for site in sites:
                    finding.sites.append((site.key(), _status(site, name, files[site.file], mutants, finding.callee,
                                                              waivers)))
                findings.append(finding)
            # a call ADDED to this function: a callee of the AI's it now calls more often than at the base
            if qualname in old and status == "changed":
                for callee, count in _calls(node).items():
                    if callee not in defined or callee in BUILTIN_METHODS or count <= _calls(old[qualname]).get(callee, 0):
                        continue
                    finding = Finding(f"{' | '.join(defined[callee][:3])}", f"a call ADDED in {rel}:{qualname}")
                    for site in sites_of(callee, rel, files[rel]):
                        if site.caller == qualname and site.kind == "call":
                            finding.sites.append((site.key(), _status(site, callee, files[rel], mutants,
                                                                      defined[callee][0], waivers)))
                    findings.append(finding)
    return findings


def _calls(node: ast.AST) -> dict[str, int]:
    out: dict[str, int] = {}
    for sub in ast.walk(node):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub is not node:
            continue
        if isinstance(sub, ast.Call):
            f = sub.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name:
                out[name] = out.get(name, 0) + 1
    return out


def _status(site: Site, callee: str, source: str, mutants: dict, callee_key: str, waivers: list[dict]) -> str:
    found = covering(site, callee, source, mutants)
    if found is not None:
        return f"COVERED by {found[0]} ({found[1]})"
    reason = waived(callee_key, site, waivers)
    if reason:
        return f"WAIVED: {reason}"
    return "MISSING: no revert mutant deletes this call (only a body edit, or none), and no waiver"


# ---------------------------------------------------------------------- the working tree against a git base
def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, timeout=120)


def ai_files(package: Path = PACKAGE) -> dict[str, str]:
    out = {}
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package).as_posix()
        if any(part in SKIP_PARTS for part in rel.split("/")):
            continue
        out[rel] = path.read_text(encoding="utf-8")
    return out


def changed_since(rev: str) -> list[str]:
    names = _git("diff", rev, "--name-only", "--", "ai_player").stdout.decode("utf-8", "replace").splitlines()
    names += _git("ls-files", "--others", "--exclude-standard", "--", "ai_player").stdout.decode("utf-8", "replace") \
        .splitlines()
    return sorted({n[len("ai_player/"):] for n in names if n.endswith(".py") and n.startswith("ai_player/")})


def base_of(rev: str) -> Callable[[str], str | None]:
    def read(rel: str) -> str | None:
        done = _git("show", f"{rev}:ai_player/{rel}")
        return done.stdout.decode("utf-8") if done.returncode == 0 else None
    return read


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", default="HEAD")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    files = ai_files()
    changed = [rel for rel in changed_since(args.since) if rel in files]
    findings = census(files, base_of(args.since), changed, load_mutants(), load_waivers())
    missing = sum(f.missing for f in findings)
    sites = sum(len(f.sites) for f in findings)
    for finding in findings:
        bad = finding.missing
        print(f"{'[FAIL]' if bad else '[ok]  '} {finding.callee} ({finding.why}): {len(finding.sites)} sites")
        for site, status in finding.sites:
            if args.verbose or not status.startswith(("COVERED", "WAIVED")):
                print(f"         {site}: {status}")
    print(f"CALL-SITE CENSUS since {args.since}: {len(changed)} AI files changed, {len(findings)} functions or added calls, "
          f"{sites} sites; {missing} MISSING")
    print(f"CALL-SITE CENSUS: {'PASS' if not missing else 'FAIL'}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
