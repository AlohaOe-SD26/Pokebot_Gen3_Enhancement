import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
import pathlib
import sys
sys.path.insert(0, _SANDBOX)
from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom
profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)
from modules.libmgba import LibmgbaEmulator
context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False; context.video = False
context.emulator.load_save_state((_SAVES / "pokenav_got.ss1").read_bytes())
from modules.map import get_map_data
from modules.map_data import MapRSE

MAPS = ["ROUTE104","ROUTE104_MR_BRINEYS_HOUSE","DEWFORD_TOWN","DEWFORD_TOWN_GYM",
        "GRANITE_CAVE_1F","GRANITE_CAVE_B1F","GRANITE_CAVE_B2F","GRANITE_CAVE_STEVENS_ROOM"]

def sym(o):
    for a in ("script_symbol","script","local_id"):
        try:
            v = getattr(o, a)
            if v: return f"{a}={v}"
        except Exception: pass
    return "?"

for name in MAPS:
    m = getattr(MapRSE, name)
    try:
        md = get_map_data((m.value[0], m.value[1]), (0,0))
    except Exception as e:
        print(f"=== {name}: ERR {e}"); continue
    print(f"\n===== {name} {m.value} size={md.map_size} =====")
    try:
        for c in md.connections:
            print(f"  CONN {c.direction if hasattr(c,'direction') else '?'} offset={getattr(c,'offset','?')} -> {c.destination_map.map_name}")
    except Exception as e:
        print(f"  conn err {e}")
    for w in md.warps:
        try:
            print(f"  WARP {w.local_coordinates} -> {w.destination_location.map_name} warp#{w.destination_warp_id}")
        except Exception as e:
            print(f"  WARP {w.local_coordinates} -> ? ({e})")
    for o in md.objects:
        try:
            print(f"  OBJ {o.local_coordinates} {sym(o)}")
        except Exception as e:
            print(f"  OBJ ? ({e})")
