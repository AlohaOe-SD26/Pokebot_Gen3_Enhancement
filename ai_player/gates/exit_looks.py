"""TEST SIDE: the ROM's WARP TABLE against the exits the AI's eyes see by their LOOK (AI-player build step 3.1, the step-3
review's finding 5). Read only, in a throwaway emulator.

    py -3.12 ai_player/gates/exit_looks.py        prints one line: EXITS {json}

WHY: the eyes used to mark a tile a warp from the map's warp-event table (`host/eyes.py`, `location.warps`), which no
screen shows. Since step 3.1 a tile is an exit by its metatile BEHAVIOUR (`eyes/view.py` EXIT_BEHAVIORS: a door, stairs,
a ladder, an escalator, an arrow mat, a hole...), and the table is read only here. This scan says what that costs:

  1. THE GAME'S OWN RULE (`src/field_control_avatar.c`, typed below from the decomp, NOT from the eyes' table): a warp
     event fires on a step only for a tile whose behaviour passes IsWarpMetatileBehavior (a door, a ladder, an
     escalator, a non-animated door (+ water door, deep-south warp), the Lavaridge, Aqua Hideout, Mossdeep and Mt Pyre
     warps, and MB_BRIDGE_OVER_OCEAN for the Union Room), IsArrowWarpMetatileBehavior (the four arrows, the water arrow,
     the Shoal Cave entrance) or TryDoorWarp (an animated door, going north); a cracked floor drops the player
     (`MetatileBehavior_IsCrackedFloorHole`). Every one of those looks must be in the eyes' table but the Union Room's
     (its behaviour is the bridges' too: 608 bridge tiles on Routes 110 and 119 would turn into walls).
  2. THE v1 MAPS (New Game to Petalburg: every map whose name starts LITTLEROOT_TOWN, OLDALE_TOWN, PETALBURG_CITY,
     ROUTE101, ROUTE102, ROUTE103): EVERY warp tile there must LOOK like an exit, so the AI sees every way out it can use.
  3. THE WHOLE ROM, for the record: how many warp tiles look like exits, which looks the rest have (each checked NOT to
     be a look the game warps on: they are places scripts, Fly, Dig or Dive put the player), and how many exit-looking
     tiles have no warp (closed doors: the AI tries one, nothing happens, it remembers it closed: `world/memory.py`).
  FAULT-TEST of check 2: the same scan with SOUTH_ARROW_WARP taken out of the eyes' table (the doormats) must fail it.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.eyes.view import BEHAVIOR_NAMES, EXIT_BEHAVIORS  # noqa: E402
from ai_player.gates.probe_eyes import RomMaps, boot  # noqa: E402

PROFILE = "ai-step0-fixture"
#: The game's step-warp looks, by name (`src/field_control_avatar.c`, `src/metatile_behavior.c`; module docstring, 1).
GAME_STEP_WARP_LOOKS = frozenset({
    "ANIMATED_DOOR", "LADDER", "UP_ESCALATOR", "DOWN_ESCALATOR", "NON_ANIMATED_DOOR", "WATER_DOOR", "DEEP_SOUTH_WARP",
    "LAVARIDGE_GYM_B1F_WARP", "LAVARIDGE_GYM_1F_WARP", "AQUA_HIDEOUT_WARP", "MT_PYRE_HOLE", "MOSSDEEP_GYM_WARP",
    "BRIDGE_OVER_OCEAN", "NORTH_ARROW_WARP", "SOUTH_ARROW_WARP", "EAST_ARROW_WARP", "WEST_ARROW_WARP",
    "WATER_SOUTH_ARROW_WARP", "SHOAL_CAVE_ENTRANCE", "CRACKED_FLOOR_HOLE",
})
#: The one step-warp look the eyes leave out on purpose (module docstring, 1).
LEFT_OUT = frozenset({"BRIDGE_OVER_OCEAN"})
V1_PREFIXES = ("LITTLEROOT_TOWN", "OLDALE_TOWN", "PETALBURG_CITY", "ROUTE101", "ROUTE102", "ROUTE103")


def name_of(value: int) -> str:
    return BEHAVIOR_NAMES[value] if 0 <= value < len(BEHAVIOR_NAMES) else f"INVALID_{value:02X}"


def scan(exit_looks: frozenset[int]) -> dict:
    from modules.context import context
    from modules.map_data import MapRSE

    rom = RomMaps(context.emulator)
    looks = {name_of(v) for v in exit_looks}
    total = recognised = no_warp = 0
    unrecognised: collections.Counter = collections.Counter()
    examples: dict[str, list] = collections.defaultdict(list)
    v1: list[dict] = []
    step_warps_missed: list = []
    maps = 0
    for member in MapRSE:
        key = tuple(member.value)
        try:
            events, layout = rom.events(key), rom.layout(key)
        except Exception:  # noqa: BLE001 - a map the table does not hold
            continue
        maps += 1
        warps = set(events["warps"])
        for x, y in sorted(warps):
            tile = rom.tile(key, x, y)
            look = name_of(tile["behavior"]) if tile else "(outside the layout)"
            total += 1
            seen = look in looks
            recognised += seen
            if not seen:
                unrecognised[look] += 1
                if len(examples[look]) < 4:
                    examples[look].append(f"{member.name} ({x},{y})")
                if look in GAME_STEP_WARP_LOOKS - LEFT_OUT:
                    step_warps_missed.append(f"{member.name} ({x},{y}) {look}")
            if member.name.startswith(V1_PREFIXES):
                v1.append({"map": member.name, "tile": [x, y], "look": look, "seen": seen})
        for y in range(layout["height"]):
            for x in range(layout["width"]):
                if (x, y) not in warps and name_of(rom.tile(key, x, y)["behavior"]) in looks:
                    no_warp += 1
    return {"maps": maps, "warp_tiles": total, "recognised": recognised, "unrecognised": dict(unrecognised.most_common()),
            "unrecognised_examples": dict(examples), "exit_looks_without_a_warp": no_warp, "v1": v1,
            "v1_not_seen": [w for w in v1 if not w["seen"]], "step_warps_missed": step_warps_missed,
            "game_looks_not_in_the_eyes": sorted(GAME_STEP_WARP_LOOKS - LEFT_OUT - looks)}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    boot(PROFILE)
    real = scan(EXIT_BEHAVIORS)
    without_mats = frozenset(v for v in EXIT_BEHAVIORS if name_of(v) != "SOUTH_ARROW_WARP")
    fault = scan(without_mats)
    out = {**real, "fault_without_doormats": {"v1_not_seen": len(fault["v1_not_seen"]),
                                               "not_seen": [[w["map"], w["tile"]] for w in fault["v1_not_seen"]],
                                               "examples": [f"{w['map']} {w['tile']}" for w in fault["v1_not_seen"][:4]]}}
    print("EXITS " + json.dumps(out, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
