#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the route the bot's OWN planner would take between two tiles — no story run.

⛔ WHY THIS EXISTS. Two routing detours were reported (the Littleroot running-shoes leg and a
Rustboro leg that swings through a fenced area). Diagnosing a route by reading story code is
guesswork, and reproducing one by driving the whole story costs ~100k frames per attempt. This asks
`calculate_path` — **the planner production actually uses** — and prints every waypoint.

‼ IT IS ALSO THE FIX-VERIFICATION INSTRUMENT, and that is the harder half. `--avoid` names a
rectangle the route must NOT enter; it exits 1 if the route enters it. ⭐ That reading cannot be
satisfied by a no-op: if nothing changed, the route still enters the box and the check still fails.
A "the detour is gone" claim backed by anything weaker is not evidence.

⚠ WHAT IT DOES AND DOES NOT MODEL. `calculate_path` sees the map as the bot sees it, INCLUDING the
live NPC positions in the loaded save (`get_map_objects` is camera-ranged, so NPCs far away are not
modelled). ⇒ a route dumped from one fixture is evidence about THAT story state. Dump from the
fixture whose era matches the leg you are fixing, and say which one in any claim you make.
⛔ KI-74 is still OPEN: `setmetatile` tiles are invisible to the shared map model, so the planner can
believe a tile walkable that the game refuses. A dumped route is what the PLANNER intends, which is
exactly the right question for a DETOUR (the planner is choosing the long way) and the wrong one for
a JAM (the planner is choosing an illegal way).

Usage:
    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 probe_path_dump.py --save rustboro.ss1 --map RUSTBORO_CITY --to 16,53
    PYTHONUTF8=1 py -3.12 probe_path_dump.py --save rustboro.ss1 --map RUSTBORO_CITY \\
        --from 16,20 --to 16,53 --avoid 20,30,28,40
Exit 0 if a route exists and (when --avoid is given) stays out of the box; 1 otherwise.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context                                  # noqa: E402
from modules.game import set_rom                                     # noqa: E402
from modules.profiles import load_profile_by_name                    # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--save", default="rustboro.ss1", help="fixture under saves/")
    ap.add_argument("--map", dest="map_name", required=True, help="MapRSE name, e.g. RUSTBORO_CITY")
    ap.add_argument("--from", dest="src", default="", help="X,Y (default: the player's tile)")
    ap.add_argument("--to", dest="dst", required=True, help="X,Y")
    ap.add_argument("--avoid", default="", help="x1,y1,x2,y2 — the route must NOT enter this box")
    ap.add_argument("--through-grass", action="store_true",
                    help="set avoid_encounters=False (the A/B arm for a suspected grass detour)")
    ap.add_argument("--through-scripts", action="store_true",
                    help="set avoid_scripted_events=False — the A/B arm for a TRIGGER detour. "
                         "map_path.py:1034-1037 charges +10000 per ARMED coord-event tile against a "
                         "base step cost of 1, so one armed tile can buy 10,000 steps of detour.")
    ap.add_argument("--profile", default="repro-ml")
    args = ap.parse_args()

    profile = load_profile_by_name(args.profile)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)

    from modules.libmgba import LibmgbaEmulator

    context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)
    context.audio = False
    context.video = False
    # ⛔ THE THIRD LINE OF THE TRIPLE (gate #54). Without it this probe paces itself to 60fps by
    # BLOCKING on an audio write every frame — `audio = False` only silences the samples.
    context.emulation_speed = 0

    from modules.map_data import MapRSE
    from modules.map_path import PathFindingError, calculate_path
    from modules.player import get_player_avatar

    save = REPO / "tools" / "story-dev" / "saves" / args.save
    if not save.exists():
        print(f"  ⛔ no such fixture: {save}")
        return 2
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(4):
        context.emulator.run_single_frame()

    try:
        map_enum = getattr(MapRSE, args.map_name)
    except AttributeError:
        print(f"  ⛔ unknown map: {args.map_name}")
        return 2

    avatar = get_player_avatar()
    here = tuple(avatar.local_coordinates)
    live_map = avatar.map_group_and_number

    src = here if not args.src else tuple(int(v) for v in args.src.split(","))
    dst = tuple(int(v) for v in args.dst.split(","))

    print("=" * 96)
    print("PATH DUMP — what the bot's OWN planner intends")
    print("=" * 96)
    print(f"  fixture   : {args.save}")
    print(f"  player is : {live_map} at {here}")
    print(f"  map       : {args.map_name}")
    print(f"  from -> to: {src} -> {dst}")
    if tuple(src) != here:
        # ⛔ KI-60: `calculate_path` never validates its SOURCE tile, so a bogus --from yields a
        # confident answer about a position the player is not in. Say it out loud.
        print("  ⚠ --from differs from the player's ACTUAL tile. KI-60: the planner does NOT")
        print("     validate its source, so this answer describes a hypothetical, not this save.")
    print()

    # ⭐⭐ `avoid_encounters` DEFAULTS TO TRUE (`map_path.py:723`), and that is the single most
    # likely innocent explanation for a "why did it go the long way?" report: avoiding encounters
    # means avoiding GRASS, so the planner will happily walk a longer grass-free route. Exposing it
    # makes the A/B one command instead of a guess.
    try:
        path = calculate_path((map_enum, src), (map_enum, dst),
                              avoid_encounters=not args.through_grass,
                              avoid_scripted_events=not args.through_scripts)
    except PathFindingError as error:
        print(f"  ⛔ NO ROUTE: {error}")
        print("=" * 96)
        return 1

    # `Waypoint` is a dataclass (map_path.py:702): direction, map, coordinates, is_warp, ...
    print(f"  route: {len(path)} waypoint(s)")
    for i, wp in enumerate(path):
        tag = ""
        if i == 0:
            tag = "  <- start"
        elif i == len(path) - 1:
            tag = "  <- goal"
        extra = []
        if wp.is_warp:
            extra.append("WARP")
        if wp.is_water_tile:
            extra.append("water")
        if wp.action is not None:
            extra.append(str(wp.action))
        note = ("  [" + ", ".join(extra) + "]") if extra else ""
        print(f"    {i:>3}: map{wp.map} {tuple(wp.coordinates)} {wp.direction.name}{note}{tag}")

    rc = 0
    if args.avoid:
        x1, y1, x2, y2 = (int(v) for v in args.avoid.split(","))
        lo_x, hi_x = min(x1, x2), max(x1, x2)
        lo_y, hi_y = min(y1, y2), max(y1, y2)
        inside = [tuple(wp.coordinates) for wp in path
                  if lo_x <= wp.coordinates[0] <= hi_x and lo_y <= wp.coordinates[1] <= hi_y]
        print()
        print(f"  --avoid box x{lo_x}..{hi_x}, y{lo_y}..{hi_y}")
        if inside:
            print(f"  ❌ THE ROUTE ENTERS THE BOX at {len(inside)} waypoint(s): {inside[:10]}")
            print("     ⇒ the detour is REPRODUCED. This is the reading a fix must flip.")
            rc = 1
        else:
            print("  ✅ the route stays OUT of the box.")
            print("     ‼ On its own this proves the box is avoided, NOT that the route is sensible —")
            print("       check the waypoint count above against the straight-line distance too.")
    print("=" * 96)
    return rc


if __name__ == "__main__":
    sys.exit(main())
