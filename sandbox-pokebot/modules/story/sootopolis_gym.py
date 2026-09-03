"""§Ch22 — THE SOOTOPOLIS GYM: the ice puzzle, Juan, and the way out.

⛔⛔ THE THREE THINGS THAT MAKE THIS GYM DIFFERENT FROM EVERY OTHER MAP THIS BOT WALKS, all
MEASURED live on 2026-09-02 (`--driver ch22probe`, evidence `2026-09-02-ch22probe-PARTA.txt`):

 1. **`calculate_path` IS CONFIDENTLY WRONG HERE — DO NOT USE IT INSIDE THIS GYM.** It returned a
    16-waypoint route straight up column 8 from the entrance to Juan, THROUGH all six locked-stair
    tiles and 64 un-walked ice tiles, and reported ZERO live walls on it. Three independent reasons:
    `map_path.py:137` gates its `"Slide "` branch on `collision != 0` but the locked stairs are
    collision **0**; `:351` matches `tile_type == "Ice"` exactly so `"Thin Ice"` falls through; and
    the puzzle is **EXACT COVER, not shortest path**.

 2. **`_live_collision_grid` IS A FALSE NEGATIVE BY CONSTRUCTION HERE, AND FAILS SILENTLY.** The
    gym's `setmetatile`s all pass `FALSE`, so `MAPGRID_IMPASSABLE` is never set and the collision
    bits NEVER CHANGE as the ice cracks. MEASURED: one ice step moved the METATILE grid by one tile
    ((8,19) `0x20d` -> `0x20e`) and the COLLISION grid by **zero**. ⇒ `probe_live_mapgrid.py` and
    `_live_wall_tiles` will report 0 differences and PASS over a catastrophically wrong model.
    **The oracle here is `_live_metatile_grid` and/or `ICE_STEP_COUNT`.** (KI-73.)

 3. **EVERY TILE EXACTLY ONCE.** 64 thin-ice tiles in three sections (7 / 19 / 38) against
    `ICE_STEP_COUNT` thresholds 8 / 28 / 67; the arithmetic closes exactly, so a single revisit is a
    FALL. A fall drops you to B1F and costs the walk plus up to ten trainer battles.
    ✅ The puzzle RESETS on every entry (`ClearTempFieldEventData` + `OnTransition`), MEASURED by
    re-entering — so a failed attempt costs only the walk, and a static route table is SAFE.
"""

from typing import Generator

from modules.context import context
from modules.map_data import MapRSE
from modules.story.seafloor_cavern import _at, _on_map, _var, _where
from modules.story.sootopolis import _live_metatile_grid

GYM_1F = MapRSE.SOOTOPOLIS_CITY_GYM_1F

#: MEASURED live: the tile the city->gym warp lands on.
GYM_ENTRANCE = (8, 25)
#: MEASURED live: the last normal floor tile before the first ice band, in the stair column.
GYM_APPROACH = (8, 20)
#: Every stair pair sits in this column, so every inter-section climb is a straight walk up it.
STAIR_COLUMN = 8
#: Juan's tile is (8,2); (8,3) is the tile in FRONT of him — the walk's destination.
JUAN_STAND = (8, 3)

#: Metatile ids, MEASURED live and cross-checked against the decomp tileset attributes.
THIN_ICE = (0x20D, 0x215)   # steppable exactly once
CRACKED_ICE = 0x20E         # stepped once — a second step BREAKS it
BROKEN_ICE = 0x206          # a hole; stepping here is a fall
LOCKED_STAIRS = 0x20F       # MB_SLIDE_SOUTH — shoves the player back onto the ice below
OPEN_STAIRS = 0x207

#: ⛔⛔ GENERATED, NOT HAND-WRITTEN — by `tools/story-dev/solve_gym_ice.py` from the DECOMP layout
#: (`data/layouts/SootopolisCity_Gym_1F/map.bin` + the gym tileset's metatile attributes), which
#: re-derives it on every run so this table can never silently drift from the map.
#: ✅ ITS TILE SET IS LIVE-VERIFIED: decomp vs the live `gBackupMapLayout` = 64/64, zero differences
#: in BOTH directions (evidence `2026-09-02-ch22-ICEROUTE-generated.txt` + `…-LIVECOORDS.txt`).
#: ⛔ BOTH ENDPOINTS OF EACH SECTION ARE FORCED, and constraining only the START was a REAL DEFECT in
#: the generator's first cut: it produced a valid Hamiltonian path for section 1 ending at (9,18),
#: from which the (8,16)/(8,15) stairs are unreachable without re-crossing CRACKED ice — a fall on
#: the very first transition. **A route that covers every tile is not a route you can LEAVE.**
ICE_ROUTE: tuple[tuple[tuple[int, int], ...], ...] = (
    # section 1 — 7 tiles, (8,19) -> (8,17)
    (
        (8, 19), (7, 19), (7, 18), (8, 18), (9, 18), (9, 17), (8, 17)
    ),
    # section 2 — 19 tiles, (8,14) -> (8,12)
    (
        (8, 14), (7, 14), (6, 14), (5, 14), (5, 13), (5, 12), (6, 12), (7, 12), (7, 13), (8, 13),
        (9, 13), (9, 14), (10, 14), (11, 14), (11, 13), (11, 12), (10, 12), (9, 12), (8, 12)
    ),
    # section 3 — 38 tiles, (8,9) -> (8,6)
    (
        (8, 9), (7, 9), (6, 9), (6, 8), (5, 8), (5, 9), (4, 9), (3, 9), (3, 8), (3, 7), (3, 6),
        (4, 6), (4, 7), (5, 7), (6, 7), (6, 6), (7, 6), (7, 7), (8, 7), (8, 8), (9, 8), (9, 9),
        (10, 9), (10, 8), (10, 7), (11, 7), (11, 8), (12, 8), (12, 9), (13, 9), (13, 8), (13, 7),
        (13, 6), (12, 6), (11, 6), (10, 6), (9, 6), (8, 6)
    ),
)

#: ⛔ MEASURED, NOT DERIVED — and the first cut of this constant was WRONG. `OnTransition` seeds
#: `ICE_STEP_COUNT` at 1 and each ice step adds 1, so the decomp's unlock THRESHOLDS are 8 / 28 / 67.
#: But the unlock script itself does `addvar VAR_ICE_STEP_COUNT, 1` **in the same beat as the step
#: that crosses the threshold** — MEASURED live 2026-09-02: the 7th step of section 1 took the var
#: 7 -> **9**, not 7 -> 8. ⇒ the value AFTER a completed section is the threshold PLUS ONE.
#: ✅ ALL THREE MEASURED by the first successful walk (2026-09-02, `--driver ch22ice`, 64/64 steps):
#: **9 / 29 / 68** — each exactly the decomp threshold PLUS ONE, confirming the unlock's `addvar`
#: lands in the same beat as the crossing step, consistently, in all three sections.
#: ⛔ The PREDICTION was 8 / 28 / 67 (the raw thresholds) and it was WRONG in a now-understood way.
SECTION_END_COUNT: tuple[int | None, ...] = (9, 29, 68)

#: The value the var reads once the whole puzzle is walked — the grade for `walk_the_ice`.
ICE_COMPLETE_COUNT = 68

#: The decomp's unlock thresholds, for reference — NOT what the var reads after the section.
SECTION_UNLOCK_THRESHOLD = (8, 28, 67)


def ice_route_tiles() -> set[tuple[int, int]]:
    """Every tile the route steps on — the set that must equal the live thin-ice set."""
    return {tile for section in ICE_ROUTE for tile in section}


def assert_route_matches_live_floor() -> None:
    """⛔ THE PRE-WALK GATE: the embedded table must match the floor the game is actually running.

    ‼ WHY THIS RUNS BEFORE EVERY WALK AND NOT ONCE AT BUILD TIME. The table was verified against the
    live grid on 2026-09-02, but a table is a CACHE of a measurement and this project's rule is that
    a repeated number is a decaying number. Re-deriving the comparison costs one grid read.

    ⛔ SET COMPARISON, BOTH DIRECTIONS — never a count. A matching COUNT is not a matching SET: a
    positive control proves a scan is not blind, and says nothing about it over-reporting
    (`08-MISTAKES.md` 2026-08-27).
    """
    from modules.modes import BotModeError

    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: the route check needs GYM_1F; standing at {_where()}.")
    grid = _live_metatile_grid(GYM_1F)
    live = {tile for tile, mt in grid.items() if mt in THIN_ICE}
    planned = ice_route_tiles()
    if live != planned:
        raise BotModeError(
            f"Ch22: the embedded ICE_ROUTE does not match the live floor. "
            f"live-only={sorted(live - planned)[:8]} planned-only={sorted(planned - live)[:8]} "
            f"(live={len(live)} planned={len(planned)}). ⛔ REFUSING TO WALK — regenerate the table "
            "with `tools/story-dev/solve_gym_ice.py` rather than editing it by hand."
        )


def walk_the_ice(report: dict | None = None) -> Generator:
    """Walk the 64-step exact-cover route from the gym entrance to Juan's tile.

    ⛔ EVERY STEP IS CHECKED **BEFORE** IT IS TAKEN, against `_live_metatile_grid` — the target must
    be THIN ice, never cracked and never broken. That check is the whole safety story: the planner
    cannot help here (trap 1), the collision oracle cannot see the floor (trap 2), and a single
    revisit is a fall (trap 3).

    ⛔ AND `ICE_STEP_COUNT` MUST ADVANCE ON EVERY STEP — by +1 normally, or +2 on the step that
    CROSSES an unlock threshold (the unlock's own `addvar` lands in the same beat; MEASURED). The
    FLOOR (`after > before`) is the part that matters and must never be relaxed: position alone is
    not enough, because the var is what the game's unlock thresholds are counted against, so an
    avatar that moves without the counter advancing means the model is wrong.
    """
    from modules.modes import BotModeError
    from modules.modes.util.walking import navigate_to
    from modules.story.early_game import _check_abort, wait_until_truly_controllable
    from modules.story.sootopolis import _bounded_step

    if report is None:
        report = {}
    report.setdefault("sections", [])
    report.setdefault("steps", 0)

    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: walk_the_ice needs GYM_1F; standing at {_where()}.")
    yield from wait_until_truly_controllable()
    assert_route_matches_live_floor()

    # ⛔ The approach tile is normal floor, so `navigate_to` is SAFE here and ONLY here — it is the
    # one leg of this gym that contains no ice.
    if not _at(GYM_1F, GYM_APPROACH):
        yield from navigate_to(GYM_1F, GYM_APPROACH)
    if not _at(GYM_1F, GYM_APPROACH):
        raise BotModeError(f"Ch22: could not reach the ice approach {GYM_APPROACH} — at {_where()}.")

    for index, section in enumerate(ICE_ROUTE):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        # ⛔ THE STAIRS BETWEEN SECTIONS ARE NOT IN THE ROUTE TABLE — the table is ICE ONLY, and the
        # first walk failed here with "(8,17) -> (8,14) is not a single orthogonal step". The two
        # tiles between sections are the stair pair that the previous section's completion UNLOCKS.
        # ⛔⛔ AND THEY MUST BE VERIFIED OPEN BEFORE STEPPING: a LOCKED stair is `MB_SLIDE_SOUTH`,
        # which shoves the player back onto the ice they just cracked — i.e. a FALL. This is the
        # single most dangerous step in the gym, and it is the one the route table cannot cover.
        # ⛔ CLIMB TO THE TILE *BELOW* THE SECTION START, NEVER ONTO IT. The first cut targeted
        # `section[0]` itself and so CONSUMED the first ice tile outside the route loop: the walk
        # then refused its own step 1 with "(8,19) reads 0x20E, not thin ice" — the bot had cracked
        # the tile it was about to step on. The route loop owns every ICE step; the climb owns only
        # the stairs. (Caught by the pre-step guard on the second walk, not by review.)
        staging = (section[0][0], section[0][1] + 1)
        if not _at(GYM_1F, staging):
            yield from _climb_to(staging)
        for tile in section:
            _check_abort()
            grid = _live_metatile_grid(GYM_1F)
            here = tuple(_here())
            state = grid.get(tuple(tile))
            if state not in THIN_ICE:
                raise BotModeError(
                    f"Ch22: REFUSING to step onto {tile} — it reads metatile "
                    f"{'0x%03X' % state if state is not None else None}, not thin ice "
                    f"{[hex(v) for v in THIN_ICE]}. cracked=0x{CRACKED_ICE:03X} "
                    f"broken=0x{BROKEN_ICE:03X}. At {here}, section {index + 1}, "
                    f"step {report['steps'] + 1} of 64. A second step on a cracked tile is a FALL."
                )
            direction = _direction_between(here, tile)
            before = _var("ICE_STEP_COUNT")
            yield from _bounded_step(direction, expect=tuple(tile), map_enum=GYM_1F)
            after = _var("ICE_STEP_COUNT")
            report["steps"] += 1
            # ⛔ THE HAZARD THIS GUARDS IS "THE AVATAR MOVED AND THE GAME DID NOT SCORE IT" — so the
            # floor is `after > before`, and that is the part that must never be relaxed.
            # ‼ The CEILING is 2, not 1, and the first cut of this check got it wrong: on the step
            # that CROSSES an unlock threshold the game adds 1 for the step AND 1 for the unlock in
            # the same beat. MEASURED: section 1's 7th step took the var 7 -> 9. The guard caught my
            # wrong model on the first walk, which is exactly what it was for — so the model was
            # corrected from the measurement rather than the guard being loosened away.
            if not isinstance(after, int) or not isinstance(before, int) or not (
                before + 1 <= after <= before + 2
            ):
                raise BotModeError(
                    f"Ch22: stepped onto {tile} but ICE_STEP_COUNT went {before!r} -> {after!r} "
                    "(expected +1, or +2 on the step that crosses an unlock threshold). The "
                    "position moved and the game's own counter did not agree — the model is wrong, "
                    "and continuing would walk a route the game is not scoring."
                )
        # ⛔ The unlock script runs `addvar` then `delay 40`, so give it a bounded moment to settle
        # before reading — then RECORD what it actually is.
        yield from _settle_var("ICE_STEP_COUNT")
        count = _var("ICE_STEP_COUNT")
        report["sections"].append((index + 1, len(section), tuple(_here()), count))
        expected = SECTION_END_COUNT[index] if index < len(SECTION_END_COUNT) else None
        if expected is None:
            # ⛔ NOT YET MEASURED: record it loudly rather than asserting a number nobody has seen.
            from modules.console import console

            console.print(f"[yellow]Ch22: section {index + 1} ended with ICE_STEP_COUNT={count} — "
                          f"UNMEASURED until now; record it in SECTION_END_COUNT.[/]")
        elif count != expected:
            raise BotModeError(
                f"Ch22: section {index + 1} finished at {_here()} with ICE_STEP_COUNT={count!r}, "
                f"expected {expected}. The section's tiles were all walked, so either the unlock "
                "did not fire or the model of the counter is wrong."
            )
        yield from wait_until_truly_controllable()

    report["end_tile"] = tuple(_here())
    report["end_count"] = _var("ICE_STEP_COUNT")
    return report


def _here() -> tuple[int, int]:
    from modules.player import get_player_avatar

    return tuple(get_player_avatar().local_coordinates)


def _direction_between(a, b) -> str:
    from modules.modes import BotModeError

    dx, dy = b[0] - a[0], b[1] - a[1]
    if (abs(dx) + abs(dy)) != 1:
        raise BotModeError(
            f"Ch22: {a} -> {b} is not a single orthogonal step. The route table is only valid as a "
            "contiguous walk; a gap means the bot is not where the table thinks it is."
        )
    return {(0, -1): "Up", (0, 1): "Down", (-1, 0): "Left", (1, 0): "Right"}[(dx, dy)]


def _climb_to(target: tuple[int, int], *, max_steps: int = 6) -> Generator:
    """Walk straight up the stair column to `target` — the STAGING tile below a section, never onto
    the ice itself.

    ⛔ The caller passes the tile one SOUTH of the section start. Targeting the section start itself
    was a real defect: the climb consumed the first ice tile, and the route loop then refused to
    step onto its own already-cracked step 1.

    ⛔ Between ice sections the player must cross a pair of stair tiles that the previous section's
    completion unlocks. `navigate_to` is NOT used — the planner is provably wrong inside this gym
    (it reads locked stairs as ordinary floor, because they are collision 0). Each step is checked
    against the LIVE metatile grid first: a `0x20F` locked stair is `MB_SLIDE_SOUTH` and would shove
    the bot back onto the ice it just cracked, which is a fall.
    """
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort
    from modules.story.sootopolis import _bounded_step

    for _ in range(max_steps):
        _check_abort()
        here = tuple(_here())
        if here == tuple(target):
            return
        if here[0] != target[0]:
            raise BotModeError(
                f"Ch22: the inter-section climb expects a single column; at {here}, target "
                f"{target}. The stair pairs all sit in column {STAIR_COLUMN}."
            )
        nxt = (here[0], here[1] - 1)
        state = _live_metatile_grid(GYM_1F).get(nxt)
        if state == LOCKED_STAIRS:
            raise BotModeError(
                f"Ch22: REFUSING to step onto {nxt} — it is still a LOCKED stair "
                f"(0x{LOCKED_STAIRS:03X}, MB_SLIDE_SOUTH). It would shove the bot back onto the ice "
                "it just cracked, which is a FALL. The previous section did not unlock it."
            )
        if state in (CRACKED_ICE, BROKEN_ICE):
            raise BotModeError(
                f"Ch22: REFUSING to step onto {nxt} — it reads 0x{state:03X} "
                f"(cracked/broken ice). The climb is off-route."
            )
        yield from _bounded_step("Up", expect=nxt, map_enum=GYM_1F)
    raise BotModeError(
        f"Ch22: could not climb to {target} within {max_steps} steps — at {_here()}."
    )


def _settle_var(name: str, *, stable_frames: int = 45, budget_frames: int = 600) -> Generator:
    """Let a var stop changing, then return — bounded, and it never asserts a VALUE.

    ⛔ WAITING FOR A SPECIFIC VALUE WAS THE FIRST CUT AND IT WAS THE WRONG SHAPE: it hardcoded a
    number the unlock script had not been measured to produce, so a correct walk would have hung
    until its budget. Waiting for STABILITY lets the caller RECORD what the game actually did.
    The unlock runs `addvar` then `delay 40`, so `stable_frames` is a little over that.
    """
    from modules.story.early_game import _check_abort

    last = _var(name)
    steady = 0
    frames = 0
    while frames < budget_frames and steady < stable_frames:
        _check_abort()
        now = _var(name)
        steady = steady + 1 if now == last else 0
        last = now
        yield
        frames += 1
