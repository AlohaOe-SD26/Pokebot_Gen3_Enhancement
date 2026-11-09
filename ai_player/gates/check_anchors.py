"""TEST SIDE (2026-11-09, chapter 6-7 branch): EVERY MUTANT RUNNER'S ANCHORS HIT EXACTLY ONCE, checked in seconds.

    py -3.12 -B ai_player/gates/check_anchors.py [--root DIR]      exit 0 = PASS, 1 = FAIL (or a table that cannot be read)

WHY (08-MISTAKES 2026-11-09): chapter 6's round 3 added `forget_slide`, whose last line repeated `forget_bump`'s, so
revert_step3's W64 anchor matched TWICE. The rounds checked only revert_step5's and revert_r1's anchors; the full lane
found it eight rounds later (revert_step3 FAIL before running a mutant). A code change anywhere in ai_player/ can break
an older runner's anchor, so this gate checks EVERY runner's, without running one mutant.

HOW: each runner in `RUNNERS` is imported from `<root>/ai_player/gates/` (its own module code builds its table, so the
table read is the table it runs: revert_r1 adds `revert_r1_mutants.json` in its `_load()`), and every mutant's edits
are applied the way that runner's `make_copy` applies them: IN ORDER, on the text of `<root>/ai_player/<file>` read with
`read_text(encoding="utf-8")`, each edit requiring `text.count(old) == 1` and then `text.replace(old, new)` (a second
edit of the same file sees the first edit's result). An edit whose anchor does not hit exactly once is reported as
`NOT UNIQUE <runner> <mutant> <file>: <hits> hits`; the mutant's later edits are still checked, on the text as it was.

A runner whose table cannot be read (the file is missing, its import raises, the table attribute is missing, not a dict,
empty, malformed, or revert_r1's data file is missing) is an ERROR and the gate FAILS: a table nobody could read is not
a table that passed.

KNOWN LIMIT: the copies' ignore patterns (`evidence`, `__pycache__`, `*.ss1`; revert_step11 also `fixtures`) are not
modelled: an anchor in a file a runner does not copy would PASS here and fail in the runner.

`gates/test_check_anchors.py` proves it: the real tree PASSES (totals per runner), and on temp copies the old one-line
W64 anchor (2 hits), a missing anchor (0 hits), a renamed table and a corrupt/missing revert_r1_mutants.json FAIL.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
#: runner -> (the attribute holding its table, the data file its import must find, relative to gates/, or None)
RUNNERS: dict[str, tuple[str, str | None]] = {
    "revert_step2": ("MUTANTS", None),
    "revert_step3": ("MUTANTS", None),
    "revert_step4": ("MUTANTS", None),
    "revert_step5": ("MUTANTS", None),
    "revert_step11": ("REVERTS", None),
    "revert_safety_gates": ("MUTANTS", None),
    "revert_r1": ("MUTANTS", "revert_r1_mutants.json"),
}
_SERIAL = itertools.count()


@dataclass
class Report:
    totals: dict[str, tuple[int, int]] = field(default_factory=dict)  # runner -> (mutants, edits)
    findings: list[tuple[str, str, str, int]] = field(default_factory=list)  # (runner, mutant, file, hits)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (runner, why)

    @property
    def ok(self) -> bool:
        return not self.findings and not self.errors and len(self.totals) == len(RUNNERS)


def load_table(root: Path, runner: str) -> dict:
    """The runner's table as its own module builds it, imported from `root`; raises ValueError when it cannot be read."""
    attribute, data = RUNNERS[runner]
    path = root / "ai_player" / "gates" / f"{runner}.py"
    if not path.is_file():
        raise ValueError(f"{path} is missing")
    if data and not (path.parent / data).is_file():
        raise ValueError(f"its data file {data} is missing (the import would silently drop its mutants)")
    spec = importlib.util.spec_from_file_location(f"_check_anchors_{runner}_{next(_SERIAL)}", path)
    module = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    sys.modules[spec.name] = module
    try:
        # compiled from the SOURCE as it is now, never through __pycache__: a .pyc is validated by the source's mtime in
        # whole seconds and its size, so an edit of the same length within a second (a renamed table) would be read stale
        # (2026-11-09: test_check_anchors failed 4 tests in the quick lane, which runs without -B, and passed alone; an
        # A/B on a copy, rename the table then restore it within one second: exec_module read the RENAMED table back
        # after the restore, this compile read the restored one)
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec", dont_inherit=True), module.__dict__)
    except BaseException as error:  # noqa: BLE001 - a runner's import may SystemExit (revert_r1's duplicate check)
        if isinstance(error, KeyboardInterrupt):
            raise
        raise ValueError(f"its import raised {type(error).__name__}: {error}") from None
    finally:
        sys.path[:] = saved
        sys.modules.pop(spec.name, None)
    table = getattr(module, attribute, None)
    if not isinstance(table, dict) or not table:
        raise ValueError(f"{attribute} is {'missing' if table is None else 'not a non-empty dict'}")
    for name, entry in table.items():
        edits = entry[2] if isinstance(entry, (tuple, list)) and len(entry) >= 3 else None
        if not isinstance(edits, list) or not all(isinstance(e, (tuple, list)) and len(e) == 3
                                                  and all(isinstance(x, str) for x in e) for e in edits):
            raise ValueError(f"{attribute}[{name!r}] has no list of (file, old, new) edits at [2]")
    if not any(entry[2] for entry in table.values()):
        raise ValueError(f"{attribute} has no edit at all")
    return table


def check(root: Path = REPO) -> Report:
    report = Report()
    originals: dict[str, str | None] = {}
    for runner in RUNNERS:
        try:
            table = load_table(root, runner)
        except ValueError as error:
            report.errors.append((runner, str(error)))
            continue
        edits_seen = 0
        for name, entry in table.items():
            texts: dict[str, str | None] = {}
            for relative, old, new in entry[2]:
                edits_seen += 1
                if relative not in texts:
                    if relative not in originals:
                        target = root / "ai_player" / relative
                        originals[relative] = target.read_text(encoding="utf-8") if target.is_file() else None
                    texts[relative] = originals[relative]
                text = texts[relative]
                hits = text.count(old) if text is not None else 0
                if hits != 1:
                    report.findings.append((runner, name, relative if text is not None else f"{relative} (missing)",
                                            hits))
                    continue
                texts[relative] = text.replace(old, new)
        report.totals[runner] = (len(table), edits_seen)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO, help="the folder holding ai_player/ (default: this repo)")
    args = parser.parse_args(argv)
    report = check(args.root.resolve())
    for runner, (mutants, edits) in report.totals.items():
        print(f"ANCHORS {runner}: {mutants} mutants, {edits} edits")
    for runner, why in report.errors:
        print(f"ERROR {runner}: its table could not be read ({why})")
    for runner, name, relative, hits in report.findings:
        print(f"NOT UNIQUE {runner} {name} {relative}: {hits} hits")
    mutants = sum(m for m, _ in report.totals.values())
    edits = sum(e for _, e in report.totals.values())
    print(f"ANCHORS GATE: {'PASS' if report.ok else 'FAIL'} ({len(report.totals)} of {len(RUNNERS)} runners, {mutants} "
          f"mutants, {edits} edits, {len(report.findings)} not unique, {len(report.errors)} errors)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
