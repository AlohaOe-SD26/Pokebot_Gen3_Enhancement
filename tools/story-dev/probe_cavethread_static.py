"""#24-cavethread STATIC recon — no emulator, no ROM, no CPU contention with the batch.

Replays `WarpGraph.map_route` / `map_distance` (BFS over connections + warp edges) against
the committed ROM-derived cache, to answer ONE question the punch list assumes the answer to:

    does the warp graph already know a multi-hop route into the deep cave interiors,
    or does it genuinely need the hand-built chain tables `#24-cavethread` proposes?

Map names come from an AST parse of `map_data.py` — NEVER a bulk import (`modules/data`
runs generators at import and has gutted that file twice).
"""
import ast
import json
from collections import deque
from pathlib import Path

ROOT = Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot")

# --- map name <-> (group, number), via AST so nothing executes -----------------
NAMES: dict[str, tuple] = {}
tree = ast.parse((ROOT / "modules" / "map_data.py").read_text(encoding="utf-8"))
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "MapRSE":
        for item in node.body:
            if isinstance(item, ast.Assign) and isinstance(item.value, ast.Tuple):
                try:
                    val = ast.literal_eval(item.value)
                except ValueError:
                    continue
                for tgt in item.targets:
                    if isinstance(tgt, ast.Name):
                        NAMES[tgt.id] = tuple(val)
BY_ID = {v: k for k, v in NAMES.items()}


def label(m):
    return BY_ID.get(tuple(m), str(tuple(m)))


# --- load the cache -----------------------------------------------------------
payload = json.loads((ROOT / "cache" / "warp_graph_BPEE0.json").read_text(encoding="utf-8"))
assert payload["version"] == 2, payload["version"]
edges = [(tuple(e[0]), tuple(e[1]), tuple(e[2]), tuple(e[3])) for e in payload["edges"]]
connections = {tuple(e[0]): {tuple(v) for v in e[1]} for e in payload["connections"]}

edges_by_map: dict[tuple, list] = {}
for e in edges:
    edges_by_map.setdefault(e[0], []).append(e)


def map_route(a, b):
    """EXACTLY `WarpGraph.map_route`: BFS over connections + warp edges, excluding `a`."""
    a, b = tuple(a), tuple(b)
    if a == b:
        return []
    visited = {a}
    q = deque([(a, [])])
    while q:
        cur, path = q.popleft()
        nbrs = list(connections.get(cur, ()))
        nbrs += [e[2] for e in edges_by_map.get(cur, ())]
        for n in nbrs:
            if n in visited:
                continue
            newp = path + [n]
            if n == b:
                return newp
            visited.add(n)
            q.append((n, newp))
    return None


def report(name_a, name_b):
    a, b = NAMES.get(name_a), NAMES.get(name_b)
    if a is None or b is None:
        print(f"  !! unknown map: {name_a if a is None else name_b}")
        return
    known_a = a in edges_by_map or a in connections
    known_b = b in edges_by_map or b in connections or any(e[2] == b for e in edges)
    route = map_route(a, b)
    print(f"\n{name_a} -> {name_b}")
    print(f"  graph knows source={known_a} dest={known_b}")
    if route is None:
        print("  ROUTE: none")
    else:
        print(f"  ROUTE: {len(route)} hop(s)")
        for i, m in enumerate(route, 1):
            print(f"    {i}. {label(m)}")


print("=" * 78)
print("INTO the deep interiors (the maps #24-cavethread says are 3 and 4 warps deep)")
print("=" * 78)
report("ROUTE122", "MT_PYRE_SUMMIT")
report("MT_PYRE_EXTERIOR", "MT_PYRE_SUMMIT")
report("JAGGED_PASS", "MAGMA_HIDEOUT_4F")
report("ROUTE106", "GRANITE_CAVE_B2F")

print()
print("=" * 78)
print("OUT of a deep interior to a heal town — the leg that dropped 2 real-HW runs")
print("=" * 78)
report("GRANITE_CAVE_B2F", "DEWFORD_TOWN")
report("MT_PYRE_SUMMIT", "LILYCOVE_CITY")
report("FIERY_PATH", "LAVARIDGE_TOWN")
