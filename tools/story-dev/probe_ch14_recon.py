"""§Ch14 recon — Mt. Pyre and the Magma Hideout, ROM-verified. NO EMULATION LOOP.

WHY THIS EXISTS BEFORE ANY CODE. §Ch13 (the Surf arc to Fortree/Winona) is the last chapter
with a build spec; the punch list's next unbuilt chapters are **Mt. Pyre**, then the **Magma
Hideout**. This project's standing rule is that map/warp facts are ROM-VERIFIED, never
recalled — `HUNTING_GROUNDS` says it outright ("Nothing goes in here on a guess"), and every
tile adopted from memory has cost a debugging session.

‼ THESE TWO AREAS ARE THE EXACT SHAPE THAT HAS BROKEN NAVIGATION BEFORE:
  * `_CAVE_EXITS` in `early_game.py` is a SINGLE-HOP table (one warp in, one warp out).
    Granite Cave B1F/B2F are still parked *because* they are two and three hops deep and the
    global navigator cannot cross warp levels — that failure dropped two real-hardware runs to
    Manual on 2026-07-22.
  * Mt. Pyre is **8 maps** (1F-6F + EXTERIOR + SUMMIT). The Magma Hideout is **8 maps** with
    THREE separate rooms per floor (`2F_1R/2R/3R`, `3F_1R/2R/3R`). Both are multi-hop by
    construction, so the depth of every warp chain must be known BEFORE anything navigates.

This dumps, per map: size, warp count, and every warp's (from_tile -> destination map + warp
id). That is the raw material for a `_CAVE_EXITS`-style table and for the chapter's route.

    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 probe_ch14_recon.py            # Mt. Pyre + Magma Hideout
    PYTHONUTF8=1 py -3.12 probe_ch14_recon.py --area pyre
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--profile", default="probe-ch14")
ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"])
ap.add_argument("--area", default="all", choices=["all", "pyre", "magma", "approach"])
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

PYRE = ["MT_PYRE_1F", "MT_PYRE_2F", "MT_PYRE_3F", "MT_PYRE_4F", "MT_PYRE_5F", "MT_PYRE_6F",
        "MT_PYRE_EXTERIOR", "MT_PYRE_SUMMIT"]
MAGMA = ["MAGMA_HIDEOUT_1F", "MAGMA_HIDEOUT_2F_1R", "MAGMA_HIDEOUT_2F_2R", "MAGMA_HIDEOUT_2F_3R",
         "MAGMA_HIDEOUT_3F_1R", "MAGMA_HIDEOUT_3F_2R", "MAGMA_HIDEOUT_3F_3R", "MAGMA_HIDEOUT_4F"]
#: The overworld approach — Lilycove is the hub the chapter starts from, Route 122/123 lead to
#: Mt. Pyre's exterior, and Route 112/Jagged Pass side is where the Magma Hideout sits.
APPROACH = ["LILYCOVE_CITY", "ROUTE121", "ROUTE122", "ROUTE123", "ROUTE120", "MOSSDEEP_CITY"]

sets = {"pyre": PYRE, "magma": MAGMA, "approach": APPROACH}
todo = sum(sets.values(), []) if args.area == "all" else sets[args.area]


def name_of(group, number):
    try:
        return MapRSE((group, number)).name
    except Exception:  # noqa: BLE001
        return f"({group},{number})"


print(f"build={args.build}  rom={profile.rom.id}\n")
for n in todo:
    m = getattr(MapRSE, n, None)
    if m is None:
        print(f"‼ {n}: not in MapRSE")
        continue
    try:
        loc = get_map_data(m, (0, 0))
        size = loc.map_size
        warps = loc.warps
    except Exception as error:  # noqa: BLE001
        print(f"‼ {n}: {type(error).__name__}: {error}")
        continue
    print(f"=== {n}  {m.value}  size={size}  warps={len(warps)}")
    for i, w in enumerate(warps):
        try:
            d = w.destination_location
            dest = f"{name_of(d.map_group, d.map_number)} warp#{w.destination_warp_id}"
        except Exception:
            try:
                dest = f"{name_of(w.destination_map_group, w.destination_map_number)} warp#{w.destination_warp_id}"
            except Exception as error:  # noqa: BLE001
                dest = f"<unreadable: {type(error).__name__}>"
        try:
            src = tuple(w.local_coordinates)
        except Exception:
            src = "?"
        print(f"    warp[{i}] at {src} -> {dest}")
    print()

print("--- READ THIS INTO THE SPEC ---")
print("A map whose only exit warps land on ANOTHER interior map is multi-hop, and the global")
print("navigator cannot cross warp levels: `_CAVE_EXITS` is single-hop and that limitation")
print("already stranded two real-hardware runs (2026-07-22). Count the hops from each floor")
print("back to an OUTDOOR map before letting the story navigate there.")
