"""Recon: dump the FULL Lavaridge Gym warp graph (1F holes <-> B1F vents).

The live explorer (`do_lavaridge_gym`) cycles because it guesses which B1F warp
tile is the room's exit vent. The warp table already answers this exactly — this
probe prints, per floor: every warp id, its tile, its metatile, and its resolved
destination (map + warp id + tile), plus the B1F connectivity COMPONENTS (the
sealed rooms) so the fall->vent chain can be solved statically as a graph.
"""

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

GYM1F = MapRSE.LAVARIDGE_TOWN_GYM_1F.value
GYMB1F = MapRSE.LAVARIDGE_TOWN_GYM_B1F.value


def metatile(gnum, t):
    try:
        return get_map_data(gnum, t)._metatile_attributes[0]
    except Exception:
        return None


def floor(gnum, label):
    md = get_map_data(gnum, (0, 0))
    w, h = md.map_size
    passable = {(x, y) for y in range(h) for x in range(w) if not get_map_data(gnum, (x, y)).collision}
    warps = md.warps
    print(f"\n===== {label}  group={gnum}  size={w}x{h}  passable={len(passable)}  warps={len(warps)} =====")
    for i, wp in enumerate(warps):
        t = tuple(wp.local_coordinates)
        try:
            dl = wp.destination_location
            dest = f"{dl.map_group_and_number} {dl.map_name} warp_id={wp.destination_warp_id} tile={tuple(dl.local_position)}"
        except Exception as e:
            dest = f"?? {e}"
        print(f"  warp[{i:2d}] tile={t} mt={metatile(gnum, t)} elev={wp.elevation} -> {dest}")
    return passable, [tuple(x.local_coordinates) for x in warps]


def components(gnum, passable, warps, label):
    """Sealed-room decomposition: which warp tiles are mutually walkable."""
    seen = set()
    print(f"\n----- {label} connectivity components (sealed rooms) -----")
    idx = 0
    for start in sorted(passable):
        if start in seen:
            continue
        comp = {start}
        q = deque([start])
        while q:
            t = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (t[0] + dx, t[1] + dy)
                if n in passable and n not in comp:
                    comp.add(n)
                    q.append(n)
        seen |= comp
        inside = sorted(t for t in warps if t in comp)
        print(f"  room {idx}: {len(comp)} tiles, warp tiles={inside}")
        idx += 1


p1, w1 = floor(GYM1F, "LAVARIDGE GYM 1F")
pb, wb = floor(GYMB1F, "LAVARIDGE GYM B1F")
components(GYM1F, p1, w1, "1F")
components(GYMB1F, pb, wb, "B1F")
