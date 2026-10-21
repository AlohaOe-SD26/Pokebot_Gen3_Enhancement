"""Decide whether a workflow runs a FIX ROUND, from the verifier's JSON alone (backlog N6, spec S2-3; LESSONS PR-1).

    py -3.12 tools/workflows/stage_helpers.py refix <verdict.json>     prints PASS | REFIX | UNKNOWN <why>
                                                                       exit 0 PASS, 1 REFIX, 2 UNKNOWN

WHY. LESSONS PR-1 ("a fix round runs only for a FAILURE or a rule violation; weak proofs go to the next step's list")
was PROSE ONLY, and real workflow scripts did otherwise: step 5.1's script looped `while (!v.all_pass ||
v.weak_proofs.length || v.rule_violations.length)`, so a weak proof bought a whole fix round. The other failure is the
silent one: a verifier that forgets its JSON, or writes `"all_pass": "false"` (a STRING, which JavaScript and Python
both read as TRUE), must never read as a pass. So the decision is a pure function of the file with three answers:
  PASS     `all_pass` is the boolean true and `FAILURES` is absent or an empty list: no fix round.
  REFIX    the JSON parses, `all_pass` is the boolean false and `FAILURES` is a NON-EMPTY list: one fix round, aimed at
           exactly those FAILURES (a rule violation is a FAILURE; the verify template says so).
  UNKNOWN  anything else: a missing or unreadable file, bad JSON, a top level that is not an object, `all_pass` absent
           or not a boolean (the string "false" included), `all_pass: false` with an empty or missing `FAILURES`,
           `FAILURES` not a list, or `all_pass: true` WITH failures (a contradiction).
UNKNOWN MEANS ASK A HUMAN, NEVER PASS. The key is `FAILURES` exactly as the verify template asks for it; an older
script's lowercase `failures` is therefore UNKNOWN, which errs toward a human, not toward a pass.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PASS, REFIX, UNKNOWN = "PASS", "REFIX", "UNKNOWN"


def refix_decision_why(verifier_json_path) -> tuple[str, str]:
    """(verdict, reason) for the verifier JSON at `verifier_json_path`; never raises."""
    path = Path(verifier_json_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return UNKNOWN, f"verifier JSON not readable ({type(error).__name__}): {path}"
    try:
        data = json.loads(text)
    except ValueError as error:
        return UNKNOWN, f"verifier JSON does not parse: {error}"
    if not isinstance(data, dict):
        return UNKNOWN, f"verifier JSON top level is {type(data).__name__}, not an object"
    if "all_pass" not in data:
        return UNKNOWN, "all_pass is absent"
    all_pass = data["all_pass"]
    if not isinstance(all_pass, bool):
        return UNKNOWN, f"all_pass is {all_pass!r} ({type(all_pass).__name__}), not a boolean"
    failures = data.get("FAILURES")
    if failures is not None and not isinstance(failures, list):
        return UNKNOWN, f"FAILURES is {type(failures).__name__}, not a list"
    if all_pass:
        if failures:
            return UNKNOWN, f"all_pass is true but FAILURES lists {len(failures)}: a contradiction"
        return PASS, "all_pass is true and FAILURES is empty"
    if not failures:
        return UNKNOWN, "all_pass is false but FAILURES is missing or empty: nothing to fix, so a human decides"
    return REFIX, f"all_pass is false with {len(failures)} FAILURES"


def refix_decision(verifier_json_path) -> str:
    """PASS, REFIX or UNKNOWN (see the module docstring). UNKNOWN means ask a human, never PASS."""
    return refix_decision_why(verifier_json_path)[0]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "refix":
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    verdict, why = refix_decision_why(argv[1])
    print(f"{verdict} {why}")
    return {PASS: 0, REFIX: 1}.get(verdict, 2)


if __name__ == "__main__":
    sys.exit(main())
