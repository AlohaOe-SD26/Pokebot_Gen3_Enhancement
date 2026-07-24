"""MEASUREMENT ONLY. Drive the REAL `_leave_route120_north_bridge()` generator
against `devon_scope_got.ss1` and log per-frame diagnostics, to see exactly
where/why the production code differs from the raw-hold-button probe (which
showed Up from (13,16) reaches (13,15) trivially in isolation).

Run: py -3.12 tools/story-dev/repro_route120_bridge_drive.py
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

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"
context.emulator.load_save_state(STATE.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
print(f"[loaded] {STATE}")

from modules.player import get_player_avatar, player_avatar_is_controllable, player_avatar_is_standing_still
from modules.tasks import get_global_script_context
from modules.map import get_map_objects
from modules.story.early_game import _leave_route120_north_bridge

gen = _leave_route120_north_bridge()
frame = 0
last_held = None
try:
    while True:
        pos = tuple(get_player_avatar().local_coordinates)
        gsc_active = get_global_script_context().is_active
        controllable = player_avatar_is_controllable()
        still = player_avatar_is_standing_still()
        held = getattr(context.emulator, "_held_buttons", None)
        if frame % 20 == 0 or frame < 5:
            print(f"f{frame:>5} pos={pos} gsc={gsc_active} controllable={controllable} "
                  f"still={still} held_buttons_attr={held}")
        next(gen)
        context.emulator.run_single_frame()
        frame += 1
        if frame > 2500:
            print("... aborting local drive loop past 2500 frames (would be past the 900-bound anyway)")
            break
except StopIteration:
    print(f"[gen returned normally] at frame {frame}, final pos={tuple(get_player_avatar().local_coordinates)}")
except Exception as e:
    print(f"[gen RAISED] {type(e).__name__}: {e} at frame {frame}, "
          f"pos={tuple(get_player_avatar().local_coordinates)}")

print("DONE")
