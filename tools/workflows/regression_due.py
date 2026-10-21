"""Which AI-player suites are DUE: their newest evidence was made on another tree than this one (LESSONS PR-2, spec S2-3).

    py -3.12 tools/workflows/regression_due.py [--map tools/workflows/suite_map.json] [--repo .]
        one line per suite, `DUE  <suite>: <why>` or `ok   <suite>: <why>`; exit 0 nothing due, 1 something due,
        2 the map is wrong (an unknown glob, a bad file): an error, never silence.

WHY. LESSONS PR-2: "run the suites of the code a step touched; the full regression at each CHAPTER boundary". Knowing
which suites a change touched was memory work, and the step-5.1 script ran the FULL regression because nothing could
say which were stale. `provenance.check_evidence` lists evidence files of another tree, but not WHICH SUITE they
belong to or whether the difference touches that suite's code. `suite_map.json` gives each suite its evidence names and
the files it covers; this tool reads every suite's NEWEST evidence file and decides:
  DUE  never run                    no evidence file matches the suite's names.
  DUE  no provenance                the newest file has no `code:` line with a digest and a `HEAD <commit>` (PR-12: the
                                    digest is read ONLY by `provenance.code_digest`).
  DUE  unknown commit               the evidence's HEAD is not a commit of this repository.
  DUE  uncommitted evidence         the evidence ran on an UNCOMMITTED tree (its digest is not the empty-diff digest),
                                    this tree is not that one, and no KEPT TREE `<evidence_dir>/trees/<digest>.zip`
                                    (`provenance.snapshot_tree`) recomputes to that digest: which files it had changed
                                    is not recoverable from a digest, so the tool cannot clear the suite (it errs
                                    toward running it). With the kept tree, the files its diff touched join the
                                    changed set below (a superset of what differs: never fewer files).
  DUE  changed: <files>             files differ between the evidence commit and this working tree (`git diff
                                    --name-only <commit>` plus untracked files) and some match the suite's `covers`.
  ok   same tree / untouched        otherwise.
HOW THE DIGEST IS USED, AND WHY NOT ALONE. The digest (`provenance.tree_digest` over `read_tree`, the same two
functions `provenance()` uses, called directly so no frozen-tree watch is started) covers only the UNCOMMITTED
difference of `ai_player/` from HEAD. Two clean trees at different commits therefore share one digest, so "the digest
differs" cannot be the test on its own (the spec's wording, read literally, would clear a suite whose code changed in
a COMMIT). The digest is decisive only when the evidence's commit IS HEAD: equal digests then prove `ai_player/` (less
evidence, Markdown and the seed ledger) is the tested tree, and only covered files OUTSIDE that scope can make the
suite due. Every git call here only READS (rev-parse, diff, ls-files).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MAP = HERE / "suite_map.json"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from ai_player.gates.provenance import CODE_LINE, code_digest, read_tree, tree_digest, tree_files  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: The digest of an EMPTY difference from HEAD: what a clean tree's evidence carries.
CLEAN_DIGEST = tree_digest(b"", {})[:16]
#: The scope `provenance.read_tree` digests (PACKAGE_SCOPE less EXCLUDED), as globs over repo-relative paths.
DIGEST_SCOPE = ("ai_player/**",)
DIGEST_EXCLUDED = ("ai_player/evidence/**", "**/*.md", "ai_player/gates/ledger.json*")
HEAD_RE = re.compile(r"\bHEAD ([0-9a-f]{7,40})\b")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


class MapError(ValueError):
    pass


def glob_regex(glob: str) -> re.Pattern:
    """A repo-relative path glob: `**/` = zero or more folders, `**` = anything, `*` = within one folder, `?` = one
    character. Case-sensitive, like git paths."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


def matches(path: str, globs) -> bool:
    return any(glob_regex(g).match(path) for g in globs)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, timeout=60, check=True,
                          text=True, encoding="utf-8", errors="replace").stdout


def _names(text: str) -> set[str]:
    return {n.strip() for n in text.splitlines() if n.strip()}


def load_map(path: Path, repo: Path) -> dict:
    """Read and VALIDATE the map: every `covers` glob must match at least one file of the repo (a typo is an error,
    never a suite that silently covers nothing)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise MapError(f"suite map unreadable: {type(error).__name__}: {error}") from error
    suites = data.get("suites")
    if not isinstance(suites, dict) or not suites:
        raise MapError("suite map has no `suites` object")
    files = _names(_git(repo, "ls-files")) | _names(_git(repo, "ls-files", "--others", "--exclude-standard"))
    excluded = data.get("exclude", [])
    errors = []
    for name, suite in suites.items():
        if not isinstance(suite, dict) or not suite.get("evidence") or not suite.get("covers"):
            errors.append(f"suite {name!r} needs non-empty `evidence` and `covers` lists")
            continue
        for glob in suite["covers"]:
            if not any(glob_regex(glob).match(f) and not matches(f, excluded) for f in files):
                errors.append(f"suite {name!r}: covers glob {glob!r} matches no file of the repository")
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


def evidence_commit(text: str) -> str | None:
    """The `HEAD <commit>` of the first `code:` line that names one (the line `code_digest` reads)."""
    for found in CODE_LINE.finditer(text):
        m = HEAD_RE.search(found["rest"])
        if m:
            return m.group(1)
    return None


def kept_tree_files(path: Path, digest: str) -> set[str] | None:
    """The files a kept tree's diff and untracked set touched, or None when the zip is absent, unreadable, or does not
    recompute to `digest` (a kept tree that is not the evidence's tree clears nothing)."""
    if not path.is_file():
        return None
    try:
        recomputed, files = tree_files(path)
    except Exception:  # noqa: BLE001 - a damaged zip means "cannot clear", never a crash
        return None
    return set(files) if recomputed == digest else None


def assess(repo: Path, smap: dict) -> list[tuple[str, bool, str]]:
    """(suite, due, why) for every suite of the map."""
    head = _git(repo, "rev-parse", "HEAD").strip()
    _, diff, untracked, _ = read_tree(repo)
    current = tree_digest(diff, untracked)[:16]
    untracked_names = _names(_git(repo, "ls-files", "--others", "--exclude-standard"))
    excluded = smap.get("exclude", [])
    folder = repo / smap.get("evidence_dir", "ai_player/evidence")
    out = []
    for name, suite in smap["suites"].items():
        ev = newest_evidence(folder, suite["evidence"])
        if ev is None:
            out.append((name, True, "never run (no evidence file matches)"))
            continue
        text = ev.read_text(encoding="utf-8", errors="replace")
        digest, commit = code_digest(text), evidence_commit(text)
        if not digest or not commit:
            out.append((name, True, f"no provenance in {ev.name} (no code line with a digest and HEAD)"))
            continue
        try:
            full = _git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").strip()
        except subprocess.CalledProcessError:
            full = ""
        if not full:
            out.append((name, True, f"unknown commit {commit} in {ev.name}"))
            continue
        same_head = full == head
        changed = _names(_git(repo, "diff", "--name-only", full)) | untracked_names
        if digest != CLEAN_DIGEST and not (same_head and digest == current):
            dirty = kept_tree_files(folder / "trees" / f"{digest}.zip", digest)
            if dirty is None:
                out.append((name, True, f"uncommitted evidence: {ev.name} ran on uncommitted tree {digest} and no kept "
                                        f"tree trees/{digest}.zip recomputes to it; this tree is {head[:8]} + {current}"))
                continue
            changed |= dirty
        if same_head and digest == current:
            changed = {f for f in changed if not (matches(f, DIGEST_SCOPE) and not matches(f, DIGEST_EXCLUDED))}
        hit = sorted(f for f in changed if matches(f, suite["covers"]) and not matches(f, excluded))
        if hit:
            more = f" (+{len(hit) - 5} more)" if len(hit) > 5 else ""
            out.append((name, True, f"changed since {ev.name} ({commit}): {', '.join(hit[:5])}{more}"))
        else:
            why = "same tree" if same_head and digest == current else f"untouched since {commit}"
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
    n = sum(1 for _, due, _ in rows if due)
    print(f"{n} of {len(rows)} suites due")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
