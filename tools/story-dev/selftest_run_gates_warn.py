"""Fault test for `run_gates.py`'s WARN state (2026-10-21, spec S3-2's critic fix).

WHY: a gate in `WARN_OK` may exit `WARN_EXIT` (4) to say "I ran but could NOT verify" (the facts-ledger gate on a machine
without the pinned decomp clone). That third state is only safe if it is narrow: a WARN must not fail the suite, must be
counted OUT of the passing enforcing gates and named in the closing line (the headline carries the caveat), and ANY other
non-zero exit, or exit 4 from a gate NOT in `WARN_OK`, must still be a FAIL. Each case below runs the real `main()` over
fake gate scripts in a temp folder, with `HERE`, `GATES`, `WARN_OK` and `ADVISORY` patched. No ROM; under 2 s.
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_gates as RG  # noqa: E402

_REAL = (RG.HERE, RG.GATES, RG.WARN_OK, RG.ADVISORY, list(sys.argv))


def run(gates: dict[str, int], warn_ok: set[str]) -> tuple[int, str]:
    """The real run_gates.main() over fake gates: {script name: its exit code}."""
    tmp = Path(tempfile.mkdtemp(prefix="rgwarn-"))
    try:
        for name, code in gates.items():
            (tmp / name).write_text(f"import sys; sys.exit({code})\n", encoding="utf-8")
        RG.HERE, RG.GATES = tmp, [(n, False) for n in gates]
        RG.WARN_OK, RG.ADVISORY = frozenset(warn_ok), frozenset()
        sys.argv = ["run_gates.py"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RG.main()
        return rc, buf.getvalue()
    finally:
        RG.HERE, RG.GATES, RG.WARN_OK, RG.ADVISORY, sys.argv[:] = *_REAL[:4], _REAL[4]
        shutil.rmtree(tmp, ignore_errors=True)


CASES = [
    ("CONTROL a WARN_OK gate exiting 4 -> the suite passes, the WARN is named and counted out",
     {"w.py": 4, "p.py": 0}, {"w.py"},
     lambda rc, out: rc == 0 and "ran but could NOT verify: w.py" in out and "ALL 1 ENFORCING" in out),
    ("FAULT a WARN_OK gate exiting 1 -> FAIL", {"w.py": 1, "p.py": 0}, {"w.py"},
     lambda rc, out: rc == 1 and "FAILED: 1" in out),
    ("FAULT a gate NOT in WARN_OK exiting 4 -> FAIL", {"x.py": 4, "p.py": 0}, set(),
     lambda rc, out: rc == 1 and "FAILED: 1" in out),
    ("CONTROL every gate passes -> no WARN text, all counted", {"w.py": 0, "p.py": 0}, {"w.py"},
     lambda rc, out: rc == 0 and "could NOT verify" not in out and "ALL 2 ENFORCING" in out),
    ("FAULT the real WARN_OK names a script that is not a registered gate -> caught here", None, None, None),
]


def main() -> int:
    ok = True
    for label, gates, warn_ok, want in CASES:
        if gates is None:
            registered = {n for n, _ in _REAL[1]}
            good = set(_REAL[2]) <= registered
            label = label.replace("FAULT", "CHECK") + f" (WARN_OK {sorted(_REAL[2])} all registered: {good})"
        else:
            rc, out = run(gates, warn_ok)
            good = want(rc, out)
            label += f"  (rc={rc})"
        ok &= good
        print(("PASS " if good else "FAIL ") + label)
    print(f"{'ALL PASS' if ok else 'FAILED'} ({len(CASES)} checks)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
