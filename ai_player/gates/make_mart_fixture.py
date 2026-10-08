"""TEST SIDE: build the MART fixture for build step 2's MART arm: the player inside the Rustboro Poke Mart, in
front of the clerk's counter.

    py -3.12 ai_player/gates/make_mart_fixture.py [--out PATH]

WHY IT EXISTS: no save in `tools/story-dev/saves/` stands in a mart. So this script MAKES one by PLAYING from
`tools/story-dev/saves/rustboro.ss1` (Rustboro City (20,42), ₽6680, 5 Poke Balls in the bag; its md5 is pinned
below) with ordinary button presses in a throwaway emulator (no memory write): it walks a fixed route of
single steps to the mart's door (`data/maps/RustboroCity/map.json`: the warp at (16,45) to
MAP_RUSTBORO_CITY_MART), goes in, and walks to the tile across the counter from the clerk
(`data/maps/RustboroCity_Mart/map.json`: the clerk, OBJ_EVENT_GFX_MART_EMPLOYEE, at (1,3) facing right).

Each step is one direction HELD until the player's tile changes (read from save block 1 `pos` by this file,
never by the AI's eyes), at most 40 frames, then a settle; a step that does not move the player aborts the
build. The script stops on the target tile, facing UP, the way it walked (NOT toward the clerk, who is to the
left: turning to the clerk is the AI's job), saves the state, and prints what it did and where it ended: map,
tile, facing, money, the balls, every object on the map (the clerk's included), so the fixture's documentation
is a printout, not a claim.
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

from ai_player.gates.probe_eyes import _s16, _u32, boot, own_progress  # noqa: E402

SOURCE = REPO / "tools" / "story-dev" / "saves" / "rustboro.ss1"
SOURCE_MD5 = "9585924eba83f2e18bfbf371787841ff"  # pinned here (rustboro.ss1 is not in FIXTURES.md5)
DEFAULT_OUT = Path(__file__).resolve().parent / "fixtures" / "mart_rustboro.ss1"
PROFILE = "ai-step0-fixture"
#: Rustboro (20,42) -> left 6 -> (14,42), down 4 -> (14,46), right 2 -> (16,46), up -> the door (16,45) = the mart.
#: Inside: the arrival tile, then the route to the counter (filled in from the map, checked by the walk).
OUTSIDE = ["Left"] * 6 + ["Down"] * 4 + ["Right"] * 2 + ["Up"]
STEP_FRAMES, SETTLE_FRAMES, WARP_FRAMES = 40, 12, 240
MART_MAP = (11, 7)  # data/maps/map_groups.json: RustboroCity_Mart is group 11, number 7 (checked below)


def place(context) -> tuple[tuple[int, int], tuple[int, int], int]:
    """Save block 1 pos and location, and the player object's facing (raw)."""
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    raw = context.emulator.read_bytes(sb1, 6)
    avatar = read_symbol("gPlayerAvatar", size=0x24)
    me = read_symbol("gObjectEvents", avatar[5] * 0x24, 0x24)
    return (_s16(raw, 0), _s16(raw, 2)), (raw[4], raw[5]), me[0x18] & 0x0F


def step(context, button: str, log: list) -> None:
    emulator = context.emulator
    before, where, _ = place(context)
    emulator.hold_button(button)
    moved = False
    for _ in range(STEP_FRAMES):
        emulator.run_single_frame()
        now, there, _ = place(context)
        if now != before or there != where:
            moved = True
            break
    emulator.release_button(button)
    for _ in range(SETTLE_FRAMES):
        emulator.run_single_frame()
    after, there, _ = place(context)
    log.append([emulator.get_frame_count(), button, list(before), list(after), list(there)])
    if not moved:
        raise SystemExit(f"step {button} from {before} on map {where} did not move the player: {log}")


def settle_warp(context, log: list) -> None:
    from modules.memory import get_game_state

    for _ in range(WARP_FRAMES):
        context.emulator.run_single_frame()
    log.append([context.emulator.get_frame_count(), "settle", get_game_state().name, list(place(context)[1])])


def build(out: Path) -> dict:
    data = SOURCE.read_bytes()
    md5 = hashlib.md5(data).hexdigest()
    if md5 != SOURCE_MD5:
        raise SystemExit(f"{SOURCE.name} md5 {md5} is not the pinned {SOURCE_MD5}")
    context = boot(PROFILE)
    emulator = context.emulator
    emulator.load_save_state(data)
    for _ in range(4):
        emulator.run_single_frame()
    log: list = []
    start = place(context)
    for button in OUTSIDE:
        step(context, button, log)
    settle_warp(context, log)
    arrived = place(context)
    if arrived[1] != MART_MAP:
        raise SystemExit(f"after the door the map is {arrived[1]}, not the mart {MART_MAP}: {log}")
    # Inside: walk up the left aisle to the tile across the counter from the clerk (x 3, y 3), the clerk at (1,3).
    x, y = arrived[0]
    while x > 3:
        step(context, "Left", log)
        x = place(context)[0][0]
    while y > 3:
        step(context, "Up", log)
        y = place(context)[0][1]
    for _ in range(SETTLE_FRAMES):
        emulator.run_single_frame()
    end = place(context)
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    progress = own_progress(context, sb1, sb2)
    from modules.map import get_map_objects

    objects = [{"local_id": o.local_id, "graphics_id": o.graphics_id, "xy": list(o.current_coords)} for o in get_map_objects()]
    state = emulator.get_save_state()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(state)
    return {"source": str(SOURCE.relative_to(REPO)), "source_md5": md5, "start": [list(start[0]), list(start[1])],
            "steps": log, "end": {"pos": list(end[0]), "map": list(end[1]), "facing_raw": end[2]},
            "money": progress["money"], "balls": {e["name"]: e["quantity"] for e in progress["bag"]["poke_balls"]},
            "objects": objects, "out": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out),
            "out_md5": hashlib.md5(state).hexdigest()}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build(args.out)
    print("FIXTURE " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
