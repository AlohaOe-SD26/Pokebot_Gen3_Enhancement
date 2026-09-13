"""`#24-maintain-staletarget` — does the stale boss target actually COST anything? Re-derivable.

⛔ WHY THIS FILE EXISTS AT ALL. The numbers behind the 2026-09-12 "downgrade" ruling were first
produced by throwaway one-liners. An adversarial reviewer reproduced most of them from scratch and
then said the quiet part: *"no script under tools/story-dev computes these; they rest on an
uncommitted, now-unverifiable methodology."* ⇒ a measurement that decides a ruling must be
RE-DERIVABLE by the next session, or the ruling rests on my word. This is that script.

## THE FILED DEFECT
`_prepare_for_fight` (`plugins/custom_modes/story_mode.py`) runs the maintenance errand BEFORE it
escalates the boss target on a reactive re-attempt:
    :2613  yield from self._maintain_lagging_battler(target)     <- errand runs with THIS target
    :2763  target = team_max + 1                                 <- boss-mode escalation
    :2780  target = max(target, team_max + 5)                    <- heavy escalation
    :2803  catchup = target - TRAIN_CATCHUP_GAP                  <- exclusion floor from the NEW target
Claim: the errand tops a laggard up, then the same call re-excludes it — budget spent for nothing,
on exactly the runs with the worst laggards.

## ⛔⛔ WHAT THE STDOUT LINES ACTUALLY MEAN — read this before trusting any count
`story_mode.py:2394` prints `"… is below the Lv N prep floor - maintaining it at …"` the moment
`decide_maintenance` APPROVES a slot — **before** the `try:` that rotates and trains. So it proves
APPROVAL, NOT COMPLETION. This project's rule 7 is exactly this ("a candidate is not an attempt"),
and the first version of this analysis described that print as "maintenance ACTED", which is wrong.
The line that proves completion is `[MAINTAIN] done pid=… REACHED` — and it goes to the DEBUG log,
never to stdout, so the two streams cannot be correlated by line proximity.
⇒ this script reports APPROVED, and says so in the output. Do not relabel it.

## ⛔ AND THERE ARE **TWO** ESCALATION PATHS. The first analysis measured only the RARE one.
    heavy   `:2786`  "lost here N× — training harder"      — measured:   67 events, 12% of lanes
    boss    `:2763`  "boss-training mode"                  — measured: 3,132 events, 83% of lanes  (47x)
Both are gated by the SAME `losses >= 2` condition and both recompute `catchup`. An analysis that
covers only the first is not an answer. This one counts both.

Run: py -3.12 tools/story-dev/probe_staletarget_cost.py
"""
import collections
import glob
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent
RUNS = sorted(glob.glob(str(ROOT / "x4-runs" / "2026091*" / "L*" / "stdout.txt")))

#: APPROVAL, not completion — see the module docstring.
APPROVED = re.compile(r"below the Lv (\d+) prep floor")
SKIPPED = re.compile(r"skipping maintenance - ([^.\[]{0,80})")
ESC_HEAVY = re.compile(r"lost here \d+. . training harder")
ESC_BOSS = re.compile(r"boss-training mode")
RUN_START = re.compile(r"ENDLESS RESET: starting run")
#: The aborts that preempt the errand AFTER approval — each spends ZERO training frames.
ABORTS = ("rather than training the wrong Pok", "could not reach", "carrying on")

runs = approved = skipped = 0
esc = collections.Counter()
lanes_with = collections.Counter()
near = collections.Counter()      # escalation with an APPROVAL within N lines before
aborted_after_approval = 0
skip_reasons = collections.Counter()

for f in RUNS:
    try:
        lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
    except Exception:
        continue
    lane_heavy = lane_boss = False
    for i, l in enumerate(lines):
        if RUN_START.search(l):
            runs += 1
        if APPROVED.search(l):
            approved += 1
            # ⭐ THE CONJUNCT THAT MATTERS: did the approved errand actually get to spend frames?
            nxt = " ".join(x for x in lines[i + 1:i + 4])
            if any(a in nxt for a in ABORTS):
                aborted_after_approval += 1
        m = SKIPPED.search(l)
        if m:
            skipped += 1
            skip_reasons[m.group(1).strip()[:46]] += 1
        for name, rx in (("heavy :2786", ESC_HEAVY), ("boss  :2763", ESC_BOSS)):
            if rx.search(l):
                esc[name] += 1
                if name.startswith("heavy"):
                    lane_heavy = True
                else:
                    lane_boss = True
                for win in (3, 60, 200):
                    if any(APPROVED.search(w) for w in lines[max(0, i - win):i]):
                        near[(name, win)] += 1
    if lane_heavy:
        lanes_with["heavy :2786"] += 1
    if lane_boss:
        lanes_with["boss  :2763"] += 1

print("=" * 96)
print("  #24-maintain-staletarget — measured cost of the stale boss target")
print("=" * 96)
print(f"  lanes scanned            : {len(RUNS)}")
print(f"  runs                     : {runs}")
print(f"  maintenance APPROVED     : {approved}   (approval, NOT completion — see docstring)")
print(f"    ...aborted within 3 lines of approval: {aborted_after_approval}"
      f"  ⇒ ZERO training frames spent in these")
print(f"  maintenance SKIPPED      : {skipped}")
print()
print("  ESCALATIONS — both paths, same `losses >= 2` gate:")
for name in ("heavy :2786", "boss  :2763"):
    print(f"    {name} : {esc[name]:>5} events across {lanes_with[name]:>3} lanes")
print()
print("  ⭐ THE QUESTION — an escalation with maintenance APPROVED shortly before it:")
for name in ("heavy :2786", "boss  :2763"):
    row = "  ".join(f"<={w}L: {near[(name, w)]}" for w in (3, 60, 200))
    print(f"    {name} : {row}")
print()
print("  top SKIP reasons (what refuses the errand instead):")
for k, v in skip_reasons.most_common(5):
    print(f"    {v:>5}  {k}")
print()
print("=" * 96)
print("  HOW TO READ THIS: a NON-ZERO 'approved shortly before an escalation' is only a COST if the")
print("  errand then SPENT frames. Compare it against the aborted-after-approval count — every case")
print("  traced by hand on 2026-09-12 aborted (rotation blocked, or the heal walk failed) and spent")
print("  nothing. ⛔ The instrument cannot see completion from stdout alone; `[MAINTAIN] done … REACHED`")
print("  lives in the debug log. Treat a non-zero here as 'go read the debug log', never as proof.")
print("=" * 96)
