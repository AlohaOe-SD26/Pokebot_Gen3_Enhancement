"""§Ch21 LEG 3, FIRST FACT: can the bot get OUT of the Sootopolis pocket after the Cave of Origin?

‼ WHY THIS EXISTS, AND WHY IT IS STATIC. `04-HANDOFF.md`'s queue opens leg 3 with
"THE POCKET-EXIT PROBE, NOT A BUILD", and the build spec
(`ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md` §3.4/§4.11/§5) calls the walk back out
of the ~343-tile north-west pocket **"the single largest un-measured risk in this whole area"**.
Every number in that section is a **re-implementation** — three agents wrote three BFS models
over the decomp layout binaries and agreed to the tile — and this project has measured that
**agreement is not a confidence signal**. Nothing in it was ever asked of `calculate_path`.

This probe asks PRODUCTION. It needs no emulation loop: `calculate_path` answers about any
(map, tile) pair off ROM layout data, so the whole question is seconds of static queries rather
than a ~25-minute drive. That matters because the cost of the drive is precisely what makes
people skip the measurement (`#24-ch21anchor`'s own filing says so).

‼ WHAT IT CANNOT ANSWER, STATED UP FRONT. It does **not** walk. It cannot tell you whether
`navigate_to` completes, whether a wild encounter interrupts, or where the (9,20) warp really
lands (§4.11 — decomp-established as SOOTOPOLIS_CITY (31,16), still never observed live). Those
need the live driver. What this settles is the PLANNER's answer, which is the thing leg 3's
design actually turns on.

--------------------------------------------------------------------------------------------
THE MECHANISM UNDER TEST (`modules/map_path.py`, the passability rule)
--------------------------------------------------------------------------------------------
`active_objects` is built from `get_map_objects()`, which is CAMERA-RANGE limited, and the
tile test is LOADEDNESS, never occupancy:

    if (tile.dynamic_collision_flag is None
            and tile.dynamic_object_id
            and (tile.map.map_group_and_number, tile.dynamic_object_id) not in active_objects):
        return False

⇒ a ROM-template object tile is impassable whenever that object is **not currently loaded**.
The bot reads ROM templates, never the save-block copy that `setobjectxyperm` writes, so after
the escort moves Steven to (32,18) the planner still guards his template tile (20,36).

--------------------------------------------------------------------------------------------
HOW THE COUNTERFACTUAL IS ASKED — and why the fault injection is legitimate
--------------------------------------------------------------------------------------------
"Would the pocket open if Steven were loaded?" cannot be asked by observation: loadedness is a
function of where the player is standing, and the player is in the cave. So the probe patches
`map_path.get_map_objects` to return synthetic loaded objects and re-asks.

⛔ A fault-injection rig is worthless unless it is shown to reproduce something real. **CONTROL 3
does exactly that**: it replays the state-2 geometry (Steven local_id 7 on (20,36), Boy2 15 on
(19,37), asking from (21,36)) and must return **98 waypoints** — the number `--driver
ch21leg2probe` measured LIVE on 2026-08-27. If the rig cannot reproduce a known live reading,
every counterfactual below is noise and the probe says so instead of printing a table.

Object identities are MEASURED, not inferred: `harness_sandbox_ch21leg2probe_*.log` logged
`OBJ-at-21-36 [... (15, (19, 37)), (7, (20, 36)) ...]`. ⛔ Do not re-derive them from porymap
list order — the spec explicitly flags that as an inference.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_pocket_exit.py
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
from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import get_event_flag, get_event_var
from modules.player import get_player_avatar

SAVE = REPO / "tools" / "story-dev" / "saves" / "post_wallace.ss1"

CITY = MapRSE.SOOTOPOLIS_CITY
B1F = MapRSE.CAVE_OF_ORIGIN_B1F
F1 = MapRSE.CAVE_OF_ORIGIN_1F
ENTR = MapRSE.CAVE_OF_ORIGIN_ENTRANCE

# ⛔ TWO DIFFERENT TILES, AND CONFLATING THEM IS THE WHOLE POINT OF §4.11.
WARP_TARGET = (31, 16)      # what the ROM warp table and the decomp both name — the warp EVENT tile
LANDING = (31, 17)          # where the AVATAR ACTUALLY RESTS — MEASURED LIVE 2026-08-27 by
                            # `--driver ch21pocket` (`L1 ENTR->CITY: landed SOOTOPOLIS_CITY(31,17)`).
                            # Gen3 auto-steps the player one tile clear of a doorway warp. Every
                            # measurement below is taken FROM HERE, because this is where the bot is.
POKE_CENTER = (43, 31)      # ⚠ this is the Poke Center DOOR, i.e. a WARP tile; a path TO it ends
                            # INSIDE the building (map_path.py's destination-warp exception)
PC_FRONT = (43, 32)         # the tile in FRONT of the door — a real city tile, used for the
                            # "and the bot can continue" question, which a door tile cannot answer
DIVE_TILE = (29, 53)        # leg 1's arrival tile; the swim-out starts near here
STEVEN_APPROACH = (21, 36)

STEVEN_ID, STEVEN_TEMPLATE, STEVEN_STATE3 = 7, (20, 36), (32, 18)
BOY2_ID, BOY2_TEMPLATE = 15, (19, 37)

CONTROL3_EXPECTED_WP = 98   # measured LIVE by --driver ch21leg2probe, 2026-08-27


# ‼ FAULT HOOK — `POKEBOT_POCKET_FAULT=rig` breaks the injection rig on purpose (the synthetic
# objects claim the wrong map, so `active_objects` never matches a tile's `dynamic_object_id`).
# CONTROL 3 MUST go red under it. A control that cannot fail is decoration, and this project has
# measured that a gate nobody fault-tested is worse than no gate at all.
_FAULT = _os.environ.get("POKEBOT_POCKET_FAULT", "").strip()


class _LoadedObject:
    """A stand-in for a loaded map object, shaped exactly as `map_path` reads one."""

    def __init__(self, local_id: int, coords: tuple[int, int]) -> None:
        self.flags = []                      # deliberately NOT the player
        self.map_group_and_number = (0, 0) if _FAULT == "rig" else CITY.value
        self.local_id = local_id
        self.current_coords = coords
        self.previous_coords = coords


def _with_loaded(objects: list[_LoadedObject]):
    mp.get_map_objects = lambda: list(objects)


def _restore() -> None:
    mp.get_map_objects = get_map_objects


def path_len(src_map, src, dst_map, dst) -> int | None:
    """Waypoint count, or None if the planner refuses. A refusal IS a reading."""
    try:
        return len(calculate_path((src_map, src), (dst_map, dst)))
    except PathFindingError:
        return None
    except Exception:
        return None


def verdict(n: int | None) -> str:
    return f"OK {n} wp" if n is not None else "REFUSED"


def main() -> int:
    print("=" * 94)
    print("§Ch21 LEG 3 — POCKET-EXIT PROBE (static; production's planner is the oracle)")
    print("=" * 94)

    context.emulator.load_save_state(SAVE.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    at = tuple(avatar.local_coordinates)
    try:
        here = MapRSE(tuple(avatar.map_group_and_number)).name
    except Exception:
        here = f"UNKNOWN{tuple(avatar.map_group_and_number)}"
    state = get_event_var("SOOTOPOLIS_CITY_STATE")
    wallace = get_event_flag("WALLACE_GOES_TO_SKY_PILLAR")

    print(f"\nFIXTURE  {SAVE.name}: {here} {at}  state={state}  "
          f"WALLACE_GOES_TO_SKY_PILLAR={wallace}")
    print(f"         objects loaded here: "
          f"{[(o.local_id, tuple(o.current_coords)) for o in get_map_objects()]}")

    # ⛔ ANTI-VACUITY. A probe run on the wrong era measures nothing (playbook §0b Q3).
    premise_ok = here == "CAVE_OF_ORIGIN_B1F" and state == 3 and wallace
    if not premise_ok:
        print("\n‼ VACUOUS — the fixture is not leg 3's premise (expected CAVE_OF_ORIGIN_B1F, "
              "state 3, WALLACE_GOES_TO_SKY_PILLAR set). Nothing below is about leg 3.")
        return 1

    # ------------------------------------------------------------ THE WARP CHAIN
    # §4.11 is "leg 3's first fact": the (9,20) exit warp's landing tile is decomp-established
    # as (31,16) but was never read from OUR side. This reads it out of the ROM warp table via
    # `PathTile.warps_to` — an INDEPENDENT route to the same claim.
    # ⛔ An earlier attempt used `get_map_data(...).warps_to` and returned ZERO warps on three
    # maps that certainly have them. A scan that cannot answer positive is not evidence, so the
    # control below must find the warp the atlas already documents or the section is discarded.
    print("\n" + "-" * 94)
    print("MEASUREMENT 0 — the warp chain out of the cave, read from the ROM (§4.11)")
    print("-" * 94)

    def warps_of(m: MapRSE, _span: int, only_to: str | None = None) -> list[str]:
        # ⛔ BOUND THE SCAN BY THE MAP'S REAL SIZE. Tile lookup is a FLAT index (y*width + x), so an
        # out-of-bounds x silently WRAPS into the next row and reports the same warp twice under a
        # phantom coordinate: on the 19-wide Entrance, (28,4) and (9,5) are both index 104. A first
        # version of this scan ran a fixed 40x40 and printed FOUR warps for Entrance where the
        # decomp has TWO. Measured sizes: Entrance (19,26), 1F (23,23), B1F (19,19).
        try:
            width, height = get_map_data(m, (0, 0)).map_size
        except Exception:  # noqa: BLE001 - without the size the scan cannot be trusted at all
            return ["     (map size unreadable — scan skipped rather than reported unbounded)"]
        rows = []
        for y in range(height):
            for x in range(width):
                try:
                    tile = mp._find_tile_by_local_coordinates(m.value, (x, y))
                except Exception:
                    continue
                w = getattr(tile, "warps_to", None)
                if not w:
                    continue
                try:
                    dest = MapRSE(tuple(w[0])).name
                except Exception:
                    dest = str(tuple(w[0]))
                if only_to is not None and dest != only_to:
                    continue
                rows.append(f"     ({x},{y}) --warp--> {dest} {tuple(w[1])}")
        return rows

    _with_loaded([])
    for m, only in [(ENTR, None), (F1, None), (B1F, None),
                    (CITY, "CAVE_OF_ORIGIN_ENTRANCE")]:
        rows = warps_of(m, 0, only)
        print(f"  {m.name}{' (cave warp only)' if only else ''}:")
        print("\n".join(rows) if rows else "     (none found)")
    city_rows = warps_of(CITY, 0, "CAVE_OF_ORIGIN_ENTRANCE")
    _restore()
    warp_control = len(city_rows) > 0
    print(f"\n  C0 scan sees the DOCUMENTED Sootopolis->CaveOfOrigin warp: "
          f"{'PASS' if warp_control else 'FAIL — scan is blind, discard MEASUREMENT 0'}")
    print(f"  ⛔ The table names the warp EVENT tile {WARP_TARGET}. The AVATAR RESTS ON {LANDING} "
          f"— MEASURED LIVE")
    print("    2026-08-27; two of the three return warps auto-step one tile clear of the doorway")
    print("    ((9,5)->rests (9,6)), and B1F->1F does not ((14,5) exactly). Everything below is")
    print("    measured FROM THE RESTING TILE.")

    # ---------------------------------------------------------------- CONTROLS
    print("\n" + "-" * 94)
    print("CONTROLS — a probe that finds nothing is indistinguishable from one that cannot see")
    print("-" * 94)

    c1 = path_len(B1F, (9, 14), B1F, (9, 3))
    c1_ok = c1 is not None
    print(f"  C1 planner answers on the player's own map  B1F (9,14)->(9,3): "
          f"{verdict(c1)}  {'PASS' if c1_ok else 'FAIL'}")

    c2a = path_len(CITY, LANDING, CITY, WARP_TARGET)
    c2b = path_len(CITY, WARP_TARGET, CITY, LANDING)
    c2_ok = c2a is not None and c2b is not None
    print(f"  C2 planner answers about a map the player is NOT on  "
          f"{LANDING}<->{WARP_TARGET}: {verdict(c2a)}/{verdict(c2b)}  "
          f"{'PASS' if c2_ok else 'FAIL'}")

    _with_loaded([_LoadedObject(STEVEN_ID, STEVEN_TEMPLATE),
                  _LoadedObject(BOY2_ID, BOY2_TEMPLATE)])
    # ⛔ C3's TARGET IS THE WARP TILE, NOT THE RESTING TILE. The 98 wp it must reproduce was
    # measured live TO (31,16); re-pointing it at (31,17) silently changes the subject and it
    # returns 97. (That is not hypothetical — this control caught exactly that edit.)
    c3 = path_len(CITY, STEVEN_APPROACH, CITY, WARP_TARGET)
    _restore()
    c3_ok = c3 == CONTROL3_EXPECTED_WP
    print("  C3 the FAULT-INJECTION RIG reproduces a LIVE reading  "
          "(21,36)->(31,16) with Steven+Boy2 loaded at their state-2 tiles:")
    print(f"     got {verdict(c3)}, live-measured {CONTROL3_EXPECTED_WP} wp  "
          f"{'PASS' if c3_ok else 'FAIL'}")

    if not (c1_ok and c2_ok and c3_ok):
        print("\n‼ CONTROLS FAILED — every measurement below is UNTRUSTED. Do not act on it.")
        return 1
    print("\n  ALL CONTROLS PASS — the planner answers, and the rig reproduces a live number.")

    # ------------------------------------------------------- THE SEAL, AND WHY
    print("\n" + "-" * 94)
    print("MEASUREMENT 1 — is the landing tile sealed, and is LOADEDNESS the reason?")
    print("-" * 94)

    # ‼ THE CUT TILES ARE IN THE MATRIX ON PURPOSE. Without them a refusal cannot be ATTRIBUTED
    # — an adversarial review of the first version named exactly this gap.
    targets = [
        ("-> (43,32) PC front    ", PC_FRONT),
        ("-> (29,53) dive/arrival", DIVE_TILE),
        ("-> (21,36) Steven appr.", STEVEN_APPROACH),
        ("-> (20,36) Steven tile ", STEVEN_TEMPLATE),
        ("-> (19,37) Boy2 tile   ", BOY2_TEMPLATE),
        ("-> (31,22) inside pocket", (31, 22)),
    ]
    arms = {
        "A nothing loaded          ": [],
        "B Steven@(32,18) [STATE 3]": [_LoadedObject(STEVEN_ID, STEVEN_STATE3)],
        "E Boy2 loaded ELSEWHERE   ": [_LoadedObject(BOY2_ID, (25, 45))],
        "F Steven@(20,36) [state 2]": [_LoadedObject(STEVEN_ID, STEVEN_TEMPLATE)],
    }
    table: dict[tuple[str, str], str] = {}
    for arm, objects in arms.items():
        _with_loaded(objects)
        print(f"\n  {arm}   (from {LANDING})")
        for label, dst in targets:
            v = verdict(path_len(CITY, LANDING, CITY, dst))
            table[(arm[0], label)] = v
            print(f"      {label}  {v}")
    _restore()

    print("\n  DISCRIMINATION — arms that AGREE prove nothing (a vacuous A/B):")
    discriminating = 0
    for label, _ in targets:
        row = [table[(a, label)] for a in "ABEF"]
        differ = len(set(row)) > 1
        discriminating += 1 if differ else 0
        print(f"    {label}  A={row[0]:9s} B={row[1]:9s} E={row[2]:9s} F={row[3]:9s}"
              f"  {'<<< ARMS DIFFER' if differ else 'arms agree'}")
    print(f"\n  {discriminating} of {len(targets)} targets discriminate between the arms.")

    # ---------------------------------------------------- SIZE OF THE DANGER
    print("\n" + "-" * 94)
    print("MEASUREMENT 2 — how much of the escape route is fatal to a RE-PLAN?")
    print("-" * 94)
    print("  `navigate_to` restarts a FRESH plan on a waypoint timeout (walking.py). If a")
    print("  re-plan is taken while Steven is unloaded, it refuses and the leg dies. So: walk")
    print("  the route the bot WOULD take, and ask the pessimistic question at every tile.")

    _with_loaded([_LoadedObject(STEVEN_ID, STEVEN_STATE3)])
    try:
        waypoints = calculate_path((CITY, LANDING), (CITY, PC_FRONT))
    except Exception as error:
        _restore()
        print(f"  ‼ could not compute the escape route: {type(error).__name__}: {error}")
        return 1

    # ⛔ ONLY CITY WAYPOINTS ARE A FAIR QUESTION. The route's tail warps INTO the Poke Center
    # (the destination-warp exception at map_path.py:841 lets a warp tile be the destination),
    # so its last waypoint is an INTERIOR tile. Asking "path from (7,8) to (43,31) on
    # SOOTOPOLIS_CITY" mis-types an interior coordinate as a city one and refuses for a reason
    # that has nothing to do with the pocket. Counting it would inflate the danger figure.
    city_route = [(i, tuple(w.coordinates)) for i, w in enumerate(waypoints)
                  if tuple(w.map) == CITY.value]
    off_map = len(waypoints) - len(city_route)

    _with_loaded([])          # the pessimistic regime: nothing loaded
    danger = [(i, t) for i, t in city_route
              if path_len(CITY, t, CITY, PC_FRONT) is None]
    _restore()

    safe = [i for i, _ in city_route if not any(d[0] == i for d in danger)]
    first_safe = safe[0] if safe else None
    first_safe_tile = next((t for i, t in city_route if i == first_safe), None)
    print(f"\n  escape route (Steven loaded)          : {len(waypoints)} waypoints "
          f"({len(city_route)} on SOOTOPOLIS_CITY, {off_map} off-map/interior — not tested)")
    print(f"  city waypoints where a RE-PLAN REFUSES: {len(danger)} of {len(city_route)}")
    print(f"  first waypoint safe to re-plan from   : index {first_safe} = {first_safe_tile}")
    if danger:
        print(f"  first 8 danger tiles                  : {danger[:8]}")
        print(f"  last danger tile                      : {danger[-1]}")

    # ------------------------------------------------------------ POCKET SIZE
    print("\n" + "-" * 94)
    print("MEASUREMENT 3 — how big is the sealed pocket? (spec's re-implementations say ~343)")
    print("-" * 94)
    _with_loaded([])
    in_bounds = 0
    reachable = 0
    for y in range(60):
        for x in range(60):
            if (x, y) == LANDING:
                continue
            try:
                mp._find_tile_by_local_coordinates(CITY.value, (x, y))
            except Exception:
                continue
            in_bounds += 1
            if path_len(CITY, LANDING, CITY, (x, y)) is not None:
                reachable += 1
    _restore()
    print(f"  in-bounds tiles queried: {in_bounds}")
    print(f"  reachable from {LANDING} with nothing loaded: {reachable}")

    # ------------------------------------------------- INTRA-CAVE RETURN LEGS
    print("\n" + "-" * 94)
    print("MEASUREMENT 4 — the intra-cave return, by production rather than by re-implementation")
    print("-" * 94)
    legs = [
        ("B1F      (9,14) -> (9,3)  ", B1F, (9, 14), (9, 3), 21),
        ("1F       (14,5) -> (11,17)", F1, (14, 5), (11, 17), 23),
        ("ENTRANCE (9,5)  -> (9,20) ", ENTR, (9, 5), (9, 20), 15),
    ]
    total = 0
    for label, m, a, b, re_impl in legs:
        n = path_len(m, a, m, b)
        total += n or 0
        note = "" if n is None else (
            "matches" if n == re_impl
            else f"vs {re_impl} re-impl STEPS (a step count is not a waypoint count)")
        print(f"  {label}  {verdict(n):10s}  {note}")
    print(f"  --> intra-cave return total: {total} waypoints, across 3 warp transitions")

    print("\n" + "=" * 94)
    print("READ THIS NARROWLY. Everything above is the PLANNER's answer, measured statically.")
    print("Still UNMEASURED and needing the live driver: where the (9,20) warp actually lands")
    print("(§4.11), whether `navigate_to` completes the walk, and the cave's encounter pressure")
    print("(§4.10). A static OK is evidence the leg is worth driving; it is not the standard.")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
