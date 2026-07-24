"""MEASUREMENT ONLY. Confirms the mechanism found by story_harness.py's replay of
devon_scope_got.ss1: `_leave_route120_north_bridge()`'s guard is
`map==ROUTE120 and y<=16`, which matches ANY tile on the western half of Route
120 -- not just the isolated bridge-strand tile (13,16) it was written for. When
re-entered from (5,15) (where midstuck.ss1 shows the player actually was, after
a battle mid-route), the hard-coded held walk targets (13,15) via "Up", which is
unreachable by heading Up from x=5 (Up only changes y, never x) -- reproducing
the exact derail text.

Drives the REAL `_leave_route120_north_bridge()` generator both ways:
  A) from (13,16) [the tile it was designed for]      -> expect: succeeds
  B) from (5,15)  [the tile midstuck.ss1 shows in production] -> expect: the
     exact 'held walk: never reached (13, 15) heading Up' BotModeError

Run: py -3.12 tools/story-dev/repro_route120_bridge_guard_fault.py
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
_BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(_BUILD))

STATE = _REPO / "tools" / "story-dev" / "saves" / "devon_scope_got.ss1"
assert STATE.is_file(), f"missing state: {STATE}"

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator
from modules.player import get_player_avatar
from modules.map_data import MapRSE
from modules.story.early_game import _leave_route120_north_bridge
from modules.modes._interface import BotModeError


def fresh_emulator():
    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    context.bot_mode = "Story"
    context.emulator.load_save_state(STATE.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()


def drive_to_pos(steps, max_frames_per_leg=1200):
    """Walk (held input) along `steps` = [(direction, (x,y)), ...] from the save's
    native (13,16), so we start the real generator from an actually-reachable
    live position (not a memory-poked one). Same route the real held-walk uses."""
    for direction, tgt in steps:
        context.emulator.reset_held_buttons()
        frames = 0
        while tuple(get_player_avatar().local_coordinates) != tgt:
            context.emulator.hold_button(direction)
            context.emulator.run_single_frame()
            frames += 1
            if frames > max_frames_per_leg:
                raise RuntimeError(f"setup walk never reached {tgt} heading {direction} (stuck at "
                                    f"{tuple(get_player_avatar().local_coordinates)})")
    context.emulator.reset_held_buttons()
    for _ in range(10):
        context.emulator.run_single_frame()


def drive_gen(gen, cap=1000):
    frame = 0
    try:
        while frame < cap:
            next(gen)
            context.emulator.run_single_frame()
            frame += 1
    except StopIteration:
        return frame, "returned", tuple(get_player_avatar().local_coordinates)
    except BotModeError as e:
        return frame, f"BotModeError: {e}", tuple(get_player_avatar().local_coordinates)
    except Exception as e:
        return frame, f"{type(e).__name__}: {e}", tuple(get_player_avatar().local_coordinates)
    return frame, "cap hit, still running", tuple(get_player_avatar().local_coordinates)


print("=" * 78)
print("A) _leave_route120_north_bridge() from (13,16) -- the tile it targets")
fresh_emulator()
start = tuple(get_player_avatar().local_coordinates)
print(f"   start pos = {start}")
frames, outcome, end = drive_gen(_leave_route120_north_bridge())
print(f"   -> {outcome} after {frames} frames, end pos={end}")

print("\n" + "=" * 78)
print("B) _leave_route120_north_bridge() from (5,15) -- reproduces production's")
print("   real re-entry position (per midstuck.ss1, captured by story_harness.py")
print("   mid-replay of this exact save)")
fresh_emulator()
drive_to_pos([("Up", (13, 15)), ("Left", (5, 15))])
start = tuple(get_player_avatar().local_coordinates)
print(f"   start pos = {start}")
frames, outcome, end = drive_gen(_leave_route120_north_bridge(), cap=1500)
print(f"   -> {outcome} after {frames} frames, end pos={end}")

print("\n" + "=" * 78)
print("DONE")
