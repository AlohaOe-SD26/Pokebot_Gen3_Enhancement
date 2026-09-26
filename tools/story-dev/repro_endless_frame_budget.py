"""Regression: a wedged or looping run must be STOPPED by the frame budget, not merely
reported after it finally returns.

FROM REAL DATA — the user's x4 bundle `20260727-063751`. `MAX_FRAMES_PER_RUN` was checked
only AFTER `super().run()` returned, so it could describe a runaway run but never end one.
Its own docstring promised the opposite ("so a run that neither finishes nor raises cannot
hold the batch forever"). Three of four lanes then did exactly that, costing the batch more
than half its wall-clock:

  * P3 run 1  — HARD HANG at the Weather Institute. 27,000,000 frames / ~6.5 h of identical
                heartbeats: `state=3 controllable=False`, frozen at ROUTE 119(32,1) (10,10).
                ZERO STUCK dumps in that stretch, so the global watchdog never fired either.
  * P1 run 7  — 19.9M frames spinning Route 103 / healing at Oldale, forever.
  * P2 run 35 — 13.4M frames of the same on Route 116.
  * P4 run 12 — DID report `frame-cap (7,545,828 > 3,500,000)` … after burning >2x the cap.

P1/P2 are LIVELOCKS, not hangs — they produce real encounters and battles, so no
"nothing progressed" detector can ever catch them. Only a budget can.

No emulator needed — this drives the REAL `_run_with_frame_budget` against a fake emulator
whose frame counter we control, including the mid-run reset that made the old post-hoc
check unenforceable.
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
from modules.context import context  # noqa: E402
from modules.modes import BotModeError  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


CAP = story_mode.StoryEndlessResetMode.MAX_FRAMES_PER_RUN
mode = story_mode.StoryEndlessResetMode.__new__(story_mode.StoryEndlessResetMode)


class FakeEmulator:
    """Frame counter we drive by hand. `per_yield` frames elapse per generator step."""

    def __init__(self, start=0, per_yield=1000):
        self.frame = start
        self.per_yield = per_yield

    def get_frame_count(self):
        return self.frame


def drive(inner, start_frame, emu, max_steps=200_000):
    """Run the budget wrapper to completion; return (steps, error_or_None)."""
    context.emulator = emu
    gen = mode._run_with_frame_budget(inner, start_frame)
    steps = 0
    try:
        while steps < max_steps:
            next(gen)
            steps += 1
            emu.frame += emu.per_yield
    except StopIteration:
        return steps, None
    except BotModeError as exc:
        return steps, exc
    return steps, RuntimeError("did not terminate within max_steps")


def hung_run():
    """P3: yields forever, never progresses, never raises."""
    while True:
        yield


def finite_run(n):
    for _ in range(n):
        yield


print("== ‼ REPRODUCTION: a hung run is STOPPED, not merely reported ==")
emu = FakeEmulator(start=0, per_yield=1000)
steps, err = drive(hung_run(), 0, emu)
check(isinstance(err, BotModeError),
      f"the hang raises BotModeError instead of running forever (got {type(err).__name__})")
check(emu.frame <= CAP + emu.per_yield * mode.BUDGET_CHECK_INTERVAL,
      f"it is stopped near the cap, not at 27M frames (stopped at {emu.frame:,}, cap {CAP:,})")
print(f"     stopped after {steps:,} steps / {emu.frame:,} frames (cap {CAP:,})")
check("frame budget exhausted" in str(err), f"the derail says why: {str(err)[:70]}")

print("\n== a LIVELOCK is caught too — activity does not exempt it ==")
def livelock_run():
    # P1/P2: real work every step (encounters, battles), just no story progress.
    n = 0
    while True:
        n += 1
        yield n
emu = FakeEmulator(start=0, per_yield=1000)
steps, err = drive(livelock_run(), 0, emu)
check(isinstance(err, BotModeError),
      "a busy-but-unproductive run is bounded by the budget, not by a progress detector")

print("\n== ‼ the MID-RUN EMULATOR RESET does not disable the budget ==")
# The hard reset happens INSIDE the run and get_frame_count() restarts with it, so the
# counter goes backwards. A naive `now - start_frame` goes negative and nothing is ever
# over cap — the exact trap that made the old post-hoc check unenforceable.
class ResettingEmulator(FakeEmulator):
    def __init__(self):
        super().__init__(start=900_000, per_yield=1000)
        self.did_reset = False

    def get_frame_count(self):
        if not self.did_reset and self.frame > 950_000:
            self.did_reset = True
            self.frame = 0          # emulator reset: counter restarts
        return self.frame

emu = ResettingEmulator()
steps, err = drive(hung_run(), 900_000, emu)
check(emu.did_reset, "the fake emulator really did reset mid-run")
check(isinstance(err, BotModeError),
      f"the budget still fires after a mid-run reset (got {type(err).__name__})")
check(emu.frame <= CAP + emu.per_yield * mode.BUDGET_CHECK_INTERVAL,
      f"and it measures frames since the RESET, not a negative elapsed ({emu.frame:,})")

print("\n== a normal run is NOT disturbed ==")
emu = FakeEmulator(start=0, per_yield=1)
steps, err = drive(finite_run(5000), 0, emu)
check(err is None, f"a short run completes normally (got {type(err).__name__ if err else 'None'})")
check(steps == 5000, f"every yield is passed through ({steps} of 5000)")

emu = FakeEmulator(start=0, per_yield=100)   # 5000 steps -> 500k frames, well under cap
steps, err = drive(finite_run(5000), 0, emu)
check(err is None, "a long-but-legal run is not cut short")

print("\n== the inner generator is closed when the wrapper unwinds (parking a batch) ==")
closed = {"yes": False}
def closing_run():
    try:
        while True:
            yield
    except GeneratorExit:
        closed["yes"] = True
        raise
context.emulator = FakeEmulator(per_yield=1)
gen = mode._run_with_frame_budget(closing_run(), 0)
next(gen)
gen.close()
check(closed["yes"], "closing the wrapper closes the story generator")

print("\n== ⭐ 2026-09-26: the REPORTED run length is the run's, not 'this end minus last end' ==")
# Every endless run hard-resets INSIDE the run, so `start_frame` belongs to the previous
# emulator session. The old outcome line printed `now - start_frame`: e.g. a §Ch23 derail
# logged at "(187,804 frames)", impossible from a NEW GAME. The wrapper now publishes the
# same re-based count it enforces.
emu = ResettingEmulator()                      # previous session ended at 900k, then reset
steps, err = drive(finite_run(3000), 900_000, emu)
since_reset = emu.frame                        # counter restarted at 0 on the reset
check(err is None, "a finite run across the mid-run reset completes")
reported = getattr(mode, "_run_elapsed_frames", None)   # absent on the pre-fix code => FAIL, not crash
check(reported == since_reset,
      f"reported = frames since the RESET ({reported!r} == {since_reset:,})")
check(reported is not None and reported != max(0, emu.frame - 900_000),
      "and NOT the old 'this end minus the previous session's end' figure")

print("\n== ⭐ 2026-09-26: once §Ch24 OWNS the run, the cap extends to cover the league grind ==")
from modules.story import pokemon_league  # noqa: E402

PURSE = pokemon_league.CH24_TRAIN_PURSE_FRAMES
ALLOW = getattr(mode, "CH24_GAUNTLET_ALLOWANCE_FRAMES", 0)
if not hasattr(mode, "_frame_cap_for_this_run"):   # the pre-fix code: report, then test the RUN anyway
    check(False, "`_frame_cap_for_this_run` exists (the §Ch24-aware cap)")
    mode._frame_cap_for_this_run = lambda: mode.MAX_FRAMES_PER_RUN
mode.BUDGET_CHECK_INTERVAL = 64                # instance override: 64k-frame granularity below
GRAN = 1000 * mode.BUDGET_CHECK_INTERVAL
check(PURSE >= 4_500_000,
      f"the purse still covers the measured ~4.5M-frame grind (CH24_TRAIN_PURSE_FRAMES={PURSE:,})")
mode._ch24_owns_run = False
check(mode._frame_cap_for_this_run() == CAP, "unlatched: the cap is the base cap")
mode._ch24_owns_run = True
check(mode._frame_cap_for_this_run() == CAP + PURSE + ALLOW,
      f"latched: base + purse + allowance ({mode._frame_cap_for_this_run():,})")


def latching_run(latch_at_step):
    """A hung run that §Ch24 latches part-way through, as `train_for_league()` does."""
    n = 0
    while True:
        n += 1
        if n == latch_at_step:
            mode._ch24_owns_run = True
        yield


def run_latched(latch_at_step):
    mode._ch24_owns_run = False
    emu = FakeEmulator(start=0, per_yield=1000)
    _steps, err = drive(latching_run(latch_at_step), 0, emu, max_steps=100_000)
    return emu.frame, err


LATCH_STEP = 4_000                             # latch at ~4M frames: under the base cap
stop_at, err = run_latched(LATCH_STEP)
check(isinstance(err, BotModeError), "a latched run that wedges is STILL stopped (the extension is finite)")
check(stop_at > CAP + GRAN,
      f"it is NOT stopped at the base cap ({stop_at:,} > {CAP + GRAN:,}) — the grind survives")
check(stop_at <= CAP + PURSE + ALLOW + GRAN,
      f"and it stops at base + purse + allowance ({stop_at:,} <= {CAP + PURSE + ALLOW + GRAN:,})")

print("\n== FAULT ARM: the discriminator really discriminates (extension removed => base cap) ==")
_real_cap = mode._frame_cap_for_this_run
mode._frame_cap_for_this_run = lambda: CAP     # the pre-2026-09-26 behaviour
fault_stop, fault_err = run_latched(LATCH_STEP)
mode._frame_cap_for_this_run = _real_cap
check(isinstance(fault_err, BotModeError) and fault_stop <= CAP + GRAN,
      f"with the extension disabled the SAME run dies at the base cap ({fault_stop:,})")
check(fault_stop < stop_at, "so the two arms differ — the latched check above is not vacuous")

print("\n== an UNLATCHED livelock is still ended at the base cap (early game is not loosened) ==")
mode._ch24_owns_run = False
emu = FakeEmulator(start=0, per_yield=1000)
steps, err = drive(livelock_run(), 0, emu, max_steps=100_000)
check(isinstance(err, BotModeError) and emu.frame <= CAP + GRAN,
      f"unlatched livelock stopped at the base cap ({emu.frame:,})")
del mode.BUDGET_CHECK_INTERVAL                 # restore the class value for the source checks

print("\n== the budget is enforced DURING the run, not after it returns ==")
import io  # noqa: E402
import tokenize  # noqa: E402


def _code_only(text: str) -> str:
    """The source with every COMMENT token removed. ⛔ A gate must not fire on a MENTION: the fix's
    own comment quotes the old `get_frame_count() - start_frame` expression, and a textual check
    that sees it would teach the reader to bypass the gate (CLAUDE.md session discipline #6)."""
    toks = [t for t in tokenize.generate_tokens(io.StringIO(text).readline)
            if t.type != tokenize.COMMENT]
    return tokenize.untokenize(toks)


src = _code_only((SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(encoding="utf-8"))
loop = src[src.index("class StoryEndlessResetMode"):]
check("yield from self._run_with_frame_budget(super().run()" in loop,
      "the endless loop drives the story through the budget wrapper")
check(loop.index("_run_with_frame_budget") < loop.index("outcome = f\"frame-cap"),
      "the in-run budget exists alongside the post-hoc report, not instead of it")
post_hoc = loop[loop.index("def run(self)"):]
check("_run_elapsed_frames" in post_hoc and "get_frame_count() - start_frame" not in post_hoc,
      "the outcome line reports the wrapper's re-based count, not `now - start_frame`")
check("self._frame_cap_for_this_run()" in post_hoc,
      "the post-hoc 'frame-cap' label uses the SAME effective cap the wrapper enforced")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
