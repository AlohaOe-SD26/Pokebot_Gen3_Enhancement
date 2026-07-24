"""Load a captured stuck save state and print the exact readers that
_wait_until_cutscene_over / navigate_to see, over a few frames. Read-only.

Usage: python tools/story-dev/probe_stuck_state.py <state.ss1> [frames]
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

state_arg = sys.argv[1] if len(sys.argv) > 1 else "midstuck.ss1"
frames = int(sys.argv[2]) if len(sys.argv) > 2 else 12

# resolve the state path (saves/, tool dir, or absolute)
cands = [
    _pl.Path(state_arg),
    _REPO / "tools" / "story-dev" / "saves" / state_arg,
    BUILD / "profiles" / "repro-ml" / state_arg,
    BUILD / "profiles" / "repro-ml" / "states" / state_arg,
]
state_path = next((c for c in cands if c.is_file()), None)
assert state_path, f"state not found: {state_arg}"

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

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
context.emulator.load_save_state(state_path.read_bytes())
print(f"[loaded] {state_path}")

from modules.memory import get_game_state
from modules.tasks import get_global_script_context, get_immediate_script_context, is_waiting_for_input
from modules.player import player_avatar_is_controllable, player_avatar_is_standing_still, get_player_avatar
from modules.battle_state import get_current_battle_script_instruction, get_main_battle_callback, battle_is_active
from modules.game import decode_string
from modules.memory import read_symbol
from modules.story.early_game import _menu_task_active


def battle_text():
    try:
        return decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception as e:
        return f"<err {e}>"


for i in range(frames):
    gsc = get_global_script_context()
    isc = get_immediate_script_context()
    try:
        pos = tuple(get_player_avatar().local_coordinates)
    except Exception as e:
        pos = f"<err {e}>"
    print(
        f"f{i}: state={get_game_state()} pos={pos} ba={battle_is_active()} "
        f"controllable={player_avatar_is_controllable()} still={player_avatar_is_standing_still()} "
        f"gsc={gsc.is_active} isc={isc.is_active} waiting_input={is_waiting_for_input()} "
        f"menu={_menu_task_active()} cb={get_main_battle_callback()} "
        f"instr={get_current_battle_script_instruction()} bt={battle_text()!r}"
    )
    context.emulator.run_single_frame()
