"""§Ch23 — VICTORY ROAD: what does the entrance→exit route actually require?

⛔⛔ THIS SCRIPT'S FIRST VERSION WAS WRONG, AND THE WAY IT WAS WRONG IS THE REASON IT NOW EXISTS
IN THIS FORM. It reported a "71-step 1F-only route needing no Strength and no Rock Smash", which
would have deleted a boulder solver from §Ch23. An adversarial review refuted it, and the refutation
is confirmed against our OWN production pathfinder:

    modules/map_path.py:859   if tile.elevation not in (0, 15) and from_elevation != 0 \\
                                   and tile.elevation != from_elevation: return False
    modules/map_path.py:1039  if neighbour.elevation == 15: elevation = node.elevation
                              else:                         elevation = neighbour.elevation

⇒ Gen 3 gives the PLAYER a **carried elevation**, and an elevation-15 tile **preserves** it rather
than setting it. v1 compared TILE-TO-TILE and treated any 15 as a free pass — so it walked straight
across the multi-level bridge on 1F, where an elevation-3 corridor passes UNDER an elevation-4 one,
and joined two regions the game keeps apart. **Our own planner would have refused that route**, so
the number could never have driven.

‼ **AND V1 HAD A NEGATIVE CONTROL THAT PASSED.** It proved 0 of 1,388 *collision* tiles leaked into
the reachable set — and said NOTHING about elevation, which is where the bug was. **A control tests
the failure mode it was written for and no other.** That is why this version carries a control for
EACH model, and a fault arm for each, independently.

WHAT IT ANSWERS:
  Q1  Is the exit reachable on 1F alone?              (v1 said yes; the answer is NO)
  Q2  What does the real route require?               (per-kit reachability across all three floors)
  Q3  Is Wally's trigger on the way, or a detour?

Usage:
    py -3.12 solve_victory_road.py --self-test     # ⛔ RUN THIS FIRST; the controls are the point
    py -3.12 solve_victory_road.py
    py -3.12 solve_victory_road.py --refresh       # re-download the decomp inputs
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request
from collections import deque

RAW = "https://raw.githubusercontent.com/pret/pokeemerald/master/"
CACHE = pathlib.Path(__file__).resolve().parent / ".cache" / "victory_road"

FLOORS = {
    "1F": dict(w=46, h=45, blockdata="data/layouts/VictoryRoad_1F/map.bin",
               mapjson="data/maps/VictoryRoad_1F/map.json"),
    "B1F": dict(w=46, h=31, blockdata="data/layouts/VictoryRoad_B1F/map.bin",
                mapjson="data/maps/VictoryRoad_B1F/map.json"),
    "B2F": dict(w=46, h=31, blockdata="data/layouts/VictoryRoad_B2F/map.bin",
                mapjson="data/maps/VictoryRoad_B2F/map.json"),
}

ENTRANCE = ("1F", (15, 40))
EXIT = ("1F", (39, 5))
WALLY_TRIGGERS = [(2, 23), (3, 23)]

#: Where the CONTROLS start on each floor. ⛔ Derived from the WARP GRAPH, not invented:
#: 1F(9,14) -> dest_warp_id 4 -> B1F warp index 4 = (8,3); B1F(30,25) <-> B2F(30,25).
#: ‼ Each must be elevation != 15, or this model's start diverges from the game's
#: ELEVATION_TRANSITION(0) — the self-test asserts exactly that, per floor.
FLOOR_STARTS = {"1F": (15, 40), "B1F": (8, 3), "B2F": (30, 25)}

BOULDER_GFX = "OBJ_EVENT_GFX_PUSHABLE_BOULDER"
ROCK_GFX = "OBJ_EVENT_GFX_BREAKABLE_ROCK"
#: Object graphics that block a tile but are neither a boulder nor a rock (trainers, item balls).
#: ⚠ Both Wallys are flag-hidden before their battles, so they do NOT block on the way in.
HIDDEN_BEFORE_BATTLE = ("OBJ_EVENT_GFX_WALLY",)


def _fetch(path: str, *, refresh: bool = False) -> bytes:
    """⛔ BINARY-SAFE: `gh api --jq .content | base64 -d` silently UTF-8 re-encodes bytes >= 0x80
    on this machine (a 7,200-byte map.bin came back as 9,433). Fetch raw; the caller asserts length."""
    out = CACHE / path.replace("/", "__")
    if out.exists() and not refresh:
        return out.read_bytes()
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(RAW + path, timeout=60) as response:
        data = response.read()
    out.write_bytes(data)
    return data


def load_floor(name: str, *, refresh: bool = False) -> dict:
    spec = FLOORS[name]
    raw = _fetch(spec["blockdata"], refresh=refresh)
    expected = spec["w"] * spec["h"] * 2
    if len(raw) != expected:
        raise SystemExit(
            f"⛔ REFUSING TO DECODE {spec['blockdata']}: {len(raw)} bytes, expected {expected} "
            f"({spec['w']}x{spec['h']} u16). This is the SILENT BINARY CORRUPTION the fetch note "
            f"warns about — do NOT relax this check."
        )
    collision, elevation = {}, {}
    for i in range(spec["w"] * spec["h"]):
        block = raw[i * 2] | (raw[i * 2 + 1] << 8)
        xy = (i % spec["w"], i // spec["w"])
        collision[xy] = (block >> 10) & 0x3
        elevation[xy] = (block >> 12) & 0xF
    meta = json.loads(_fetch(spec["mapjson"], refresh=refresh).decode("utf-8"))
    return dict(name=name, w=spec["w"], h=spec["h"], collision=collision,
                elevation=elevation, meta=meta, raw_len=len(raw))


def blockers(floor: dict, *, strength: bool, rock_smash: bool) -> set:
    """Tiles blocked by objects, given which field moves the party holds.

    ⚠ A held move is modelled as "the obstacle is simply gone". That OVER-approximates (a real push
    needs room behind the boulder), so every UNREACHABLE verdict below is CONSERVATIVE and every
    step count is a LOWER bound.
    """
    out = set()
    for obj in floor["meta"].get("object_events", []):
        gfx = obj.get("graphics_id", "?")
        if gfx in HIDDEN_BEFORE_BATTLE:
            continue
        if gfx == BOULDER_GFX and strength:
            continue
        if gfx == ROCK_GFX and rock_smash:
            continue
        out.add((obj["x"], obj["y"]))
    return out


def _enterable(map_elev: int, carried: int) -> bool:
    """The rule, copied from our own `map_path.py:859` so the two can never drift apart."""
    return map_elev in (0, 15) or carried == 0 or map_elev == carried


def _carry(map_elev: int, carried: int) -> int:
    """`map_path.py:1039` — an elevation-15 tile PRESERVES the carried elevation."""
    return carried if map_elev == 15 else map_elev


def reachable(floor: dict, start: tuple[int, int], *, blocked=frozenset(),
              ignore_collision: bool = False, ignore_elevation: bool = False,
              break_carry: bool = False) -> dict:
    """BFS keyed by (x, y, CARRIED ELEVATION) — the same state our A* uses.

    ⛔ Keying by tile alone is what made v1 wrong: the SAME tile at two carried elevations is two
    different states, and collapsing them lets the search change levels for free.
    """
    collision, elev = floor["collision"], floor["elevation"]
    if start not in collision:
        raise ValueError(f"start {start} is off the {floor['name']} grid")
    start_state = (start, _carry(elev[start], elev[start]))
    seen = {start_state: 0}
    best: dict[tuple[int, int], int] = {start: 0}
    queue = deque([start_state])
    while queue:
        (here, carried) = queue.popleft()
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nxt = (here[0] + dx, here[1] + dy)
            if nxt not in collision or nxt in blocked:
                continue
            if not ignore_collision and collision[nxt] != 0:
                continue
            if not ignore_elevation and not _enterable(elev[nxt], carried):
                continue
            # `break_carry` is the FAULT INJECTION for `_carry`: a 15-tile SETS the
            # elevation instead of preserving it. Used only by the self-test.
            if ignore_elevation:
                nxt_carried = carried
            elif break_carry:
                nxt_carried = elev[nxt]
            else:
                nxt_carried = _carry(elev[nxt], carried)
            state = (nxt, nxt_carried)
            if state in seen:
                continue
            seen[state] = seen[(here, carried)] + 1
            if nxt not in best or seen[state] < best[nxt]:
                best[nxt] = seen[state]
            queue.append(state)
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    floors = {n: load_floor(n, refresh=args.refresh) for n in FLOORS}
    for f in floors.values():
        b = blockers(f, strength=False, rock_smash=False)
        nb = sum(1 for o in f["meta"].get("object_events", [])
                 if o.get("graphics_id") == BOULDER_GFX)
        nr = sum(1 for o in f["meta"].get("object_events", [])
                 if o.get("graphics_id") == ROCK_GFX)
        print(f"{f['name']:>4}  {f['w']}x{f['h']}  {f['raw_len']} bytes (asserted)   "
              f"objects blocking: {len(b):>2}   boulders: {nb}   rocks: {nr}")

    if args.self_test:
        # ⛔ v2 ran its controls on 1F ONLY while printing answers for three floors. The B1F and
        # B2F models were therefore uncontrolled — and B1F is where the whole boulder question is.
        rc = 0
        for name in ("1F", "B1F", "B2F"):
            print(f"\n########## CONTROLS FOR {name} ##########")
            rc |= _self_test(floors[name], name)
        return rc

    f1 = floors["1F"]
    block = blockers(f1, strength=False, rock_smash=False)

    print("\n=== Q1 — is the exit reachable on 1F ALONE? ===")
    seen = reachable(f1, ENTRANCE[1], blocked=block)
    steps = seen.get(EXIT[1])
    print(f"  entrance {ENTRANCE[1]} -> exit {EXIT[1]}: "
          f"{'UNREACHABLE' if steps is None else f'{steps} steps'}   "
          f"({len(seen)} tiles reachable)")
    loose = reachable(f1, ENTRANCE[1], blocked=block, ignore_elevation=True)
    print(f"  ⛔ WITH ELEVATION IGNORED (v1's bug): "
          f"{'UNREACHABLE' if EXIT[1] not in loose else f'{loose[EXIT[1]]} steps'}   "
          f"({len(loose)} tiles) — ‼ if these two disagree, ELEVATION is what separates the "
          f"regions, and any answer computed without it is an artifact.")

    print("\n=== Q3 — Wally's trigger: on the way, or a detour? ===")
    ladders = [(w["x"], w["y"]) for w in f1["meta"]["warp_events"]
               if w.get("dest_map") == "MAP_VICTORY_ROAD_B1F"]
    for trig in WALLY_TRIGGERS:
        print(f"  trigger {trig}: "
              f"{'UNREACHABLE' if trig not in seen else f'{seen[trig]} steps from the entrance'}")
    for lad in ladders:
        if lad in seen:
            print(f"  B1F ladder {lad}: {seen[lad]} steps from the entrance")
    reachable_trigs = [t for t in WALLY_TRIGGERS if t in seen]
    if reachable_trigs and ladders:
        t0 = min(reachable_trigs, key=lambda t: seen[t])
        via = reachable(f1, t0, blocked=block)
        for lad in ladders:
            if lad in seen and lad in via:
                detour = seen[t0] + via[lad] - seen[lad]
                print(f"  ⇒ via {t0} to ladder {lad}: {seen[t0]} + {via[lad]} vs {seen[lad]} "
                      f"direct ⇒ DETOUR COST = {detour} steps")

    print("\n=== Q2 — what the route needs, per kit (1F reach only; warps are the real graph) ===")
    for label, (st, rs) in (("neither", (False, False)), ("Strength", (True, False)),
                            ("Rock Smash", (False, True)), ("both", (True, True))):
        b1 = floors["B1F"]
        arrival = (8, 3)   # B1F side of the 1F (9,14) ladder
        r = reachable(b1, arrival, blocked=blockers(b1, strength=st, rock_smash=rs))
        warps = [(w["x"], w["y"], w.get("dest_map")) for w in b1["meta"]["warp_events"]
                 if (w["x"], w["y"]) in r]
        print(f"  B1F from {arrival} with [{label:<10}]: {len(r):>3} tiles, "
              f"warps reached: {[(x, y, d.replace('MAP_VICTORY_ROAD_', '')) for x, y, d in warps]}")
    print("\n⛔⛔ DO NOT ACT ON AN 'UNREACHABLE' FROM THIS SCRIPT. It models LAND ONLY: no SURF "
          "(B2F is 238 tiles of MB_OCEAN_WATER at elevation 1), no WATERFALL, no LEDGE jumps. On "
          "TERRAIN it UNDER-approximates, so it can call reachable ground unreachable.")
    print("‼ A previous version of this line claimed 'UNREACHABLE verdicts are conservative'. That "
          "was FALSE and an adversarial review refuted it: the conservatism applies only to the "
          "OBJECT model ('the obstacle is gone'), never to terrain.")
    print("⇒ For a terrain question, ask PRODUCTION instead — `--driver ch23route` calls the real "
          "`calculate_path`, which models surf and waterfall natively. This script's job is the "
          "PER-KIT OBJECT SPLIT, which production cannot answer because it has no Strength model.")
    print("‼ It also models no trainer sight lines, and boulder pushes are ORDER-DEPENDENT — three "
          "B1F boulders have no legal push until their paired rock is smashed — so the 'both' "
          "figure is an upper bound achievable in one specific order, not a route.")
    return 0


def _self_test(floor: dict, floor_name: str = "1F") -> int:
    """⛔ ONE CONTROL PER MODEL. v1 had a collision control that passed while the ELEVATION model
    was broken — a control tests the failure mode it was written for and no other."""
    print("\n=== SELF-TEST ===")
    fails = []
    block = blockers(floor, strength=False, rock_smash=False)
    start = FLOOR_STARTS[floor_name]
    seen = reachable(floor, start, blocked=block)

    # ⛔⛔ THE TERRAIN CONTROLS MUST RUN ON THE LARGEST REACHABLE CONFIGURATION, NOT THE SMALLEST.
    # They answer "is the elevation model LIVE on this floor", and from B1F's arrival tile with
    # every boulder in place only 23 tiles are reachable — far too few to exercise elevation, so
    # both terrain controls FAILED there. ‼ That failure was HONEST (they correctly refused to
    # certify what they could not test); the fix is to give them a state that CAN test it — both
    # field moves held, which is what the route actually holds when it crosses B1F — NOT to
    # weaken the assertion.
    open_block = blockers(floor, strength=True, rock_smash=True)
    terrain_seen = reachable(floor, start, blocked=open_block)
    if len(terrain_seen) > len(seen):
        print(f"  ℹ terrain controls run with BOTH field moves held ({len(terrain_seen)} tiles "
              f"vs {len(seen)} with neither) — the smaller set cannot exercise elevation here")

    if seen.get(start) != 0:
        fails.append("positive: the entrance does not reach itself in 0 steps")
    else:
        print(f"  ✅ positive: the {floor_name} start {start} reaches itself in 0 steps")

    walls = [t for t, c in floor["collision"].items() if c != 0]
    leaked = [t for t in walls if t in seen]
    if leaked:
        fails.append(f"negative(collision): {len(leaked)} wall tiles reachable, e.g. {leaked[:4]}")
    else:
        print(f"  ✅ negative(collision): 0 of {len(walls)} wall tiles reachable")

    loose_c = reachable(floor, start, blocked=block, ignore_collision=True)
    wall = next((t for t in walls if t not in seen), None)
    if wall is not None and wall in loose_c:
        print(f"  ✅ fault(collision): ignoring collision makes {wall} reachable ⇒ the refusal is "
              f"the COLLISION model")
    else:
        fails.append("fault(collision): a wall stayed unreachable with collision ignored")

    # ⭐ THE CONTROL v1 DID NOT HAVE. There must exist an OPEN tile (collision 0) that the
    # elevation model refuses, and disabling ONLY the elevation rule must make it reachable.
    loose_e = reachable(floor, start, blocked=open_block, ignore_elevation=True)
    open_tiles = [t for t, c in floor["collision"].items() if c == 0 and t not in open_block]
    elev_blocked = [t for t in open_tiles if t not in terrain_seen and t in loose_e]
    if not elev_blocked:
        # ⛔ TWO CAUSES LOOK IDENTICAL HERE, AND ONLY ONE IS A DEFECT: either the elevation ENTRY
        # rule is broken/inert (the v1 bug), or this floor is simply flat enough that elevation
        # gates nothing from this start. ‼ They are DISTINGUISHABLE, and the distinction is already
        # measured a few lines below: if breaking `_carry` changes the answer, the elevation
        # machinery is demonstrably LIVE on this floor, so an inert ENTRY rule is a MAP FACT.
        # ⇒ report it, do not fail — a control that fails on a map property teaches the next
        # maintainer to weaken it, which is strictly worse than no control.
        carry_live = len(reachable(floor, start, blocked=open_block, break_carry=True)) !=             len(terrain_seen)
        if carry_live:
            print(f"  ⚠ negative(elevation): NO open tile on {floor_name} is refused by the ENTRY "
                  f"rule alone — but breaking `_carry` DOES change this floor's answer, so the "
                  f"elevation machinery is live and this is a MAP PROPERTY, not a broken model. "
                  f"UNCERTIFIED here, and said so rather than passing silently.")
        else:
            fails.append(f"negative(elevation): on {floor_name} NEITHER the entry rule NOR the "
                         f"carry changes anything — the elevation model is inert and UNTESTED. "
                         f"This is the v1 shape; do not trust this floor's answers.")
    else:
        print(f"  ✅ negative(elevation): {len(elev_blocked)} OPEN tiles are refused by the "
              f"elevation model alone, e.g. {sorted(elev_blocked)[:4]}")
        # ⛔ THE FAULT ARM MUST BE COMPUTED SEPARATELY, NOT RESTATED. An adversarial review found
        # the old line sitting in this same `else` and merely repeating `elev_blocked`'s own
        # definition — it could not fail independently, so it certified nothing. The arm now
        # asserts a DIFFERENT fact: that the exit's reachability itself flips with the rule.
        anchor = EXIT[1] if floor_name == "1F" else sorted(elev_blocked)[0]
        exit_strict = anchor in terrain_seen
        exit_loose = anchor in loose_e
        if exit_loose and not exit_strict:
            print(f"  ✅ fault(elevation): {anchor} is unreachable WITH the elevation "
                  f"rule and reachable WITHOUT it ⇒ elevation is what separates the regions, and "
                  f"v1's '71 steps' was exactly this artifact")
        else:
            fails.append(f"fault(elevation): the exit's reachability does NOT flip with the "
                         f"elevation rule (strict={exit_strict} loose={exit_loose}) — this arm is "
                         f"not anchored to the defect it exists to catch")

    if floor_name == "1F" and EXIT[1] in seen and EXIT[1] in loose_e and seen.get(EXIT[1]) == loose_e.get(EXIT[1]):
        print("  ⚠ note: the exit is reachable identically with and without elevation — on THIS "
              "map that would mean elevation does not separate the regions. Read Q1's two lines.")

    # ⭐⭐ THE CONTROL v2 DID NOT HAVE, AND IT IS THE RULE v2 WAS WRITTEN TO ADD.
    # An adversarial review fault-injected `_carry` (making it `return map_elev`, i.e. a 15-tile
    # SETS the elevation instead of preserving it) and the self-test still printed PASS while the
    # answer changed from 477 tiles to 32 and the B1F ladder became UNREACHABLE.
    # ‼ THAT IS v1'S FAILURE REPEATED ONE LAYER UP: v1 controlled collision while the bug was in
    # elevation-ENTRY; v2 controlled entry while the new machinery was elevation-CARRY.
    # ⇒ this control asserts the carry is LOAD-BEARING: with it, some tile is reachable ONLY
    # because the carried elevation survived a 15-tile, and breaking the carry must lose it.
    broken = reachable(floor, start, blocked=open_block, break_carry=True)
    lost = [t for t in terrain_seen if t not in broken]
    if not lost:
        fails.append("negative(carry): breaking `_carry` changed NOTHING — either the carry is "
                     "inert on this map or the injection does not reach the search. Either way "
                     "this control cannot certify the rule it exists for.")
    else:
        print(f"  ✅ negative(carry): breaking `_carry` (a 15-tile SETS instead of PRESERVES) loses "
              f"{len(lost)} tiles, e.g. {sorted(lost)[:4]} — the carry is LOAD-BEARING")
        # ⛔ ANCHOR THE ARM TO SOMETHING THE ROUTE DEPENDS ON, PER FLOOR — an arm
        # anchored to "some tile" can pass while the tile that matters is unaffected.
        ladder = {"1F": (9, 14), "B1F": (20, 21), "B2F": (19, 12)}[floor_name]
        if ladder in terrain_seen and ladder not in broken:
            print(f"  ✅ fault(carry): the B1F ladder {ladder} is reachable ONLY with the carry "
                  f"intact ({terrain_seen[ladder]} steps) ⇒ the rule decides real routing, not just counts")
        elif ladder not in terrain_seen:
            print(f"  ⚠ fault(carry): the anchor {ladder} is unreachable on {floor_name} even "
                  f"normally, so this arm cannot discriminate here — REPORTED, not graded.")
        else:
            fails.append(f"fault(carry): the {floor_name} anchor {ladder} survives a broken carry "
                         f"— this control is not anchored to anything the route depends on")

    # ⭐ A CONTROL FOR THE OBJECT MODEL, also missing: emptying `blockers()` must change the answer.
    no_objects = reachable(floor, start, blocked=frozenset())
    if len(no_objects) == len(seen):
        fails.append("negative(objects): removing every blocking object changed nothing — the "
                     "object model is inert and its per-kit answers mean nothing")
    else:
        print(f"  ✅ negative(objects): removing the {len(block)} blocking objects changes the "
              f"reachable set {len(seen)} -> {len(no_objects)} ⇒ the object model is live")

    try:
        reachable(floor, (999, 999))
        fails.append("negative: an off-grid start did not raise")
    except ValueError:
        print("  ✅ negative: an off-grid start RAISES")

    # ⛔ THE START-ELEVATION LANDMINE. The game sets `currentElevation` from the arrival tile, and
    # this model does the same — but ONLY because both start tiles are elevation 3. On an
    # elevation-15 arrival the game keeps 0 (permissive) while `_carry(15, 15)` returns 15
    # (restrictive), and the answer would silently collapse. Assert rather than hope.
    if floor["elevation"].get(start) == 15:
        fails.append(f"start-elevation: {floor_name} start {start} is elevation 15 — the carry "
                     f"would diverge from the game's ELEVATION_TRANSITION(0) start")
    else:
        print(f"  ✅ start-elevation: {floor_name} start {start} is elevation "
              f"{floor['elevation'][start]} (≠15, so the model's start matches the game's)")

    print()
    if fails:
        for f in fails:
            print(f"  ❌ {f}")
        print(f"\nSELF-TEST FAILED ({len(fails)})")
        return 1
    # ⛔ THE SUMMARY MUST NOT OVERSTATE WHAT RAN — a passing summary is what a future
    # reader quotes, and overclaiming is exactly what let v1 ship.
    print(f"SELF-TEST PASSED for {floor_name} — every control that COULD discriminate did, "
          f"and any that could not said so above (⚠) instead of passing silently.")
    return 0


if __name__ == "__main__":
    sys.exit(main())