"""Blocker #1 of §CC2: counter maps have NO verified spin tile, so phase 2 has nothing
to path to. This probe answers, from the REAL pre-Norman anchor, whether a usable tile
exists on each Fighting-counter map — and therefore whether phase 2 can pay for itself.

ANCHOR (`--anchor`, default `lavaridge`): a PRE-Norman save, i.e. the moment the counter
plan actually fires — the honest starting position (prevention rule, 08-MISTAKES
2026-07-22: never adopt a training tile without proving it FROM THE REAL ENTRY POINT;
same-map connectivity does not imply the story can get there).

‼ THE ANCHOR MUST LOAD IN A CLEAN OVERWORLD. `prenorman_fodder_grind.ss1` was the obvious
choice (captured at the exact pre-Norman grind) but it loads **inside a wild battle**
(`game_state=4`, `battle_is_active=True`), and every navigation leg then dies identically
with "stayed out of the overworld for too long (possible softlock)" — which reads like
four separate map failures and is really one harness bug. `normalize_to_overworld()` does
NOT rescue it either: it B-presses out of menus/dialogues, but a live wild battle can only
be resolved by fleeing or fighting, which needs the battle LISTENER this probe does not
run. Verified clean and pre-Norman (state=7, battle=False, BADGE05 unset):
`lavaridge` (Lavaridge Town, avg L26), `flannery_done`, `fallarbor`, `rocksmash_taught`.

‼ FIERY_PATH and GRANITE_CAVE are CAVES. Their encounters come from the cave FLOOR, not
from `MB_TALL_GRASS`, so `jaggedgrass_probe.py`'s tall-grass enumeration finds zero tiles
on them. Here a candidate is a walkable floor tile away from the warps.

Reported in three stages, cheapest first, so an early NO costs nothing:
  1. REGION reachability + hop count for each counter map (`region_reach`, no emulation).
  2. Candidate floor tiles per map (static ROM read, no emulation).
  3. Two-way navigation for the best candidate: anchor -> tile AND tile -> anchor. Only
     run when stages 1-2 pass, because a cross-region trek is expensive to simulate.

Run: py -3.12 tools/story-dev/probe_counter_tiles.py [--nav]
     (--nav enables stage 3; it is slow and off by default)
"""

import argparse
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
ap.add_argument("--nav", action="store_true", help="run the expensive stage-3 navigation test")
ap.add_argument("--frames", type=int, default=60000, help="frame budget per navigation leg")
ap.add_argument("--anchor", default="lavaridge",
                help="save basename in saves/ to start from (must load in a CLEAN overworld)")
args = ap.parse_args()

_REPO = _pl.Path(__file__).resolve().parents[2]
_SANDBOX = str(_REPO / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0

SAVE = (_SAVES / f"{args.anchor}.ss1").read_bytes()
context.emulator.load_save_state(SAVE)
for _ in range(30):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.story import region_reach

pa = get_player_avatar()
levels = [m.level for m in get_party() if m is not None]
print("=" * 78)
print("ANCHOR — where the bot actually stands when the counter plan fires")
print("=" * 78)
print(f"  map={pa.map_group_and_number} local={tuple(pa.local_coordinates)}")
print(f"  party levels={levels} avg={sum(levels)/len(levels):.1f}")

# Fighting-counter maps named by counter_plan, plus the already-pending Granite Cave.
COUNTER_MAPS = [
    MapRSE.FIERY_PATH,
    MapRSE.JAGGED_PASS,
    MapRSE.GRANITE_CAVE_1F,
    MapRSE.GRANITE_CAVE_B1F,
]

print()
print("=" * 78)
print("STAGE 1 — region reachability from the anchor (no emulation)")
print("=" * 78)
stage1 = {}
for m in COUNTER_MAPS:
    try:
        ok = region_reach.is_map_reachable(m)
        hops = region_reach.hops_to(m)
        why = region_reach.why_unreachable(m)
    except Exception as e:
        ok, hops, why = False, None, f"<probe error {type(e).__name__}: {e}>"
    stage1[m] = ok
    print(f"  {m.name:22s} reachable={str(ok):5s} hops={hops}  {why}")

print()
print("=" * 78)
print("STAGE 2 — candidate floor tiles (static ROM read, caves have no tall grass)")
print("=" * 78)


def walkable_floor_tiles(map_enum, limit=None):
    """Walkable, non-warp tiles. For a cave every such tile rolls encounters, so any of
    them is a valid spin tile — unlike a route, where only MB_TALL_GRASS does."""
    gnum = map_enum.value
    md = get_map_data(gnum, (0, 0))
    w, h = md.map_size
    warps = set()
    try:
        for wp in md.warps:
            warps.add(tuple(wp.local_coordinates))
    except Exception:
        pass
    out = []
    for y in range(h):
        for x in range(w):
            try:
                t = get_map_data(gnum, (x, y))
            except Exception:
                continue
            if t.collision:
                continue
            if (x, y) in warps:
                continue
            out.append((x, y))
            if limit and len(out) >= limit:
                return out, (w, h), warps
    return out, (w, h), warps


stage2 = {}
for m in COUNTER_MAPS:
    try:
        tiles, size, warps = walkable_floor_tiles(m)
    except Exception as e:
        print(f"  {m.name:22s} <read failed: {type(e).__name__}: {e}>")
        continue
    stage2[m] = tiles
    if not tiles:
        print(f"  {m.name:22s} {size}  NO walkable non-warp tiles found")
        continue
    # Prefer a tile in the middle of the walkable mass — away from warps and edges, so a
    # spin has room and cannot accidentally step through a door.
    cx = sum(t[0] for t in tiles) / len(tiles)
    cy = sum(t[1] for t in tiles) / len(tiles)
    central = sorted(tiles, key=lambda t: abs(t[0] - cx) + abs(t[1] - cy))[:5]
    print(f"  {m.name:22s} {size}  walkable={len(tiles):4d}  warps={len(warps)}")
    print(f"      most-central candidates: {central}")

print()
print("=" * 78)
print("VERDICT")
print("=" * 78)
usable = [m for m in COUNTER_MAPS if stage1.get(m) and stage2.get(m)]
for m in COUNTER_MAPS:
    reach = "reachable" if stage1.get(m) else "UNREACHABLE"
    tiles = len(stage2.get(m, []))
    verdict = "candidate" if (stage1.get(m) and tiles) else "no"
    print(f"  {m.name:22s} {reach:12s} tiles={tiles:4d}  -> {verdict}")
print()
if usable:
    print(f"  {len(usable)} counter map(s) are both reachable AND have floor tiles:")
    print(f"    {[m.name for m in usable]}")
    print("  Next: promote a central tile into TRAINING_GRASS after the stage-3 two-way")
    print("  navigation passes (rerun with --nav).")
else:
    print("  NO counter map is both reachable and tiled from this anchor.")
    print("  Phase 2 cannot be built against this candidate list — widen reachability first.")

if not args.nav:
    print()
    print("(stage 3 navigation skipped — pass --nav to run it)")
    raise SystemExit(0)

print()
print("=" * 78)
print("STAGE 3 — two-way navigation from the anchor (expensive)")
print("=" * 78)
from modules.modes import BotModeError
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.story.early_game import normalize_to_overworld


def step(gen, n):
    for _ in range(n):
        try:
            next(gen)
        except StopIteration:
            return True
        context.emulator.run_single_frame()
    return False


def reset():
    """Load the anchor AND get to a clean controllable overworld first.

    ‼ `prenorman_fodder_grind.ss1` was captured MID-GRIND and loads **inside a wild
    battle** (`game_state=4`, `battle_is_active=True`). Without this the navigator has no
    overworld to work from and every leg dies identically with "stayed out of the
    overworld for too long (possible softlock)" — which reads like four separate map
    failures and is really one harness bug. Same class as the 2026-07-22
    checkpoint-saved-mid-dialogue lesson: a save is not a starting position until it is
    normalised.
    """
    context.emulator.load_save_state(SAVE)
    for _ in range(30):
        context.emulator.run_single_frame()
    step(normalize_to_overworld(), 6000)


anchor_map = tuple(pa.map_group_and_number)
anchor_tile = tuple(pa.local_coordinates)
anchor_enum = next((m for m in MapRSE if tuple(m.value) == anchor_map), None)

for m in usable:
    tiles = stage2[m]
    cx = sum(t[0] for t in tiles) / len(tiles)
    cy = sum(t[1] for t in tiles) / len(tiles)
    target = sorted(tiles, key=lambda t: abs(t[0] - cx) + abs(t[1] - cy))[0]
    reset()
    print(f"  {m.name} -> {target}")
    try:
        ok_out = step(navigate_to_anywhere(m, target, avoid_encounters=True), args.frames)
    except BotModeError as e:
        print(f"    OUT  FAIL  {str(e)[:110]}")
        continue
    except Exception as e:
        print(f"    OUT  ERR   {type(e).__name__}: {str(e)[:90]}")
        continue
    now = get_player_avatar()
    if not ok_out or tuple(now.local_coordinates) != target or tuple(now.map_group_and_number) != tuple(m.value):
        print(f"    OUT  TIMEOUT/WRONG  ended {now.map_group_and_number} {tuple(now.local_coordinates)}")
        continue
    print(f"    OUT  OK")
    if anchor_enum is None:
        print("    BACK skipped (anchor map not in MapRSE)")
        continue
    try:
        ok_back = step(navigate_to_anywhere(anchor_enum, anchor_tile, avoid_encounters=True), args.frames)
    except Exception as e:
        print(f"    BACK FAIL  {type(e).__name__}: {str(e)[:90]}")
        continue
    now = get_player_avatar()
    print(f"    BACK {'OK' if ok_back and tuple(now.map_group_and_number) == anchor_map else 'FAIL'}"
          f"  (ended {now.map_group_and_number} {tuple(now.local_coordinates)})")
