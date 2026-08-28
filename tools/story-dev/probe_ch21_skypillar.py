"""§Ch21 LEG 3 — CAN A BIKELESS BOT CLIMB THE SKY PILLAR? Ask PRODUCTION, not a re-implementation.

‼ WHY THIS EXISTS, AND WHY IT IS NOT A DUPLICATE OF `probe_skypillar_clean_layout.py`.
That probe decodes the DECOMP's shipped `SkyPillar_*_Clean/map.bin` binaries over the network and
runs its own BFS. This one asks the tile data and the planner OUR BOT ACTUALLY USES, from the ROM
we actually run, with no network. They answer different questions and they DISAGREE — which is the
single most important thing this probe found, so keep both.

The §Ch21 ATLAS's whole climb route came from two independent BFS re-implementations over the
`*_Clean` binaries. This project has MEASURED that agreement between re-implementations is not a
confidence signal, and playbook §0d says: before re-implementing production logic, check whether
production already PUBLISHES the value. `calculate_path` does.

--------------------------------------------------------------------------------------------
WHAT IT FOUND (2026-08-27) — and why it matters more than the numbers
--------------------------------------------------------------------------------------------
Production's tile data reports **38 cracked tiles on 2F and 34 on 4F**. The atlas, reading
`2F_Clean`, reports **ZERO on 2F** and five on 4F. Both are honest; they are reading DIFFERENT
LAYOUTS. Ours is the one with the cracks.

That would be a footnote except for three measured facts that compose into a blocker:
  1. `map_path.py` does not model `"Cracked Floor"` AT ALL (`grep -n Cracked` = 0 hits), so the
     planner cannot avoid one — and MEASURED HERE, its own proposed routes CROSS 27 of them.
  2. There is **NO crack-free route** across 2F or 4F on the layout we read (measured by making
     the cracked tiles impassable through the object-blocking rig and re-planning).
  3. The bot is **BIKELESS** at this point in the story (`RECEIVED_BIKE` False, no bike in the
     bag on `post_wallace.ss1`), and the Sky Pillar's cracked floors are survived by SPEED —
     a walking player falls.
⇒ A bikeless bot cannot cross 2F on the layout we read, yet the story requires exactly that.
   **Therefore the story climb almost certainly runs on the CLEAN layouts while our planner
   models the post-game ones.** ⛔ That inference has ONE unverified link — "a walking player
   falls" is the atlas's decomp claim, not measured here. It is named in the output, not hidden.

⇒ CONSEQUENCE FOR THE BUILD: `navigate_to` is UNSAFE on 2F and 4F. Leg 3 cannot plan the climb
with the planner; it needs waypoints valid for the layout that is actually live, which only a
drive to the Sky Pillar can confirm.

--------------------------------------------------------------------------------------------
WHAT THIS PROBE CANNOT ANSWER — stated up front so nobody over-reads it
--------------------------------------------------------------------------------------------
* WHICH LAYOUT IS LIVE during the story climb. `get_map_data()` reads the STATIC ROM header
  (`map.py:751`); the game may swap at runtime. A companion check (`--driver ch21pocket` with
  `CH21_LAYOUT_PROBE=1`) compared live vs static ON SOOTOPOLIS and found them EQUAL at state 3 —
  a clean negative on ONE map at ONE state, which does NOT settle the Sky Pillar.
* WHERE THE AVATAR RESTS after each warp. A warp table gives the warp EVENT tile; the avatar may
  be auto-stepped one tile clear of a doorway (MEASURED 2026-08-27 on the Cave of Origin, and it
  is PER-WARP). Every Sky Pillar warp below is a TARGET; the resting tiles are UNVERIFIED.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_skypillar.py
Self-test:  POKEBOT_SKYPILLAR_PROBE_FAULT=rig ... same ...   # C2 must go RED and exit 1
"""

import os as _os
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

import modules.map_path as mp
from modules.items import get_item_bag
from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import get_event_flag

SAVE = REPO / "tools" / "story-dev" / "saves" / "post_wallace.ss1"

FLOORS = [
    "SKY_PILLAR_ENTRANCE", "SKY_PILLAR_OUTSIDE", "SKY_PILLAR_1F", "SKY_PILLAR_2F",
    "SKY_PILLAR_3F", "SKY_PILLAR_4F", "SKY_PILLAR_5F", "SKY_PILLAR_TOP",
]

#: The climb, leg by leg, with the ATLAS's verdict for comparison. ⛔ A REFUSAL on the two
#: `expect_refused` legs is the EXPECTED reading — it is what proves the sealed pockets are real
#: and the fall is genuinely required. A probe whose "failure" is the finding must say so, or a
#: future reader will treat the red as a bug and "fix" it.
LEGS = [
    ("1F  (6,13)->(10,1)", "SKY_PILLAR_1F", (6, 13), (10, 1), "atlas OK 17 steps", False),
    ("2F  (10,1)->(3,1)", "SKY_PILLAR_2F", (10, 1), (3, 1), "atlas OK 10, 0 cracked on CLEAN", False),
    ("3F  (3,1)->(7,1)", "SKY_PILLAR_3F", (3, 1), (7, 1), "atlas NO PATH (sealed pocket)", True),
    ("3F  (3,1)->(11,1)", "SKY_PILLAR_3F", (3, 1), (11, 1), "the 4F stairs", False),
    ("4F  (11,1)->(3,1)", "SKY_PILLAR_4F", (11, 1), (3, 1), "atlas NO PATH (sealed pocket)", True),
    ("4F  (11,1)->(5,4)", "SKY_PILLAR_4F", (11, 1), (5, 4), "atlas: reachable, crosses NO crack", False),
    ("3F  (6,4)->(7,1)", "SKY_PILLAR_3F", (6, 4), (7, 1), "the post-fall walk", False),
    ("4F  (7,1)->(3,1)", "SKY_PILLAR_4F", (7, 1), (3, 1), "atlas OK 7 steps", False),
    ("5F  (3,1)->(10,1)", "SKY_PILLAR_5F", (3, 1), (10, 1), "atlas OK 34 steps", False),
    ("TOP (16,14)->(14,9)", "SKY_PILLAR_TOP", (16, 14), (14, 9), "atlas OK 14 steps", False),
]

ATLAS_4F_CRACKED = {(0, 3), (1, 3), (6, 4), (7, 4), (9, 4)}

# ‼ FAULT HOOK — `POKEBOT_SKYPILLAR_PROBE_FAULT=rig` makes the blocking rig inert (the synthetic
# blockers claim the wrong map), so "no crack-free route" would read as "route exists" and the
# whole crack analysis would silently invert. CONTROL 2 must go RED under it.
_FAULT = _os.environ.get("POKEBOT_SKYPILLAR_PROBE_FAULT", "").strip()


class _Blocker:
    """A synthetic loaded object, used to make a tile impassable to `calculate_path`."""

    def __init__(self, map_value, local_id: int, coords: tuple[int, int]) -> None:
        self.flags = []
        self.map_group_and_number = (0, 0) if _FAULT == "rig" else map_value
        self.local_id = local_id
        self.current_coords = coords
        self.previous_coords = coords


def _with_blockers(map_value, tiles) -> None:
    mp.get_map_objects = lambda: [_Blocker(map_value, 900 + i, t) for i, t in enumerate(tiles)]


def _restore() -> None:
    mp.get_map_objects = get_map_objects


def plan(m: MapRSE, src, dst, block=()):
    """Waypoint coordinates, or None if the planner refuses. A refusal IS a reading."""
    _with_blockers(m.value, block)
    try:
        return [tuple(w.coordinates) for w in calculate_path((m, src), (m, dst))]
    except PathFindingError:
        return None
    except Exception:
        return None
    finally:
        mp.get_map_objects = lambda: []


def cracked_of(m: MapRSE) -> list[tuple[int, int]]:
    """Every tile whose behaviour our own map data calls a cracked floor.

    ⛔ BOUNDED BY THE MAP'S REAL SIZE (`R-SCANBOUND`, 2026-08-27): tile lookup is a FLAT index
    (`y*width + x`), so an out-of-bounds x WRAPS into the next row and reports a phantom tile.
    """
    width, height = get_map_data(m, (0, 0)).map_size
    found = []
    for y in range(height):
        for x in range(width):
            try:
                tile = get_map_data(m, (x, y))
            except Exception:
                continue
            if tile is not None and "rack" in str(getattr(tile, "tile_type", "")):
                found.append((x, y))
    return found


def warps_of(m: MapRSE) -> list[str]:
    """⛔ via `PathTile.warps_to`, NOT `get_map_data(...).warps_to` — the latter was MEASURED
    BLIND on 2026-08-27 (zero warps on three maps that certainly have them)."""
    width, height = get_map_data(m, (0, 0)).map_size
    rows = []
    for y in range(height):
        for x in range(width):
            try:
                tile = mp._find_tile_by_local_coordinates(m.value, (x, y))
            except Exception:
                continue
            warp = getattr(tile, "warps_to", None)
            if not warp:
                continue
            try:
                dest = MapRSE(tuple(warp[0])).name
            except Exception:
                dest = str(tuple(warp[0]))
            rows.append(f"({x},{y})->{dest}{tuple(warp[1])}")
    return rows


def main() -> int:
    print("=" * 94)
    print("§Ch21 LEG 3 — SKY PILLAR, asked of PRODUCTION (static; no network, no emulation loop)")
    print("=" * 94)

    context.emulator.load_save_state(SAVE.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    mp.get_map_objects = lambda: []

    missing = [n for n in FLOORS if not hasattr(MapRSE, n)]
    if missing:
        print(f"\n‼ VACUOUS — MapRSE has no member(s) {missing}; nothing below is about the Sky Pillar.")
        return 1

    # ------------------------------------------------------------------ CONTROLS
    print("\n" + "-" * 94)
    print("CONTROLS — a probe that finds nothing is indistinguishable from one that cannot see")
    print("-" * 94)

    # C1 — an expected COUNT, not merely an expected member. ‼ 2026-08-27: a member-only control
    # passed while the scan DOUBLE-REPORTED every warp. A control must be able to see over-reporting.
    cave_warps = warps_of(MapRSE.CAVE_OF_ORIGIN_ENTRANCE)
    c1_ok = len(cave_warps) == 2
    print(f"  C1 warp scan finds EXACTLY 2 warps on CAVE_OF_ORIGIN_ENTRANCE (measured 2026-08-27): "
          f"got {len(cave_warps)}  {'PASS' if c1_ok else 'FAIL'}")

    # C2 — the blocking rig must actually CHANGE an answer, or every 'no crack-free route'
    # verdict below is meaningless (it would just be the rig doing nothing).
    two_f = MapRSE.SKY_PILLAR_2F
    naive_2f = plan(two_f, (10, 1), (3, 1))
    blocked_2f = plan(two_f, (10, 1), (3, 1), block=[naive_2f[0]]) if naive_2f else None
    c2_ok = bool(naive_2f) and (blocked_2f is None or blocked_2f != naive_2f)
    print(f"  C2 the BLOCKING RIG changes an answer (block the naive route's first waypoint): "
          f"{len(naive_2f) if naive_2f else None} wp -> "
          f"{len(blocked_2f) if blocked_2f else 'REFUSED'}  {'PASS' if c2_ok else 'FAIL'}")

    if not (c1_ok and c2_ok):
        print("\n‼ CONTROLS FAILED — every measurement below is UNTRUSTED. Do not act on it.")
        return 1
    print("\n  ALL CONTROLS PASS.")

    # ------------------------------------------------------- THE BOT'S OWN CAPABILITY
    print("\n" + "-" * 94)
    print("MEASUREMENT 0 — is the bot BIKELESS? (speed is what survives a cracked floor)")
    print("-" * 94)
    bag = get_item_bag()
    owned = []
    for attr in ("items", "key_items", "poke_balls", "tms_hms", "berries"):
        for slot in (getattr(bag, attr, None) or []):
            try:
                owned.append(slot.item.name)
            except Exception:
                pass
    bikes = [n for n in owned if "Bike" in n]
    print(f"  bike in bag: {bikes if bikes else 'NONE'}   RECEIVED_BIKE flag: "
          f"{get_event_flag('RECEIVED_BIKE')}   bag slots: {len(owned)}")
    print("  ⛔ A bikeless bot FALLS on any cracked tile it walks onto (the atlas's decomp claim:")
    print("     Mach Bike at PLAYER_SPEED_FASTEST survives; Acro Bike and walking do not).")
    print("     ‼ THAT LINK IS THE ATLAS'S, NOT MEASURED HERE — it is the one unverified step in")
    print("     the conclusion at the end of this run.")

    # --------------------------------------------------------------- THE WARP CHAIN
    print("\n" + "-" * 94)
    print("MEASUREMENT 1 — the Sky Pillar warp chain, from the ROM (⚠ TARGETS, not resting tiles)")
    print("-" * 94)
    for name in FLOORS:
        m = getattr(MapRSE, name)
        size = get_map_data(m, (0, 0)).map_size
        print(f"  {name:22s} size={size}  {warps_of(m)}")
    print("  ⚠ Every coordinate above is a warp EVENT tile. Where the avatar RESTS is UNVERIFIED")
    print("    and is per-warp (MEASURED on the Cave of Origin 2026-08-27). Only a drive settles it.")

    # ------------------------------------------------------------- CRACKED TILES
    print("\n" + "-" * 94)
    print("MEASUREMENT 2 — cracked tiles PRODUCTION sees, vs what the atlas measured on *_Clean")
    print("-" * 94)
    cracked: dict[str, list[tuple[int, int]]] = {}
    for name in FLOORS:
        m = getattr(MapRSE, name)
        cracked[name] = cracked_of(m)
        print(f"  {name:22s} {len(cracked[name]):3d} cracked tile(s)")
    four_f = set(cracked["SKY_PILLAR_4F"])
    print(f"\n  4F vs the atlas's CLEAN set {sorted(ATLAS_4F_CRACKED)}:")
    print(f"    atlas tiles still cracked here : {sorted(ATLAS_4F_CRACKED & four_f)}")
    print(f"    EXTRA cracked tiles we see     : {len(four_f - ATLAS_4F_CRACKED)}")
    print(f"  2F: atlas measured 0 on CLEAN; we see {len(cracked['SKY_PILLAR_2F'])}")
    print("  ⇒ ⛔ WE ARE READING A DIFFERENT LAYOUT THAN THE ATLAS MEASURED.")

    # -------------------------------------------------------- THE CLIMB, PER LEG
    print("\n" + "-" * 94)
    print("MEASUREMENT 3 — each climb leg asked of `calculate_path`, and does its route CROSS a crack?")
    print("-" * 94)
    print("  (the planner cannot see cracked floors at all — `grep -n Cracked map_path.py` = 0 hits)")
    total_crossings = 0
    surprises = []
    for label, floor, src, dst, note, expect_refused in LEGS:
        m = getattr(MapRSE, floor)
        route = plan(m, src, dst)
        if route is None:
            verdict = "REFUSED"
            if not expect_refused:
                surprises.append(f"{label} refused but was not expected to")
        else:
            hits = [t for t in route if t in set(cracked[floor])]
            total_crossings += len(hits)
            verdict = (f"OK {len(route):3d} wp, crosses {len(hits)} crack(s)"
                       + (f" {hits[:5]}" if hits else ""))
            if expect_refused:
                surprises.append(f"{label} PATHED but the atlas says it is a sealed pocket")
        flag = "  <-- EXPECTED REFUSAL (proves the sealed pocket / the fall)" if expect_refused else ""
        print(f"  {label:22s} {verdict:52s} [{note}]{flag}")
    print(f"\n  TOTAL cracked-tile crossings across the planned climb: {total_crossings}")
    print("  ⇒ every one is a tile where a BIKELESS bot FALLS when the chapter did not intend to.")

    # ------------------------------------------------ IS A CRACK-FREE CLIMB POSSIBLE?
    print("\n" + "-" * 94)
    print("MEASUREMENT 4 — is there a CRACK-FREE route? (cracked tiles made impassable)")
    print("-" * 94)
    blocked_legs = []
    for label, floor, src, dst, _note, expect_refused in LEGS:
        if expect_refused:
            continue
        m = getattr(MapRSE, floor)
        safe = plan(m, src, dst, block=cracked[floor])
        if safe is None:
            blocked_legs.append(label)
            print(f"  {label:22s} ‼ NO CRACK-FREE ROUTE")
        else:
            print(f"  {label:22s} crack-free route exists: {len(safe)} wp")

    # --------------------------------------------------------- FALSE-BLOCK RISK
    print("\n" + "-" * 94)
    print("MEASUREMENT 5 — object templates per floor (the Sootopolis false-block risk)")
    print("-" * 94)
    for name in FLOORS:
        m = getattr(MapRSE, name)
        try:
            count = len(get_map_data(m, (0, 0)).objects)
        except Exception as error:
            count = f"UNREADABLE ({type(error).__name__})"
        print(f"  {name:22s} {count} object template(s)")
    print("  ⇒ a floor with ZERO templates cannot suffer the loadedness false-block that sealed")
    print("    the Sootopolis pocket. Floors with templates need the same care leg 3 step 0 took.")

    _restore()

    # --------------------------------------------------------------- THE VERDICT
    print("\n" + "=" * 94)
    print("VERDICT")
    print("=" * 94)
    if surprises:
        print("  ‼ READINGS THAT CONTRADICT THE ATLAS — investigate before building:")
        for s in surprises:
            print(f"     - {s}")
    else:
        print("  The atlas's route SHAPE is confirmed by production: both sealed pockets refuse,")
        print("  and the post-fall walk works. The atlas's STEP COUNTS differ (different layout,")
        print("  and steps are not waypoints) — do not quote them as expected waypoint counts.")
    if blocked_legs:
        print(f"\n  ⛔ NO CRACK-FREE ROUTE ON: {', '.join(blocked_legs)}")
        print("  ⇒ On the layout WE read, a bikeless bot cannot cross those floors at all. The")
        print("    story requires crossing them bikeless, so the story layout is almost certainly")
        print("    NOT the one we read. ‼ THE UNVERIFIED LINK: 'a walking player falls' is the")
        print("    atlas's decomp claim, not measured here. Settle it before building.")
        print("  ⇒ `navigate_to` IS UNSAFE ON THOSE FLOORS regardless of which layout is live.")
    print("\n  ⛔ NOT ANSWERABLE HERE, AND A DRIVE OWES EACH: which layout is live during the story")
    print("     climb; where the avatar RESTS after each warp; whether the fall is unconditional.")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
