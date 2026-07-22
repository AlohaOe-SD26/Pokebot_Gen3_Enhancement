import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
import sys, pathlib
sys.path.insert(0, _SANDBOX)
from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom
p = load_profile_by_name("repro-fresh"); context.profile = p
context.config.load(p.path, strict=False); set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator
context.emulator = LibmgbaEmulator(p, lambda: None); context.audio=False; context.video=False
context.emulator.load_save_state((_SAVES / "post_rival.ss1").read_bytes())
for _ in range(3): context.emulator.run_single_frame()
from modules.map import get_map_data
from modules.map_data import MapRSE

MAPS = ["ROUTE104","ROUTE104_MR_BRINEYS_HOUSE","DEWFORD_TOWN","DEWFORD_TOWN_GYM",
        "DEWFORD_TOWN_POKEMON_CENTER_1F","DEWFORD_TOWN_HALL",
        "ROUTE106","GRANITE_CAVE_1F","GRANITE_CAVE_B1F","GRANITE_CAVE_B2F","GRANITE_CAVE_STEVENS_ROOM",
        "ROUTE107","ROUTE108","ROUTE109","ROUTE109_SEASHORE_HOUSE",
        "SLATEPORT_CITY","SLATEPORT_CITY_POKEMON_CENTER_1F","SLATEPORT_CITY_MART",
        "SLATEPORT_CITY_HARBOR","SLATEPORT_CITY_OCEANIC_MUSEUM_1F","SLATEPORT_CITY_OCEANIC_MUSEUM_2F"]

def sym(o):
    for a in ("script_symbol","local_id"):
        try:
            v=getattr(o,a)
            if v: return f"{a}={v}"
        except Exception: pass
    return "?"

out=[]
for name in MAPS:
    try:
        m=getattr(MapRSE,name); md=get_map_data((m.value[0],m.value[1]),(0,0))
    except Exception as e:
        out.append(f"\n### {name}: ERR {e}"); continue
    out.append(f"\n### {name} {m.value} size={md.map_size}")
    try:
        for c in md.connections:
            d=getattr(c,'direction',None) or getattr(c,'_direction',None) or '?'
            out.append(f"  CONN {d} offset={getattr(c,'offset','?')} -> {c.destination_map.map_name}")
    except Exception as e: out.append(f"  conn err {e}")
    for w in md.warps:
        try: out.append(f"  WARP {w.local_coordinates} -> {w.destination_location.map_name} #{w.destination_warp_id}")
        except Exception as e: out.append(f"  WARP {w.local_coordinates} -> ? ({e})")
    for o in md.objects:
        try:
            s=sym(o)
            if "BerryTree" not in s: out.append(f"  OBJ {o.local_coordinates} {s}")
        except Exception as e: out.append(f"  OBJ ? ({e})")
txt="\n".join(out)
(_pl.Path(__file__).resolve().parent / "recon_dewford_slateport.txt").write_text(txt, encoding="utf-8")
print(txt)
