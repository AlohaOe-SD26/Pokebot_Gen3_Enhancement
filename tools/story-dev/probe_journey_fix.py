"""#24-journey / KI-39 — A/B PROOF that map-granularity warp planning fixes the real bug.

THE BUG, as measured on 2026-07-31 (`probe_journey_why.py`, `probe_journey_walls.py`):
VERDANTURF_TOWN declares a North map CONNECTION to ROUTE116, so `warp_graph`'s union-find
merges them into one region. But **0 of 40 sampled ROUTE116 tiles are walkable from
Verdanturf**, while the RUSTURF_TUNNEL door at VERDANTURF (8,1) IS reachable. The only
passable link is a WARP INSIDE ONE REGION — and `WarpGraph.plan()` returns `[]` for any
same-region pair, so `navigate_to_anywhere` could never be told about it.

THE A/B. Same graph, same save, same live emulator:
  OLD arm — `graph.plan(from, to)`            -> what the code asked before
  NEW arm — `graph.warp_candidates(from, to)` -> what it asks now
plus, for each candidate, the SAME `calculate_path` the executor uses to validate the
first leg. A candidate that cannot be walked to is not a fix, so it is measured, not
assumed.

CONTROL CASES ARE INCLUDED ON PURPOSE. A planner that suddenly returns a warp route for
everything would be a regression wearing a fix's clothes, so this also asserts that trips
which already WALK fine still report "walkable, no warp needed".

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_journey_fix.py
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
context.bot_mode = "Manual"

from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar
from modules.warp_graph import get_warp_graph

SAVES = REPO / "tools" / "story-dev" / "saves"
FAILURES: list[str] = []


def name_of(m) -> str:
    try:
        return MapRSE(tuple(m)).name
    except ValueError:
        return str(tuple(m))


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def walkable(src, src_xy, dst, dst_xy) -> bool:
    try:
        calculate_path((tuple(src), tuple(src_xy)), (tuple(dst), tuple(dst_xy)))
        return True
    except (PathFindingError, Exception):
        return False


def main() -> int:
    context.emulator.load_save_state((SAVES / "rocksmash_taught.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    a = get_player_avatar()
    here, here_xy = tuple(a.map_group_and_number), tuple(a.local_coordinates)
    graph = get_warp_graph()
    print(f"PLAYER {name_of(here)} {here_xy}")
    print(f"GRAPH  {graph.stats()}\n")

    # The map-level adjacency must survive the cache round-trip, or the fix silently
    # reverts to region granularity on every run after the first.
    print("0. the graph kept its MAP-level adjacency")
    # Assert the PROPERTY, not a magic count: most of the 518 maps are interiors with no
    # edge connections at all, so "> N maps have connections" is a number with no meaning
    # behind it (08-MISTAKES: a threshold justified by one worked example is a guess with
    # arithmetic attached). Mauville's four neighbours are ROM-verified in
    # `probe_journey_why.py`'s header dump: North ROUTE111, South ROUTE110, West ROUTE117,
    # East ROUTE118.
    mauville_neighbours = graph.connections.get(tuple(MapRSE.MAUVILLE_CITY.value), set())
    expected = {tuple(MapRSE.ROUTE110.value), tuple(MapRSE.ROUTE111.value),
                tuple(MapRSE.ROUTE117.value), tuple(MapRSE.ROUTE118.value)}
    check("Mauville's four ROM-declared neighbours all survived into the graph",
          expected <= mauville_neighbours,
          f"missing {sorted(name_of(m) for m in expected - mauville_neighbours)}")
    check("adjacency is symmetric (you can always walk back the way you came)",
          tuple(MapRSE.MAUVILLE_CITY.value) in graph.connections.get(tuple(MapRSE.ROUTE117.value), set()))
    check("Verdanturf's declared North connection to Route 116 is in the graph",
          tuple(MapRSE.ROUTE116.value) in graph.connections.get(tuple(MapRSE.VERDANTURF_TOWN.value), set()))

    VERD = tuple(MapRSE.VERDANTURF_TOWN.value)
    R116 = tuple(MapRSE.ROUTE116.value)

    print("\n1. THE BUG — same region, and the only link is a warp")
    check("Verdanturf and Route 116 really are ONE region (the collapse that hides the warp)",
          graph.region_of(VERD) == graph.region_of(R116),
          f"regions {graph.region_of(VERD)} / {graph.region_of(R116)}")
    old = graph.plan(VERD, R116)
    check("OLD arm: plan() returns [] — 'no warps needed', which is FALSE",
          old == [], repr(old))
    check("...and walking really is impossible (so [] was wrong, not merely unhelpful)",
          not walkable(VERD, (16, 9), R116, (11, 7)))

    print("\n2. THE FIX — map granularity finds the Rusturf Tunnel warp")
    new = graph.warp_candidates(VERD, R116, limit=6)
    for i, c in enumerate(new, 1):
        reach = walkable(VERD, (16, 9), c.from_map, c.from_coords)
        print(f"     candidate {i}: {name_of(c.from_map)}{c.from_coords} -> "
              f"{name_of(c.to_map)}{c.to_coords}   leg-1 walkable={reach}")
    check("NEW arm: at least one warp candidate is offered", len(new) > 0, f"{len(new)} candidates")
    check("the first candidate is the RUSTURF TUNNEL door at VERDANTURF (8,1)",
          bool(new) and tuple(new[0].from_map) == VERD and tuple(new[0].from_coords) == (8, 1),
          repr(new[0]) if new else "none")
    check("...and its first leg is actually walkable from inside Verdanturf",
          bool(new) and walkable(VERD, (16, 9), new[0].from_map, new[0].from_coords))
    # ‼ The progress filter. Before it, candidates 5 and 6 were the Verdanturf BATTLE TENT
    # LOBBY and MART — real routes (walk in, walk out, then take the tunnel) that make no
    # progress. They are harmless only while an earlier candidate validates.
    junk = {tuple(MapRSE.VERDANTURF_TOWN_BATTLE_TENT_LOBBY.value),
            tuple(MapRSE.VERDANTURF_TOWN_MART.value),
            tuple(MapRSE.VERDANTURF_TOWN_POKEMON_CENTER_1F.value)}
    check("no dead-end-interior candidates survive the progress filter",
          not any(tuple(c.to_map) in junk for c in new),
          ", ".join(name_of(c.to_map) for c in new))
    here_d = graph.map_distance(VERD, R116)
    check("no candidate moves AWAY from the target",
          all((graph.map_distance(c.to_map, R116) or 99) <= here_d for c in new),
          f"from Verdanturf d={here_d}; "
          + ", ".join(f"{name_of(c.to_map)} d={graph.map_distance(c.to_map, R116)}" for c in new))
    # ‼ And the criterion must NOT be "strictly closer": the phantom Verdanturf->Route116
    # connection puts the target 1 hop away, so a strict test would filter out the very
    # warp that works. Pin that, so nobody "tightens" it back into a bug.
    check("the phantom connection really does make the target look 1 hop away "
          "(which is why 'strictly closer' would be wrong)", here_d == 1, f"d={here_d}")

    print("\n3. FROM MAUVILLE (the real starting point) — the whole journey now plans")
    cands = graph.warp_candidates(here, R116, limit=6)
    usable = [c for c in cands if walkable(here, here_xy, c.from_map, c.from_coords)]
    for c in cands:
        print(f"     candidate: {name_of(c.from_map)}{c.from_coords} -> {name_of(c.to_map)}"
              f"   leg-1 walkable from Mauville={walkable(here, here_xy, c.from_map, c.from_coords)}")
    check("Mauville -> Route116 offers a warp candidate", len(cands) > 0)
    check("at least one candidate's first leg is walkable from Mauville RIGHT NOW",
          len(usable) > 0, f"{len(usable)} of {len(cands)}")

    print("\n4. CONTROLS — a fix must not turn every walk into a warp detour")
    for label, target, xy in (
        ("Mauville -> ROUTE117 (31,16), the KI-39 control that always worked", MapRSE.ROUTE117, (31, 16)),
        ("Mauville -> VERDANTURF (16,9), several maps but plainly walkable", MapRSE.VERDANTURF_TOWN, (16, 9)),
    ):
        ok = walkable(here, here_xy, tuple(target.value), xy)
        check(f"{label}: still walkable, so the executor takes the UNCHANGED fast path", ok)

    print("\n5. HONEST REFUSALS — what this fix does NOT solve (measure it, don't claim it)")
    # FIERY_PATH is the counter the ladder names. Its only Mauville-side doors are on
    # ROUTE112, which sits behind the ROCK SMASH twin-rocks choke at ROUTE111 (18,101):
    # measured reachable y>=102, blocked y<=101 on columns 17-20.
    FIERY = tuple(MapRSE.FIERY_PATH.value)
    fcands = graph.warp_candidates(here, FIERY, limit=6)
    fusable = [c for c in fcands if walkable(here, here_xy, c.from_map, c.from_coords)]
    for c in fcands:
        print(f"     candidate: {name_of(c.from_map)}{c.from_coords} -> {name_of(c.to_map)}"
              f"   leg-1 walkable={walkable(here, here_xy, c.from_map, c.from_coords)}")
    check("FIERY_PATH: a warp route IS found (the planner is not the missing piece)",
          len(fcands) > 0, f"{len(fcands)} candidates")
    check("FIERY_PATH: but NO candidate's first leg is walkable — the Rock Smash choke at "
          "ROUTE111 (18,101) is the real blocker, not route planning",
          len(fusable) == 0, f"{len(fusable)} usable")

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
