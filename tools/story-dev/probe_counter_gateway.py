"""Can a two-stage APPROACH GATEWAY reach a counter tile that direct navigation cannot?

WHY THIS EXISTS. `probe_counter_reachability.py` found Wattson's ROUTE111 (25,55) and
Winona's ROUTE118 (29,15) "unreachable" — but that word was too strong. Traced
2026-07-30: `navigate_to_anywhere` branches on REGION, where a region is the set of maps
joined by direct N/S/E/W connections (`warp_graph.py`). Mauville and Route 111 are
edge-connected, so they are the SAME region, so the bot tries to WALK straight there,
`calculate_path` hits the Go-Goggles desert that splits Route 111 in two, and it gives up —
**it never considers a warp-assisted detour, because it already decided no warps were
needed.** The route plainly exists (Mauville -> Route 112 -> Fiery Path -> Lavaridge ->
Route 113 -> Fallarbor -> Route 114 -> Route 111 north), and `training_areas.TRAINING_GRASS`
already records "reachable from Fallarbor, NOT from Mauville" (verified 2026-07-24).

THE IDEA UNDER TEST. When the direct leg fails, navigate to a GATEWAY first — a map/tile on
the far side, which the warp planner CAN reach because it is a different region — then walk
the last leg from there. Poké Center doors make natural gateways: they are map+tile pairs
the heal trips already navigate to successfully, so they are pre-proven waypoints.

‼ THIS PROBE DECIDES WHAT GETS ENCODED. Only a gateway whose BOTH legs pass here is written
into `training_areas.APPROACH_GATEWAYS`. A guessed gateway would be a wrong "yes" that costs
a long walk to nowhere — exactly the KI-24b class this project keeps paying for.

Run: py -3.12 tools/story-dev/probe_counter_gateway.py
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
context.bot_mode = "Story"

import modules.story.early_game as eg
from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE, PokemonCenter
from modules.memory import get_game_state
from modules.player import get_player_avatar, player_avatar_is_controllable

SAVES = REPO / "tools" / "story-dev" / "saves"
NAV_CAP = 200_000

# (label, save, target map+tile, [gateway candidates, in order of preference])
CASES = [
    (
        "WATTSON — Sandshrew @ ROUTE111 (25,55)",
        "rocksmash_taught.ss1",
        (MapRSE.ROUTE111, (25, 55)),
        # ‼ A GATEWAY MUST BE IN A DIFFERENT REGION. First attempt used Poké Centres
        # (Fallarbor, Lavaridge) and every leg failed in 255 frames — because those towns
        # are edge-connected to Mauville, i.e. the SAME region, so `navigate_to_anywhere`
        # took its same-region branch and hit the very desert we were trying to route
        # around. FIERY_PATH is a cave, reached through warps, so it is a different region
        # and the warp planner actually engages.
        [("Fiery Path", (MapRSE.FIERY_PATH, (18, 19)))],
    ),
    (
        "WINONA — Electrike @ ROUTE118 (29,15)",
        # ‼ NOT devon_scope_got.ss1: it sits at ROUTE120 (13,16), the documented
        # north-bridge strand where Steven's scene isolates the avatar and only
        # `_leave_route120_north_bridge`'s held walk escapes. A nav failure from there
        # says nothing about Route 118.
        "ch13_fortree_door.ss1",
        (MapRSE.ROUTE118, (29, 15)),
        [("Fiery Path", (MapRSE.FIERY_PATH, (18, 19))),
         ("Mauville PC", PokemonCenter.MauvilleCity.value)],
    ),
]



def load(save_name):
    context.emulator.load_save_state((SAVES / save_name).read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    avatar = get_player_avatar()
    return (
        tuple(avatar.map_group_and_number),
        tuple(avatar.local_coordinates),
        get_game_state().name,
        player_avatar_is_controllable(),
        getattr(get_map_data_for_current_position(), "map_name", "?"),
    )


def drive_nav(dest_map, dest_tile):
    """Run the REAL executor navigation. -> (ok, frames, detail)."""
    frames = 0
    try:
        generator = eg._navigate_riding_out(dest_map, dest_tile, avoid_encounters=True)
        while frames < NAV_CAP:
            next(generator)
            context.emulator.run_single_frame()
            frames += 1
        return False, frames, "CAP HIT"
    except StopIteration:
        try:
            here = tuple(get_player_avatar().map_group_and_number)
            arrived = here == tuple(dest_map.value)
        except Exception:
            arrived = False
        return arrived, frames, "arrived" if arrived else "returned but not on the map"
    except Exception as error:
        return False, frames, f"{type(error).__name__}: {str(error)[:130]}"


results = []
for label, save_name, (target_map, target_tile), gateways in CASES:
    print("=" * 78)
    print(f"{label}   (save: {save_name})")
    print("=" * 78)
    here = load(save_name)
    print(f"  anchor: {here[4]} {here[1]}  state={here[2]} controllable={here[3]}")
    if here[2] != "OVERWORLD" or not here[3]:
        print("  SKIP — not a clean controllable overworld")
        results.append((label, "SKIPPED", ""))
        print()
        continue

    ok, frames, detail = drive_nav(target_map, target_tile)
    print(f"  DIRECT  -> {'OK' if ok else 'FAIL'} in {frames} frames — {detail}")
    if ok:
        results.append((label, "DIRECT WORKS", f"{frames} frames"))
        print()
        continue

    winner = None
    for gw_label, (gw_map, gw_tile) in gateways:
        load(save_name)  # always retry from the SAME anchor, never a half-moved state
        ok1, f1, d1 = drive_nav(gw_map, tuple(gw_tile))
        print(f"  via {gw_label}: leg 1 (anchor -> gateway) {'OK' if ok1 else 'FAIL'} "
              f"in {f1} frames — {d1}")
        if not ok1:
            continue
        ok2, f2, d2 = drive_nav(target_map, target_tile)
        print(f"  via {gw_label}: leg 2 (gateway -> target) {'OK' if ok2 else 'FAIL'} "
              f"in {f2} frames — {d2}")
        if ok2:
            winner = (gw_label, gw_map, tuple(gw_tile), f1 + f2)
            break
    results.append(
        (label, f"GATEWAY: {winner[0]}" if winner else "NO GATEWAY WORKED",
         f"{winner[1].name} {winner[2]}, {winner[3]} frames total" if winner else "")
    )
    print()

print("=" * 78)
print("VERDICT — only a gateway with BOTH legs green may be encoded")
print("=" * 78)
for label, verdict, detail in results:
    print(f"  {label:<44} {verdict}")
    if detail:
        print(f"      {detail}")
print()
print("Encode the winners into training_areas.APPROACH_GATEWAYS with this evidence.")
print("A gateway that failed here must NOT be guessed into the table.")
