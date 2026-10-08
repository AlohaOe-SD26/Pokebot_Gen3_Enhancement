"""TEST SIDE: the CODE line of every live driver's evidence, with a DIGEST of the working tree (AI-player step 2.1).

    py -3.12 ai_player/gates/provenance.py        prints the line for this tree (to compare with an evidence file)
    py -3.12 ai_player/gates/provenance.py --check-evidence
                                                  (the step-3.1 verifier's second round) every evidence file at the top of
                                                  ai_player/evidence/ names THIS tree's digest (exit 0), or which do not

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
    print(f"live_step1.py, live_step2.py: {provenance()}")
    print(f"live_step0.py: {provenance(scope=HOOK_SCOPE, label='ai_player/ + hook')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
