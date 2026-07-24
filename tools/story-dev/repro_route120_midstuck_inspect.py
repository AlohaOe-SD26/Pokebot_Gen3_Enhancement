"""MEASUREMENT ONLY. Inspect the harness's auto-saved midstuck.ss1 (captured during
the devon_scope_got.ss1 replay at f1273, no-progress window, battle text 'BLAZIKEN
gained 565 EXP. Points!'). Where IS the player when the second held-walk derail
fires, and what does _leave_route120_north_bridge()'s guard evaluate to there?

Run: py -3.12 tools/story-dev/repro_route120_midstuck_inspect.py
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
_BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(_BUILD))

STATE = _REPO / "tools" / "story-dev" / "saves" / "midstuck.ss1"
assert STATE.is_file(), f"missing state: {STATE}"

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
context.emulator.load_save_state(STATE.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
print(f"[loaded] {STATE}")

from modules.player import get_player_avatar
from modules.map_data import MapRSE
from modules.memory import get_event_flag

avatar = get_player_avatar()
map_gn = tuple(avatar.map_group_and_number)
pos = tuple(avatar.local_coordinates)
try:
    map_name = MapRSE(map_gn).name
except ValueError:
    map_name = f"<unknown {map_gn}>"
print(f"map_group_and_number={map_gn} ({map_name})  local_coordinates={pos}  facing={avatar.facing_direction!r}")
print(f"RECEIVED_DEVON_SCOPE={bool(get_event_flag('RECEIVED_DEVON_SCOPE'))}")

# Evaluate the exact guard _leave_route120_north_bridge() uses.
guard = (map_gn == MapRSE.ROUTE120.value and pos[1] <= 16)
print(f"\n_leave_route120_north_bridge() guard 'map==ROUTE120 and y<=16': {guard}")
if guard:
    print(f"   -> IT WOULD RUN THE HELD WALK, targeting (13,15) via Up, from actual pos {pos}.")
    if pos[0] != 13:
        print(f"   -> x={pos[0]} != 13: holding Up will NOT land on x=13, so the walk can")
        print(f"      never reach exactly (13,15) -- this is the derail, confirmed by position.")
