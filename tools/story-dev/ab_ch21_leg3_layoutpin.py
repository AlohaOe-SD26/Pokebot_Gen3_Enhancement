"""§Ch21 LEG 3 — THE LAYOUT-PIN FIX, A/B'd AGAINST THE DRIVE THAT THE BUG ACTUALLY KILLED.

‼ WHY THIS EXISTS. Leg 3's FIRST drive (2026-09-01) walked out of the Sootopolis Poke Center and
jammed at `SOOTOPOLIS_CITY (31,42)`:

    UnreachableDestinationError: Could not reach (29, 53) on MapRSE.SOOTOPOLIS_CITY: the field is
    idle and we are still at (31, 42), so retrying cannot change the result

⛔ THE PLANNER WAS NOT BROKEN — IT WAS LOOKING AT A DIFFERENT MAP. `modules/map.py:735-755` caches
each map's 24-byte layout struct in `_map_layout_cache` keyed by **`(rom id, map)` ALONE**. It does
not record whether those bytes came from the LIVE `gMapHeader` (`get_map_data_for_current_position`)
or from the STATIC ROM `gMapGroups` table (`get_map_data`). Both writers populate the same entry, so
**whichever reader touches a map first wins for the whole process — and `calculate_path` silently
inherits that choice.** SOOTOPOLIS_CITY swaps to `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE` at
`VAR_SOOTOPOLIS_CITY_STATE` 1-4, which is exactly the state leg 3 runs in, and the STATIC layout
calls a 9x3 block (x=27..35, y=43..45) open water where the game has solid rock.

--------------------------------------------------------------------------------------------
WHAT MAKES THIS AN A/B RATHER THAN A DEMONSTRATION
--------------------------------------------------------------------------------------------
The fixture is **the stall state the failing drive captured of itself** —
`saves/stalls/repro-ml-f5592.ss1`, the avatar standing on (31,42) mid-jam. So ARM A is not a
reconstruction of the failure; it is the failure, re-asked.

    ARM A  no fix  — reproduce what drive 1 did: 37 waypoints, 3 of them tiles the GAME calls walls
    ARM B  the fix — pin the planner to the LIVE layout: 35 waypoints, ZERO live walls

⛔ Both arms are graded by a THIRD instrument, not by the planner that is under test:
`sootopolis._live_wall_tiles()` reads `gBackupMapLayout` — the grid the GAME itself walks on — so
"walkable" is decided by the game, not by the thing whose disagreement with the game is the bug.

‼ AND THE CACHE IS CLEARED BETWEEN ARMS ON PURPOSE. Without `_map_layout_cache.clear()` +
`_maps.clear()`, arm B would inherit arm A's seeding and the comparison would be vacuous — the
classic "both arms measured the same thing" failure.

⚠ NOTE WHAT THIS A/B CANNOT SEE, because it cost a second drive to learn: clearing the caches
wholesale means `map_path._maps` is rebuilt from EMPTY on every arm here. The real run has a
populated cache, and an earlier version of the fix evicted a SINGLE map from it — which
`_get_all_maps_metadata` (map_path.py:499-505) never refills, because it only populates when the
game key is absent entirely. That raised `KeyError: (0, 7)` on the next drive and **this script
passed clean over it**. ⇒ a probe that resets more state than the real run does can pass over a
defect the real run hits.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 ab_ch21_leg3_layoutpin.py
Evidence: evidence/2026-09-01-ch21-leg3-LAYOUTPIN-ab.txt
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
context.bot_mode = "Story"

import modules.map as map_module
import modules.map_path as map_path_module
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.story import sootopolis as ch21

CITY = MapRSE.SOOTOPOLIS_CITY
SAVE = pathlib.Path(__file__).resolve().parent / "saves" / "stalls" / "repro-ml-f5592.ss1"
FROM_TILE = (43, 32)     # the Poke Center front, where the real run resumed the walk
TO_TILE = (29, 53)       # the dive tile


def main() -> int:
    print("=" * 100)
    print("§Ch21 LEG 3 — THE LAYOUT-PIN FIX, A/B AGAINST DRIVE 1'S OWN STALL STATE")
    print("=" * 100)
    if not SAVE.exists():
        print(f"‼ MISSING FIXTURE {SAVE} — this A/B is about a SPECIFIC failing run and cannot be")
        print("  reconstructed without the stall state that run captured of itself.")
        return 1
    print(f"fixture: {SAVE.name}  (captured BY the failing drive, mid-jam at SOOTOPOLIS_CITY (31,42))")

    verdicts = []
    for label, pin in (("ARM A — WITHOUT the fix (as drive 1 ran)", False),
                       ("ARM B — WITH the fix (pin to the live layout)", True)):
        # ⛔ a FRESH cache per arm, or arm B silently inherits arm A's seeding
        map_module._map_layout_cache.clear()
        map_path_module._maps.clear()
        context.emulator.load_save_state(SAVE.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()

        print("")
        print(f"=== {label} ===")
        if pin:
            print("  ", ch21._pin_planner_to_live_layout(CITY))
        try:
            path = calculate_path((CITY, FROM_TILE), (CITY, TO_TILE))
            tiles = [tuple(w.coordinates) for w in path]
        except PathFindingError:
            print("   NO ROUTE")
            verdicts.append((label, None, None))
            continue
        walls = ch21._live_wall_tiles(CITY, tiles)
        print(f"   {FROM_TILE}->{TO_TILE}: {len(tiles)} waypoints")
        print(f"   waypoints the GAME calls WALLS: {walls if walls else 'NONE'}")
        print(f"   ⇒ {'‼ WOULD JAM' if walls else 'walkable end to end'}")
        verdicts.append((label, len(tiles), walls))

    print("")
    print("=" * 100)
    arm_a, arm_b = verdicts[0], verdicts[1]
    discriminates = arm_a[2] and not arm_b[2]
    print(f"DISCRIMINATING: {discriminates}   "
          f"(ARM A walls={arm_a[2]}, ARM B walls={arm_b[2]})")
    if not discriminates:
        print("‼ THE ARMS DID NOT DIFFER — this A/B proves NOTHING as it stands. Do not read a")
        print("  clean ARM B as evidence unless ARM A actually reproduced the failure.")
    print("=" * 100)
    return 0 if discriminates else 1


if __name__ == "__main__":
    raise SystemExit(main())
