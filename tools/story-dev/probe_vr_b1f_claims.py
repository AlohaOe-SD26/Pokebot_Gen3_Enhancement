"""Check the Victory Road B1F/B2F audit's LOAD-BEARING COORDINATES against the decomp myself.

⛔ WHY THIS EXISTS. An agent audit produced a headline that §Ch23 code will depend on: *two boulder
pushes permanently seal B1F, and both are available on the first move.* That audit is a NOTE, not
truth (`ai-research-notes/00-READ-THIS-FIRST.md`), and the single most likely way it is wrong is a
COORDINATE-SPACE mistake — if its object coordinates are offset from the layout grid by a constant,
every tile it names is wrong and the conclusion is worthless while still reading perfectly.

‼ WHAT THIS PROBE DOES AND DOES NOT SETTLE.
  ✅ It settles GEOMETRY: do the named boulders exist at the named tiles, are the shaft-bottom walls
     really walls, are the push destinations really open, are the standing tiles really standable.
  ⛔ It does NOT settle the SOKOBAN, and it MUST NOT TRY. Which pushes are fatal, and whether a
     solution is minimal, are questions about a reachable STATE GRAPH. This probe once answered them
     by building a board and calling `reachable()` on it, and produced two confident FALSE
     refutations — see the long comment at section 6. **Do not cite this probe as confirming or
     refuting the seal.** Two independent Sokoban solvers do that (note §0 and §E3); the live checks
     in §F outrank both.

It reuses `solve_victory_road.py`'s loader on purpose, so the byte-length assertion that guards
against the silent base64 corruption applies here too.
"""
from __future__ import annotations

import collections

import solve_victory_road as S

# The audit's claims, transcribed. Each is checked, not assumed.
ARRIVAL = (8, 3)
LADDER_B2F = (30, 25)
SEALING = [((4, 7), (4, 8)), ((9, 10), (9, 11))]        # boulder -> the FATAL south destination
SHAFT_BOTTOMS = [(4, 11), (9, 14)]                       # claimed collision-1 walls
SOLUTION = [                                             # (boulder, stand_on, dest, direction)
    ((4, 7), (5, 7), (3, 7), "WEST"),
    ((9, 10), (8, 10), (10, 10), "EAST"),
]
SMASH = (18, 12)
CLAIMED_CHAMBER = 23


def head(t: str) -> None:
    print("\n" + "=" * 96 + f"\n{t}\n" + "=" * 96)


def main() -> int:
    fails: list[str] = []
    b1f = S.load_floor("B1F")
    print(f"B1F loaded: {b1f['w']}x{b1f['h']}, {b1f['raw_len']} bytes "
          f"(= {b1f['w']}*{b1f['h']}*2 = {b1f['w'] * b1f['h'] * 2}) ✅ length asserted by the loader")

    # ---- 1. THE OBJECTS ------------------------------------------------------------------------
    head("1. WHAT OBJECTS ARE ACTUALLY ON B1F, AND WHERE")
    by_gfx: dict[str, list[tuple[int, int]]] = collections.defaultdict(list)
    for obj in b1f["meta"].get("object_events", []):
        by_gfx[obj.get("graphics_id", "?")].append((obj["x"], obj["y"]))
    for gfx, tiles in sorted(by_gfx.items()):
        print(f"  {gfx:<38} n={len(tiles):<3} {sorted(tiles)}")
    boulders = set(by_gfx.get(S.BOULDER_GFX, []))
    rocks = set(by_gfx.get(S.ROCK_GFX, []))
    print(f"\n  boulders={len(boulders)}  rocks={len(rocks)}")
    if len(boulders) != 8:
        fails.append(f"CLAIM 'B1F has 8 boulders' -> found {len(boulders)}")
    if len(rocks) != 6:
        fails.append(f"CLAIM 'B1F has 6 rocks' -> found {len(rocks)}")

    # ---- 2. DO THE NAMED BOULDERS EXIST? The coordinate-space test. -----------------------------
    head("2. ⛔ THE COORDINATE-SPACE TEST — do the named boulders exist at the named tiles?")
    for b, _ in SEALING:
        ok = b in boulders
        print(f"  boulder at {b}: {'✅ PRESENT' if ok else '⛔ ABSENT'}")
        if not ok:
            fails.append(f"CLAIM 'a boulder sits at {b}' -> no boulder there; the audit's object "
                         f"coordinates may be in a different space than the layout grid")
    print(f"  rock at {SMASH}: {'✅ PRESENT' if SMASH in rocks else '⛔ ABSENT'}")
    if SMASH not in rocks:
        fails.append(f"CLAIM 'smash the rock at {SMASH}' -> no rock there")

    # ---- 3. THE SHAFT GEOMETRY — the reason a south push is claimed fatal ------------------------
    head("3. THE SHAFT GEOMETRY — is there really a wall at the bottom?")
    for t in SHAFT_BOTTOMS:
        c = b1f["collision"].get(t)
        print(f"  {t}: collision={c} {'✅ WALL' if c else '⛔ OPEN — not a closed shaft'}")
        if not c:
            fails.append(f"CLAIM '{t} is collision-1 (the shaft bottom)' -> collision={c}")
    print("\n  the shaft interiors (must be OPEN for the boulder to be pushed in at all):")
    for (bx, by), (dx, dy) in SEALING:
        col = [(bx, y) for y in range(by + 1, SHAFT_BOTTOMS[0][1] + 4) if (bx, y) in b1f["collision"]]
        line = "  ".join(f"({x},{y}):{b1f['collision'][(x, y)]}" for x, y in col[:8])
        print(f"    x={bx} below y={by}: {line}")

    # ---- 4. THE MINIMUM SOLUTION'S TILES ---------------------------------------------------------
    head("4. THE 2-PUSH SOLUTION — are the stand tiles standable and the destinations open?")
    occupied = {(o["x"], o["y"]) for o in b1f["meta"].get("object_events", [])}
    for boulder, stand, dest, direction in SOLUTION:
        sc, dc = b1f["collision"].get(stand), b1f["collision"].get(dest)
        se, de, be = (b1f["elevation"].get(stand), b1f["elevation"].get(dest),
                      b1f["elevation"].get(boulder))
        dest_free = dest not in occupied
        ok = sc == 0 and dc == 0 and dest_free
        print(f"  PUSH {direction} {boulder} -> {dest}, standing {stand}")
        print(f"    stand {stand}: collision={sc} elev={se}   dest {dest}: collision={dc} "
              f"elev={de} unoccupied={dest_free}   boulder elev={be}")
        # ⚠ A push crossing an elevation boundary is not a plain move; flag it rather than judge it.
        if len({e for e in (se, de, be) if e is not None}) > 1:
            print(f"    ⚠ elevations differ across stand/boulder/dest — a push across an elevation "
                  f"boundary is NOT modelled here; treat as UNSETTLED")
        print(f"    => {'✅ geometrically legal' if ok else '⛔ ILLEGAL'}")
        if not ok:
            fails.append(f"CLAIM 'PUSH {direction} {boulder} -> {dest} from {stand}' -> "
                         f"stand collision={sc}, dest collision={dc}, dest unoccupied={dest_free}")

    # ---- 5. THE ARRIVAL CHAMBER ------------------------------------------------------------------
    head("5. THE ARRIVAL CHAMBER — is it really 23 tiles whose only exits are those two boulders?")
    # Boulders and rocks PRESENT (nothing cleared yet): this is the floor as the bot first meets it.
    virgin = S.blockers(b1f, strength=False, rock_smash=False)
    seen = S.reachable(b1f, ARRIVAL, blocked=virgin)
    print(f"  reachable from {ARRIVAL} with every boulder and rock in place: {len(seen)} tiles "
          f"(audit says {CLAIMED_CHAMBER})")
    if len(seen) != CLAIMED_CHAMBER:
        fails.append(f"CLAIM 'the arrival chamber is {CLAIMED_CHAMBER} tiles' -> {len(seen)}")
    print(f"  is the B2F ladder {LADDER_B2F} reachable from the chamber? "
          f"{'⛔ YES — then it is not sealed at all' if LADDER_B2F in seen else '✅ NO, as claimed'}")
    if LADDER_B2F in seen:
        fails.append("CLAIM 'the chamber is closed' -> the B2F ladder is reachable without any push")

    # Which obstacles actually touch the chamber? THIS is the "only two exits" claim.
    touching = {t: [] for t in ("boulder", "rock")}
    for tile in sorted(seen):
        for d in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            n = (tile[0] + d[0], tile[1] + d[1])
            if n in boulders:
                touching["boulder"].append(n)
            elif n in rocks:
                touching["rock"].append(n)
    tb, tr = sorted(set(touching["boulder"])), sorted(set(touching["rock"]))
    print(f"  obstacles ADJACENT to the chamber: boulders={tb}  rocks={tr}")
    if set(tb) != {b for b, _ in SEALING}:
        fails.append(f"CLAIM 'the only two exits are the boulders at (4,7) and (9,10)' -> the "
                     f"chamber actually touches boulders {tb}")
    if tr:
        fails.append(f"CLAIM 'no rock is adjacent to the arrival chamber' -> rocks {tr} are")

    # ---- 6. ⛔⛔ THE SECTION THAT USED TO BE HERE WAS WRONG. READ THIS BEFORE WRITING ANOTHER. ----
    # This probe once carried two more sections that "tested" the seal and the minimality of the
    # 2-push solution by BUILDING A BOARD (move the boulders, delete the rock) and asking
    # `reachable()` about it. Both produced CONFIDENT FALSE REFUTATIONS:
    #     "PUSH WEST (4,7) is REDUNDANT"          -> WRONG, it is required
    #     "pushing (4,7) SOUTH does not seal"     -> WRONG, it seals (indirectly)
    #
    # ⛔ ROOT CAUSE, AND IT IS NOT THE ONE I FIRST GUESSED. I blamed the missing directional
    # edge-blocker rule; an independent solver PROVED that rule is vacuous on B1F (all 13 passable
    # MB_IMPASSABLE_NORTH tiles have a wall directly north, so 0 passable->passable crossings are
    # blocked by it). The real cause is simpler and more general:
    #
    #   ‼ APPLYING A SUBSET OF ACTIONS DOES NOT PRODUCE A REACHABLE STATE.
    #
    # The seal test cleared "every other obstacle" — but you cannot clear them FROM the sealed
    # state; that is what sealed means. The necessity test dropped push 1 and kept push 2 — but the
    # ONLY way to (8,10), where you must stand to make push 2, is (4,7)->(4,10)->(8,10), which push
    # 1 is what opens. Both boards are unreachable, and a query over an unreachable board can
    # neither confirm nor refute anything.
    #
    # ⇒ THE RULE: a "necessity" test that removes step k and keeps step k+1 assumes the steps are
    #   INDEPENDENT. These pushes are ORDER-DEPENDENT — a fact this project had already written
    #   down before I tested as though it were false.
    # ⇒ THE RIGHT INSTRUMENT is a Sokoban over the reachable STATE GRAPH (player position + carried
    #   elevation + boulder positions + rock mask), enumerating forced FIRST ACTIONS. That is what
    #   `ai-research-notes/2026-09-03-ch23-VICTORY-ROAD-B1F-B2F.md` §E3 records; two independent
    #   solvers agree on 70,442 reachable states, 891 dead, 2 fatal actions, minimum cost 3.
    # ⛔ DO NOT re-add a reachability-over-a-hand-built-board test here. Being generous with it does
    #   not repair it — generosity over an impossible premise is still vacuous.
    print("\n" + "=" * 96)
    print("6. GEOMETRY ONLY — THE SOKOBAN QUESTIONS ARE DELIBERATELY NOT ASKED HERE")
    print("=" * 96)
    print("  This probe answers 'are the named tiles what the audit says they are?' and stops.")
    print("  It does NOT decide which pushes are fatal or whether a solution is minimal: those are")
    print("  questions about a STATE GRAPH, and a reachability query over a hand-built board gives")
    print("  confident wrong answers to them. (It did, twice — see the comment above this line.)")
    print("  ⇒ For those, see the two independent Sokoban solvers recorded in")
    print("    `ai-research-notes/2026-09-03-ch23-VICTORY-ROAD-B1F-B2F.md` §0 and §E3.")

    # ---- verdict ---------------------------------------------------------------------------------
    head("VERDICT")
    if fails:
        print(f"⛔ {len(fails)} CLAIM(S) DO NOT SURVIVE A DIRECT READ OF THE DECOMP:")
        for f in fails:
            print(f"   - {f}")
    else:
        print("✅ every GEOMETRIC claim checked here survives a direct read of the decomp.")
    print("\n⛔ SCOPE, RESTATED SO IT IS NOT OVERCLAIMED: this probe checked GEOMETRY ONLY — object")
    print("   positions, wall/floor collision, and chamber reachability. It does NOT model boulder")
    print("   pushes, so it CANNOT confirm 'exactly these two pushes are fatal and no others'.")
    print("   That still needs the independent re-derivation and the three LIVE checks in")
    print("   `ai-research-notes/2026-09-03-ch23-VICTORY-ROAD-B1F-B2F.md` §F.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
