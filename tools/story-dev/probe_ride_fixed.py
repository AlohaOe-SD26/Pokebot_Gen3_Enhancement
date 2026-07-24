"""Load the (14,5) 'Got away safely!' hang state and drive the ACTUAL (fixed)
_wait_until_cutscene_over against the real emulator, replicating the harness
press->advance order. Prove it dismisses the message and returns.

Usage: python tools/story-dev/probe_ride_fixed.py [state.ss1]
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

state_arg = sys.argv[1] if len(sys.argv) > 1 else "current_state.ss1"
cands = [
    _pl.Path(state_arg),
    BUILD / "profiles" / "repro-ml" / state_arg,
    _REPO / "tools" / "story-dev" / "saves" / state_arg,
]
state_path = next((c for c in cands if c.is_file()), None)
assert state_path, f"state not found: {state_arg}"

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"
context.emulator.load_save_state(state_path.read_bytes())

from modules.tasks import is_waiting_for_input
from modules.game import decode_string
from modules.memory import read_symbol
from modules.story.early_game import _wait_until_cutscene_over


def bt():
    try:
        return decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        return "?"


print(f"[loaded] {state_path.name}  waiting_input={is_waiting_for_input()} bt={bt()!r}")

gen = _wait_until_cutscene_over("B")
outcome = "cap"
frames = 0
CAP = 4000
try:
    while frames < CAP:
        next(gen)                       # rider decides + queues a press for this frame
        context.emulator.run_single_frame()  # apply it (harness order)
        frames += 1
except StopIteration:
    outcome = "returned"
except Exception as e:
    outcome = f"raised {type(e).__name__}: {e}"

print(f"[result] {outcome} after {frames} frames; waiting_input={is_waiting_for_input()} bt={bt()!r}")
if outcome == "returned" and not is_waiting_for_input():
    print("PASS: the fixed rider dismissed 'Got away safely!' and returned cleanly.")
else:
    print("FAIL: the message was NOT cleared / rider did not return — dig deeper.")
