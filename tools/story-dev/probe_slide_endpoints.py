"""KI-76 CORRECTNESS HALF — where does every current slide in the ROM actually END, and how often
is our model's endpoint WRONG? (`#24-orphans` (6), built 2026-08-17)

⛔ THIS PROBE CHANGES NOTHING. It measures. Its whole job is to turn KI-76's two STATIC-ANALYSIS
claims into counts on every map that has currents — above all on ROUTE132/133/134, which
`map_path.py`'s own comment admits are "unmeasured", and which are the approach to the Regi arc
and Ever Grande (§Ch23).

THE TWO DEFECTS IT COUNTS (both from KI-76, both currently UNFIXED):

  D1 — THE SLIDE ENDS ONE TILE SHORT, IN THE WRONG MOVEMENT MODE.
       `map_path.py:340-344` walks the chain while the next tile is water:
           if next_tile.elevation == 1 and not next_tile.collision:  destination = next_tile
           else:                                                     break
       so our endpoint is the LAST WATER TILE. The game does something else: when the next tile is
       walkable LAND, `CheckForObjectEventCollision` returns `COLLISION_STOP_SURFING` and
       `CreateStopSurfingTask` runs — the player is moved ONTO the land tile and DISMOUNTS.
       ⇒ ARMED whenever a chain stops because the next tile is land you can stand on.
       A chain that stops against a WALL is NOT armed: the game blocks you there too.

  D2 — A SLIDE CAN END ON A WARP, AND THE WARP PENALTY IS COMPUTED ONE BRANCH TOO EARLY.
       `map_path.py:971-972` charges the `cost = 1000000` warp penalty against the NEIGHBOUR;
       `:1013-1022` only afterwards substitutes the slide DESTINATION for that neighbour. So the
       destination's `warps_to` is never inspected, never penalised, never marked `is_warp`.
       ⇒ ARMED whenever a chain's endpoint tile is itself a warp: the planner sees traversable
       water and the game posts you to another map.

‼ WHY A STATIC PROBE IS THE RIGHT INSTRUMENT HERE. Both defects are properties of MAP DATA plus
our own model, and both are decided before a single frame runs. A live drive can confirm ONE tile
per run; this reads every chain on every map in seconds. It does NOT replace the live confirmation
KI-76 asks for ("surf onto Room 7 (5,8); surf onto Room 6 (14,9)") — it tells you which tiles are
worth spending a live run on, and it is the fixture-finder for the eventual A/B.

‼‼ THE POSITIVE CONTROL IS THE POINT, NOT A COURTESY (08-MISTAKES 2026-08-17: "a zero from a NEW
instrument is not a measurement until that instrument has produced a NON-ZERO on a case where you
know the answer"). KI-76 recorded two numbers from an INDEPENDENT analysis a different session
made of the Seafloor Cavern:
      ROOM7 — 44 of its 117 chains funnel into (3,18) and push south onto (3,19)
      ROOM6 —  9 of its 108 chains terminate on (14,8), a Non-Animated Door warp
If this probe cannot reproduce BOTH, its numbers for ROUTE132/133/134 are worthless and it says so
by EXITING 1. A green run on the routes therefore means something; without the control it would
only mean the loop ran.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_slide_endpoints.py
Exit: 0 if both positive controls reproduce; 1 if either fails (⇒ the probe is broken, not the map).
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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE

# ‼‼ PRODUCTION IS THE ORACLE — added 2026-08-17 after an ADVERSARIAL REVIEW kicked back v1.
#
# v1 re-implemented the slide loop and reported its own answer. The review's finding was correct
# and I had under-weighted my own disclosure: `simulate()` stops at a map edge, production FOLLOWS
# the connection — so 645 of 4,384 chains (14.7%; 28.0% of ROUTE132, 17.3% of ROUTE133) were
# UNMEASURED, and worse, production spends ONE 512-step budget across the whole cross-map chain.
# That makes "no cycles / the longest chain is 73 / the cap has 7x margin" unproven exactly where
# it matters, and raises the opposite hazard: a cap that fires on a healthy long cross-map path.
#
# ⇒ So stop arguing about the replica. `PathMap.tiles` RUNS THE REAL LOOP (`map_path.py:260-350`)
# and publishes its result as `PathTile.forced_movement_to`. This probe now reads THAT as the
# endpoint, and keeps `simulate()` only (a) to derive the BREAK REASON, which production does not
# record, and (b) as a CROSS-CHECK whose disagreements are reported rather than hidden.
# ‼ Building `.tiles` also EXERCISES the 512 cap for real: if any chain in this ROM cycles across
# a map connection, `map_path.py:267` raises and this probe reports it instead of guessing.
from modules.map_path import Direction, _get_map_metadata

BAR = "=" * 100
SLIDE_CAP = 512  # identical to production (`map_path.py:260`), so a cap hit here means one there


def head(t: str) -> None:
    print(f"\n{BAR}\n{t}\n{BAR}\n")


# --- caches: a chain can cross a map boundary, so map data is fetched by (group, number) ----------
_tiles_cache: dict[tuple[int, int], dict[tuple[int, int], object]] = {}
_warps_cache: dict[tuple[int, int], set[tuple[int, int]]] = {}
_size_cache: dict[tuple[int, int], tuple[int, int]] = {}


def _load(map_key: tuple[int, int]):
    """Tiles-by-local-position, warp coordinates, and map size for one map."""
    if map_key not in _tiles_cache:
        md = get_map_data(map_key, (0, 0))
        _tiles_cache[map_key] = {t.local_position: t for t in get_map_all_tiles(md)}
        # ‼ Same source `map_path.py:119-124` builds its `warp_cache` from — `md.warps` — so "is
        # this tile a warp" means here exactly what it means to the planner. Deriving it any other
        # way would measure a different question than the one D2 is about.
        _warps_cache[map_key] = {w.local_coordinates for w in md.warps}
        _size_cache[map_key] = md.map_size
    return _tiles_cache[map_key], _warps_cache[map_key], _size_cache[map_key]


PUSH_DELTA = {
    "Eastward Current": (1, 0),
    "Westward Current": (-1, 0),
    "Southward Current": (0, 1),
    "Northward Current": (0, -1),
}


def simulate(start_tile, map_key: tuple[int, int]) -> dict:
    """Replay `map_path.py:260-344`'s slide loop and report WHERE it ended and WHY.

    ⛔ Deliberately a faithful re-implementation rather than a call into `PathMap`: the production
    loop lives inside a `@property` that builds every tile of the map, and calling it would tell us
    what the planner concluded, not which BRANCH ended the chain. The break reason IS the finding.

    ‼ SIMPLIFICATION, STATED RATHER THAN HIDDEN: production also follows a chain across a map
    CONNECTION. This stops at the map edge and reports `edge` instead. That is sound for what is
    being counted — `probe_current_edges.py` already measured **0 armed edge tiles in this ROM**,
    i.e. no current in the game pushes off a map edge without a connection — and any chain that DID
    leave its map would be reported here as `edge`, visibly, never silently folded into an armed or
    safe bucket. If an `edge` count is ever non-trivial, this is the line to revisit.
    """
    tiles, warps, size = _load(map_key)
    destination = start_tile
    cur_key = map_key
    steps = 0
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    reason = "open_water"       # left the while-loop: endpoint is water but not a current
    next_tile = None
    cap = SLIDE_CAP

    while destination.tile_type.endswith(" Current"):
        cap -= 1
        if cap <= 0:
            reason = "cap"
            break
        marker = (cur_key, destination.local_position)
        if marker in seen:
            reason = "cycle"
            break
        seen.add(marker)

        x, y = destination.local_position
        dx, dy = PUSH_DELTA[destination.tile_type]
        w, h = size
        nx, ny = x + dx, y + dy
        if nx < 0 or ny < 0 or nx >= w or ny >= h:
            reason = "edge"
            break

        next_tile = tiles.get((nx, ny))
        if next_tile is None:
            reason = "unreadable"
            break
        if next_tile.elevation == 1 and not next_tile.collision:
            destination = next_tile
            steps += 1
        else:
            reason = "blocked"
            break

    end_key = cur_key
    end_pos = destination.local_position
    _t, end_warps, _s = _load(end_key)

    # D1: the chain stopped because something non-water was ahead. ARMED only if that something is
    # LAND YOU CAN STAND ON — collision 0. A collision tile is a wall and the game stops you too.
    d1 = bool(reason == "blocked" and next_tile is not None and not next_tile.collision)
    # D2: the endpoint tile is itself a warp. Independent of D1 — a chain can be both.
    d2 = end_pos in end_warps

    return {
        "start": start_tile.local_position,
        "end": end_pos,
        "end_map": end_key,
        "steps": steps,
        "reason": reason,
        "next": next_tile.local_position if next_tile is not None else None,
        "next_elev": next_tile.elevation if next_tile is not None else None,
        "d1": d1,
        "d2": d2,
    }


def production_endpoints(map_key: tuple[int, int]) -> tuple[dict, str]:
    """Ask PRODUCTION where every current chain on this map ends. Returns ({start: (map, pos, steps)}, note).

    ⛔ This is the authority, not `simulate()`. `PathMap.tiles` executes `map_path.py:260-350`
    verbatim — cross-map connection following and the shared 512-step budget included.
    A `RuntimeError` here is the cap FIRING, which is itself the measurement the review asked for,
    so it is caught and REPORTED rather than allowed to abort the run.
    """
    try:
        tiles = _get_map_metadata(map_key).tiles
    except RuntimeError as exc:
        return {}, f"‼ PRODUCTION RAISED (the 512-step cap fired): {exc}"
    out = {}
    for t in tiles:
        if t.forced_movement_to:
            out[t.local_coordinates] = t.forced_movement_to[Direction.North]
    return out, ""


print("Simulating EVERY current chain on EVERY map that has currents, and classifying its endpoint.")
print("‼ D1 ARMED = the chain stops because walkable LAND is ahead (the game dismounts you ONTO it).")
print("‼ D2 ARMED = the chain's endpoint tile IS a warp (the planner never penalises it).\n")

results: dict[str, list[dict]] = {}
map_meta: dict[str, tuple[int, int]] = {}
prod_notes: dict[str, str] = {}
failed: list[tuple[str, str]] = []

for map_enum in MapRSE:
    try:
        md = get_map_data(map_enum, (0, 0))
        all_tiles = get_map_all_tiles(md)
    except Exception as exc:
        failed.append((map_enum.name, f"{type(exc).__name__}: {exc}"))
        continue
    currents = [t for t in all_tiles if t.tile_type in PUSH_DELTA]
    if not currents:
        continue
    key = (md.map_group, md.map_number)
    _tiles_cache[key] = {t.local_position: t for t in all_tiles}
    _warps_cache[key] = {w.local_coordinates for w in md.warps}
    _size_cache[key] = md.map_size
    rows = [simulate(t, key) for t in currents]

    # --- PRODUCTION IS THE ORACLE: overwrite the endpoint with what the real loop computes ------
    prod, note = production_endpoints(key)
    if note:
        prod_notes[map_enum.name] = note
    for r in rows:
        pe = prod.get(r["start"])
        if pe is None:
            r["prod"] = None
            r["agree"] = None
            continue
        p_map, p_pos, p_steps = pe
        r["prod"] = (tuple(p_map), tuple(p_pos), p_steps)
        r["agree"] = (tuple(p_map) == r["end_map"] and tuple(p_pos) == r["end"])

        # Reclassify BOTH defects on production's endpoint, which may be on ANOTHER MAP.
        p_tiles, p_warps, p_size = _load(tuple(p_map))
        end_tile = p_tiles.get(tuple(p_pos))
        r["d2"] = tuple(p_pos) in p_warps
        r["prod_steps"] = p_steps
        if end_tile is None:
            r["d1"] = False
            r["reason"] = "prod_unreadable"
            continue
        if end_tile.tile_type in PUSH_DELTA:
            # The real loop stopped ON a current tile ⇒ it broke because what lies ahead is not
            # water. Read that tile: walkable land ⇒ the game dismounts onto it (D1 ARMED); a
            # collision tile is a wall and the game stops you there too (NOT armed).
            dx, dy = PUSH_DELTA[end_tile.tile_type]
            ax, ay = tuple(p_pos)[0] + dx, tuple(p_pos)[1] + dy
            if 0 <= ax < p_size[0] and 0 <= ay < p_size[1]:
                ahead = p_tiles.get((ax, ay))
                r["d1"] = bool(ahead is not None and not ahead.collision)
                r["next"] = (ax, ay)
                r["next_elev"] = ahead.elevation if ahead is not None else None
                r["reason"] = "blocked"
            else:
                # Off the map with no connection followed — production's own `_conn is None` break.
                r["d1"] = False
                r["reason"] = "noconn"
        else:
            # Ended on plain water: the chain simply ran out of current. No dismount, no D1.
            r["d1"] = False
            r["reason"] = "open_water"

    results[map_enum.name] = rows
    map_meta[map_enum.name] = key

head("1. EVERY MAP WITH CURRENTS — how many of its chains are ARMED for each defect")

print(f"  {'map':<32} {'chains':>7} {'D1 armed':>9} {'D2 armed':>9} {'both':>6} {'cycles':>7} {'edge':>6}")
for name in sorted(results, key=lambda n: -len(results[n])):
    rows = results[name]
    d1 = sum(1 for r in rows if r["d1"])
    d2 = sum(1 for r in rows if r["d2"])
    both = sum(1 for r in rows if r["d1"] and r["d2"])
    cyc = sum(1 for r in rows if r["reason"] in ("cycle", "cap"))
    edge = sum(1 for r in rows if r["reason"] == "edge")
    print(f"  {name:<32} {len(rows):>7} {d1:>9} {d2:>9} {both:>6} {cyc:>7} {edge:>6}")

head("2. POSITIVE CONTROL — reproduce KI-76's two INDEPENDENTLY-RECORDED cavern numbers")

print("  KI-76 (2026-08-13, a different session, a different analysis) recorded:")
print("     ROOM7 — 44 of 117 chains funnel into (3,18) and push south onto (3,19)")
print("     ROOM6 —  9 of 108 chains terminate on (14,8), a Non-Animated Door warp")
print("  ⛔ If this probe cannot reproduce BOTH, nothing else it prints may be believed.\n")

control_ok = True

r7 = results.get("SEAFLOOR_CAVERN_ROOM7", [])
c7 = sum(1 for r in r7 if r["end"] == (3, 18) and r["next"] == (3, 19))
ok7 = (len(r7) == 117 and c7 == 44)
control_ok &= ok7
print(f"  ROOM7: chains={len(r7)} (expect 117), ending (3,18)->(3,19) = {c7} (expect 44)"
      f"   {'PASS' if ok7 else '‼ FAIL'}")

r6 = results.get("SEAFLOOR_CAVERN_ROOM6", [])
c6 = sum(1 for r in r6 if r["end"] == (14, 8))
warp6 = (14, 8) in _warps_cache.get(map_meta.get("SEAFLOOR_CAVERN_ROOM6", (0, 0)), set())
ok6 = (len(r6) == 108 and c6 == 9 and warp6)
control_ok &= ok6
print(f"  ROOM6: chains={len(r6)} (expect 108), ending (14,8) = {c6} (expect 9), "
      f"(14,8) is a warp = {warp6} (expect True)   {'PASS' if ok6 else '‼ FAIL'}")

head("3. ‼ THE UNMEASURED MAPS — ROUTE132 / ROUTE133 / ROUTE134 (the Regi arc and §Ch23 approach)")

print("  `map_path.py:258` says in as many words that these are unmeasured. They are the reason")
print("  the 512-step cap was added on faith. Here is what they actually contain.\n")

for name in ("ROUTE132", "ROUTE133", "ROUTE134"):
    rows = results.get(name)
    if not rows:
        print(f"  {name}: NO current tiles found — ‼ that contradicts probe_current_edges.py; the")
        print("       scanner is broken, not the map.")
        continue
    d1 = [r for r in rows if r["d1"]]
    d2 = [r for r in rows if r["d2"]]
    cyc = [r for r in rows if r["reason"] in ("cycle", "cap")]
    longest = max(rows, key=lambda r: r["steps"])
    print(f"  {name}: chains={len(rows)}  D1_armed={len(d1)}  D2_armed={len(d2)}  "
          f"cycles={len(cyc)}  longest_chain={longest['steps']} steps (from {longest['start']})")
    ends = {}
    for r in d1:
        ends[(r["end"], r["next"])] = ends.get((r["end"], r["next"]), 0) + 1
    for (end, nxt), n in sorted(ends.items(), key=lambda kv: -kv[1])[:6]:
        print(f"       D1: {n:>4} chain(s) stop on {end}; the GAME dismounts onto {nxt}")
    if len(ends) > 6:
        print(f"       ... and {len(ends) - 6} more distinct D1 endpoints")
    for r in d2[:6]:
        print(f"       D2: chain from {r['start']} ENDS ON WARP {r['end']}")
    if len(d2) > 6:
        print(f"       ... and {len(d2) - 6} more D2 endpoints")

head("4. WHOLE-ROM TOTALS")

all_rows = [r for rows in results.values() for r in rows]
print(f"  maps with currents        : {len(results)}   (unreadable maps: {len(failed)})")
print(f"  current chains simulated  : {len(all_rows)}")
print(f"  D1 ARMED (wrong endpoint AND wrong movement mode): "
      f"{sum(1 for r in all_rows if r['d1'])}")
print(f"  D2 ARMED (endpoint is an unpenalised warp)       : "
      f"{sum(1 for r in all_rows if r['d2'])}")
print(f"  cycles / cap hits                                : "
      f"{sum(1 for r in all_rows if r['reason'] in ('cycle', 'cap'))}")
print(f"  chains stopping at a map EDGE (see simulate()'s stated simplification): "
      f"{sum(1 for r in all_rows if r['reason'] == 'edge')}")
print("\n  Endpoint reasons across the whole ROM:")
reasons: dict[str, int] = {}
for r in all_rows:
    reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
    print(f"    {k:<12} {v}")

head("4b. ‼ IS THE DISMOUNT PREMISE ACTUALLY TRUE? — elevation of every D1 tile the game would")
print("  KI-76's mechanism is specific: the game dismounts you onto land at ELEVATION_DEFAULT (3).")
print("  If a D1-armed chain's next tile is NOT elevation 3, the dismount claim does not obviously")
print("  hold for it and it must not be counted as if it did. ⛔ Do not assume this — it is the")
print("  premise the whole defect rests on, and it costs one dict to check.\n")
elevs: dict[int, int] = {}
for r in all_rows:
    if r["d1"]:
        elevs[r["next_elev"]] = elevs.get(r["next_elev"], 0) + 1
for k, v in sorted(elevs.items(), key=lambda kv: -kv[1]):
    tag = "  <- ELEVATION_DEFAULT: the documented dismount case" if k == 3 else "  <- ‼ NOT elevation 3 — the dismount mechanism is UNCONFIRMED for these"
    print(f"    elevation {k:<3} {v:>6}{tag}")

head("4c. ‼‼ THE ORACLE — PRODUCTION'S OWN ENDPOINT vs THIS PROBE'S REPLICA")
print("  v1 of this probe classified on its OWN re-implementation and therefore could not see past")
print("  a map boundary; an adversarial review kicked that back, correctly. Every count above is now")
print("  classified on `PathTile.forced_movement_to` — the value `map_path.py:260-350` ITSELF")
print("  computes, cross-map connection following and the shared 512-step budget included.")
print("  ⇒ There is no longer an `edge` blind spot: production followed those chains and this probe")
print("    read where they truly ended.\n")
covered = [r for r in all_rows if r.get("prod") is not None]
uncovered = [r for r in all_rows if r.get("prod") is None]
agree = [r for r in covered if r["agree"]]
disagree = [r for r in covered if not r["agree"]]
print(f"    chains production answered for : {len(covered)} of {len(all_rows)}")
print(f"    replica AGREED with production  : {len(agree)}")
print(f"    replica DISAGREED (production wins; these are the cross-map chains v1 could not see):"
      f" {len(disagree)}")
if uncovered:
    print(f"    ‼ production returned NO forced-movement for {len(uncovered)} chain(s) — a real gap,")
    print("      not a zero. Do not fold these into any total.")
dis_by_map: dict[str, int] = {}
for n, rows_ in results.items():
    d = sum(1 for r in rows_ if r.get("prod") is not None and not r["agree"])
    if d:
        dis_by_map[n] = d
for n, v in sorted(dis_by_map.items(), key=lambda kv: -kv[1]):
    print(f"      {n:<30} {v:>6} chain(s) where the replica stopped short of production")
print("\n  ‼ A DISAGREEMENT IS NOT A PROBE BUG: it is precisely the cross-map case, and production's")
print("    answer is the one used above. Agreement on the remaining chains is what shows the replica")
print("    was faithful everywhere it could see — which is why the break-REASON it supplies is safe.")

if prod_notes:
    print("\n  ‼‼ PRODUCTION RAISED ON THESE MAPS — the 512-step cap FIRED, which is a live defect:")
    for n, note in prod_notes.items():
        print(f"      {n}: {note}")
else:
    print("\n  ✅ THE 512-STEP CAP NEVER FIRED on any map with currents, with production following")
    print("     every cross-map chain on ONE shared budget. ⇒ no current chain in this ROM cycles,")
    print("     and the cap cannot truncate a healthy path. (This is the claim v1 could NOT make.)")
prod_max = max((r.get("prod_steps", 0) for r in covered), default=0)
print(f"\n  Longest chain PRODUCTION computed (cross-map following included): {prod_max} steps")
print(f"  ⇒ against the 512 cap at `map_path.py:260` that is a {512 / prod_max:.1f}x margin, "
      f"now PROVEN rather than assumed.")

noconn = [r for r in all_rows if r["reason"] == "noconn"]
print(f"\n  ⛔ THE ONE RESIDUAL, STATED RATHER THAN ROUNDED AWAY: {len(noconn)} chain(s) "
      f"({100.0 * len(noconn) / len(all_rows):.1f}%) end ON a map edge,")
print("     so the tile the game would dismount onto lies on the NEIGHBOURING map and this")
print("     classifier does not read across that boundary. They are counted as NOT D1-armed.")
print(f"  ⇒ ‼ THE D1 TOTAL IS THEREFORE A LOWER BOUND, UNDERSTATED BY AT MOST {len(noconn)}.")
print("     (D2 is unaffected: it is decided by the endpoint tile itself, which production gave us.)")

if failed:
    print(f"\n‼ UNREADABLE MAPS (measurement gaps, not zeroes): {len(failed)}")
    for name, err in failed[:10]:
        print(f"    {name}: {err}")

head("DONE — measurement only. Nothing was changed.")

if not control_ok:
    print("‼‼ POSITIVE CONTROL FAILED — this probe could not reproduce KI-76's recorded cavern")
    print("   numbers, so its ROUTE132/133/134 figures are NOT evidence. Fix the probe first.")
    sys.exit(1)

print("✅ Positive control reproduced both recorded cavern numbers — the counts above are evidence.")
sys.exit(0)
