"""Which AI-player suites are DUE: their newest evidence was made on another tree than this one (LESSONS PR-2, spec S2-3).

    py -3.12 tools/workflows/regression_due.py [--map tools/workflows/suite_map.json] [--repo .]
        one line per suite, `DUE  <suite>: <why>` or `ok   <suite>: <why>`; exit 0 nothing due, 1 something due,
        2 the map is wrong (an unknown glob, a bad file, an import of ai_player/ no suite covers): an error, never
        silence.

WHY. LESSONS PR-2: "run the suites of the code a step touched; the full regression at each CHAPTER boundary". Knowing
which suites a change touched was memory work, and the step-5.1 script ran the FULL regression because nothing could
say which were stale. `provenance.check_evidence` lists evidence files of another tree, but not WHICH SUITE they
belong to or whether the difference touches that suite's code. `suite_map.json` gives each suite its evidence names and
the files it covers; this tool reads every suite's NEWEST evidence file and decides:
  DUE  never run                    no evidence file matches the suite's names.
  DUE  no provenance                the newest file has no `code:` line with a digest and a `HEAD <commit>`, both read
                                    from the SAME line (PR-12: the digest is read ONLY by `provenance.code_digest`).
  DUE  unknown scope / commit       the code line names a scope label this tool does not know, or a commit that is not
                                    in this repository.
  DUE  uncommitted evidence         the evidence ran on an UNCOMMITTED tree (its digest is not the empty-diff digest),
                                    this tree is not that one, and no KEPT TREE `<evidence_dir>/trees/<digest>.zip`
                                    (`provenance.snapshot_tree`) recomputes to that digest: which files it had changed
                                    is not recoverable from a digest, so the tool cannot clear the suite (it errs
                                    toward running it). With the kept tree, the files its diff touched join the
                                    changed set below (a superset of what differs: never fewer files).
  DUE  changed: <files>             files differ between the evidence commit and this working tree (`git diff
                                    --name-only --no-renames <commit>`, so a MOVE lists both paths, plus untracked
                                    files) and some match the suite's `covers`.
  DUE  unproven: <what>             nothing visibly changed, but the evidence does not RECORD part of what the suite
                                    covers, so "the same tree" cannot be proven: (a) covered files OUTSIDE the scope
                                    the evidence's digest covers (its code line's label: `ai_player/` covers only
                                    ai_player/, `ai_player/ + hook` adds the hook); a file there that was dirty while
                                    the suite ran and was restored afterwards would otherwise read "ok", although other
                                    code was tested; (b) covered files GIT IGNORES (other than bytecode caches), which
                                    no digest, kept tree or diff ever records; (c) covered files git is told NOT TO
                                    LOOK AT (`git update-index --assume-unchanged` / `--skip-worktree`: the `h`/`S`
                                    flags and their lower-case forms in `git ls-files -v`), whose edits neither the
                                    diff nor the digest sees (round 2, 2026-10-21). The remedy for (a) is a driver
                                    that records the wider scope (`covers:<suite>`, below), never a looser rule here.
  ok   same tree / untouched        otherwise. "ok" means NOT STALE; it says nothing about whether that run passed.
THE `covers:<suite>` LABEL (spec S4-1, 2026-10-21). Round 2 measured that 'ok' was UNREACHABLE: every suite of the
shipped map covers files outside both older labels (`ai_player/`, `ai_player/ + hook`: sandbox-pokebot/modules/**,
ai-agent/scoring.py, and for units and revert_safety_gates the documents check_lessons reads, which provenance's digest
leaves out by design), so every suite read DUE `unproven` even on a clean tree with fresh evidence (the CLI still says
so in ONE NOTE line when that is the case). `ai_player/gates/run_regression.py` now writes a code line labelled
`covers:<suite>`, whose digest is `provenance.suite_digest` over EXACTLY that suite's covered files (`suite_covers`:
its `covers` less the map's `exclude`, plus its `reads`); this tool recomputes the same function, so such evidence can
read "ok", and the files it covers are never "outside" it. A `covers:` label naming a suite the map lacks is an
unknown scope (DUE), never a guess.
WHAT A SUITE COVERS. `covers` (code globs, less the map's `exclude`) plus `reads`: the NON-CODE files its driver reads
(MEASURED 2026-10-21 by scanning the files each driver runs: check_lessons reads ai_player/LESSONS.md, the README
tree, 06/07/08, a review note and CLAUDE.md; ledger_check and test_safety_gates read ai_player/gates/ledger.json;
test_goals reads ai-agent/knowledge.py as data). `exclude` never removes a `reads` file: a committed edit that
breaks LESSONS.md must make `units` DUE (round 2; it read "untouched" because `**/*.md` was excluded).
HOW THE DIGEST IS USED, AND WHY NOT ALONE. The digest (`provenance.tree_digest` over `read_tree`, the same two
functions `provenance()` uses, called directly so no frozen-tree watch is started) covers only the UNCOMMITTED
difference of its scope from HEAD. Two clean trees at different commits therefore share one digest, so "the digest
differs" cannot be the test on its own (the spec's wording, read literally, would clear a suite whose code changed in
a COMMIT). The digest is decisive only when the evidence's commit IS HEAD: equal digests (recomputed over the SAME
scope the evidence names) then prove that scope is the tested tree.
PATHS. Every git listing is NUL-separated (`-z`) with `core.quotepath=false`: a quoted path ("ai_player/caf\\303\\251.py")
matches no glob, and was silently read as "untouched". A kept tree's patch headers are parsed here too (quoted, spaced
and renamed paths), because `provenance.tree_files` reads only the plain `a/<path> b/` form.
GIT IGNORES, DECIDED (2026-10-21): bytecode caches (`__pycache__/`, `*.pyc`) are not code under test (the purity gate
proves each cache holds exactly its source's code, which is also why provenance's digest leaves them out); any other
ignored file under a suite's `covers` makes it UNPROVEN (b above); an ignored dependency the AI player needs but that
is not repo code (the emulator binding the installer downloads, the bot's profiles) is listed in the map's
`environment` and printed as a NOTE on every run, so its absence from the decision is said, never silent.
THE MAP IS CHECKED AGAINST THE CODE. Every top-level module ai_player/ imports that resolves to a path of this repo
(an import scan of ai_player/**/*.py, the way its own `sys.path` entries resolve: the importing file's folder, the
repo, the framework folder `sandbox-pokebot/`, `ai-agent/`) must be covered by EVERY suite that runs ai_player code,
or be named in `environment` when git tracks nothing there; otherwise the map is an error (exit 2). WHY: the first map left out `sandbox-pokebot/modules/**`, which ai_player/host/eyes.py imports, so a
committed change there read "untouched". Every git call here only READS (rev-parse, diff, ls-files).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MAP = HERE / "suite_map.json"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
#: (spec S4-1) the glob rule, `suite_covers` and the `covers:<suite>` digest live in provenance, ONE copy for this tool
#: and for the producer that writes that label (ai_player/gates/run_regression.py)
from ai_player.gates.provenance import (CODE_LINE, COVERS_LABEL, HOOK_SCOPE, PACKAGE_SCOPE, code_digest,  # noqa: E402
                                        glob_matches as matches, glob_regex, read_tree, suite_covers, suite_digest,
                                        tree_digest, tree_files)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: The digest of an EMPTY difference from HEAD: what a clean tree's evidence carries (the same for every scope).
CLEAN_DIGEST = tree_digest(b"", {})[:16]
#: The scope each code-line LABEL digests (`provenance.line(head, label, ...)`; live_step0 prints "ai_player/ + hook").
LABEL_SCOPES = {"ai_player/": PACKAGE_SCOPE, "ai_player/ + hook": HOOK_SCOPE}
#: What provenance's digest leaves out of every scope (its EXCLUDED pathspecs), as globs over repo-relative paths.
DIGEST_EXCLUDED = ("ai_player/evidence/**", "**/*.md", "ai_player/gates/ledger.json*")
HEAD_RE = re.compile(r"\bHEAD ([0-9a-f]{7,40})\b")
LABEL_RE = re.compile(r"\bHEAD [0-9a-f]{7,40}; (?P<label>.+?) (?:clean at HEAD|has UNCOMMITTED changes)")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
#: Bytecode caches: never code under test (the purity gate's rule e).
CACHE_RE = re.compile(r"(?:^|/)(?:__pycache__|\.pytest_cache)(?:/|$)|\.py[co]$")
#: The words of an `unproven` reason that say the evidence's recorded scope is narrower than the suite's covers.
RECORDS_ONLY = " records only "
#: (round 2) printed ONCE when every suite is DUE only because its evidence records too narrow a scope.
ALL_UNPROVEN_NOTE = ("NOTE every suite is DUE only as `unproven`: each covers files outside the scope its evidence "
                     "records (`ai_player/` or `ai_player/ + hook`), so 'ok' is unreachable with that evidence. "
                     "Nothing here is known to be stale; the remedy is a producer that records a wider "
                     "scope (`py -3.12 ai_player/gates/run_regression.py --full` writes `covers:<suite>` evidence), "
                     "never a looser rule in this tool.")
#: The folders ai_player's own `sys.path` entries add, in the order a top-level import name is resolved.
IMPORT_ROOTS = ("", "sandbox-pokebot", "ai-agent")


class MapError(ValueError):
    pass


def unwatched_files(repo: Path) -> set[str]:
    """Tracked files git is told not to look at: `git ls-files -v` tags assume-unchanged entries in LOWER case and
    skip-worktree entries `S` (`s` = both). An edit there shows in no `git diff` and no digest."""
    out = set()
    for item in _git(repo, "ls-files", "-v", "-z").split("\0"):
        tag, _, path = item.partition(" ")
        if path and len(tag) == 1 and (tag.islower() or tag == "S"):
            out.add(path)
    return out


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(repo), capture_output=True, timeout=60,
                          check=True, text=True, encoding="utf-8", errors="replace").stdout


def _z(text: str) -> set[str]:
    """The paths of a `-z` (NUL-separated) git listing."""
    return {n for n in text.split("\0") if n}


def repo_files(repo: Path) -> tuple[set[str], set[str], set[str]]:
    """(tracked, untracked, ignored) paths. Ignored folders come collapsed (`--directory`), ending in '/'."""
    tracked = _z(_git(repo, "ls-files", "-z"))
    untracked = _z(_git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    ignored = _z(_git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"))
    return tracked, untracked, ignored


def scope_globs(scope) -> tuple[str, ...]:
    """A provenance scope (folders and files) as globs: a folder entry covers everything under it."""
    return tuple(entry if Path(entry).suffix else entry.rstrip("/") + "/**" for entry in scope)


def in_scope(path: str, globs) -> bool:
    """Is `path` inside the digest of a scope (its globs, less what the digest leaves out)?"""
    return matches(path, globs) and not matches(path, DIGEST_EXCLUDED)


def _import_targets(repo: Path, files: set[str]) -> dict[str, str]:
    """{repo-relative target: the importing file} for every top-level module an ai_player/**/*.py file imports that
    resolves to a path of this repo (a folder -> "<folder>/", a module file -> its path)."""
    std = set(sys.stdlib_module_names)
    targets: dict[str, str] = {}
    for rel in sorted(f for f in files if f.startswith("ai_player/") and f.endswith(".py")
                      and not f.startswith("ai_player/evidence/")):
        try:
            tree = ast.parse((repo / rel).read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
        for name in sorted(names - std - {"ai_player", "__future__"}):
            here = str(Path(rel).parent).replace("\\", "/")
            for root in (here, *IMPORT_ROOTS):
                base = f"{root}/{name}" if root else name
                if (repo / base).is_dir():
                    targets.setdefault(base + "/", rel)
                    break
                if (repo / f"{base}.py").is_file():
                    targets.setdefault(f"{base}.py", rel)
                    break
    return targets


def uncovered_imports(repo: Path, smap: dict, files: set[str]) -> list[str]:
    """Each import target of ai_player/ (outside ai_player/) that a suite RUNNING ai_player code (its covers match an
    ai_player/ file) does not cover and `environment` does not name: a map that under-covers the code is an error,
    never a quiet "untouched". Every such suite must cover every target, because which ai_player module a suite
    reaches at run time is not knowable from its name (revert_safety_gates, mapped to gates/ only, reaches brain/)."""
    environment = smap.get("environment", [])
    ai_files = [f for f in files if f.startswith("ai_player/")]
    runners = {name: s for name, s in smap["suites"].items()
               if any(matches(f, s.get("covers", [])) for f in ai_files)}
    errors = []
    for target, importer in sorted(_import_targets(repo, files).items()):
        if target.startswith("ai_player/"):
            continue
        if target.endswith("/"):
            under = sorted(f for f in files if f.startswith(target) and not CACHE_RE.search(f)
                           and not matches(f, DIGEST_EXCLUDED))
        else:
            under = [target] if target in files else []
        if not under:
            # nothing git tracks: an ignored dependency (the emulator binding); it must be NAMED, never skipped
            if not matches(target, environment):
                errors.append(f"ai_player imports {target} ({importer}) but git tracks nothing there: name it under "
                              f"`environment` or cover it")
            continue
        for name, suite in runners.items():
            missed = [f for f in under if not matches(f, suite.get("covers", []))]
            if missed:
                errors.append(f"suite {name!r} does not cover {target} ({len(missed)} files, e.g. {missed[0]}), which "
                              f"ai_player imports ({importer})")
    return errors


def load_map(path: Path, repo: Path) -> dict:
    """Read and VALIDATE the map: every `covers` glob must match at least one file of the repo (a typo is an error,
    never a suite that silently covers nothing), and every import target of ai_player/ must be covered."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise MapError(f"suite map unreadable: {type(error).__name__}: {error}") from error
    suites = data.get("suites")
    if not isinstance(suites, dict) or not suites:
        raise MapError("suite map has no `suites` object")
    environment = data.get("environment", [])
    if not isinstance(environment, list) or not all(isinstance(g, str) and g for g in environment):
        raise MapError("`environment` must be a list of globs")
    tracked, untracked, _ = repo_files(repo)
    files = tracked | untracked
    excluded = data.get("exclude", [])
    errors = []
    for name, suite in suites.items():
        if not isinstance(suite, dict) or not suite.get("evidence") or not suite.get("covers"):
            errors.append(f"suite {name!r} needs non-empty `evidence` and `covers` lists")
            continue
        for glob in suite["covers"]:
            if not any(glob_regex(glob).match(f) and not matches(f, excluded) for f in files):
                errors.append(f"suite {name!r}: covers glob {glob!r} matches no file of the repository")
        reads = suite.get("reads", [])
        if not isinstance(reads, list) or not all(isinstance(g, str) and g for g in reads):
            errors.append(f"suite {name!r}: `reads` must be a list of globs")
            continue
        for glob in reads:
            # a LITERAL path must exist (a typo is an error); a WILDCARD mirrors the driver's own glob, which may
            # match nothing yet (check_lessons globs ai_player/readme/**/*.md before that folder exists)
            if not any(ch in glob for ch in "*?") and glob not in files:
                errors.append(f"suite {name!r}: reads {glob!r} is not a file of the repository")
    if not errors:
        errors += uncovered_imports(repo, data, files)
    if errors:
        raise MapError("; ".join(errors))
    return data


def newest_evidence(folder: Path, patterns) -> Path | None:
    """The newest top-level evidence file whose NAME matches a pattern (case-insensitive): by the date its name starts
    with, then by modification time (several files share one date)."""
    pats = [glob_regex(p.lower()) for p in patterns]
    hits = [p for p in folder.glob("*.txt") if any(r.match(p.name.lower()) for r in pats)] if folder.is_dir() else []
    if not hits:
        return None

    def key(p: Path):
        m = DATE_RE.match(p.name)
        return (m.group(1) if m else "", p.stat().st_mtime, p.name)
    return max(hits, key=key)


def evidence_provenance(text: str) -> tuple[str | None, str | None, str | None]:
    """(digest, commit, scope label), ALL read from ONE code line: the first one `provenance.code_digest` reads a
    digest from (the same line `code_digest(text)` returns). Reading the commit from another line could pair one
    run's digest with another run's HEAD."""
    for found in CODE_LINE.finditer(text):
        digest = code_digest(found.group(0))
        if digest:
            head, label = HEAD_RE.search(found["rest"]), LABEL_RE.search(found["rest"])
            return digest, head.group(1) if head else None, label["label"] if label else None
    return None, None, None


def evidence_commit(text: str) -> str | None:
    """The `HEAD <commit>` of the code line `code_digest` reads (see evidence_provenance)."""
    return evidence_provenance(text)[1]


_OCTAL = re.compile(rb"\\([0-7]{3}|.)")
_ESCAPES = {b"n": b"\n", b"t": b"\t", b'"': b'"', b"\\": b"\\", b"a": b"\a", b"b": b"\b", b"f": b"\f", b"r": b"\r",
            b"v": b"\v"}


def _unquote(raw: bytes) -> str:
    """A git C-quoted path body (without its quotes) -> the path ("caf\\303\\251" -> "café")."""
    def one(m: re.Match) -> bytes:
        g = m.group(1)
        return bytes([int(g, 8)]) if len(g) == 3 else _ESCAPES.get(g, g)
    return _OCTAL.sub(one, raw).decode("utf-8", "replace")


_QUOTED = rb'"((?:[^"\\]|\\.)*)"'


def patch_names(diff: bytes) -> set[str]:
    """Every path a `git diff` patch touches: git writes a `diff --git a/<p> b/<p>` header for EVERY file (quoted when
    the name has non-ASCII bytes; a name with spaces is not quoted, so the header is split at its middle, where both
    halves are equal), and a rename or copy also writes `rename from <old>` / `rename to <new>` (a pure rename has no
    other line naming them). A rename therefore names both paths."""
    names: set[str] = set()
    for line in diff.split(b"\n"):
        if line.startswith(b"diff --git "):
            rest = line[len(b"diff --git "):]
            quoted = re.findall(_QUOTED, rest)
            if quoted:
                names.update(_unquote(q)[2:] for q in quoted)
            elif rest.startswith(b"a/") and (len(rest) - 5) % 2 == 0:
                half = (len(rest) - 5) // 2
                a, b = rest[2:2 + half], rest[2 + half + 3:]
                if rest[2 + half:2 + half + 3] == b" b/" and a == b:
                    names.add(a.decode("utf-8", "replace"))
        else:
            m = re.match(rb"(?:rename|copy) (?:from|to) (.*)$", line)
            if m:
                q = re.fullmatch(_QUOTED, m.group(1))
                names.add(_unquote(q.group(1)) if q else m.group(1).decode("utf-8", "replace"))
    return names


def kept_tree_files(path: Path, digest: str) -> set[str] | None:
    """The files a kept tree's diff and untracked set touched, or None when the zip is absent, unreadable, or does not
    recompute to `digest` (a kept tree that is not the evidence's tree clears nothing)."""
    if not path.is_file():
        return None
    try:
        recomputed, files = tree_files(path)
        with zipfile.ZipFile(path) as kept:
            names = patch_names(kept.read("diff.patch"))
    except Exception:  # noqa: BLE001 - a damaged zip means "cannot clear", never a crash
        return None
    return set(files) | names if recomputed == digest else None


def _sample(paths, n: int = 3) -> str:
    paths = sorted(paths)
    more = f" (+{len(paths) - n} more)" if len(paths) > n else ""
    return ", ".join(paths[:n]) + more


def assess(repo: Path, smap: dict) -> list[tuple[str, bool, str]]:
    """(suite, due, why) for every suite of the map."""
    head = _git(repo, "rev-parse", "HEAD").strip()
    tracked, untracked_names, ignored = repo_files(repo)
    files = tracked | untracked_names
    unwatched = unwatched_files(repo)
    excluded = smap.get("exclude", [])
    environment = smap.get("environment", [])
    folder = repo / smap.get("evidence_dir", "ai_player/evidence")
    digests: dict[tuple, str] = {}

    def current(scope) -> str:
        if scope not in digests:
            if isinstance(scope, str):
                # (spec S4-1) a `covers:<suite>` label: that suite's own covered files, by provenance's one function
                digests[scope] = suite_digest(repo, smap["suites"][scope], excluded)
            else:
                _, diff, untracked, _ = read_tree(repo, scope)
                digests[scope] = tree_digest(diff, untracked)[:16]
        return digests[scope]

    out = []
    for name, suite in smap["suites"].items():
        ev = newest_evidence(folder, suite["evidence"])
        if ev is None:
            out.append((name, True, "never run (no evidence file matches)"))
            continue
        digest, commit, label = evidence_provenance(ev.read_text(encoding="utf-8", errors="replace"))
        if not digest or not commit:
            out.append((name, True, f"no provenance in {ev.name} (no code line with both a digest and a HEAD)"))
            continue
        scope = LABEL_SCOPES.get(label or "")
        if scope is None and (label or "").startswith(COVERS_LABEL) and label[len(COVERS_LABEL):] in smap["suites"]:
            # (spec S4-1) the digest covers exactly the named suite's covered files (`provenance.suite_covers`)
            scope = label[len(COVERS_LABEL):]
        if scope is None:
            out.append((name, True, f"unknown scope label {label!r} in {ev.name}: which files its digest covers is "
                                    f"not known"))
            continue
        if isinstance(scope, str):
            recorded = smap["suites"][scope]

            def inside(path: str, _suite=recorded) -> bool:
                return suite_covers(path, _suite, excluded)
        else:
            globs = scope_globs(scope)

            def inside(path: str, _globs=globs) -> bool:
                return in_scope(path, _globs)
        try:
            full = _git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").strip()
        except subprocess.CalledProcessError:
            full = ""
        if not full:
            out.append((name, True, f"unknown commit {commit} in {ev.name}"))
            continue
        blind = sorted(f for f in unwatched if suite_covers(f, suite, excluded))
        if blind:
            out.append((name, True, f"unproven: git is told not to look at {len(blind)} covered file(s) "
                                    f"(assume-unchanged / skip-worktree: {_sample(blind, 3)}), so neither the diff "
                                    f"nor the digest sees an edit there"))
            continue
        same_tree = full == head and digest == current(scope)
        changed = _z(_git(repo, "diff", "--name-only", "--no-renames", "-z", full)) | untracked_names
        if digest != CLEAN_DIGEST and not same_tree:
            dirty = kept_tree_files(folder / "trees" / f"{digest}.zip", digest)
            if dirty is None:
                out.append((name, True, f"uncommitted evidence: {ev.name} ran on uncommitted tree {digest} and no kept "
                                        f"tree trees/{digest}.zip recomputes to it; this tree is {head[:8]} + "
                                        f"{current(scope)}"))
                continue
            changed |= dirty
        if same_tree:
            changed = {f for f in changed if not inside(f)}
        hit = sorted(f for f in changed if suite_covers(f, suite, excluded))
        if hit:
            out.append((name, True, f"changed since {ev.name} ({commit}): {_sample(hit, 5)}"))
            continue
        outside = [f for f in files if suite_covers(f, suite, excluded) and not inside(f)]
        hidden = [f for f in ignored if suite_covers(f, suite, excluded) and not CACHE_RE.search(f)
                  and not matches(f, environment)]
        if outside or hidden:
            parts = []
            if outside:
                parts.append(f"{ev.name}{RECORDS_ONLY}{label}, and the suite also covers {len(outside)} files outside "
                             f"it (e.g. {_sample(outside, 2)}), whose state when it ran is not recorded")
            if hidden:
                parts.append(f"git ignores {len(hidden)} covered files ({_sample(hidden, 2)}), which no evidence records")
            out.append((name, True, "unproven: " + "; ".join(parts)))
            continue
        why = "same tree" if same_tree else f"untouched since {commit}"
        out.append((name, False, f"{why} ({ev.name})"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", default=str(MAP))
    ap.add_argument("--repo", default=str(REPO))
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        smap = load_map(Path(args.map), repo)
    except MapError as error:
        print(f"ERROR {error}")
        return 2
    rows = assess(repo, smap)
    for name, due, why in rows:
        print(f"{'DUE ' if due else 'ok  '} {name}: {why}")
    if smap.get("environment"):
        print(f"NOTE not tracked by this tool (environment, ignored by git): {', '.join(smap['environment'])}")
    n = sum(1 for _, due, _ in rows if due)
    unproven = sum(1 for _, due, why in rows if due and why.startswith("unproven:"))
    if rows and all(due and why.startswith("unproven:") and RECORDS_ONLY in why for _, due, why in rows):
        print(ALL_UNPROVEN_NOTE)
    print(f"{n} of {len(rows)} suites due" + (f" ({unproven} of them only unproven)" if unproven else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
