"""Decide whether a workflow runs a FIX ROUND, from the verifier's JSON alone (backlog N6, spec S2-3; LESSONS PR-1).

    py -3.12 tools/workflows/stage_helpers.py refix <verdict.json>     prints PASS | REFIX | UNKNOWN <why>
                                                                       exit 0 PASS, 1 REFIX, 2 UNKNOWN

WHY. LESSONS PR-1 ("a fix round runs only for a FAILURE or a rule violation; weak proofs go to the next step's list")
was PROSE ONLY, and real workflow scripts did otherwise: step 5.1's script looped `while (!v.all_pass ||
v.weak_proofs.length || v.rule_violations.length)`, so a weak proof bought a whole fix round. The other failure is the
silent one: a verifier that forgets its JSON, or writes `"all_pass": "false"` (a STRING, which JavaScript and Python
both read as TRUE), must never read as a pass. So the decision is a pure function of the file with three answers:
  PASS     `all_pass` is the boolean true, `complete` is the boolean true, `FAILURES` is absent or an empty list,
           and `rule_violations` is absent or an empty list: no fix round.
  REFIX    `all_pass` is the boolean false and `FAILURES` is a NON-EMPTY list: one fix round, aimed at exactly those
           FAILURES (a rule violation is a FAILURE; the verify template says to list it in both). `complete` may be
           false here: the failures found are real, and the re-verify after the fix covers what was not checked.
  UNKNOWN  anything else, and in particular every verdict that CONTRADICTS ITSELF or is AMBIGUOUS:
           - a missing or unreadable file, bad JSON, a top level that is not an object, a DUPLICATED key anywhere
             (json keeps the LAST one silently, so `{"all_pass": false, ..., "all_pass": true}` would read as a pass);
           - `all_pass` absent or not a boolean (the string "false" included); `complete` absent or not the boolean
             true where a PASS would follow (the verify template's WAIT-RULE writes `complete: false` when a verify
             is cut short at 150 calls, and an unfinished check with nothing found yet is not a pass);
           - `FAILURES` or `rule_violations` not a list; `all_pass: false` with an empty or missing `FAILURES`;
           - `all_pass: true` WITH failures, or WITH rule violations (a rule violation is a FAILURE);
           - a VARIANT spelling of a key (`failures`, `Failures`, `rule-violations`, `All_Pass`, a zero-width
             character inside one) that holds anything but nothing: the verifier meant something by it, and the
             exact-key reader would have ignored it. An empty variant (`"failures": []`) is ignored.
UNKNOWN MEANS ASK A HUMAN, NEVER PASS. The file is read as UTF-8 with an optional BOM (PowerShell's `Out-File` writes
one), so a correct verdict saved from PowerShell is not noise; any other encoding is UNKNOWN, never an exception.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

PASS, REFIX, UNKNOWN = "PASS", "REFIX", "UNKNOWN"
#: The keys the verify template asks for, exactly as written there.
KEYS = ("all_pass", "complete", "FAILURES", "rule_violations")
#: Characters that make two spellings of one key look different: everything but letters and digits (so `_`, `-`,
#: spaces and zero-width characters, which are not word characters, all drop out).
_NOT_ALNUM = re.compile(r"[\W_]+")


class _DuplicateKey(ValueError):
    pass


def _no_duplicates(pairs: list) -> dict:
    """json `object_pairs_hook`: refuse a duplicated key instead of keeping the last one silently."""
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise _DuplicateKey(f"duplicated key {key!r}")
        out[key] = value
    return out


def _fold(key: str) -> str:
    """A key reduced to its letters and digits, case-folded: every spelling of one word folds to one string."""
    return _NOT_ALNUM.sub("", unicodedata.normalize("NFKC", key)).casefold()


def refix_decision_why(verifier_json_path) -> tuple[str, str]:
    """(verdict, reason) for the verifier JSON at `verifier_json_path`; never raises."""
    path = Path(verifier_json_path)
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except OSError as error:
        return UNKNOWN, f"verifier JSON not readable ({type(error).__name__}): {path}"
    except UnicodeDecodeError as error:
        return UNKNOWN, f"verifier JSON is not UTF-8 ({error.reason} at byte {error.start}): {path}"
    try:
        data = json.loads(text, object_pairs_hook=_no_duplicates)
    except _DuplicateKey as error:
        return UNKNOWN, f"verifier JSON has a {error}: the reader would keep only the last one"
    except ValueError as error:
        return UNKNOWN, f"verifier JSON does not parse: {error}"
    if not isinstance(data, dict):
        return UNKNOWN, f"verifier JSON top level is {type(data).__name__}, not an object"
    folded = {_fold(k): k for k in KEYS}
    for key, value in data.items():
        canonical = folded.get(_fold(key))
        if canonical is not None and key != canonical and value is not None and value != []:
            return UNKNOWN, f"key {key!r} is a variant spelling of {canonical!r} and holds {value!r}: ambiguous"
    if "all_pass" not in data:
        return UNKNOWN, "all_pass is absent"
    all_pass = data["all_pass"]
    if not isinstance(all_pass, bool):
        return UNKNOWN, f"all_pass is {all_pass!r} ({type(all_pass).__name__}), not a boolean"
    failures = data.get("FAILURES")
    if failures is not None and not isinstance(failures, list):
        return UNKNOWN, f"FAILURES is {type(failures).__name__}, not a list"
    violations = data.get("rule_violations")
    if violations is not None and not isinstance(violations, list):
        return UNKNOWN, f"rule_violations is {type(violations).__name__}, not a list"
    complete = data.get("complete")
    if complete is not None and not isinstance(complete, bool):
        return UNKNOWN, f"complete is {complete!r} ({type(complete).__name__}), not a boolean"
    if all_pass:
        if failures:
            return UNKNOWN, f"all_pass is true but FAILURES lists {len(failures)}: a contradiction"
        if violations:
            return UNKNOWN, (f"all_pass is true but rule_violations lists {len(violations)}: a contradiction (a rule "
                             f"violation is a FAILURE)")
        if complete is not True:
            return UNKNOWN, (f"all_pass is true but complete is {complete!r}: an unfinished verify is not a pass "
                             f"(the template requires `complete: true`)")
        return PASS, "all_pass is true, complete is true, FAILURES and rule_violations are empty"
    if not failures:
        return UNKNOWN, "all_pass is false but FAILURES is missing or empty: nothing to fix, so a human decides"
    tail = "" if complete is not False else "; the verify was INCOMPLETE, so the re-verify must cover the rest"
    return REFIX, f"all_pass is false with {len(failures)} FAILURES{tail}"


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
