# -*- coding: utf-8 -*-
"""⛔ DOES THE GRIND TILE ACTUALLY ROLL ENCOUNTERS? (`#24-trainingbrackets`)

WHY THIS EXISTS. A proposed PRODUCTION change adds `(VICTORY_ROAD_1F, (15, 39), (36, 40))` to
`TRAINING_GRASS`. The whole row rests on `(15,39)` being encounter ground.

\u26d4\u26d4 **CORRECTION (2026-09-18) \u2014 I FIRST WROTE, IN THIS VERY DOCSTRING, THAT THE ONLY EVIDENCE
WAS A COMMENT \u201cciting a driver reading with no committed artifact\u201d. THAT WAS FALSE.**
\u2705 `tools/story-dev/ch23route_R15.log:110` exists and reads
`[ch23route]     (15, 39) tile_type='Cave' elev=3 collision=0`.
I had grepped only `tools/story-dev/evidence/*.txt` \u2014 the log lives at the `tools/story-dev/` root \u2014
and concluded ABSENCE FROM A PARTIAL SEARCH. See `08-MISTAKES.md` 2026-09-18.

\u2b50 **THIS PROBE IS STILL WORTH HAVING, FOR A NARROWER AND HONEST REASON:** `ch23route_R15.log`
records the grind tile and its neighbours, but it carries **no SEPARATING CONTROL** \u2014 it cannot show
the reading is about THIS tile rather than about the map in general. This probe supplies that control
(`(15,40)` is a South Arrow Warp and `(15,41)` is Normal with collision=1; both answer
`has_encounters=False`), and it is re-runnable and committed.

`victory_road.py:474` warns why the distinction matters:

    only `MB_CAVE` rolls encounters on 1F, 16 walkable tiles are `MB_NORMAL`, and a spin parked on
    one of those generates ZERO battles while looking perfectly healthy.

\u21d2 a wrong tile here is the project's worst failure shape: **it fails by being quiet.** The grind
would run, burn hours, and train nothing, looking fine the whole time.

\u203c AND A COMMENT IS NOT AN ARTIFACT. `CLAUDE.md` is explicit that a claim code depends on gets
verified in our own harness. This probe makes that reading re-runnable and committable.

\u26d4\u26d4 KI-74 APPLIES, AND THIS PROBE DOES **NOT** CLEAR IT \u2014 SAYING SO IS THE POINT.
\u203c **CORRECTION (2026-09-18, caught by a Tier 1 reviewer before commit):** this paragraph originally
read *\u201cTHIS READS THE **LIVE** GRID \u2026 this prints BOTH \u2026 and says so when they disagree\u201d*. **That was
false.** The only reader in this file is `get_map_data` (see `read()` below) \u2014 there is no live-grid
access anywhere in it, and the probe's own closing output has always said so.
\u21d2 what KI-74 means here: on a LAYOUT-SWAPPED map the static ROM view lies to every reader,
`get_map_data` included, so this probe would be lied to as well. Victory Road 1F is not known to be
layout-swapped, but **this probe cannot prove that** \u2014 the decisive cross-check is a live
`gBackupMapLayout` dump, which is `probe_live_mapgrid.py`'s job, not this one's.

READ-ONLY: loads save states and reads tiles. Nothing is walked, nothing is written.
"""
import pathlib as _pl
import sys

sys.path.insert(0, str(_pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement") / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.player import get_player_avatar

SAVES = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\saves")
VR1F = MapRSE.VICTORY_ROAD_1F

#: The tile the proposed TRAINING_GRASS row names, and the one `TRAIN_SPOT_1F` already points at.
GRIND_TILE = (15, 39)
#: Neighbours, so a PASS on the grind tile is not the only datum \u2014 if every tile answers the same
#: way the reading proves nothing about THIS tile.
NEIGHBOURS = [(15, 38), (15, 40), (14, 39), (16, 39), (15, 41), (14, 40)]

#: A fixture standing on VICTORY_ROAD_1F, so the LIVE layout is the one we care about.
FIXTURE = "grind_stall_ppzero.ss1"

print("=" * 108)
print("DOES THE GRIND TILE ROLL ENCOUNTERS?  \u2014 reading tiles only; nothing is walked")
print("=" * 108)

p = SAVES / FIXTURE
if not p.exists():
    raise SystemExit(f"MISSING FIXTURE: {p}")
context.emulator.load_save_state(p.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

av = get_player_avatar()
here_val = tuple(av.map_group_and_number)
print(f"  fixture   : {FIXTURE}")
print(f"  standing  : {MapRSE(here_val).name} {tuple(av.local_coordinates)}")
if here_val != tuple(VR1F.value):
    raise SystemExit(f"\u26d4 fixture is not on VICTORY_ROAD_1F (it is on {here_val}) \u2014 wrong premise")


def read(tile):
    """Every field that bears on 'does this tile roll encounters'."""
    md = get_map_data(VR1F, tile)
    return {
        "has_encounters": getattr(md, "has_encounters", "n/a"),
        "tile_type": getattr(md, "tile_type", "n/a"),
        "collision": getattr(md, "collision", "n/a"),
        "elevation": getattr(md, "elevation", "n/a"),
    }


print()
print(f"  {'tile':<10} {'has_encounters':<16} {'tile_type':<26} {'coll':<6} elev")
print("  " + "-" * 74)
rows = {}
for t in [GRIND_TILE] + NEIGHBOURS:
    try:
        r = read(t)
    except Exception as error:  # noqa: BLE001 - a failed read IS the reading
        print(f"  {str(t):<10} \u26d4 COULD NOT READ: {type(error).__name__}: {error}")
        continue
    rows[t] = r
    star = " \u2b50" if t == GRIND_TILE else ""
    print(f"  {str(t):<10} {str(r['has_encounters']):<16} {str(r['tile_type'])[:26]:<26} "
          f"{str(r['collision']):<6} {r['elevation']}{star}")

print()
print("-" * 108)
g = rows.get(GRIND_TILE)
if g is None:
    print("  \u26d4 THE GRIND TILE COULD NOT BE READ \u2014 the proposed TRAINING_GRASS row is UNSUPPORTED.")
    raise SystemExit(1)

enc = g["has_encounters"]
print(f"  \u2b50 GRIND TILE {GRIND_TILE}: has_encounters={enc}  tile_type={g['tile_type']}  "
      f"collision={g['collision']}")

# \u203c A control: if EVERY tile answers the same, this reading cannot distinguish this tile from any
# other, and a PASS would be meaningless. Say so rather than claiming a result.
vals = {t: r["has_encounters"] for t, r in rows.items()}
distinct = set(map(str, vals.values()))
if len(distinct) == 1:
    print(f"  \u26a0\u26a0 CONTROL WEAK: every tile read returned has_encounters={distinct.pop()}. This "
          f"reading cannot tell {GRIND_TILE} apart from its neighbours, so it supports the row only "
          f"weakly \u2014 it shows the AREA rolls encounters, not that this TILE is special.")
else:
    others = {t: v for t, v in vals.items() if t != GRIND_TILE}
    print(f"  \u2705 CONTROL SEPARATES: neighbours differ \u2014 {others}")
    print(f"     \u21d2 the reading is about THIS tile, not about the map in general.")

if enc is True:
    print(f"  \u2705 THE ROW IS SUPPORTED: {GRIND_TILE} rolls encounters.")
elif enc is False:
    print(f"  \u26d4\u26d4 THE ROW IS REFUTED: {GRIND_TILE} does NOT roll encounters. A grind parked here "
          f"would train NOTHING while looking perfectly healthy \u2014 exactly the failure the "
          f"`victory_road.py:474` comment warns about. DO NOT ADD THE ROW.")
else:
    print(f"  \u26a0 INCONCLUSIVE: has_encounters read back as {enc!r}, which is neither True nor False.")

print()
print("  \u203c LIMITS OF THIS PROBE, STATED: it reads our planner's view (`get_map_data`). KI-74 records")
print("    that a LAYOUT-SWAPPED map lies to exactly that reader. Victory Road 1F is not known to be")
print("    layout-swapped, but this probe does NOT prove it isn't \u2014 the decisive cross-check is a")
print("    live `gBackupMapLayout` dump (`probe_live_mapgrid.py`), and the strongest evidence of all")
print("    is a drive that stands here and counts battles.")
print("=" * 108)
