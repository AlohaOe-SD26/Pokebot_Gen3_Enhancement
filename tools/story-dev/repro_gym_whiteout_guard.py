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
  [3] DOES NOT FIRE WHEN IT SHOULD NOT — unpatched, the same call walks normally and reaches the
      leaders. Without this control, "it raised" proves nothing.
  [4] THE RECOVERY ACTUALLY RETRIES — `do_mossdeep_gym_chapter` is run against a
      `walk_to_the_leaders` that always raises `BotModeError`, and must make THREE attempts and
      then report all three, rather than dying on the first.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_gym_whiteout_guard.py
"""

import pathlib
import sys

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

context.emulator = LibmgbaEmulator(profile, lambda: None)
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
    exercises the IN-LOOP guard rather than the cheap one at function entry."""
    calls["n"] += 1
    return calls["n"] < 400


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
print("\n[3] CONTROL — unpatched, the same call must walk the route normally")
reset()
error = drive(mossdeep_gym.walk_to_the_leaders(verbose=False))
here = mossdeep_gym._tile()
record(
    "[3] the guard does NOT fire on the healthy path",
    error is None and here in mossdeep_gym.LEADER_APPROACH_TILES,
    f"ended at {here} with {type(error).__name__ + ': ' + str(error)[:120] if error else 'no error'}",
)

# ---------------------------------------------------------------- [4] the recovery retries
print("\n[4] RECOVERY — the chapter must RETRY three times, not die on the first failure")
reset()
real_walk = mossdeep_gym.walk_to_the_leaders
real_fight = mossdeep_gym.fight_the_leaders
attempts = {"n": 0}


def always_whiteout(*_args, **_kwargs):
    attempts["n"] += 1
    raise BotModeError("injected: pretending a whiteout ended attempt %d" % attempts["n"])
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
    "[4] the chapter retried 3 times and reported every attempt",
    attempts["n"] == 3 and isinstance(error, BotModeError) and "3 attempts" in str(error),
    f"attempts={attempts['n']} (want 3), error={type(error).__name__}: {str(error)[:160]}",
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
