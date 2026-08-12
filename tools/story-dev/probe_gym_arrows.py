"""KI-58 / §Ch18 — DUMP THE ARROW LAYOUT so the statue puzzle can be SIMULATED.

‼ WHY THIS EXISTS. The Mossdeep Gym is a rotating-tile statue puzzle: nine floor switches call
`moverotatingtileobjects <colour>`, and every statue standing on a coloured ARROW metatile of that
colour shifts one tile in the arrow's direction. To plan a route we must be able to answer "where
would the statues be after pressing blue three times?" WITHOUT pressing blue three times — because
a search that has to press buttons costs an emulator step per edge and the route is ~116 steps deep
over a 1024-state statue space.

The arrows are MAP LAYOUT: they are baked into the ROM and they never move. Only the statues move.
So the arrow field can be dumped ONCE and the whole puzzle simulated offline from it.

‼ WHAT THIS PROBE DOES NOT DO: it does not trust the claimed arrow encoding. The note in KI-58 says
"arrows start at 0x250; colour = (mt-0x250)//8; direction = (mt-0x250)%8 with 0=R,1=D,2=L,3=U".
That is a NOTE, and by this project's rule a note is not truth. This probe DERIVES the encoding from
data instead: it prints every distinct metatile id that a statue actually stands on, then checks the
derived model against a live-measured switch press.

‼ THE METATILE ID IS NOT PUBLICLY EXPOSED. `modules/map.py` computes it at line 779 as
`map_grid_block & 0x03FF` but returns only (attributes, collision, elevation). Rather than widen a
SHARED module for a probe, this file re-reads the same two bytes itself — the read is six lines and
is a pure ROM lookup, so there is nothing to keep in sync.

CONTROLS (printed, and the probe reports FAIL rather than exiting 0 quietly):
  [1] ARROW COVERAGE — every statue must stand on a tile the derived model recognises as an arrow.
      A statue on a non-arrow tile would mean the model cannot predict it, and a solver built on it
      would be silently wrong.
  [2] SIMULATOR vs THE GAME — replay the live-measured YELLOW press at (3,30) recorded in KI-58 and
      require the simulator to reproduce the observed statue delta EXACTLY.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_arrows.py
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.memory import unpack_uint16, unpack_uint32

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "in_mossdeep_gym.ss1"
GYM = MapRSE.MOSSDEEP_CITY_GYM

line = "=" * 96


def metatile_id(x: int, y: int) -> int | None:
    """The raw metatile id at (x, y), re-read the way `map.py:762-779` reads it.

    Returns None for off-map coordinates rather than the border metatile, because a border tile is
    not a real tile and letting it enter the arrow table would invent arrows that do not exist."""
    tile = get_map_data(GYM, (x, y))
    width, height = tile.map_size
    if not (0 <= x < width and 0 <= y < height):
        return None
    offset = (x * 2) + (width * y * 2)
    map_data_pointer = unpack_uint32(tile._map_layout[12:16])
    block = unpack_uint16(context.emulator.read_bytes(map_data_pointer + offset, 2))
    return block & 0x03FF


context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

origin = get_map_data(GYM, (0, 0))
WIDTH, HEIGHT = origin.map_size

print(line)
print("MOSSDEEP GYM — arrow layout dump (so the statue puzzle can be simulated)")
print(line)
print(f"\nmap size: {WIDTH} x {HEIGHT}")

# ------------------------------------------------------------------ the statues (ROM templates)
# ‼ `MapLocation.objects` reads the map header's event list, which lives in ROM — so it is always
# the INITIAL template positions, never the mutated ones. That is exactly what a simulator wants as
# its starting state. (The live, mutated positions come from `get_map_objects()`.)
templates = origin.objects
statue_templates = [t for t in templates if t.trainer_type == "None"]
print(f"object templates: {len(templates)}  (of which trainer_type=None: {len(statue_templates)})")

print("\n" + line)
print("WHAT EACH OBJECT TEMPLATE STANDS ON")
print(line)
print(f"\n  {'id':>3} {'gfx':>4} {'coords':<9} {'metatile':>9} {'trainer':<20} movement")
under = {}
for t in templates:
    x, y = t.local_coordinates
    mt = metatile_id(x, y)
    under[(x, y)] = mt
    print(f"  {t.local_id:>3} {t.graphics_id:>4} {str((x, y)):<9} "
          f"{('0x%03X' % mt) if mt is not None else '   --':>9} {t.trainer_type:<20} {t.movement_type}")

# ------------------------------------------------------------------ derive the arrow encoding
# Group the metatile ids that objects stand on. If the puzzle model is right, the statues sit on a
# small contiguous band of ids, and that band is the arrow set.
statue_mts = sorted({under[t.local_coordinates] for t in statue_templates
                     if under[t.local_coordinates] is not None})
print("\n" + line)
print("DISTINCT METATILES UNDER trainer_type=None OBJECTS  (the candidate ARROW set)")
print(line)
print(f"\n  {[hex(m) for m in statue_mts]}")
if statue_mts:
    base = min(statue_mts)
    print(f"\n  lowest id seen: {hex(base)}   highest: {hex(max(statue_mts))}   "
          f"span: {max(statue_mts) - base + 1}")
    print(f"  claimed base from KI-58 note: 0x250  ->  {'MATCHES' if base == 0x250 else 'DOES NOT MATCH the lowest id seen'}")
    print("\n  decomposed against base 0x250 as (mt-0x250)//8 = colour, (mt-0x250)%8 = direction:")
    for m in statue_mts:
        d = m - 0x250
        print(f"    {hex(m)}  ->  colour {d // 8}, direction {d % 8}")

# ------------------------------------------------------------------ the whole arrow field
print("\n" + line)
print("EVERY TILE WHOSE METATILE FALLS IN THE ARROW BAND 0x250..0x27F")
print(line)
arrow_field: dict[tuple[int, int], int] = {}
for y in range(HEIGHT):
    for x in range(WIDTH):
        mt = metatile_id(x, y)
        if mt is not None and 0x250 <= mt <= 0x27F:
            arrow_field[(x, y)] = mt
by_colour: dict[int, list] = {}
for (x, y), mt in sorted(arrow_field.items()):
    by_colour.setdefault((mt - 0x250) // 8, []).append(((x, y), (mt - 0x250) % 8))
print(f"\n  {len(arrow_field)} arrow tiles in {len(by_colour)} colour band(s)\n")
COLOUR_NAMES = {0: "colour0", 1: "colour1", 2: "colour2", 3: "colour3", 4: "colour4", 5: "colour5"}
for colour in sorted(by_colour):
    cells = by_colour[colour]
    print(f"  band {colour} ({COLOUR_NAMES.get(colour, '?')}) — {len(cells)} tiles")
    for (x, y), direction in cells:
        print(f"      {str((x, y)):<9} dir {direction}")

print("\n" + line)
print("CONTROL [1] — ARROW COVERAGE: does every statue stand on an arrow?")
print(line)
off_arrow = [t.local_coordinates for t in statue_templates if t.local_coordinates not in arrow_field]
print(f"\n  statues: {len(statue_templates)}   standing on an arrow tile: "
      f"{len(statue_templates) - len(off_arrow)}   NOT on an arrow: {len(off_arrow)}")
if off_arrow:
    print(f"  ‼ off-arrow statues: {sorted(off_arrow)}")
    print("  A statue the model cannot see is a statue the solver will misplace. Investigate before")
    print("  building anything on this dump.")
print(f"  [1] {'OK' if not off_arrow else 'FAIL'}")

print("\n" + line)
print("A MAP OF THE ARROW FIELD  (digit = direction code, letter = colour band)")
print(line)
header = "     " + "".join(str(x % 10) for x in range(WIDTH))
print("\n" + header)
statue_cells = {t.local_coordinates for t in statue_templates}
for y in range(HEIGHT):
    row = ""
    for x in range(WIDTH):
        cell = (x, y)
        if cell in arrow_field:
            row += "ABCDEF"[(arrow_field[cell] - 0x250) // 8] if cell not in statue_cells else "abcdef"[(arrow_field[cell] - 0x250) // 8]
        else:
            try:
                row += "#" if get_map_data(GYM, cell).collision != 0 else "."
            except Exception:  # noqa: BLE001 — an unreadable tile draws as wall, never as floor
                row += "#"
    print(f"  {y:>2} {row}")
print(header)
print("\n  UPPERCASE = arrow tile, lowercase = arrow tile WITH A STATUE ON IT, # = wall, . = floor")

print("\n" + line)
print("NEXT")
print(line)
print("""
  This dump is the input to the simulator. The simulator is validated in
  `probe_gym_simulate.py`, which replays the live-measured YELLOW press at (3,30) and requires an
  exact reproduction of the observed statue delta before any route is planned on it.
""")
print(line)
