"""
Warp-aware world graph (sandbox enhancement #8).

Upstream's pathfinding (modules/map_path.py) is limited to 'regions' of
directly-connected maps: warps (doors, stairs, cave entrances) can be walked
INTO but never planned THROUGH. This module builds the missing world model:

- Maps that are joined by edge connections (North/South/East/West) form a
  REGION (upstream's `navigate_to` can already walk freely within one).
- Every warp is a directed EDGE from the tile you step on in one region to
  the arrival tile in another region.

`plan()` finds a shortest sequence of warp edges between any two maps, and
`modules/modes/util/global_navigation.py` turns that plan into actual
walking. The graph is extracted from the game's own map headers (ROM data,
readable through the emulator at any time — no save needed) and cached to
disk per ROM, so extraction only happens once per game version.

Honest limitations (deliberate):
- Dive/Emerge connections and 'dynamic' warps (destination stored in save
  data, e.g. Secret Bases; group/number 127/127) are excluded from the
  graph — routes will simply not use them.
- The graph does not know about locked doors or event-gated warps; if a
  planned warp fails in practice, navigation raises a friendly error.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from modules.context import context
from modules.map import get_map_data
from modules.map_data import MapFRLG, MapRSE
from modules.runtime import get_base_path

#: 2 (2026-07-31, #24-journey): the cache now also stores MAP-LEVEL connection adjacency.
#: Version 1 only stored `regions`, which is the union-find COLLAPSE of that adjacency and
#: cannot be un-collapsed — and collapsing it is exactly what made same-region warp routes
#: unplannable (KI-39). Bumping the version makes every old cache rebuild, which is right.
CACHE_VERSION = 2
_CONNECTION_DIRECTIONS = {"North", "South", "East", "West"}
_DYNAMIC_WARP_MARKER = 127


@dataclass(frozen=True)
class WarpEdge:
    """A traversable warp: stand on/walk into `from_coords` on `from_map`
    and you arrive at `to_coords` on `to_map`."""

    from_map: tuple[int, int]
    from_coords: tuple[int, int]
    to_map: tuple[int, int]
    to_coords: tuple[int, int]

    def to_json(self) -> list:
        return [list(self.from_map), list(self.from_coords), list(self.to_map), list(self.to_coords)]

    @classmethod
    def from_json(cls, data: list) -> "WarpEdge":
        return cls(tuple(data[0]), tuple(data[1]), tuple(data[2]), tuple(data[3]))


class WarpGraph:
    def __init__(
        self,
        regions: dict[tuple[int, int], int],
        edges: list[WarpEdge],
        connections: dict[tuple[int, int], set[tuple[int, int]]] | None = None,
    ):
        # map (group, number) -> region id; maps sharing a region are walkable
        # without any warp via upstream navigate_to().
        self.regions = regions
        self.edges = edges
        #: MAP-level edge adjacency, i.e. `regions` BEFORE the union-find collapse.
        #: Kept because the collapse is lossy in exactly the way that matters: two maps in
        #: one region may still need a warp to get between them (see `warp_candidates`).
        self.connections: dict[tuple[int, int], set[tuple[int, int]]] = connections or {}
        self._edges_by_region: dict[int, list[WarpEdge]] = {}
        self._edges_by_map: dict[tuple[int, int], list[WarpEdge]] = {}
        for edge in edges:
            if edge.from_map in self.regions:
                self._edges_by_region.setdefault(self.regions[edge.from_map], []).append(edge)
            self._edges_by_map.setdefault(edge.from_map, []).append(edge)

    # ------------------------------------------------------------ planning
    def region_of(self, map_group_and_number: tuple[int, int]) -> int | None:
        return self.regions.get(tuple(map_group_and_number))

    def warp_candidates(
        self, from_map: tuple[int, int], to_map: tuple[int, int], limit: int = 6
    ) -> list[WarpEdge]:
        """Distinct FIRST warps of short map-level routes `from_map` -> `to_map`.

        ‼ WHY THIS EXISTS — it is the whole of KI-39. `plan()` works at REGION
        granularity and returns `[]` ("no warps needed") the moment start and goal share a
        region. Measured 2026-07-31: the ENTIRE Hoenn overworld is one region, so every
        overworld->overworld trip got `[]` and the warp planner was never consulted — even
        when the only physical link IS a warp. Proven case: VERDANTURF_TOWN declares a North
        map CONNECTION to ROUTE116, so the union-find merges them; but **0 of 40 sampled
        ROUTE116 tiles are walkable from Verdanturf**, while the RUSTURF_TUNNEL door at
        VERDANTURF (8,1) is reachable. The declared connection is not a walkable link; the
        real one is a warp INSIDE one region, which `plan()` can never return.

        Returns the first warp of the shortest route, then of the shortest route that does
        NOT use that warp, and so on — up to `limit`. The caller validates each against the
        live world with `calculate_path` and takes the first that is actually walkable-to,
        which is what makes this robust to the graph's own blind spots (a declared-but-
        unwalkable connection, a locked door, a rock in the way).

        Empty list = no warp-using route is known (which is NOT the same as "you can walk
        there" — the caller decides that with `calculate_path`, not with this).
        """
        from_map, to_map = tuple(from_map), tuple(to_map)
        here_distance = self.map_distance(from_map, to_map)
        banned: set[WarpEdge] = set()
        out: list[WarpEdge] = []
        # Search past rejects — otherwise one dead-end interior costs us a whole slot.
        for _ in range(max(0, limit) * 3):
            if len(out) >= max(0, limit):
                break
            first = self._first_warp_of_shortest_route(from_map, to_map, banned)
            if first is None:
                break
            banned.add(first)
            # ‼ PROGRESS FILTER. Banning the previous answer makes the search offer
            # increasingly silly routes: measured Verdanturf->Route116 returned the
            # BATTLE TENT LOBBY and the MART as candidates 5 and 6 — genuine routes
            # (walk in, walk out, then take the tunnel) that go nowhere. They are only
            # harmless while an earlier candidate validates; if one ever didn't, the
            # executor would walk into a shop, re-plan, and have banned the good warp.
            # Reject only candidates that move AWAY from the target. ‼ NOT "strictly
            # closer" — that criterion is wrong for the exact case this method exists for:
            # the phantom Verdanturf->Route116 connection makes the graph distance 1, so
            # nothing can beat it and the Rusturf Tunnel (also 1) would be filtered out.
            # The graph distance is untrustworthy precisely BECAUSE of phantom connections,
            # so it is used only as a coarse junk filter; the executor's `calculate_path`
            # validation and its `used_warps` set are what actually keep this honest.
            if here_distance is not None:
                onward = self.map_distance(first.to_map, to_map)
                if onward is None or onward > here_distance:
                    continue
            out.append(first)
        return out

    def map_route(self, from_map: tuple[int, int], to_map: tuple[int, int]) -> "list[tuple[int, int]] | None":
        """The maps a shortest journey passes through, EXCLUDING `from_map`, or None.

        Not a walking plan — connection edges here can be phantoms (see `warp_candidates`),
        so this is only good for "which maps is this journey about". `#24-smashroute` uses
        it to decide where to look for a field-move obstacle: the rock that seals the
        Mauville->Fiery Path corridor is on ROUTE111, which is neither the start nor the
        destination, so searching only those two would never find it.
        """
        from_map, to_map = tuple(from_map), tuple(to_map)
        if from_map == to_map:
            return []
        visited = {from_map}
        queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque([(from_map, [])])
        while queue:
            current, path = queue.popleft()
            neighbours = list(self.connections.get(current, ()))
            neighbours += [edge.to_map for edge in self._edges_by_map.get(current, ())]
            for neighbour in neighbours:
                if neighbour in visited:
                    continue
                new_path = path + [neighbour]
                if neighbour == to_map:
                    return new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))
        return None

    def map_distance(self, from_map: tuple[int, int], to_map: tuple[int, int]) -> "int | None":
        """Fewest map transitions (connection OR warp, uniform cost) between two maps.

        Uniform weighting is deliberate and matches `story.region_reach`: a connection can
        span a whole route's walk and a warp can be one doorway, so this is a coarse "how
        many map transitions", not a real distance. It is used only to answer "does this
        warp take me CLOSER", which uniform cost answers correctly.
        """
        from_map, to_map = tuple(from_map), tuple(to_map)
        if from_map == to_map:
            return 0
        visited = {from_map}
        queue: deque[tuple[tuple[int, int], int]] = deque([(from_map, 0)])
        while queue:
            current, hops = queue.popleft()
            for neighbour in self.connections.get(current, ()):
                if neighbour in visited:
                    continue
                if neighbour == to_map:
                    return hops + 1
                visited.add(neighbour)
                queue.append((neighbour, hops + 1))
            for edge in self._edges_by_map.get(current, ()):
                if edge.to_map in visited:
                    continue
                if edge.to_map == to_map:
                    return hops + 1
                visited.add(edge.to_map)
                queue.append((edge.to_map, hops + 1))
        return None

    def _first_warp_of_shortest_route(
        self, from_map: tuple[int, int], to_map: tuple[int, int], banned: "set[WarpEdge]"
    ) -> "WarpEdge | None":
        """BFS the MAP graph and return the first warp of the shortest route that USES AT
        LEAST ONE WARP. None if no such route exists.

        ‼ THE "AT LEAST ONE WARP" REQUIREMENT IS THE POINT, not a quirk. The caller only
        asks after `calculate_path` has already refused the direct walk, so a route the
        graph thinks needs no warp is a route that has just been REFUTED in the live world.
        Returning it would hand back the same failing plan. The Verdanturf->Route116 case is
        exactly this: the ROM declares a map connection (so the graph sees a 1-hop walk)
        while the only passable link is the Rusturf Tunnel warp.

        State is `(map, has_used_a_warp)` rather than `map`, because a map first reached
        without a warp must still be explorable as a warp-using state — collapsing the two
        would let a cheap walk-only prefix permanently mask the warp route behind it.
        Bounded by the visited set (at most 2x the map count), so it always terminates.
        """
        if from_map == to_map:
            return None
        visited: set[tuple[tuple[int, int], bool]] = {(from_map, False)}
        queue: deque[tuple[tuple[int, int], bool, "WarpEdge | None"]] = deque([(from_map, False, None)])
        while queue:
            current, used_warp, first = queue.popleft()
            for neighbour in self.connections.get(current, ()):
                state = (neighbour, used_warp)
                if state in visited:
                    continue
                if neighbour == to_map and used_warp:
                    return first
                visited.add(state)
                queue.append((neighbour, used_warp, first))
            for edge in self._edges_by_map.get(current, ()):
                if edge in banned:
                    continue
                state = (edge.to_map, True)
                if state in visited:
                    continue
                new_first = first if first is not None else edge
                if edge.to_map == to_map:
                    return new_first
                visited.add(state)
                queue.append((edge.to_map, True, new_first))
        return None

    def plan(
        self, from_map: tuple[int, int], to_map: tuple[int, int]
    ) -> list[WarpEdge] | None:
        """Shortest warp sequence (BFS, fewest warps) from the region of
        `from_map` to the region of `to_map`. Empty list = same region.
        None = no known route."""
        start = self.region_of(from_map)
        goal = self.region_of(to_map)
        if start is None or goal is None:
            return None
        if start == goal:
            return []

        # BFS over regions; edges are directed, so one-way warps are honest.
        visited = {start}
        queue: list[tuple[int, list[WarpEdge]]] = [(start, [])]
        while queue:
            region, path = queue.pop(0)
            for edge in self._edges_by_region.get(region, []):
                target_region = self.regions.get(edge.to_map)
                if target_region is None or target_region in visited:
                    continue
                new_path = path + [edge]
                if target_region == goal:
                    return new_path
                visited.add(target_region)
                queue.append((target_region, new_path))
        return None

    def stats(self) -> dict:
        return {
            "maps": len(self.regions),
            "regions": len(set(self.regions.values())),
            "warp_edges": len(self.edges),
            "connection_edges": sum(len(v) for v in self.connections.values()),
        }

    # ------------------------------------------------------------ build
    @classmethod
    def build(cls) -> "WarpGraph":
        """Extract the world graph from the running game's map headers.
        Requires `context.emulator`/`context.rom` (any state — ROM data)."""
        map_enum = MapRSE if context.rom.is_rse else MapFRLG

        map_tuples: list[tuple[int, int]] = []
        for member in map_enum:
            try:
                get_map_data(member.value, (0, 0))
            except (ValueError, KeyError):
                continue  # map does not exist in this game revision
            map_tuples.append(tuple(member.value))

        # --- pass 1: regions via union-find over edge connections
        parent: dict[tuple[int, int], tuple[int, int]] = {m: m for m in map_tuples}

        def find(node: tuple[int, int]) -> tuple[int, int]:
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(a: tuple[int, int], b: tuple[int, int]) -> None:
            root_a, root_b = find(a), find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        # ‼ The adjacency is KEPT, not just consumed by the union-find. Collapsing it into
        # region ids is what made same-region warp routes unplannable (KI-39, #24-journey).
        connections: dict[tuple[int, int], set[tuple[int, int]]] = {}
        for map_tuple in map_tuples:
            map_data = get_map_data(map_tuple, (0, 0))
            for connection in map_data.connections:
                if connection.direction not in _CONNECTION_DIRECTIONS:
                    continue  # Dive/Emerge need HM08 — excluded on purpose
                destination = (connection.destination_map_group, connection.destination_map_number)
                if destination in parent:
                    union(map_tuple, destination)
                    # Edge connections are physically two-way — you can always walk back the
                    # way you came — even when only one side's header declares them.
                    connections.setdefault(map_tuple, set()).add(destination)
                    connections.setdefault(destination, set()).add(map_tuple)

        region_ids: dict[tuple[int, int], int] = {}
        root_to_id: dict[tuple[int, int], int] = {}
        for map_tuple in map_tuples:
            root = find(map_tuple)
            if root not in root_to_id:
                root_to_id[root] = len(root_to_id)
            region_ids[map_tuple] = root_to_id[root]

        # --- pass 2: warp edges
        edges: list[WarpEdge] = []
        for map_tuple in map_tuples:
            map_data = get_map_data(map_tuple, (0, 0))
            for warp in map_data.warps:
                dest_group = warp.destination_map_group
                dest_number = warp.destination_map_number
                if dest_group == _DYNAMIC_WARP_MARKER and dest_number == _DYNAMIC_WARP_MARKER:
                    continue  # dynamic warp (save-data destination) — excluded
                destination = (dest_group, dest_number)
                if destination not in region_ids:
                    continue
                # Arrival coordinates: the destination map's warp with the
                # given id, or (special case 0xFF) this warp's own coords.
                warp_id = warp.destination_warp_id
                if warp_id == 0xFF:
                    arrival = warp.local_coordinates
                else:
                    destination_warps = get_map_data(destination, (0, 0)).warps
                    if warp_id >= len(destination_warps):
                        continue  # malformed warp entry — skip honestly
                    arrival = destination_warps[warp_id].local_coordinates
                edges.append(
                    WarpEdge(
                        from_map=map_tuple,
                        from_coords=tuple(warp.local_coordinates),
                        to_map=destination,
                        to_coords=tuple(arrival),
                    )
                )

        return cls(region_ids, edges, connections)

    # ------------------------------------------------------------ cache
    def save_cache(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": CACHE_VERSION,
            "regions": [[list(k), v] for k, v in self.regions.items()],
            "edges": [edge.to_json() for edge in self.edges],
            # Map-level adjacency (see CACHE_VERSION's note): without it a cache load
            # would silently produce a graph that cannot plan same-region warp routes.
            "connections": [[list(k), [list(v) for v in vs]] for k, vs in self.connections.items()],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load_cache(cls, path: Path) -> "WarpGraph | None":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("version") != CACHE_VERSION:
                return None  # not our object / wrong version -> rebuild
            regions = {tuple(entry[0]): entry[1] for entry in payload["regions"]}
            edges = [WarpEdge.from_json(entry) for entry in payload["edges"]]
            # `connections` is REQUIRED at version 2; a KeyError here correctly falls
            # through to the `except` below and rebuilds rather than loading a graph that
            # would quietly lose `warp_candidates`.
            connections = {tuple(entry[0]): {tuple(v) for v in entry[1]} for entry in payload["connections"]}
            return cls(regions, edges, connections)
        except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
            return None  # corrupt/missing cache -> rebuild


_graph_singleton: WarpGraph | None = None
_graph_rom_id: str | None = None


def _cache_path() -> Path:
    safe_rom_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(context.rom.id))
    return get_base_path() / "cache" / f"warp_graph_{safe_rom_id}.json"


def get_warp_graph() -> WarpGraph:
    """Lazy singleton: disk cache if valid, else extract from the ROM and cache."""
    global _graph_singleton, _graph_rom_id
    if _graph_singleton is not None and _graph_rom_id == context.rom.id:
        return _graph_singleton

    graph = WarpGraph.load_cache(_cache_path())
    if graph is None:
        graph = WarpGraph.build()
        try:
            graph.save_cache(_cache_path())
        except OSError:
            pass  # cache is an optimization, never a requirement

    _graph_singleton = graph
    _graph_rom_id = context.rom.id
    return graph
