"""`#24-rarepredicate` DATA HALF: compute the RARE-SPECIES set, and validate it against the
figures already recorded in `03-PUNCH-LIST.md`. NO EMULATOR — pure computation over the two
committed caches.

USER RULING (`06-DECISIONS-LOG.md` 2026-08-06, ruling 3): "rare" is three OR'd rules — shiny
(already works) / rare gender variant / **rare species**. This file computes the third:

    rare species  =  best_slot_rate <= 4%   OR   warp_depth >= 3

WHY TWO AXES. The user named two examples that no single score ranks together — Skitty is rare by
SCARCITY (2% slot, rank 11 of 132) and Bagon is rare by ACCESS ("gated to a specific location",
rank 56 of 132 by rate, i.e. statistically median). A composite score that puts both above a
common species also puts half the dex above it.

    best_slot_rate = the HIGHEST encounter rate the species has anywhere. A species is scarce
                     only if even its BEST home is thin; using the min would call Zigzagoon rare.
    warp_depth     = 0-1 BFS over `cache/warp_graph_BPEE0.json`. Seed every non-underwater
                     group-0 map at 0; CONNECTION edges cost 0 (you walk across a map boundary),
                     WARP edges cost 1 (a door/cave mouth). Take the MIN over all of a species'
                     locations — a mon is only as gated as its easiest home.
                     Dive edges are excluded at `warp_graph.py:20`, so Dive-only maps come out
                     unreachable (d99) BY DESIGN.

THRESHOLD RATIONALE (recorded 2026-08-06, re-derived here): there is a CLIFF between 4% and 5% —
the 5% Safari slots add 18 species at once. 4% is the natural stop.

‼ KNOWN FALSE NEGATIVES, ACCEPTED. **Feebas is not in the encounter index at all** — the index is
built from `gWildMonHeaders` and the 6-tile mechanic is not in that table — so the most iconic
pseudo-rare species can never fire this rule. Same for Beldum and other gift/static species.
Pure-sea endgame species (Luvdisc, Corsola, Staryu) are structurally d0 and miss.
‼ And the depth cutoff earns some of its precision by luck: Meteor Falls' d2 rooms are also
Surf-gated in reality, so `>=3` is a good INFERENCE about access, never proof of a required HM.

Run:  PYTHONUTF8=1 py -3.12 rare_species_dataset.py [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import deque

REPO = pathlib.Path(__file__).resolve().parents[2]
CACHE = REPO / "sandbox-pokebot" / "cache"

ap = argparse.ArgumentParser()
ap.add_argument("--json", default=None, help="write the computed dataset here")
args = ap.parse_args()

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


wg = json.loads((CACHE / "warp_graph_BPEE0.json").read_text(encoding="utf-8"))
ei = json.loads((CACHE / "encounter_index_BPEE0.json").read_text(encoding="utf-8"))["index"]

# ---------------------------------------------------------------- warp depth
adj_free: dict[tuple, set] = {}   # connection edges — cost 0
adj_warp: dict[tuple, set] = {}   # warp edges — cost 1

for src, dsts in wg["connections"]:
    s = tuple(src)
    for d in dsts:
        adj_free.setdefault(s, set()).add(tuple(d))
        adj_free.setdefault(tuple(d), set()).add(s)

# Warps are added in both directions (a door works both ways). ⚠ CORRECTED 2026-09-29 (design v2 step 0): the old
# comment here said a directed graph left 34 species "unreachable"; that was an artifact of the edge-parse bug below.
# With the correct destination, one-way and two-way warps give IDENTICAL per-species depths (verified 2026-09-29).
# ⛔ FIXED 2026-09-29: an edge is `[from_map, from_coords, to_map, to_coords]` (`modules/warp_graph.py` `to_json`), so
# the destination MAP is `edge[2]`. This read `edge[1]` — a TILE coordinate — as a map, which is why the 2026-08-07 run
# "did not reproduce" the 2026-08-06 figures. A fix to what the data IS, not a tune toward Bagon's depth.
for edge in wg["edges"]:
    s, d = tuple(edge[0]), tuple(edge[2])
    adj_warp.setdefault(s, set()).add(d)
    adj_warp.setdefault(d, set()).add(s)

# Seed: every NON-UNDERWATER group-0 map (the overworld: towns and routes), as the 2026-08-06 spec says.
# ⛔ FIXED 2026-09-29: the old comment claimed "Underwater maps are not group 0" — false: `map_data.py` puts
# UNDERWATER_ROUTE124/126/127/128/129/105/125 at (0,50)-(0,56). Seeding them at 0 made Dive-only species "d0".
# The set is DERIVED from `MapRSE` by name (no hardcoded range), so a renumbered map cannot silently re-enter the seeds.
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
from modules.map_data import MapRSE  # noqa: E402

UNDERWATER_G0 = {m.value for m in MapRSE if m.name.startswith("UNDERWATER_") and m.value[0] == 0}
check("the underwater group-0 maps are found by name (7 in Emerald)", len(UNDERWATER_G0) == 7, str(sorted(UNDERWATER_G0)))
seeds = {tuple(m) for m, _region in wg["regions"] if m[0] == 0 and tuple(m) not in UNDERWATER_G0}
INF = 99
depth: dict[tuple, int] = {}


def _relax_free(frontier: set, d: int) -> set:
    """Expand a cost-0 (connection) closure from `frontier` at depth `d`."""
    out, stack = set(), list(frontier)
    while stack:
        m = stack.pop()
        if depth.get(m, INF) <= d:
            if m not in out:
                out.add(m)
            continue
        depth[m] = d
        out.add(m)
        for n in adj_free.get(m, ()):
            if depth.get(n, INF) > d:
                stack.append(n)
    return out


# 0-1 BFS: settle the free closure, then step one warp, repeat.
level = _relax_free(seeds, 0)
d = 0
while level and d < 20:
    nxt = set()
    for m in level:
        for n in adj_warp.get(m, ()):
            if depth.get(n, INF) > d + 1:
                nxt.add(n)
    if not nxt:
        break
    d += 1
    level = _relax_free(nxt, d)

# ---------------------------------------------------------------- per species
rows = []
for sid, locs in ei.items():
    if not locs:
        continue
    best_rate = max(l.get("rate", 0) for l in locs)
    depths = [depth.get(tuple(l["map"]), INF) for l in locs]
    wd = min(depths) if depths else INF
    rows.append({
        "species_index": int(sid),
        "best_slot_rate": best_rate,
        "warp_depth": wd,
        "n_maps": len({tuple(l["map"]) for l in locs}),
        "rare_by_rate": best_rate <= 4,
        "rare_by_depth": wd >= 3,
    })
for r in rows:
    r["rare"] = r["rare_by_rate"] or r["rare_by_depth"]

hist: dict[str, int] = {}
for r in rows:
    k = "d99" if r["warp_depth"] >= INF else (f"d{r['warp_depth']}" if r["warp_depth"] < 4 else "d4+")
    hist[k] = hist.get(k, 0) + 1

print(f"species with encounters : {len(rows)}")
print(f"warp-depth histogram    : {dict(sorted(hist.items()))}")
print(f"rare by rate  (<=4%)    : {sum(r['rare_by_rate'] for r in rows)}")
print(f"rare by depth (>=3)     : {sum(r['rare_by_depth'] for r in rows)}")
print(f"RARE (either rule)      : {sum(r['rare'] for r in rows)}")
print()
print("VALIDATION — internal consistency, then AGREEMENT with the 2026-08-06 record (below).")
# --- INTERNAL CONSISTENCY (these are pass/fail) ---
check("132 species carry wild encounters", len(rows) == 132, f"got {len(rows)}")
check("the histogram accounts for every species", sum(hist.values()) == len(rows),
      f"{sum(hist.values())} vs {len(rows)}")
check("every species resolved to a finite-or-99 depth",
      all(0 <= r["warp_depth"] <= 99 for r in rows))
check("the OR'd rule is the union of its two parts",
      sum(r["rare"] for r in rows)
      == len({i for i, r in enumerate(rows) if r["rare_by_rate"] or r["rare_by_depth"]}))

# The two species the USER named, which is what the rule ultimately has to honour.
# ‼ THE INDEX IS KEYED BY INTERNAL ROM SPECIES INDEX, NOT NATIONAL DEX. Skitty is national 300
# but internal 315; the first run of this script looked up 300, found a different species
# entirely, and reported "Skitty not in the index" on a species that is plainly there. Resolve
# through the SAME call production uses (`encounter_index._resolve_species_index` ->
# `get_species_by_name(name).index`) rather than any dex number.
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
by_id = {r["species_index"]: r for r in rows}
try:
    from modules.pokemon import get_species_by_name

    for name, why in (("Bagon", "pseudo-rare via warp depth"), ("Skitty", "rare via rate")):
        r = by_id.get(get_species_by_name(name).index)
        check(f"{name} is selected — {why}", r is not None and r["rare"],
              f"rate={r['best_slot_rate']}% depth={r['warp_depth']}" if r else "not in the index")
except Exception as error:  # noqa: BLE001
    check("species names resolve through modules.pokemon", False, f"{type(error).__name__}: {error}")

if args.json:
    pathlib.Path(args.json).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\nwrote {args.json}")

# ============================================================================
# ✅ AGREEMENT WITH THE FIGURES RECORDED 2026-08-06 (`28-HANDOFF-ARCHIVE.md`, the `#24-rarepredicate` spec)
#
# History: the 2026-08-07 run of this script "did not reproduce" them (d0=62 d1=36 d2=22 d3=11 d99=1; 23 RARE; Bagon
# d2), and `03`/`06`/`08` recorded the dataset as unverified. That verdict rested on TWO defects in THIS script, both
# fixed 2026-09-29 (design v2 step 0; verified by an independent agent and re-run by the orchestrator):
#   1. `edge[1]` (a tile coordinate) was read as the warp's destination map; it is `edge[2]`.
#   2. the underwater group-0 maps were seeded at depth 0 (a false comment said they are not group 0).
# Each fix alone does NOT reproduce the record; both together reproduce every recorded number. These are now HARD
# checks: a change that moves the numbers must be deliberate, and must update the record with it.
# ⚠ Reproducing warp depth does NOT make it the pseudo-rare rule: design v2 step 7 uses the user's 2026-08-14 reasoning
# (field-move gates + few locations, `03` `#24-rarepredicate`), and the rate half (<= 4%) of the archived rule.
# ============================================================================
RECORDED = {"d0": 59, "d1": 21, "d2": 39, "d3": 7, "d4+": 3, "d99": 3}
RECORDED_DEPTH3 = 13
RECORDED_RARE = 26

print()
print("AGREEMENT — recorded 2026-08-06 vs computed here (hard checks)")
check("the histogram matches the record", dict(sorted(hist.items())) == dict(sorted(RECORDED.items())),
      f"recorded {RECORDED} computed {dict(sorted(hist.items()))}")
check("depth>=3 count matches the record", sum(r["rare_by_depth"] for r in rows) == RECORDED_DEPTH3,
      f"recorded {RECORDED_DEPTH3} computed {sum(r['rare_by_depth'] for r in rows)}")
check("RARE total matches the record", sum(r["rare"] for r in rows) == RECORDED_RARE,
      f"recorded {RECORDED_RARE} computed {sum(r['rare'] for r in rows)}")

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")


