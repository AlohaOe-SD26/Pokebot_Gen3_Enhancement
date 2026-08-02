"""#24-pc: find the PC tile inside a Poké Centre, and the tile to stand on to use it.
NO EMULATION LOOP — boots the ROM and reads map headers. Seconds, not frames.

WHY A PROBE AND NOT A CONSTANT. `interact_with_pc()` (upstream,
`modules/modes/util/pc_interaction.py`) refuses unless the tile the player FACES has
`tile_type == "PC"`. The standing rule in this project is that a tile is adopted only after
it is PROVEN from real map data, never recalled — `HUNTING_GROUNDS` says it outright
("Nothing goes in here on a guess") and every tile that was guessed has cost a debugging
session. So: scan the Poké Centre map, report every PC tile, and derive the standing tile
and facing direction from the map itself.

The heal routine already pins the rest of this map's geometry — nurse at (7,4), exit warp at
(7,8), the tile above the door at (7,7) — see `higher_level_actions.heal_in_pokemon_center`.

    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 probe_pc_tile.py --profile probe-pc
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--profile", default="probe-pc")
ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"])
ap.add_argument("--width", type=int, default=16, help="how wide to scan the interior")
ap.add_argument("--height", type=int, default=12, help="how tall to scan the interior")
args = ap.parse_args()

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / f"{args.build}-pokebot"))

from modules.context import context  # noqa: E402
from modules.profiles import create_profile, profile_directory_exists, load_profile_by_name  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402
from modules.game import set_rom  # noqa: E402

if not profile_directory_exists(args.profile):
    roms = list_available_roms()
    assert roms, "no ROMs found in roms/"
    create_profile(args.profile, roms[0])
profile = load_profile_by_name(args.profile)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0

from modules.map import get_map_data  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402

# Every town's Poké Centre 1F shares one interior layout, so proving it on a few is enough.
CENTRES = [n for n in (
    "PETALBURG_CITY_POKEMON_CENTER_1F",
    "RUSTBORO_CITY_POKEMON_CENTER_1F",
    "LAVARIDGE_TOWN_POKEMON_CENTER_1F",
    "VERDANTURF_TOWN_POKEMON_CENTER_1F",
    "MAUVILLE_CITY_POKEMON_CENTER_1F",
    "OLDALE_TOWN_POKEMON_CENTER_1F",
) if hasattr(MapRSE, n)]

print(f"build={args.build}  rom={profile.rom.id}\n")
print(f"{'centre':<38}{'PC tile(s)':<22}{'stand on':<12}face")
print("-" * 84)

results = {}
for name in CENTRES:
    m = getattr(MapRSE, name)
    pcs = []
    for y in range(args.height):
        for x in range(args.width):
            try:
                loc = get_map_data(m, (x, y))
            except Exception:
                continue
            if loc is None:
                continue
            try:
                if loc.tile_type == "PC":
                    pcs.append((x, y))
            except Exception:
                continue
    # You use a PC by standing SOUTH of it and facing Up (the interior's PC sits against
    # the north wall, so the tile below is the only approachable side).
    stand = face = "-"
    if pcs:
        px, py = pcs[0]
        below = get_map_data(m, (px, py + 1))
        if below is not None and below.is_surfable is False and below.collision == 0:
            stand, face = f"({px}, {py + 1})", "Up"
        else:
            stand, face = f"({px}, {py + 1})?", "Up"
    results[name] = (pcs, stand, face)
    print(f"{name:<38}{str(pcs):<22}{stand:<12}{face}")

print()
distinct = {tuple(v[0]) for v in results.values() if v[0]}
if not results:
    print("‼ no Poké Centre maps found in MapRSE — check the names above")
elif len(distinct) == 1 and all(v[0] for v in results.values()):
    pcs = next(iter(distinct))
    px, py = pcs[0]
    print(f"‼ ALL {len(results)} centres agree: PC at {pcs[0]}, stand on ({px}, {py + 1}) facing Up.")
    print("   Safe to adopt as a constant — it is one shared interior layout, proven from map")
    print("   data on several maps rather than recalled.")
else:
    print("‼ CENTRES DISAGREE — do NOT adopt a single constant. Per-map table required:")
    for k, (pcs, stand, face) in results.items():
        print(f"     {k}: {pcs} stand {stand}")
