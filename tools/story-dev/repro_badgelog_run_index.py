"""Regression: `run_index` must advance by ONE per run, not two.

FROM REAL DATA — the user's x4 bundle `20260726-231412`. P1 completed 19 runs; its
`badge-log.json` carried run_index 1, 3, 5, 7 … 37. Nineteen runs, all-odd indices,
exactly 2 per run. Same shape in P2/P3/P4.

`reset_for_new_run()` has two legitimate callers:
  * `modules/main.py`, when the frame counter goes backwards (i.e. the emulator reset);
  * `StoryEndlessResetMode`, which knows exactly where its run boundaries are.

The FIRST fix tried to dedupe on adjacency — "if a reset already happened and no poll
has occurred since, this is the same boundary" (`_run_index and _last_poll_frame < 0`).
That could never work, and this repro pins down why: the ORDER is

    mode reset  ->  [thousands of polls]  ->  emulator hard reset  ->  main.py reset

because the mode signals BEFORE `super().run()` while the hard reset happens INSIDE it.
The two calls are never adjacent, so `_last_poll_frame` is always a real frame by the
time the second one lands, and both increment.

The fix is OWNERSHIP: a mode that knows its own boundaries passes `authoritative=True`,
and main.py's heuristic stands down for the rest of the process.

No emulator needed.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules import badge_log  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


def fresh():
    """Reset the module back to process-start state."""
    badge_log._run_index = 0
    badge_log._last_poll_frame = -1
    badge_log._mode_is_authoritative = False


def poll(frame):
    """Stand in for the per-frame poll that runs between the two reset calls."""
    badge_log._last_poll_frame = frame


print("== ‼ REPRODUCTION: what each dedupe strategy yields over P1's 19 real runs ==")
# Version-independent model of both strategies. The bundle proves that in production
# NEITHER of the two calls was ever deduped (19 runs produced 19 odd indices, i.e. a
# stride of 2), so frames always elapsed between them — model that.
#
# This asserts the SHAPE (double-counting vs one-per-run), not the literal 37: the exact
# interleaving that produced 37 rather than 38 is not observable from the logs, and
# pinning a number reverse-engineered from a guess would be a fake proof.
def _count(strategy: str, runs: int = 19) -> int:
    idx, last_poll, owned = 0, -1, False
    for run in range(1, runs + 1):
        for authoritative in (True, False):
            if strategy == "ownership":
                if authoritative:
                    owned = True
                elif owned:
                    continue
            elif strategy == "adjacency":
                if idx and last_poll < 0:
                    continue
            idx += 1
            last_poll = 50_000 * run                 # frames elapse before the next call
    return idx

adj, own = _count("adjacency"), _count("ownership")
print(f"     adjacency (old)  -> {adj}   for 19 runs  (bundle: stride of 2, ending at 37)")
print(f"     ownership (new)  -> {own}   for 19 runs")
check(adj == 38, f"BUG reproduced: the old strategy counts ~2 per run (got {adj})")
check(own == 19, f"FIXED: ownership yields exactly one index per run (got {own})")

print("\n== ‼ the same, against the REAL reset_for_new_run ==")
fresh()
for run in range(1, 20):                       # P1 completed 19 runs
    badge_log.reset_for_new_run(1, authoritative=True)   # mode, before super().run()
    poll(50_000 * run)                                    # the run actually plays
    badge_log.reset_for_new_run(0)                        # main.py, on the hard reset
got = badge_log._run_index
print(f"     19 runs -> run_index = {got}")
check(got == 19, f"run_index advances once per run (got {got}, the bundle showed 37)")

print("\n== the old adjacency test is shown to be unable to catch this ==")
# `_last_poll_frame` is a real frame at the moment main.py's call lands, every time.
check(badge_log._last_poll_frame >= 0,
      "a poll always separates the two calls, so adjacency-dedupe never fires")

print("\n== the ADJACENT race at batch start is one boundary, not two ==")
# The realistic race: the emulator resets as the mode starts up, so main.py's detection
# fires moments before the mode declares ownership, with NOTHING played in between.
# (The reverse-with-a-full-run-between ordering is not a real sequence: the mode signals
# at the top of iteration k, and main.py's detection fires inside super().run() after.)
fresh()
badge_log.reset_for_new_run(0)                        # main.py wins the startup race
badge_log.reset_for_new_run(1, authoritative=True)    # mode takes ownership immediately
check(badge_log._run_index == 1,
      f"batch start counts as run 1, not 2 (got {badge_log._run_index})")
for run in range(2, 6):                               # and the batch proceeds normally
    poll(50_000 * run)
    badge_log.reset_for_new_run(0)
    badge_log.reset_for_new_run(1, authoritative=True)
check(badge_log._run_index == 5,
      f"5 runs -> run_index 5 (got {badge_log._run_index})")

print("\n== a NON-endless run still gets main.py's fallback (no regression) ==")
fresh()
for run in range(1, 4):
    badge_log.reset_for_new_run(0)     # only main.py ever calls it here
    poll(50_000 * run)
check(badge_log._run_index == 3,
      f"main.py alone still counts runs (got {badge_log._run_index})")

print("\n== every record still carries a run_index, and it starts at 1 ==")
fresh()
badge_log.reset_for_new_run(1, authoritative=True)
check(badge_log._run_index == 1, f"first run is index 1 (got {badge_log._run_index})")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
