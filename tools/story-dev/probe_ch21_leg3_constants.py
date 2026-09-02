"""§Ch21 LEG 3 — EVERY CONSTANT THE LEG WILL HARDCODE, RE-ASKED OF PRODUCTION FROM THE FIXTURE.

‼ WHY THIS EXISTS. Leg 3's BUILD SPEC hardcodes ~12 coordinates and ~8 waypoint counts, each
tagged MEASURED by a recon agent. This project's own rule is that an agent's reading is a NOTE,
never truth, and that the authoritative check is production's own answer over our own ROM. Two of
the spec's "MEASURED" claims are already known to be wrong elsewhere in the tree
(`VISITED_SOOTOPOLIS_CITY`, and the atlas's "35 wp and a detour"), so the rest are not exempt.

⇒ This probe loads the PINNED leg-3 fixture and re-asks `calculate_path` / the tile reader / the
flag reader for every number leg 3 is about to bake in. It runs OFFLINE with no emulation loop
(30 settling frames only), takes seconds, and it is the cheapest possible way to discover that a
constant is wrong BEFORE a one-shot ~55,000-frame swim depends on it.

--------------------------------------------------------------------------------------------
WHAT IT DELIBERATELY DOES **NOT** DO
--------------------------------------------------------------------------------------------
⛔ It does NOT emulate the leg. Paths through SOOTOPOLIS_CITY depend on which NPCs are camera-
loaded at a live moment, and this fixture stands on CAVE_OF_ORIGIN_B1F, so no Sootopolis object is
loaded at all. That is not a limitation to work around — it is a CONTROL (C3 below): with nothing
loaded the planner is MEASURED to refuse the pocket escape, which is exactly why leg 3 must assert
Steven is camera-loaded before it plans. A run of this probe that found the pocket path would mean
the recon's Steven-gate rationale was wrong.

⛔ It does NOT prove which layout ROUTE131 loads at runtime. See
`probe_ch21_route131_tail.py` for the SET A / SET B adjudication, and note that BOTH probes are
static: the runtime layout reading is owed by the first live drive.

--------------------------------------------------------------------------------------------
CONTROLS
--------------------------------------------------------------------------------------------
C1  the fixture is the one we think it is: CAVE_OF_ORIGIN_B1F (9,14), state 3, Wallace flag set.
    ⛔ Asserted by IDENTITY (map + tile + var), never by "a save state loaded".
C2  the planner is ALIVE in this process: a control path that MUST succeed (ROUTE131 (40,19) ->
    (28,15), production's own published 16) and a control that MUST fail (ROUTE131 (28,15) -> the
    door, which the PRE-BUILD GATE measured as no route in SET A). A probe where everything
    refuses is indistinguishable from one where the planner is broken.
C3  the pocket escape MUST refuse from this fixture (nothing loaded). If it succeeds, the recon's
    entire Steven-gate rationale is wrong and leg 3's S5 must be re-thought.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_leg3_constants.py
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.memory import get_event_flag, get_event_var

SAVE = pathlib.Path(__file__).resolve().parent / "saves" / "post_wallace.ss1"

CITY = MapRSE.SOOTOPOLIS_CITY
ENTRANCE = MapRSE.SKY_PILLAR_ENTRANCE
R131 = MapRSE.ROUTE131
R126 = MapRSE.ROUTE126

#: Every row is (label, the SPEC's claim, how it is checked). ⛔ The spec's number is written down
#: so a MISMATCH is visible as a mismatch, never silently absorbed into "what we measured".
_results: list[tuple[str, str, str, bool | None]] = []


def record(label: str, expected: str, got: str, ok: bool | None) -> None:
    _results.append((label, expected, got, ok))
    mark = "  " if ok is None else ("OK" if ok else "‼ ")
    print(f"  {mark} {label:<52} spec: {expected:<28} got: {got}")


def plan(source_map, source, destination_map, destination):
    """calculate_path or None. ⛔ It RAISES on failure; a bare call would abort the probe."""
    try:
        return calculate_path((source_map, source), (destination_map, destination))
    except PathFindingError:
        return None
    except Exception as error:                       # a broken planner must not read as "no path"
        print(f"      ⛔ UNEXPECTED {type(error).__name__}: {error}")
        return None


def describe(path) -> str:
    if path is None:
        return "NO ROUTE"
    last = path[-1]
    return (f"{len(path)} wp, ends {tuple(last.coordinates)} on map {tuple(last.map)}, "
            f"is_warp={last.is_warp}")


def per_map_split(path) -> str:
    if path is None:
        return "-"
    counts: dict[tuple[int, int], int] = {}
    for waypoint in path:
        counts[tuple(waypoint.map)] = counts.get(tuple(waypoint.map), 0) + 1
    name = {tuple(m.value): m.name for m in MapRSE}
    return "  ".join(f"{name.get(k, k)}:{v}" for k, v in counts.items())


def main() -> int:
    print("=" * 100)
    print("§Ch21 LEG 3 — THE CONSTANTS, RE-ASKED OF PRODUCTION (offline, no emulation loop)")
    print("=" * 100)

    context.emulator.load_save_state(SAVE.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    # ------------------------------------------------------------------ C1: fixture identity
    print("")
    print("-" * 100)
    print("CONTROL 1 — the fixture is the one we think it is (asserted by IDENTITY)")
    print("-" * 100)
    avatar = get_player_avatar()
    here_map = tuple(avatar.map_group_and_number)
    here_tile = tuple(avatar.local_coordinates)
    b1f = MapRSE.CAVE_OF_ORIGIN_B1F.value
    state = get_event_var("SOOTOPOLIS_CITY_STATE")
    pillar = get_event_var("SKY_PILLAR_STATE")
    wallace = get_event_flag("WALLACE_GOES_TO_SKY_PILLAR")
    c1_ok = here_map == b1f and here_tile == (9, 14) and state == 3 and bool(wallace)
    print(f"  map                       : {here_map}  (CAVE_OF_ORIGIN_B1F = {b1f})")
    print(f"  tile                      : {here_tile}   spec: (9,14)")
    print(f"  SOOTOPOLIS_CITY_STATE     : {state}       spec: 3")
    print(f"  SKY_PILLAR_STATE          : {pillar}       spec: 0")
    print(f"  WALLACE_GOES_TO_SKY_PILLAR: {bool(wallace)}    spec: True")
    print(f"  ⇒ {'PASS' if c1_ok else 'FAIL — every number below is about the WRONG SAVE'}")
    if not c1_ok:
        return 1

    # ------------------------------------------------------------------ C2: the planner is alive
    print("")
    print("-" * 100)
    print("CONTROL 2 — the planner is ALIVE: one path that must SUCCEED, one that must REFUSE")
    print("-" * 100)
    must_succeed = plan(R131, (40, 19), R131, (28, 15))
    must_refuse = plan(R131, (28, 15), R131, (36, 6))
    c2a = must_succeed is not None and len(must_succeed) == 16
    c2b = must_refuse is None
    print(f"  MUST SUCCEED  R131 (40,19) -> (28,15) : {describe(must_succeed)}   "
          f"(production's published 16)  {'PASS' if c2a else 'FAIL'}")
    print(f"  MUST REFUSE   R131 (28,15) -> (36,6)  : {describe(must_refuse)}   "
          f"(the door is invisible in SET A)  {'PASS' if c2b else 'FAIL'}")
    c2_ok = c2a and c2b
    print(f"  ⇒ {'PASS — the planner both finds and refuses, so a refusal below means something'
          if c2_ok else 'FAIL — do not trust any path result below'}")
    if not c2_ok:
        return 1

    # ------------------------------------------------------------------ C3: the pocket must refuse
    print("")
    print("-" * 100)
    print("CONTROL 3 — with NOTHING loaded the pocket escape MUST refuse (the Steven-gate premise)")
    print("-" * 100)
    pocket = plan(CITY, (31, 17), CITY, (43, 32))
    to_dive = plan(CITY, (31, 17), CITY, (29, 53))
    c3_ok = pocket is None and to_dive is None
    print(f"  CITY (31,17) -> (43,32) [the PC front] : {describe(pocket)}")
    print(f"  CITY (31,17) -> (29,53) [the dive tile]: {describe(to_dive)}")
    if c3_ok:
        print("  ⇒ PASS — both refuse, exactly as the recon measured. Leg 3's Steven gate is")
        print("     therefore load-bearing: without him camera-loaded the crossing cannot be planned.")
    else:
        print("  ⇒ ‼ FAIL — a path exists with nothing loaded. The recon's Steven-gate rationale is")
        print("     WRONG and leg 3's S5/S6 must be re-designed before any drive.")

    # ------------------------------------------------------------------ the acceptance predicate
    print("")
    print("=" * 100)
    print("MEASUREMENT 1 — THE ACCEPTANCE PREDICATE'S CONTINUATION PROOF (the load-bearing one)")
    print("=" * 100)
    print("  ⛔ §Ch15, §Ch18 and §Ch19 each PASSED their own acceptance test while STRANDED, so this")
    print("     is the one number the leg is actually graded on.")
    good = plan(ENTRANCE, (6, 16), ENTRANCE, (14, 3))
    trap = plan(ENTRANCE, (6, 16), ENTRANCE, (14, 4))
    record("ENTRANCE (6,16) -> (14,3)  [the PROOF]", "21 wp, is_warp=False", describe(good),
           good is not None and not good[-1].is_warp
           and tuple(good[-1].map) == ENTRANCE.value)
    record("ENTRANCE (6,16) -> (14,4)  [the TRAP]", "21 wp, is_warp=True", describe(trap),
           trap is not None and trap[-1].is_warp)
    if trap is not None and trap[-1].is_warp:
        print(f"      ⇒ CONFIRMED: aiming at (14,4) leaves SKY_PILLAR_ENTRANCE and lands on "
              f"{tuple(trap[-1].coordinates)} of map {tuple(trap[-1].map)} — that is leg 4's")
        print( "        Wallace cutscene. The three conjuncts (bool / same map / not is_warp) are all")
        print( "        load-bearing: dropping `not is_warp` would make the TRAP pass as the PROOF.")
    else:
        print("      ⇒ ‼ THE TRAP DID NOT REPRODUCE. Do not weaken the predicate on that basis —")
        print("        re-measure. A trap that cannot be demonstrated is not a trap that is absent.")

    # ------------------------------------------------------------------ the rest of the constants
    print("")
    print("=" * 100)
    print("MEASUREMENT 2 — the remaining hardcoded constants")
    print("=" * 100)

    # the underwater exit warp, and the (10,8) decoy the spec bans
    uw = MapRSE.UNDERWATER_SOOTOPOLIS_CITY
    uw_path = plan(uw, (9, 6), uw, (9, 8))
    record("UNDERWATER (9,6) -> (9,8) [the exit warp]", "ends UW_ROUTE126 (45,65)",
           describe(uw_path),
           uw_path is not None and uw_path[-1].is_warp)
    for tile in ((9, 8), (10, 8)):
        try:
            data = get_map_data(uw, tile)
            record(f"UNDERWATER {tile} behaviour", "(9,8) arrow / (10,8) plain",
                   f"{data.tile_type}, collision={data.collision}", None)
        except Exception as error:
            record(f"UNDERWATER {tile} behaviour", "-", f"ERROR {type(error).__name__}", False)

    # the swim
    swim = plan(R126, (45, 65), R131, (40, 20))
    record("ROUTE126 (45,65) -> ROUTE131 (40,20) [the swim]", "322 wp", describe(swim),
           swim is not None)
    if swim is not None:
        print(f"      per-map split: {per_map_split(swim)}")
        surf_actions = [(i, tuple(w.map), tuple(w.coordinates), w.action.name)
                        for i, w in enumerate(swim) if w.action is not None]
        print(f"      waypoints carrying an ACTION ({len(surf_actions)}): {surf_actions}")
        r131_tiles = [tuple(w.coordinates) for w in swim if tuple(w.map) == R131.value]
        print(f"      its {len(r131_tiles)} ROUTE131 tiles: {r131_tiles}")

    # the staging leg and the fatal fallback
    record("ROUTE131 (40,19) -> (28,15) [the ROUTE]", "16 wp", describe(must_succeed), True)
    fallback = plan(R131, (40, 20), R131, (28, 15))
    record("ROUTE131 (40,20) -> (28,15) [the FALLBACK]", "35 wp, FATAL", describe(fallback),
           fallback is not None and len(fallback) == 35)
    if fallback is not None:
        crosses = [tuple(w.coordinates) for w in fallback
                   if tuple(w.coordinates) in {(23, 18), (23, 19), (24, 18), (24, 19)}]
        print(f"      ⛔ of its tiles, these are LIVE WALLS on SET B: {crosses}")
        print( "         ⇒ this is why the blind step at (40,19) is MANDATORY, not an optimisation.")

    # the tiles leg 3 will step on or guard
    for label, map_enum, tile in (
        ("the blind step", R131, (40, 19)),
        ("the staging tile", R131, (28, 15)),
        ("the door", R131, (36, 6)),
        ("the dive tile", CITY, (29, 53)),
        ("the PC front", CITY, (43, 32)),
        ("the pocket resting tile", CITY, (31, 17)),
        ("ENTRANCE continue target", ENTRANCE, (14, 3)),
        ("ENTRANCE arrival prediction", ENTRANCE, (6, 16)),
    ):
        try:
            data = get_map_data(map_enum, tile)
            record(f"{label} {map_enum.name} {tile}", "-",
                   f"{data.tile_type}, collision={data.collision}, elevation={data.elevation}", None)
        except Exception as error:
            record(f"{label} {map_enum.name} {tile}", "-", f"ERROR {type(error).__name__}", False)

    # capability + the flag the spec says the atlas has backwards
    print("")
    print("-" * 100)
    print("MEASUREMENT 3 — capabilities and the flag the BUILD SPEC says the atlas has BACKWARDS")
    print("-" * 100)
    party = get_party()
    print(f"  party size {len(party)}; HP: {[(m.species_name_for_stats if hasattr(m, 'species_name_for_stats') else m.species.name, m.current_hp, m.total_hp) for m in party]}")
    for move in ("Surf", "Dive", "Fly"):
        try:
            has = party.has_pokemon_with_move(move, True)
        except Exception as error:
            has = f"ERROR {type(error).__name__}: {error}"
        print(f"  has a {move} user with PP : {has}")
    for flag in ("VISITED_SOOTOPOLIS_CITY", "VISITED_PACIFIDLOG_TOWN", "RECEIVED_BIKE",
                 "BADGE05_GET", "BADGE07_GET", "SYS_WEATHER_CTRL"):
        try:
            print(f"  flag {flag:<26} = {bool(get_event_flag(flag))}")
        except Exception as error:
            print(f"  flag {flag:<26} = ERROR {type(error).__name__}")
    print(f"  ⛔ the §Ch21 ATLAS says VISITED_SOOTOPOLIS_CITY is False; the BUILD SPEC says True.")
    print(f"     The reading above settles it for THIS fixture and the loser must be corrected.")

    # ------------------------------------------------------------------ summary
    print("")
    print("=" * 100)
    print("SUMMARY — only rows the spec gave a number for are graded")
    print("=" * 100)
    graded = [row for row in _results if row[3] is not None]
    bad = [row for row in graded if not row[3]]
    for row in bad:
        print(f"  ‼ MISMATCH  {row[0]}: spec {row[1]!r} vs got {row[2]!r}")
    print(f"  {len(graded) - len(bad)}/{len(graded)} graded constants agree with the BUILD SPEC.")
    print("")
    print("=" * 100)
    print("READ NARROWLY. These are STATIC answers from a loaded save with NOTHING camera-loaded.")
    print("City paths WILL differ live (that is CONTROL 3's whole point), and the runtime ROUTE131")
    print("layout is still unmeasured. Nothing here retires the first drive's readings.")
    print("=" * 100)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
