"""Pick + two-way sweep a training tile for the Flannery prep (Segment 11d).

Prevention rule (08-MISTAKES 2026-07-22): never adopt a training tile without
proving BOTH directions FROM THE REAL ENTRY TILE — Lavaridge Town, where the bot
actually stands when Segment 11d starts. Jagged Pass is the only grass adjacent to
Lavaridge, so: enumerate its tall-grass tiles, then for each candidate navigate
Lavaridge -> tile AND tile -> the Lavaridge PC, and report only tiles that pass both.
"""

import pathlib as _pl
import sys

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.modes import BotModeError
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.player import get_player_avatar

TALL_GRASS_MB = 2  # MB_TALL_GRASS
SAVE = (_SAVES / "lavaridge.ss1").read_bytes()


def step(gen, n=4000):
    for _ in range(n):
        try:
            next(gen)
        except StopIteration:
            return True
        context.emulator.run_single_frame()
    return False


def reset():
    context.emulator.load_save_state(SAVE)
    for _ in range(30):
        context.emulator.run_single_frame()


# 1. Enumerate Jagged Pass tall grass.
import os
TARGET = os.environ.get("PROBE_MAP", "JAGGED_PASS")
gnum = MapRSE[TARGET].value
md = get_map_data(gnum, (0, 0))
w, h = md.map_size
grass = []
for y in range(h):
    for x in range(w):
        t = get_map_data(gnum, (x, y))
        if not t.collision and (t._metatile_attributes[0] & 0x1FF) == TALL_GRASS_MB:
            grass.append((x, y))
print(f"{TARGET} ({w}x{h}) tall-grass tiles: {len(grass)}")
print(f"  {grass}")

# 2. Candidates: the grass tiles nearest the Lavaridge exit (14,39) — least walking.
ANCHOR = tuple(int(v) for v in os.environ.get("PROBE_ANCHOR", "14,39").split(","))
cands = sorted(grass, key=lambda t: abs(t[0] - ANCHOR[0]) + abs(t[1] - ANCHOR[1]))[:6]
print(f"\ncandidates (nearest {ANCHOR}): {cands}")

reset()
print(f"start: {get_player_avatar().map_group_and_number} {get_player_avatar().local_coordinates}")

for tile in cands:
    reset()
    try:
        ok_out = step(navigate_to_anywhere(MapRSE[TARGET], tile, avoid_encounters=True), 12000)
    except BotModeError as e:
        print(f"  {tile}: OUT fail ({str(e)[:60]})")
        continue
    except Exception as e:
        print(f"  {tile}: OUT err {str(e)[:60]}")
        continue
    pa = get_player_avatar()
    if not ok_out or tuple(pa.local_coordinates) != tile or pa.map_group_and_number != gnum:
        print(f"  {tile}: OUT timeout (ended {pa.map_group_and_number} {pa.local_coordinates})")
        continue
    # Return leg: back to the Lavaridge PC door tile.
    try:
        ok_back = step(navigate_to_anywhere(MapRSE.LAVARIDGE_TOWN, (9, 7), avoid_encounters=True), 12000)
    except BotModeError as e:
        print(f"  {tile}: OUT ok, BACK fail ({str(e)[:60]})")
        continue
    except Exception as e:
        print(f"  {tile}: OUT ok, BACK err {str(e)[:60]}")
        continue
    pa = get_player_avatar()
    verdict = "PASS (two-way)" if ok_back and pa.map_group_and_number == MapRSE.LAVARIDGE_TOWN.value else "BACK timeout"
    print(f"  {tile}: OUT ok, {verdict} (ended {pa.map_group_and_number} {pa.local_coordinates})")
