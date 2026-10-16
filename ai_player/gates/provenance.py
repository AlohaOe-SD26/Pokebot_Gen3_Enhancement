"""TEST SIDE: the CODE line of every live driver's evidence, with a DIGEST of the working tree (AI-player step 2.1).

    py -3.12 ai_player/gates/provenance.py        prints the line for this tree (to compare with an evidence file)
    py -3.12 ai_player/gates/provenance.py --check-evidence
                                                  (the step-3.1 verifier's second round) every evidence file at the top of
                                                  ai_player/evidence/ names THIS tree's digest (exit 0), or which do not
    py -3.12 ai_player/gates/provenance.py --snapshot          (the step-5.1 verifier's second round) keep this tree in
                                                  ai_player/evidence/trees/<digest>.zip (the graded drivers do it themselves)
    py -3.12 ai_player/gates/provenance.py --compare A B       the files two kept trees (digests or zip paths) differ in

WHY (the step-2 review, item 2): the seed-9 replication was run on code that changed afterwards, and its evidence
said only "HEAD 9f859914; ai_player/ has UNCOMMITTED changes": every uncommitted tree printed the SAME line, so
nobody could tell which code a run had tested. Now the line carries a digest of exactly what differs from HEAD:
sha256 over `git diff HEAD --binary` of the scope (staged and unstaged edits) and over every UNTRACKED file in it
(its path and the sha256 of its bytes). Two trees that differ anywhere in the scope give different digests; the
same tree gives the same digest at any time, so a reviewer recomputes it (`main` below) and compares.

WHAT IS LEFT OUT: `ai_player/evidence/` (the drivers write their evidence there DURING a run: it is output, not
the code under test), the Markdown documents (`*.md`: they run nowhere, and the README quotes the evidence, so it
is written AFTER the runs it describes), (build step 5.2) the seed ledger `gates/ledger.json` (`gates/ledger.py`: a
graded sweep writes it at its start and its end, so it is a RECORD of runs, not code), and what `.gitignore` ignores
(`__pycache__`: the purity gate proves every cache file holds exactly its source's code, rule e). Every git call here
only READS (rev-parse, diff, ls-files).

(Build step 5.2, the lessons draft's missing gates) TWO MORE GUARDS LIVE HERE, because every driver already calls this module:
  G6 ONE EVIDENCE READER  `code_digest(text)` is the only reader of an evidence file's code line: `evidence_digests`,
                    `keep_earlier` and `prune_evidence.digest_of` all call it. (The step-5.1 regression: the first read only the
                    first 12 lines and the second the first 4000 characters, so two step-0 files whose COMMAND is a
                    multi-line `-c` script, the code line on line 32, had a digest for one and none for the other.)
  G1 FROZEN-TREE WATCH  `FrozenTree`: the files of the code under test (the `HOOK_SCOPE`, less what the digest leaves out),
                    each by its size, modification time and sha256 at the START; `check()` before each run of a sweep and
                    `seal(verdict)` at the verdict turn the verdict into FAIL "the tree changed mid-run" when a file was
                    changed, added, removed or even rewritten with the same bytes. (The lessons draft, PR-5: rate_step5
                    printed the code line ONCE, at the start, and every run imported the live tree: an edit mid-sweep was
                    graded under the start's digest, silently.) THE BACKSTOP for every other driver: the first `provenance()`
                    of a process starts its watch (`watch`), and `keep_earlier`, which every evidence writer calls just
                    before it writes, checks it; a driver that did not seal its own verdict has its evidence file AMENDED at
                    exit with the FAIL line and its exit code forced to 1 (`_amend_at_exit`).
"""

from __future__ import annotations

import atexit
import hashlib
import os
import re
import subprocess
import sys
import threading
from collections.abc import Iterable, Mapping
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
#: The scope of the step-1 and step-2 drivers, and of step 0's (which also runs the hook).
PACKAGE_SCOPE = ("ai_player",)
HOOK_SCOPE = ("ai_player", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py")
#: (build step 5.2, G2) the seed ledger: a record the graded sweeps write, never the code under test
LEDGER_PATH = "ai_player/gates/ledger.json"
#: Never the code under test: output the drivers write during a run, the documents, and the seed ledger (git pathspecs).
EXCLUDED = (":(exclude)ai_player/evidence", ":(exclude,glob)**/*.md", f":(exclude,glob){LEDGER_PATH}*")


def tree_digest(diff: bytes, untracked: Mapping[str, bytes]) -> str:
    """The digest of a working tree's difference from HEAD: `diff` (`git diff HEAD --binary`) and every untracked
    file (path -> its bytes), in path order. Pure: what the tests check."""
    digest = hashlib.sha256()
    digest.update(b"diff\0" + diff + b"\0untracked\0")
    for path in sorted(untracked):
        digest.update(path.encode("utf-8") + b"\0" + hashlib.sha256(untracked[path]).hexdigest().encode("ascii") + b"\0")
    return digest.hexdigest()


def line(head: str, label: str, diff: bytes, untracked: Mapping[str, bytes], changed: int) -> str:
    """The CODE line of an evidence file (pure)."""
    digest = tree_digest(diff, untracked)[:16]
    if not diff and not untracked:
        return f"HEAD {head}; {label} clean at HEAD (working-tree digest sha256:{digest}, an empty diff)"
    return (f"HEAD {head}; {label} has UNCOMMITTED changes (the code under test is the working tree): working-tree digest "
            f"sha256:{digest} over git diff HEAD ({changed} files, {len(diff)} bytes) and {len(untracked)} untracked files "
            f"(recompute: py -3.12 ai_player/gates/provenance.py)")


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, timeout=60, check=True).stdout


def read_tree(repo: Path, scope: Iterable[str] = PACKAGE_SCOPE) -> tuple[str, bytes, dict[str, bytes], int]:
    """(short HEAD, the diff, the untracked files, how many files the diff touches), by read-only git calls."""
    paths = ["--", *scope, *EXCLUDED]
    head = _git(repo, "rev-parse", "--short", "HEAD").decode().strip()
    diff = _git(repo, "diff", "HEAD", "--binary", *paths)
    changed = len([n for n in _git(repo, "diff", "HEAD", "--name-only", *paths).decode("utf-8", "replace").splitlines() if n])
    names = [n for n in _git(repo, "ls-files", "--others", "--exclude-standard", "-z", *paths).decode("utf-8").split("\0") if n]
    untracked = {name: (repo / name).read_bytes() for name in names if (repo / name).is_file()}
    return head, diff, untracked, changed


def provenance(repo: Path = REPO, scope: Iterable[str] = PACKAGE_SCOPE, label: str = "ai_player/") -> str:
    """The CODE line for the tree at `repo` (never raises: a failure is reported in the line). (Build step 5.2, G1) The
    first call of a process for THIS repository starts the process's frozen-tree watch (`watch`): every driver prints its
    code line at its start, so that is when the tree it grades is fixed."""
    if Path(repo).resolve() == REPO:
        try:
            watch()
        except Exception:  # noqa: BLE001 - a driver must not fail on its record-keeping; the watch is then absent
            pass
    try:
        head, diff, untracked, changed = read_tree(repo, tuple(scope))
        return line(head, label, diff, untracked, changed)
    except Exception as error:  # noqa: BLE001
        return f"unknown ({type(error).__name__}: {error})"


#: (the step-3.1 verifier's second round: "Older evidence files still sit in ai_player/evidence with other digests ... a
#: literal reading of 'every evidence file' would not hold") the evidence folder's TOP LEVEL is the evidence of the tree as
#: it stands; files of earlier trees live in `evidence/archive/<their digest>/` (kept, never rewritten).
EVIDENCE = REPO / "ai_player" / "evidence"
_DIGEST_MARK = "working-tree digest sha256:"
#: (build step 5.2, G6) an evidence file's CODE LINE: at the start of a line, after an optional bracketed tag
#: (`verify_knowledge.py` prints "[VERIFY] code: ..."). A line that only MENTIONS "code:" (indented, as inside a `-c`
#: script a command line quotes, or after other words) is not one.
CODE_LINE = re.compile(r"^(?:\[[A-Z0-9-]+\] *)?code: (?P<rest>.*)$", re.M)
_HEX16 = re.compile(r"(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])")


def code_digest(text: str) -> str | None:
    """(Build step 5.2, G6: THE one reader) The 16-hex working-tree digest the FIRST code line that names one carries, read
    from the WHOLE text (no line or character limit: a long command quoted above the code line pushes it down), or None.
    The digest is the one after "working-tree digest sha256:"; a code line without that mark is read by its first
    16-hex word (an older format), never by a prefix of a longer hex string (a full commit hash)."""
    for found in CODE_LINE.finditer(text):
        rest = found["rest"]
        at = rest.find(_DIGEST_MARK)
        if at >= 0:
            digest = rest[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16]
            if _HEX16.fullmatch(digest):
                return digest
            continue
        word = _HEX16.search(rest)
        if word:
            return word.group(0)
    return None


def line_digest(code: str) -> str | None:
    """The 16-hex digest in a code line as `provenance()` returns it (no "code: " prefix), or None ("unknown (...)")."""
    at = code.find(_DIGEST_MARK)
    digest = code[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16] if at >= 0 else ""
    return digest if _HEX16.fullmatch(digest) else None


def file_digest(path: Path) -> str | None:
    """(G6) The digest an evidence FILE's code line names (`code_digest` over the whole file), or None."""
    return code_digest(path.read_text(encoding="utf-8", errors="replace"))


def evidence_digests(folder: Path = EVIDENCE) -> dict[str, str | None]:
    """Each top-level evidence file -> the 16-hex digest its code line names (`code_digest`: the one reader), or None."""
    return {path.name: file_digest(path) for path in sorted(folder.glob("*.txt"))}


def keep_earlier(path: Path, current: str | None = None, folder: Path = EVIDENCE) -> Path | None:
    """(step 4.1 round 3, the step-4.1 verifier: "Evidence-policy order broken ... `--retire` ran after round 2's graded
    chains had started, so 12 top-level evidence files of the never-committed tree 8b742931d35fa205 ... were overwritten.
    They are unrecoverable") Called by EVERY evidence writer just before it writes `path`: when a file is already there, at
    the top level of the evidence folder, and its code line names ANOTHER tree's digest than `current` (default: this
    tree's), it is MOVED to `archive/<that digest>/` first (a name already taken there gets the next free `.N` suffix), so a
    graded run can no longer write over an earlier tree's evidence, whatever the order of the round's steps. A file of no
    digest goes to `archive/no-digest/`. Returns where it went (None: nothing to keep). `gates/prune_evidence.py` then
    keeps, indexes or packs it by the archive policy."""
    import shutil

    if current is None and folder.resolve() == EVIDENCE.resolve():
        # (build step 5.2, G1) THE BACKSTOP: a real driver's write (tests pass `current`): the tree must not have moved
        # since the process's first code line
        _backstop(path)
    if path.parent.resolve() != folder.resolve() or not path.is_file():
        return None
    if current is None:
        current = line_digest(provenance())
    digest = file_digest(path)
    if digest is not None and digest == current:
        return None
    target_dir = folder / "archive" / (digest or "no-digest")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    suffix = 1
    while target.exists():
        if target.read_bytes() == path.read_bytes():
            path.unlink()
            return target
        target = target_dir / f"{path.stem}.{suffix}{path.suffix}"
        suffix += 1
    shutil.move(str(path), str(target))
    print(f"[EVIDENCE] kept the earlier tree's {path.name} (code {digest or 'no digest'}): {target.relative_to(folder).as_posix()}")
    return target


#: (the step-5.1 verifier's second round: "the claim that dee96b and a883634 differ only in gates and comments cannot be
#: checked independently, because the dee96b tree was not kept") every graded driver KEEPS the tree it ran on: its diff
#: against HEAD and the untracked files the digest covers, in `evidence/trees/<digest>.zip` (`snapshot_tree`; the archive
#: policy's tools never touch this folder); `--compare A B` lists the files two kept trees differ in, each zip's digest
#: recomputed from its own contents first.
TREES = EVIDENCE / "trees"


def snapshot_tree(repo: Path = REPO, folder: Path | None = None) -> Path | None:
    """Keep this tree (`TREES`): `HEAD`, `diff.patch` and `untracked/<path>` in `<digest>.zip`, once per digest. Returns
    the zip's path (None if git could not be read: the run goes on, its code line says why)."""
    import zipfile

    folder = folder or TREES
    try:
        head, diff, untracked, _ = read_tree(repo)
    except Exception:  # noqa: BLE001 - a driver must not fail on its record-keeping
        return None
    target = folder / f"{tree_digest(diff, untracked)[:16]}.zip"
    if target.is_file():
        return target
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as kept:
        kept.writestr("HEAD", head)
        kept.writestr("diff.patch", diff)
        for name, data in sorted(untracked.items()):
            kept.writestr(f"untracked/{name}", data)
    return target


def tree_files(path: Path) -> tuple[str, dict[str, bytes]]:
    """A kept tree: (its digest recomputed from the zip's own contents, path -> its diff section or untracked bytes)."""
    import re
    import zipfile

    with zipfile.ZipFile(path) as kept:
        diff = kept.read("diff.patch")
        untracked = {name[len("untracked/"):]: kept.read(name) for name in kept.namelist() if name.startswith("untracked/")}
    files: dict[str, bytes] = {}
    for section in re.split(rb"(?m)^(?=diff --git )", diff):
        found = re.match(rb"diff --git a/(\S+) b/", section)
        if found:
            files[found.group(1).decode("utf-8", "replace")] = section
    files.update(untracked)
    return tree_digest(diff, untracked)[:16], files


def compare_trees(a: Path, b: Path) -> tuple[str, str, list[str]]:
    """(a's digest, b's digest, the files whose change against HEAD differs between the two kept trees)."""
    digest_a, files_a = tree_files(a)
    digest_b, files_b = tree_files(b)
    return digest_a, digest_b, sorted(n for n in set(files_a) | set(files_b) if files_a.get(n) != files_b.get(n))


def check_evidence(folder: Path = EVIDENCE, repo: Path = REPO) -> tuple[bool, str]:
    """(ok, report): every top-level evidence file names the CURRENT tree's digest."""
    now = line_digest(provenance(repo))
    found = evidence_digests(folder)
    other = {name: digest for name, digest in found.items() if digest != now}
    report = (f"{len(found)} evidence files at the top of {folder.name}/; {len(found) - len(other)} name this tree's digest "
              f"{now}; other: {len(other)} {sorted(other.items())[:12]}")
    return bool(found) and now is not None and not other, report


# ---------------------------------------------------------------------- G1: the frozen-tree watch (build step 5.2)
#: what the watch never counts as the code under test (the digest's own exclusions, as file rules): a folder of these
#: names, a file of these suffixes, and these paths (relative to the repository, POSIX)
_WATCH_SKIP_DIRS = ("__pycache__",)
_WATCH_SKIP_SUFFIXES = (".md", ".pyc", ".pyo")
_WATCH_SKIP_PATHS = ("ai_player/evidence", LEDGER_PATH, LEDGER_PATH + ".lock", LEDGER_PATH + ".tmp")
MID_RUN = "the tree changed mid-run"


class FrozenTree:
    """(Build step 5.2, G1) The files of the code under test as they were when a graded driver STARTED: each file of `scope`
    (folders walked) by its size and modification time, and its sha256. `check(when)` compares the files now (a file whose
    size or time moved is hashed again): one CHANGED, ADDED or REMOVED, or REWRITTEN with its old bytes (an edit undone
    between two checks still ran in the runs between them), is a move, recorded with `when`. `seal(verdict)` checks once
    more and returns ("FAIL", "FROZEN TREE: FAIL - the tree changed mid-run: ...") after any move, else (verdict, the PASS
    line). Thread-safe (a sweep checks from its workers). It needs no git: a scratch copy is watched the same way."""

    def __init__(self, repo: Path = REPO, scope: Iterable[str] = HOOK_SCOPE, explicit: bool = False) -> None:
        self.repo = Path(repo).resolve()
        self.scope = tuple(scope)
        #: True: the driver checks and seals its own verdict (the backstop then never amends its files)
        self.explicit = explicit
        self.sealed = False
        self._lock = threading.Lock()
        self.stats = self._stats()
        self.hashes = {rel: self._sha(rel) for rel in self.stats}
        self.digest = hashlib.sha256("".join(f"{rel}\0{sha}\0" for rel, sha in sorted(self.hashes.items()))
                                     .encode("utf-8")).hexdigest()[:16]
        self.checks = 0
        self.moves: list[str] = []

    def _skipped(self, rel: str) -> bool:
        return (rel.endswith(_WATCH_SKIP_SUFFIXES) or any(rel == p or rel.startswith(p + "/") for p in _WATCH_SKIP_PATHS)
                or any(part in _WATCH_SKIP_DIRS for part in rel.split("/")))

    def _stats(self) -> dict[str, tuple[int, int]]:
        out: dict[str, tuple[int, int]] = {}
        for entry in self.scope:
            top = self.repo / entry
            if top.is_file():
                paths = [top]
            elif top.is_dir():
                paths = []
                for folder, dirs, files in os.walk(top):
                    dirs[:] = sorted(d for d in dirs if d not in _WATCH_SKIP_DIRS)
                    paths += [Path(folder) / name for name in files]
            else:
                continue
            for path in paths:
                rel = path.relative_to(self.repo).as_posix()
                if self._skipped(rel):
                    continue
                try:
                    st = path.stat()
                except OSError:
                    continue
                out[rel] = (st.st_size, st.st_mtime_ns)
        return out

    def _sha(self, rel: str) -> str:
        return hashlib.sha256((self.repo / rel).read_bytes()).hexdigest()

    def check(self, when: str) -> bool:
        """True when every watched file is as it was at the start; else the move is recorded (`moves`) and False."""
        with self._lock:
            self.checks += 1
            now = self._stats()
            added = sorted(set(now) - set(self.stats))
            removed = sorted(set(self.stats) - set(now))
            changed: list[str] = []
            rewritten: list[str] = []
            for rel in sorted(set(now) & set(self.stats)):
                if now[rel] == self.stats[rel]:
                    continue
                try:
                    same = self._sha(rel) == self.hashes[rel]
                except OSError:
                    same = False
                (rewritten if same else changed).append(rel)
            if not (added or removed or changed or rewritten):
                return True
            parts = [f"{len(found)} {what} {found[:6]}" for what, found in (("changed", changed), ("added", added),
                                                                           ("removed", removed),
                                                                           ("rewritten with the start's bytes", rewritten))
                     if found]
            self.moves.append(f"{when}: " + "; ".join(parts))
            return False

    @property
    def moved(self) -> bool:
        return bool(self.moves)

    def seal(self, verdict: str) -> tuple[str, str]:
        """The verdict as it stands after one last check, and the line that says why (written into the evidence)."""
        self.check("at the verdict")
        self.sealed = True
        if self.moves:
            more = f" (and {len(self.moves) - 1} later checks saw it too)" if len(self.moves) > 1 else ""
            return "FAIL", (f"FROZEN TREE: FAIL - {MID_RUN}: {self.moves[0]}{more}. The runs did not all play one tree, so "
                            f"no verdict stands for any (was {verdict})")
        return verdict, (f"FROZEN TREE: PASS - the tree did not change from the start to the verdict ({self.checks} checks of "
                         f"{len(self.stats)} files, files digest {self.digest})")


_WATCHES: dict[Path, FrozenTree] = {}
_WATCH_LOCK = threading.Lock()
_AMEND: list[Path] = []


def watch(repo: Path = REPO, explicit: bool = False) -> FrozenTree:
    """The process's frozen-tree watch of `repo`, started at the first call (`provenance()` makes it for every driver).
    `explicit=True` (a driver that checks and seals its own verdict) marks it so the backstop leaves its files alone."""
    key = Path(repo).resolve()
    with _WATCH_LOCK:
        if key not in _WATCHES:
            _WATCHES[key] = FrozenTree(key)
        if explicit:
            _WATCHES[key].explicit = True
        return _WATCHES[key]


def _backstop(path: Path) -> None:
    """(G1, the backstop) Called by `keep_earlier` before a real evidence write: a watch that saw the tree move turns the
    file into a FAIL at exit (`_amend_at_exit`), unless its driver seals its own verdict."""
    tree = _WATCHES.get(REPO)
    if tree is None or tree.explicit:
        return
    if tree.check(f"before writing {path.name}"):
        return
    print(f"[FROZEN-TREE] {MID_RUN}: {tree.moves[-1]}: {path.name} will be amended with a FAIL line at exit", flush=True)
    with _WATCH_LOCK:
        if not _AMEND:
            atexit.register(_amend_at_exit)
        if path not in _AMEND:
            _AMEND.append(path)


def _amend_at_exit() -> None:
    tree = _WATCHES.get(REPO)
    first = tree.moves[0] if tree is not None and tree.moves else "unknown"
    text = (f"FROZEN TREE: FAIL - {MID_RUN}: {first}. (The provenance backstop: the verdict above does not stand, and the "
            f"driver's exit code is 1.)")
    for path in _AMEND:
        try:
            body = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
            if MID_RUN not in body:
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(("" if body.endswith("\n") or not body else "\n") + text + "\n")
        except OSError:
            pass
    print(text, flush=True)
    try:
        sys.stderr.flush()
    except Exception:  # noqa: BLE001
        pass
    os._exit(1)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "--check-evidence" in sys.argv[1:]:
        ok, report = check_evidence()
        print(f"EVIDENCE: {report} -> {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    if "--snapshot" in sys.argv[1:]:
        print(f"TREE kept: {snapshot_tree()}")
        return 0
    if "--compare" in sys.argv[1:]:
        at = sys.argv.index("--compare")
        a, b = (Path(p) if Path(p).suffix == ".zip" else TREES / f"{p}.zip" for p in sys.argv[at + 1:at + 3])
        digest_a, digest_b, files = compare_trees(a, b)
        print(f"TREES {a.name} (recomputed {digest_a}) and {b.name} (recomputed {digest_b}) differ in {len(files)} "
              f"files: {files}")
        return 0
    print(f"live_step1.py, live_step2.py: {provenance()}")
    print(f"live_step0.py: {provenance(scope=HOOK_SCOPE, label='ai_player/ + hook')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
