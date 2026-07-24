"""Ch12 route recon: from flannery_done.ss1, probe how far the GLOBAL navigator can
route toward Petalburg, and dump the connection/exit coords the legs will need.

We do NOT drive a full run here — just: (1) print each route map's connections +
warps so the leg boundaries are known, and (2) try navigate_to_anywhere to a few
waypoints to see where the global pathfinder succeeds vs needs a hand-built leg
(one-way ledges, the Rusturf boulder, the Go-Goggles desert).
"""

import pathlib as _pl
import sys

_SAVES = _pl.Path(__file__).resolve().parent / "saves"
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False

from modules.map import get_map_data
from modules.map_data import MapRSE

# The route maps, in order. Print connections so leg boundaries are known.
ROUTE = [
    "LAVARIDGE_TOWN", "ROUTE112", "ROUTE111", "MAUVILLE_CITY", "ROUTE117",
    "VERDANTURF_TOWN", "RUSTURF_TUNNEL", "ROUTE116", "RUSTBORO_CITY",
    "ROUTE104", "PETALBURG_WOODS", "PETALBURG_CITY",
]
print("=== connections along the Lavaridge -> Petalburg route ===")
for name in ROUTE:
    try:
        gnum = MapRSE[name].value
    except KeyError:
        print(f"  {name}: NOT IN MapRSE")
        continue
    md = get_map_data(gnum, (0, 0))
    conns = []
    for c in md.connections:
        try:
            conns.append(f"{c.direction}->{c.destination_map.map_name}")
        except Exception:
            pass
    warp_dests = []
    for wp in md.warps:
        try:
            dl = wp.destination_location
            warp_dests.append(f"{tuple(wp.local_coordinates)}->{dl.map_name}")
        except Exception:
            pass
    print(f"\n  {name} {gnum} size={md.map_size}")
    print(f"    connections: {conns}")
    if name in ("VERDANTURF_TOWN", "RUSTURF_TUNNEL", "PETALBURG_CITY"):
        print(f"    warps: {warp_dests}")

# Global-navigator reach test from flannery_done: try each waypoint, report reached.
from modules.modes import BotModeError
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.player import get_player_avatar

SAVE = (_SAVES / "flannery_done.ss1").read_bytes()


def step(gen, n=15000):
    for _ in range(n):
        try:
            next(gen)
        except StopIteration:
            return True
        context.emulator.run_single_frame()
    return False


print("\n=== global-navigator reach test (from flannery_done) ===")
context.emulator.load_save_state(SAVE)
for _ in range(30):
    context.emulator.run_single_frame()
pa = get_player_avatar()
print(f"start: {pa.map_group_and_number} {tuple(pa.local_coordinates)}")

for name, tile in [
    ("ROUTE112", (6, 46)),      # Route 112 lower (toward Route 111/Mauville)
    ("MAUVILLE_CITY", (22, 8)),
    ("VERDANTURF_TOWN", (17, 8)),
    ("ROUTE116", (30, 8)),
    ("PETALBURG_CITY", (15, 8)),
]:
    context.emulator.load_save_state(SAVE)
    for _ in range(30):
        context.emulator.run_single_frame()
    try:
        ok = step(navigate_to_anywhere(MapRSE[name], tile, avoid_encounters=True, avoid_scripted_events=False), 20000)
        pa = get_player_avatar()
        print(f"  -> {name}{tile}: {'REACHED' if ok else 'timeout'} (ended {pa.map_group_and_number} {tuple(pa.local_coordinates)})")
    except BotModeError as e:
        print(f"  -> {name}{tile}: FAIL ({str(e)[:70]})")
    except Exception as e:
        print(f"  -> {name}{tile}: err {type(e).__name__} {str(e)[:60]}")
