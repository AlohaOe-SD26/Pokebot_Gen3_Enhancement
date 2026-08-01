"""Regression test for the counter-training budget gate. NO EMULATOR.

WHAT WENT WRONG (measured live, batch `20260731-170603`, three times, verbatim):

    Story: counter hunt CAUGHT Machop (slot 5).
    Story: training Machop to L35 rejected — estimated 1693806 frames exceeds the
           budget (250000). It joins the fight at L16.

The gate was ALL-OR-NOTHING. A hunting-ground counter is ~15 levels below the team BY
CONSTRUCTION, so "train to the team or not at all" resolves to NOT AT ALL essentially every
time — and the chain spent a full cross-Hoenn journey and a Poké Ball to field a L16 Machop
against Norman's L28-31 team. **Balance Badges earned in that batch: 0.**

It also contradicted the user's ruling for `#24-counters` — *"price both, then catch-and-train
a Fighting type for Norman"*. Catching and then declining to train is the cost of one option
with the benefit of neither.

`affordable_training_target` spends the budget instead of refusing it.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.counter_hunt import affordable_training_target as afford  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


# The measured Machop case: L16 -> L35 costs 1,693,806 frames, i.e. ~89k per level.
PER_LEVEL = 89_000
machop = lambda level: (level - 16) * PER_LEVEL  # noqa: E731

print("1. the measured case — it must now train SOMETHING")
target = afford(16, 35, 250_000, machop)
check("it no longer refuses outright", target > 16, f"L{target}")
check("it stays within the budget", machop(target) <= 250_000, f"{machop(target)} frames")
check("it takes the HIGHEST affordable level, not the first",
      machop(target + 1) > 250_000, f"L{target} affordable, L{target + 1} is not")
check("it never exceeds what was actually wanted", afford(16, 18, 10_000_000, machop) == 18)

print("\n2. honest declines are preserved")
# ‼ The caller distinguishes "trained a bit" from "could not train at all", and the second
# must still be reachable — otherwise a genuinely unaffordable case silently reports success.
check("a budget too small for even one level returns the current level",
      afford(16, 35, 1_000, machop) == 16)
check("an already-sufficient mon is a no-op", afford(30, 30, 250_000, machop) == 30)
check("a wanted level below the current one cannot go backwards",
      afford(30, 20, 250_000, machop) == 30)

print("\n3. an UNKNOWN estimate is not a cheap one")
# The neighbouring training entry points all treat None as "decline", and this must match —
# an unknown cost that reads as free is how a 2M-frame grind gets started by accident.
check("None at the first level stops immediately",
      afford(16, 35, 250_000, lambda level: None) == 16)
check("None partway through stops there, keeping what was affordable",
      afford(16, 35, 10_000_000, lambda level: None if level > 20 else machop(level)) == 20)

print("\n4. it is not fooled by a non-monotonic estimator")
# Costs rise with level, so the scan stops at the first miss. Pin that this is the intended
# reading rather than an accident: a dip AFTER an unaffordable level must not be picked up.
weird = lambda level: 1_000_000 if level == 18 else (level - 16) * 1_000  # noqa: E731
check("it stops at the first unaffordable level and does not resume",
      afford(16, 35, 250_000, weird) == 17, f"L{afford(16, 35, 250_000, weird)}")

print("\n5. ‼ THE HONEST LIMIT OF THIS FIX — pinned so nobody over-claims it")
# Spending the budget is strictly better than refusing it, but it does NOT make a L16 catch
# a real answer to a L31 boss: at ~89k frames/level, 250,000 buys about TWO levels.
levels_bought = afford(16, 35, 250_000, machop) - 16
check("250k frames buys only ~2-3 levels at the measured rate",
      1 <= levels_bought <= 3, f"{levels_bought} levels")
check("...so the counter still enters Norman far below the team",
      afford(16, 35, 250_000, machop) < 28 - 5,
      f"L{afford(16, 35, 250_000, machop)} vs Norman's L28-31")
# What a budget WOULD have to be to close the gap — recorded so the decision has a number.
need = (26 - 16) * PER_LEVEL
check("closing to within ~5 levels of Norman would cost ~890k frames",
      850_000 <= need <= 950_000, f"{need} frames")

print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("ALL PASS")
