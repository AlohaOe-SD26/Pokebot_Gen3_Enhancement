"""KI-58, second pass: flood-fill the Mossdeep Gym instead of eyeballing it or asking the planner.

‼ WHY THIS EXISTS, AND WHY KI-58's FIRST EXPLANATION WAS WRONG. KI-58 said the gym does not yield
to the warp-graph method because its tiles carry `MB_MOSSDEEP_GYM_WARP`, "a distinct behaviour"
whose destination comes from gym-specific logic. **The decomp says otherwise.** In
`src/field_control_avatar.c` that behaviour sits in the same `IsWarpMetatileBehavior` list as
`MetatileBehavior_IsAquaHideoutWarp` — the panels my graph already modelled correctly — and
`DoMossdeepGymWarp()` (`src/field_screen_effect.c:559`) is an ordinary warp with a different fade
and `SKIP_OBJECT_EVENT_LOAD`:

    SetObjectEventLoadFlag(SKIP_OBJECT_EVENT_LOAD); LockPlayerFieldControls(); SaveObjectEvents();
    TryFadeOutOldMapMusic(); WarpFadeOutScreen(); PlaySE(SE_WARP_IN);
    CreateTask(Task_WarpAndLoadMap, 10); gFieldCallback = FieldCB_MossdeepGymWarpExit;

The DESTINATION is still the warp event's. So the warp model was right and the real question is the
one KI-58 skipped: **why do two of the walks fail?** The chain in KI-58 was hand-read off an ASCII
collision map by eye, which is exactly the kind of evidence that produces a confident wrong story.

WHAT THIS DOES INSTEAD: its own flood fill over `collision == 0`, from a given tile, treating warp
tiles as **enterable but terminal** — you may step onto a panel, you may not walk THROUGH it,
because stepping on it warps you. That is the precise notion a warp maze needs, and it does not
depend on `calculate_path`'s quirks at all. It then reports, per component, which warp tiles it can
touch — i.e. the real adjacency of the warp graph.

‼ CONTROLS:
  * PLANNER AGREEMENT — for a sample of pairs, the flood's verdict must not contradict
    `calculate_path`. Two independent models agreeing is the point; where they disagree the
    disagreement itself is the finding, and it is printed rather than hidden.
  * KNOWN-GOOD control — `(6,34) -> (1,33)` plans in 10 wp (measured 2026-08-12), so the flood must
    put them in the same component. If it does not, the flood is wrong and nothing here is usable.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_components.py
"""

import pathlib
import sys
from collections import deque

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

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
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_aqua.ss1"
GYM = MapRSE.MOSSDEEP_CITY_GYM
X0, X1, Y0, Y1 = 0, 26, 0, 36

line = "=" * 96

context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

print(line)
print("KI-58 second pass — Mossdeep Gym components, by flood fill")
print(line)

# ---------------------------------------------------------------- read the map once
free: dict = {}
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        try:
            tile = get_map_data(GYM, (x, y))
            free[(x, y)] = tile.collision == 0
        except Exception:  # noqa: BLE001 — off-map reads are simply "not walkable"
            free[(x, y)] = False

warps = {}
for index, warp in enumerate(get_map_data(GYM, (0, 0)).warps):
    warps[tuple(warp.local_coordinates)] = index
print(f"\n{len(warps)} warps on {GYM.name}: {sorted(warps)}")


def flood(start):
    """Tiles reachable WITHOUT warping. A warp tile can be entered but not walked through."""
    if not free.get(start):
        return set(), set()
    seen = {start}
    queue = deque([start])
    touched_warps = set()
    while queue:
        x, y = queue.popleft()
        if (x, y) in warps and (x, y) != start:
            touched_warps.add((x, y))
            continue  # ‼ terminal: stepping on it warps us, so we cannot pass THROUGH
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if free.get(nxt) and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen, touched_warps


# ---------------------------------------------------------------- components
print("\n" + line)
print("COMPONENTS — flood from each warp's ARRIVAL side, plus the entrance floor tile")
print(line)

seeds = {"entrance floor (6,34)": (6, 34)}
for tile, index in sorted(warps.items()):
    seeds[f"warp {index} @ {tile}"] = tile

reported = {}
for label, seed in seeds.items():
    tiles, touched = flood(seed)
    reported[seed] = (tiles, touched)
    dest = ""
    if seed in warps:
        w = get_map_data(GYM, (0, 0)).warps[warps[seed]]
        try:
            d = w.destination_location
            dest = f"  (fires -> {MapRSE(tuple(d.map_group_and_number)).name} {tuple(d.local_position)})"
        except Exception:  # noqa: BLE001 — an unreadable destination is reported as blank
            dest = "  (destination unreadable)"
    print(f"\n  {label}{dest}")
    print(f"      component: {len(tiles)} tile(s)")
    print(f"      warps touchable from it: {sorted((warps[t], t) for t in touched) or 'NONE'}")

# ---------------------------------------------------------------- controls
print("\n" + line)
print("CONTROLS")
print(line)
ok = True

print("\n  [1] KNOWN-GOOD — (6,34) -> (1,33) plans in 10 wp, so they must share a component")
entrance_tiles, entrance_warps = reported[(6, 34)]
shares = (1, 33) in entrance_warps
print(f"      {'OK  ' if shares else 'FAIL'}  (1,33) touchable from (6,34): {shares}")
if not shares:
    ok = False


def plans(a, b) -> bool:
    try:
        calculate_path(get_map_data(GYM, a), get_map_data(GYM, b))
        return True
    except PathFindingError:
        return False
    except Exception:  # noqa: BLE001
        return False


print("\n  [2] PLANNER AGREEMENT — the flood must not contradict `calculate_path`")
SAMPLE = [((6, 34), (1, 33)), ((6, 34), (3, 28)), ((9, 18), (7, 18)),
          ((8, 12), (11, 3)), ((11, 35), (13, 32)), ((21, 10), (23, 8)), ((20, 24), (23, 20))]
for a, b in SAMPLE:
    tiles, touched = reported.get(a, flood(a))
    flood_says = (b in tiles) or (b in touched)
    planner_says = plans(a, b)
    agree = flood_says == planner_says
    print(f"      {'OK  ' if agree else 'DISAGREE'}  {a} -> {b}: flood={flood_says} planner={planner_says}")

print("\n" + line)
print("READING")
print(line)
if not ok:
    print("\n  The known-good control failed — the flood is wrong; ignore everything above.")
else:
    print("\n  Any DISAGREE row above is the finding: two independent models of the same map")
    print("  differing tells you which one is wrong far faster than re-reading either.")
    print("  ‼ And note the correction this probe exists for: MB_MOSSDEEP_GYM_WARP is an ORDINARY")
    print("    warp (decomp `DoMossdeepGymWarp`), so the warp-event model was never the problem.")
print(line)
