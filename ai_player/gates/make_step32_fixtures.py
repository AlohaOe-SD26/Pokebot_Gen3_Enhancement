"""TEST SIDE: the two MEMORIES of the step-4 verifier's round's live arms for step 3.2's findings 3 and 5 (`gates/live_step3.py`
FORGET, REOPEN and their reverts). The verifier: "Findings 3 (bump forgotten) and 5 (doors reopen on visible news) are proven
only by unit tests and mutants ... No live arm walks back through a bumped way or meets a closed door."

    py -3.12 ai_player/gates/make_step32_fixtures.py [--only bumps|closed]

Each memory is the AI's OWN: a `goto` walk of its own navigator (`hands_harness.py` run, Story, seed 3, the cartridge's
clock pinned) from a step-3 fixture, its `world.jsonl` last line kept. Then ONE thing is PLANTED, test side, and printed:
what a person who had been there before would remember, which no early map of the game gives the AI to learn itself.
  house_2f_bumps.world.jsonl    from `house_2f_clockset.ss1` (the player's room, md5 pinned), errand (0, 4): the room seen.
                                PLANTED: the tile (0, 5), a one-tile gap between the room's left wall and the wall at (1, 5),
                                learned blocked going DOWN and going UP (one bump each, `BUMP_GIVE_UP` is 2: dear, not
                                refused), as if someone had stood there. The game lets the player through both ways (measured:
                                errands (0, 4) -> (0, 6) -> (0, 4) walk through it, 2 steps each). WHY BOTH: the errand INTO
                                (0, 5) then has no cheaper way in than a retry from above (from below it is 6 steps round plus
                                the same retry), and the errand past it is the A/B: through it 2 steps once the bump is
                                forgotten, round it 6 while it is remembered (a retry costs `BUMP_RETRY_COST`, 10).
  littleroot_closed.world.jsonl from `littleroot_twin.ss1` (Littleroot after the first walk out, VAR_LITTLEROOT_TOWN_STATE 0,
                                md5 pinned), errand (9, 9): May's house's door (14, 8) seen. PLANTED: that door remembered
                                CLOSED (`MapMemory.closed`, with the memory's news count then, 0), as if it had not opened on
                                an earlier visit. The memory has heard no words. The twin's words are news a person sees;
                                a door found closed is worth a try again after news (`world/memory.py` _reopen), and May's
                                house is where the explorer meets May, whose news lets it past the twin (arm SCENEX).
Each is written with a `.build.json` printout: the walk, the truth at its end, what was planted, the md5s.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import run  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GAME_CLOCK = "2026-10-08T06:00"
HOUSE = (FIXTURES / "house_2f_clockset.ss1", "2cc0b61450870d34646f7583bfd0c787")
TWIN = (FIXTURES / "littleroot_twin.ss1", "fe4661736a30dd3f34b87c0db7ae1d10")
BUMPS = FIXTURES / "house_2f_bumps.world.jsonl"
CLOSED = FIXTURES / "littleroot_closed.world.jsonl"
#: the planted bumps: (tile, the side it was bumped from, the direction) on the player's room (map 1:1)
BUMP_TILE, BUMP_MAP = (0, 5), "1:1"
#: the planted closed door: May's house's door on Littleroot (map 0:9)
DOOR_TILE, DOOR_MAP = (14, 8), "0:9"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def check(source: tuple[Path, str]) -> None:
    if md5(source[0]) != source[1]:
        raise SystemExit(f"{source[0]} has md5 {md5(source[0])}, pinned {source[1]}")


def walk(source: tuple[Path, str], errands: str) -> tuple[dict, dict]:
    """The AI's own goto walk; returns (the harness result, the memory's last snapshot)."""
    check(source)
    run_dir = Path(tempfile.mkdtemp(prefix="ai_step32_fix_"))
    result = run("goto", source[0], 3, 3000, None, None, None, run_dir, None, "Story", None, {"goto": errands}, GAME_CLOCK)
    lines = [line for line in (run_dir / "world.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return result, json.loads(lines[-1])


def last_frame(memory: dict) -> int:
    return max(int(fact[4]) for data in memory["maps"].values() for fact in data["tiles"].values())


def build_bumps() -> dict:
    result, memory = walk(HOUSE, "0,4")
    room = memory["maps"][BUMP_MAP]
    key = f"{BUMP_TILE[0]},{BUMP_TILE[1]}"
    known = key in room["tiles"] and not set(room["tiles"][key][0]) & set("bwdp")
    frame = last_frame(memory)
    planted = {}
    for direction, frm in (("down", [0, 4]), ("up", [0, 6])):
        planted[f"{key}|{direction}"] = {"from": frm, "direction": direction, "first": frame, "bumps": 1, "last": frame,
                                         "planted": "test side (make_step32_fixtures.py): as if someone had stood there"}
    room["bumped"].update(planted)
    BUMPS.write_text(json.dumps(memory, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    out = {"world": str(BUMPS.relative_to(REPO)), "from": str(HOUSE[0].relative_to(REPO)), "from_md5": HOUSE[1],
           "played": "the AI's own navigator (hands_harness run: brain goto, errand (0, 4), Story, seed 3, clock pinned "
                     f"{GAME_CLOCK})", "reason": result["reason"], "frames": result["frames"], "presses": result["presses"],
           "truth": result["truth"], "planted": planted, "tile_known_walkable": known,
           "bumps_in_memory": sorted(room["bumped"]), "md5": md5(BUMPS), "ok": result["reason"].startswith("goto: done") and known}
    (FIXTURES / "house_2f_bumps.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def build_closed() -> dict:
    result, memory = walk(TWIN, "9,9")
    town = memory["maps"][DOOR_MAP]
    key = f"{DOOR_TILE[0]},{DOOR_TILE[1]}"
    fact = town["tiles"].get(key)
    door = fact is not None and ("d" in fact[0] or "p" in fact[0])
    planted = {"frame": last_frame(memory), "how": "planted (test side, make_step32_fixtures.py): as if it had not opened on "
                                                    "an earlier visit", "news": int(memory.get("news") or 0)}
    town["closed"][key] = planted
    CLOSED.write_text(json.dumps(memory, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    out = {"world": str(CLOSED.relative_to(REPO)), "from": str(TWIN[0].relative_to(REPO)), "from_md5": TWIN[1],
           "played": "the AI's own navigator (hands_harness run: brain goto, errand (9, 9), Story, seed 3, clock pinned "
                     f"{GAME_CLOCK})", "reason": result["reason"], "frames": result["frames"], "presses": result["presses"],
           "truth": result["truth"], "planted": {key: planted}, "door_seen": fact, "door_looks_like_an_exit": door,
           "news": memory.get("news"), "heard": memory.get("heard"), "md5": md5(CLOSED),
           "ok": result["reason"].startswith("goto: done") and door and not memory.get("heard")}
    (FIXTURES / "littleroot_closed.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("bumps", "closed"))
    args = parser.parse_args()
    ok = True
    for name, build in (("bumps", build_bumps), ("closed", build_closed)):
        if args.only not in (None, name):
            continue
        out = build()
        ok &= bool(out["ok"])
        print(f"{name}: {json.dumps({k: v for k, v in out.items() if k not in ('truth',)}, ensure_ascii=False)[:1500]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
