"""Verifies the cave entrance/exit tables against the ROM's own warp data.

WHY THIS EXISTS (#24-counters blocker #1, 2026-07-26). `_exit_training_cave_if_inside`
knew only GRANITE_CAVE. The global navigator cannot cross warp levels, so ANY target
outside a cave plan-fails from within it ("not on connected maps") — that stranding
dropped two real-HW runs to Manual on 2026-07-22. The two-way sweep
(`probe_counter_tiles.py --nav`) then showed FIERY_PATH (18,19) is reachable OUT from
Lavaridge but the RETURN leg failed *inside the cave*, so the tile could not be promoted
into `TRAINING_GRASS` until a second cave was supported.

‼ AND THESE ARE COORDINATES, WHICH MUST NEVER BE GUESSED. While writing the table I typed
Route 112's Fiery Path door as `(2, 30)` from memory. The ROM says **(11, 36)**. This test
exists so the next person cannot make that mistake silently: every tile in
`_CAVE_EXITS` / `_CAVE_ENTRANCES` is checked to be a REAL warp at that exact tile, leading
where the table claims, and the entrance/exit pair is checked to be the SAME physical
doorway (matching `destination_warp_id`), not two different mouths of the same cave.

Run: py -3.12 tools/story-dev/repro_cave_exit_table.py
"""

import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_REPO = _pl.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "sandbox-pokebot"))

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
context.emulator.load_save_state((_REPO / "tools/story-dev/saves/lavaridge.ss1").read_bytes())
for _ in range(20):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.story.early_game import _CAVE_ENTRANCES, _CAVE_EXITS

failures = []


def check(label, cond):
    print(f"    {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


def warps_of(map_enum):
    return {tuple(w.local_coordinates): w for w in get_map_data(map_enum.value, (0, 0)).warps}


def name_of(group, number):
    hit = [m.name for m in MapRSE if tuple(m.value) == (group, number)]
    return hit[0] if hit else f"({group},{number})"


print("=" * 78)
print("1) every _CAVE_EXITS tile is a REAL warp leading OUT of the cave")
print("=" * 78)
for cave_map, exit_tile in _CAVE_EXITS.items():
    w = warps_of(cave_map).get(tuple(exit_tile))
    if w is None:
        check(f"{cave_map.name} {tuple(exit_tile)} is a warp", False)
        continue
    dest = name_of(w.destination_map_group, w.destination_map_number)
    print(f"    {cave_map.name} {tuple(exit_tile)} -> {dest}")
    check(f"{cave_map.name} {tuple(exit_tile)} is a real warp", True)
    check(
        f"{cave_map.name} exit leaves the cave (dest {dest} is not another floor of it)",
        not dest.startswith(cave_map.name.split("_")[0] + "_") or "ROUTE" in dest,
    )

print()
print("=" * 78)
print("2) every _CAVE_ENTRANCES tile is a REAL warp leading INTO the cave")
print("=" * 78)
for cave_map, (outside_map, door_tile) in _CAVE_ENTRANCES.items():
    w = warps_of(outside_map).get(tuple(door_tile))
    if w is None:
        check(f"{outside_map.name} {tuple(door_tile)} is a warp", False)
        continue
    dest = name_of(w.destination_map_group, w.destination_map_number)
    print(f"    {outside_map.name} {tuple(door_tile)} -> {dest}")
    check(f"{outside_map.name} {tuple(door_tile)} is a real warp", True)
    check(f"{outside_map.name} {tuple(door_tile)} leads into {cave_map.name}", dest == cave_map.name)

print()
print("=" * 78)
print("3) the entrance and exit are the SAME doorway, not two mouths of one cave")
print("=" * 78)
# ‼ The real trap. Fiery Path has TWO warps to Route 112 — (26,36) south and (26,4)
# north. Entering by one and leaving by the other would surface the bot on the wrong side
# of the mountain, far from the Poké Center its heal targets. The ROM ties them together:
# the outside door's `destination_warp_id` indexes the cave's warp list, so it must point
# at the very tile we use as the exit.
for cave_map, (outside_map, door_tile) in _CAVE_ENTRANCES.items():
    exit_tile = _CAVE_EXITS.get(cave_map)
    if exit_tile is None:
        check(f"{cave_map.name} has an exit entry to pair with", False)
        continue
    door = warps_of(outside_map).get(tuple(door_tile))
    cave_warps = get_map_data(cave_map.value, (0, 0)).warps
    if door is None or door.destination_warp_id >= len(cave_warps):
        check(f"{cave_map.name} door resolves to a cave warp", False)
        continue
    landed = tuple(cave_warps[door.destination_warp_id].local_coordinates)
    print(f"    {outside_map.name} {tuple(door_tile)} lands on {cave_map.name} {landed}; "
          f"exit table uses {tuple(exit_tile)}")
    check(
        f"{cave_map.name}: entering by the door lands on the SAME tile we exit by",
        landed == tuple(exit_tile),
    )

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: both cave tables are ROM-verified, and each cave's entrance and exit are")
print("the same physical doorway — so a heal trip cannot surface on the wrong side.")
