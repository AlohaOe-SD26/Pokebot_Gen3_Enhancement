"""Probe the captured after-faint PARTY_MENU wedge (livetest 20260724-004252/run05,
saved as ki17_partymenu_wedge.ss1): print the exact menu internals the state-aware
sweep reads (tasks / cursor / party HP), then trial inputs to find what advances it.
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

STATE = (_REPO / "tools/story-dev/saves/ki17_partymenu_wedge.ss1").read_bytes()
context.emulator.load_save_state(STATE)

from modules.memory import get_game_state, GameState, read_symbol
from modules.tasks import get_tasks, get_global_script_context, is_waiting_for_input
from modules.pokemon_party import get_party
from modules.battle_state import get_current_battle_script_instruction, get_main_battle_callback
from modules.menuing import get_party_menu_cursor_pos
from modules.game import decode_string


def snap(tag=""):
    try:
        tasks = [t.symbol for t in get_tasks()]
    except Exception as e:
        tasks = f"<err {e}>"
    try:
        cursor = get_party_menu_cursor_pos(len(get_party()))
    except Exception as e:
        cursor = f"<err {e}>"
    try:
        hp = [(m.species.name, m.current_hp) for m in get_party() if m is not None]
    except Exception as e:
        hp = f"<err {e}>"
    try:
        bt = decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        bt = "?"
    print(f"{tag} state={get_game_state()} tasks={tasks} cursor={cursor}")
    print(f"{tag}   hp={hp} waiting={is_waiting_for_input()} instr={get_current_battle_script_instruction()} bt={bt!r}")


snap("[t0]")
for i in range(12):
    context.emulator.run_single_frame()
snap("[t12 idle]")

def trial(name, presses, frames=400):
    context.emulator.load_save_state(STATE)
    context.emulator.reset_held_buttons()
    start_state = str(get_game_state())
    n = 0
    for i in range(frames):
        b = presses(i)
        if b:
            context.emulator.press_button(b)
        context.emulator.run_single_frame()
        if str(get_game_state()) != start_state:
            print(f"[{name}] game_state CHANGED at frame {i}: {get_game_state()}")
            snap(f"[{name}]")
            return
    print(f"[{name}] no state change in {frames}f")
    snap(f"[{name}]")


trial("A-every-8f", lambda i: "A" if i % 8 == 0 else None)
trial("B-every-8f", lambda i: "B" if i % 8 == 0 else None)
trial("Down-then-A", lambda i: ("Down" if (i // 8) % 4 < 2 else "A") if i % 8 == 0 else None)
trial("nothing", lambda i: None, frames=200)
