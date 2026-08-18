"""`#24-ki76correctness` — WHICH tiles funnel into ROOM6 `(14,8)`, and where can a driver STAND?

⛔ OBSERVE-ONLY. Static ROM read; no navigation, no emulator driving, nothing written.

WHY THIS EXISTS. `#24-ki76correctness`'s live confirmation needs to step the avatar onto a tile
whose current carries it into `(14,8)` — the Non-Animated Door our planner never penalises. The
docs record the COUNT (9 of Room 6's 108 chains) and the shared ENDPOINT, but not the nine ENTRY
tiles, and not a tile a driver can legally stand on first. Both are recoverable in seconds, and
guessing either would waste a multi-minute drive.

‼ AND THERE IS A TRAP THIS PROBE EXISTS TO AVOID. The tile the docs name as the funnel, `(14,9)`,
is itself a CURRENT. You cannot ask the planner to `navigate_to` a current tile and expect to be
left standing on it: `map_path.py:1013` SUBSTITUTES the slide destination for that neighbour, which
is the very defect under test. ⇒ the driver must path to a NON-CURRENT staging tile and then step
ONE tile by hand. This probe finds such a tile, or reports that none exists — which would itself be
the finding, and would change the driver's design before a single frame is burned.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_room6_warp_entries.py
Exit: 0 always (measurement).
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

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)
# ‼‼ `is_test_run=True` IS LOAD-BEARING, NOT COSMETIC — added 2026-08-17 (deep sanity check, pass 2).
# Without it `LibmgbaEmulator.__init__` registers an `atexit` shutdown that CREATES A SAVE STATE and
# OVERWRITES `profiles/repro-ml/current_state.ss1` — the file the profile auto-loads next launch.
# ⛔ This file's own docstring claimed "OBSERVE-ONLY ... nothing written", and that was FALSE: an
# audit agent ran both probes and caught them mutating shared profile state. A probe that edits the
# world it measures is the one thing a probe must never do, and the claim was in the docstring the
# whole time.
context.audio = False
context.video = False

# ‼ THE PINNED COPY, NOT THE VOLATILE ORIGINAL. `post_dive.ss1` is re-captured by
# `--driver spacecenter` on every PASS; `post_dive_ki76.ss1` is the pinned copy taken 2026-08-17.
ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive_ki76.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE
from modules.map_path import Direction, _get_map_metadata

BAR = "=" * 100
ROOM6 = MapRSE.SEAFLOOR_CAVERN_ROOM6
TARGET = (14, 8)

md = get_map_data(ROOM6, (0, 0))
key = (md.map_group, md.map_number)
tiles = {t.local_position: t for t in get_map_all_tiles(md)}
warps = {w.local_coordinates for w in md.warps}
W, H = md.map_size


def head(t: str) -> None:
    print(f"\n{BAR}\n{t}\n{BAR}\n")


print(f"{ROOM6.name}  size={W}x{H}  warps={sorted(warps)}\n")

# --- PRODUCTION is the oracle for where a chain ends (same rule as probe_slide_endpoints.py) -----
prod = {}
for t in _get_map_metadata(key).tiles:
    if t.forced_movement_to:
        prod[t.local_coordinates] = t.forced_movement_to[Direction.North]

head(f"1. EVERY TILE WHOSE SLIDE ENDS ON THE WARP {TARGET}")

entries = sorted(pos for pos, (m, p, _s) in prod.items()
                 if tuple(m) == key and tuple(p) == TARGET)
print(f"  count = {len(entries)}   (KI-76 records 9 — a MISMATCH here means one of us is wrong)")
for pos in entries:
    tt = tiles[pos].tile_type
    steps = prod[pos][2]
    print(f"    {str(pos):<10} {tt:<22} steps={steps}")

head("2. CAN A DRIVER STAND NEXT TO ONE? — neighbours that are NOT currents")

DELTA = {"North": (0, -1), "South": (0, 1), "East": (1, 0), "West": (-1, 0)}
staging = []
for pos in entries:
    for dname, (dx, dy) in DELTA.items():
        nx, ny = pos[0] + dx, pos[1] + dy
        if not (0 <= nx < W and 0 <= ny < H):
            continue
        n = tiles.get((nx, ny))
        if n is None:
            continue
        is_current = n.tile_type.endswith(" Current")
        # A legal stand-and-step tile: water you can be on, NOT itself a current (or the planner
        # would slide you off it), NOT a warp (or you would leave the map first).
        if (not is_current) and n.elevation == 1 and not n.collision and (nx, ny) not in warps:
            staging.append(((nx, ny), dname, pos, n.tile_type))

if staging:
    print("  ✅ STAGING TILES FOUND — stand here, then press the direction shown to step onto the entry:")
    print(f"  {'stand on':<10} {'press':<7} {'steps onto':<10} {'stand tile type':<24}")
    for stand, dname, entry, tt in staging:
        # Pressing dname moves FROM stand TO entry only if entry = stand + delta(dname); we built it
        # the other way round, so the press direction is the OPPOSITE.
        opposite = {"North": "South", "South": "North", "East": "West", "West": "East"}[dname]
        print(f"  {str(stand):<10} {opposite:<7} {str(entry):<10} {tt:<24}")
else:
    print("  ⛔ NONE. Every neighbour of every entry tile is itself a current, a wall, or a warp.")
    print("     ⇒ the driver CANNOT stage-and-step; it would have to enter the flow from further")
    print("       out and ride in, which changes the design. This is a finding, not a failure.")

head("3. THE NEIGHBOURHOOD OF THE FUNNEL TILE THE DOCS NAME — (14,9)")

for y in range(max(0, 7), min(H, 14)):
    row = []
    for x in range(max(0, 9), min(W, 18)):
        t = tiles.get((x, y))
        if t is None:
            row.append("  ?  ")
            continue
        mark = "W" if (x, y) in warps else ("#" if t.collision else ("~" if t.tile_type.endswith(" Current") else "."))
        row.append(f" {mark}{'*' if (x, y) == TARGET else ' '}  ")
    print(f"  y={y:<3} " + "".join(row))
print(f"\n  x =      " + "".join(f" {x:<4}" for x in range(max(0, 9), min(W, 18))))
print("  legend: W=warp  #=collision  ~=current  .=plain water/floor  *=the target warp (14,8)")

head("4. WHAT PRODUCTION SAYS HAPPENS FROM (14,9) SPECIFICALLY")

p = prod.get((14, 9))
if p is None:
    print("  (14,9) has NO forced movement — it is not a current tile. ⛔ The docs' description of")
    print("  it as 'a northward current directly under the door' would then be WRONG; check before")
    print("  building a driver on it.")
else:
    m, pos, steps = p
    print(f"  (14,9) tile_type = {tiles[(14,9)].tile_type!r}")
    print(f"  production slides it to map={tuple(m)} pos={tuple(pos)} in {steps} steps")
    print(f"  is that the warp {TARGET}? {tuple(pos) == TARGET and tuple(m) == key}")

head("5. ‼‼ CAN THE DRIVER ACTUALLY GET TO A STAGING TILE? — REACHABILITY FROM ROOM 6's ENTRY")

print("  ⛔ THIS SECTION IS THE POINT OF THE PROBE. Sections 2-4 answer 'which tile would work';")
print("  this one answers 'can we STAND there', and the two answers are very different — Room 6 is")
print("  ONE-WAY (KI-76: our entry mask forbids entering a current head-on against its flow).")
print("  A driver built on an unreachable staging tile fails at runtime after minutes of setup.\n")

from modules.map_path import PathFindingError, calculate_path  # noqa: E402

ROOM6_ENTRY = (11, 21)  # where Ch20Room6Mode leaves the avatar after Rooms 1-2 (story_harness.py)
reachable = []
for stand in sorted({s for s, _d, _e, _t in staging}):
    try:
        path = calculate_path(get_map_data(ROOM6, ROOM6_ENTRY), get_map_data(ROOM6, stand))
    except PathFindingError:
        print(f"  {str(stand):<9} NO PATH")
        continue
    except Exception as exc:  # noqa: BLE001 - a novel failure here IS the finding
        print(f"  {str(stand):<9} ‼ {type(exc).__name__}: {str(exc)[:70]}")
        continue
    coords = [tuple(w.coordinates) for w in path]
    # ‼ Assert the ROUTE is clean, not merely that one exists: a waypoint on a CURRENT would sweep
    # the avatar away mid-approach, and a non-final waypoint on a WARP would eject it from the map.
    via_cur = [c for c in coords[:-1] if c in tiles and tiles[c].tile_type.endswith(" Current")]
    via_warp = [c for c in coords[:-1] if c in warps]
    clean = not via_cur and not via_warp and coords[-1] == stand
    reachable.append((stand, len(coords), clean))
    print(f"  {str(stand):<9} PATH len={len(coords):<3} ends_on_target={coords[-1] == stand}  "
          f"via_currents={via_cur or 'none'}  via_warps={via_warp or 'none'}"
          f"{'   <- ✅ USABLE' if clean else '   <- ⛔ route is not clean'}")

usable = [r for r in reachable if r[2]]
print(f"\n  reachable: {len(reachable)} of {len(set(s for s, _d, _e, _t in staging))}   "
      f"USABLE (clean route): {len(usable)}")
if usable:
    best = min(usable, key=lambda r: r[1])
    entry_for = [e for s, _d, e, _t in staging if s == best[0]]
    print(f"  ⇒ ✅ THE DRIVER'S STAGING TILE IS {best[0]} ({best[1]} waypoints), stepping onto {entry_for}.")
else:
    print("  ⇒ ⛔ NO usable staging tile. The stage-and-step design is DEAD; the driver would have")
    print("    to enter the flow from outside the pocket and ride in. Report this, do not improvise.")

head("DONE — measurement only. Nothing was changed.")
