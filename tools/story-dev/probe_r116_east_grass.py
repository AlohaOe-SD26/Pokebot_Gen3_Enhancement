"""`#24-r116sweep` follow-up: is ANY Route 116 grass reachable from the side Wattson's hunt
arrives on?

WHAT THE SWEEP ACTUALLY MEASURED (2026-08-09, from `saves/mauville_prewattson.ss1`,
badge03=False). The journey **succeeded**: the bot walked Mauville -> ROUTE116 and stood on
the map at **(65, 11)** after ~32,000 frames. What failed was the last, intra-map leg:

    Could not find a path from (65/11 @ ROUTE116) to (11/7 @ ROUTE116)

‼ That is not the same finding as "Route 116 is unreachable", and the difference decides
whether Wattson has a legal counter at all. `(11, 7)` is `RUSTBORO_TRAINING_GRASS` — a tile
chosen for the **pre-Roxanne** era, when the route is entered from the WEST (Rustboro). The
counter hunt arrives from the **EAST** (Mauville -> Verdanturf -> Rusturf Tunnel). So the
verdict on the table is "that TILE does not work from that side", and the open question is
whether a tile on the arrival side would.

WHAT THIS PROBE DOES — statically, no emulation loop, seconds not frames:
  1. enumerates every ROUTE116 tile the ROM marks `has_encounters` (i.e. real grass),
  2. asks `calculate_path` whether each is reachable FROM THE ARRIVAL TILE (65, 11),
  3. prints the reachable ones nearest the arrival point — the candidates a sweep should test.

‼ POSITIVE CONTROL, twice over, because a probe that finds nothing is indistinguishable from
a probe that cannot see:
  * the grass scan must find `(11, 7)` — a tile the project already uses as Route 116 grass
    and which a save (`route116team.ss1`) stands on;
  * `calculate_path` must succeed for a trivially adjacent target, proving the planner is
    answering at all from the arrival tile.
If either control fails the result is reported as UNTRUSTED rather than as an answer.

‼ AND READ THE RESULT NARROWLY. `calculate_path` reachable is evidence a sweep is WORTH
running; it is NOT the standard. `HUNTING_GROUNDS` entry requires DRIVEN reach-and-leave
(`--driver groundsweep`) — that rule is what took counter conversion 15% -> 50% (z = +2.73),
and a static YES has already nearly retired a working feature once (08-MISTAKES 2026-07-30).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r116_east_grass.py
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path

ROUTE = MapRSE.ROUTE116
ARRIVAL = (65, 11)          # measured: where the driven journey from Mauville actually lands
RUSTBORO_TILE = (11, 7)     # the tile currently in TRAINING_GRASS, and the sweep's target
WIDTH, HEIGHT = 80, 40      # scanned generously; out-of-bounds tiles simply raise and are skipped


def grass_tiles() -> list[tuple[int, int]]:
    found = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            try:
                tile = get_map_data(ROUTE, (x, y))
                if tile is not None and tile.has_encounters and tile.collision == 0:
                    found.append((x, y))
            except Exception:
                continue
    return found


def reachable(src: tuple[int, int], dst: tuple[int, int]) -> tuple[bool, str]:
    try:
        path = calculate_path((ROUTE, src), (ROUTE, dst), avoid_encounters=False, avoid_scripted_events=False)
        return True, f"{len(path)} waypoints"
    except PathFindingError as error:
        return False, str(error)[:110]
    except Exception as error:
        return False, f"{type(error).__name__}: {str(error)[:90]}"


def main() -> int:
    print("=" * 86)
    print(f"ROUTE116 grass scan — arrival tile {ARRIVAL} (measured), Rustboro tile {RUSTBORO_TILE}")
    print("=" * 86)

    tiles = grass_tiles()
    print(f"  grass tiles with encounters: {len(tiles)}")

    # ---- CONTROL 1: the scan must see a tile we already know is grass ----
    control_scan = RUSTBORO_TILE in tiles
    print(f"  CONTROL 1 (scan sees {RUSTBORO_TILE}): {'PASS' if control_scan else 'FAIL'}")

    # ---- CONTROL 2: the planner must answer at all from the arrival tile ----
    ok_self, why_self = reachable(ARRIVAL, (ARRIVAL[0], ARRIVAL[1] + 1))
    print(f"  CONTROL 2 (planner answers from {ARRIVAL}): {'PASS' if ok_self else 'FAIL'} — {why_self}")

    if not (control_scan and ok_self):
        print("\n‼ CONTROLS FAILED — treat everything below as UNTRUSTED.")

    # ---- the question ----
    ok_rustboro, why_rustboro = reachable(ARRIVAL, RUSTBORO_TILE)
    print(f"\n  {ARRIVAL} -> {RUSTBORO_TILE} (the swept tile): "
          f"{'reachable' if ok_rustboro else 'NOT reachable'} — {why_rustboro}")

    # ---- ‼ DISCRIMINATOR: is the ARRIVAL TILE a pocket, or is the grass the problem? ----
    # "0 of 138 unreachable" is a uniform FAIL, and this project's own rule (08-MISTAKES
    # 2026-07-31) is that a probe failing every case has found a SYMPTOM, not a cause. Two very
    # different worlds produce that number: (a) the route's grass genuinely sits behind a
    # barrier from the east, or (b) the bot arrived in a small enclosed pocket and can barely
    # move at all — in which case the finding is about the ARRIVAL, not about the grass.
    # Measuring the size and shape of the reachable region separates them.
    walkable, reach = [], []
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            try:
                tile = get_map_data(ROUTE, (x, y))
                if tile is None or tile.collision != 0:
                    continue
            except Exception:
                continue
            walkable.append((x, y))
            if reachable(ARRIVAL, (x, y))[0]:
                reach.append((x, y))
    if reach:
        xs, ys = [p[0] for p in reach], [p[1] for p in reach]
        box = f"x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}"
    else:
        box = "empty"
    print(f"\n  REGION CHECK (every 2nd tile): {len(reach)} of {len(walkable)} walkable tiles "
          f"reachable from {ARRIVAL}; bounding box: {box}")
    if len(reach) <= max(3, len(walkable) // 20):
        print("  ‼ The arrival tile can barely move — read this as a finding about the ARRIVAL,")
        print("    not as proof that Route 116's grass is walled off from the east.")

    # ---- ‼ THE SECOND DISCRIMINATOR: is it the ROUTE, or the ENTRANCE the journey picked? ----
    # Same scan from the WEST-side tile. If the west region holds the grass the east pocket
    # lacks, then Route 116's grass is not "unreachable" in any absolute sense — the journey
    # simply arrives at an entrance from which the destination tile cannot be walked to, and
    # the tile leg then fails with no attempt at another entrance. Those two findings imply
    # completely different work, so the probe must not report one when it measured the other.
    west_reach = [p for p in walkable if reachable(RUSTBORO_TILE, p)[0]]
    west_grass = [t for t in tiles if reachable(RUSTBORO_TILE, t)[0]]
    print(f"  WEST COMPARISON from {RUSTBORO_TILE}: {len(west_reach)} of {len(walkable)} walkable "
          f"tiles, and {len(west_grass)} of {len(tiles)} grass tiles, are reachable")

    hits = []
    for tile in tiles:
        ok, why = reachable(ARRIVAL, tile)
        if ok:
            hits.append((abs(tile[0] - ARRIVAL[0]) + abs(tile[1] - ARRIVAL[1]), tile, why))
    hits.sort()

    print(f"\n  grass tiles REACHABLE from {ARRIVAL}: {len(hits)} of {len(tiles)}")
    for distance, tile, why in hits[:12]:
        print(f"    {tile}   manhattan={distance:<4} {why}")
    if not hits:
        print("    NONE — no Route 116 grass can be walked to from the side the hunt arrives on.")
        print("    ⇒ Wattson's only legal pre-badge counter (Nincada @ ROUTE116) is not huntable,")
        print("      and the honest answer is that he must be beaten by levels/lead, not a hunt.")
    else:
        best = hits[0][1]
        print(f"\n  ⇒ NEXT: earn the entry the same way it is required of every ground —")
        print(f"    SWEEP_GROUND=ROUTE116:{best[0]},{best[1]} SWEEP_RETURN=MAUVILLE_CITY:19,15 \\")
        print(f"      py -3.12 story_harness.py mauville_prewattson.ss1 --driver groundsweep --frames 900000")
        print("    ‼ A static YES is not the standard: DRIVEN reach-and-leave is.")
    return 0 if (control_scan and ok_self) else 1


if __name__ == "__main__":
    raise SystemExit(main())
