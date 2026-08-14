"""KI-76 / D5 — is the unguarded `None` unpack in the current-slide loop ARMED on real maps?

THE DEFECT (`modules/map_path.py`): the slide loop follows a current across map edges:

    if x >= destination.map_size[0] - 1:
        x = 0
        current_map, offset = _get_connection_for_direction(destination, "East")   # <- can be None

`_get_connection_for_direction()` returns **`None`** when the map has no connection that way
(`map_path.py:435-439`), and the tuple unpack is unguarded at four sites. A `None` there is a
**`TypeError` raised inside `PathMap.tiles`** — i.e. on the first `calculate_path` that touches the
map, not at a nice boundary.

‼ WHY THIS MATTERS MORE THAN THE CAVERN: the Seafloor Cavern's currents are interior, so it is safe.
But **Routes 124-134 and Pacifidlog are full of currents**, and `ROUTE128` is **already on a driven
path** (`--driver ch20dive` sails it every run). If a current sits on a map edge whose connection is
absent in that direction, any route planned on that map crashes.

WHAT THIS MEASURES (facts, no opinions):
  1. Every map in the game that contains `* Current` tiles — not just the ones we expected.
  2. For each, the current tiles that sit ON a map edge, and whether the map declares a connection
     in the direction that current pushes.
  3. ⇒ the exact list of ARMED tiles: an edge current pushing off-map with no connection.

  A tile is ARMED only if the current would actually push it OFF the edge — an eastward current on
  the WEST edge is harmless. That distinction is the whole point; counting "currents on edges"
  without it would overstate the risk.

CONTROL: the Seafloor Cavern rooms must report 0 armed tiles (their currents are interior). If they
report armed tiles, this probe's edge logic is wrong, not the maps.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_current_edges.py
Exit: 0 always (measurement probe).
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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE

BAR = "=" * 100

# The direction each current pushes, and which edge that direction runs off.
PUSH = {
    "Eastward Current": ("East", "x_max"),
    "Westward Current": ("West", "x_min"),
    "Northward Current": ("North", "y_min"),
    "Southward Current": ("South", "y_max"),
}


def head(t):
    print(f"\n{BAR}\n{t}\n{BAR}\n")


print("Scanning all 518 maps for `* Current` tiles, then checking edge tiles against the map's")
print("own connection table. ‼ ARMED = an edge current pushing OFF-MAP with no connection that way.\n")

maps_with = []
armed_total = 0
armed_rows = []
failed = []

for map_enum in MapRSE:
    try:
        md = get_map_data(map_enum, (0, 0))
        tiles = get_map_all_tiles(md)
    except Exception as exc:
        failed.append((map_enum.name, f"{type(exc).__name__}: {exc}"))
        continue
    currents = [t for t in tiles if t.tile_type.endswith(" Current")]
    if not currents:
        continue
    w, h = md.map_size
    conn_dirs = {c.direction for c in md.connections}
    armed_here = []
    for t in currents:
        x, y = t.local_position
        direction, edge = PUSH.get(t.tile_type, (None, None))
        if direction is None:
            continue
        on_edge = (
            (edge == "x_max" and x >= w - 1)
            or (edge == "x_min" and x <= 0)
            or (edge == "y_min" and y <= 0)
            or (edge == "y_max" and y >= h - 1)
        )
        if on_edge and direction not in conn_dirs:
            armed_here.append(((x, y), t.tile_type, direction))
    maps_with.append((map_enum.name, len(currents), sorted(conn_dirs), len(armed_here)))
    armed_total += len(armed_here)
    if armed_here:
        armed_rows.append((map_enum.name, armed_here))

head("1. EVERY MAP WITH CURRENTS")

print(f"  maps with `* Current` tiles: {len(maps_with)}   (unreadable maps: {len(failed)})")
print(f"  {'map':<40} {'currents':>9}  connections                armed")
for name, n, conns, armed in sorted(maps_with, key=lambda r: -r[1]):
    flag = "  <- ‼ ARMED" if armed else ""
    print(f"  {name:<40} {n:>9}  {','.join(conns) or '(none)':<26} {armed}{flag}")

head("2. THE ARMED TILES — an edge current pushing off-map with no connection")

if not armed_rows:
    print("  ✅ NONE. The unguarded `None` unpack (KI-76 / D5) is NOT armed anywhere in this ROM.")
    print("     ⇒ It is a latent robustness defect, not a live crash. Worth a guard, not a hotfix.")
else:
    for name, rows in armed_rows:
        print(f"  ‼ {name}")
        for coords, ttype, direction in rows[:12]:
            print(f"      {coords} {ttype!r} pushes {direction} off-map, no {direction} connection")
        if len(rows) > 12:
            print(f"      ... and {len(rows) - 12} more")
    print(f"\n  TOTAL ARMED TILES: {armed_total}")
    print("  ⇒ Any `calculate_path` touching these maps raises TypeError inside `PathMap.tiles`.")

head("3. CONTROL — the Seafloor Cavern's currents are INTERIOR and must report 0 armed")

for m in (MapRSE.SEAFLOOR_CAVERN_ROOM6, MapRSE.SEAFLOOR_CAVERN_ROOM7):
    row = [r for r in maps_with if r[0] == m.name]
    if not row:
        print(f"  ‼ {m.name} reported NO currents — the scanner is broken, not the map.")
    else:
        _n, cur, _c, armed = row[0]
        print(f"  {m.name}: currents={cur} armed={armed}  {'PASS' if armed == 0 else '‼ FAIL — edge logic is wrong'}")

head("4. IS ANY OF THIS ON A PATH THE BOT ALREADY DRIVES?")

DRIVEN = {"ROUTE128", "UNDERWATER_ROUTE128", "MOSSDEEP_CITY", "ROUTE124", "ROUTE125", "ROUTE126", "ROUTE127"}
touched = [(n, cur, armed) for n, cur, _c, armed in maps_with if n in DRIVEN]
if touched:
    for n, cur, armed in touched:
        print(f"  {n:<28} currents={cur:<5} armed={armed}   {'‼ LIVE CRASH RISK' if armed else 'safe'}")
else:
    print("  None of the currently-driven maps contain currents at all.")
print("\n  (DRIVEN = the maps `--driver ch20dive` and the Mossdeep chapters actually plan on.)")

if failed:
    print(f"\n‼ UNREADABLE MAPS (measurement gaps, not zeroes): {len(failed)}")
    for name, err in failed[:10]:
        print(f"    {name}: {err}")

head("DONE — measurement only. Nothing was changed.")
