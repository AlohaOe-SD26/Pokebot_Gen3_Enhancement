"""UNIT PROOFS of the anchor gate (`gates/check_anchors.py`): every mutant runner's anchors hit exactly once. Test side;
no emulator, and no mutant is ever run.
    py -3.12 -B ai_player/gates/test_check_anchors.py
CONTROL and FAULTS (CLAUDE.md rule 6):
  ControlTests  the real tree PASSES (every runner read, every runner with edits; totals printed), by `check` and by the
                CLI's exit code and last line; the temp copy the faults use PASSES before any fault is planted.
  FaultTests    on that temp copy: W64's real case (its old one-line anchor restored in revert_step3's table: 2 hits, the
                08-MISTAKES 2026-11-09 failure), an anchor gone from its target file (0 hits), and a table that cannot
                be read (revert_step4's MUTANTS renamed; revert_r1_mutants.json corrupt; it missing) each FAIL, by name;
                and a table renamed then restored within one second is read FRESH (the quick lane's failure of a loader
                through __pycache__; A/B 2026-11-09: that loader ERRORS this test, the shipped one passes).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import check_anchors  # noqa: E402

GATE = Path(check_anchors.__file__).resolve()
#: forget_bump's last three lines in world/memory.py (W64's anchor since 2026-11-09)
FORGET_BUMP_TAIL = ('        if (memory.bumped.get((xy, direction)) or {}).get("slid"):\n            return None\n'
                    '        return memory.bumped.pop((xy, direction), None)\n')
#: the W64 edit as it was before 58fd4778 (its parent, dd8b31ef), as source text of revert_step3.py
OLD_W64_SOURCE = (r'[("world/memory.py", "        return memory.bumped.pop((xy, direction), None)\n", '
                  r'"        return None  # MUTANT W64\n")],')
OLD_W64_EDIT = ("world/memory.py", "        return memory.bumped.pop((xy, direction), None)\n",
                "        return None  # MUTANT W64\n")


def run_cli(root: Path) -> tuple[int, str]:
    done = subprocess.run([sys.executable, "-B", str(GATE), "--root", str(root)], capture_output=True, text=True,
                          encoding="utf-8", timeout=120)
    return done.returncode, done.stdout + done.stderr


class ControlTests(unittest.TestCase):
    def test_the_real_tree_passes_and_every_runner_has_edits(self) -> None:
        report = check_anchors.check(REPO)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.findings, [])
        self.assertEqual(set(report.totals), set(check_anchors.RUNNERS))
        for runner, (mutants, edits) in report.totals.items():
            print(f"CONTROL {runner}: {mutants} mutants, {edits} edits, all hit once")
            self.assertGreater(edits, 0, runner)
        self.assertTrue(report.ok)

    def test_the_cli_passes_on_the_real_tree(self) -> None:
        code, out = run_cli(REPO)
        self.assertEqual(code, 0, out)
        # (BP-1, 2026-11-09) eight runners: revert_bossprep joined
        self.assertRegex(out.strip().splitlines()[-1], r"^ANCHORS GATE: PASS \(8 of 8 runners, \d+ mutants, \d+ edits, "
                                                       r"0 not unique, 0 errors\)$")


class FaultTests(unittest.TestCase):
    root: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(tempfile.mkdtemp(prefix="ai_player_anchor_gate_"))
        shutil.copytree(REPO / "ai_player", cls.root / "ai_player",
                        ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root, ignore_errors=True)

    def plant(self, relative: str, edit) -> None:
        """Replace `<copy>/ai_player/<relative>` by edit(text) (None deletes it) until the test ends."""
        path = self.root / "ai_player" / relative
        original = path.read_text(encoding="utf-8")
        self.addCleanup(path.write_text, original, encoding="utf-8")
        changed = edit(original)
        if changed is None:
            path.unlink()
        else:
            self.assertNotEqual(changed, original, f"the fault did not change {relative}")
            path.write_text(changed, encoding="utf-8")

    def test_0_the_copy_passes_before_any_fault(self) -> None:
        self.assertTrue(check_anchors.check(self.root).ok)

    def test_w64_old_one_line_anchor_hits_twice(self) -> None:
        def restore_old_w64(text: str) -> str:
            start = text.index('[("world/memory.py",', text.index('"W64": ('))
            end = text.index('# MUTANT W64\\n")],', start) + len('# MUTANT W64\\n")],')
            return text[:start] + OLD_W64_SOURCE + text[end:]
        self.plant("gates/revert_step3.py", restore_old_w64)
        self.assertEqual(check_anchors.load_table(self.root, "revert_step3")["W64"][2], [OLD_W64_EDIT],
                         "the planted table is not the parent's W64")
        report = check_anchors.check(self.root)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.findings, [("revert_step3", "W64", "world/memory.py", 2)])
        code, out = run_cli(self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("NOT UNIQUE revert_step3 W64 world/memory.py: 2 hits", out)
        self.assertRegex(out, r"(?m)^ANCHORS GATE: FAIL \(8 of 8 runners, .*1 not unique, 0 errors\)$")

    def test_an_anchor_gone_from_its_file_hits_zero(self) -> None:
        def rewrite_forget_bump(text: str) -> str:
            self.assertEqual(text.count(FORGET_BUMP_TAIL), 1)
            return text.replace(FORGET_BUMP_TAIL, FORGET_BUMP_TAIL[:-1] + "  # a later round rewrote this line\n")
        self.plant("world/memory.py", rewrite_forget_bump)
        report = check_anchors.check(self.root)
        self.assertEqual(report.errors, [])
        self.assertIn(("revert_step3", "W64", "world/memory.py", 0), report.findings)
        self.assertEqual({(f[2], f[3]) for f in report.findings}, {("world/memory.py", 0)}, report.findings)
        self.assertFalse(report.ok)

    def test_a_table_restored_within_the_same_second_is_read_fresh(self) -> None:
        """The quick lane's failure (2026-11-09): a loader through __pycache__ read the RENAMED table back after its
        restore (same length, same second). Bytecode writing is forced ON so the arm is not vacuous under -B."""
        saved, sys.dont_write_bytecode = sys.dont_write_bytecode, False
        self.addCleanup(setattr, sys, "dont_write_bytecode", saved)
        check_anchors.load_table(self.root, "revert_step4")
        second = int(time.time())
        while int(time.time()) == second:  # start at a second boundary: plant, read and restore share one second
            time.sleep(0.005)
        self.plant("gates/revert_step4.py", lambda t: t.replace("\nMUTANTS: dict", "\nMUTANTZ: dict", 1))
        with self.assertRaises(ValueError):
            check_anchors.load_table(self.root, "revert_step4")
        self.doCleanups()
        sys.dont_write_bytecode = False
        self.addCleanup(setattr, sys, "dont_write_bytecode", saved)
        self.assertEqual(int(time.time()), second + 1, "the arm crossed a second: not a same-second restore")
        self.assertIn("B0", check_anchors.load_table(self.root, "revert_step4"))

    def test_a_table_that_cannot_be_read_is_an_error(self) -> None:
        cases = {
            "revert_step4 MUTANTS renamed": ("revert_step4", "gates/revert_step4.py",
                                             lambda t: t.replace("\nMUTANTS: dict", "\nMUTANTZ: dict", 1)),
            "revert_r1_mutants.json corrupt": ("revert_r1", "gates/revert_r1_mutants.json", lambda t: t[: len(t) // 2]),
            "revert_r1_mutants.json missing": ("revert_r1", "gates/revert_r1_mutants.json", lambda t: None),
        }
        for label, (runner, relative, edit) in cases.items():
            with self.subTest(label):
                try:
                    self.plant(relative, edit)
                    report = check_anchors.check(self.root)
                    self.assertEqual([r for r, _ in report.errors], [runner], report.errors)
                    self.assertNotIn(runner, report.totals)
                    self.assertFalse(report.ok)
                    code, out = run_cli(self.root)
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"ERROR {runner}: its table could not be read", out)
                finally:
                    self.doCleanups()  # the next case starts from the clean copy


if __name__ == "__main__":
    unittest.main()
