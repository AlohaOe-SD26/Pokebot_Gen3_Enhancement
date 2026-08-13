"""KI-59 — does the fix CHANGE ROUTING where it should, and NOT change it where it should not?

`repro_impassable_dirs.py` proves the per-tile vectors now match the decomp. That is necessary and
not sufficient: `map_path.py` is shared by every bot mode, so the questions that decide whether the
change is safe are

  1. does `calculate_path` actually behave differently on a map with LIVE tiles?   (效果 / effect)
  2. does it behave IDENTICALLY on a map with none?                                (collateral)

Run this in BOTH arms and diff the output:

    PYTHONUTF8=1 py -3.12 probe_ki59_routing_ab.py > after.txt
    git stash push -- ../../sandbox-pokebot/modules/map_path.py
    PYTHONUTF8=1 py -3.12 probe_ki59_routing_ab.py > before.txt
    git stash pop
    diff before.txt after.txt

EXPECTED: the VICTORY_ROAD_1F block differs; the MOSSDEEP_CITY control block is byte-identical.
‼ If the control block differs, the change has collateral damage and must be reverted.

‼ KI-60: `calculate_path` never validates its SOURCE tile, so every source used here is asserted
open (collision == 0 and not `Impassable *`) before it is used. A result is evidence about the
DESTINATION only.
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path

BAR = "=" * 100


def grid_of(map_enum):
    return {tuple(t.local_position): t for t in get_map_all_tiles(get_map_data(map_enum, (0, 0)))}


def is_open(t) -> bool:
    return t is not None and t.collision == 0 and not t.tile_type.startswith("Impassable ")


def route(map_enum, src, dst) -> str:
    """Length of the route, or the failure. Deterministic string for diffing."""
    try:
        wp = calculate_path((map_enum, src), (map_enum, dst))
        return f"OK len={len(wp)}"
    except PathFindingError as exc:
        return f"NO-PATH ({str(exc)[:40]})"
    except Exception as exc:  # reported, never swallowed — a new error TYPE is itself a finding
        return f"ERROR {type(exc).__name__}: {str(exc)[:40]}"


print(f"{BAR}\nEFFECT — VICTORY_ROAD_1F (29 LIVE `Impassable North` tiles)\n{BAR}")
print("For each live tile T, we ask the planner to reach T from each open orthogonal neighbour.")
print("Ground truth: T's NORTH edge is a wall, so approaching from the NORTH (travelling South)")
print("must FAIL, while E/W/S approaches must succeed. The old model claimed the exact opposite.\n")

vr = grid_of(MapRSE.VICTORY_ROAD_1F)
live = sorted(p for p, t in vr.items() if t.tile_type.startswith("Impassable ") and t.collision == 0)
print(f"live tiles: {len(live)}  -> {live}\n")

DIRS = {"from-N(travel S)": (0, -1), "from-E(travel W)": (1, 0), "from-S(travel N)": (0, 1), "from-W(travel E)": (-1, 0)}

tested = 0
for target in live[:10]:  # a fixed, deterministic sample — enough to diff, cheap to run
    x, y = target
    parts = []
    for label, (dx, dy) in DIRS.items():
        src = (x + dx, y + dy)
        if not is_open(vr.get(src)):
            parts.append(f"{label}=src-not-open")
            continue
        parts.append(f"{label}={route(MapRSE.VICTORY_ROAD_1F, src, target)}")
        tested += 1
    print(f"  T={str(target):<9} " + "  ".join(parts))
print(f"\n  approaches actually exercised: {tested}")

print(f"\n{BAR}\nCOLLATERAL CONTROL — MOSSDEEP_CITY (ZERO `Impassable *` tiles)\n{BAR}")
print("This map cannot reach the changed branch, so EVERY line below must be byte-identical")
print("across the two arms. Any difference here is collateral damage.\n")

md = grid_of(MapRSE.MOSSDEEP_CITY)
assert not any(t.tile_type.startswith("Impassable ") for t in md.values()), "control map is not clean"

open_tiles = sorted(p for p, t in md.items() if is_open(t))
print(f"open tiles on the control map: {len(open_tiles)}")
# A fixed, spread-out, reproducible sample — no randomness, so the two arms are comparable.
step = max(1, len(open_tiles) // 12)
sample = open_tiles[::step][:12]
for i in range(len(sample) - 1):
    src, dst = sample[i], sample[i + 1]
    print(f"  {str(src):<9} -> {str(dst):<9} {route(MapRSE.MOSSDEEP_CITY, src, dst)}")

print(f"\n{BAR}\nEARLY-LADDER REGRESSION — the ONLY built-content maps that carry live tiles\n{BAR}")
print("The fix changes behaviour by design on the 51 maps with `Impassable *` tiles. Most are")
print("unbuilt content (Victory Road, the Regi tombs, Shoal Cave, Artisan Cave, the Contest Hall).")
print("These are the ones the CURRENT ladder actually walks, so a regression here is a live bug:")
print("  * LITTLEROOT_TOWN_BRENDANS_HOUSE_2F / MAYS_HOUSE_2F — ‼ §Ch1 BEGINS in this room")
print("  * VERDANTURF_TOWN_WANDAS_HOUSE — the Rusturf Tunnel beat")
print("  * GRANITE_CAVE_B2F — the Steven's-letter beat")
print("Full reachability from a fixed anchor is printed as a canonical signature; diff the arms.\n")

EARLY = [
    MapRSE.LITTLEROOT_TOWN_BRENDANS_HOUSE_2F,
    MapRSE.LITTLEROOT_TOWN_MAYS_HOUSE_2F,
    MapRSE.VERDANTURF_TOWN_WANDAS_HOUSE,
    MapRSE.GRANITE_CAVE_B2F,
]

for map_enum in EARLY:
    g = grid_of(map_enum)
    live = sorted(p for p, t in g.items() if t.tile_type.startswith("Impassable ") and t.collision == 0)
    open_tiles = sorted(p for p, t in g.items() if is_open(t))
    print(f"  --- {map_enum.name} --- open={len(open_tiles)} live_impassable={len(live)} at {live}")
    if not open_tiles:
        print("      (no open tiles — nothing to measure)")
        continue
    anchor = open_tiles[0]
    reachable = 0
    unreachable = []
    for dst in open_tiles:
        if dst == anchor:
            continue
        r = route(map_enum, anchor, dst)
        if r.startswith("OK"):
            reachable += 1
        else:
            unreachable.append(dst)
    print(f"      anchor={anchor}  reachable={reachable}/{len(open_tiles) - 1}")
    print(f"      unreachable={unreachable}")
    # The live tiles themselves: can the planner stand on them at all?
    for t in live:
        print(f"      live tile {t}: from anchor -> {route(map_enum, anchor, t)}")

print(f"\n{BAR}\nDONE — diff this output between the two arms.\n{BAR}")
