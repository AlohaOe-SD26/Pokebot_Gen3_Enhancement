"""TEST SIDE: run one of the AI's HANDS brains in a throwaway emulator, in this process (build step 2).

    py -3.12 ai_player/gates/hands_harness.py BRAIN [--state PATH | --fresh] [--seed N] [--frames N]
                                              [--fault ungated_a|blind_count] [--mart-count N] [--clock HH:MM]
                                              [--save-end PATH] [--run-dir DIR] [--record PATH]
                 BUILD STEP 3, the world brains (explore, roam, goto): [--goal-map MAP] [--roam-steps N]
                                              [--goto 'x,y;x,y'] [--world-in world.jsonl] [--intent-frames N] [--no-crop]
    prints one line: HANDS {json}
    py -3.12 ai_player/gates/hands_harness.py truth STATE      (the second-path truth of a saved state: TRUTH {json})

WHY IT EXISTS: a run through the real launcher (`py -3.12 -m ai_player run`) is the PROOF (the purity
instrument counts every press, write, load and frame, `gates/live_step2.py`), but it costs ~30 s of start-up.
This harness runs the SAME brain (`ai_player.mode.HandsBrain`, the AI's own eyes, hands and skills) against the
framework's emulator in-process, pressing through a test-side `Controls` with the controller's exact
semantics (`ai_player/host/controller.py`: `hold` presses until released, one frame per `yield`), so the
hands can be developed and recorded quickly. It is ALSO what the fixture builders use to play a stretch of
the game with the AI's own hands (`gates/make_clock_fixture.py`). Nothing here is evidence of purity.

AFTER THE RUN it reads, by a SECOND PATH (the probe's own decoders, `gates/probe_eyes.py`, and the framework's
party reader, never the eyes' bytes or code): the player's name and gender (save block 2: playerName[8] @0,
playerGender @8, decoded by the probe's charmap), the party's HP (`get_party()`), the money and the bag
(`probe_eyes.own_progress`: save block 1 XOR the key), the map. These go into the HANDS line as `truth`.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.probe_eyes import _u32, boot, own_progress, own_text  # noqa: E402

PROFILE = "ai-step0-fixture"
#: `include/global.h` struct SaveBlock2: playerName[PLAYER_NAME_LENGTH + 1 = 8] @0, playerGender @8,
#: localTimeOffset (struct Time: s16 days, s8 hours, s8 minutes, s8 seconds) @0x98.
SB2_NAME, SB2_NAME_SIZE, SB2_GENDER, SB2_LOCAL_TIME_OFFSET = 0x00, 8, 0x08, 0x98
#: `include/global.h` struct SaveBlock1: flags[] @0x1270, vars[] @0x139C (from VARS_START 0x4000).
SB1_FLAGS, SB1_VARS, VARS_START = 0x1270, 0x139C, 0x4000
#: `include/constants/flags.h` FLAG_SET_WALL_CLOCK 0x51; `vars.h` VAR_LITTLEROOT_INTRO_STATE 0x4092.
FLAG_SET_WALL_CLOCK, VAR_LITTLEROOT_INTRO_STATE = 0x51, 0x4092
#: `include/constants/items.h` ITEM_POKE_BALL = 4; `include/item.h` struct Item (0x2C bytes): price @0x10.
ITEM_POKE_BALL, ITEM_SIZE, ITEM_PRICE = 4, 0x2C, 0x10
#: BUILD STEP 3: `include/global.h` SaveBlock1.gameStats @0x159C, SaveBlock2.encryptionKey @0xAC; the stats read.
SB1_GAME_STATS, SB2_ENCRYPTION_KEY = 0x159C, 0xAC
GAME_STATS = {"steps": 5, "total_battles": 7, "wild_battles": 8, "trainer_battles": 9}


class HarnessControls:
    """The brain's `Controls` on the throwaway emulator, with `host/controller.py`'s semantics: `tap` presses for
    one frame and leaves one released; `hold` holds until released, even if interrupted; one frame per `yield`
    (the harness runs the frame after each `next`)."""

    def __init__(self, emulator) -> None:
        self.emulator = emulator
        self.presses = 0

    def wait(self, frames: int):
        for _ in range(frames):
            yield

    def tap(self, button: str):
        self.emulator.press_button(button)
        self.presses += 1
        yield
        yield

    def hold(self, button: str, frames: int):
        self.emulator.hold_button(button)
        self.presses += 1
        try:
            for _ in range(frames):
                yield
        finally:
            self.emulator.release_button(button)


def truth(context) -> dict:
    """The end state by a second path (see the module docstring)."""
    from modules.memory import get_game_state, read_symbol
    from modules.pokemon_party import get_party

    emulator = context.emulator
    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    raw_name = bytes(emulator.read_bytes(sb2 + SB2_NAME, SB2_NAME_SIZE))
    gender = emulator.read_bytes(sb2 + SB2_GENDER, 1)[0]
    location = emulator.read_bytes(sb1 + 4, 2)
    out = {"frame": emulator.get_frame_count(), "game_state": get_game_state().name, "name": own_text(raw_name),
           "name_bytes": raw_name.hex(), "gender": gender, "gender_name": {0: "BOY", 1: "GIRL"}.get(gender, "?"),
           "map": [location[0], location[1]]}
    try:
        party = get_party()
        out["party"] = [[m.species.name, m.current_hp, m.total_hp] for m in party]
        # (the step-3 verifier's second round) each party Pokemon's IDENTITY and total experience, by the framework's
        # own decoder (`Pokemon.personality_value`, `Pokemon.total_exp`): the XP arm's second path for the eyes' claim
        out["party_exp"] = [[f"{m.personality_value:08x}", m.species.name, m.total_exp, m.level] for m in party]
    except Exception as error:  # noqa: BLE001
        out["party"] = f"unreadable: {type(error).__name__}: {error}"
    try:
        progress = own_progress(context, sb1, sb2)
        out["money"] = progress["money"]
        out["balls"] = {e["name"]: e["quantity"] for e in progress["bag"]["poke_balls"]}
        out["flags"] = progress["flags"]
    except Exception as error:  # noqa: BLE001
        out["money"] = f"unreadable: {type(error).__name__}: {error}"
    # the wall clock: its flag and the intro's state variable (save block 1), the game's own local time
    # (`gLocalTime`, `src/rtc.c`: RtcInitLocalTimeOffset sets it to the time set) and the stored offset
    flag_byte = emulator.read_bytes(sb1 + SB1_FLAGS + FLAG_SET_WALL_CLOCK // 8, 1)[0]
    out["FLAG_SET_WALL_CLOCK"] = bool(flag_byte >> (FLAG_SET_WALL_CLOCK % 8) & 1)
    out["VAR_LITTLEROOT_INTRO_STATE"] = int.from_bytes(
        emulator.read_bytes(sb1 + SB1_VARS + 2 * (VAR_LITTLEROOT_INTRO_STATE - VARS_START), 2), "little")
    local = bytes(read_symbol("gLocalTime", 0, 5))
    offset = bytes(emulator.read_bytes(sb2 + SB2_LOCAL_TIME_OFFSET, 5))

    def as_time(raw: bytes) -> list[int]:
        return [int.from_bytes(raw[0:2], "little", signed=True)] + [b - 256 if b >= 128 else b for b in raw[2:5]]

    out["gLocalTime"] = as_time(local)
    out["localTimeOffset"] = as_time(offset)
    # BUILD STEP 3 (`gates/live_step3.py`): the player's tile (save block 1 `pos`, s16 x and y @0) and the game's OWN
    # counters of steps and battles (`include/global.h` SaveBlock1.gameStats[] @0x159C, each u32 XOR'd with save
    # block 2's encryptionKey @0xAC: `src/overworld.c` GetGameStat; `include/constants/game_stat.h` GAME_STAT_STEPS 5,
    # GAME_STAT_TOTAL_BATTLES 7, GAME_STAT_WILD_BATTLES 8, GAME_STAT_TRAINER_BATTLES 9), never the AI's eyes.
    pos = bytes(emulator.read_bytes(sb1, 4))
    out["pos"] = [int.from_bytes(pos[0:2], "little", signed=True), int.from_bytes(pos[2:4], "little", signed=True)]
    key = int.from_bytes(bytes(emulator.read_bytes(sb2 + SB2_ENCRYPTION_KEY, 4)), "little")
    stats = bytes(emulator.read_bytes(sb1 + SB1_GAME_STATS, 4 * 10))
    out["game_stats"] = {name: int.from_bytes(stats[4 * index:4 * index + 4], "little") ^ key
                         for name, index in GAME_STATS.items()}
    item = read_symbol("gItems", ITEM_POKE_BALL * ITEM_SIZE, ITEM_SIZE)
    out["rom_poke_ball"] = {"name": own_text(item[:14]), "price": int.from_bytes(item[ITEM_PRICE:ITEM_PRICE + 2], "little")}
    return out


def truth_of(state: Path) -> dict:
    """`truth` of a saved state, loaded into a throwaway emulator (`gates/live_step2.py` reads the state a run left)."""
    context = boot(PROFILE)
    data = state.read_bytes()
    context.emulator.load_save_state(data)
    result = truth(context)
    result["state_md5"] = __import__("hashlib").md5(data).hexdigest()
    return result


class RecordingEyes:
    """The AI's eyes, plus a RECORDER: every look whose screen changed (the menu, its cursor, whether it takes
    input, the wait and its reason, the page of text) is kept as `{frame, screen, player}`, the screen as
    `Observation.to_dict()` writes it. `gates/test_hands.py` replays these RECORDED screens (`--record`)."""

    def __init__(self, eyes) -> None:
        self.eyes = eyes
        self.records: list[dict] = []
        self._last = None

    def look(self):
        look = self.eyes.look()
        screen = look.screen
        ui = screen.ui
        key = (screen.game_state, screen.waits_for_button, screen.wait_reason, screen.script_running, screen.controls_locked,
               None if ui is None else (ui.kind, ui.cursor, ui.accepts_input, ui.cursor_xy, ui.text, ui.page, ui.hours,
                                        ui.minutes, ui.quantity), screen.text if screen.waits_for_button or ui else None)
        if key != self._last:
            self._last = key
            data = look.to_dict()
            player = data.get("player")
            self.records.append({"frame": look.frame, "screen": data["screen"],
                                 "player": None if player is None else {k: player[k] for k in ("map_const", "x", "y", "facing", "settling")}})
        return look


def play(context, brain: str, seed: int, frames: int, run_dir: Path, fault: str | None = None,
         mart_count: int | None = None, clock: str | None = None, personality: str | None = None,
         record: Path | None = None, world: dict | None = None) -> dict:
    """Run the hands brain `brain` on the already booted emulator of `context`, one frame per `next`. BUILD STEP 3:
    `world` holds the world brains' options (goal_map, roam_steps, goto, world_in, intent_frames, no_crop)."""
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.mode import BrainSettings, HandsBrain
    from ai_player.options import DEFAULT_MART_COUNT, DEFAULT_MART_ITEM, DEFAULT_ROAM_STEPS, HandsOptions, parse_tiles

    emulator = context.emulator
    world = world or {}
    clock_value = tuple(int(p) for p in clock.split(":")) if clock else None
    options = HandsOptions(brain=brain, run_dir=run_dir, seed=seed, personality=personality, mart_item=DEFAULT_MART_ITEM,
                           mart_count=mart_count or DEFAULT_MART_COUNT, clock=clock_value,
                           fault_ungated_a=fault == "ungated_a", fault_blind_count=fault == "blind_count",
                           goal_map=world.get("goal_map"), roam_steps=world.get("roam_steps") or DEFAULT_ROAM_STEPS,
                           goto=parse_tiles(world.get("goto") or ""),
                           world_in=Path(world["world_in"]) if world.get("world_in") else None,
                           intent_frames=world.get("intent_frames"))
    lines: list[str] = []
    brain_object = HandsBrain(BrainSettings(frames=frames), lines.append, options)
    controls = HarnessControls(emulator)
    eyes = FrameworkEyes(crop=not world.get("no_crop"))
    eyes = RecordingEyes(eyes) if record is not None else eyes
    started = time.monotonic()
    steps = brain_object.play(controls, eyes)
    reason = None
    count = 0
    while True:
        try:
            next(steps)
        except StopIteration as done:
            reason = done.value
            break
        emulator.run_single_frame()
        count += 1
        if count > frames + 10:
            reason = "harness: the brain overran its budget"
            break
    if record is not None:
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps({"brain": brain, "seed": seed, "fault": fault, "reason": reason,
                                      "records": eyes.records}, ensure_ascii=False), encoding="utf-8")
    return {"brain": brain, "seed": seed, "fault": fault, "reason": reason, "frames": count,
            "seconds": round(time.monotonic() - started, 1), "presses": controls.presses, "lines": lines,
            "actions": str(run_dir / "actions.jsonl"), "world_file": str(run_dir / "world.jsonl")}


def run(brain: str, state: Path | None, seed: int, frames: int, fault: str | None, mart_count: int | None,
        clock: str | None, run_dir: Path, save_end: Path | None, personality: str | None = None,
        record: Path | None = None, world: dict | None = None) -> dict:
    context = boot(PROFILE)
    emulator = context.emulator
    if state is not None:
        emulator.load_save_state(state.read_bytes())
    start_truth = truth(context) if state is not None else None
    result = play(context, brain, seed, frames, run_dir, fault, mart_count, clock, personality, record, world)
    end = truth(context)
    if save_end is not None:
        save_end.parent.mkdir(parents=True, exist_ok=True)
        save_end.write_bytes(emulator.get_save_state())
    return {**result, "start_truth": start_truth, "truth": end, "saved_end": str(save_end) if save_end else None}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) == 3 and sys.argv[1] == "truth":
        print("TRUTH " + json.dumps(truth_of(Path(sys.argv[2])), ensure_ascii=False), flush=True)
        return 0
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("brain", choices=("intro", "nurse", "mart", "clock", "explore", "roam", "goto"))
    parser.add_argument("--goal-map", help="step 3, explore: the map constant to reach")
    parser.add_argument("--roam-steps", type=int, help="step 3, roam: training steps")
    parser.add_argument("--goto", help="step 3, goto: 'x,y;x,y'")
    parser.add_argument("--world-in", help="step 3: a world.jsonl to start from")
    parser.add_argument("--intent-frames", type=int, help="step 3: the intent's own budget")
    parser.add_argument("--no-crop", action="store_true", help="step 3 FAULT: the eyes see the whole map (AI_PLAYER_FAULT_NO_CROP)")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--frames", type=int, default=20000)
    parser.add_argument("--fault", choices=("ungated_a", "blind_count"))
    parser.add_argument("--mart-count", type=int)
    parser.add_argument("--clock")
    parser.add_argument("--personality")
    parser.add_argument("--save-end", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--record", type=Path, help="write every changed screen the eyes saw (for gates/test_hands.py)")
    args = parser.parse_args()
    if args.state is None and not args.fresh:
        parser.error("--state PATH or --fresh")
    run_dir = args.run_dir or Path(tempfile.mkdtemp(prefix="ai_hands_"))
    world = {"goal_map": args.goal_map, "roam_steps": args.roam_steps, "goto": args.goto, "world_in": args.world_in,
             "intent_frames": args.intent_frames, "no_crop": args.no_crop}
    result = run(args.brain, args.state, args.seed, args.frames, args.fault, args.mart_count, args.clock, run_dir,
                 args.save_end, args.personality, args.record, world)
    print("HANDS " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
