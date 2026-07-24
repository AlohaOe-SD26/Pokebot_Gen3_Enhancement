"""Ch12 leg-1 STATIC recon (no walking): Lavaridge -> Mauville routing facts.

Answers, from ROM data + static calculate_path only:
 1. LAVARIDGE_TOWN / ROUTE112 / ROUTE111 / FIERY_PATH connections + warp tiles.
 2. Which Route 112 tiles are statically pathable FROM the Lavaridge-side entry:
    the Fiery Path north door (22,10)? the south door (11,36)? the cable-car
    station door (28,28)? the Route 111 boundary?
 3. Route 111: from the Route-112-junction side, is the south exit (toward
    Mauville) pathable past the twin-rocks choke at (18,100)/(19,100) —
    and does the desert really seal north<->south?

Run while batches are live: loads a save state ONLY to initialize memory readers
(no frames are advanced beyond boot; nothing is driven).
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
context.emulator.load_save_state((_SAVES / "flannery_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import calculate_path, PathFindingError

print("=== connections + warps ===")
for name in ("LAVARIDGE_TOWN", "ROUTE112", "ROUTE111", "FIERY_PATH", "MAUVILLE_CITY"):
    m = MapRSE[name]
    md = get_map_data(m, (0, 0))
    conns = []
    for c in md.connections:
        try:
            conns.append(f"{c.direction}->{c.destination_map.map_name}(off={c.offset})")
        except Exception:
            pass
    warps = []
    for wp in md.warps:
        try:
            warps.append(f"{tuple(wp.local_coordinates)}->{wp.destination_location.map_name}")
        except Exception:
            pass
    print(f"\n{name} size={md.map_size}")
    print(f"  connections: {conns}")
    print(f"  warps: {warps}")

print("\n=== static pathability (calculate_path, no walking) ===")


def try_path(frm, to, label):
    try:
        wps = calculate_path(frm, to, avoid_encounters=False, avoid_scripted_events=False)
        print(f"  {label}: PATHABLE ({len(wps)} steps)")
    except PathFindingError as e:
        print(f"  {label}: NO PATH ({str(e)[:80]})")
    except Exception as e:
        print(f"  {label}: err {type(e).__name__}: {str(e)[:80]}")


R112 = MapRSE.ROUTE112
R111 = MapRSE.ROUTE111
LAV = MapRSE.LAVARIDGE_TOWN
FIERY = MapRSE.FIERY_PATH

# Lavaridge town: east exit tiles are on the right edge; try from the town center.
try_path((LAV, (9, 7)), (R112, (22, 11)), "Lavaridge(9,7) -> R112(22,11) [north Fiery door staging]")
try_path((LAV, (9, 7)), (R112, (11, 36)), "Lavaridge(9,7) -> R112(11,36) [south Fiery door]")
try_path((LAV, (9, 7)), (R112, (28, 28)), "Lavaridge(9,7) -> R112(28,28) [cable-car station door]")
try_path((LAV, (9, 7)), (R111, (18, 99)), "Lavaridge(9,7) -> R111(18,99) [above the twin rocks]")
try_path((LAV, (9, 7)), (R111, (13, 90)), "Lavaridge(9,7) -> R111(13,90) [the proven prior probe]")

# Within Route 111: from just above the rocks to south (Mauville side) — the rocks choke.
try_path((R111, (18, 99)), (R111, (18, 102)), "R111(18,99) -> (18,102) [through the rock choke]")
try_path((R111, (18, 99)), (R111, (13, 90)), "R111(18,99) -> (13,90) [north along 111]")
try_path((R111, (13, 90)), (R111, (18, 99)), "R111(13,90) -> (18,99) [south along 111 — desert seal?]")
try_path((R111, (18, 102)), (MapRSE.MAUVILLE_CITY, (19, 6)), "R111(18,102) -> Mauville(19,6)")

# Fiery Path interior: south entrance tile to north exit tile.
try_path((FIERY, (26, 36)), (FIERY, (26, 4)), "Fiery(26,36) -> (26,4) [tunnel south->north]")
try_path((FIERY, (26, 4)), (FIERY, (26, 36)), "Fiery(26,4) -> (26,36) [tunnel north->south]")

print("\ndone")
