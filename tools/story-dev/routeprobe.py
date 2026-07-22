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
context.emulator.load_save_state((_SAVES / "post_rival.ss1").read_bytes())
from modules.player import get_player_avatar
from modules.map_data import MapRSE
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.modes import BotModeError
# cross to Route 104 first
for _ in range(20): context.emulator.run_single_frame()
gen=None
def step_gen(g,n=400):
    for _ in range(n):
        try: next(g)
        except StopIteration: return True
        context.emulator.run_single_frame()
    return False
# walk south to cross
for i in range(45):
    context.emulator.set_inputs  # noop
    from modules.libmgba import input_map  # not needed
    context.emulator.press_button("Down")
    for _ in range(12): context.emulator.run_single_frame()
    pa=get_player_avatar()
    if pa.map_group_and_number==MapRSE.ROUTE104.value: break
pa=get_player_avatar(); print("on Route104 at", pa.local_coordinates)
# try navigating to candidate south tiles
for tile in [(5,19),(5,30),(5,50),(13,50),(17,49),(17,50),(17,55),(20,55),(11,44)]:
    context.emulator.load_save_state((_SAVES / "post_rival.ss1").read_bytes())
    for _ in range(20): context.emulator.run_single_frame()
    for i in range(45):
        context.emulator.press_button("Down")
        for _ in range(12): context.emulator.run_single_frame()
        if get_player_avatar().map_group_and_number==MapRSE.ROUTE104.value: break
    try:
        ok=step_gen(navigate_to_anywhere(MapRSE.ROUTE104, tile, avoid_encounters=False, avoid_scripted_events=False), 1500)
        pa=get_player_avatar()
        print(f"  nav->{tile}: {'REACHED' if ok else 'timeout'} now {pa.map_group_and_number} {pa.local_coordinates}")
    except BotModeError as e:
        print(f"  nav->{tile}: FAIL ({str(e)[:50]})")
    except Exception as e:
        print(f"  nav->{tile}: err {str(e)[:50]}")
