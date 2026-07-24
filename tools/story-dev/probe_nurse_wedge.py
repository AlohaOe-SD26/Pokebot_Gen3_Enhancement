"""Probe the (7,4) nurse-approach wedge (gsc=True + waiting_input=True +
controllable=True + stale battle cb): which input clears BOTH the waiting
message and the parked script context, and what state follows?

Usage: python tools/story-dev/probe_nurse_wedge.py
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

STATE = (_REPO / "tools" / "story-dev" / "saves" / "ki15_nurse_wedge.ss1").read_bytes()

from modules.tasks import is_waiting_for_input, get_global_script_context, get_tasks
from modules.player import player_avatar_is_controllable
from modules.game import decode_string
from modules.memory import read_symbol, get_game_state


def snap():
    gsc = get_global_script_context()
    scripts = list(gsc.script_function_name or []) if hasattr(gsc, "script_function_name") else []
    return (str(get_game_state()), gsc.is_active, is_waiting_for_input(), player_avatar_is_controllable())


def trial(name, press_fn, frames=900):
    context.emulator.load_save_state(STATE)
    context.emulator.reset_held_buttons()
    changes = []
    last = snap()
    for i in range(frames):
        press_fn(i)
        context.emulator.run_single_frame()
        s = snap()
        if s != last:
            changes.append((i, s))
            last = s
            if len(changes) >= 8:
                break
    print(f"[{name}] changes: {changes if changes else 'NONE in ' + str(frames) + 'f'}")
    print(f"          final: gsc={last[1]} waiting={last[2]} controllable={last[3]}")
    context.emulator.reset_held_buttons()


# what script is parked?
context.emulator.load_save_state(STATE)
gsc = get_global_script_context()
try:
    print(f"[script] mode={gsc.mode} native={gsc.native_function_name} "
          f"bc={hex(gsc.bytecode_pointer)} stack={gsc.stack_depth}")
except Exception as e:
    print(f"[script] <err {e}>")
try:
    print(f"[tasks] {[t.symbol for t in get_tasks()]}")
except Exception as e:
    print(f"[tasks] <err {e}>")

trial("A-each-frame", lambda i: context.emulator.press_button("A"))
trial("B-each-frame", lambda i: context.emulator.press_button("B"))
trial("A-every-8f", lambda i: context.emulator.press_button("A") if i % 8 == 0 else None)
trial("nothing", lambda i: None, frames=400)
