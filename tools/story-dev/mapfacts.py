"""Generic map facts: objects, warps, and a passability grid for any MapRSE member.

    PROBE_MAPS=DEWFORD_TOWN,SLATEPORT_CITY_OCEANIC_MUSEUM_1F py mapfacts.py

Static ROM data only (no save state), so it shows the map as authored — use a live
in-state check when hidden-NPC templates or setmetatile puzzles are in play.
"""

import os
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

for name in os.environ.get("PROBE_MAPS", "DEWFORD_TOWN").split(","):
    name = name.strip()
    gnum = MapRSE[name].value
    md = get_map_data(gnum, (0, 0))
    w, h = md.map_size
    print(f"\n===== {name} group={gnum} size={w}x{h} =====")
    print("-- warps --")
    for i, wp in enumerate(md.warps):
        try:
            dl = wp.destination_location
            dest = f"{dl.map_group_and_number} {dl.map_name} tile={tuple(dl.local_position)}"
        except Exception as e:
            dest = f"?? {e}"
        print(f"  warp[{i:2d}] {tuple(wp.local_coordinates)} -> {dest}")
    print("-- objects --")
    for o in md.objects:
        try:
            print(f"  obj id={o.local_id} {tuple(o.local_coordinates)} script={o.script_symbol} flag={o.flag_id}")
        except Exception:
            print(f"  obj {o.to_dict()}")
    warp_t = {tuple(x.local_coordinates) for x in md.warps}
    obj_t = {}
    for o in md.objects:
        try:
            obj_t[tuple(o.local_coordinates)] = o.local_id
        except Exception:
            pass
    print("-- grid: '.'=walk '#'=wall 'W'=warp digit=object id --")
    print("     " + "".join(str(x % 10) for x in range(w)))
    for y in range(h):
        row = []
        for x in range(w):
            t = (x, y)
            if t in obj_t:
                row.append(str(obj_t[t] % 10))
            elif t in warp_t:
                row.append("W")
            else:
                row.append("." if not get_map_data(gnum, t).collision else "#")
        print(f"y{y:3d} " + "".join(row))
