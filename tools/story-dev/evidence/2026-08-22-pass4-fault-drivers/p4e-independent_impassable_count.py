"""P4e AUDIT (independent re-derivation): counts `Impassable *` / live tiles across all 518
MapRSE maps WITHOUT calling modules.map.get_map_all_tiles / modules.map.get_map_data /
modules.map_path._get_map_metadata (the helpers the shipped repro/probe scripts call).

This script does its OWN pointer-chase over raw emulator memory (gMapGroups -> map header ->
map layout -> block data -> tileset attribute table), independently re-implemented from the
decomp field offsets, to cross-check the previously reported headline figures
(2,658 total / 2,257 dormant / 401 live; tombs 144, Shoal Cave 98, Victory Road 58).

The ONLY project code reused is:
  * `modules.map._get_tile_type_name` -- a static lookup table from behaviour-byte -> name
    string. This is decomp CONSTANT DATA, not pathfinding logic, and is not part of the KI-59
    inversion bug (that bug lives entirely in modules/map_path.py, never touched here).
  * `modules.map_data.MapRSE` / `MapGroupRSE` -- enum DATA (map group/number table), not logic.
"""
import pathlib
import struct
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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

assert context.rom.is_emerald, f"expected Emerald, got {context.rom}"

from modules.memory import read_symbol
from modules.map import _get_tile_type_name  # static decomp lookup table only
from modules.map_data import MapGroupRSE, MapRSE

rd = context.emulator.read_bytes


def u16(b, o=0):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o=0):
    return struct.unpack_from("<I", b, o)[0]


# ---- MY OWN header enumeration (independent of modules.map.get_map_data's cache-builder) ----
n_groups = len(MapGroupRSE)
map_group_ptrs = read_symbol("gMapGroups", size=4 * n_groups)
headers: dict[tuple[int, int], bytes] = {}
for g in range(n_groups):
    n_maps = len(MapGroupRSE(g).maps)
    group_ptr = u32(map_group_ptrs, g * 4)
    group_table = rd(group_ptr, 4 * n_maps)
    for m in range(n_maps):
        hp = u32(group_table, m * 4)
        headers[(g, m)] = rd(hp, 0x1C)
print(f"[independent] enumerated {len(headers)} map headers ({n_groups} groups) -- MapRSE has {len(list(MapRSE))}")

layout_cache: dict[tuple[int, int], bytes] = {}


def get_layout(g, m):
    key = (g, m)
    if key not in layout_cache:
        layout_ptr = u32(headers[key], 0)
        layout_cache[key] = rd(layout_ptr, 24)
    return layout_cache[key]


def tile_attr_and_collision(g, m, x, y):
    layout = get_layout(g, m)
    data_ptr = u32(layout, 12)
    width = u32(layout, 0)
    offset = (x * 2) + (width * y * 2)
    block = u16(rd(data_ptr + offset, 2))
    metatile = block & 0x3FF
    collision = (block & 0x0C00) >> 10
    PRIMARY_N, ATTR_SIZE, ATTR_OFF, SECONDARY_N = 512, 2, 0x10, 1024
    if metatile < PRIMARY_N:
        tileset_ptr = u32(layout, 16)
        attrs_ptr = u32(rd(tileset_ptr + ATTR_OFF, 4))
        off = metatile * ATTR_SIZE
    else:
        tileset_ptr = u32(layout, 20)
        attrs_ptr = u32(rd(tileset_ptr + ATTR_OFF, 4))
        off = (metatile - PRIMARY_N) * ATTR_SIZE
    attribute = u16(rd(attrs_ptr + off, 2))
    return attribute, collision


total_imp = 0
total_live = 0
by_map: dict[str, tuple[int, int]] = {}   # name -> (imp, live)
failed = []

for map_enum in MapRSE:
    g, m = map_enum.value
    if (g, m) not in headers:
        failed.append(map_enum.name)
        continue
    layout = get_layout(g, m)
    width, height = u32(layout, 0), u32(layout, 4)
    imp = live = 0
    for y in range(height):
        for x in range(width):
            attribute, collision = tile_attr_and_collision(g, m, x, y)
            tile_type = _get_tile_type_name(attribute & 0xFF)
            if tile_type.startswith("Impassable "):
                imp += 1
                if collision == 0:
                    live += 1
    if imp:
        by_map[map_enum.name] = (imp, live)
    total_imp += imp
    total_live += live

print(f"\n[independent] TOTAL Impassable* tiles = {total_imp}   dormant = {total_imp - total_live}   live = {total_live}")
print(f"[independent] failed maps: {failed}")

tomb_names = ["DESERT_RUINS", "ISLAND_CAVE", "ANCIENT_TOMB"]
tomb_total = sum(live for name, (i, live) in by_map.items() if any(name.startswith(t) for t in tomb_names))
shoal_total = sum(live for name, (i, live) in by_map.items() if name.startswith("SHOAL_CAVE"))
vr_total = sum(live for name, (i, live) in by_map.items() if name.startswith("VICTORY_ROAD"))
seafloor_total = sum(live for name, (i, live) in by_map.items() if name.startswith("SEAFLOOR_CAVERN"))

print(f"[independent] Regi tombs (Desert Ruins+Island Cave+Ancient Tomb) live = {tomb_total}")
print(f"[independent] Shoal Cave live = {shoal_total}")
print(f"[independent] Victory Road live = {vr_total}")
print(f"[independent] Seafloor Cavern live = {seafloor_total}  (claimed: 0)")

print("\n[independent] per-map breakdown (name: imp/live), only maps with imp>0:")
for name, (i, live) in sorted(by_map.items()):
    print(f"    {name:<32} imp={i:<4} live={live}")

print("\n=== CLAIMED (05-KNOWN-ISSUES.md, probe_impassable_dirs.py, 2026-08-13) ===")
print("  total=2658 dormant=2257 live=401 | tombs(144: 48 each) shoal=98 victory_road=58")
print("\n=== MATCH? ===")
print(f"  total  : {'MATCH' if total_imp == 2658 else 'MISMATCH'} ({total_imp} vs 2658)")
print(f"  live   : {'MATCH' if total_live == 401 else 'MISMATCH'} ({total_live} vs 401)")
print(f"  tombs  : {'MATCH' if tomb_total == 144 else 'MISMATCH'} ({tomb_total} vs 144)")
print(f"  shoal  : {'MATCH' if shoal_total == 98 else 'MISMATCH'} ({shoal_total} vs 98)")
print(f"  vroad  : {'MATCH' if vr_total == 58 else 'MISMATCH'} ({vr_total} vs 58)")
