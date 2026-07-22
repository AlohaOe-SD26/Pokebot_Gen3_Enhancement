import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
import sys, pathlib
sys.path.insert(0, _SANDBOX)
from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom
p=load_profile_by_name("repro-fresh"); context.profile=p
context.config.load(p.path,strict=False); set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator
context.emulator=LibmgbaEmulator(p,lambda:None); context.audio=False; context.video=False
from modules.map import get_map_data
from modules.map_data import MapRSE
# Recon: what do Route104 warps (17,50) and (5,18) lead to, resolved properly?
md=get_map_data((MapRSE.ROUTE104.value[0],MapRSE.ROUTE104.value[1]),(0,0))
for w in md.warps:
    try:
        dl=w.destination_location
        print(f"WARP {w.local_coordinates} -> map={dl.map_group_and_number} name={dl.map_name}")
    except Exception as e:
        print(f"WARP {w.local_coordinates} -> ? {e}")
