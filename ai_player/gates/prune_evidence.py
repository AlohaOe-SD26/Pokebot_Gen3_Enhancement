"""TEST SIDE: the EVIDENCE ARCHIVE POLICY (step 4.1, the step-4 review's item 9: "ai_player/evidence/archive is 54 MB. Keep in
archive only the files cited by docs/commit messages plus a one-line index of the rest; delete the uncited intermediate
verification copies (they remain in git history)").

    py -3.12 ai_player/gates/prune_evidence.py                  (a DRY RUN: what would be kept, indexed, deleted)
    py -3.12 ai_player/gates/prune_evidence.py --apply
    py -3.12 ai_player/gates/prune_evidence.py --retire DIGEST [--apply]
    py -3.12 ai_player/gates/prune_evidence.py --reindex        (step 4.1 round 2: every line's size and sha256 from its blob)

THE POLICY (`ai_player/evidence/archive/README.md` states it for readers):
  * `evidence/` (top level) holds the evidence of the CURRENT tree only (`provenance.py --check-evidence`).
  * `evidence/archive/<digest>/` holds ONLY the files of earlier trees that a document or a commit message CITES BY NAME
    (`CITING`: the project's docs, the AI player's README and gates, and `git log`'s messages). A folder named as a whole
    ("archived in evidence/archive/<digest>/") is not a citation of each file in it.
  * Every other file of an earlier tree is listed, one line each, in `evidence/archive/INDEX.md` (its path, the size and
    sha256 OF THE BLOB git holds (step 4.1 round 2: they were the working copy's, CRLF on Windows, which the printed
    `git show` does not print), the commit that holds it and the first line it begins with) and DELETED from the working
    tree: it stays in git
    history (`git show <commit>:<path>`). A file is deleted only when git TRACKS it and it is unchanged against that
    commit (so nothing is lost: an untracked or modified file is kept and said).
  * `--retire DIGEST`: before a round's final runs rewrite the top level, the top-level files of the tree DIGEST (their
    `code:` line names it) are handled the same way: a cited one is MOVED to `archive/DIGEST/`, the rest indexed and deleted;
    (step 4.1 round 2) one git does not hold as it is (a tree never committed) is MOVED there too, kept and said.
  * (step 4.1 round 3, the verifier: "the archive is back to 9.8 MB ... 115 files ... kept wholesale"; "the
    prune_evidence.py gap with the `[VERIFY] code:` prefix is not fixed") an UNCITED file of a tree git does not hold (at the
    top level being retired, or already in the archive) is PACKED into its tree folder's `uncited.zip` (`pack`: every member
    checked byte for byte before the file is deleted), one INDEX line each; a tagged code line ("[VERIFY] code: ...") is
    read. And every evidence writer calls `provenance.keep_earlier` before it writes, so a run started before `--retire`
    archives an earlier tree's file instead of writing over it.
Read-only git only (`ls-files`, `diff --quiet`, `rev-parse`, `log`); the files are moved and deleted by this script."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "ai_player" / "evidence"
ARCHIVE = EVIDENCE / "archive"
INDEX = ARCHIVE / "INDEX.md"
#: The documents whose words count as a CITATION (the archive's own README and INDEX are the policy, not a citation).
CITING = ("PROJECT KNOWLEDGE/**/*.md", "ai_player/README.md", "ai-agent/**/*.md", "ai_player/gates/*.py")
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
#: (step 4.1 round 3, the verifier: "The prune_evidence.py gap with the `[VERIFY] code:` prefix is not fixed") a code line
#: may carry a bracketed tag before it (`verify_knowledge.py` prints "[VERIFY] code: ..."). (Build step 5.2, G6) the
#: pattern and the reader are `provenance`'s, the ONE reader `evidence_digests` and `keep_earlier` use too: this file read
#: the first 4000 characters and that one the first 12 lines, so a file whose command is a multi-line `-c` script (its code
#: line on line 32) had a digest for one and none for the other.
from ai_player.gates.provenance import CODE_LINE, code_digest, file_digest  # noqa: E402,F401
#: (step 4.1 round 3, the verifier: "the archive is back to 9.8 MB ... The 115 files (8.2 MB) of the never-committed tree
#: 8b742931d35fa205 are kept wholesale, against the 'cited by name only' policy") the uncited files of a tree git does not
#: hold (never committed) are PACKED into this one compressed file in their tree's folder, one INDEX line each (their size
#: and sha256, the pack that holds them), instead of kept as files: nothing is lost, and only cited files stay readable
PACK_NAME = "uncited.zip"


def digest_of(path: Path) -> str | None:
    """The 16-hex digest the file's code line names (`provenance.file_digest`, the one reader), or None."""
    return file_digest(path)


def pack(folder: Path, files: list[Path]) -> list[str]:
    """(step 4.1 round 3) Add `files` (all in `folder`) to `folder/uncited.zip` (deflated), check every packed member's bytes
    against its file, then delete the files. Returns their INDEX lines. Nothing is deleted unless every member checks."""
    import zipfile

    target = folder / PACK_NAME
    lines = []
    with zipfile.ZipFile(target, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        names = set(archive.namelist())
        for path in files:
            if path.name in names:
                raise SystemExit(f"{path.name} is already in {target}: not packed twice")
            archive.write(path, arcname=path.name)
    def shown(p: Path) -> str:
        try:
            return p.relative_to(REPO).as_posix()
        except ValueError:
            return p.as_posix()

    with zipfile.ZipFile(target) as archive:
        for path in files:
            data = path.read_bytes()
            if archive.read(path.name) != data:
                raise SystemExit(f"{path.name}: the packed copy differs from the file: nothing deleted")
            lines.append(f"- `{shown(path)}` ({len(data)} B, sha256 {hashlib.sha256(data).hexdigest()[:12]}; packed in "
                         f"`{shown(target)}`, a tree never committed): {first_line(path)}")
    for path in files:
        path.unlink()
    return lines


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace")


def citing_text() -> str:
    parts = []
    for pattern in CITING:
        for path in REPO.glob(pattern):
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
    parts.append(git("log", "--format=%B").stdout)
    return "\n".join(parts)


def cited(path: Path, text: str) -> bool:
    """A file is CITED when its name (or its name without `.txt`) appears in a citing document or a commit message."""
    return path.name in text or (path.suffix == ".txt" and path.stem in text)


def safe_to_delete(path: Path) -> tuple[bool, str]:
    rel = path.relative_to(REPO).as_posix()
    if git("ls-files", "--error-unmatch", rel).returncode != 0:
        return False, "untracked (no copy in git history)"
    if git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        return False, "changed against HEAD (the change is in no commit)"
    return True, ""


def first_line(path: Path) -> str:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            line = handle.readline().strip()
    except OSError:
        return ""
    return line[:160].replace("|", "/")


def blob(commit: str, rel: str) -> bytes | None:
    """(step 4.1 round 2) The file as GIT stores it at `commit` (what `git show <commit>:<path>` prints), or None."""
    done = subprocess.run(["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=str(REPO), capture_output=True)
    return done.stdout if done.returncode == 0 else None


def index_line(path: Path, commit: str) -> str:
    """One INDEX line. (Step 4.1 round 2, the verifier: "INDEX.md's sha256 and size are those of the CRLF working copies,
    but the printed `git show <commit>:<path>` returns the LF blob") the size and sha256 are THE BLOB'S, so the printed
    command's output can be checked against the line as it stands."""
    rel = path.relative_to(REPO).as_posix()
    data = blob(commit, rel)
    if data is None:
        raise SystemExit(f"{rel} is not in git at {commit[:12]}: not indexed")
    return (f"- `{rel}` ({len(data)} B, sha256 {hashlib.sha256(data).hexdigest()[:12]}; `git show {commit[:12]}:{rel}`): "
            f"{first_line(path)}")


INDEX_LINE = re.compile(r"^- `(?P<rel>[^`]+)` \((?P<size>\d+) B, sha256 (?P<sha>[0-9a-f]{12}); `git show (?P<commit>[0-9a-f]+):"
                        r"(?P=rel)`\): (?P<first>.*)$")


def reindex() -> int:
    """(step 4.1 round 2) Every INDEX line's size and sha256 recomputed from the blob its own `git show` names, the line
    otherwise unchanged; a line whose blob is missing aborts (nothing is written)."""
    lines = INDEX.read_text(encoding="utf-8").splitlines()
    out, changed, checked = [], 0, 0
    for line in lines:
        found = INDEX_LINE.match(line)
        if found is None:
            out.append(line)
            continue
        data = blob(found["commit"], found["rel"])
        if data is None:
            raise SystemExit(f"no blob for {found['rel']} at {found['commit']}: the INDEX is left as it was")
        checked += 1
        new = (f"- `{found['rel']}` ({len(data)} B, sha256 {hashlib.sha256(data).hexdigest()[:12]}; "
               f"`git show {found['commit']}:{found['rel']}`): {found['first']}")
        changed += new != line
        out.append(new)
    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"REINDEXED: {checked} lines checked against their blobs, {changed} rewritten (size and sha256 of the blob)")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="move and delete (default: a dry run)")
    parser.add_argument("--retire", help="the digest of the tree whose TOP-LEVEL evidence is retired first")
    parser.add_argument("--reindex", action="store_true", help="recompute every INDEX line's size and sha256 from its blob")
    args = parser.parse_args()
    if args.reindex:
        return reindex()
    head = git("rev-parse", "HEAD").stdout.strip()
    text = citing_text()
    moves: list[tuple[Path, Path]] = []
    candidates: list[Path] = []
    if args.retire:
        for path in sorted(EVIDENCE.glob("*.txt")):
            if digest_of(path) != args.retire:
                continue
            if cited(path, text):
                moves.append((path, ARCHIVE / args.retire / path.name))
            else:
                candidates.append(path)
    candidates += sorted(p for p in ARCHIVE.rglob("*") if p.is_file() and p.name not in ("README.md", "INDEX.md", PACK_NAME))
    keep, delete, held, packs = [], [], [], {}
    for path in candidates:
        if cited(path, text):
            keep.append(path)
            continue
        ok, why = safe_to_delete(path)
        if not ok and args.retire and path.parent == EVIDENCE:
            # (step 4.1 round 2) a retired tree's top-level file git does not hold as it is (untracked, or changed against
            # HEAD: a tree never committed) cannot be indexed and deleted: (round 3) it is PACKED into its tree's folder's
            # `uncited.zip`, so the top level holds the current tree's evidence only (`provenance.py --check-evidence`)
            packs.setdefault(ARCHIVE / args.retire, []).append(path)
            continue
        if not ok and path.parent.parent == ARCHIVE:
            # (round 3) an archived file of a tree git does not hold, cited by nothing: PACKED (one INDEX line), not kept
            packs.setdefault(path.parent, []).append(path)
            continue
        (delete if ok else held).append((path, why))
    size = lambda paths: sum(p.stat().st_size for p in paths)
    print(f"HEAD {head[:12]}; citing documents {CITING} + the commit messages")
    print(f"MOVE to the archive (cited, of the retired tree {args.retire}): {len(moves)} {[p.name for p, _ in moves]}")
    print(f"KEEP (cited): {len(keep)} files, {size(keep)} B: {[p.relative_to(ARCHIVE).as_posix() for p in keep]}")
    print(f"INDEX AND DELETE (uncited, in git at {head[:12]}): {len(delete)} files, {size([p for p, _ in delete])} B")
    print(f"PACK (uncited, of a tree git does not hold): "
          f"{ {folder.name: (len(files), size(files)) for folder, files in packs.items()} }")
    print(f"HELD (uncited but not safe to delete): {len(held)} {[(p.name, why) for p, why in held][:10]}")
    if not args.apply:
        print("DRY RUN: nothing changed (--apply to apply)")
        return 0
    lines = [index_line(path, head) for path, _ in delete]
    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    moves = []
    for folder, files in packs.items():
        folder.mkdir(parents=True, exist_ok=True)
        staged = []
        for path in files:
            # a retired top-level file first goes to its tree's folder, then into the pack
            if path.parent != folder:
                target = folder / path.name
                if target.exists():
                    raise SystemExit(f"{target} exists: not packed")
                shutil.move(str(path), str(target))
                path = target
            staged.append(path)
        lines += pack(folder, staged)
    existing = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else (
        "# The evidence archive's INDEX: files of earlier trees deleted from the working tree (`gates/prune_evidence.py`)\n\n"
        "Each line: the file's path, its size and sha256, the git command that shows it, and its first line. The policy is "
        "in `README.md` beside this file.\n\n")
    INDEX.write_text(existing + "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    for path, _ in delete:
        path.unlink()
    for folder in sorted((p for p in ARCHIVE.iterdir() if p.is_dir()), reverse=True):
        if not any(folder.rglob("*")):
            folder.rmdir()
    print(f"APPLIED: the cited moved, {len(delete)} indexed in {INDEX.relative_to(REPO).as_posix()} and deleted, "
          f"{sum(len(f) for f in packs.values())} packed (one INDEX line each)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
