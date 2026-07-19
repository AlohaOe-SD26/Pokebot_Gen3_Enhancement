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
from dataclasses import dataclass
from pathlib import Path

from modules.context import context
from modules.map import get_map_data
from modules.map_data import MapFRLG, MapRSE
from modules.runtime import get_base_path

CACHE_VERSION = 1
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
    def __init__(self, regions: dict[tuple[int, int], int], edges: list[WarpEdge]):
        # map (group, number) -> region id; maps sharing a region are walkable
        # without any warp via upstream navigate_to().
        self.regions = regions
        self.edges = edges
        self._edges_by_region: dict[int, list[WarpEdge]] = {}
        for edge in edges:
            if edge.from_map in self.regions:
                self._edges_by_region.setdefault(self.regions[edge.from_map], []).append(edge)

    # ------------------------------------------------------------ planning
    def region_of(self, map_group_and_number: tuple[int, int]) -> int | None:
        return self.regions.get(tuple(map_group_and_number))

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

        for map_tuple in map_tuples:
            map_data = get_map_data(map_tuple, (0, 0))
            for connection in map_data.connections:
                if connection.direction not in _CONNECTION_DIRECTIONS:
                    continue  # Dive/Emerge need HM08 — excluded on purpose
                destination = (connection.destination_map_group, connection.destination_map_number)
                if destination in parent:
                    union(map_tuple, destination)

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

        return cls(region_ids, edges)

    # ------------------------------------------------------------ cache
    def save_cache(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": CACHE_VERSION,
            "regions": [[list(k), v] for k, v in self.regions.items()],
            "edges": [edge.to_json() for edge in self.edges],
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
            return cls(regions, edges)
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
