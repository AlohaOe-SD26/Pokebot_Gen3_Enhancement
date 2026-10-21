"""GATE (shim): run `tools/experience/test_extract_experience.py`, the A6 experience-records suite (spec S3-3), from the
gate suite's own folder.

WHY A SHIM. `run_gates.py` runs only scripts in `tools/story-dev/`, and the spec places the extractor and its tests
in `tools/experience/` (outside `ai-agent/`, so the learner never restarts; outside `ai_player/`, so nothing here is
in the AI's code digest). This file adds no checks of its own: it runs that suite in this process and returns its
exit code unchanged (0 all pass; 1 a FAIL; 4 WARN = the real-data arms were SKIPPED because this machine has no
learner clone or no pinned decomp, never a pass).
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1] / "experience" / "test_extract_experience.py"

if __name__ == "__main__":
    sys.argv = [str(SUITE)]
    try:
        runpy.run_path(str(SUITE), run_name="__main__")
    except SystemExit as exc:
        sys.exit(exc.code)
    sys.exit(1)  # the suite always ends in sys.exit; reaching here means it did not run to its verdict
