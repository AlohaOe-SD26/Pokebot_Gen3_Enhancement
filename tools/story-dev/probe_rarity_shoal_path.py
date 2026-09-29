"""Design v2 step 7 (RP): does Snorunt's only room need Strength AND Surf from the story path? Measured with
PRODUCTION's pathfinder, `modules.map_path.calculate_path`, not with a hand-written flood fill.

WHY THIS EXISTS. `probe_rarity_access_gates.py` (an independent verifier's flood fill) says yes, but its pre-registered
control did not reproduce (296/333 tiles against the recorded 262/299; `2026-09-29-rarepredicate-PREDICTIONS.md` R3),
and the predictions said that nothing else such a probe prints is believed on its own. So the two facts the table
depends on are re-measured here with the bot's own pathfinder:

  S1  the Ice Room's ONLY entrance is the Lower Room warp (28,11);
  S2  with the Lower Room boulder in place, NO arrival into the Lower Room has a path to (28,11), while the tile
      beside the boulder IS reachable (it can be pushed). With the boulder gone, a path exists. ⇒ Strength.
  S3  from Mossdeep (a story-path city; `post_dive.ss1` stands there) the Route 125 warp into Shoal Cave has NO path
      without Surf, and has one with Surf. ⇒ Surf.

HOW THE BOULDER IS MODELLED. `calculate_path` treats an object-template tile as a wall while the object's hide-flag
is CLEAR and the object is not currently loaded (`map_path.py` `is_tile_accessible`, the `dynamic_collision_flag`
branch). The player is in Mossdeep, so the Lower Room boulder (graphics 87, flag 0x11) is never loaded. Arm A forces
flag 0x11 CLEAR (boulder present); arm B forces it SET (boulder gone). Every other flag reads the save.

CONTROLS. The push tile (24,3) must be REACHABLE in arm A (otherwise "no path" could mean "the room is sealed",
not "the boulder seals it"). Arm B must FIND the path arm A does not (otherwise the boulder is not what blocks it).

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_rarity_shoal_path.py
Exit:  1 if any of S1-S3 or either control fails; 0 otherwise.
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
context.emulator.load_save_state((REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1").read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

import modules.map_path as mp  # noqa: E402
from modules.map import get_map_data  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.player import get_player_avatar  # noqa: E402

LOWER = MapRSE.SHOAL_CAVE_LOW_TIDE_LOWER_ROOM.value
ICE = MapRSE.SHOAL_CAVE_LOW_TIDE_ICE_ROOM.value
R125 = MapRSE.ROUTE125.value
ICE_WARP = (28, 11)
PUSH_TILE = (24, 3)
BOULDER_FLAG = 0x11
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def path_exists(src, dst, *, no_surfing: bool) -> bool:
    try:
        mp.calculate_path(src, dst, no_surfing=no_surfing)
        return True
    except mp.PathFindingError:
        return False


def main() -> int:
    player = get_player_avatar()
    print(f"anchor: post_dive.ss1, player on {MapRSE(player.map_group_and_number).name} {player.local_coordinates}")

    print("\nS1 — every warp INTO the Ice Room, from every Shoal Cave map")
    into_ice, into_lower = [], []
    for m in (m for m in MapRSE if m.name.startswith("SHOAL_CAVE_")):
        for w in get_map_data(m, (0, 0)).warps:
            dest = (w.destination_map_group, w.destination_map_number)
            if dest in (ICE, LOWER):
                arrival = get_map_data(dest, (0, 0)).warps[w.destination_warp_id].local_coordinates
                print(f"    {m.name} {w.local_coordinates} -> {MapRSE(dest).name} arriving {arrival}")
                (into_ice if dest == ICE else into_lower).append((m.value, w.local_coordinates, arrival))
    check("S1 the Ice Room's only entrance is the Lower Room warp (28,11)",
          [(src, xy) for src, xy, _ in into_ice] == [(LOWER, ICE_WARP)], str(into_ice))

    boulder = [o for o in get_map_data(LOWER, (0, 0)).objects if o.local_coordinates == (25, 3)]
    check("the Lower Room has a pushable boulder (graphics 87) at (25,3) with hide-flag 0x11",
          len(boulder) == 1 and boulder[0].graphics_id == 87 and boulder[0].flag_id == BOULDER_FLAG,
          str([(o.graphics_id, o.flag_id) for o in boulder]))

    real = mp.get_event_flag_by_number
    arrivals = [arr for src, _xy, arr in into_lower if src != ICE]
    results = {}
    for arm, present in (("A", True), ("B", False)):
        mp.get_event_flag_by_number = lambda n, _p=present: (not _p) if n == BOULDER_FLAG else real(n)
        try:
            results[arm] = {arr: (path_exists((LOWER, arr), (LOWER, ICE_WARP), no_surfing=True),
                                  path_exists((LOWER, arr), (LOWER, PUSH_TILE), no_surfing=True)) for arr in arrivals}
        finally:
            mp.get_event_flag_by_number = real
        print(f"\n  arm {arm} (boulder {'PRESENT' if present else 'GONE'}): "
              + "; ".join(f"from {a}: ice-warp={r[0]} push-tile={r[1]}" for a, r in results[arm].items()))
    check("S2 boulder PRESENT: no Lower Room arrival has a path to the Ice Room warp",
          not any(r[0] for r in results["A"].values()))
    check("S2 control: boulder PRESENT, the push tile (24,3) IS reachable (the boulder can be pushed)",
          any(r[1] for r in results["A"].values()))
    check("S2 control: boulder GONE, a path to the Ice Room warp EXISTS (the boulder is what blocks it)",
          any(r[0] for r in results["B"].values()))

    print("\nS3 — the Route 125 approach from Mossdeep")
    cave_warps = [w.local_coordinates for w in get_map_data(R125, (0, 0)).warps
                  if MapRSE((w.destination_map_group, w.destination_map_number)).name.startswith("SHOAL_CAVE_")]
    src = (player.map_group_and_number, player.local_coordinates)
    for xy in cave_warps:
        on_foot = path_exists(src, (R125, xy), no_surfing=True)
        surfing = path_exists(src, (R125, xy), no_surfing=False)
        print(f"    ROUTE125 {xy}: on foot={on_foot}  with Surf={surfing}")
        check(f"S3 Route 125 cave warp {xy}: no path on foot, a path with Surf", not on_foot and surfing)
    check("S3 the Route 125 side has a Shoal Cave warp at all", bool(cave_warps))

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS — Snorunt's room needs Strength (inside) and Surf (the approach from the story path)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
