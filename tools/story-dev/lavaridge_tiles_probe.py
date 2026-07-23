"""Print the raw tile grid (collision / elevation / behaviour) for both gym floors."""

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

for label, gnum in (("1F", MapRSE.LAVARIDGE_TOWN_GYM_1F.value), ("B1F", MapRSE.LAVARIDGE_TOWN_GYM_B1F.value)):
    md = get_map_data(gnum, (0, 0))
    w, h = md.map_size
    print(f"\n===== {label} ({w}x{h}) — cell = collision:elevation:behaviour =====")
    print("      " + "".join(f"{x:>12d}" for x in range(w)))
    for y in range(h):
        cells = []
        for x in range(w):
            t = get_map_data(gnum, (x, y))
            cells.append(f"{t.collision}:{t.elevation}:{t._metatile_attributes[0]}".rjust(12))
        print(f"y={y:2d} " + "".join(cells))
