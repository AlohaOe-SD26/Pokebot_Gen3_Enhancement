"""Empirically discover the Ch12 route legs: from flannery_done, chain _navigate_riding_out
to each successive map and report which hops work and where scenes/ledges/boulders break
a leg. This tells us the exact leg structure to hardcode in travel_lavaridge_to_petalburg.
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

from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.story import early_game

# Load flannery_done and step out of the gym first (the story exits the gym after the badge).
context.emulator.load_save_state((_SAVES / "flannery_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()


def drive(gen, n=25000):
    for _ in range(n):
        try:
            next(gen)
        except StopIteration:
            return True
        context.emulator.run_single_frame()
    return False


def here():
    pa = get_player_avatar()
    return pa.map_group_and_number, tuple(pa.local_coordinates)


print("start:", here())
# First get to Lavaridge town proper (out of the gym) using the established helper.
drive(early_game.normalize_to_overworld())
try:
    drive(early_game._navigate_riding_out(MapRSE.LAVARIDGE_TOWN, (9, 7)))
except Exception as e:
    print("  (exit-gym nav note:", str(e)[:60], ")")
print("after gym exit:", here())

# Chained legs: (target map, a reachable tile near its FORWARD exit).
LEGS = [
    ("ROUTE112", (6, 46)),        # west Route 112, lower (below the ledges)
    ("ROUTE111", (13, 137)),      # Route 111 far south (toward Mauville)
    ("MAUVILLE_CITY", (19, 5)),   # into Mauville from the north
    ("ROUTE117", (55, 8)),        # Route 117, toward Verdanturf (west)
    ("VERDANTURF_TOWN", (16, 8)), # Verdanturf
    ("ROUTE116", (60, 8)),        # Route 116 (via Rusturf) toward Rustboro
    ("RUSTBORO_CITY", (24, 55)),  # Rustboro, toward Route 104 south
    ("ROUTE104", (12, 55)),       # Route 104, toward Petalburg Woods / Petalburg
    ("PETALBURG_CITY", (15, 20)), # Petalburg City
]

for name, tile in LEGS:
    try:
        ok = drive(early_game._navigate_riding_out(MapRSE[name], tile, tries=6))
        print(f"  leg -> {name}{tile}: {'OK' if ok else 'timeout'}  now {here()}")
    except Exception as e:
        print(f"  leg -> {name}{tile}: FAIL {type(e).__name__}: {str(e)[:80]}  now {here()}")
        break
