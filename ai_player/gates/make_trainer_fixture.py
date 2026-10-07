"""TEST SIDE: build the TRAINER-battle fixture for live arms BT / BT2 (step 0.1, review finding 9).

    py -3.12 ai_player/gates/make_trainer_fixture.py [--out PATH]

WHY IT EXISTS: arm B proved the listener isolation on a WILD battle. The review asked for the
TRAINER path too (`BattleListener` turns every trainer battle into the bot's `DefaultBattleStrategy`),
on a fixture where a trainer battle is ACTIVE. A scan of all 175 saves in `tools/story-dev/saves/`
(2026-10-07) found none: every save whose battle-type flags say TRAINER sits in a menu inside the
battle (a party menu, a move-learn summary screen), where `BattleListener` never fires. The closest
is `evostall.ss1`: OVERWORLD on Route 116 with `EventScript_ShowTrainerIntroMsg` running, i.e. a
trainer has spotted the player and is talking. This script loads it in a throwaway emulator, taps A
until the battle starts, lets the battle intro play out with no input, and saves the state: a trainer
battle waiting at its first decision.

It prints the source md5, every press it made, and the result's md5, game state and battle-type flags,
so the fixture can be rebuilt and checked. The live driver pins the result by md5.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.host.launcher import resolve_build_root  # noqa: E402

SOURCE = REPO / "tools" / "story-dev" / "saves" / "evostall.ss1"
#: The output is pinned by md5 in `live_step0.py`. A rebuild need not reproduce those bytes (the save
#: state carries the real-time clock), so a rebuild means re-pinning, after inspecting the printout.
DEFAULT_OUT = Path(__file__).resolve().parent / "fixtures" / "trainer_battle_r116.ss1"
PROFILE = "ai-step0-fixture"
TAP_EVERY = 20
MAX_FRAMES_TO_BATTLE = 3000
SETTLE_FRAMES = 1200  # the battle intro (slide-in, "Trainer sent out", "Go!") plays without input
BATTLE_TYPE_TRAINER = 1 << 3


def build(out: Path) -> dict:
    build_root = resolve_build_root()
    sys.path.insert(0, str(build_root))
    from modules.context import context
    from modules.game import set_rom
    from modules.libmgba import LibmgbaEmulator
    from modules.profiles import load_profile_by_name

    profile = load_profile_by_name(PROFILE)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)
    context.audio = False
    context.video = False
    context.emulation_speed = 0

    from modules.memory import GameState, get_game_state, read_symbol, unpack_uint32

    source = SOURCE.read_bytes()
    emulator = context.emulator
    emulator.load_save_state(source)
    presses: list[int] = []
    frames = 0
    battle_at = None
    for frames in range(1, MAX_FRAMES_TO_BATTLE + 1):
        if get_game_state() == GameState.BATTLE:
            battle_at = frames
            break
        if frames % TAP_EVERY == 0:
            emulator.press_button("A")
            presses.append(emulator.get_frame_count())
        emulator.run_single_frame()
    if battle_at is None:
        raise SystemExit(f"no battle started within {MAX_FRAMES_TO_BATTLE} frames of tapping A")
    for _ in range(SETTLE_FRAMES):
        emulator.run_single_frame()
    state = get_game_state()
    flags = unpack_uint32(read_symbol("gBattleTypeFlags", size=4))
    data = emulator.get_save_state()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {
        "source": str(SOURCE.relative_to(REPO)),
        "source_md5": hashlib.md5(source).hexdigest(),
        "a_taps_at_frame_counts": presses,
        "battle_started_after_frames": battle_at,
        "settle_frames": SETTLE_FRAMES,
        "out": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out),
        "out_md5": hashlib.md5(data).hexdigest(),
        "frame_count": emulator.get_frame_count(),
        "game_state": state.name,
        "battle_type_flags": flags,
        "trainer_battle": bool(state == GameState.BATTLE and flags & BATTLE_TYPE_TRAINER),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build(args.out)
    print("FIXTURE " + json.dumps(result), flush=True)
    return 0 if result["trainer_battle"] else 1


if __name__ == "__main__":
    sys.exit(main())
