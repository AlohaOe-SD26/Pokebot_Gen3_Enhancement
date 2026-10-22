"""Gate: `tools/scripts_census.py`, the event-script census that KB2 slice 2's design rests on (2026-10-22).

WHY: slice 2's parsers (`items_gifts.json`, `events.json`) may not be written before a census of every `scripts.inc`
command at the pinned decomp, and a census is only worth trusting while it classifies EVERY line: its first real run
found 30 lines of two shapes nobody had listed (`#ifdef BUGFIX` blocks and one-line C comments), and it found the
field-item scripts (`finditem`, 165 lines) in the SHARED `data/scripts/item_ball_scripts.inc`, not in the map scripts
the spec named. A pin bump that brings a new shape must turn this red, not slip into a parser.

Arms (FAULT + CONTROL each):
  A1 the census's own self-test: CONTROL a clean temp tree (every kind counted, preprocessor lines listed by file:line,
     0 UNPARSED) and FAULT one planted unparsable line (exit 1, named by file:line)
  A2 the pin refusal: FAULT a folder that is not a clone is REFUSED (exit 2); its CONTROL is A3 running at all
  A3 the real census at the pinned clone: exit 0 and 0 UNPARSED in both tables
Exit 0 PASS, 1 FAIL, 4 WARN (no pinned clone: A3 SKIPPED, never a pass). No ROM; ~5 s.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CENSUS = REPO / "tools" / "scripts_census.py"
sys.path.insert(0, str(REPO / "tools"))
import decomp_lookup as dl  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CENSUS), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    results: list[tuple[str, bool]] = []
    p = run("--self-test")
    print(p.stdout.rstrip())
    results.append(("A1 the census self-test (CONTROL + FAULT)", p.returncode == 0 and "ALL PASS" in p.stdout))

    with tempfile.TemporaryDirectory(prefix="census_notaclone_") as tmp:
        p = run("--decomp", tmp)
    results.append(("A2 FAULT: a folder that is not a clone is REFUSED (exit 2)",
                    p.returncode == 2 and "REFUSED" in p.stdout))

    warn = False
    try:
        dl.decomp_root()
    except dl.DecompRefused as exc:
        warn = True
        print(f"WARN  A3 SKIPPED: no pinned decomp clone ({exc.kind}); the real census did not run")
    if not warn:
        with tempfile.TemporaryDirectory(prefix="census_out_") as tmp:
            out = Path(tmp) / "census.md"
            p = run("--out", str(out))
            text = out.read_text(encoding="utf-8") if out.exists() else ""
        stats = [line for line in p.stderr.splitlines() if line.startswith("CENSUS ")]
        print("\n".join(stats))
        clean = (p.returncode == 0 and len(stats) == 2 and all(s.endswith(" 0 UNPARSED") for s in stats)
                 and text.count("**0 UNPARSED**") == 2)
        results.append(("A3 the real census at the pin: exit 0, 0 UNPARSED in both tables", clean))

    for label, ok in results:
        print(("PASS  " if ok else "FAIL  ") + label)
    failed = [label for label, ok in results if not ok]
    if failed:
        print(f"SELFTEST scripts_census gate: FAILED ({len(failed)} of {len(results)})")
        return 1
    if warn:
        print(f"SELFTEST scripts_census gate: WARN ({len(results)} arms PASS, the real-data arm SKIPPED)")
        return 4
    print(f"SELFTEST scripts_census gate: ALL PASS ({len(results)} arms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
