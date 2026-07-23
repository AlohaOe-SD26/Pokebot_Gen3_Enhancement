"""Regenerate rocksmash_taught.ss1 in a CLEAN, controllable overworld (user report
2026-07-23: the committed checkpoint was saved in the BAG_MENU, so loading it as a
milestone lands in a menu). Load rocksmash_got (HM06 in bag, before the teach), teach
Rock Smash to a valid learner, normalize to the overworld, verify, and overwrite the
checkpoint. Backs up the old file first and round-trip-verifies the new one.
"""

import pathlib as _pl
import sys

_SAVES = _pl.Path(__file__).resolve().parent / "saves"
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False


def drive(gen, cap=40000):
    frames = 0
    try:
        while frames < cap:
            next(gen)
            frames += 1
            context.emulator.run_single_frame()
    except StopIteration:
        pass
    return frames


def clean_state():
    from modules.memory import GameState, get_game_state
    from modules.player import get_player_avatar, player_avatar_is_controllable
    from modules.story.early_game import _menu_task_active
    from modules.pokemon_party import get_party

    knows = any(
        learned is not None and learned.move.name == "Rock Smash"
        for mon in get_party()
        if mon is not None and not mon.is_egg
        for learned in mon.moves
    )
    pa = get_player_avatar()
    return {
        "knows_rock_smash": knows,
        "state": get_game_state().name,
        "controllable": player_avatar_is_controllable(),
        "menu": _menu_task_active(),
        "pos": tuple(pa.local_coordinates),
        "map": pa.map_group_and_number,
    }


# --- Load the pre-teach checkpoint and run the teach. ---
context.emulator.load_save_state((_SAVES / "rocksmash_got.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.items import get_item_by_name
from modules.story.early_game import ensure_hm_learner, normalize_to_overworld, teach_hm_move

hm06 = get_item_by_name("HM06")
slot = drive(ensure_hm_learner(hm06)) and None  # noqa — ensure_hm_learner returns via StopIteration value
# ensure_hm_learner returns the slot as its StopIteration value; capture it properly:


def run_returning(gen, cap=40000):
    frames = 0
    value = None
    try:
        while frames < cap:
            next(gen)
            frames += 1
            context.emulator.run_single_frame()
    except StopIteration as stop:
        value = stop.value
    return value


context.emulator.load_save_state((_SAVES / "rocksmash_got.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
slot = run_returning(ensure_hm_learner(hm06))
print(f"learner slot: {slot}")
drive(teach_hm_move(hm06, slot))
drive(normalize_to_overworld())

state = clean_state()
print("post-teach state:", state)
assert state["knows_rock_smash"], "teach failed — party does not know Rock Smash"
assert state["state"] == "OVERWORLD" and state["controllable"] and not state["menu"], f"not a clean overworld: {state}"

# --- Back up the old file, write the new one, round-trip verify. ---
target = _SAVES / "rocksmash_taught.ss1"
backup = _SAVES / "rocksmash_taught.ss1.menu-bak"
if target.exists() and not backup.exists():
    backup.write_bytes(target.read_bytes())
    print(f"backed up old (menu) state -> {backup.name}")
target.write_bytes(context.emulator.get_save_state())
print(f"wrote new {target.name}")

# Reload the freshly written file and confirm it opens clean.
context.emulator.load_save_state(target.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
verify = clean_state()
print("round-trip verify:", verify)
assert verify["knows_rock_smash"] and verify["state"] == "OVERWORLD" and verify["controllable"] and not verify["menu"], (
    f"round-trip check failed: {verify}"
)
print("SUCCESS: rocksmash_taught.ss1 now loads to a clean, controllable overworld with Rock Smash known.")
