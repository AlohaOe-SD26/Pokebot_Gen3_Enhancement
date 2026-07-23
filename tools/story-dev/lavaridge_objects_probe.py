"""Where is Flannery really? Dump Lavaridge Gym 1F/B1F object events + room tile sets."""

import pathlib as _pl
import sys
from collections import deque

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
    print(f"\n===== {label} objects =====")
    for o in md.objects:
        try:
            print(f"  obj {tuple(o.local_coordinates)} script={o.script_symbol} flag={o.flag_id} kind={o.kind}")
        except Exception as e:
            print(f"  obj ? {e} :: {o.to_dict()}")
    w, h = md.map_size
    passable = {(x, y) for y in range(h) for x in range(w) if not get_map_data(gnum, (x, y)).collision}
    seen, idx = set(), 0
    print(f"----- {label} room tile sets -----")
    for start in sorted(passable):
        if start in seen:
            continue
        comp, q = {start}, deque([start])
        while q:
            t = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (t[0] + dx, t[1] + dy)
                if n in passable and n not in comp:
                    comp.add(n)
                    q.append(n)
        seen |= comp
        print(f"  room {idx}: {sorted(comp)}")
        idx += 1
