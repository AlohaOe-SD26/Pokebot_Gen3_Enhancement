r"""GATE — `fix_doc_citations.py` re-points a RANGE citation at BOTH ends, and never a longer number's prefix.

WHY (2026-09-26): the repairer replaced the bare `path:old` token, so `victory_road.py:2014-2026` became `2017-2026` —
the exact defect `08-MISTAKES.md` already named ("A RE-POINT SHIFTS BOTH ENDS BY THE SAME OFFSET"), committed a
second time, by the tool. `probe_citation_ranges.py` only catches an INVERTED range, not a stale end. The old logic,
swapped back in, fails this self-test on 2 of 4 cases (range end; `a.py:12` inside `a.py:120`).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_fix_doc_citations.py
"""
import sys

import fix_doc_citations

if __name__ == "__main__":
    sys.exit(fix_doc_citations._selftest())
