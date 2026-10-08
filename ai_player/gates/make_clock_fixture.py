"""TEST SIDE: build the CLOCK fixture for build step 2's CLOCK arm: a New Game played from a fresh boot to the
player's own room, standing under the stopped wall clock.

    py -3.12 ai_player/gates/make_clock_fixture.py [--out PATH] [--seed N]

WHY IT EXISTS: the clock is set in the intro's FIRST scene after the truck, and no save in `tools/story-dev/
saves/` stands there (`pokedex_done.ss1` and later saves have long set it). Step 2 has no navigator, so the AI
cannot walk there itself yet (step 3). This script MAKES the fixture by PLAYING, in a throwaway emulator, with
button presses only (no memory write):
  1. the AI's OWN intro skill (`gates/hands_harness.py` play, brain `intro`, the pinned seed: the same code
     as the INTRO arm) from a fresh boot to the truck;
  2. then, by this file's own presses: wait for the truck to stop (a Right press moves the player only once
     it has), walk out of it (the dynamic warp at x 4), press A ONLY while the AI's eyes say the game waits
     (Mom's scenes outside and in the hall: "Isn't it nice in here?", "go set the clock"), walk to the stairs
     and up them, and walk to the tile under the clock: (5, 2) in the boy's room, (3, 2) in the girl's
     (`data/maps/LittlerootTown_{Brendans,Mays}House_2F/map.json` bg event WallClock at (5, 1) / (3, 1)).
     Walking is one step at a time on a breadth-first path over the tiles the AI's eyes report on screen
     (blocked tiles and people are walls), each step one direction held until the tile changes (read from
     save block 1 `pos` by this file);
  3. it stops on that tile facing the way it walked in (not the clock: turning to the clock is the AI's job),
     saves the state, and prints every press, every step and the end: map, tile, facing,
     `VAR_LITTLEROOT_INTRO_STATE` (5: "entered 2F to set clock", `data/maps/LittlerootTown/scripts.inc`),
     `FLAG_SET_WALL_CLOCK` (still clear), the player's name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import play, truth  # noqa: E402
from ai_player.gates.probe_eyes import _s16, _u32, boot  # noqa: E402

DEFAULT_OUT = Path(__file__).resolve().parent / "fixtures" / "clock_room.ss1"
PROFILE = "ai-step0-fixture"
DEFAULT_SEED = 7  # the AI's choices for seed 7: Catcher, BOY, "Rowan" (ai_player/personality.py)
STEP_FRAMES, SETTLE_FRAMES, PRESS_GAP = 40, 10, 10
#: include/constants/vars.h VAR_LITTLEROOT_INTRO_STATE = 0x4092; flags.h FLAG_SET_WALL_CLOCK = 0x51.
VAR_LITTLEROOT_INTRO_STATE, FLAG_SET_WALL_CLOCK = 0x4092, 0x51
#: include/global.h struct SaveBlock1: flags[] @0x1270, vars[VARS_COUNT] @0x139C (u16 each, from VARS_START 0x4000).
SB1_VARS, SB1_FLAGS, VARS_START = 0x139C, 0x1270, 0x4000
ROOMS = {"LITTLEROOT_TOWN_BRENDANS_HOUSE_2F": (5, 2), "LITTLEROOT_TOWN_MAYS_HOUSE_2F": (3, 2)}
STAIRS = {"LITTLEROOT_TOWN_BRENDANS_HOUSE_1F": (8, 2), "LITTLEROOT_TOWN_MAYS_HOUSE_1F": (2, 2)}
DIRS = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}


class Walker:
    def __init__(self, context) -> None:
        from ai_player.host.eyes import FrameworkEyes

        self.context = context
        self.emulator = context.emulator
        self.eyes = FrameworkEyes()
        self.log: list = []

    def frame(self, count: int = 1) -> None:
        for _ in range(count):
            self.emulator.run_single_frame()

    def pos(self) -> tuple[tuple[int, int], tuple[int, int]]:
        from modules.memory import read_symbol

        sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
        raw = self.emulator.read_bytes(sb1, 6)
        return (_s16(raw, 0), _s16(raw, 2)), (raw[4], raw[5])

    def step(self, button: str) -> bool:
        before = self.pos()
        self.emulator.hold_button(button)
        moved = False
        for _ in range(STEP_FRAMES):
            self.frame()
            if self.pos() != before:
                moved = True
                break
        self.emulator.release_button(button)
        self.frame(SETTLE_FRAMES)
        self.log.append([self.emulator.get_frame_count(), "step", button, list(before[0]), list(self.pos()[0]), moved])
        return moved

    def gated_scenes(self, done, budget: int) -> None:
        """Press A only on the frames the AI's eyes say the game waits for a button, until `done(look)`."""
        last = -PRESS_GAP
        for index in range(budget):
            look = self.eyes.look()
            if done(look):
                return
            if look.screen.waits_for_button and look.screen.ui is None and index - last >= PRESS_GAP:
                self.emulator.press_button("A")
                self.log.append([look.frame, "A", look.screen.wait_reason])
                last = index
            self.frame()
        raise SystemExit(f"the scenes did not end within {budget} frames: {self.log[-12:]}")

    def walk_to(self, target: tuple[int, int], budget: int = 60) -> None:
        """Breadth-first over the on-screen tiles (blocked tiles and objects are walls), one step at a time."""
        for _ in range(budget):
            look = self.eyes.look()
            player = look.player
            if player is None or player.x is None or look.view is None:
                self.frame()
                continue
            here = (player.x, player.y)
            if here == target:
                return
            walls = {(t.x, t.y) for row in look.view.rows for t in row if t.blocked}
            walls |= {(o.x, o.y) for o in look.view.objects if o.source == "object"}
            tiles = {(t.x, t.y) for row in look.view.rows for t in row}
            first = {}
            queue = deque([here])
            seen = {here}
            while queue:
                x, y = queue.popleft()
                if (x, y) == target:
                    break
                for button, (dx, dy) in DIRS.items():
                    nxt = (x + dx, y + dy)
                    if nxt in seen or nxt not in tiles or (nxt in walls and nxt != target):
                        continue
                    seen.add(nxt)
                    first[nxt] = first.get((x, y), button)
                    queue.append(nxt)
            goal = target
            if goal not in first:
                # off screen (or not reachable on screen): walk toward the reachable tile nearest to it
                if not first:
                    raise SystemExit(f"no step possible from {here}: {look.view.ascii()}")
                goal = min(first, key=lambda t: (abs(t[0] - target[0]) + abs(t[1] - target[1]), t))
                if abs(goal[0] - target[0]) + abs(goal[1] - target[1]) >= abs(here[0] - target[0]) + abs(here[1] - target[1]):
                    raise SystemExit(f"no way closer to {target} from {here}: {look.view.ascii()}")
            self.step(first[goal])
        raise SystemExit(f"did not reach {target} in {budget} steps")


def var_and_flag(context) -> tuple[int, bool]:
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    value = int.from_bytes(context.emulator.read_bytes(sb1 + SB1_VARS + 2 * (VAR_LITTLEROOT_INTRO_STATE - VARS_START), 2), "little")
    flags = context.emulator.read_bytes(sb1 + SB1_FLAGS + FLAG_SET_WALL_CLOCK // 8, 1)[0]
    return value, bool(flags >> (FLAG_SET_WALL_CLOCK % 8) & 1)


def build(out: Path, seed: int) -> dict:
    context = boot(PROFILE)
    intro = play(context, "intro", seed, 30000, Path(tempfile.mkdtemp(prefix="ai_clockfix_")))
    if not str(intro["reason"]).startswith("intro: in the truck"):
        raise SystemExit(f"the AI's intro did not reach the truck: {intro['reason']}")
    walker = Walker(context)
    # 1. the truck: Right moves the player only once the truck has stopped; then out through x = 4.
    for _ in range(120):
        if walker.step("Right"):
            break
        walker.frame(30)
    else:
        raise SystemExit("the truck never let the player move")
    start_map = walker.pos()[1]
    for _ in range(6):
        if walker.pos()[1] != start_map:
            break
        walker.step("Right")
    # 2. Mom's scenes, outside and in the hall, until Mom has said to set the clock (VAR_LITTLEROOT_INTRO_STATE 4,
    #    read by this file) and the player is free in the house.
    def free_in_house(look) -> bool:
        p = look.player
        return (p is not None and p.map_const in STAIRS and var_and_flag(context)[0] == 4 and not look.screen.script_running
                and not look.screen.controls_locked and look.screen.ui is None and not look.screen.waits_for_button
                and not look.screen.text_box_open)
    walker.gated_scenes(free_in_house, 6000)
    house = walker.eyes.look().player.map_const
    walker.walk_to(STAIRS[house])
    walker.frame(240)
    look = walker.eyes.look()
    room = look.player.map_const if look.player else None
    if room not in ROOMS:
        raise SystemExit(f"up the stairs is {room}, not the player's room")
    walker.walk_to(ROOMS[room])
    walker.frame(SETTLE_FRAMES)
    end = walker.eyes.look()
    state_value, clock_set = var_and_flag(context)
    data = context.emulator.get_save_state()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"seed": seed, "intro": {k: intro[k] for k in ("reason", "frames", "presses")}, "walk": walker.log,
            "end": {"map": end.player.map_const, "pos": [end.player.x, end.player.y], "facing": end.player.facing,
                    "signs_in_view": [(o.dx, o.dy) for o in end.view.objects if o.kind == "sign"] if end.view else None},
            "VAR_LITTLEROOT_INTRO_STATE": state_value, "FLAG_SET_WALL_CLOCK": clock_set, "truth": truth(context),
            "out": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out), "out_md5": hashlib.md5(data).hexdigest()}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    result = build(args.out, args.seed)
    print("FIXTURE " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result["VAR_LITTLEROOT_INTRO_STATE"] == 5 and not result["FLAG_SET_WALL_CLOCK"] else 1


if __name__ == "__main__":
    sys.exit(main())
