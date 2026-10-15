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
is written AFTER the runs it describes), and what `.gitignore` ignores (`__pycache__`: the purity gate proves every
cache file holds exactly its source's code, rule e). Every git call here only READS (rev-parse, diff, ls-files).
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
#: The scope of the step-1 and step-2 drivers, and of step 0's (which also runs the hook).
PACKAGE_SCOPE = ("ai_player",)
HOOK_SCOPE = ("ai_player", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py")
#: Never the code under test: output the drivers write during a run, and the documents (git pathspecs).
EXCLUDED = (":(exclude)ai_player/evidence", ":(exclude,glob)**/*.md")


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
    """The CODE line for the tree at `repo` (never raises: a failure is reported in the line)."""
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


def evidence_digests(folder: Path = EVIDENCE) -> dict[str, str | None]:
    """Each top-level evidence file -> the 16-hex digest its code line names (within its first 12 lines), or None."""
    out: dict[str, str | None] = {}
    for path in sorted(folder.glob("*.txt")):
        head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:12])
        at = head.find(_DIGEST_MARK)
        out[path.name] = head[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16] if at >= 0 else None
    return out


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

    if path.parent.resolve() != folder.resolve() or not path.is_file():
        return None
    if current is None:
        line_now = provenance()
        at = line_now.find(_DIGEST_MARK)
        current = line_now[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16] if at >= 0 else None
    head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:12])
    at = head.find(_DIGEST_MARK)
    digest = head[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16] if at >= 0 else None
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
    current = provenance(repo)
    at = current.find(_DIGEST_MARK)
    now = current[at + len(_DIGEST_MARK):at + len(_DIGEST_MARK) + 16] if at >= 0 else None
    found = evidence_digests(folder)
    other = {name: digest for name, digest in found.items() if digest != now}
    report = (f"{len(found)} evidence files at the top of {folder.name}/; {len(found) - len(other)} name this tree's digest "
              f"{now}; other: {len(other)} {sorted(other.items())[:12]}")
    return bool(found) and now is not None and not other, report


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
