"""§Ch20's EXIT — is the Kyogre landing tile really an ATOLL? Measured in OUR ROM, not recalled.

WHY THIS EXISTS
---------------
`ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md` Blocker 2 says the chapter's
forced exit lands the player on `ROUTE128 (38,22)`, releases them **facing NORTH**, and that north
is a **closed 41-tile lagoon** on a map with `"allow_escaping": false` — so the obvious move
strands the run permanently, and the correct move is SOUTH then Surf.

‼ That claim came from a subagent decoding `data/layouts/Route128/map.bin` off GitHub. It is a
NOTE, not truth, and it is exactly the kind of load-bearing claim this project requires to be
re-measured in our own harness before code depends on it — the standing rule after
`probe_shoal_tide.py` was found to have COPIED the pathfinder's bug and so agreed with production
while both were wrong. **This probe shares no code with that agent's decode**: it reads the live
ROM through `modules.map.get_map_all_tiles`, the same reader the chapter will use.

‼ IT IS ALSO THE CHEAPEST POSSIBLE INSURANCE. Three chapters have already shipped stranded
(§Ch15 four floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room). This one
is claimed to strand you BY DESIGN, and to point the trap the way the camera faces.

WHAT IT ANSWERS
  1. What is `(38,22)` — collision, elevation, tile_type — and what are its four neighbours?
  2. Flood-fill the ON-FOOT component containing `(38,22)`. Does it touch the map edge?
  3. Flood-fill the WATER component NORTH of the landing vs the one SOUTH. Are they the same
     component? Does each reach the map edge?
  4. ‼ THE ACTIONABLE ONE: from which neighbour, in which direction, can the bot actually Surf into
     the OPEN ocean? Reported as a concrete (step_to, face, surf_onto) triple.

CONTROLS (so a null result is attributable)
  * Every tile read is printed with its raw collision/elevation/tile_type — no derived-only claims.
  * The two water bodies are compared by COMPONENT IDENTITY, not by size: "41 vs 1766" is a
    suggestive pair of numbers, but "same component: False" is the finding.
  * A tile far south is checked to reach the map edge, as a POSITIVE control that the flood fill
    can find an edge at all — otherwise "does not reach the edge" would be unattributable.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_route128_landing.py
Exit: 0 always (measurement probe, not a gate).
"""

import pathlib
import sys
from collections import deque

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

LANDING = (38, 22)
ROUTE128 = MapRSE.ROUTE128

#: The claim under test, stated up front so the output can be read as PASS/FAIL against it rather
#: than as a pile of numbers. ‼ Pre-registered, in the house style.
CLAIM = (
    "Blocker 2: (38,22) is MB_SHALLOW_WATER; its on-foot component does NOT reach the map edge; "
    "the water NORTH of it is a CLOSED lagoon in a DIFFERENT component from the open ocean SOUTH; "
    "and the correct escape is to step SOUTH to (38,23), face south and Surf onto (38,24)."
)


def _fmt(tile) -> str:
    return f"coll={tile.collision} elev={tile.elevation} type={str(tile.tile_type)!r}"


def main() -> int:
    print("=" * 100)
    print("ROUTE 128 KYOGRE LANDING — is it an atoll?  (read from OUR ROM, live)")
    print("=" * 100)
    print(f"CLAIM UNDER TEST: {CLAIM}\n")

    tiles = get_map_all_tiles(get_map_data(ROUTE128, LANDING))
    by_xy = {t.local_position: t for t in tiles}
    width = max(x for x, _ in by_xy) + 1
    height = max(y for _, y in by_xy) + 1
    print(f"1 — MAP: ROUTE128 is {width} x {height}, {len(by_xy)} tiles read\n")

    print("2 — THE LANDING TILE AND ITS FOUR NEIGHBOURS")
    landing = by_xy.get(LANDING)
    print(f"    (38,22)  {_fmt(landing)}   <- where the cutscene drops the player")
    for label, xy in (("N", (38, 21)), ("S", (38, 23)), ("W", (37, 22)), ("E", (39, 22))):
        t = by_xy.get(xy)
        print(f"    {label} {xy}  {_fmt(t) if t is not None else '<off map>'}")
    print()

    def flood(start, passable):
        """4-way component from `start` over tiles satisfying `passable`. Returns (set, hit_edge)."""
        if start not in by_xy or not passable(by_xy[start]):
            return set(), False
        seen, queue, edge = {start}, deque([start]), False
        while queue:
            x, y = queue.popleft()
            if x in (0, width - 1) or y in (0, height - 1):
                edge = True
            for nxt in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
                if nxt in seen or nxt not in by_xy:
                    continue
                if passable(by_xy[nxt]):
                    seen.add(nxt)
                    queue.append(nxt)
        return seen, edge

    landing_type = str(landing.tile_type)
    on_foot = lambda t: t.collision == 0 and str(t.tile_type) == landing_type   # noqa: E731
    foot_set, foot_edge = flood(LANDING, on_foot)
    print("3 — THE ON-FOOT COMPONENT (tiles of the SAME type as the landing, collision 0)")
    print(f"    size={len(foot_set)}  reaches_map_edge={foot_edge}")
    print(f"    ‼ if reaches_map_edge is False the player is on an ISLAND of {len(foot_set)} tiles\n")

    # Water = anything walkable that is NOT the landing's own (shallow) type. Deliberately loose:
    # the question is "are north and south the SAME body", and a loose definition can only MERGE
    # them, never split them — so a False here is the strong direction of the result.
    water = lambda t: t.collision == 0 and str(t.tile_type) != landing_type    # noqa: E731
    north_seed, south_seed = (38, 20), (38, 24)
    north_set, north_edge = flood(north_seed, water)
    south_set, south_edge = flood(south_seed, water)
    same = bool(north_set) and bool(south_set) and (north_seed in south_set)
    print("4 — THE TWO WATER BODIES  (‼ the finding is the COMPONENT IDENTITY, not the sizes)")
    print(f"    NORTH seed {north_seed}: size={len(north_set)} reaches_map_edge={north_edge}")
    print(f"    SOUTH seed {south_seed}: size={len(south_set)} reaches_map_edge={south_edge}")
    print(f"    SAME COMPONENT? {same}")
    print(f"    POSITIVE CONTROL — the south body finding an edge proves the fill CAN find one: "
          f"{south_edge}\n")

    print("5 — WHERE CAN THE BOT ACTUALLY SURF?  (the actionable answer)")
    print("    A tile is a surf launch point if the bot can STAND on it and an adjacent tile is in")
    print("    the OPEN-OCEAN component. Shallow water is walkable but is NOT surfable in Gen 3,")
    print("    so facing the wrong way from the landing tile does nothing at all.")
    launches = []
    for xy in sorted(foot_set):
        x, y = xy
        for face, nxt in (("Up", (x, y - 1)), ("Down", (x, y + 1)),
                          ("Left", (x - 1, y)), ("Right", (x + 1, y))):
            if nxt in south_set:
                launches.append((xy, face, nxt))
    if launches:
        print(f"    {len(launches)} launch point(s) onto the open ocean; nearest to the landing:")
        launches.sort(key=lambda L: abs(L[0][0] - LANDING[0]) + abs(L[0][1] - LANDING[1]))
        for stand, face, onto in launches[:6]:
            steps = abs(stand[0] - LANDING[0]) + abs(stand[1] - LANDING[1])
            print(f"      stand {stand} face {face:<5} -> surf onto {onto}   ({steps} step(s) "
                  f"from the landing)")
    else:
        print("    ‼‼ NONE. If this prints, the landing is a hard strand and the chapter cannot")
        print("       end there at all — escalate before writing the exit leg.")
    print()

    print("6 — THE TRAP, STATED CORRECTLY")
    # ‼ THIS CHECK WAS WRONG ON ITS FIRST RUN AND IS CORRECTED IN PLACE (2026-08-13).
    # It used to ask "are there launch points NORTH of the landing?" and reported REFUTED because
    # 33 exist. That is TRUE and IRRELEVANT: the sandbar is a 71-tile atoll that wraps around, so
    # its northern tiles still touch the OPEN ocean on the flanks. The danger was never "north" as
    # a compass direction — it is surfing into the CLOSED LAGOON, which is a different component
    # regardless of where you stand. The old check measured a proxy for the hazard instead of the
    # hazard, which is this project's most-repeated mistake shape. What follows measures the trap.
    traps = []
    for xy in sorted(foot_set):
        x, y = xy
        for face, nxt in (("Up", (x, y - 1)), ("Down", (x, y + 1)),
                          ("Left", (x - 1, y)), ("Right", (x + 1, y))):
            if nxt in north_set:
                traps.append((xy, face, nxt))
    print(f"    TRAP launches — stand on the sandbar, surf into the CLOSED lagoon: {len(traps)}")
    for stand, face, onto in traps[:6]:
        print(f"      ⛔ stand {stand} face {face:<5} -> surf onto {onto}  (lagoon, "
              f"{len(north_set)} tiles, no exit)")
    from_landing = [L for L in traps if L[0] == LANDING]
    print(f"    ‼ TRAP launches FROM THE LANDING TILE ITSELF: {len(from_landing)}  "
          f"{from_landing if from_landing else '(none — the landing cannot surf at all)'}")
    print()

    print("=" * 100)
    print("VERDICT vs the pre-registered claim")
    print("=" * 100)
    checks = [
        ("landing is shallow/standable", landing is not None and landing.collision == 0),
        ("on-foot component does NOT reach the map edge", not foot_edge),
        ("north water and south water are DIFFERENT components", not same),
        ("south water reaches the map edge (open ocean)", south_edge),
        ("north water does NOT reach the map edge (closed lagoon)", not north_edge),
        ("at least one surf launch point onto the OPEN ocean exists", bool(launches)),
        ("the recommended escape (38,23)/Down/(38,24) is one of them",
         ((38, 23), "Down", (38, 24)) in launches),
        ("the landing tile itself CANNOT surf (all four neighbours are shallow)",
         not any(L[0] == LANDING for L in launches + traps)),
        ("a TRAP exists — the closed lagoon is surfable-into from the sandbar", bool(traps)),
    ]
    for label, ok in checks:
        print(f"  {'CONFIRMED' if ok else '‼ REFUTED  '}  {label}")
    print()
    print("‼ Read the REFUTED lines, if any, before writing §Ch20's exit leg. This probe measures")
    print("  the MAP only — it does not prove which way the cutscene leaves the player facing;")
    print("  that is still a decomp claim and wants a live check when the chapter is driven.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
