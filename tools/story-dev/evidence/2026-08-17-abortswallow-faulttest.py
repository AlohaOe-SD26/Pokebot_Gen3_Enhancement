r"""SCRATCH — FAULT-TEST the new `#24-abortswallow` guards WITHOUT the emulator.

The guard is `reraise_if_aborting(error)`, which re-raises ONLY when the module latch is set. So the
decisive question is behavioural and testable in isolation:
  * latch CLEAR -> the handler still swallows (no regression to normal operation)  [the control arm]
  * latch SET   -> the abort propagates instead of being swallowed                 [the fix]
⛔ And the counter_hunt narrowing: a PathFindingError must NOT be re-raised even with the latch set,
because StoryMode.run catches only BotModeError and a leaked latch is worse than the silence.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot")))
from modules.modes import BotModeError
from modules.map_path import PathFindingError
import modules.story.early_game as eg

print("StoryAbort is a BotModeError :", issubclass(eg.StoryAbort, BotModeError))
print("PathFindingError is a BotModeError:", issubclass(PathFindingError, BotModeError), " (must be False)")

def guarded(err, latch):
    """Reproduce the shipped handler shape: reraise_if_aborting as the first statement."""
    eg.set_story_abort(latch)
    try:
        try:
            raise err
        except BotModeError as error:
            eg.reraise_if_aborting(error)
            return "SWALLOWED"
    except BotModeError:
        return "PROPAGATED"
    finally:
        eg.set_story_abort(False)

def counter_hunt_shape(err, latch):
    """Reproduce counter_hunt's `except Exception` + isinstance narrowing."""
    eg.set_story_abort(latch)
    try:
        try:
            raise err
        except Exception as error:
            if isinstance(error, BotModeError):
                eg.reraise_if_aborting(error)
            return "SWALLOWED"
    except BaseException:
        return "PROPAGATED"
    finally:
        eg.set_story_abort(False)

print("\n--- early_game handler shape (except BotModeError):")
for label, err, latch, want in [
    ("CONTROL  ordinary BotModeError, latch CLEAR", BotModeError("route blocked"), False, "SWALLOWED"),
    ("FIX      StoryAbort,           latch SET  ", eg.StoryAbort("whiteout"),      True,  "PROPAGATED"),
    ("FIX      LAUNDERED BotModeError, latch SET", BotModeError("cannot reach X"), True,  "PROPAGATED"),
]:
    got = guarded(err, latch)
    print(f"  [{'ok ' if got == want else 'FAIL'}] {label} -> {got:11} (want {want})")

print("\n--- counter_hunt shape (except Exception + isinstance narrowing):")
for label, err, latch, want in [
    ("CONTROL  ordinary BotModeError, latch CLEAR", BotModeError("train failed"),  False, "SWALLOWED"),
    ("FIX      StoryAbort,            latch SET  ", eg.StoryAbort("whiteout"),     True,  "PROPAGATED"),
    ("⛔ LEAK  PathFindingError,      latch SET  ", PathFindingError("no path"),   True,  "SWALLOWED"),
]:
    got = counter_hunt_shape(err, latch)
    print(f"  [{'ok ' if got == want else 'FAIL'}] {label} -> {got:11} (want {want})")
