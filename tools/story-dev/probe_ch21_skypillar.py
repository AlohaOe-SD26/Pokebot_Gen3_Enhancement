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

⛔⛔ **AND THE FIRST VERSION OF THIS PROBE DREW THE WRONG CONCLUSION FROM THAT — AN ADVERSARIAL
REVIEW REFUTED IT (2026-08-27).** It reported "there is NO crack-free route across 2F or 4F", and
the handoff carried that as leg 3's BLOCKER. The measurement was real but it **answered the wrong
question**: it blocked the DEFAULT crack set (38 on 2F, 34 on 4F), of which **33 and 29 are SOLID
GROUND on the CLEAN layout the story actually runs on**. Blocking tiles that are not cracked in the
story manufactures a blocker that does not exist. MEASUREMENT 4 now asks BOTH questions side by
side, and the STORY column is the one that decides the build: **every leg has a crack-free route,
and on 4F banning the five real cracks costs NOTHING (29 wp either way).**

What remains true, and is the real constraint:
  1. `map_path.py` does not model `"Cracked Floor"` AT ALL (`grep -n Cracked` = 0 hits), so the
     planner neither proposes the deliberate fall nor avoids a real crack. ⛔ For a WALKING bot a
     cracked tile is TERMINAL — you fall on ENTRY, you do not "cross" it — so the chapter must ban
     the five CLEAN cracks explicitly rather than trust an A* tie-break.
  2. The bot is **BIKELESS** at this point in the story (`RECEIVED_BIKE` False, no bike in the
     bag on `post_wallace.ss1`), and the Sky Pillar's cracked floors are survived by SPEED —
     a walking player falls. That is WHY the story uses the CLEAN layouts at all.
⇒ A bikeless bot cannot cross 2F on the layout we read, yet the story requires exactly that.
   ✅ **SETTLED the same day by a decomp recon pass: we read the POST-GAME layout.** Six floors
   swap to `*_CLEAN` in `OnTransition`, gated `call_if_lt VAR_SKY_PILLAR_STATE, 2`, so the STORY
   climb runs entirely on CLEAN (2F_Clean has ZERO cracks). `setmaplayoutindex` writes only
   `gSaveBlock1Ptr->mapLayoutId` and the live `gMapHeader` — never the ROM table this probe reads.

⇒ CONSEQUENCE FOR THE BUILD, and it is milder than it first looked: the misread is **PESSIMISTIC**
— DEFAULT-walkable ⊆ CLEAN-walkable on all five climb floors with zero exceptions — so a route
found here can never walk the bot into a story-time WALL on 1F-5F. ⛔ TWO EXCEPTIONS INVERT IT:
`SKY_PILLAR_TOP` (31 static-open tiles are CLEAN walls) and `ROUTE131` (116, swapped
UNCONDITIONALLY). And because a crack-free route costs EXACTLY the same, which one A* returns is a
TIE-BREAK — so the chapter must BAN 4F's five CLEAN-cracked tiles explicitly rather than trust it.

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

#: ⛔⛔ THE CRACK SET THAT MATTERS FOR THE STORY IS THE *CLEAN* ONE, NOT THE DEFAULT ONE.
#: An adversarial review REFUTED the first version of MEASUREMENT 4: it blocked the DEFAULT set
#: (38 on 2F, 34 on 4F) and concluded "NO crack-free route across 2F or 4F", which the handoff
#: then carried as leg 3's BLOCKER. But 33 of those 38 and 29 of those 34 are NOT cracked on the
#: CLEAN layout the story actually runs on — so the measurement was, in the reviewer's words,
#: "the ANSWER TO THE WRONG QUESTION". Blocking tiles that are solid ground in the story
#: manufactures a blocker that does not exist.
#: Source of the CLEAN sets: the decomp's own `SkyPillar_*_Clean/map.bin`, decoded by
#: `probe_skypillar_clean_layout.py` (2F_Clean has ZERO; 4F_Clean retains five).
CLEAN_CRACKED_BY_FLOOR = {
    "SKY_PILLAR_1F": set(),
    "SKY_PILLAR_2F": set(),
    "SKY_PILLAR_3F": set(),
    "SKY_PILLAR_4F": ATLAS_4F_CRACKED,
    "SKY_PILLAR_5F": set(),
    "SKY_PILLAR_TOP": set(),
    "SKY_PILLAR_ENTRANCE": set(),   # does not layout-swap
    "SKY_PILLAR_OUTSIDE": set(),    # does not layout-swap
}

#: The three LIVE resting-tile readings measured 2026-08-27, used to blind-test the derived rule.
#: ⛔ The third is the DISCRIMINATING NEGATIVE: without it, a rule that always predicts "+1 south"
#: would score 2/3 and look convincing.
LIVE_RESTING_CASES = [
    ("Entrance(9,20)->CITY", "SOOTOPOLIS_CITY", (31, 16), (31, 17)),
    ("1F(11,17)->ENTRANCE", "CAVE_OF_ORIGIN_ENTRANCE", (9, 5), (9, 6)),
    ("B1F(9,3)->1F  [NEGATIVE]", "CAVE_OF_ORIGIN_1F", (14, 5), (14, 5)),
]

#: Warps the recon says are ARROW WARPS — they do NOT fire on step, so a walk-only planner stalls
#: forever with no error. The control is an ordinary staircase, which must NOT read as one.
ARROW_WARPS = [
    ("SKY_PILLAR_ENTRANCE", (6, 16)), ("SKY_PILLAR_ENTRANCE", (14, 4)),
    ("SKY_PILLAR_1F", (6, 13)), ("SKY_PILLAR_1F", (7, 13)),
]
ARROW_CONTROL = ("SKY_PILLAR_1F", (10, 1))

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
    print("MEASUREMENT 4 — is there a CRACK-FREE route? Asked TWICE, because WHICH crack set you")
    print("  block is the whole question. ⛔ For a WALKING bot a cracked tile is TERMINAL — you")
    print("  fall on entry, you do not 'cross' it — so a usable route must not ENTER one.")
    print("-" * 94)
    blocked_legs = []
    for label, floor, src, dst, _note, expect_refused in LEGS:
        if expect_refused:
            continue
        m = getattr(MapRSE, floor)
        clean_set = CLEAN_CRACKED_BY_FLOOR.get(floor, set())
        story = plan(m, src, dst, block=clean_set)      # the STORY question
        postgame = plan(m, src, dst, block=cracked[floor])  # the POST-GAME question
        story_txt = f"{len(story)} wp" if story is not None else "REFUSED"
        post_txt = f"{len(postgame)} wp" if postgame is not None else "REFUSED"
        if story is None:
            blocked_legs.append(label)
        print(f"  {label:22s} STORY(block {len(clean_set):2d} CLEAN cracks): {story_txt:9s}"
              f"   post-game(block {len(cracked[floor]):2d}): {post_txt}")
    print("\n  ⛔ THE STORY COLUMN IS THE ONE THAT DECIDES THE BUILD. An adversarial review REFUTED")
    print("     the first version of this check, which reported only the post-game column and so")
    print("     concluded 'NO crack-free route across 2F or 4F' — a blocker that does not exist,")
    print("     because 33 of 2F's 38 and 29 of 4F's 34 default cracks are SOLID GROUND on CLEAN.")

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

    # ------------------------------------------- VALIDATING THE RECON'S OWN CLAIMS
    # ‼ WHY THIS IS HERE. The Sky Pillar recon pass (2026-08-27) produced claims whose two
    # adjudicating critics DIED on an account session limit, leaving them UNVERIFIED. CLAUDE.md's
    # standing directive is that an agent's output is a NOTE and CLAUDE VALIDATES IT. These three
    # checks settle the load-bearing ones against PRODUCTION's own tile data, so the answer is
    # re-runnable instead of a number in a chat log.
    print("")
    print("-" * 94)
    print("MEASUREMENT 6 — validating the recon's load-bearing claims against our own tile data")
    print("-" * 94)

    def behaviour(m: MapRSE, coords: tuple[int, int]) -> str:
        try:
            return str(getattr(get_map_data(m, coords), "tile_type", "?"))
        except Exception as error:  # noqa: BLE001 - an unreadable tile is itself a reading
            return f"UNREADABLE:{type(error).__name__}"

    # (a) THE RESTING-TILE RULE. Claim: `SetUpWarpExitTask()` branches on the behaviour AT THE WARP
    # TARGET — the door family exits one tile SOUTH, anything else rests exactly.
    rule_hits = 0
    for label, map_name, target, observed in LIVE_RESTING_CASES:
        m = getattr(MapRSE, map_name)
        beh = behaviour(m, target)
        predicted = (target[0], target[1] + 1) if "Door" in beh else target
        ok = predicted == observed
        rule_hits += ok
        verdict_word = "MATCH" if ok else "MISMATCH"
        print(f"  (a) {label:26s} {str(target):8s} = {beh:20s} "
              f"predict {str(predicted):9s} live {observed}  {verdict_word}")
    rule_ok = rule_hits == len(LIVE_RESTING_CASES)
    print(f"      => blind test {rule_hits}/{len(LIVE_RESTING_CASES)} — "
          + ("RULE CONFIRMED by our own tile data" if rule_ok
             else "‼ RULE REFUTED — do not use it to predict Sky Pillar resting tiles"))

    # (b) THE FOUR ARROW WARPS.
    arrows_found = 0
    for map_name, coords in ARROW_WARPS:
        beh = behaviour(getattr(MapRSE, map_name), coords)
        is_arrow = "Arrow Warp" in beh
        arrows_found += is_arrow
        print(f"  (b) {map_name:22s} {str(coords):8s} = {beh:20s}"
              + ("  <-- ARROW WARP, does NOT fire on step" if is_arrow else ""))
    ctrl_beh = behaviour(getattr(MapRSE, ARROW_CONTROL[0]), ARROW_CONTROL[1])
    ctrl_ok = "Arrow Warp" not in ctrl_beh
    print(f"      control: {ARROW_CONTROL[0]} {ARROW_CONTROL[1]} = {ctrl_beh!r} — must NOT be an "
          f"arrow warp: {'PASS' if ctrl_ok else 'FAIL'}")
    arrows_ok = arrows_found == len(ARROW_WARPS) and ctrl_ok
    print(f"      => {arrows_found}/{len(ARROW_WARPS)} arrow warps "
          + ("CONFIRMED" if arrows_ok else "‼ NOT CONFIRMED"))

    # (c) THE 4F TIE-BREAK. Two recon agents CONTRADICTED each other: one said the stale model can
    # NEVER route onto a real CLEAN crack; the other that a crack-free route costs exactly the SAME,
    # making it a pure A* tie-break. Ask production what it ACTUALLY returns on this build.
    four = getattr(MapRSE, "SKY_PILLAR_4F")
    for label, src, dst in [("4F (11,1)->(5,4)", (11, 1), (5, 4)),
                            ("4F (7,1)->(3,1)", (7, 1), (3, 1))]:
        route = plan(four, src, dst)
        if route is None:
            print(f"  (c) {label:20s} REFUSED")
            continue
        crossed = [t for t in route if t in ATLAS_4F_CRACKED]
        decoy = "  ‼ HITS THE (9,4) DECOY — the climb would be WASTED" if (9, 4) in crossed else ""
        print(f"  (c) {label:20s} {len(route):3d} wp, crosses CLEAN-cracked: "
              f"{crossed if crossed else 'NONE'}{decoy}")
    print("      ⚠ NONE here means THIS BUILD's tie-break happens to be safe — never that it is")
    print("        GUARANTEED. Equal cost means a planner change could flip it silently, so the")
    print("        chapter must still BAN these five tiles explicitly. Banning them costs nothing.")

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
        print("  ⇒ On the layout WE read, a bikeless bot could not cross those floors at all.")
        print("  ✅ SETTLED 2026-08-27 (decomp): that is because WE READ THE POST-GAME LAYOUT. Six")
        print("     floors swap to *_CLEAN in OnTransition, gated `call_if_lt VAR_SKY_PILLAR_STATE,")
        print("     2`, so the STORY climb runs entirely on CLEAN — where 2F has ZERO cracks.")
        print("     `setmaplayoutindex` never touches the ROM table this probe reads.")
        print("  ⇒ The misread is PESSIMISTIC, not wrong: DEFAULT-walkable ⊆ CLEAN-walkable on all")
        print("    five climb floors (0 exceptions), so a route found here cannot walk the bot into")
        print("    a story-time WALL on 1F-5F. ⛔ EXCEPT `SKY_PILLAR_TOP` (31 static-open tiles are")
        print("    CLEAN walls) and `ROUTE131` (116, and it swaps UNCONDITIONALLY).")
    print("\n  ⛔ WHAT A DRIVE STILL OWES: confirmation of the resting tiles predicted by the rule")
    print("     validated in MEASUREMENT 6(a); whether the fall is unconditional for a WALKING")
    print("     player; and the SECOND fall the descent needs (Top->5F->4F(3,1) lands in a 12-tile")
    print("     west pocket with no walking exit — omit it and the bot summits and is STRANDED).")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
