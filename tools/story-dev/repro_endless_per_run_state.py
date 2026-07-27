"""Regression: ENDLESS LOOP must give every run a clean slate, and must not call a
failed run "finished".

FROM REAL DATA — the user's x4 bundle `P1 - P4 x4 LOGs 20260726-231412`.

`StoryEndlessResetMode.run()` loops `yield from super().run()` on the SAME mode object,
so `StoryMode.__init__` runs ONCE PER BATCH. Every per-run counter used to be assigned
there, under a comment asserting the opposite ("Instance state ... so ENDLESS RESET's
next run starts with a clean slate"). Two measured consequences:

  1. `_rival_attempts` (cap `RIVAL_MAX_ATTEMPTS = 3`) never reset, so it tripped on run 4
     of every lane and the bot handed itself to Manual at the Rustboro rival WITHOUT
     FIGHTING IT. P1 run 8's debug log is the proof: zero `BattleOutcome.Lost` in the
     whole run, yet it ended

         Story: couldn't beat the Rustboro rival in 3 tries ... handing to manual

     Cost: 16 of 20 P1 runs, 6 of 9 P2 runs, 5 of 8 P3 runs — all dead at the same beat.

  2. `_defeat_counts` carried losses between runs, so "give up on this boss" thresholds
     tripped on BORROWED defeats. Measured across run boundaries in the same bundle:
         MT_CHIMNEY   defeat #7 (run 1) -> #8 (run 2)
         FORTREE_GYM  defeat #8 (run 1) -> #9 (run 3)
         MAUVILLE_GYM defeat #3 (run 1) -> #4,#5,#6 (run 2) -> derailed "6 losses"
                      after only THREE real losses in run 2.

Separately, `outcome` defaulted to "finished" and only a raised `BotModeError` changed
it — but a derail can instead call `context.set_manual_mode()` and return normally. All
16 P1 "finished" runs were dead runs (several printed "finished (0 frames)"), so the
batch summary read ~80% success against a true ~20%.

No emulator needed — this drives the REAL StoryMode class with mgba stubbed out.
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

from plugins.custom_modes import story_mode  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


# The per-run counters, and the value each must hold on a fresh run.
PER_RUN_STATE = {
    "_rival_attempts": 0,
    "_defeat_counts": {},
    "_loss_ko_history": {},
    "_loss_seq": 0,
    "_training_unreachable": set(),
    "_derails": 0,
    "_last_defeat_key": None,
    "_last_derail_sig": None,
    "_whiteout_pending": False,
    "_ki15_nudge_stable": 0,
    "_ki15_nudge_pos": None,
    "_reached_end_of_content": False,
}

print("== the mode exposes a per-run reset (not just __init__) ==")
check(hasattr(story_mode.StoryMode, "reset_per_run_state"),
      "StoryMode.reset_per_run_state exists")
if failures:
    # Pre-fix code: everything below depends on this method existing. Report the
    # A/B cleanly instead of dying in a traceback.
    print("\nFAIL (1)\n  " + failures[0])
    print("  -> per-run state is only ever set in __init__, which the endless loop "
          "runs ONCE PER BATCH, not once per run.")
    sys.exit(1)

mode = story_mode.StoryMode.__new__(story_mode.StoryMode)
mode.reset_per_run_state()

print("\n== a fresh run starts every per-run counter at zero ==")
for attr, want in PER_RUN_STATE.items():
    got = getattr(mode, attr, "<missing>")
    check(got == want, f"{attr} == {want!r} (got {got!r})")

print("\n== ‼ THE BUG: three runs' worth of state, as it looked at run 4 ==")
# Exactly the state the real batch was in when P1 run 4 began.
mode._rival_attempts = 3
mode._defeat_counts = {(0, 25): 13, (24, 12): 7, (12, 1): 8}
mode._loss_seq = 35
mode._training_unreachable = {("a", "b", (1, 2))}
mode._derails = 2
cap = story_mode.StoryMode.RIVAL_MAX_ATTEMPTS
check(mode._rival_attempts >= cap,
      f"carried-over attempts ({mode._rival_attempts}) are at the cap ({cap})")
# This is the exact predicate at the rival gate: `attempts + 1 > cap` -> give up.
check(mode._rival_attempts + 1 > cap,
      "WITHOUT a reset, the very next rival encounter gives up without fighting")

print("\n== the reset clears it, so run 4 fights again ==")
mode.reset_per_run_state()
check(mode._rival_attempts + 1 <= cap,
      f"after reset, attempt 1 of {cap} is allowed (fights instead of quitting)")
for attr, want in PER_RUN_STATE.items():
    got = getattr(mode, attr, "<missing>")
    check(got == want, f"{attr} cleared back to {want!r} (got {got!r})")

print("\n== defeat counts do not leak into the next run's give-up threshold ==")
mode._defeat_counts[(10, 0)] = 3          # 3 losses to Wattson in run N
mode.reset_per_run_state()
check(mode._defeat_counts.get((10, 0), 0) == 0,
      "MAUVILLE_GYM defeat count is 0 at the start of run N+1 (was carrying #3)")

print("\n== the endless loop actually CALLS the reset, before handing to the story ==")
src = (SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(encoding="utf-8")
loop = src[src.index("class StoryEndlessResetMode"):]
check("self.reset_per_run_state()" in loop,
      "StoryEndlessResetMode calls reset_per_run_state()")
# ‼ Scope to the body of `run()` before looking for these. Anchoring on bare text over the
# whole class made this repro fail on an unrelated (and correct) change: it matched
# `super().run()` inside `_run_with_frame_budget`'s DOCSTRING, which is defined above `run`.
# Assert the ordering property, not the call syntax.
runbody = loop[loop.index("\n    def run(self):"):]
i_reset = runbody.index("self.reset_per_run_state()")
i_drive = runbody.index("_run_with_frame_budget")
check(i_reset < i_drive, "the reset happens BEFORE the run is driven, not after it")
i_while = runbody.index("while target == 0 or completed < target:")
check(i_while < i_reset, "and INSIDE the per-run loop, not once before it")

print("\n== a run that hands itself to Manual is not reported as 'finished' ==")
check('outcome = "stopped: handed to Manual mid-run' in loop or
      "outcome = 'stopped: handed to Manual mid-run" in loop,
      "there is a 'stopped' outcome for the set_manual_mode() exit path")
i_else = loop.index("\n            else:")
i_stopped = loop.index("handed to Manual mid-run")
check(i_else < i_stopped,
      "it hangs off the try/except `else` (only when run() returned normally)")

print("\n== ‼ a GENUINE completion must still say 'finished', not 'stopped' ==")
# The end-of-built-content return calls set_manual_mode() and returns normally, exactly
# like a give-up does. Distinguishing them by "did we end up in Manual?" alone would
# relabel real successes as failures — P2 run 1 of bundle `20260726-231412` reached the
# Feather Badge this way. The mode flags the real completion explicitly.
check("_reached_end_of_content" in src,
      "StoryMode has an explicit end-of-content flag")
i_flag = src.index("self._reached_end_of_content = True")
i_manual = src.index("context.set_manual_mode()", i_flag - 400)
check(i_flag < i_manual,
      "the flag is set BEFORE the completion's set_manual_mode()/return")
check("_reached_end_of_content = False" in src,
      "and it is cleared per run by reset_per_run_state (else run N+1 inherits a win)")
check("not getattr(self, \"_reached_end_of_content\", False)" in loop,
      "the endless loop only says 'stopped' when the run did NOT reach the end")

# It must be reset per run, or one completion would mark every later run complete.
mode._reached_end_of_content = True
mode.reset_per_run_state()
check(mode._reached_end_of_content is False,
      "a completed run does not leave the next run pre-marked as complete")

print("\n== REPRODUCTION: the batch lifecycle, both ways, 8 runs ==")
# Version-independent simulation of the two object lifetimes, using the REAL cap and
# the REAL gate predicate. Shows the observed failure directly: with init-once state,
# every run from #4 quits at the rival having lost nothing.
def simulate(reset_each_run: bool, runs: int = 8):
    attempts = 0
    fought = []
    for run in range(1, runs + 1):
        if reset_each_run:
            attempts = 0
        attempts += 1                      # the gate increments on ENTRY
        if attempts > cap:
            continue                       # gave up without fighting
        fought.append(run)
    return fought

old = simulate(reset_each_run=False)       # __init__ once per BATCH  (the bug)
new = simulate(reset_each_run=True)        # reset once per RUN       (the fix)
print(f"     init-once-per-batch : rival fought on runs {old}")
print(f"     reset-once-per-run  : rival fought on runs {new}")
check(old == [1, 2, 3],
      f"BUG reproduced — only runs 1-3 ever fight the rival (got {old})")
check(new == [1, 2, 3, 4, 5, 6, 7, 8],
      f"FIXED — every run fights the rival (got {new})")
check(4 not in old and 4 in new,
      "run 4 is the exact boundary the user's bundle died on, in all three lanes")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
