"""UNIT PROOFS of the evidence folder's keeping rules (step 4.1 round 3). Test side.

    py -3.12 ai_player/gates/test_evidence.py        (exit 0 = every test passed)

WHY (the step-4.1 verifier's second round): "Evidence-policy order broken ... `--retire` ran after round 2's graded chains
had started, so 12 top-level evidence files of the never-committed tree 8b742931d35fa205 ... were overwritten. They are
unrecoverable"; "The prune_evidence.py gap with the `[VERIFY] code:` prefix is not fixed"; "the archive is back to 9.8 MB
... 115 files ... kept wholesale". Each rule below is a test with its FAULT half (the rule switched off, the test fails):

  KeepEarlierTests  `provenance.keep_earlier`, called by every evidence writer just before it writes: a top-level file of
                    ANOTHER tree is moved to `archive/<its digest>/` first (never written over), a name taken there gets a
                    suffix, an identical copy is not kept twice, a file of THIS tree is left to be rewritten, a file outside
                    the folder's top level is not touched. FAULT (the step-4.1 round-2 order: no keep): the earlier bytes lost.
  CodeLineTests     `prune_evidence.CODE_LINE` reads a code line with a bracketed tag ("[VERIFY] code: ...", as
                    `verify_knowledge.py` prints it). FAULT (round 2's `^code:`): no digest found.
  PackTests         `prune_evidence.pack`: uncited files of a tree git does not hold are packed into one `uncited.zip`, every
                    member checked byte for byte before a file is deleted, one INDEX line each with its size and sha256.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import prune_evidence  # noqa: E402
from ai_player.gates.provenance import keep_earlier  # noqa: E402

OLD, NEW = "8b742931d35fa205", "d272da770b442dc4"


def evidence(digest: str | None, body: str = "the run's lines") -> str:
    code = (f"code: HEAD 7a70a445; ai_player/ has UNCOMMITTED changes (the code under test is the working tree): "
            f"working-tree digest sha256:{digest} over git diff HEAD") if digest else "code: HEAD 7a70a445 (no digest)"
    return f"AI PLAYER - A LIVE PROOF\ndate: 2026-10-09\n{code}\n{body}\n"


class Folder(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ai_test_evidence_"))
        self.folder = self.root / "evidence"
        self.folder.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class KeepEarlierTests(Folder):
    def test_an_earlier_trees_file_is_moved_to_its_archive_folder_before_it_is_written_over(self) -> None:
        path = self.folder / "2026-10-09-step1-E1.txt"
        path.write_text(evidence(OLD, "the earlier run"), encoding="utf-8")
        kept = keep_earlier(path, NEW, self.folder)
        self.assertEqual(kept, self.folder / "archive" / OLD / path.name)
        self.assertFalse(path.exists())
        self.assertIn("the earlier run", kept.read_text(encoding="utf-8"))
        path.write_text(evidence(NEW, "the new run"), encoding="utf-8")  # the writer's own write
        self.assertIn("the earlier run", kept.read_text(encoding="utf-8"), "the earlier bytes survive the new write")

    def test_fault_without_the_keep_the_earlier_bytes_are_lost(self) -> None:
        path = self.folder / "2026-10-09-step1-E1.txt"
        path.write_text(evidence(OLD, "the earlier run"), encoding="utf-8")
        path.write_text(evidence(NEW, "the new run"), encoding="utf-8")  # round 2's order: written over, no keep
        found = [p for p in self.folder.rglob("*.txt") if "the earlier run" in p.read_text(encoding="utf-8")]
        self.assertEqual(found, [])

    def test_this_trees_file_is_left_to_be_rewritten_and_outside_files_are_not_touched(self) -> None:
        mine = self.folder / "a.txt"
        mine.write_text(evidence(NEW), encoding="utf-8")
        self.assertIsNone(keep_earlier(mine, NEW, self.folder))
        self.assertTrue(mine.exists())
        elsewhere = self.root / "b.txt"
        elsewhere.write_text(evidence(OLD), encoding="utf-8")
        self.assertIsNone(keep_earlier(elsewhere, NEW, self.folder))
        self.assertTrue(elsewhere.exists())
        self.assertIsNone(keep_earlier(self.folder / "missing.txt", NEW, self.folder))

    def test_a_taken_name_gets_a_suffix_and_an_identical_copy_is_not_kept_twice(self) -> None:
        path = self.folder / "x.txt"
        path.write_text(evidence(OLD, "one"), encoding="utf-8")
        first = keep_earlier(path, NEW, self.folder)
        path.write_text(evidence(OLD, "two"), encoding="utf-8")
        second = keep_earlier(path, NEW, self.folder)
        self.assertEqual(second.name, "x.1.txt")
        path.write_text(evidence(OLD, "two"), encoding="utf-8")
        self.assertEqual(keep_earlier(path, NEW, self.folder), second)
        self.assertEqual(sorted(p.name for p in (self.folder / "archive" / OLD).iterdir()), ["x.1.txt", "x.txt"])
        self.assertEqual(first.read_text(encoding="utf-8"), evidence(OLD, "one"))

    def test_a_file_of_no_digest_goes_to_no_digest(self) -> None:
        path = self.folder / "y.txt"
        path.write_text(evidence(None), encoding="utf-8")
        self.assertEqual(keep_earlier(path, NEW, self.folder), self.folder / "archive" / "no-digest" / "y.txt")


class CodeLineTests(unittest.TestCase):
    def test_a_tagged_code_line_names_its_digest(self) -> None:
        text = f"[VERIFY] code: HEAD 7a70a445; ... working-tree digest sha256:{NEW} over git diff HEAD\n[VERIFY] more\n"
        self.assertEqual(prune_evidence.CODE_LINE.search(text).group(1), NEW)
        self.assertEqual(prune_evidence.CODE_LINE.search(evidence(OLD)).group(1), OLD)

    def test_fault_round_2s_pattern_misses_the_tag(self) -> None:
        import re

        text = f"[VERIFY] code: HEAD 7a70a445; ... working-tree digest sha256:{NEW} over git diff HEAD\n"
        self.assertIsNone(re.compile(r"^code: .*?([0-9a-f]{16})", re.M).search(text))


class PackTests(Folder):
    def test_uncited_files_are_packed_checked_and_indexed(self) -> None:
        tree = self.folder / "archive" / OLD
        tree.mkdir(parents=True)
        files = []
        for name in ("a.txt", "b.txt"):
            path = tree / name
            path.write_text(evidence(OLD, f"run {name}"), encoding="utf-8")
            files.append(path)
        digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:12] for p in files}
        lines = prune_evidence.pack(tree, files)
        self.assertFalse(any(p.exists() for p in files))
        with zipfile.ZipFile(tree / prune_evidence.PACK_NAME) as archive:
            self.assertEqual(sorted(archive.namelist()), ["a.txt", "b.txt"])
            self.assertIn("run a.txt", archive.read("a.txt").decode("utf-8"))
        for line, name in zip(lines, ("a.txt", "b.txt")):
            self.assertIn(digests[name], line)
            self.assertIn("packed in", line)

    def test_a_name_already_packed_is_not_packed_twice_and_nothing_is_deleted(self) -> None:
        tree = self.folder / "archive" / OLD
        tree.mkdir(parents=True)
        path = tree / "a.txt"
        path.write_text(evidence(OLD), encoding="utf-8")
        prune_evidence.pack(tree, [path])
        path.write_text(evidence(OLD, "again"), encoding="utf-8")
        with self.assertRaises(SystemExit):
            prune_evidence.pack(tree, [path])
        self.assertTrue(path.exists())


class SnapshotTests(Folder):
    """(build step 5.1, the verifier's second round: "the dee96b tree was not kept", so "two trees differ only in gates and
    comments" could not be checked) `provenance.snapshot_tree` keeps the tree a graded driver ran on; its digest is
    recomputed from the kept zip's own contents and two kept trees are compared file by file."""

    def test_this_tree_is_kept_and_its_digest_recomputed_from_the_zip(self) -> None:
        from ai_player.gates.provenance import compare_trees, provenance, snapshot_tree, tree_files

        kept = snapshot_tree(folder=self.folder)
        self.assertIsNotNone(kept)
        digest, files = tree_files(kept)
        self.assertEqual(kept.stem, digest)
        self.assertIn(f"sha256:{digest}", provenance())  # the very digest every evidence file of this tree names
        self.assertEqual(snapshot_tree(folder=self.folder), kept)  # once per digest
        self.assertEqual(compare_trees(kept, kept)[2], [])
        # FAULT half: one changed byte in a kept file is a different tree (its recomputed digest is not its name), and the
        # comparison names the file that changed
        changed = self.folder / "changed.zip"
        with zipfile.ZipFile(kept) as source, zipfile.ZipFile(changed, "w") as target:
            for name in source.namelist():
                data = source.read(name)
                target.writestr(name, data + b"\n# one more line\n" if name.startswith("untracked/") else data)
        other, _ = tree_files(changed)
        untracked = [name for name in files if not files[name].startswith(b"diff --git ")]
        if untracked:
            self.assertNotEqual(other, digest)
            self.assertEqual(compare_trees(kept, changed)[2], sorted(untracked))


if __name__ == "__main__":
    unittest.main(verbosity=2)
