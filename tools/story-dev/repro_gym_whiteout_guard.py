"""§Ch18 — PROVE the Mossdeep Gym executor survives a whiteout mid-route.

‼ WHY THIS EXISTS. An adversarial review of the gym executor found a real defect that the driven
PASS could never have caught, because the PASS had `whiteouts=0`: `walk_to_the_leaders()` checked
the gym map ONCE, at entry, and then reasoned in the gym's local coordinates forever. A whiteout —
the realistic outcome of losing one of the nine trainer battles that route walks through — deposits
the player in front of a Pokémon Center, on a different map, whose local `(x, y)` is a perfectly
ordinary-looking pair of numbers. The old code would have fed those to `solve_route` and either
misdiagnosed the failure ("the simulated statue map is wrong") or found a phantom route and started
pressing buttons inside the Pokémon Center.

It also raised `RuntimeError`, while `do_mossdeep_gym_chapter` only catches `BotModeError` — so the
whole re-enter-and-re-solve recovery could never have fired even if the error had been correct.

A claim that this is now fixed is worth nothing without a fault injection, so this file injects one.

WHAT IT CHECKS, two-sided on purpose — a guard that always fires is as useless as one that never
does:
  [1] FIRES WHEN IT SHOULD — with `_on_gym_map` forced False part-way through the route, the walk
      raises, and the message names a WHITEOUT rather than blaming the statue model.
  [2] IS THE RIGHT TYPE — the error is a `BotModeError`. This is not pedantry: the chapter's retry
      loop catches exactly that type, so a `RuntimeError` here silently disables the recovery.
  [3] DOES NOT FIRE WHEN IT SHOULD NOT — unpatched, the same call walks a healthy PREFIX of the
      route without raising and makes real progress. Without this control, "it raised" proves
      nothing: a guard that always fires would pass check [1].

‼ CHECK [3] IS A BOUNDED PREFIX, NOT THE WHOLE ROUTE, AND THAT IS A HARD CONSTRAINT RATHER THAN
LAZINESS. **Battle handling does not run inside a bot mode's generator** — it lives in the main
loop's listeners (`modules/battle_fault.py:5`; the driven run's log shows
`CONTROLLER -> TrainerApproachListener` and `CONTROLLER -> BattleListener.fight`). Driving a
generator by hand, as this file does, has no listeners at all, so the moment one of the gym's nine
trainers starts a battle there is nothing that can win it and the walk stalls until its frame
budget runs out. The first version of this repro tried to walk the full route here and sat for
45 minutes doing exactly that.
⇒ The FULL healthy route is proven elsewhere, by the thing that does have listeners: the driven
`--driver mossdeepgym` PASS (`at_leaders=True at=(23,8) whiteouts=0`, 117 steps, one plan). This
file's job is only the guard's two-sided behaviour, and it says so rather than overclaiming.
  [4] THE RECOVERY ACTUALLY RETRIES — `do_mossdeep_gym_chapter` is run against a
      `walk_to_the_leaders` that always raises `BotModeError`, and must make THREE attempts and
      then report all three, rather than dying on the first.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_gym_whiteout_guard.py
"""

import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)  # ‼ is_test_run: without it the
    # emulator registers an atexit that OVERWRITES shared `profiles/<name>/current_state.ss1`
    # and writes a states/ snapshot. Pass 2 fixed this for the two KI-76 probes; PASS 4
    # (2026-08-22) found SEVEN MORE still writing — `profiles/repro-ml/states/` had reached
    # 2,820 files / 160 MB. A probe that mutates shared state is not observe-only.
context.audio = False
context.video = False

from modules.modes import BotModeError
from modules.story import mossdeep_gym

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "in_mossdeep_gym.ss1"
MAX_FRAMES = 400_000

line = "=" * 96
results: list[tuple[str, bool, str]] = []


def record(label: str, passed: bool, detail: str) -> None:
    results.append((label, passed, detail))
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}\n         {detail}")


def drive(generator, *, limit: int = MAX_FRAMES):
    """Run a bot generator against the emulator and return the exception it raised, or None."""
    frames = 0
    try:
        for _ in generator:
            context.emulator.run_single_frame()
            frames += 1
            if frames > limit:
                return TimeoutError(f"generator did not finish within {limit} frames")
    except Exception as error:  # noqa: BLE001 — capturing the exception IS the measurement here
        return error
    return None


def reset() -> None:
    context.emulator.load_save_state(ANCHOR.read_bytes())
    for _ in range(90):
        context.emulator.run_single_frame()


print(line)
print("REPRO — the gym executor must survive a whiteout mid-route")
print(line)

# ---------------------------------------------------------------- [1] and [2]: fault injected
print("\n[1]+[2] FAULT INJECTION — force the player 'off the gym map' part-way through the route")
reset()
real_on_gym_map = mossdeep_gym._on_gym_map
calls = {"n": 0}


def flaky_on_gym_map() -> bool:
    """True until the route is well under way, then False forever — a whiteout, in effect.

    The threshold is high enough that the puzzle has been built and several steps walked, so this
    exercises the IN-LOOP guard rather than the cheap one at function entry.

    ⛔ RECALIBRATED 400 → 80 ON 2026-08-26, AND THE REASON IS A LESSON ABOUT THIS FAULT'S UNITS.
    The threshold counts CALLS, and calls-per-step is a property of the WALKER, not of the route:
    under the old `_step_towards` a single direction change stalled ~600 frames with one
    `_on_gym_map()` call per frame, so 400 calls landed INSIDE STEP ~1. The `#26-mossdeeppuzzlespeed`
    pre-turn removed that stall (~24-45 calls/step now), silently moving the SAME threshold to step
    ~9-16 — PAST THE FIRST TRAINER'S SIGHT LINE. A battle started, nothing here can win one (no
    listeners), and `drive()` burned its full 400k-frame budget → TimeoutError instead of the
    expected BotModeError → checks [1]+[2] failed and the gate hit the suite's 900s bound. The
    PRODUCTION guard was fine the whole time; the REPRO'S calibration was coupled to the walker's
    frame cost. 80 calls ≈ entry guard + puzzle build + ~2-3 steps under the new walker: "several
    steps walked", still short of every trainer. ⇒ A FAULT KEYED TO A FRAME-DERIVED COUNT MUST BE
    RE-EXAMINED WHENEVER THE THING IT INSTRUMENTS CHANGES SPEED."""
    calls["n"] += 1
    return calls["n"] < 80


mossdeep_gym._on_gym_map = flaky_on_gym_map
try:
    error = drive(mossdeep_gym.walk_to_the_leaders(verbose=False))
finally:
    mossdeep_gym._on_gym_map = real_on_gym_map

raised = error is not None
message = str(error) if error else "<no exception>"
record(
    "[1] the guard FIRES when the player leaves the gym mid-route",
    raised and "WHITEOUT" in message.upper(),
    f"{type(error).__name__ if error else 'None'}: {message[:180]}",
)
record(
    "[2] the error is a BotModeError, so the chapter's retry can catch it",
    isinstance(error, BotModeError),
    f"type is {type(error).__name__} (must be BotModeError, not RuntimeError — a RuntimeError "
    "would bypass do_mossdeep_gym_chapter's except clause and kill the chapter)",
)

# ---------------------------------------------------------------- [3] control: healthy path
print("\n[3] CONTROL — unpatched, a healthy PREFIX of the route must raise nothing and make progress")
reset()
start_tile = mossdeep_gym._tile()
# Bounded on purpose — see the module docstring. Without the main loop's battle listeners this
# harness cannot win a gym trainer battle, so the walk is exercised only as far as it reliably
# goes unattended. Long enough to cover the entry guard, the puzzle build, several steps and at
# least one warp; short enough to finish in well under a minute.
error = drive(mossdeep_gym.walk_to_the_leaders(verbose=False), limit=6_000)
here = mossdeep_gym._tile()
timed_out = isinstance(error, TimeoutError)
record(
    "[3] the guard does NOT fire on the healthy path, and the walk progresses",
    timed_out and here != start_tile,
    f"walked {start_tile} -> {here} over 6,000 frames; outcome = "
    f"{'hit the frame budget with no error raised (expected)' if timed_out else type(error).__name__ + ': ' + str(error)[:140] if error else 'the route completed'}",
)

# ---------------------------------------------------------------- [4] the recovery retries
print("\n[4] RECOVERY — on a NON-whiteout failure the chapter must RETRY three times")
# ‼ RENAMED AND RE-SCOPED 2026-08-12 (KI-67). This check used to be described as "pretending a
# whiteout", and it never was one: it injects a plain `BotModeError` with the abort latch CLEAR,
# which is a nav/scene failure, not a defeat. The distinction became load-bearing when the whiteout
# unwind was given its own identity — a REAL whiteout must now escape on attempt 1 (see [5]) — so
# leaving the old wording here would have left a green test documenting a contract that no longer
# holds. The 3-attempt behaviour it asserts is still correct FOR THIS CASE, which is why the check
# stays rather than being deleted.
reset()
real_walk = mossdeep_gym.walk_to_the_leaders
real_fight = mossdeep_gym.fight_the_leaders
attempts = {"n": 0}


def always_whiteout(*_args, **_kwargs):
    attempts["n"] += 1
    raise BotModeError("injected: an ordinary (non-whiteout) failure on attempt %d" % attempts["n"])
    yield  # pragma: no cover — makes this a generator function, as the real one is


def never_called(*_args, **_kwargs):
    raise AssertionError("fight_the_leaders must not run when the walk failed")
    yield  # pragma: no cover


mossdeep_gym.walk_to_the_leaders = always_whiteout
mossdeep_gym.fight_the_leaders = never_called
try:
    error = drive(mossdeep_gym.do_mossdeep_gym_chapter(), limit=20_000)
finally:
    mossdeep_gym.walk_to_the_leaders = real_walk
    mossdeep_gym.fight_the_leaders = real_fight

record(
    "[4] a NON-whiteout failure is retried 3 times and every attempt is reported",
    attempts["n"] == 3 and isinstance(error, BotModeError) and "3 attempts" in str(error),
    f"attempts={attempts['n']} (want 3), error={type(error).__name__}: {str(error)[:160]}",
)

# ---------------------------------------------------------------------------------------------
print("\n[5] A REAL WHITEOUT must escape on attempt 1, NOT consume the retry budget (KI-67)")
# ‼ THE OTHER HALF OF [4], AND THE ONE THAT WAS MISSING. The abort latch is cleared ONLY by
# `StoryMode.run`, so a chapter that caught the abort and retried in place ran straight into the
# next `_check_abort()` and died instantly — one whiteout burned all three attempts and reported
# two failures that never happened. Re-raising hands the retry to the layer that can actually
# perform it: `StoryMode.run` clears the latch, rides out the respawn and re-runs `_play()`.
reset()
from modules.story.early_game import StoryAbort, set_story_abort  # noqa: E402

wo_attempts = {"n": 0}


def whiteout_abort(*_args, **_kwargs):
    wo_attempts["n"] += 1
    set_story_abort(True)
    from modules.story.early_game import _check_abort

    _check_abort()          # exactly how a real whiteout surfaces inside a segment
    yield  # pragma: no cover


mossdeep_gym.walk_to_the_leaders = whiteout_abort
mossdeep_gym.fight_the_leaders = never_called
try:
    wo_error = drive(mossdeep_gym.do_mossdeep_gym_chapter(), limit=20_000)
finally:
    mossdeep_gym.walk_to_the_leaders = real_walk
    mossdeep_gym.fight_the_leaders = real_fight
    set_story_abort(False)   # ‼ the latch is PROCESS-GLOBAL — never leave it set for the next check

record(
    "[5] a whiteout abort escapes after ONE attempt instead of burning all three",
    wo_attempts["n"] == 1 and isinstance(wo_error, StoryAbort),
    f"attempts={wo_attempts['n']} (want 1), error={type(wo_error).__name__}: {str(wo_error)[:120]}",
)

# ---------------------------------------------------------------- verdict
print("\n" + line)
print("VERDICT")
print(line)
passed = sum(1 for _, ok, _ in results if ok)
print(f"\n  {passed} / {len(results)} checks pass\n")
for label, ok, _ in results:
    print(f"    {'PASS' if ok else 'FAIL'}  {label}")
print(f"\n  {'RESULT: ALL PASS' if passed == len(results) else 'RESULT: FAILURES PRESENT'}")
print(line)
sys.exit(0 if passed == len(results) else 1)
