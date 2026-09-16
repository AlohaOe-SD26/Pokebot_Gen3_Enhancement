"""WHAT DOES THE **ROM** LAYOUT SAY ABOUT THE ELITE FOUR DOORS, BEFORE ANY SCRIPT RUNS?

⛔⛔ THIS PROBE EXISTS TO TRY TO **REFUTE** A PLANNING PREMISE, NOT TO CONFIRM IT.

THE PREMISE (`ai-research-notes/2026-09-15-…-CORRECTION.md` §D''): the §Ch24 exit door is opened at
runtime by `PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles`
(`setmetatile 6,1,…OpenDoor_Frame,FALSE` / `setmetatile 6,2,…OpenDoor_Opening,FALSE`), which writes
`gBackupMapLayout` in **RAM**, while our planner reads a **ROM** blockdata pointer and caches it
forever (`modules/map.py:748-755`) ⇒ the opened door is invisible to `calculate_path`.

‼ **THAT PREMISE HAS AN OBVIOUS WAY TO BE WRONG, AND NOBODY HAD CHECKED IT.** If the ROM layout
ALREADY marks (6,1)/(6,2) walkable, then our planner would route through the door all along, the
premise collapses, and a §Ch24 build would be reorganised around a defect that does not exist. An
adversarial review asked for exactly this check and called it *the single most important thing*.

⭐ AND IT IS ANSWERABLE WITHOUT EVER ENTERING THE ROOM. The ROM layout is STATIC: `get_map_data`
takes any `map_enum` and reads ROM, so a save state standing anywhere at all can be used to
interrogate Sidney's room. (The LIVE grid is the opposite — `gBackupMapLayout` only ever describes
the loaded map, which is why `probe_live_mapgrid.py` must be run while standing there.)

⇒ **THIS PROBE READS ONLY THE ROM SIDE, FOR ALL FIVE ROOMS AT ONCE, FROM ONE SAVE STATE.**
It cannot and does not claim anything about the live grid. Pairing the two is the next step, and it
needs a save taken AFTER a victory — which does not exist yet.

CONTROLS (a reading with no control is not a measurement):
  C1  a tile that MUST be walkable — the auto-walk end tile (6,7), where the player provably stands
      after entering. If this reads impassable, the reader is wrong and every verdict is void.
  C2  a tile that MUST be a wall — (0,0), the room's top-left corner, outside the playable floor.
  C3  the trainer's own tile (6,5) is reported but NOT asserted: an NPC is an object, not collision,
      so the ROM grid is expected to call it walkable. Printed because a reader that called it a
      wall would be confusing a sprite for terrain.

    PYTHONUTF8=1 py -3.12 probe_e4_door_rom_view.py [save.ss1]

Exit 0 if the controls hold (whatever the verdict); 1 if a control fails, because then nothing the
probe says can be trusted.
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

from modules.map import get_map_data
from modules.map_data import MapRSE

BAR = "=" * 100

#: The five gauntlet rooms. The four E4 rooms are dimensionally identical (13x14); the Champion's
#: room is 13x13 and its entry warp is one row higher — see §C of the note.
ROOMS = [
    ("SIDNEY", MapRSE.EVER_GRANDE_CITY_SIDNEYS_ROOM),
    ("PHOEBE", MapRSE.EVER_GRANDE_CITY_PHOEBES_ROOM),
    ("GLACIA", MapRSE.EVER_GRANDE_CITY_GLACIAS_ROOM),
    ("DRAKE", MapRSE.EVER_GRANDE_CITY_DRAKES_ROOM),
    ("CHAMPION", MapRSE.EVER_GRANDE_CITY_CHAMPIONS_ROOM),
]

#: The tiles the victory script rewrites, plus the column between the player and the door.
DOOR_TILES = [(6, 1), (6, 2)]


def collision_at(map_enum, tile):
    try:
        return get_map_data(map_enum, tile).collision
    except Exception as error:  # noqa: BLE001 — a failed read is a RESULT here, not a crash
        return f"ERR:{type(error).__name__}"


def main() -> int:
    save = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("post_ch24_atdoor.ss1")
    if not save.is_absolute():
        for base in (pathlib.Path(__file__).resolve().parent / "saves", pathlib.Path.cwd()):
            if (base / save).exists():
                save = base / save
                break

    print(BAR)
    print("THE ROM LAYOUT'S VIEW OF THE ELITE FOUR DOORS — before any script has run")
    print(BAR)
    print(f"save: {save}")
    print("‼ The save's POSITION is irrelevant: the ROM layout is static and `get_map_data` takes")
    print("  any map. Only the LIVE grid would require standing in the room.")
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    failures = []
    print("\n  collision: 0 = walkable, 1 = blocked (higher values are elevation-ish transitions)\n")
    for name, map_enum in ROOMS:
        size = get_map_data(map_enum, (0, 0)).map_size
        door = {t: collision_at(map_enum, t) for t in DOOR_TILES}
        c1 = collision_at(map_enum, (6, 7))          # must be walkable
        c2 = collision_at(map_enum, (0, 0))          # must be a wall
        c3 = collision_at(map_enum, (6, 5))          # trainer's tile, reported only
        door_txt = "  ".join(f"{t}={v}" for t, v in door.items())
        print(f"  {name:<9} {map_enum.name:<40} size={size}")
        print(f"      DOOR TILES : {door_txt}")
        print(f"      C1 (6,7) player end tile, must be WALKABLE : {c1}"
              f"   {'PASS' if c1 == 0 else 'FAIL'}")
        print(f"      C2 (0,0) corner, must be a WALL            : {c2}"
              f"   {'PASS' if c2 not in (0,) else 'FAIL'}")
        print(f"      C3 (6,5) trainer tile (reported, not asserted): {c3}")
        if c1 != 0:
            failures.append(f"{name} C1 (6,7) read {c1}, expected 0")
        if c2 == 0:
            failures.append(f"{name} C2 (0,0) read 0, expected a wall")
        print("")

    print(BAR)
    if failures:
        print("  ⛔ CONTROL FAILURE — the reader is wrong, so NO verdict below can be trusted:")
        for f in failures:
            print(f"      {f}")
        print(BAR)
        return 1

    blocked = []
    for name, map_enum in ROOMS:
        vals = [collision_at(map_enum, t) for t in DOOR_TILES]
        if any(v != 0 for v in vals):
            blocked.append(name)

    print("  VERDICT")
    if len(blocked) == len(ROOMS):
        print("      Every room's door tiles read NON-WALKABLE in the ROM layout.")
        print("      ⇒ the §D'' premise SURVIVES this attempt to refute it: our planner, which reads")
        print("        ROM, cannot route through a door that only `setmetatile` opens.")
        print("      ‼ STILL NOT PROVEN — this is only the ROM half. The LIVE half needs a save taken")
        print("        AFTER a victory, then `probe_live_mapgrid.py <save> EVER_GRANDE_CITY_SIDNEYS_ROOM`.")
    elif not blocked:
        print("      ⛔⛔ EVERY room's door tiles are ALREADY WALKABLE in the ROM layout.")
        print("      ⇒ THE §D'' PREMISE IS REFUTED. Our planner would route through the door with no")
        print("        live-grid read at all, and the §Ch24 build order must be reconsidered AGAIN.")
    else:
        print(f"      ⚠ MIXED — blocked in {blocked}, walkable in the rest. Neither the premise nor its")
        print("        refutation holds uniformly; treat each room separately and say so.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
