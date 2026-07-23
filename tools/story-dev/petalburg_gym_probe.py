"""Deep-map the Petalburg Gym (Norman, Ch12) — trainer objects + the room/door warp
graph + whether the route to Petalburg needs the Go-Goggles desert.

The gym is one tall map (9x112) of stacked rooms joined by internal warps whose
destinations are VAR_PETALBURG_GYM_STATE-gated at run time. This prints the object
events (trainers/Norman/greeter) with their tiles, and the warp pairs grouped by y so
the room→door structure is legible for the §Ch12 spec.
"""

import pathlib as _pl
import sys

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False

from modules.map import get_map_data
from modules.map_data import MapRSE

GYM = MapRSE.PETALBURG_CITY_GYM.value
md = get_map_data(GYM, (0, 0))
w, h = md.map_size
print(f"PETALBURG_CITY_GYM {w}x{h}")
print("\n-- objects (trainers / Norman / greeter / Wally's dad) --")
for o in md.objects:
    try:
        print(f"  id={o.local_id:2d} {tuple(o.local_coordinates)}  {o.script_symbol}  flag={o.flag_id}")
    except Exception as e:
        print(f"  obj ? {e}")

print("\n-- warps, sorted by y (each room is a horizontal band) --")
warps = sorted(md.warps, key=lambda x: (x.local_coordinates[1], x.local_coordinates[0]))
for wp in warps:
    t = tuple(wp.local_coordinates)
    try:
        dl = wp.destination_location
        dest = f"{dl.map_group_and_number} {dl.map_name} tile={tuple(dl.local_position)}"
    except Exception as e:
        dest = f"?? {e}"
    print(f"  {t} -> {dest}")

# Does the overland route to Petalburg avoid the Go-Goggles desert? Check that
# Route 111's SOUTH section (Mauville side) is a distinct region from the desert.
print("\n-- Route 111 connections (is the desert on the Mauville-side path?) --")
r111 = get_map_data(MapRSE.ROUTE111.value, (0, 0))
for c in r111.connections:
    try:
        print(f"  {c.direction:6s} -> {c.destination_map.map_name}")
    except Exception as e:
        print(f"  conn ? {e}")
