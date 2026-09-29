"""Design v2 step 7 (RP): does Snorunt's only room need Strength AND Surf from the story path? Measured with
PRODUCTION's pathfinder, `modules.map_path.calculate_path`, not with a hand-written flood fill.

WHY THIS EXISTS. `probe_rarity_access_gates.py` (an independent verifier's flood fill) says yes, but its pre-registered
control did not reproduce (296/333 tiles against the recorded 262/299; `2026-09-29-rarepredicate-PREDICTIONS.md` R3),
and the predictions said nothing else that probe prints is believed. So the facts the table depends on are
re-measured here with the bot's own pathfinder:

  S1  the Ice Room's ONLY entrance is the Lower Room warp (28,11).
  S2  NECESSITY of Strength: with the Lower Room boulder in place, NO arrival into the Lower Room has a path to (28,11),
      while the tile beside the boulder IS reachable. SUFFICIENCY: with the boulder PUSHED east three times to (28,3)
      (a live object there, its template tile free) a path exists; pushed only twice, to (27,3), none does.
  S3  NECESSITY of Surf: from the Route 125 cave warp itself, on foot, there is no path to Mossdeep (the story-path
      city beside it), while a tile next to the warp IS reachable on foot. From Mossdeep, the warp is reachable with
      Surf and not without.
  S4  SUFFICIENCY at low tide, room to room: on foot from the Route 125 arrival, following warps and asking
      `calculate_path` inside each room, the search reaches a Lower Room arrival from which the push tile is reachable,
      and never the Ice Room (the boulder is in place); the Ice Room arrival reaches an encounter tile.

‼ WHAT THIS INSTRUMENT IS AND IS NOT (the step 7 review). `calculate_path` is not a controlled instrument either: on
Meteor Falls 1F_1R it reaches about 293 tiles on foot where the controlled 2026-09-11 decoder reached 262. It is MORE
permissive there. So its NO-PATH readings (S2 boulder in place, S2 two pushes, S3 on foot) are CONSERVATIVE. The
pseudo verdict needs only those: two gates are NECESSARY. The PATH readings (S2 three pushes, S3 with Surf, S4) show
sufficiency with a permissive instrument, and are reported as such.

HOW THE BOULDER IS MODELLED. `calculate_path` treats an object-template tile as a wall while the object's hide-flag
is CLEAR and the object is not currently loaded (`map_path.py` `is_tile_accessible`, the `dynamic_collision_flag`
branch). The player is in Mossdeep, so the Lower Room boulder (graphics 87, flag 0x11) is never loaded. Arm A forces
flag 0x11 CLEAR (boulder present). Arm B forces it SET (boulder gone), and is kept only as a contrast. Arms C and D
keep the flag clear and inject a fake LIVE boulder (local id 1) at (28,3) or (27,3). A live object frees its
template tile and walls its current tile, which is exactly a pushed boulder.

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_rarity_shoal_path.py
Exit:  1 if any check or control fails; 0 otherwise.
"""

import pathlib
import sys
from types import SimpleNamespace

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
from modules.map import get_map_all_tiles, get_map_data  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.player import get_player_avatar  # noqa: E402

LOWER = MapRSE.SHOAL_CAVE_LOW_TIDE_LOWER_ROOM.value
ICE = MapRSE.SHOAL_CAVE_LOW_TIDE_ICE_ROOM.value
ENTRANCE = MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM.value
INNER = MapRSE.SHOAL_CAVE_LOW_TIDE_INNER_ROOM.value
R125 = MapRSE.ROUTE125.value
MOSSDEEP = MapRSE.MOSSDEEP_CITY.value
ICE_WARP = (28, 11)
PUSH_TILE = (24, 3)
BOULDER_FLAG = 0x11
BOULDER_ID = 1
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


def warps_into(dest):
    """[(source map, warp tile, arrival tile on `dest`)] over every Shoal Cave map and Route 125."""
    out = []
    for m in [m for m in MapRSE if m.name.startswith("SHOAL_CAVE_")] + [MapRSE.ROUTE125]:
        for w in get_map_data(m, (0, 0)).warps:
            if (w.destination_map_group, w.destination_map_number) == dest:
                arrival = get_map_data(dest, (0, 0)).warps[w.destination_warp_id].local_coordinates
                out.append((m.value, w.local_coordinates, arrival))
    return out


def warp_tiles_to(src_map, dest):
    return [w.local_coordinates for w in get_map_data(src_map, (0, 0)).warps
            if (w.destination_map_group, w.destination_map_number) == dest]


def main() -> int:
    player = get_player_avatar()
    print(f"anchor: post_dive.ss1, player on {MapRSE(player.map_group_and_number).name} {player.local_coordinates}")
    real_flag, real_objects = mp.get_event_flag_by_number, mp.get_map_objects

    # ------------------------------------------------------------------------------------------------ S1
    print("\nS1 — every warp INTO the Ice Room")
    into_ice = warps_into(ICE)
    for src, xy, arr in into_ice:
        print(f"    {MapRSE(src).name} {xy} -> ICE_ROOM arriving {arr}")
    check("S1 the Ice Room's only entrance is the Lower Room warp (28,11)",
          [(src, xy) for src, xy, _ in into_ice] == [(LOWER, ICE_WARP)], str(into_ice))
    boulder = [o for o in get_map_data(LOWER, (0, 0)).objects if o.local_coordinates == (25, 3)]
    check("the Lower Room has a pushable boulder (graphics 87, local id 1) at (25,3) with hide-flag 0x11",
          len(boulder) == 1 and boulder[0].graphics_id == 87 and boulder[0].flag_id == BOULDER_FLAG
          and boulder[0].local_id == BOULDER_ID, str([(o.graphics_id, o.flag_id, o.local_id) for o in boulder]))

    # ------------------------------------------------------------------------------------------------ S2
    arrivals = [arr for src, _xy, arr in warps_into(LOWER) if src != ICE]

    def arm(label, *, flag_set: bool, live_boulder_at=None):
        mp.get_event_flag_by_number = lambda n: flag_set if n == BOULDER_FLAG else real_flag(n)
        if live_boulder_at is not None:
            fake = SimpleNamespace(flags=[], map_group_and_number=LOWER, current_coords=live_boulder_at,
                                   previous_coords=live_boulder_at, local_id=BOULDER_ID)
            mp.get_map_objects = lambda: list(real_objects()) + [fake]
        try:
            res = {a: (path_exists((LOWER, a), (LOWER, ICE_WARP), no_surfing=True),
                       path_exists((LOWER, a), (LOWER, PUSH_TILE), no_surfing=True)) for a in arrivals}
        finally:
            mp.get_event_flag_by_number, mp.get_map_objects = real_flag, real_objects
        print(f"    arm {label}: " + "; ".join(f"from {a}: ice-warp={r[0]} push-tile={r[1]}" for a, r in res.items()))
        return res

    print("\nS2 — the Lower Room boulder")
    a = arm("A (boulder at (25,3), flag clear)", flag_set=False)
    b = arm("B (boulder deleted, flag set; contrast only)", flag_set=True)
    c = arm("C (pushed east x3: live boulder at (28,3))", flag_set=False, live_boulder_at=(28, 3))
    d = arm("D (pushed east x2: live boulder at (27,3))", flag_set=False, live_boulder_at=(27, 3))
    check("S2 NECESSITY: boulder in place, no Lower Room arrival has a path to the Ice Room warp",
          not any(r[0] for r in a.values()))
    check("S2 control: boulder in place, the push tile (24,3) IS reachable", any(r[1] for r in a.values()))
    check("S2 SUFFICIENCY: pushed east three times, a path to the Ice Room warp exists",
          any(r[0] for r in c.values()))
    check("S2 pushed only twice, still no path (the three pushes are all needed)", not any(r[0] for r in d.values()))
    check("S2 contrast: deleted, a path exists (the boulder is what blocks it)", any(r[0] for r in b.values()))

    # ------------------------------------------------------------------------------------------------ S3
    print("\nS3 — the Route 125 approach")
    cave_warps = warp_tiles_to(R125, ENTRANCE)
    check("S3 Route 125 has a warp into Shoal Cave", bool(cave_warps), str(cave_warps))
    here = (player.map_group_and_number, player.local_coordinates)
    tiles125 = {t.local_position: t for t in get_map_all_tiles(get_map_data(R125, (0, 0)))}
    tilesmd = {t.local_position: t for t in get_map_all_tiles(get_map_data(MOSSDEEP, (0, 0)))}
    for xy in cave_warps:
        to_mossdeep = path_exists((R125, xy), here, no_surfing=True)
        neighbours = [(xy[0] + dx, xy[1] + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        # Walkable = collision 0 and not elevation 1 (surf water). Shallow Water (elevation 3) IS walkable.
        land = [n for n in neighbours if n in tiles125 and tiles125[n].collision == 0 and tiles125[n].elevation != 1]
        near_ok = [n for n in land if path_exists((R125, xy), (R125, n), no_surfing=True)]
        from_md_foot = path_exists(here, (R125, xy), no_surfing=True)
        from_md_surf = path_exists(here, (R125, xy), no_surfing=False)
        print(f"    ROUTE125 {xy}: on foot to Mossdeep {here[1]} = {to_mossdeep}; land neighbours {land} reached on "
              f"foot {near_ok}; from Mossdeep on foot = {from_md_foot}, with Surf = {from_md_surf}")
        check(f"S3 NECESSITY: from the cave warp {xy}, no on-foot path to Mossdeep", not to_mossdeep)
        check(f"S3 control: from the cave warp {xy}, a land neighbour IS reached on foot", bool(near_ok))
        check(f"S3 from Mossdeep: no path on foot, a path with Surf", not from_md_foot and from_md_surf)
    md_target = next((p for p in sorted(tilesmd, key=lambda p: (abs(p[0] - here[1][0]) + abs(p[1] - here[1][1])))
                      if abs(p[0] - here[1][0]) + abs(p[1] - here[1][1]) >= 5 and tilesmd[p].collision == 0
                      and tilesmd[p].elevation != 1), None)
    check("S3 control: the instrument finds an on-foot path inside Mossdeep at all",
          md_target is not None and path_exists(here, (MOSSDEEP, md_target), no_surfing=True), f"target {md_target}")

    # ------------------------------------------------------------------------------------------------ S4
    print("\nS4 — sufficiency on foot at low tide: a room-to-room search (a permissive instrument: see the docstring)")
    # Nodes are (map, arrival tile). From each node, every warp of that map that `calculate_path` reaches on foot
    # (boulder in place, flag 0x11 as the save has it) leads to the destination's arrival tile.
    rooms = {m.value for m in MapRSE if m.name.startswith("SHOAL_CAVE_LOW_TIDE_")}
    start_nodes = [(ENTRANCE, arr) for src, _xy, arr in warps_into(ENTRANCE) if src == R125]
    seen, frontier, calls = set(start_nodes), list(start_nodes), 0
    while frontier and calls < 400:
        node = frontier.pop()
        for w in get_map_data(node[0], (0, 0)).warps:
            dest = (w.destination_map_group, w.destination_map_number)
            if dest not in rooms:
                continue
            calls += 1
            if path_exists(node, (node[0], w.local_coordinates), no_surfing=True):
                nxt = (dest, get_map_data(dest, (0, 0)).warps[w.destination_warp_id].local_coordinates)
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
    for node in sorted(seen):
        print(f"    reached {MapRSE(node[0]).name} arrival {node[1]}")
    check("S4 the search stayed inside its bound", calls < 400, f"{calls} calculate_path calls")
    push_side = [n for n in seen if n[0] == LOWER and n[1] in a and a[n[1]][1]]
    check("S4 from the Route 125 arrival, on foot, a Lower Room arrival that reaches the push tile is reached",
          bool(push_side), str(push_side))
    check("S4 the Ice Room is NOT reached on foot with the boulder in place (S2's necessity, room to room)",
          not any(n[0] == ICE for n in seen))
    ice_tiles = [t.local_position for t in get_map_all_tiles(get_map_data(ICE, (0, 0)))
                 if t.collision == 0 and t.has_encounters]
    ice_arrival = into_ice[0][2] if into_ice else None
    reached = next((p for p in ice_tiles if ice_arrival and path_exists((ICE, ice_arrival), (ICE, p),
                                                                         no_surfing=True)), None)
    print(f"    Ice Room: {len(ice_tiles)} encounter tiles; from the arrival {ice_arrival}, first reached {reached}")
    check("S4 the Ice Room arrival reaches an encounter tile on foot", reached is not None)

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS — Snorunt's room NEEDS Strength (inside) and Surf (the approach from the story path)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
