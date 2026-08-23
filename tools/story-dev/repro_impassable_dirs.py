"""KI-59 / `#24-impassabledirs` — the REPRODUCE → PROVE gate for the `Impassable *` inversion.

‼ THIS GATE IS EXPECTED TO **FAIL** BEFORE THE FIX AND **PASS** AFTER IT. That is the A/B.
Run it, record the FAIL, apply the fix, run it again, record the PASS. A gate that passes on both
sides of a change proves nothing.

WHAT IT ASSERTS
  For every `Impassable *` tile that actually REACHES the buggy branch (collision == 0), the REAL
  production `PathTile.accessible_from_direction` — read off the object `map_path` itself builds,
  NOT a re-implementation — must equal the decomp-derived truth.

‼ WHY IT READS THE PRODUCTION OBJECT INSTEAD OF RECOMPUTING
  `tools/story-dev/probe_shoal_tide.py:364-367` re-implements this logic and faithfully reproduces
  the BUG, so it agrees with production while both are wrong. A check that recomputes the thing it
  is checking cannot fail. This gate imports `_get_map_metadata` and inspects the real tiles.

GROUND TRUTH (decomp, quoted in `06-DECISIONS-LOG.md` 2026-08-13):
  `src/event_object_movement.c:4715-4722`  IsMetatileDirectionallyImpassable ORs
      gOppositeDirectionBlockedMetatileFuncs[dir-1](tile you STAND ON)   <- blocks LEAVING
      gDirectionBlockedMetatileFuncs[dir-1](DESTINATION tile)            <- blocks ENTERING
  `src/event_object_movement.c:893-905`     the two arrays, and
  `include/constants/global.h:137-141`      DIR_SOUTH 1 / DIR_NORTH 2 / DIR_WEST 3 / DIR_EAST 4.
  ⇒ `MB_IMPASSABLE_<D>` means **"this tile's <D> EDGE is a wall"**: you may not ENTER it moving
    opposite(D), and you may not LEAVE it moving D. Symmetric. Both halves are required.

MAPS (chosen deliberately — see `06-DECISIONS-LOG.md` Decision 4)
  POSITIVE  VICTORY_ROAD_1F — 29 live tiles, and ‼ it does NOT rewrite its own tiles at runtime,
            unlike the Regi tombs / Shoal Cave / Lilycove lobby (`setmetatile`,
            `setmaplayoutindex`), so a static-layout assertion there is meaningful.
  NEGATIVE  SEAFLOOR_CAVERN_ROOM1 — 27 `Impassable *` tiles, ALL `collision=1`, so ZERO reach the
            branch. This control is what proves the four documents that called KI-59 "armed in the
            Seafloor Cavern" were wrong; it must report 0 live tiles and 0 mismatches in BOTH arms.
  VACUITY   the positive map must contribute > 0 live tiles, or the gate is not testing anything.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_impassable_dirs.py
Exit: 0 = all assertions hold; 1 = a mismatch (or the gate went vacuous).
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
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

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)  # ‼ is_test_run: without it the
    # emulator registers an atexit that OVERWRITES shared `profiles/<name>/current_state.ss1`
    # and writes a states/ snapshot. Pass 2 fixed this for the two KI-76 probes; PASS 4
    # (2026-08-22) found SEVEN MORE still writing — `profiles/repro-ml/states/` had reached
    # 2,820 files / 160 MB. A probe that mutates shared state is not observe-only.
context.audio = False
context.video = False

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE
from modules.map_path import Direction, _get_map_metadata

BAR = "=" * 100
NAMES = ["N", "E", "S", "W"]


def fmt(acc) -> str:
    return "".join(NAMES[i] if acc[i] else "-" for i in range(4))


def expected_entry_vector(tile_type: str) -> list[bool]:
    """Decomp truth: start all-True, CLEAR opposite(D) for each walled edge D."""
    acc = [True, True, True, True]
    for name in tile_type[11:].replace(" and ", "/").split("/"):
        acc[Direction[name].opposite()] = False
    return acc


def expected_blocked_exits(tile_type: str) -> set:
    """Decomp truth: you may not LEAVE across a walled edge, i.e. moving D itself."""
    return {Direction[name] for name in tile_type[11:].replace(" and ", "/").split("/")}


POSITIVE = MapRSE.VICTORY_ROAD_1F
NEGATIVE = MapRSE.SEAFLOOR_CAVERN_ROOM1

failures: list[str] = []
exit_half_implemented = None
summary: list[tuple[str, int, int, int, int]] = []

for map_enum, role in ((POSITIVE, "POSITIVE"), (NEGATIVE, "NEGATIVE control")):
    print(f"\n{BAR}\n{role}: {map_enum.name}\n{BAR}")

    raw_tiles = get_map_all_tiles(get_map_data(map_enum, (0, 0)))
    imp = [t for t in raw_tiles if t.tile_type.startswith("Impassable ")]
    live = [t for t in imp if t.collision == 0]
    print(f"  `Impassable *` tiles: {len(imp)}   of which LIVE (collision == 0): {len(live)}")
    print(f"  dormant (collision != 0, never reach the branch): {len(imp) - len(live)}")

    path_map = _get_map_metadata(map_enum.value)
    by_coords = {t.local_coordinates: t for t in path_map.tiles}

    entry_bad = exit_bad = 0
    shown = 0
    for t in live:
        coords = tuple(t.local_position)
        pt = by_coords.get(coords)
        if pt is None:
            failures.append(f"{map_enum.name} {coords}: no PathTile built for a live Impassable tile")
            continue

        want_entry = expected_entry_vector(t.tile_type)
        got_entry = list(pt.accessible_from_direction)
        if got_entry != want_entry:
            entry_bad += 1
            if shown < 6:
                print(
                    f"    ENTRY MISMATCH {coords} {t.tile_type!r}: "
                    f"production=[{fmt(got_entry)}] expected=[{fmt(want_entry)}]"
                )
                shown += 1

        want_exit = expected_blocked_exits(t.tile_type)
        got_exit = getattr(pt, "blocked_exit_directions", None)
        if got_exit is None:
            if exit_half_implemented is None:
                exit_half_implemented = False
        else:
            exit_half_implemented = True
            if set(got_exit) != want_exit:
                exit_bad += 1
                if shown < 8:
                    print(
                        f"    EXIT MISMATCH  {coords} {t.tile_type!r}: "
                        f"production={sorted(d.name for d in got_exit)} "
                        f"expected={sorted(d.name for d in want_exit)}"
                    )
                    shown += 1

    if entry_bad > 6:
        print(f"    ... and {entry_bad - 6} more entry mismatches (only the first few are shown)")

    print(f"  => entry-vector mismatches: {entry_bad} / {len(live)}")
    print(f"  => exit-set mismatches    : {exit_bad} / {len(live)}" if exit_half_implemented else "  => exit-set: NOT IMPLEMENTED (PathTile has no `blocked_exit_directions`)")
    summary.append((map_enum.name, len(imp), len(live), entry_bad, exit_bad))

    if role == "POSITIVE":
        if len(live) == 0:
            failures.append(
                f"VACUOUS: {map_enum.name} contributed 0 live tiles — this gate would pass without testing anything"
            )
        if entry_bad:
            failures.append(f"{map_enum.name}: {entry_bad} live tiles have the wrong entry vector")
        if exit_half_implemented and exit_bad:
            failures.append(f"{map_enum.name}: {exit_bad} live tiles have the wrong blocked-exit set")
    else:
        if len(live) != 0:
            failures.append(
                f"NEGATIVE control broke: {map_enum.name} reported {len(live)} live tiles, expected 0 "
                f"— the 'zero of the cavern's tiles reach the branch' finding would be falsified"
            )
        if entry_bad or exit_bad:
            failures.append(f"NEGATIVE control {map_enum.name} produced mismatches ({entry_bad}/{exit_bad})")

if exit_half_implemented is False:
    failures.append(
        "the EXIT half is not implemented: `PathTile` has no `blocked_exit_directions`, so the "
        "planner can still route OFF a walled edge (decomp gOppositeDirectionBlockedMetatileFuncs)"
    )

print(f"\n{BAR}\nSUMMARY\n{BAR}")
print(f"  {'map':<28} {'impassable':>10} {'live':>6} {'entry-bad':>10} {'exit-bad':>9}")
for name, n_imp, n_live, e_bad, x_bad in summary:
    print(f"  {name:<28} {n_imp:>10} {n_live:>6} {e_bad:>10} {x_bad:>9}")
print(f"  exit half implemented: {exit_half_implemented}")

if failures:
    print(f"\n‼ FAIL — {len(failures)} problem(s):")
    for f in failures:
        print(f"    - {f}")
    print("\n(If this is the BEFORE arm of the A/B, this failure IS the reproduction.)")
    sys.exit(1)

print("\nALL CHECKS PASS — production matches the decomp on both halves, and the negative control")
print("confirms the branch is inert in the Seafloor Cavern.")
sys.exit(0)
