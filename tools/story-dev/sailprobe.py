import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
import sys, pathlib
sys.path.insert(0, _SANDBOX)
from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom
p = load_profile_by_name("repro-fresh"); context.profile=p
context.config.load(p.path, strict=False); set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator
context.emulator = LibmgbaEmulator(p, lambda: None); context.audio=False; context.video=False
context.emulator.load_save_state((_SAVES / "post_rival.ss1").read_bytes())
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.map_data import MapRSE
# settle
for _ in range(30): context.emulator.run_single_frame()
def pos():
    pa=get_player_avatar(); return pa.map_group_and_number, pa.local_coordinates, pa.facing_direction
print("start:", pos(), "controllable", player_avatar_is_controllable())
# walk south, logging each step
prev=None
for i in range(40):
    context.emulator.press_button("Down")
    for _ in range(10): context.emulator.run_single_frame()
    m,c,f = pos()
    if (m,c)!=prev:
        print(f"step{i}: map={m} pos={c} facing={f}")
        prev=(m,c)
    if m == MapRSE.ROUTE104.value:
        print("*** crossed onto ROUTE 104 ***"); break
print("end:", pos())
