"""mapdump — reusable map-recon tool for building the Story bot.

Dumps the GROUND TRUTH for any map straight from the ROM/emulator so we build
from facts instead of guessing coordinates (see PROJECT KNOWLEDGE/
12-STORYMODE-DESIGN.md §R "Recon Playbook", and ML-7/ML-8 for why this matters):

  * dimensions
  * map CONNECTIONS (direction / offset / destination map) — how routes join,
    and which intermediate maps are warp-split (invisible to connection routing)
  * WARPS (local coords -> destination group/number/warp-id) — doorways/caves
  * NPC object events (only if a save state on that map is loaded): coords,
    movement type + range (wanderer vs stationary) — the usual "silent blocker"
  * a COLLISION / tile-type grid ('.' walkable, '#' blocked, 'W' warp, 'P' player)

This is a DEV TOOL, not a bot feature — it is NOT promoted into custom-pokebot.

Usage (from sandbox-pokebot/):
    py -3.12 tools/mapdump.py <MAP_NAME> [--profile NAME] [--state PATH]
                               [--region rse|frlg] [--grid] [--no-grid]
Examples:
    py -3.12 tools/mapdump.py PETALBURG_CITY --profile story-b-test
    py -3.12 tools/mapdump.py PETALBURG_WOODS --state /tmp/woods_entered.ss1 \
        --profile story-b-test
Notes:
  * MAP_NAME is a MapRSE/MapFRLG enum name (e.g. ROUTE104, RUSTBORO_CITY).
  * --state loads a .ss1 save state first (needed for the NPC dump; the player
    should be ON the requested map for NPCs to be meaningful).
  * Without --state the static dump (dims/connections/warps/collision) still
    works — get_map_data reads any map by id.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _boot(profile_name: str, state_path: str | None):
    from modules.context import context
    from modules.game import set_rom
    from modules import profiles

    profile = profiles.load_profile_by_name(profile_name)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    context.video = False
    context.audio = False
    from modules.libmgba import LibmgbaEmulator

    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.emulation_speed = 0
    context.bot_mode = "Manual"
    if state_path:
        context.emulator.load_save_state(Path(state_path).read_bytes())
    context.emulator.run_single_frame()
    return context


def _resolve_map(name: str, region: str):
    from modules.map_data import MapRSE, MapFRLG

    enum = MapFRLG if region == "frlg" else MapRSE
    try:
        return enum[name.upper()]
    except KeyError:
        raise SystemExit(f"Unknown map '{name}' for region {region}. "
                         f"Use an exact enum name like ROUTE104 / RUSTBORO_CITY.")


def _map_of(dest) -> str:
    g = getattr(dest, "map_group", None)
    n = getattr(dest, "map_number", None)
    try:
        from modules.map_data import MapRSE
        return MapRSE((g, n)).name
    except Exception:
        return f"{g}/{n}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dump ground-truth map recon.")
    ap.add_argument("map", help="Map enum name, e.g. PETALBURG_CITY / ROUTE104")
    ap.add_argument("--profile", default="story-b-test", help="Profile to boot (for the ROM).")
    ap.add_argument("--state", default=None, help="Optional .ss1 save state to load first.")
    ap.add_argument("--region", default="rse", choices=("rse", "frlg"))
    ap.add_argument("--grid", dest="grid", action="store_true", default=True, help="Show collision grid (default).")
    ap.add_argument("--no-grid", dest="grid", action="store_false", help="Skip the collision grid.")
    args = ap.parse_args(argv)

    _boot(args.profile, args.state)
    from modules.map import get_map_data, get_map_data_for_current_position
    from modules.player import get_player_avatar

    M = _resolve_map(args.map, args.region)
    d = get_map_data(M, (0, 0))
    W, H = d.map_size
    print(f"=== {M.name}  group/number={M.value}  dims={W}x{H} ===")

    # --- connections ---
    print("-- connections --")
    conns = getattr(d, "connections", []) or []
    if not conns:
        print("  (none — this map is reached only by warps)")
    for c in conns:
        print(f"  {c.direction:6} offset={c.offset:<4} -> {_map_of(c.destination_map)}")

    # --- warps ---
    print("-- warps (local_coords -> dest group/number : warp_id) --")
    warps = getattr(d, "warps", []) or []
    warpset = set()
    for w in warps:
        wc = w.local_coordinates
        warpset.add(tuple(wc))
        dg = getattr(w, "destination_map_group", None)
        dn = getattr(w, "destination_map_number", None)
        wid = getattr(w, "destination_warp_id", None)
        try:
            from modules.map_data import MapRSE
            dname = MapRSE((dg, dn)).name
        except Exception:
            dname = f"{dg}/{dn}"
        print(f"  {str(tuple(wc)):8} -> {dname} : warp {wid}")

    # --- NPCs (need player on this map) ---
    player_xy = None
    if args.state:
        try:
            cur = get_map_data_for_current_position()
            if (cur.map_group, cur.map_number) == M.value:
                player_xy = tuple(get_player_avatar().local_coordinates)
            print("-- NPC object events (current position on this map) --")
            from modules.map import get_map_objects

            for o in get_map_objects():
                if getattr(o, "movement_type", "") == "Player":
                    continue
                print(f"  id={o.local_id} at={o.current_coords} init={o.initial_coords} "
                      f"facing={o.facing_direction} move={o.movement_type} "
                      f"range=({o.range_x},{o.range_y}) gfx={o.graphics_id}")
        except Exception as e:  # noqa: BLE001
            print(f"  (NPC dump unavailable: {e!r})")

    # --- collision / tile-type grid ---
    if args.grid:
        print("-- collision grid  ('.'=walk 0  '#'=blocked  'W'=warp  'P'=player) --")
        print("    " + "".join(str(x % 10) for x in range(W)))
        for y in range(H):
            row = []
            for x in range(W):
                if player_xy == (x, y):
                    row.append("P")
                    continue
                t = get_map_data(M, (x, y))
                if (x, y) in warpset:
                    row.append("W")
                elif t.collision == 0:
                    row.append(".")
                else:
                    row.append("#")
            print(f"{y:3} " + "".join(row))

    return 0


if __name__ == "__main__":
    sys.exit(main())
