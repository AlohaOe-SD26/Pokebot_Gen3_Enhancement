"""GATE — prove the FORK-DRIFT METER still sees a real change, and still ignores a cosmetic one.

WHY THIS EXISTS (2026-09-15). `promote.py --check` is called *the authority* on sandbox↔custom drift
in four places across PROJECT KNOWLEDGE, and `04-HANDOFF.md` tells agents to trust its live number
over any figure written into a document. On 2026-09-15 that authority was measured WRONG in the
harmless-looking direction: it reported

    drift (sandbox → custom): 1 file(s)
        modules/modes/util/higher_level_actions.py

while `git status` was clean and git itself stored ONE blob for both copies —

    git rev-parse HEAD:custom-pokebot/modules/modes/util/higher_level_actions.py \
                  HEAD:sandbox-pokebot/modules/modes/util/higher_level_actions.py
    -> 08b92af10e79bc15d543e460c7859a7b0279d844   (BOTH)

The cause was `core.autocrlf=true`: the copy git had CHECKED OUT carried CRLF, the copy a Python
tool had WRITTEN carried LF, and the meter hashed raw bytes. The files were identical in every sense
that can affect the running bot — the tokenizer never sees a CR (PEP 278 universal newlines).

⛔ THE DAMAGE A PHANTOM DOES IS NOT COSMETIC. It has exactly two outcomes, both bad:
  (a) an agent acts on it and "promotes" the file — producing a commit git records as containing
      NOTHING, i.e. precisely the no-op promotion `promote.py`'s own module docstring says it
      REFUSES to make because it "inflates a commit and lies"; or
  (b) the reader learns the number is noise and stops reading it — at which point the next REAL
      drift, a fix that never reached the fork that ships, is invisible.
  `CLAUDE.md` rule 6: a gate with false positives is strictly worse than no gate.

⛔ AND THE FIX BUYS ITS OWN RISK, WHICH IS WHY THIS FILE IS A GATE AND NOT A COMMENT. Teaching a
comparator to ignore a category of difference trades false positives for the possibility of false
NEGATIVES — and a false negative here is the failure that actually costs: a promoted-looking fork
that never received the fix. So the normalisation is not trusted, it is TESTED, and the arm that
matters most is the CONTROL THAT MUST FIRE: two files one character apart must still read as drift.
Without that arm, a `_digest` that returned a constant would pass every other arm perfectly.

WHAT IT RUNS. `promote.py`'s own `_self_test()`, unchanged and un-duplicated — five arms over real
files on disk, driving the REAL `measure()` with SANDBOX/CUSTOM rebound to a temporary tree:

    A  one character of content differs        -> MUST read drift=1   (the control)
    B  line endings differ, CRLF vs LF         -> MUST read drift=0, line-ending-only=1
    C  byte-identical                          -> MUST read nothing at all
    D  absent from custom entirely             -> MUST read drift=1
    E  content AND endings both differ         -> MUST read drift=1   (not excused as cosmetic)

‼ IT DELIBERATELY DOES NOT RE-IMPLEMENT THE COMPARISON. A self-test that re-derives the logic it is
testing passes whenever the two derivations agree — including when both are wrong. That vacuous
shape is one this project has paid for more than once, so the arms call the shipped function.

⭐ TO FAULT-TEST THIS GATE ITSELF: make `promote._digest` return a constant (or drop the `.replace`
calls) and re-run — arm A (or arm B) goes red and this exits 1.

    PYTHONUTF8=1 py -3.12 selftest_promote_drift.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import promote  # noqa: E402  — path is set above; promote.py is a sibling, not a package


def main() -> int:
    # ⛔ Call the SHIPPED entry point, not a copy of its arms. If `_self_test` is ever renamed or
    #   removed, this gate must fail loudly rather than quietly test nothing — hence no getattr
    #   default, and no try/except around the import.
    return promote._self_test()


if __name__ == "__main__":
    sys.exit(main())
