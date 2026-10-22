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
                    `verify_knowledge.py` prints it). FAULT (round 2's `^code:`): no digest found. (Build step 5.2, G6: the
                    reader is `provenance.code_digest`, the one every checker uses; `test_safety_gates.py` G6 tests it on
                    a file whose command is a multi-line `-c` script.)
  PackTests         `prune_evidence.pack`: uncited files of a tree git does not hold are packed into one `uncited.zip`, every
                    member checked byte for byte before a file is deleted, one INDEX line each with its size and sha256.
  IdentityTests     (#28-evidence-identity) on a THROW-AWAY git repository (`ThrowawayRepo`), never the real evidence folder:
                    evidence identity is the code UNDER TEST (the label's files at the line's HEAD + the digest). (1) a clean
                    re-run after a commit that changed a scoped file archives the earlier commit's file; (2) a commit of only
                    unscoped files (.md, the evidence folder, outside ai_player/) leaves it current; (3) one diff on two
                    commits with different scoped files is two trees; (4) a HEAD git does not have is never the same tree;
                    (5) check_evidence calls (1)'s file not current. FAULT halves: `digest_only` (every commit's scope reads
                    the same, the rule before the fix) and a scope without its exclusions.
  RetireTests       `prune_evidence --retire` by archive key `<digest>-<HEAD>`; a bare clean digest is refused.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
#: the HEAD the planted code lines name, and (#28-evidence-identity) the archive folder an OLD file of it goes to
PLANT_HEAD = "7a70a445"
OLD_KEY = f"{OLD}-{PLANT_HEAD}"


def evidence(digest: str | None, body: str = "the run's lines", head: str = PLANT_HEAD) -> str:
    code = (f"code: HEAD {head}; ai_player/ has UNCOMMITTED changes (the code under test is the working tree): "
            f"working-tree digest sha256:{digest} over git diff HEAD") if digest else f"code: HEAD {head} (no digest)"
    return f"AI PLAYER - A LIVE PROOF\ndate: 2026-10-09\n{code}\n{body}\n"


def this_head() -> str:
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO), capture_output=True, check=True,
                          text=True).stdout.strip()


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
        self.assertEqual(kept, self.folder / "archive" / OLD_KEY / path.name)
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
        # (#28-evidence-identity) THIS tree's file: this HEAD's ai_player/ files and this digest
        mine.write_text(evidence(NEW, head=this_head()), encoding="utf-8")
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
        self.assertEqual(sorted(p.name for p in (self.folder / "archive" / OLD_KEY).iterdir()), ["x.1.txt", "x.txt"])
        self.assertEqual(first.read_text(encoding="utf-8"), evidence(OLD, "one"))

    def test_a_file_of_no_digest_goes_to_no_digest(self) -> None:
        path = self.folder / "y.txt"
        path.write_text(evidence(None), encoding="utf-8")
        self.assertEqual(keep_earlier(path, NEW, self.folder), self.folder / "archive" / "no-digest" / "y.txt")


class ThrowawayRepo(unittest.TestCase):
    """(#28-evidence-identity) A THROW-AWAY git repository with a synthetic scope, never the real evidence folder:
    `ai_player/mode.py` and `ai_player/lib.py` (in every label's scope), `ai_player/notes.md` and a committed
    `ai_player/evidence/keep.json` (in the folder, but left out of every digest), `other/tool.py` (outside `ai_player/`),
    and `tools/workflows/suite_map.json` with one suite, `units`, covering `ai_player/**` (for `covers:units` lines)."""

    SUITE = {"covers": ["ai_player/**"], "evidence": ["*-regression-units.txt"]}
    MAP_EXCLUDE = ["ai_player/evidence/**", "**/*.md", "ai_player/gates/ledger.json*"]

    def setUp(self) -> None:
        from ai_player.gates import provenance

        provenance._SCOPE_HASHES.clear()
        self.repo = Path(tempfile.mkdtemp(prefix="ai_test_identity_"))
        self.ev = self.repo / "ai_player" / "evidence"
        self.git("init", "-q")
        self.commit("A", **{"ai_player/mode.py": "MODE = 1\n", "ai_player/lib.py": "LIB = 1\n",
                            "ai_player/notes.md": "notes\n", "ai_player/evidence/keep.json": "{}\n",
                            "other/tool.py": "TOOL = 1\n",
                            "tools/workflows/suite_map.json": json.dumps(
                                {"exclude": self.MAP_EXCLUDE, "suites": {"units": self.SUITE}}) + "\n"})

    def tearDown(self) -> None:
        shutil.rmtree(self.repo, ignore_errors=True)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                               "-c", "core.autocrlf=false", *args], cwd=str(self.repo), capture_output=True, check=True,
                              text=True).stdout.strip()

    def put(self, **files: str) -> None:
        for rel, body in files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")

    def commit(self, message: str, **files: str) -> str:
        """Write `files` (keyword = repo path), commit exactly them, return the new short HEAD."""
        self.put(**files)
        self.git("add", "--", *files)
        self.git("commit", "-q", "-m", message, "--", *files)
        return self.head()

    def head(self) -> str:
        return self.git("rev-parse", "--short", "HEAD")

    def evidence(self, name: str, code: str | None = None) -> Path:
        """A top-level evidence file whose code line is `code` (default: what `provenance()` prints for this tree)."""
        from ai_player.gates.provenance import provenance

        self.ev.mkdir(parents=True, exist_ok=True)
        path = self.ev / name
        path.write_text(f"AI PLAYER - A PLANTED RUN\ncode: {code or provenance(self.repo)}\nVERDICT: PASS\n",
                        encoding="utf-8")
        return path

    def keep(self, path: Path, **kw) -> Path | None:
        return keep_earlier(path, folder=self.ev, repo=self.repo, **kw)

    @staticmethod
    def digest_only():
        """THE FAULT: identity reduced to (label, digest), as `keep_earlier` and `check_evidence` decided before
        #28-evidence-identity: every commit's scope reads the same."""
        from unittest import mock

        from ai_player.gates import provenance

        return mock.patch.object(provenance, "scope_hash", lambda repo, head, label: "every commit the same")


class IdentityTests(ThrowawayRepo):
    """(#28-evidence-identity) Evidence identity = the code UNDER TEST (the label's files at the code line's HEAD + the
    digest), not the diff from HEAD. Each numbered test is the coordinator's case, with its FAULT and CONTROL."""

    # (1) the measured bug: a clean-tree file of commit A, a commit B that changes a scoped file, a clean re-run on B
    def test_1_control_a_clean_rerun_after_a_scoped_commit_archives_the_earlier_commits_file(self) -> None:
        from ai_player.gates.provenance import CLEAN_DIGEST, code_digest, line_digest, provenance

        path = self.evidence("2026-10-21-regression-units.txt")
        a = self.head()
        b = self.commit("B", **{"ai_player/mode.py": "MODE = 2\n"})
        # the precondition that made the bug: the two clean trees carry ONE digest
        self.assertEqual(code_digest(path.read_text(encoding="utf-8")), line_digest(provenance(self.repo)))
        self.assertEqual(code_digest(path.read_text(encoding="utf-8")), CLEAN_DIGEST)
        kept = self.keep(path)
        self.assertEqual(kept, self.ev / "archive" / f"{CLEAN_DIGEST}-{a}" / path.name, "A's evidence was not archived")
        # and the next commit's clean evidence goes to ANOTHER folder: two clean trees never share one
        again = self.evidence(path.name)
        self.commit("C", **{"ai_player/lib.py": "LIB = 3\n"})
        self.assertEqual(self.keep(again), self.ev / "archive" / f"{CLEAN_DIGEST}-{b}" / path.name)

    def test_1_fault_digest_only_writes_over_the_earlier_commits_file(self) -> None:
        path = self.evidence("2026-10-21-regression-units.txt")
        self.commit("B", **{"ai_player/mode.py": "MODE = 2\n"})
        with self.digest_only():
            self.assertIsNone(self.keep(path), "the digest-only rule called commit A's evidence this tree's")
        self.assertTrue(path.is_file())  # left at the top level, where the writer's next write goes over it

    # (2) a commit that changes ONLY unscoped files (a .md, the evidence folder, a file outside ai_player/)
    def test_2_control_a_docs_only_commit_leaves_the_evidence_current(self) -> None:
        from ai_player.gates.provenance import check_evidence

        path = self.evidence("2026-10-21-step1-A.txt")
        a = self.head()
        b = self.commit("B: docs, evidence and outside files only", **{
            "ai_player/notes.md": "more notes\n", "ai_player/evidence/keep.json": '{"x": 1}\n',
            "other/tool.py": "TOOL = 2\n"})
        self.assertNotEqual(a, b)
        self.assertIsNone(self.keep(path), "a docs-only commit made the evidence another tree's")
        self.assertTrue(path.is_file())
        ok, report = check_evidence(self.ev, self.repo)
        self.assertTrue(ok, report)

    def test_2_fault_a_scope_without_the_exclusions_calls_a_docs_commit_another_tree(self) -> None:
        from unittest import mock

        from ai_player.gates import provenance

        path = self.evidence("2026-10-21-step1-A.txt")
        self.commit("B", **{"ai_player/notes.md": "more notes\n"})
        with mock.patch.object(provenance, "EXCLUDED_GLOBS", ()):
            self.assertIsNotNone(self.keep(path), "the .md is excluded even with no exclusions: the test is vacuous")

    # (3) a dirty tree: the same uncommitted diff on two commits whose scoped files differ
    def test_3_control_the_same_diff_on_another_scoped_commit_is_another_tree(self) -> None:
        from ai_player.gates.provenance import code_digest

        self.put(**{"ai_player/mode.py": "MODE = 1\nEDIT = True\n"})  # uncommitted
        path = self.evidence("2026-10-21-step1-B.txt")
        a, dirty = self.head(), code_digest(path.read_text(encoding="utf-8"))
        self.assertIsNone(self.keep(path), "a re-run of the SAME dirty tree must leave its file")
        self.commit("B: lib only", **{"ai_player/lib.py": "LIB = 2\n"})
        again = self.evidence("probe.txt")
        self.assertEqual(code_digest(again.read_text(encoding="utf-8")), dirty, "precondition: the same diff digest")
        again.unlink()
        self.assertEqual(self.keep(path), self.ev / "archive" / f"{dirty}-{a}" / path.name)

    def test_3_fault_digest_only_calls_the_two_dirty_trees_one(self) -> None:
        self.put(**{"ai_player/mode.py": "MODE = 1\nEDIT = True\n"})
        path = self.evidence("2026-10-21-step1-B.txt")
        self.commit("B: lib only", **{"ai_player/lib.py": "LIB = 2\n"})
        with self.digest_only():
            self.assertIsNone(self.keep(path))

    # (4) a code line whose HEAD git does not have
    def test_4_an_unknown_commit_is_never_the_same_tree(self) -> None:
        from ai_player.gates.provenance import CLEAN_DIGEST, check_evidence, code_identity

        line = f"HEAD deadbee1; ai_player/ clean at HEAD (working-tree digest sha256:{CLEAN_DIGEST}, an empty diff)"
        self.assertIsNone(code_identity(f"code: {line}", self.repo), "an unknown commit was given an identity")
        path = self.evidence("2026-10-21-step1-C.txt", line)
        self.assertFalse(check_evidence(self.ev, self.repo)[0])
        self.assertEqual(self.keep(path), self.ev / "archive" / f"{CLEAN_DIGEST}-deadbee1" / path.name)

    def test_4_control_the_same_line_with_a_known_head_is_the_same_tree(self) -> None:
        from ai_player.gates.provenance import CLEAN_DIGEST, check_evidence, code_digest, line_digest, provenance

        line = f"HEAD {self.head()}; ai_player/ clean at HEAD (working-tree digest sha256:{CLEAN_DIGEST}, an empty diff)"
        path = self.evidence("2026-10-21-step1-C.txt", line)
        self.assertTrue(check_evidence(self.ev, self.repo)[0])
        self.assertIsNone(self.keep(path))
        # FAULT: the digest alone calls the unknown commit's line this tree's
        unknown = line.replace(f"HEAD {self.head()}", "HEAD deadbee1")
        self.assertEqual(code_digest(f"code: {unknown}"), line_digest(provenance(self.repo)))

    # (6) the verify's surviving mutant V1: the per-process cache keyed WITHOUT the label
    def test_6_two_labels_at_one_head_keep_their_own_scope_hash(self) -> None:
        """check_evidence asks for `ai_player/` and `ai_player/ + hook` at the SAME HEAD in one process, so the cache
        must be keyed by the label: otherwise the second label is handed the first one's scope hash. FAULT: the hook
        label reads the package label's hash (mutant V1). CONTROL: asked alone, with a cold cache, it reads the same."""
        from ai_player.gates import provenance

        head = self.commit("hook", **{"sandbox-pokebot/plugins/custom_modes/ai_player_mode.py": "HOOK = 1\n"})
        package = provenance.scope_hash(self.repo, head, "ai_player/")
        hook = provenance.scope_hash(self.repo, head, "ai_player/ + hook")
        self.assertIsNotNone(package)
        self.assertIsNotNone(hook)
        self.assertNotEqual(package, hook, "the hook label was handed the package label's cached scope hash")
        provenance._SCOPE_HASHES.clear()
        self.assertEqual(provenance.scope_hash(self.repo, head, "ai_player/ + hook"), hook)

    # (7) the verify's surviving mutant V13: a covers:<suite> label must honour suite_map's `exclude`
    def test_7_a_covers_label_leaves_out_what_suite_map_excludes(self) -> None:
        """`covers:units` covers `ai_player/**` minus suite_map's `exclude` (Markdown, the evidence folder, the
        ledger). FAULT: with the exclusions ignored (mutant V13) a commit that changes only `ai_player/notes.md` gives
        another scope hash. CONTROL: a commit that changes `ai_player/lib.py` does."""
        from ai_player.gates import provenance

        before = self.head()
        docs = self.commit("docs", **{"ai_player/notes.md": "notes, edited\n"})
        code = self.commit("code", **{"ai_player/lib.py": "LIB = 2\n"})
        first = provenance.scope_hash(self.repo, before, "covers:units")
        self.assertIsNotNone(first)
        self.assertEqual(provenance.scope_hash(self.repo, docs, "covers:units"), first,
                         "a Markdown-only commit changed covers:units' scope hash: suite_map's exclude was ignored")
        self.assertNotEqual(provenance.scope_hash(self.repo, code, "covers:units"), first)
        # the same rule for the DIGEST half (`label_digest`): an uncommitted Markdown edit leaves covers:units' digest
        # alone (FAULT: mutant V13, the exclusions dropped there), an uncommitted scoped edit (CONTROL) moves it
        clean = provenance.label_digest(self.repo, "covers:units")
        self.put(**{"ai_player/notes.md": "an uncommitted docs edit\n"})
        self.assertEqual(provenance.label_digest(self.repo, "covers:units"), clean,
                         "an uncommitted Markdown edit moved covers:units' digest: suite_map's exclude was ignored")
        self.put(**{"ai_player/lib.py": "LIB = 3\n"})
        self.assertNotEqual(provenance.label_digest(self.repo, "covers:units"), clean)

    # (5) check_evidence on (1)'s shape
    def test_5_control_check_evidence_calls_a_scoped_commits_clean_evidence_not_current(self) -> None:
        from ai_player.gates.provenance import check_evidence

        self.evidence("2026-10-21-regression-units.txt")
        ok, report = check_evidence(self.ev, self.repo)
        self.assertTrue(ok, report)
        self.commit("B", **{"ai_player/mode.py": "MODE = 2\n"})
        ok, report = check_evidence(self.ev, self.repo)
        self.assertFalse(ok, report)
        self.assertIn("2026-10-21-regression-units.txt", report)
        self.assertIn("another tree", report)

    def test_5_fault_digest_only_calls_it_current(self) -> None:
        from ai_player.gates.provenance import check_evidence

        self.evidence("2026-10-21-regression-units.txt")
        self.commit("B", **{"ai_player/mode.py": "MODE = 2\n"})
        with self.digest_only():
            self.assertTrue(check_evidence(self.ev, self.repo)[0])

    # the covers:<suite> label, as run_regression writes it and passes it (`code=`)
    def test_covers_label_by_the_writers_own_line(self) -> None:
        from ai_player.gates.provenance import suite_line

        def run_line() -> str:
            return suite_line(self.repo, "units", self.SUITE, self.MAP_EXCLUDE)

        path = self.evidence("2026-10-21-regression-units.txt", run_line())
        a = self.head()  # the commit the file's code line names
        self.assertIn("covers:units clean at HEAD", path.read_text(encoding="utf-8"))
        self.assertIsNone(self.keep(path, code=run_line()), "the same tree's re-run archived its own file")
        self.commit("B: docs", **{"ai_player/notes.md": "x\n"})
        self.assertIsNone(self.keep(path, code=run_line()), "a docs-only commit made covers:units evidence stale")
        self.commit("C", **{"ai_player/lib.py": "LIB = 9\n"})
        self.assertIsNotNone(self.keep(path, code=run_line()))
        self.assertTrue(any(p.parent.name.endswith(f"-{a}") for p in (self.ev / "archive").rglob(path.name)))

    def test_covers_label_a_writer_of_another_label_or_no_identity_archives(self) -> None:
        from ai_player.gates.provenance import provenance, suite_line

        path = self.evidence("x.txt", suite_line(self.repo, "units", self.SUITE, self.MAP_EXCLUDE))
        self.assertIsNotNone(self.keep(path, code=provenance(self.repo)), "an ai_player/ line is not covers:units")
        path = self.evidence("y.txt", suite_line(self.repo, "units", self.SUITE, self.MAP_EXCLUDE))
        self.assertIsNotNone(self.keep(path, code="unknown (no suite_map scope for this run)"))

    def test_code_fields_reads_the_line_code_digest_reads(self) -> None:
        from ai_player.gates.provenance import code_digest, code_fields

        text = (f"command: py -c \"print('code: HEAD 1234567; ai_player/ clean at HEAD (working-tree digest "
                f"sha256:{'f' * 16}')\"\n  code: HEAD 2345678; ai_player/ clean at HEAD (working-tree digest "
                f"sha256:{'e' * 16}, an empty diff)\n[VERIFY] code: HEAD 3456789; ai_player/ + hook clean at HEAD "
                f"(working-tree digest sha256:{NEW}, an empty diff)\ncode: HEAD 4567890; ai_player/ clean at HEAD "
                f"(working-tree digest sha256:{OLD}, an empty diff)\n")
        self.assertEqual(code_fields(text), (code_digest(text), "3456789", "ai_player/ + hook"))
        self.assertEqual(code_fields("no code line\n"), (None, None, None))


class RetireTests(ThrowawayRepo):
    """(#28-evidence-identity) `prune_evidence --retire` by archive key: a clean digest names no one tree."""

    def test_a_bare_clean_digest_is_refused_and_a_key_names_one_commit(self) -> None:
        from ai_player.gates.provenance import CLEAN_DIGEST

        old = self.evidence("2026-10-20-x.txt")
        a = self.head()
        self.commit("B", **{"ai_player/mode.py": "MODE = 2\n"})
        new = self.evidence("2026-10-21-y.txt")
        b = self.head()
        with self.assertRaises(SystemExit):
            prune_evidence.retire_plan(self.ev, self.ev / "archive", CLEAN_DIGEST, "")
        moves, candidates = prune_evidence.retire_plan(self.ev, self.ev / "archive", f"{CLEAN_DIGEST}-{a}", "")
        self.assertEqual((moves, candidates), ([], [old]), "the key retired another commit's file, or missed its own")
        moves, _ = prune_evidence.retire_plan(self.ev, self.ev / "archive", f"{CLEAN_DIGEST}-{b}", "2026-10-21-y.txt")
        self.assertEqual(moves, [(new, self.ev / "archive" / f"{CLEAN_DIGEST}-{b}" / new.name)])

    def test_a_bare_dirty_digest_moves_each_file_and_its_summary_to_its_own_key(self) -> None:
        from ai_player.gates.provenance import code_digest, summary_of

        self.put(**{"ai_player/mode.py": "MODE = 1\nEDIT = True\n"})
        path = self.evidence("2026-10-21-regression-units.txt")
        summary_of(path).write_text('{"schema": 1}\n', encoding="utf-8")
        dirty, a = code_digest(path.read_text(encoding="utf-8")), self.head()
        moves, _ = prune_evidence.retire_plan(self.ev, self.ev / "archive", dirty, "2026-10-21-regression-units.txt")
        self.assertEqual(sorted(t.as_posix() for _, t in moves),
                         sorted((self.ev / "archive" / f"{dirty}-{a}" / n).as_posix()
                                for n in (path.name, summary_of(path).name)))
        # `main` packs an uncited retired file into ARCHIVE / key_of(file): a summary (no code line) takes its .txt's key
        self.assertEqual(prune_evidence.key_of(summary_of(path)), f"{dirty}-{a}")
        self.assertEqual(prune_evidence.key_of(path), f"{dirty}-{a}")


class CodeLineTests(unittest.TestCase):
    def test_a_tagged_code_line_names_its_digest(self) -> None:
        # (build step 5.2, G6) through the ONE reader, `provenance.code_digest`, which `prune_evidence` re-uses
        text = f"[VERIFY] code: HEAD 7a70a445; ... working-tree digest sha256:{NEW} over git diff HEAD\n[VERIFY] more\n"
        self.assertEqual(prune_evidence.code_digest(text), NEW)
        self.assertEqual(prune_evidence.code_digest(evidence(OLD)), OLD)
        self.assertIsNotNone(prune_evidence.CODE_LINE.search(text))

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
