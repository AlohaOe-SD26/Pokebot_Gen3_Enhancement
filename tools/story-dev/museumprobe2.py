"""Reproduce + diagnose the Oceanic Museum "stuck at the greeter" loop.

Loads slateport.ss1 (the Ch8b anchor), runs the real `deliver_devon_goods_to_stern`
through the faithful loop, and once we are on MUSEUM 1F traces, every few frames, the
ON-SCREEN TEXT plus the script/task state — which is what actually identifies the
attendant dialogue we keep re-triggering.
"""

import pathlib as _pl
import sys

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-ml")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.emulator.load_save_state((_SAVES / "slateport.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.game import decode_string
from modules.map_data import MapRSE
from modules.memory import read_symbol
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.story.early_game import deliver_devon_goods_to_stern
from modules.tasks import get_global_script_context, get_immediate_script_context, get_tasks

M1F = MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F.value


def text():
    for sym in ("gStringVar4", "gDisplayedStringBattle"):
        try:
            s = decode_string(read_symbol(sym))
            if s and s.strip():
                return s.replace("\n", " | ")[:110]
        except Exception:
            pass
    return ""


gen = deliver_devon_goods_to_stern()
last = None
for frame in range(60000):
    try:
        next(gen)
    except StopIteration:
        print(f"f{frame}: generator finished")
        break
    except Exception as e:
        print(f"f{frame}: RAISED {type(e).__name__}: {e}")
        break
    context.emulator.run_single_frame()
    pa = get_player_avatar()
    if pa.map_group_and_number != M1F or frame % 20:
        continue
    gs = get_global_script_context()
    ims = get_immediate_script_context()
    sig = (
        tuple(pa.local_coordinates),
        str(pa.facing_direction),
        player_avatar_is_controllable(),
        gs.is_active,
        (gs.script_function_name, gs.native_function_name),
        ims.is_active,
        text(),
    )
    if sig != last:
        tasks = [t.symbol for t in get_tasks() if "Msg" in t.symbol or "Field" in t.symbol or "Multi" in t.symbol]
        print(f"f{frame}: pos={sig[0]} face={sig[1]} ctrl={sig[2]} gs={sig[3]}{sig[4]} "
              f"imm={sig[5]} tasks={tasks} text={sig[6]!r}")
        last = sig
