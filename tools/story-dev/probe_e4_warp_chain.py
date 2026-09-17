"""THE ELITE FOUR WARP CHAIN, READ FROM THE ROM'S OWN WARP TABLES.

⛔ WHY THIS EXISTS. `probe_e4_halls.py` prints a row reading `HALL2  PHOEBE -> GLACIA`, and I cited
it as MEASURED evidence that Hall 2 joins Phoebe's room to Glacia's. An adversarial reviewer caught
that the endpoint labels in that probe are a HARDCODED STRING in its own `HALLS` table — it reads
`collision` only and never touches a warp destination. So it proves the corridor's SHAPE and merely
ASSERTS its connectivity. That is the project's own "instrument the action, not the label" rule,
and I broke it.

This probe reads `MapData.warps` — the ROM's warp table — and follows the chain. Nothing here is
typed by me except the list of maps to dump.

CONTROLS: the chain is followed for SIDNEY/HALL1/PHOEBE too, where the answer is already MEASURED
LIVE (`ch24phoebe` drove SIDNEY -> HALL1 (5,12) -> PHOEBE). If this method reproduces that known
result it works; if it does not, the METHOD is broken, not the data.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE

context.emulator.load_save_state((REPO / "tools" / "story-dev" / "saves" / "post_phoebe_L75.ss1").read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

BAR = "=" * 100
CHAIN = [
    ("SIDNEY", MapRSE.EVER_GRANDE_CITY_SIDNEYS_ROOM),
    ("HALL1", MapRSE.EVER_GRANDE_CITY_HALL1),
    ("PHOEBE", MapRSE.EVER_GRANDE_CITY_PHOEBES_ROOM),
    ("HALL2", MapRSE.EVER_GRANDE_CITY_HALL2),
    ("GLACIA", MapRSE.EVER_GRANDE_CITY_GLACIAS_ROOM),
    ("HALL3", MapRSE.EVER_GRANDE_CITY_HALL3),
    ("DRAKE", MapRSE.EVER_GRANDE_CITY_DRAKES_ROOM),
]

print(BAR)
print("  THE E4 WARP CHAIN — destinations READ FROM THE ROM WARP TABLE, not from a label")
print(BAR)
for label, m in CHAIN:
    data = get_map_data(m, (0, 0))
    print(f"\n  {label:8s} {m.name}")
    for i, w in enumerate(data.warps):
        try:
            dest = MapRSE((w.destination_map_group, w.destination_map_number)).name
        except Exception:
            dest = f"({w.destination_map_group},{w.destination_map_number})"
        print(f"      warp {i}: tile {w.local_coordinates} elev {w.elevation}"
              f"  ->  {dest}  warp_id {w.destination_warp_id}")

print(f"\n{BAR}")
print("  WHAT THIS DECIDES")
print("    * HALL2 must show a warp -> PHOEBES_ROOM and a warp -> GLACIAS_ROOM. If it does, the")
print("      'PHOEBE -> GLACIA' endpoint claim is MEASURED rather than asserted.")
print("    * CONTROL: HALL1 must show SIDNEYS_ROOM + PHOEBES_ROOM, which is already driven LIVE.")
print(BAR)
