"""Against the (14,5) 'Got away safely!' battle-return wedge, try each input
strategy for a bounded window and report whether it clears waiting_input /
advances the main battle callback off ReturnFromBattleToOverworld.

Usage: python tools/story-dev/probe_press_variants.py
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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

STATE = (BUILD / "profiles" / "repro-ml" / "current_state.ss1").read_bytes()

from modules.tasks import is_waiting_for_input
from modules.battle_state import get_main_battle_callback, battle_is_active
from modules.player import player_avatar_is_controllable
from modules.game import decode_string
from modules.memory import read_symbol, get_game_state


def snap():
    try:
        bt = decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        bt = "?"
    return (str(get_game_state()), battle_is_active(), player_avatar_is_controllable(),
            is_waiting_for_input(), get_main_battle_callback(), bt)


def trial(name, press_fn, frames=600):
    context.emulator.load_save_state(STATE)
    context.emulator.reset_held_buttons()
    before = snap()
    for i in range(frames):
        press_fn(i)
        context.emulator.run_single_frame()
        s = snap()
        if not s[3] or s[4] != "ReturnFromBattleToOverworld":
            print(f"[{name}] CHANGED at frame {i}: waiting_input={s[3]} cb={s[4]} bt={s[5]!r}")
            context.emulator.reset_held_buttons()
            return
    context.emulator.reset_held_buttons()
    after = snap()
    print(f"[{name}] no change after {frames}f: waiting_input={after[3]} cb={after[4]}")


print(f"[start] {snap()}")
trial("press-A-each-frame", lambda i: context.emulator.press_button("A"))
trial("press-B-each-frame", lambda i: context.emulator.press_button("B"))
trial("A-every-other", lambda i: context.emulator.press_button("A") if i % 2 == 0 else None)
trial("hold-A", lambda i: context.emulator.hold_button("A"))
trial("mash-AB", lambda i: context.emulator.press_button("A" if i % 2 else "B"))
trial("do-nothing", lambda i: None, frames=300)
