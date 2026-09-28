r"""GATE (ROM) — every training / hunting SPIN TILE can roll a wild LAND encounter (`#27-r101standstill`, 2026-09-28).

WHY: a spin parked on a tile that cannot roll an encounter fails QUIETLY. It looks healthy, trains nothing and catches
nothing (`victory_road.py` calls it the project's worst failure shape). `TRAINING_GRASS`'s ROUTE101 row sat on (9, 9),
the TRAVEL waypoint, which is plain ground: the Surf-learner hunt spun there in 204 batch episodes with 0 battles until
the 18k watchdog. `probe_grind_tile_encounters.py` guarded ONE grind tile; nothing guarded the table. This does.

  T1  every `TRAINING_GRASS` row's tile rolls LAND encounters (encounter flag set, not surfable water). The three rows
      on OCEAN WATER are listed in `KNOWN_WATER_ROWS` against the follow-up `#27-waterrows`: they must still read as
      water. A row that stops being water FAILS until it is removed from the list, so the list cannot go stale.
  T2  the named spin constants (`RUSTBORO_TRAINING_GRASS`, `PETALBURG_TRAINING_GRASS`, `ROUTE117_TRAINING_GRASS`) roll
      land encounters too.
  T3  SEPARATING CONTROL: the reader says False for ROUTE101 (9, 9) and True for (12, 10). Without it, a reader that
      said True everywhere would pass T1.
  T4  `_hm_hunting_grounds(HM03)` offers only land-encounter tiles, and includes ROUTE101 (12, 10).
FAULT ARMS (built in; each must FAIL for its own reason; the unmutated subject must pass first):
  F1  a table with ROUTE101 back on (9, 9) fails T1;
  F2  `POKEBOT_R101_FAULT_OLDTILE=1` (the tile filter skipped) makes `_hm_hunting_grounds` offer a non-land tile: T4.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_training_tiles.py
"""
from __future__ import annotations

import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "probe-tiles"
if not profile_directory_exists(PROFILE):
    create_profile(PROFILE, list_available_roms()[0])
profile = load_profile_by_name(PROFILE)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0   # ⛔ UNTHROTTLED — a registered gate must be (`probe_gate_unthrottled.py`)
context.bot_mode = "Manual"
context.emulator.load_save_state((REPO / "tools" / "story-dev" / "saves" / "norman_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.items import get_item_by_name  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.story import early_game as EG  # noqa: E402
from modules.story import training_areas as TA  # noqa: E402

#: The OCEAN-WATER rows, a known defect filed as `#27-waterrows` (the table calls itself "land-only"). ⛔ Never add a row
#: here to make this gate pass: fix the row's tile. A row listed here that is no longer water FAILS T1.
KNOWN_WATER_ROWS = {(MapRSE.ROUTE115, (6, 53)), (MapRSE.ROUTE118, (29, 15)), (MapRSE.ROUTE119, (21, 109))}
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def is_water(map_enum, tile) -> bool:
    from modules.map import get_map_data

    d = get_map_data(map_enum, tuple(tile))
    return bool(d.has_encounters) and bool(d.is_surfable)


def t1(rows, sink=None):
    bad, stale = [], []
    for map_enum, tile, _band in rows:
        if tile is None:
            continue
        land = TA.tile_rolls_land_encounters(map_enum, tile)
        if (map_enum, tuple(tile)) in KNOWN_WATER_ROWS:
            if not is_water(map_enum, tile):
                stale.append((map_enum.name, tile))
        elif land is not True:
            bad.append((map_enum.name, tile, land))
    check(not bad and not stale,
          f"T1 every TRAINING_GRASS row rolls land encounters (bad: {bad}; known-water rows no longer water: {stale})",
          sink)


def main() -> int:
    print("T1 — the table")
    t1(TA.TRAINING_GRASS)
    print("T2 — the named spin constants")
    consts = {"RUSTBORO_TRAINING_GRASS": EG.RUSTBORO_TRAINING_GRASS, "PETALBURG_TRAINING_GRASS": EG.PETALBURG_TRAINING_GRASS,
              "ROUTE117_TRAINING_GRASS": EG.ROUTE117_TRAINING_GRASS}
    bad = {k: v for k, v in consts.items() if TA.tile_rolls_land_encounters(v[0], v[1]) is not True}
    check(not bad, f"T2 the named spin constants roll land encounters (bad: {bad})")
    print("T3 — separating control")
    old = TA.tile_rolls_land_encounters(MapRSE.ROUTE101, (9, 9))
    new = TA.tile_rolls_land_encounters(MapRSE.ROUTE101, (12, 10))
    check(old is False and new is True, f"T3 ROUTE101 (9,9) reads {old} and (12,10) reads {new} (want False / True)")
    print("T4 — the HM hunt's grounds")
    hm03 = get_item_by_name("HM03")
    grounds = EG._hm_hunting_grounds(hm03)
    nonland = [(m.name, t) for m, t, _n in grounds if TA.tile_rolls_land_encounters(m, t) is not True]
    has_r101 = any(m == MapRSE.ROUTE101 and tuple(t) == (12, 10) for m, t, _n in grounds)
    check(not nonland and has_r101,
          f"T4 _hm_hunting_grounds(HM03) offers only land tiles, incl. ROUTE101 (12,10) (non-land: {nonland}; "
          f"{len(grounds)} grounds)")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    rows = [(MapRSE.ROUTE101, (9, 9), band) if m == MapRSE.ROUTE101 else (m, t, band) for m, t, band in TA.TRAINING_GRASS]
    sink: list = []
    t1(rows, sink)
    check(base_ok and bool(sink), "F1 a table with ROUTE101 back on (9,9) fails T1")
    os.environ["POKEBOT_R101_FAULT_OLDTILE"] = "1"
    try:
        g2 = EG._hm_hunting_grounds(hm03)
    finally:
        os.environ.pop("POKEBOT_R101_FAULT_OLDTILE", None)
    nonland2 = [(m.name, t) for m, t, _n in g2 if TA.tile_rolls_land_encounters(m, t) is not True]
    check(base_ok and bool(nonland2), f"F2 with the tile filter skipped, the hunt is offered non-land tiles ({nonland2})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — every training and hunting spin tile can roll a land encounter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
