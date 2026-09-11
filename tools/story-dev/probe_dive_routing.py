"""KI-68 — WHAT does the planner actually need to cross a DIVE transition? Measure, don't assume.

‼ WHY THIS IS THE FOUNDATION FOR TWO ARCS AT ONCE. Both of the next things this bot must do are
behind a dive:
  * **§Ch21** — the Seafloor Cavern, entered by diving on Route 128;
  * **the REGI arc** — the Sealed Chamber is `UNDERWATER_SEALED_CHAMBER`, reached by diving on
    Route 134, and **Relicanth itself is a dive-only (underwater) encounter**.
So "can the bot dive" gates the Kyogre story AND the legendary golems. It is worth measuring
properly once.

‼ WHAT KI-68 ESTABLISHED, and what this probe REFINES. `WaypointAction.Dive`/`Emerge` are declared
in `map_path.py` and assigned NOWHERE; `can_dive()` has zero callers; `warp_graph.py` and
`region_reach.py` exclude dive edges *on purpose*. The easy conclusion — "Dive is impossible" — is
WRONG and worth killing early: `modules/modes/util/higher_level_actions.py` `dive()` exists, drives
`Task_UseDive`, and only requires standing on a deep-water tile while not already underwater.

⇒ The real shape is: **Dive is not AUTO-ROUTABLE, but it is DRIVEABLE.** That is the same shape this
project has already solved three times — the §Ch18 gym exit is a coord_event no warp-graph solver
will ever offer, Steven's house exit is a bottom-row door the navigate helpers cannot use, and both
are handled by driving the transition explicitly instead of teaching the planner about it.

So the question this probe answers is NOT "is Dive supported" but:
    **which legs can the existing planner do, and exactly where must a chapter take over?**

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dive_routing.py
"""

import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)  # ‼ is_test_run: without it the
    # emulator registers an atexit that OVERWRITES shared `profiles/<name>/current_state.ss1`
    # and writes a states/ snapshot. Pass 2 fixed this for the two KI-76 probes; PASS 4
    # (2026-08-22) found SEVEN MORE still writing — `profiles/repro-ml/states/` had reached
    # 2,820 files / 160 MB. A probe that mutates shared state is not observe-only.
context.audio = False
context.video = False
# ‼ THE THIRD LINE OF THE TRIPLE (added 2026-09-11, `#26-gatestartupcontention`). Without it the
# emulator stays THROTTLED and paces itself to 60fps by BLOCKING on an audio write every frame
# (`libmgba.py:618-621`) — `context.audio = False` only silences the samples, it does not stop the
# write. `emulation_speed = 0` routes to `set_throttle(False)` (`context.py:101-102`), the only one
# that CLOSES the stream. ⛔ This gate is short TODAY, which is exactly how the omission hid in
# `repro_gym_whiteout_guard.py` until its route grew: 900s bound = only ~54,000 frames at 1x.
context.emulation_speed = 0

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.memory import get_event_flag
from modules.player import get_player_avatar
from modules.pokemon_party import get_party

BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


avatar = get_player_avatar()
print(f"anchor: post_dive.ss1")
print(f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)")

# ---------------------------------------------------------------------------------------------
head("1 — THE TWO PRECONDITIONS `can_dive()` CHECKS (badge + a party mon that knows Dive)")

badge7 = get_event_flag("BADGE07_GET")
knows_dive = [
    (i, m.species.name) for i, m in enumerate(get_party())
    if m is not None and any(mv is not None and mv.move.name == "Dive" for mv in m.moves)
]
print(f"  BADGE07_GET                    : {badge7}")
print(f"  party members that KNOW Dive   : {knows_dive or 'NONE'}")
print(f"\n  can_dive() would return        : {bool(badge7) and bool(knows_dive)}")
print("  ‼ `can_dive()` needs the move KNOWN, not merely learnable — and it is dead code today")
print("    (zero callers), so this is what a caller WOULD get, not what anything currently asks.")

# ---------------------------------------------------------------------------------------------
head("2 — DO THE UNDERWATER MAPS EXIST, AND DOES THE WARP GRAPH KNOW THEM?")

TARGETS = [
    ("UNDERWATER_ROUTE134", MapRSE.UNDERWATER_ROUTE134, "dive spot for the SEALED CHAMBER"),
    ("UNDERWATER_SEALED_CHAMBER", MapRSE.UNDERWATER_SEALED_CHAMBER, "the chamber's water entrance"),
    ("SEALED_CHAMBER_OUTER_ROOM", MapRSE.SEALED_CHAMBER_OUTER_ROOM, "Braille + the DIG spot"),
    ("SEALED_CHAMBER_INNER_ROOM", MapRSE.SEALED_CHAMBER_INNER_ROOM, "the Regi unlock itself"),
    ("UNDERWATER_SEAFLOOR_CAVERN", MapRSE.UNDERWATER_SEAFLOOR_CAVERN, "§Ch21, the Kyogre arc"),
    ("DESERT_RUINS", MapRSE.DESERT_RUINS, "Regirock"),
    ("ISLAND_CAVE", MapRSE.ISLAND_CAVE, "Regice"),
    ("ANCIENT_TOMB", MapRSE.ANCIENT_TOMB, "Registeel"),
]
for name, enum, why in TARGETS:
    try:
        data = get_map_data(enum, (0, 0))
        size = data.map_size
        warps = [(tuple(w.local_coordinates),
                  getattr(MapRSE((w.destination_map_group, w.destination_map_number)), "name", "?"))
                 for w in data.warps]
        print(f"  {name:<28} size={size}  warps={len(warps)}   ({why})")
        for tile, dest in warps[:4]:
            print(f"      {tile} -> {dest}")
    except Exception as error:  # noqa: BLE001 - a map we cannot read is itself the finding
        print(f"  {name:<28} <unreadable: {type(error).__name__}: {error}>")

# ---------------------------------------------------------------------------------------------
head("3 — ‼ THE ACTUAL GAP: is the dive transition a WARP at all?")

print("  A dive is NOT a warp event — it is a MOVE used on a deep-water tile, and the destination")
print("  is a different map with the same coordinates. That is why no warp-graph solver will ever")
print("  offer it, and why `WaypointAction.Dive` being unassigned is a DESIGN state, not a bug:")
print("  `calculate_path` plans within one map plus warp edges.\n")

from modules.warp_graph import __file__ as wg_file  # noqa: E402

wg_src = pathlib.Path(wg_file).read_text(encoding="utf-8")
for line_no, line in enumerate(wg_src.splitlines(), 1):
    if "Dive" in line or "Emerge" in line:
        print(f"  warp_graph.py:{line_no}: {line.strip()}")

# ---------------------------------------------------------------------------------------------
head("4 — WHAT A CHAPTER WOULD HAVE TO DRIVE ITSELF (the §Ch18 pattern, applied)")

print("  The legs, and who can do each:")
print("    a. surf to the deep-water tile above the dive spot   -> PLANNER (Surf is routable)")
print("    b. call `dive()` while standing on it                -> CHAPTER (an explicit action)")
print("    c. navigate on the UNDERWATER map to the chamber     -> PLANNER (ordinary same-map)")
print("    d. surface / take the warp into the chamber          -> CHAPTER or PLANNER (a real warp)")
print("\n  ‼ Only (b) is missing, and it is one call — NOT a planner rewrite. `dive()` already")
print("    exists and drives `Task_UseDive`; it refuses unless the tile really is deep water, so")
print("    a wrong tile fails LOUDLY rather than silently doing nothing.")
print("\n  ‼ WHAT MUST STILL BE MEASURED LIVE before any of this is built:")
print("    * that the planner can actually surf to the dive tile from a real anchor;")
print("    * that `dive()` succeeds there and lands us on the expected UNDERWATER map;")
print("    * that the underwater map is navigable to the chamber warp.")
print("    A static path is not a route — this project demotes tiles derived that way.")

head("VERDICT")
print(f"  can_dive() preconditions met on this anchor : {bool(badge7) and bool(knows_dive)}")
print("  underwater + Regi maps present in our table  : see section 2")
print("  planner emits a Dive waypoint                : NO — and that is by design, not a defect")
print("  ⇒ the fix is a CHAPTER that drives `dive()`, not a change to `calculate_path`.")
print("\n‼ This probe is STATIC. It proves what the code can and cannot express; it does NOT prove")
print("  the route works. That needs a driven run from a real anchor.")
