"""Probe the Petalburg-gym door wedge state (ki_ch12_gymdoor.ss1): gym VAR value +
LIVE-grid collision of the entrance-room door tiles (the static planner sees doors
open; the runtime VAR-gated metatiles may be closed — the Mauville lesson)."""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "sandbox-pokebot"))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
context.emulator.load_save_state((_REPO / "tools/story-dev/saves/ki_ch12_gymdoor.ss1").read_bytes())

from modules.memory import get_event_var
from modules.player import get_player_avatar
from modules.map import get_map_data

print("pos:", tuple(get_player_avatar().local_coordinates))
try:
    print("VAR_PETALBURG_GYM_STATE:", get_event_var("PETALBURG_GYM_STATE"))
except Exception as e:
    print("VAR read err:", e)

for t in [(1, 105), (2, 105), (6, 105), (7, 105), (1, 106), (4, 106)]:
    try:
        td = get_map_data((8, 1), t)
        print(t, "collision:", td.collision, "type:", getattr(td, "tile_type", "?"),
              "behavior?", getattr(td, "has_encounters", "-"))
    except Exception as e:
        print(t, "err", e)

# Compare with the STATIC view the planner used (same call — get_map_data reads the
# live gBackupMapLayout when the map is loaded, per the Mauville lesson; print the
# calculate_path opinion for contrast):
from modules.map_path import calculate_path, PathFindingError

try:
    wps = calculate_path((( 8, 1), (1, 106)), ((8, 1), (1, 105)))
    print("planner: (1,106)->(1,105) PATHABLE", len(wps))
except PathFindingError:
    print("planner: (1,106)->(1,105) NO PATH")
except Exception as e:
    print("planner err:", type(e).__name__, e)
