"""§Ch19 AREA ATLAS — the Mossdeep Space Center, Steven's house, and the ways in.

‼ WHY MEASURE WHAT A RESEARCH AGENT COULD JUST TELL US. Because this project's standing rule is that
an agent's output is a NOTE, never truth, and because the load-bearing facts here are coordinates —
exactly the class of claim that recall gets subtly wrong. Every number below is read from OUR ROM,
through the same accessors the bot itself uses, so a route built on it cannot disagree with what the
bot will see at runtime.

WHAT IT DUMPS, per map: the warp table (with each warp's destination resolved), and every object
event template (id, graphics, tile, trainer type, movement). Object templates live in ROM, so they
can be read for a map the player is not standing on — but ‼ they are the ORIGINAL positions and take
no account of `HIDE_` flags, so an object listed here may not be spawned. The hide flags are read
separately and printed alongside, which is what makes the listing actionable rather than misleading.

‼ THE GATE, MEASURED: the Space Center's Team Magma and Steven are hidden until the Mossdeep gym is
beaten. This probe prints those flags for the anchor it is run against, so the atlas always says
whether the NPCs it lists actually exist yet.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_space_center_recon.py
      PYTHONUTF8=1 py -3.12 probe_space_center_recon.py --anchor post_aqua.ss1
"""

import argparse
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
from modules.memory import get_event_flag, get_event_var
from modules.player import get_player_avatar

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_mossdeep_gym.ss1")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor

MAPS = [
    MapRSE.MOSSDEEP_CITY,
    MapRSE.MOSSDEEP_CITY_SPACE_CENTER_1F,
    MapRSE.MOSSDEEP_CITY_SPACE_CENTER_2F,
    MapRSE.MOSSDEEP_CITY_STEVENS_HOUSE,
]

GATE_FLAGS = [
    "HIDE_MOSSDEEP_CITY_TEAM_MAGMA",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_TEAM_MAGMA",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_TEAM_MAGMA",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_STEVEN",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_STEVEN",
]
PROGRESS_FLAGS = [
    "BADGE07_GET",
    "DEFEATED_MAGMA_SPACE_CENTER",
    "DEFEATED_GRUNT_SPACE_CENTER_1F",
    "INTERACTED_WITH_STEVEN_SPACE_CENTER",
    "RECEIVED_HM_DIVE",
    "ITEM_MOSSDEEP_STEVENS_HOUSE_HM08",
]

line = "=" * 100

context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(60):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
print(line)
print("§Ch19 AREA ATLAS — Mossdeep Space Center")
print(line)
print(f"\nanchor: {ANCHOR.name}")
print(f"player: {MapRSE(tuple(avatar.map_group_and_number)).name} {tuple(avatar.local_coordinates)}")

print("\n" + line)
print("THE GATE — are the Space Center NPCs even spawned yet?")
print(line)
print("\n  a HIDE_ flag reading True means the object is HIDDEN\n")
for name in GATE_FLAGS:
    print(f"  {name:<52} {get_event_flag(name)}")
print()
for name in PROGRESS_FLAGS:
    print(f"  {name:<52} {get_event_flag(name)}")
for var in ("MOSSDEEP_CITY_STATE", "MOSSDEEP_SPACE_CENTER_STATE", "STEVENS_HOUSE_STATE"):
    try:
        print(f"  VAR {var:<48} {get_event_var(var)}")
    except Exception as error:  # noqa: BLE001 — an unreadable var is REPORTED, never assumed 0
        print(f"  VAR {var:<48} <unreadable: {type(error).__name__}>")

for map_enum in MAPS:
    origin = get_map_data(map_enum, (0, 0))
    width, height = origin.map_size
    print("\n" + line)
    print(f"{map_enum.name}   ({width} x {height})")
    print(line)

    print("\n  WARPS")
    warps = origin.warps
    if not warps:
        print("    (none)")
    for index, warp in enumerate(warps):
        destination = (warp.destination_map_group, warp.destination_map_number)
        try:
            destination_name = MapRSE(destination).name
        except Exception:  # noqa: BLE001 — an unknown map is shown as its raw tuple, never hidden
            destination_name = f"?{destination}"
        # Resolve the arrival TILE, which is what a route actually needs.
        try:
            target_warps = get_map_data(destination, (0, 0)).warps
            arrival = (target_warps[warp.destination_warp_id].local_coordinates
                       if 0 <= warp.destination_warp_id < len(target_warps) else "?")
        except Exception:  # noqa: BLE001
            arrival = "?"
        print(f"    warp {index:>2} at {str(warp.local_coordinates):<9} -> {destination_name} "
              f"warp {warp.destination_warp_id} @ {arrival}")

    print("\n  OBJECT TEMPLATES  ‼ ROM positions; a HIDE_ flag may mean it is not spawned")
    templates = origin.objects
    if not templates:
        print("    (none)")
    for template in templates:
        print(f"    id {template.local_id:>3}  gfx {template.graphics_id:>3}  "
              f"{str(template.local_coordinates):<9} trainer={template.trainer_type:<20} "
              f"{template.movement_type}")

print("\n" + line)
print("NEXT")
print(line)
print("""
  Coordinates above are ROM ground truth and may be used to plan §Ch19 directly. What this probe
  does NOT tell you: which objects are spawned right now (cross-reference the HIDE_ flags), and
  what any of them DO (that is the scripts' business, not the map's).
""")
print(line)
