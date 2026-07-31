"""Regression test for #24-journey / KI-39 — map-granularity warp planning. NO EMULATOR.

WHAT WENT WRONG (measured live 2026-07-31; see `probe_journey_why.py` /
`probe_journey_walls.py` / `probe_journey_fix.py` for the raw numbers).

`WarpGraph.plan()` answers at REGION granularity, where a region is the union-find collapse
of map CONNECTIONS. The entire Hoenn overworld is one region (461 regions over 518 maps, and
every overworld map is region 0), so `plan()` returned `[]` — "no warps needed" — for every
overworld->overworld trip, and `navigate_to_anywhere` handed the whole journey to
`calculate_path`, which cannot cross a warp.

The case that proves it is not merely theoretical: VERDANTURF_TOWN's map header declares a
North CONNECTION to ROUTE116, so the two are one region — yet **0 of 40 sampled ROUTE116
tiles are walkable from Verdanturf**, while the RUSTURF_TUNNEL door at VERDANTURF (8,1) is
reachable. The declared connection is a phantom; the real link is a WARP INSIDE ONE REGION,
which `plan()` is structurally incapable of returning.

This file rebuilds that exact topology as a tiny synthetic graph and pins the behaviour, so
the bug cannot come back. The live end-to-end proof lives in `probe_journey_live.py` (it
needs a real emulator and takes minutes, so it is not in the sweep):
    OLD arm -> arrived=False map=MAUVILLE_CITY   (never left the starting map)
    NEW arm -> arrived=True  map=ROUTE116        (33,725 frames, via the Rusturf Tunnel)
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.warp_graph import CACHE_VERSION, WarpEdge, WarpGraph  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


# --- The Verdanturf/Route 116 topology, exactly as measured off the ROM ------------
MAUVILLE = (0, 12)
ROUTE117 = (0, 16)
VERD = (0, 14)
R116 = (0, 15)
TUNNEL = (24, 4)   # RUSTURF_TUNNEL — interior, its own region
MART = (24, 90)    # a dead-end interior off Verdanturf

TUNNEL_DOOR = WarpEdge(from_map=VERD, from_coords=(8, 1), to_map=TUNNEL, to_coords=(29, 16))
TUNNEL_EXIT = WarpEdge(from_map=TUNNEL, from_coords=(18, 20), to_map=R116, to_coords=(65, 11))
MART_DOOR = WarpEdge(from_map=VERD, from_coords=(12, 3), to_map=MART, to_coords=(3, 7))
MART_EXIT = WarpEdge(from_map=MART, from_coords=(3, 7), to_map=VERD, to_coords=(12, 3))


def build() -> WarpGraph:
    regions = {MAUVILLE: 0, ROUTE117: 0, VERD: 0, R116: 0, TUNNEL: 1, MART: 2}
    connections = {
        MAUVILLE: {ROUTE117},
        ROUTE117: {MAUVILLE, VERD},
        VERD: {ROUTE117, R116},   # <- THE PHANTOM: declared in the ROM, not walkable
        R116: {VERD},
    }
    edges = [TUNNEL_DOOR, TUNNEL_EXIT, MART_DOOR, MART_EXIT]
    return WarpGraph(regions, edges, connections)


graph = build()

print("1. the bug: region granularity cannot express this route")
check("Verdanturf and Route 116 are ONE region (the collapse that hides the warp)",
      graph.region_of(VERD) == graph.region_of(R116))
check("OLD: plan() returns [] — 'no warps needed', which is false here",
      graph.plan(VERD, R116) == [])
check("OLD: plan() is [] from Mauville too, so distance does not rescue it",
      graph.plan(MAUVILLE, R116) == [])

print("\n2. the fix: map granularity returns the Rusturf Tunnel door")
cands = graph.warp_candidates(VERD, R116)
check("a candidate is offered at all", len(cands) > 0, f"{len(cands)}")
check("the first candidate is the tunnel door at VERDANTURF (8,1)",
      bool(cands) and cands[0] == TUNNEL_DOOR, repr(cands[0]) if cands else "none")
check("it also works from two maps away (Mauville)",
      graph.warp_candidates(MAUVILLE, R116)[:1] == [TUNNEL_DOOR],
      repr(graph.warp_candidates(MAUVILLE, R116)[:1]))

print("\n3. the 'at least one warp' rule")
# ‼ Without it, BFS finds the 1-hop PHANTOM connection, reports 'no warp needed', and hands
# back the plan `calculate_path` has already refused — i.e. exactly the old behaviour.
check("a warp-using route is returned even though a shorter warp-free route 'exists'",
      TUNNEL_DOOR in graph.warp_candidates(VERD, R116))
check("no candidates when the destination is genuinely unreachable",
      graph.warp_candidates(VERD, (99, 99)) == [])
check("no candidates for a trip to where you already are",
      graph.warp_candidates(VERD, VERD) == [])

print("\n4. the progress filter (dead-end interiors must not be offered)")
# Measured before the filter: candidates 5 and 6 for Verdanturf->Route116 were the BATTLE
# TENT LOBBY and the MART — real routes (walk in, walk out, take the tunnel) that go
# nowhere. Harmless only while an earlier candidate validates.
all_c = graph.warp_candidates(VERD, R116, limit=6)
check("the Mart door is NOT offered", MART_DOOR not in all_c,
      ", ".join(repr(c.to_map) for c in all_c))
check("map_distance sees the Mart as a step backwards",
      graph.map_distance(MART, R116) > graph.map_distance(VERD, R116),
      f"mart={graph.map_distance(MART, R116)} verd={graph.map_distance(VERD, R116)}")

print("\n5. ‼ the filter is NON-INCREASING, not STRICTLY-DECREASING")
# The phantom connection puts Route 116 one hop from Verdanturf, so NOTHING can be strictly
# closer — a 'strictly closer' filter would reject the very warp that works. This test
# exists so that tightening it back is an immediate, loud failure rather than a silent
# regression to the old behaviour.
d_here = graph.map_distance(VERD, R116)
d_tunnel = graph.map_distance(TUNNEL, R116)
check("the phantom connection makes the target look 1 hop away", d_here == 1, f"{d_here}")
check("the tunnel is NOT strictly closer (so a strict filter would drop it)",
      d_tunnel == d_here, f"tunnel={d_tunnel} here={d_here}")
check("...and it is offered anyway", TUNNEL_DOOR in all_c)

print("\n6. map_distance")
check("same map is 0", graph.map_distance(VERD, VERD) == 0)
check("one connection hop", graph.map_distance(MAUVILLE, ROUTE117) == 1)
check("two connection hops", graph.map_distance(MAUVILLE, VERD) == 2)
check("unreachable is None", graph.map_distance(VERD, (99, 99)) is None)

print("\n7. the cache must carry the map-level adjacency")
# ‼ Version 1 stored only `regions`, i.e. the collapse. A cache load that dropped
# `connections` would silently revert every run after the first to region granularity —
# the bug would come back on the SECOND launch and look like flakiness.
check("CACHE_VERSION was bumped past 1", CACHE_VERSION >= 2, str(CACHE_VERSION))
with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "wg.json"
    graph.save_cache(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    check("the cache file contains a connections section", "connections" in payload)
    loaded = WarpGraph.load_cache(path)
    check("the cache round-trips", loaded is not None)
    check("connections survive the round-trip",
          loaded is not None and loaded.connections == graph.connections)
    check("...and the fix still works after a cache load",
          loaded is not None and loaded.warp_candidates(VERD, R116)[:1] == [TUNNEL_DOOR])

    # A version-1 cache (no connections) must REBUILD, never load degraded.
    path.write_text(json.dumps({"version": 1, "regions": [], "edges": []}), encoding="utf-8")
    check("a stale version-1 cache is rejected", WarpGraph.load_cache(path) is None)
    path.write_text(json.dumps({"version": CACHE_VERSION, "regions": [], "edges": []}), encoding="utf-8")
    check("a current-version cache MISSING connections is rejected, not loaded blind",
          WarpGraph.load_cache(path) is None)

print("\n8. the warp-fired check must compare MAPS, not regions")
# ‼ It used to compare REGIONS. A warp between two maps of the SAME region — precisely the
# class this whole change makes plannable — leaves the region unchanged, so a working warp
# would have been reported as "the warp did not trigger (locked or event-gated?)". A correct
# feature would have looked like a locked door.
from modules.modes.util.global_navigation import _warp_fired  # noqa: E402

same_region_warp = WarpEdge(from_map=VERD, from_coords=(8, 1), to_map=R116, to_coords=(65, 11))
check("a SAME-REGION warp that fired is recognised as fired",
      _warp_fired(same_region_warp, R116))
check("a warp that did NOT fire is recognised as not fired",
      not _warp_fired(same_region_warp, VERD))
check("a cross-region warp still works", _warp_fired(TUNNEL_DOOR, TUNNEL))
check("...and its non-firing case too", not _warp_fired(TUNNEL_DOOR, VERD))

print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("ALL PASS")
