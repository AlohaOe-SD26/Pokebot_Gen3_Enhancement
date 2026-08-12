"""§Ch16 leg 1's new failure: why can the bot not reach the Slateport Harbor door approach?

‼ WHY THIS EXISTS. With KI-56 fixed, §Ch16 got out of the Magma Hideout and crossed the region —
and then died on the LAST step of leg 1:

    UnreachableDestinationError: Could not reach (28, 13) on SLATEPORT_CITY: the field is idle
    and we are still at (19, 20), so retrying cannot change the result

That is a brand-new failure on a leg that had never been exercised past the hideout, and it is
worth exactly one measurement before anyone theorises. ‼ **The run also WHITED OUT once** (f14345)
before this, so where it is standing is a RECOVERY position, not a walked-to one — which matters,
because a whiteout respawn is the one position nobody chose.

THE CANDIDATE CAUSES, and what separates them:
  1. **A live OBJECT blocks the corridor.** Slateport is crowded and `SlateportCity_OnTransition`
     rearranges people in this era. `calculate_path` DOES see object events on the CURRENTLY
     LOADED map (that is how `open_magma_hideout_1f` can test its own Strength pushes), so a
     blocked read here is real for this frame — and might clear on another.
  2. **KI-53's shape** — a Slateport static-planner asymmetry already on record:
     `ROUTE110 -> SLATEPORT_CITY` FAILs statically while the exact reverse plans in 30 waypoints.
     If the REVERSE plans here too, this is that same defect and not a new one.
  3. **Genuine topology** — the destination is walled off in this era.

WHAT IT MEASURES, from the failure state (`profiles/ch16b/current_state.ss1`):
  * the failing query, re-run — it must REPRODUCE, or the state moved and nothing else means anything
  * the REVERSE query, which is what tells cause 2 from cause 1
  * the reachable set from the stranded tile, and whether the target is in it
  * every map object within a few tiles of the target, with its id and graphics

‼ CONTROLS:
  * REPRODUCTION — the exact failing pair must fail again here. If it plans, this save is not the
    failure and every row below describes a different world.
  * PLANNER CONTROL — a trivially adjacent tile must plan, proving the planner answers at all
    from this position rather than refusing everything.
  * STATIC ARM — the same two queries are re-run from a save where SLATEPORT_CITY is NOT the
    loaded map, so live objects cannot be seen. A pair that fails live and plans static is an
    OBJECT problem; one that fails both ways is layout or KI-53.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_slateport_harbor_approach.py
"""

import pathlib
import sys

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

from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

#: ‼ The STALL save the harness took at f20252, ~250 frames after the raise, standing on the
#: same tile.  is NOT usable: it is only written on shutdown,
#: and this run was killed while still burning frames in Manual mode.
FAILURE_STATE = REPO / "tools" / "story-dev" / "saves" / "stalls" / "ch16b-f20252.ss1"
STATIC_STATE = REPO / "tools" / "story-dev" / "saves" / "post_mtpyre.ss1"

CITY = MapRSE.SLATEPORT_CITY
STUCK = (19, 20)
TARGET = (28, 13)          # SLATEPORT_HARBOR_DOOR_APPROACH
DOOR = (28, 12)            # the warp itself

line = "=" * 96


def plan(start, end) -> str:
    try:
        return f"OK, {len(calculate_path(get_map_data(CITY, start), get_map_data(CITY, end)))} wp"
    except PathFindingError as error:
        return f"FAIL [{str(error)[:80]}]"
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash
        return f"FAIL ({type(error).__name__}: {str(error)[:60]})"


def load(path: pathlib.Path) -> str:
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    avatar = get_player_avatar()
    return f"{MapRSE(tuple(avatar.map_group_and_number)).name} {tuple(avatar.local_coordinates)}"


print(line)
print("§Ch16 leg 1 — why is SLATEPORT_CITY (28,13) unreachable from (19,20)?")
print(line)

# ---------------------------------------------------------------- LIVE arm
where = load(FAILURE_STATE)
print(f"\nLIVE ARM — the failure state. avatar: {where}")
print("-" * 96)
live_forward = plan(STUCK, TARGET)
live_reverse = plan(TARGET, STUCK)
live_door = plan(STUCK, DOOR)
print(f"  REPRODUCTION  {STUCK} -> {TARGET} : {live_forward}")
print(f"  REVERSE       {TARGET} -> {STUCK} : {live_reverse}")
print(f"  to the DOOR   {STUCK} -> {DOOR}   : {live_door}")

neighbour = (STUCK[0] + 1, STUCK[1])
print(f"  PLANNER CTRL  {STUCK} -> {neighbour} : {plan(STUCK, neighbour)}")

print("\n  MAP OBJECTS within 4 tiles of the target:")
try:
    objects = list(get_map_objects())
except Exception as error:  # noqa: BLE001 — an unreadable object list is reported, not fatal
    objects = []
    print(f"      <unreadable: {type(error).__name__}: {error}>")
near = 0
for obj in objects:
    try:
        coords = tuple(obj.current_coords)
    except Exception:  # noqa: BLE001 — one bad object must not hide the rest of the list
        continue
    if abs(coords[0] - TARGET[0]) <= 4 and abs(coords[1] - TARGET[1]) <= 4:
        near += 1
        print(f"      id={getattr(obj, 'local_id', '?')} at {coords} "
              f"gfx={getattr(obj, 'graphics_id', '?')}")
print(f"      ({near} of {len(objects)} objects are near the target)")

# ---------------------------------------------------------------- reachable set
print("\n  Is the target reachable from the stuck tile AT ALL? Probing a ring around it:")
for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (-1, 1), (1, 1)):
    tile = (TARGET[0] + dx, TARGET[1] + dy)
    print(f"      {STUCK} -> {tile}: {plan(STUCK, tile)}")

# ---------------------------------------------------------------- can we still get IN?
# ‼ THE QUESTION THAT DECIDES WHETHER THIS IS A CONSTANT FIX OR A REAL BLOCKER. Capt. Stern
# stands ON (28,13) and the door is (28,12), directly above him. If every route to the door runs
# through his tile, no choice of staging tile helps and leg 2 cannot run either.
print("\n  CAN THE DOOR STILL BE ENTERED? Candidate staging tiles -> the door (28,12):")
STAGING_CANDIDATES = [(27, 13), (27, 12), (28, 15), (27, 14), (29, 14), (29, 12), (28, 11)]
for candidate in STAGING_CANDIDATES:
    from_stuck = plan(STUCK, candidate)
    to_door = plan(candidate, DOOR)
    usable = from_stuck.startswith("OK") and to_door.startswith("OK")
    print(f"      {str(candidate):<9} reachable: {from_stuck:<12} -> door: {to_door:<12} "
          f"{'<= USABLE' if usable else ''}")

# ---------------------------------------------------------------- STATIC arm
where = load(STATIC_STATE)
print(f"\nSTATIC ARM — SLATEPORT_CITY not loaded, so live objects are invisible. avatar: {where}")
print("-" * 96)
static_forward = plan(STUCK, TARGET)
static_reverse = plan(TARGET, STUCK)
print(f"  {STUCK} -> {TARGET} : {static_forward}")
print(f"  {TARGET} -> {STUCK} : {static_reverse}")

# ---------------------------------------------------------------- verdict
print("\n" + line)
print("READING")
print(line)
if live_forward.startswith("OK"):
    print("  ‼ THE FAILURE DID NOT REPRODUCE from this save — it plans here. The saved state is")
    print("    not the failing one (the run continued past it, or the field moved). Nothing")
    print("    above describes the failure; recapture the state at the moment it raises.")
elif static_forward.startswith("OK"):
    print("  LIVE fails, STATIC plans  =>  a live OBJECT is blocking.")
    print("  ‼‼ ANSWERED BY THE DECOMP, AND IT IS NOT INTERMITTENT. `SlateportCity_OnTransition`")
    print("    calls `SlateportCity_EventScript_MovePeopleForSternInterview` whenever")
    print("    `VAR_SLATEPORT_CITY_STATE == 1`, and that script's FIRST line is literally")
    print("        setobjectxyperm LOCALID_SLATEPORT_CAPT_STERN, 28, 13")
    print("    followed by `setobjectmovementtype ... MOVEMENT_TYPE_FACE_DOWN`. The game PARKS")
    print("    Capt. Stern on the exact tile this leg targets, permanently and stationary — and")
    print("    ‼ §Ch15 is what sets that var. Beating Maxie spawns the blocker.")
    print("    So this is DETERMINISTIC: waiting and retrying can never clear it. An earlier")
    print("    version of this text guessed 'a wandering NPC may clear on its own'; the")
    print("    movement types refute that. Fix the CONSTANT, not the timing.")
elif live_reverse.startswith("OK"):
    print("  LIVE fails BOTH ways in the layout but the REVERSE plans  =>  this is KI-53's")
    print("    documented Slateport asymmetry, not a new defect. A static FAIL is not a verdict.")
else:
    print("  BOTH directions fail, live and static  =>  the target is genuinely not connected to")
    print("    the stuck tile in this era. The destination tile itself should be re-derived.")
print("\n  ‼ The whiteout matters: the bot was placed at (19,20) by a WHITEOUT RECOVERY, not by")
print("    walking there. Check whether that respawn point is the real problem before changing")
print("    any route constant.")
print(line)
