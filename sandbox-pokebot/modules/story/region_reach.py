"""
Region-scale reachability oracle (#24-regionreach, KI-24).

`_training_area_allowed` (plugins/custom_modes/story_mode.py) and
`modules/story/counter_plan.py` both answer "can the bot get here?" with tile-level
`calculate_path`. That oracle is unsound at REGION scale: proven, from a verified
Winona-era save (ROUTE120, BADGE05_GET, Surf known), it reports ROUTE118 unreachable
from ROUTE120 -- the real answer to Winona -- and it ALSO fails on a same-map walk
inside ROUTE119 alone (y=5 -> y=135, no map crossing at all). Routes 118/119/120 are
the dual-elevation-bridge maps `calculate_path` reads as WALLS; that is exactly why
`_hold_walk_route()` exists. A false negative here is invisible: nothing errors, the
training option is simply never proposed (KI-24).

This module answers the region question honestly: a graph built from the ROM's own
MapConnections (edge-adjacent maps, read live off the loaded ROM -- never a
hand-written table) plus WARPS (Poke Center doors, cave mouths, ...) as directed
edges bridging otherwise-disconnected map clusters. `calculate_path` is still the
correct tool for the final tile-level leg once actually ON a map; this module only
answers "can I get there at all", not "walk me there".

Capability gates: the ROM's connection/warp data does not encode "this edge needs
Surf" -- an all-water route and a dry bridge look identical to it. Where a
requirement cannot be derived from data, it lives in the small `KNOWN_GATES` table
below, and every entry says so explicitly. Never silently assume an edge is
passable: a wrong "yes" sends the bot on a long walk to nowhere, which is worse than
a wrong "no" (this is the same lesson KI-24 is about, just in the other direction).

Fail-safe (never raise into a caller): `reachable_maps` returns `set()` on any read
error, `is_map_reachable` returns False, and `why_unreachable` always explains
itself -- including saying so explicitly when the CHECK failed, never implying the
map itself is unreachable (that distinction is the entire point of this module;
KI-24 happened because a false negative gave no reason at all).

Reachability alone is not enough of a gate (coordinator follow-up, same day):
measured against ROUTE120 at the Winona moment, pure connectivity called 309 maps
"reachable" -- true in the sense that Surf can carry you a long way across Hoenn,
but useless as a filter for "where should I go catch a counter?" if it can't tell
Route 118 (a few hops away) from Mossdeep (many regions away). So reachability
here carries a COST: every edge (connection OR warp) is one hop, and
`reachable_map_distances`/`hops_to` expose the hop count so a caller can ask for
"reachable AND within N hops" via `max_hops`, the same way
`training_areas.estimate_frames_to_level` prices a grind in frames rather than
trusting a level gap alone. A refusal because of `max_hops` is reported as
"reachable but distant" (with the real distance), never confused with "no path
exists at all" or "gated by a missing capability" -- those are three different
facts and KI-24 is exactly about not collapsing them into a silent no.

NOT wired into story_mode.py or counter_plan.py yet -- this module is proven
standalone first (tools/story-dev/repro_region_reach.py); wiring it in is a
follow-up task.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass

_log = logging.getLogger("region_reach")

_CONNECTION_DIRECTIONS = {"North", "South", "East", "West"}  # Dive/Emerge (HM08) are
# not modeled as connection edges here -- same exclusion modules/warp_graph.py makes,
# for the same reason: they need a capability this module doesn't track per-tile.
_DYNAMIC_WARP_MARKER = 127  # warp destination stored in save data (e.g. Secret Bases);
# unresolvable without a save loaded, excluded -- matches modules/warp_graph.py.

# Hand-verified capability gates for map-PAIRS where the ROM's connection/warp data
# alone does not say a capability is required (e.g. an edge-adjacent map that is
# entirely open water). NOT derived from ROM data -- add an entry only after
# confirming in-game which HM/move is actually needed to physically stand on that
# edge. Keys are unordered (map_a, map_b) tuples of (group, number); the gate
# applies to the edge in EITHER direction. Gate values are keys into
# `_GATE_MOVE_NAMES` below.
KNOWN_GATES: dict[tuple[tuple[int, int], tuple[int, int]], str] = {
    # DEWFORD_TOWN's only two map connections are ROUTE106 (north) and ROUTE107
    # (east); both are pure open-water sea routes (hand-verified 2026-07-25 via
    # tools/story-dev recon probe: dumped connections, both maps have no land path
    # to Dewford) -- Surf is required to physically stand on either edge tile.
    ((0, 11), (0, 21)): "surf",  # DEWFORD_TOWN <-> ROUTE106
    ((0, 11), (0, 22)): "surf",  # DEWFORD_TOWN <-> ROUTE107
}

_GATE_MOVE_NAMES = {"surf": "Surf", "rock_smash": "Rock Smash", "cut": "Cut", "strength": "Strength"}

# modules/menuing.py's use_field_move() is the ROM-verified ground truth for which
# badge unlocks which field move outside of battle (RSE vs FRLG differ) -- mirrored
# here rather than re-derived, since map_path.py and capabilities.py already lean on
# the same facts for Surf/Rock Smash.
_RSE_BADGE_BY_MOVE = {
    "Cut": "BADGE01_GET",
    "Rock Smash": "BADGE03_GET",
    "Strength": "BADGE04_GET",
    "Surf": "BADGE05_GET",
}
_FRLG_BADGE_BY_MOVE = {
    "Cut": "BADGE02_GET",
    "Strength": "BADGE04_GET",
    "Surf": "BADGE05_GET",
    "Rock Smash": "BADGE06_GET",
}


@dataclass(frozen=True)
class _Edge:
    from_map: tuple[int, int]
    to_map: tuple[int, int]
    gate: str | None  # key into _GATE_MOVE_NAMES, or None if ungated


class _Graph:
    def __init__(
        self,
        nodes: set[tuple[int, int]],
        edges_by_map: dict[tuple[int, int], list[_Edge]],
        names: dict[tuple[int, int], str],
    ):
        self.nodes = nodes
        self.edges_by_map = edges_by_map
        self.names = names


def _map_label(map_tuple: tuple[int, int], graph: "_Graph | None" = None) -> str:
    if graph is not None:
        name = graph.names.get(map_tuple)
        if name:
            return name
    return str(map_tuple)


def _gate_key(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    return tuple(sorted((a, b)))


def _normalize_map(m) -> tuple[int, int] | None:
    """Accept a MapRSE/MapFRLG enum member, a MapLocation (has
    map_group_and_number), or a plain (group, number) tuple. Anything else (a
    bogus string, an unrelated object, ...) resolves to None -- callers turn that
    into an honest 'unknown map' answer, never a raise."""
    if m is None:
        return None
    value = getattr(m, "value", None)
    if isinstance(value, tuple) and len(value) == 2:
        m = value
    elif hasattr(m, "map_group_and_number"):
        try:
            m = m.map_group_and_number
        except Exception:
            return None
    if isinstance(m, tuple) and len(m) == 2:
        try:
            return (int(m[0]), int(m[1]))
        except (TypeError, ValueError):
            return None
    return None


def _resolve_from_map(from_map) -> tuple[int, int] | None:
    if from_map is not None:
        return _normalize_map(from_map)
    try:
        from modules.map import get_map_data_for_current_position

        here = get_map_data_for_current_position()
        if here is None:
            return None
        return tuple(here.map_group_and_number)
    except Exception as error:
        _log.debug("could not resolve current player position: %s", error)
        return None


def _live_capability(move_name: str, badges=None) -> bool:
    """Does a party mon know `move_name` AND does the player have the badge that
    unlocks it outside battle? Mirrors story_mode._party_can_surf()'s approach
    (party-move check) plus modules/menuing.py's badge table. `badges`, if given,
    overrides the live get_event_flag() read for the specific badge this move
    needs (a dict of flag name -> bool, or any container supporting `in`) -- used
    only when the caller didn't pin the capability directly."""
    try:
        from modules.context import context
        from modules.memory import get_event_flag
        from modules.pokemon_party import get_party

        table = _RSE_BADGE_BY_MOVE if context.rom.is_rse else _FRLG_BADGE_BY_MOVE
        badge = table.get(move_name)
        if badge is None:
            return False
        if not get_party().has_pokemon_with_move(move_name):
            return False
        if badges is not None:
            has_badge = bool(badges.get(badge)) if hasattr(badges, "get") else (badge in badges)
        else:
            has_badge = bool(get_event_flag(badge))
        return has_badge
    except Exception as error:
        _log.debug("live capability check failed (%s): %s", move_name, error)
        return False


def _resolve_caps(can_surf, can_rock_smash, can_cut, can_strength, badges) -> dict[str, bool]:
    explicit = {"surf": can_surf, "rock_smash": can_rock_smash, "cut": can_cut, "strength": can_strength}
    resolved: dict[str, bool] = {}
    for gate, value in explicit.items():
        if value is not None:
            resolved[gate] = bool(value)  # explicit argument always wins over live detection
        else:
            resolved[gate] = _live_capability(_GATE_MOVE_NAMES[gate], badges)
    return resolved


def _build_graph() -> _Graph:
    from modules.context import context
    from modules.map import get_map_data
    from modules.map_data import MapFRLG, MapRSE

    map_enum = MapRSE if context.rom.is_rse else MapFRLG

    nodes: set[tuple[int, int]] = set()
    names: dict[tuple[int, int], str] = {}
    for member in map_enum:
        try:
            get_map_data(member.value, (0, 0))
        except (ValueError, KeyError):
            continue  # map does not exist in this game revision
        node = tuple(member.value)
        nodes.add(node)
        names.setdefault(node, member.name)

    edges_by_map: dict[tuple[int, int], list[_Edge]] = {}

    def add_edge(a: tuple[int, int], b: tuple[int, int]) -> None:
        if a not in nodes or b not in nodes:
            return
        gate = KNOWN_GATES.get(_gate_key(a, b))
        edges_by_map.setdefault(a, []).append(_Edge(a, b, gate))

    # Edge weight: every edge below (connection OR warp) costs exactly 1 hop.
    # Deliberate, not an oversight -- a connection can span a whole route's walk and
    # a warp can be a single doorway, so hop count is not a real-world distance
    # metric; it is a coarse "how many map transitions" filter for `max_hops`
    # (coordinator follow-up: distinguish "Route 118, a few hops away" from
    # "Mossdeep, many regions away" without needing per-map walk-distance data we
    # don't have). If a real distance model is ever needed, weight connections by
    # map size and warps by 0 -- not attempted here; scope is "handful of hops"
    # vs "many regions", which uniform weighting already separates cleanly (see
    # tools/story-dev/repro_region_reach.py's measured numbers).
    for node in nodes:
        map_data = get_map_data(node, (0, 0))
        for connection in map_data.connections:
            if connection.direction not in _CONNECTION_DIRECTIONS:
                continue
            destination = (connection.destination_map_group, connection.destination_map_number)
            if destination not in nodes:
                continue
            # Edge connections are physically two-way (you can always walk back the
            # way you came) -- add both directions even if only one side's map
            # header happens to declare the connection.
            add_edge(node, destination)
            add_edge(destination, node)
        for warp in map_data.warps:
            dest_group = warp.destination_map_group
            dest_number = warp.destination_map_number
            if dest_group == _DYNAMIC_WARP_MARKER and dest_number == _DYNAMIC_WARP_MARKER:
                continue
            destination = (dest_group, dest_number)
            if destination not in nodes:
                continue
            # Warps are directed: this is the door/cave-mouth you can walk INTO
            # from here. A return trip only exists if the destination map has its
            # own warp back (it usually does, but we don't assume it).
            add_edge(node, destination)

    return _Graph(nodes, edges_by_map, names)


_graph_singleton: _Graph | None = None
_graph_rom_id: str | None = None


def _get_graph() -> _Graph:
    global _graph_singleton, _graph_rom_id
    from modules.context import context

    rom_id = context.rom.id
    if _graph_singleton is not None and _graph_rom_id == rom_id:
        return _graph_singleton
    graph = _build_graph()
    _graph_singleton = graph
    _graph_rom_id = rom_id
    return graph


def _bfs_distances(start: tuple[int, int], graph: _Graph, caps: dict[str, bool]) -> dict[tuple[int, int], int]:
    """Hop count from `start` to every map reachable under `caps` (BFS, uniform
    edge weight -- see the weighting note above `_build_graph`). `start` itself is
    distance 0. Bounded by construction: a map is only ever entered into the
    result dict once, so this always terminates on the finite map graph; the
    iteration cap below is a pure defensive backstop (never expected to trigger)
    against a malformed edge list."""
    distances: dict[tuple[int, int], int] = {start: 0}
    queue: deque[tuple[int, int]] = deque([start])
    max_iterations = len(graph.nodes) * 8 + 64
    iterations = 0
    while queue:
        iterations += 1
        if iterations > max_iterations:
            _log.debug("region_reach BFS exceeded its defensive iteration cap, aborting early")
            break
        current = queue.popleft()
        current_hops = distances[current]
        for edge in graph.edges_by_map.get(current, []):
            if edge.to_map in distances:
                continue
            if edge.gate is not None and not caps.get(edge.gate, False):
                continue
            distances[edge.to_map] = current_hops + 1
            queue.append(edge.to_map)
    return distances


def _bfs_path(
    start: tuple[int, int], graph: _Graph, caps: dict[str, bool], target: tuple[int, int]
) -> list[_Edge] | None:
    """Shortest edge sequence start -> target under `caps` (BFS, fewest hops), or
    None if unreachable. Same bounded-by-visited-set shape as `_bfs_reachable`."""
    if start == target:
        return []
    visited = {start}
    queue: deque[tuple[tuple[int, int], list[_Edge]]] = deque([(start, [])])
    max_iterations = len(graph.nodes) * 8 + 64
    iterations = 0
    while queue:
        iterations += 1
        if iterations > max_iterations:
            _log.debug("region_reach path BFS exceeded its defensive iteration cap, aborting early")
            break
        current, path = queue.popleft()
        for edge in graph.edges_by_map.get(current, []):
            if edge.to_map in visited:
                continue
            if edge.gate is not None and not caps.get(edge.gate, False):
                continue
            new_path = path + [edge]
            if edge.to_map == target:
                return new_path
            visited.add(edge.to_map)
            queue.append((edge.to_map, new_path))
    return None


def reachable_map_distances(
    from_map=None,
    *,
    can_surf: bool | None = None,
    can_rock_smash: bool | None = None,
    can_cut: bool | None = None,
    can_strength: bool | None = None,
    badges=None,
) -> dict:
    """Every map reachable from `from_map` (default: current player position),
    mapped to its hop count (uniform edge weight -- see `_build_graph`'s
    weighting note). `from_map` itself maps to 0. Fail-safe: any read error
    returns `{}`, never raises."""
    try:
        start = _resolve_from_map(from_map)
        if start is None:
            return {}
        graph = _get_graph()
        if start not in graph.nodes:
            return {}
        caps = _resolve_caps(can_surf, can_rock_smash, can_cut, can_strength, badges)
        return _bfs_distances(start, graph, caps)
    except Exception as error:
        _log.debug("reachable_map_distances failed: %s", error)
        return {}


def reachable_maps(
    from_map=None,
    *,
    max_hops: int | None = None,
    can_surf: bool | None = None,
    can_rock_smash: bool | None = None,
    can_cut: bool | None = None,
    can_strength: bool | None = None,
    badges=None,
) -> set:
    """All maps reachable from `from_map` (default: current player position),
    honoring capability gates. `max_hops`, if given, drops any map farther away
    than that (see `reachable_map_distances` for the actual distances). Fail-safe:
    any read error returns `set()`, never raises."""
    try:
        distances = reachable_map_distances(
            from_map, can_surf=can_surf, can_rock_smash=can_rock_smash, can_cut=can_cut,
            can_strength=can_strength, badges=badges,
        )
        if max_hops is None:
            return set(distances)
        return {m for m, hops in distances.items() if hops <= max_hops}
    except Exception as error:
        _log.debug("reachable_maps failed: %s", error)
        return set()


def hops_to(target_map, from_map=None, **caps) -> int | None:
    """Raw hop count from `from_map` (default: current position) to
    `target_map`, or None if unreachable / on any read error / for an
    unrecognised `target_map`. Never raises."""
    try:
        target = _normalize_map(target_map)
        if target is None:
            return None
        return reachable_map_distances(from_map, **caps).get(target)
    except Exception as error:
        _log.debug("hops_to failed: %s", error)
        return None


def is_map_reachable(target_map, from_map=None, *, max_hops: int | None = None, **caps) -> bool:
    """Is `target_map` reachable from `from_map` (default: current position)?
    `max_hops`, if given, additionally requires the map be within that many hops
    (a map beyond it counts as not reachable, same as no path existing -- use
    `why_unreachable` to tell the two apart). Fail-safe: any read error, or an
    unrecognised `target_map`, returns False."""
    try:
        target = _normalize_map(target_map)
        if target is None:
            return False
        distances = reachable_maps(from_map, max_hops=max_hops, **caps)
        return target in distances
    except Exception as error:
        _log.debug("is_map_reachable failed: %s", error)
        return False


def why_unreachable(target_map, from_map=None, *, max_hops: int | None = None, **caps) -> str:
    """Human-readable reason `target_map` is not reachable from `from_map`
    (default: current position). This is the point of the module: KI-24 happened
    because a false 'unreachable' gave no reason at all. Distinguishes three
    genuinely different facts -- no connection/warp path exists at all, a
    specific capability gate blocks the only path, or the path exists and is
    walkable but farther than `max_hops` -- because collapsing them into one
    silent "no" is exactly the failure mode this module exists to fix. Fail-safe:
    a read error is reported as the CHECK failing, never phrased as the map
    being unreachable."""
    try:
        start = _resolve_from_map(from_map)
        if start is None:
            return "reachability check failed: could not determine the starting map"
        target = _normalize_map(target_map)
        if target is None:
            return f"unknown map: {target_map!r}"

        graph = _get_graph()
        if start not in graph.nodes:
            return f"reachability check failed: starting map {start!r} not found in the map graph"
        if target not in graph.nodes:
            return f"unknown map: {target!r} not found in the map graph"

        resolved_caps = _resolve_caps(
            caps.get("can_surf"), caps.get("can_rock_smash"), caps.get("can_cut"), caps.get("can_strength"),
            caps.get("badges"),
        )
        distances = _bfs_distances(start, graph, resolved_caps)
        if target in distances:
            hops = distances[target]
            if max_hops is not None and hops > max_hops:
                # Genuinely reachable and walkable -- just farther than the caller
                # is willing to travel. NOT the same fact as "no path exists" or
                # "missing a capability"; say so explicitly (coordinator follow-up).
                return f"reachable but {hops} hops away (limit {max_hops})"
            return "reachable"

        # Reachable at all, ignoring capability gates? If not, it's a genuine graph
        # gap (no connection/warp path exists), not a capability the player lacks.
        open_caps = {gate: True for gate in _GATE_MOVE_NAMES}
        open_path = _bfs_path(start, graph, open_caps, target)
        if open_path is None:
            return f"no connection path from {_map_label(start, graph)} to {_map_label(target, graph)}"

        for edge in open_path:
            if edge.gate is not None and not resolved_caps.get(edge.gate, False):
                move_name = _GATE_MOVE_NAMES.get(edge.gate, edge.gate)
                return (
                    f"needs {move_name} at "
                    # ASCII arrow, not the unicode "↔" -- tools/story-dev repro scripts run
                    # in a plain Windows console (cp1252) that raises UnicodeEncodeError on
                    # non-ASCII output unless stdout is explicitly reconfigured (see
                    # repro_hm_move_replace_loop.py); avoid the trap here instead.
                    f"{_map_label(edge.from_map, graph)}<->{_map_label(edge.to_map, graph)}"
                )
        # Every edge on the ungated path is ungated, yet the gated BFS didn't reach
        # the target -- shouldn't happen, but report honestly rather than guess.
        return f"no connection path from {_map_label(start, graph)} to {_map_label(target, graph)}"
    except Exception as error:
        return f"reachability check failed: {error}"
