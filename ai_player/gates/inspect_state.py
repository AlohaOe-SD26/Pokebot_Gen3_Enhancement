"""TEST SIDE: read a saved emulator state and print what the game looks like, as one JSON line.

    py -3.12 ai_player/gates/inspect_state.py --profile NAME [--state PATH]

WHY IT EXISTS: a purity arm that reads `foreign_presses=0` only means something if the framework
listeners HAD something to act on (CLAUDE.md session rule 4: assert something the run does not
already satisfy). The live driver therefore inspects the state the run LEFT BEHIND (the emulator
writes `current_state.ss1` on shutdown): with the listeners kept, the bot fought the wild battle and
the game is back in the overworld; with them removed, the battle is still waiting. Likewise the
cheats arm reads the money the cheat would have written.

This file is test side (`ai_player/gates/`): it may use the framework to GRADE the AI, and the purity
gate forbids any play-loop file from importing it. It loads the state into a throwaway emulator
(`is_test_run=True`: no profile state is loaded, no shutdown state is written).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.platform.launcher import STATE_FILE, resolve_build_root  # noqa: E402


def inspect(profile_name: str, state_path: Path | None) -> dict:
    build_root = resolve_build_root()
    sys.path.insert(0, str(build_root))

    from modules.context import context
    from modules.game import set_rom
    from modules.libmgba import LibmgbaEmulator
    from modules.profiles import load_profile_by_name

    profile = load_profile_by_name(profile_name)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)
    context.audio = False
    context.video = False
    context.emulation_speed = 0

    from modules.memory import GameState, decrypt32, get_game_state, get_save_block, unpack_uint32
    from modules.player import get_player_avatar

    path = state_path or profile.path / STATE_FILE
    context.emulator.load_save_state(path.read_bytes())
    context.emulator.run_single_frame()

    state = get_game_state()
    money_offset = 0x490 if context.rom.is_rse else 0x290
    money = decrypt32(unpack_uint32(get_save_block(1, money_offset, 4)))
    result: dict = {
        "state_file": str(path),
        "game_state": state.name,
        "in_battle": state in (GameState.BATTLE, GameState.BATTLE_STARTING, GameState.BATTLE_ENDING),
        "money": money,
    }
    try:
        avatar = get_player_avatar()
        result["map"] = avatar.map_location.map_name
        result["xy"] = list(avatar.local_coordinates)
    except Exception as error:  # noqa: BLE001 - not every state has an avatar (title screen)
        result["map"] = f"unreadable: {type(error).__name__}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", required=True)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    print("INSPECT " + json.dumps(inspect(args.profile, args.state)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
