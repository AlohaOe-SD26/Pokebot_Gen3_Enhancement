# -*- coding: utf-8 -*-
"""⛔ CAN A GRIND INSIDE VICTORY ROAD HEAL AT ALL? (`#24-cavehealblind`, `#24-levelgap`)

WHY THIS EXISTS. A §Ch24 production grind must run on Victory Road ground (every L30+ wild ground in
Emerald is a cave/dungeon — `training_areas.py:30-49`) and heal at a Poké Center OUTSIDE it. That
makes a heal a CAVE ROUND TRIP, and ✅ **neither `_CAVE_EXITS` nor `_CAVE_ENTRANCES` knows Victory
Road** — both tables hold exactly GRANITE_CAVE_1F and FIERY_PATH (`early_game.py:2003-2012`,
`:2039-2046`). `_exit_training_cave_if_inside` is therefore *"a cheap no-op"* there, and the return
trip in `_goto_training_area` falls straight through to `_navigate_riding_out`.

⇒ THE QUESTION THIS ANSWERS: does `calculate_path` — the thing `_navigate_riding_out` ultimately
depends on — actually connect the Victory Road grind tile to the Ever Grande Poké Center, IN BOTH
DIRECTIONS? If it does not, a §Ch24 grind cannot heal, and no amount of frame budgeting fixes that.

⛔⛔ WHAT THIS IS *NOT*. `calculate_path` PLANS; it does not walk. A plan is necessary, not
sufficient. And ‼ MEASURED 2026-09-18 (`#24-league2f`): **a cross-map request whose endpoints are on
different maps is REFUSED outright** — *"are not on connected maps (note that warps don't count.)"* —
so a bare cross-map ask proves nothing about reachability. This probe therefore asks BOTH shapes and
reports them separately, because only one of them is a fair question.

⛔ READ-ONLY: it loads save states and plans routes. Nothing is walked, nothing is written.
"""
import pathlib as _pl
import sys

sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.map_data import MapRSE, PokemonCenter
from modules.map_path import calculate_path
from modules.player import get_player_avatar
from modules.story import victory_road as VR

SAVES = (_pl.Path(__file__).resolve().parent / "saves")

#: The only training spot constant in the module (`victory_road.py:477`).
TRAIN_SPOT_1F = VR.TRAIN_SPOT_1F            # (VICTORY_ROAD_1F, (15, 39))
#: Where `train_team` would heal — `map_data.py:1537`, and ‼ it is a DOOR tile.
PC_DOOR = PokemonCenter.EvergrandeCity.value

CASES = [
    ("post_wally.ss1", "post-Wally, inside Victory Road \u2014 the grind's real start state"),
    ("post_ever_grande.ss1", "OUTDOORS at Ever Grande \u2014 the control"),
    ("post_ch24_atdoor_L75.ss1", "OUTDOORS at the League door \u2014 a second control"),
]

print("=" * 116)
print("CAN A VICTORY-ROAD GRIND HEAL?  \u2014 planning only, nothing is walked")
print("=" * 116)
print(f"  grind tile   : {TRAIN_SPOT_1F[0].name} {TRAIN_SPOT_1F[1]}")
print(f"  heal target  : {PC_DOOR[0].name} {PC_DOOR[1]}   \u203c a DOOR tile \u2014 see the note at the end")


def ask(src_map, src_tile, dst_map, dst_tile, label):
    """One planning question, reported honestly whichever way it goes."""
    try:
        path = calculate_path((src_map, src_tile), (dst_map, dst_tile))
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        msg = str(error)
        kind = ("REFUSED-AS-MALFORMED" if "not on connected maps" in msg else "NO PATH")
        print(f"      {label:52} \u21d2 {kind}: {type(error).__name__}: {msg[:88]}")
        return None
    maps = sorted({tuple(w.map) for w in path})
    warps = sum(1 for w in path if w.is_warp)
    print(f"      {label:52} \u21d2 OK, {len(path):4} wp, {warps} warp(s), maps={maps}")
    return path


for name, note in CASES:
    p = SAVES / name
    if not p.exists():
        print(f"\n  {name}: MISSING")
        continue
    context.emulator.load_save_state(p.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    av = get_player_avatar()
    here_map_val = tuple(av.map_group_and_number)
    try:
        here_map = MapRSE(here_map_val)
    except ValueError:
        print(f"\n  {name}: unknown map {here_map_val}")
        continue
    here = VR._here_tile()
    print(f"\n  {name}  \u2014  {here_map.name} {here}")
    print(f"      {note}")

    # A. the SAME-MAP shape: can it reach the grind tile on its own floor?
    if here_map is TRAIN_SPOT_1F[0]:
        ask(here_map, here, TRAIN_SPOT_1F[0], TRAIN_SPOT_1F[1], "A. same-map -> the grind tile")
    else:
        print(f"      {'A. same-map -> the grind tile':52} \u21d2 n/a (not on that floor)")

    # B. the CROSS-MAP shape `_navigate_riding_out` is handed for a heal.
    #    \u203c This is the shape MEASURED to be refused outright when the maps are not connected;
    #    report it, but do NOT read a refusal here as "the bot is trapped".
    ask(here_map, here, PC_DOOR[0], PC_DOOR[1], "B. cross-map -> the Poke Center DOOR")

    # C. the same ask aimed at the tile IN FRONT of the door, which is how this project
    #    words a liveness check (walking to a DOOR tile ends you INSIDE the building).
    ask(here_map, here, PC_DOOR[0], (PC_DOOR[1][0], PC_DOOR[1][1] + 1),
        "C. cross-map -> the tile in FRONT of that door")

print("\n" + "-" * 116)
print("  \u203c HOW TO READ THIS, AND THE TRAP IT IS BUILT AROUND:")
print("    \u2022 A `REFUSED-AS-MALFORMED` line means the PLANNER declined the QUESTION (endpoints on")
print("      unconnected maps; warps are not connections). That is NOT evidence the bot is stuck \u2014")
print("      it is evidence the ask was the wrong shape. Express cross-map travel as per-map")
print("      segments that STEP ONTO the warp tile (measured 2026-09-18, `#24-league2f`).")
print("    \u2022 `NO PATH` on a SAME-MAP ask is a real reachability answer.")
print("    \u2022 \u26d4 A successful plan is still only a PLAN. `_navigate_riding_out` rides out scripted")
print("      scenes and retries; only a drive proves a heal round trip.")
print("=" * 116)
