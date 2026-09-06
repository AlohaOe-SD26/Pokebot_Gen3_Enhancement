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
    """Walk the 64-step exact-cover route from the gym entrance to (8,6), the last ice tile

    ⛔ NOT to Juan's tile: (8,6) is THREE TILES SOUTH of JUAN_STAND (8,3), and the stair climb
    that closes the gap is not in this function. (Corrected 2026-09-03.).

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

    # ⛔ `navigate_to` is SAFE here and ONLY here. ‼ AND THE REASON IS NOT THE ONE THIS COMMENT
    # USED TO GIVE ("the approach tile is normal floor, the one leg with no ice") — that argument
    # only holds when the bot is already SOUTH of the ice, which nothing here asserts. What
    # actually protects it is `assert_route_matches_live_floor()` on the line above: on any
    # partially-walked floor the cracked tiles no longer read THIN_ICE and it refuses BEFORE this
    # navigate runs. (Adversarial review, 2026-09-03: right code, wrong reason — and a wrong
    # reason is what a later edit deletes.)
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
        # ⛔⛔ THIS HELPER ONLY EVER WALKS NORTH — `nxt` is unconditionally `y - 1`. A target SOUTH
        # of the bot is therefore UNREACHABLE, and without this refusal the loop presses "Up" away
        # from it for `max_steps * 900` frames and then blames the step budget.
        # ‼ THIS IS NOT HYPOTHETICAL: the chapter's own order (…→ Juan → fall) asks exactly this.
        # `fight_juan` leaves the bot on JUAN_STAND (8,3); `fall_to_b1f` calls
        # `_climb_to(FALL_STAGING=(8,5))`, which is TWO TILES SOUTH — so the first `nxt` is (8,2),
        # **Juan's own tile**, which is plain floor and passes both guards below. Found by an
        # adversarial review 2026-09-03, before the composed arm was ever run.
        # ⇒ a DESCENT helper is still owed (`#24-ch22chapter`); this only makes the gap LOUD.
        if target[1] > here[1]:
            raise BotModeError(
                f"Ch22: `_climb_to` walks NORTH only, and {target} is SOUTH of {here} "
                f"(y increases southward). Refusing rather than pressing 'Up' away from the "
                f"target. A southward move here needs a descent helper, which does not exist yet."
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


# ============================== THE EXIT — B1F, AND WHY IT IS FORCED ==============================
# ⛔⛔ THE BOT CANNOT WALK OUT OF THIS GYM. After the ice walk it stands on a 20-TILE ISLAND
# (measured live AND re-derived offline, exact agreement), from which the exit warp and the 1F
# ladder are BOTH unreachable. The only way out is to step back onto a CRACKED tile, break it, and
# `warphole` down to B1F at the same (x,y) — the §Ch21-leg-4 shape, which no pathfinder can propose.
# ‼ AND THE PLANNER DISAGREES AND IS WRONG: from Juan's tile it reports the exit 23 wp and the
# ladder 22 wp away. Both are unreachable. ⛔ NEVER use `calculate_path` inside this gym — on EITHER
# floor. B1F's LAYOUT is static, but trainer BODIES block tiles and appear nowhere in `map.bin`, and
# sight lines are invisible to a collision planner.

#: The ONLY cracked tile orthogonally adjacent to the island — therefore the only possible fall.
FALL_TILE = (8, 6)
#: The open-stair tile directly NORTH of the fall tile. ⛔ y INCREASES SOUTHWARD, so (8,5) is ABOVE
#: (8,6): the bot stages here and steps **DOWN** to re-break the ice. The first cut said "directly
#: south … steps NORTH" and pressed Up — which walked AWAY from the fall tile, up to (8,3), and the
#: bounded map-change guard caught it in 900 frames with the position in the message.
FALL_STAGING = (8, 5)
#: B1F's only warp, back up to 1F.
B1F_LADDER = (11, 22)

#: ⛔ B1F HAS SLIDE TILES AND A PLAIN 4-CONNECTED MODEL IS WRONG ON IT. Stepping onto one carries the
#: player SOUTH until a non-slide tile — which is free movement PAST sight lines, so ignoring them is
#: wrong in the PESSIMISTIC direction (my first route model did exactly that and over-counted the
#: forced battles). Chains: (8,10)->(8,12), (8,15)->(8,17), (8,20)->(8,22).
B1F_SLIDE_TILES = ((8, 10), (8, 11), (8, 15), (8, 16), (8, 20), (8, 21))

#: ⛔⛔ THE MINIMUM-BATTLE ROUTE, and the objective is named on purpose: this MINIMISES BATTLES, not
#: distance. The shortest walk is the same 19 tiles but crosses FIVE sight lines; this one crosses
#: THREE (Andrea, Bethany, Connie). ‼ I first reported five because I asked a BINARY question ("is
#: there a trainer-free route?"), got "no", and fell back on the shortest path — see `08-MISTAKES.md`
#: 2026-09-03. ⇒ **when the ideal is unavailable, MINIMISE.**
#: Derived by a battle-weighted Dijkstra with slides modelled, and independently corroborated: an
#: adversarial agent found a DIFFERENT 3-battle route (35 tiles), agreeing on the COUNT while
#: disagreeing on the PATH — which is the stronger form of corroboration.
#: Entries are the tiles the bot must END UP on, in order; a slide entry lands past its neighbour.
B1F_ROUTE: tuple[tuple[int, int], ...] = (
    (8, 7), (8, 8), (8, 9), (8, 12), (7, 12), (6, 12), (5, 12), (5, 13), (5, 14),
    (6, 14), (7, 14), (8, 14), (8, 17), (8, 18), (8, 19), (8, 22), (9, 22), (10, 22), (11, 22),
)

#: The three trainers whose sight lines this route deliberately accepts. ⛔ Fighting them is PART OF
#: THE ROUTE, not a fault (the §Ch20 precedent).
#: ⛔⛔ THIS COMMENT USED TO ADD "and the chapter NEEDS the XP, because the party is measured not to
#: beat Juan" — **REFUTED 2026-09-03: the party beats Juan 4 times out of 4** (one control plus
#: three independent RNG draws via `POKEBOT_CH22JUAN_JITTER`). The XP is NOT the reason to fight
#: them. ‼ An adversarial review found this line still arguing XP-before-Juan while `:503` below
#: retracted its premise — a stale half of a P2 pair living INSIDE THE CODE, and load-bearing,
#: because it dictates the chapter's leg order.
#: ⛔⛔ AND THE THREE BATTLES DO NOT HAPPEN IN THE REAL CHAPTER AT ALL. **THE JUAN VICTORY SCRIPT
#: FLAGS ALL TEN B1F TRAINERS AS ALREADY DEFEATED** — `SootopolisCity_Gym_1F_EventScript_JuanDefeated`
#: runs `setvar VAR_0x8008, 8` + `call Common_EventScript_SetGymTrainers`, and
#: `SootopolisCity_Gym_SetGymTrainers` (`data/scripts/set_gym_trainers.inc`) `settrainerflag`s
#: ANDREA, CRISSY, BRIANNA, CONNIE, BRIDGET, OLIVIA, TIFFANY, BETHANY, ANNIKA and DAPHNE.
#: ✅ Read and quoted from the decomp myself, 2026-09-03.
#: ⇒ **the post-badge descent is BATTLE-FREE, the chapter needs only ONE descent, and there is no
#: XP run.** ‼ `--driver ch22exit` measured 3 battles and 629/694 → 332/694 with `badge8=False` —
#: a state the assembled chapter NEVER SEES. Those numbers are real and NOT transferable; the
#: driver is still the right instrument for the fall + route, just not for the HP cost.
B1F_FORCED_TRAINERS = ("Andrea", "Bethany", "Connie")


def fall_to_b1f(report: dict | None = None) -> Generator:
    """Break the one reachable cracked tile and drop to B1F. ⛔ This is DELIBERATE, not a failure."""
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort, wait_until_truly_controllable

    if report is None:
        report = {}
    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: the fall needs GYM_1F; standing at {_where()}.")

    grid = _live_metatile_grid(GYM_1F)
    state = grid.get(FALL_TILE)
    if state not in (CRACKED_ICE, BROKEN_ICE):
        # ⛔ FORMAT THE STATE DEFENSIVELY: `grid.get` returns None for an off-grid tile, and
        # `f"0x{None:03X}"` raises a raw TypeError — which is NOT a BotModeError, so it would
        # escape the chapter's retry loop and kill the whole story run. `walk_the_ice` already
        # formats it this way; this call site did not. (Found by an adversarial review, 2026-09-03.)
        shown = f"0x{state:03X}" if state is not None else "None (off-grid)"
        raise BotModeError(
            f"Ch22: refusing to fall — {FALL_TILE} reads {shown}, not cracked/broken. The ice "
            "walk must have completed first; falling through virgin ice is not what this leg does."
        )
    # after the ice walk the bot rests ON the fall tile (8,6); (8,5) is one step NORTH of it, and
    # `_climb_to` only ever walks north, which is exactly right here.
    if not _at(GYM_1F, FALL_STAGING):
        yield from _climb_to(FALL_STAGING)
    _check_abort()

    from modules.player import get_player_avatar
    from modules.modes.util.walking import ensure_facing_direction

    # ⛔ DOWN, not Up: the fall tile is SOUTH of the staging tile (y increases southward).
    yield from ensure_facing_direction("Down")
    # ⛔ THE WITNESS IS THE MAP CHANGE, never a coordinate — `warphole` preserves (x,y), so a
    # coordinate assert would pass even if nothing happened (the §Ch21 `_fall_through_crack` rule).
    frames = 0
    while frames < 900:
        _check_abort()
        if _on_map(MapRSE.SOOTOPOLIS_CITY_GYM_B1F):
            break
        context.emulator.press_button("Down")
        yield
        frames += 1
    else:
        raise BotModeError(
            f"Ch22: pressed Down at {FALL_STAGING} for 900 frames and the map never changed — at "
            f"{_where()}. The fall is the only exit, so this is a stranded run, not a slow one."
        )
    yield from wait_until_truly_controllable()
    report["fall_frames"] = frames
    report["b1f_arrival"] = tuple(_here())
    return report


def walk_b1f_to_ladder(report: dict | None = None) -> Generator:
    """Walk the minimum-battle route to the ladder, fighting the three trainers it accepts."""
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort, wait_until_truly_controllable
    from modules.story.sootopolis import _bounded_step

    B1F = MapRSE.SOOTOPOLIS_CITY_GYM_B1F
    if report is None:
        report = {}
    report.setdefault("b1f_steps", 0)
    if not _on_map(B1F):
        raise BotModeError(f"Ch22: the B1F walk needs B1F; standing at {_where()}.")

    for index, target in enumerate(B1F_ROUTE):
        _check_abort()
        # ⛔⛔ THE LADDER WARPS ON CONTACT, SO ITS STEP CANNOT USE `_bounded_step` — that helper's
        # success predicate is `_at(map_enum, expect)` on the SAME map, and the ladder CHANGES the
        # map mid-step. This is the §Ch21-leg-4 lesson exactly ("`_bounded_step` cannot express a
        # fall"), and it recurred here: the first drive walked the whole route, took the ladder
        # SUCCESSFULLY, and then reported a failure because the helper could not see it.
        # ⇒ the witness for a warp step is the MAP CHANGE, never a coordinate.
        if index == len(B1F_ROUTE) - 1:
            here = tuple(_here())
            dx, dy = target[0] - here[0], target[1] - here[1]
            direction = ("Down" if dy > 0 else "Up") if dy else ("Right" if dx > 0 else "Left")
            frames = 0
            while frames < 900 and _on_map(B1F):
                _check_abort()
                context.emulator.press_button(direction)
                yield
                frames += 1
            if _on_map(B1F):
                raise BotModeError(
                    f"Ch22: pressed {direction} toward the ladder {B1F_LADDER} for 900 frames and "
                    f"the map never changed — at {_where()}."
                )
            yield from wait_until_truly_controllable()
            report["b1f_steps"] += 1
            report["ladder_landing"] = tuple(_here())
            return report
        # a trainer battle can fire mid-walk; let it finish before judging position
        yield from wait_until_truly_controllable()
        here = tuple(_here())
        if here == tuple(target):
            continue
        dx, dy = target[0] - here[0], target[1] - here[1]
        if dx and dy:
            raise BotModeError(
                f"Ch22: B1F route step {here} -> {target} is diagonal. The route is only valid as a "
                "contiguous walk; a diagonal gap means the bot is not where the route thinks it is "
                "(a trainer battle may have displaced it)."
            )
        direction = ("Down" if dy > 0 else "Up") if dy else ("Right" if dx > 0 else "Left")
        if abs(dx) + abs(dy) == 1:
            yield from _bounded_step(direction, expect=tuple(target), map_enum=B1F)
        else:
            # ⛔ A SLIDE: press once toward the slide tile and let the game carry us. The witness is
            # ARRIVAL AT THE SLIDE DESTINATION, not the number of tiles moved.
            frames = 0
            while frames < 600 and tuple(_here()) != tuple(target):
                _check_abort()
                context.emulator.press_button(direction)
                yield
                frames += 1
            if tuple(_here()) != tuple(target):
                raise BotModeError(
                    f"Ch22: slide from {here} did not land on {target} within 600 frames — at "
                    f"{_where()}. B1F's slide chains are {B1F_SLIDE_TILES}."
                )
        report["b1f_steps"] += 1

    raise BotModeError(
        f"Ch22: the B1F route ran to its end without taking the ladder — at {_where()}. The last "
        "route entry must be the ladder, and it returns via the map-change witness."
    )


# ================================ JUAN — THE 8TH GYM LEADER ======================================
# ✅✅ MEASURED 2026-09-03: THE PARTY **WON**, FIRST TRY — BADGE08_GET set, city_state 6,
# BattleOutcome.Won, 5/6 survivors, 32,891 frames.
# ⛔ THIS COMMENT READ "THE PARTY IS MEASURED NOT TO WIN THIS YET" AND THAT WAS FALSE: it was
# never measured, it was CALCULATED. Every typing fact below is still correct; the conclusion
# drawn from it was not. ⚠ One win is not a reliability measurement (§Ch20's Archie was 2W/1L).
# Juan (`src/data/trainers.h`, `trainer_parties.h`): Luvdisc 41, Whiscash 41, Sealeo 43,
# Crawdaunt 43, **Kingdra 46 @ Chesto Berry** (Water Pulse / Double Team / Ice Beam / **Rest**),
# all IVs 30, plus **2x Hyper Potion** on the trainer.
#
# KINGDRA IS WATER/DRAGON, AND THAT NEUTRALISES THE WHOLE PARTY:
#   Grass 2.0 x 0.5 = 1.0 · Electric 1.0 · Ice 0.5 x 2.0 = 1.0.
# Only DRAGON is 2x, and no party member has a Dragon move (TM02 is in Meteor Falls, out of scope).
# ‼ The `12-STORYMODE-DESIGN` line "counters: Grass/Electric" is right about Juan's TEAM and WRONG
# about his ACE.
#
# ⚠ AND BUYING ITEMS DOES NOT FIX IT — the Sootopolis Mart sells Hyper/Max Potion, Full Heal and
# Revive, and money is 67,466, so healing is affordable; but the arithmetic says the problem is the
# DAMAGE RACE, not the item count (Sceptile 3HKOs a 138-HP Kingdra while being 2HKO'd by Ice Beam,
# against ~4 full bars of healing). ⛔ THAT IS A CALCULATION, NOT A MEASUREMENT — this leg exists so
# a DRIVE decides it. Never let a damage calc stand in for a discriminator.
#
# ⇒ THE FIRST DRIVE WAS EXPECTED TO LOSE AND DID NOT. A loss would have been a RESULT sizing the
# gap, not a defect,
# and the leg reports HOW FAR it got rather than merely that it failed.

JUAN_TILE = (8, 2)          # Juan himself; the bot stands one south of him
BADGE8_FLAG = "BADGE08_GET"


def juan_defeated() -> bool:
    from modules.memory import get_event_flag

    return get_event_flag(BADGE8_FLAG)


def fight_juan(report: dict | None = None, *, budget_frames: int = 40000) -> Generator:
    """Talk to Juan and ride the battle out. Reports HOW FAR the run got, win or lose.

    ⛔ THE GRADE IS THE BADGE, NOT "THE BATTLE HAPPENED" — and the leg reports the opponent's
    remaining party so a LOSS is a measurement (how many of his five we took down) rather than a
    bare failure. §Ch20's Archie precedent: a loss is a VALID BRANCH the chapter must handle.
    """
    from modules.modes import BotModeError
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story.early_game import _check_abort, wait_until_truly_controllable
    from modules.tasks import get_global_script_context, is_waiting_for_input

    if report is None:
        report = {}
    if juan_defeated():
        report["already"] = True
        return report
    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: the Juan fight needs GYM_1F; standing at {_where()}.")
    if not _at(GYM_1F, JUAN_STAND):
        raise BotModeError(
            f"Ch22: the Juan fight must start from {JUAN_STAND} (one tile SOUTH of him); standing "
            f"at {_where()}. ⛔ THE ICE WALK DOES **NOT** PUT THE BOT THERE — it ends on (8,6), "
            f"three tiles south, and the 3-step stair climb that closes the gap currently lives "
            f"ONLY in the harness driver (`Ch22JuanMode`). A chapter must own that climb."
        )

    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction("Up")
    context.emulator.press_button("A")
    yield

    frames = 0
    while frames < budget_frames:
        _check_abort()  # ⛔ FIRST statement, outside any try
        if juan_defeated() and not get_global_script_context().is_active:
            report["won"] = True
            break
        # ⛔ GATED, NOT MASHED, and on a DUTY CYCLE — a held button gives Gen 3's `waitbuttonpress`
        # no JOY_NEW edge, which is what parked a msgbox for 20,000 frames in §Ch21 leg 5.
        if frames % 4 == 0:
            context.emulator.press_button("A" if is_waiting_for_input() else "B")
        yield
        frames += 1
    else:
        report["won"] = bool(juan_defeated())
        report["timeout"] = True

    report["frames"] = frames
    report["badge"] = juan_defeated()
    report["city_state"] = _var("SOOTOPOLIS_CITY_STATE")
    report["end_tile"] = tuple(_here())
    return report


# ================================ THE CHAPTER ====================================================
# ⛔⛔ FOUR MOVEMENT LEGS LIVED ONLY IN HARNESS DRIVERS UNTIL 2026-09-03, AND ONE OF THEM DID NOT
# EXIST AT ALL. An adversarial review found the gap before any composed run: the chapter's own
# order (… -> fight_juan -> fall_to_b1f) needs a SOUTHWARD walk from JUAN_STAND (8,3) to
# FALL_STAGING (8,5), and `_climb_to` walks NORTH ONLY — its first step would have been (8,2),
# **Juan's own tile**, which is plain floor (MEASURED `0x22b`), so neither of its guards fires.
# ⇒ `_descend_to` below, plus `climb_to_juan`, `enter_gym` and `leave_gym_to_city`.
#
# ✅ THE DESCENT IS SAFE, AND THAT IS MEASURED, NOT ASSUMED (`--driver ch22stairs`, 2026-09-03,
# evidence `2026-09-03-ch22stairs-COLUMN-AB.txt`). Column x=8 BEFORE the ice walk vs AFTER it:
#     (8,4) 0x20f -> 0x207     (8,5) 0x20f -> 0x207     (8,6) 0x20d -> 0x20e
# ⇒ both stair tiles really do become OPEN_STAIRS (`MB_NORMAL`), so a plain southward step is a
# WALK and not a slide. ‼ THE ALTERNATIVE WAS NOT HYPOTHETICAL: had they stayed `MB_SLIDE_SOUTH`,
# stepping south would have shoved the bot onto cracked ice and fallen it from the WRONG tile,
# mid-chapter. This project measures the direction of a coordinate move BEFORE writing it.


def _descend_to(target: tuple[int, int], *, max_steps: int = 6) -> Generator:
    """Walk straight DOWN the stair column to `target`. The mirror of `_climb_to`, and its twin.

    ⛔ `y` INCREASES SOUTHWARD, so "descend" means `y + 1`. That is the exact confusion that made
    the §Ch22 exit leg press "Up" away from its fall tile on its first drive.
    ⛔ It refuses to step onto CRACKED or BROKEN ice: that is a FALL, and the fall is its own leg
    with its own guard. The caller stops one tile SHORT of the fall tile.
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
                f"Ch22: the descent expects a single column; at {here}, target {target}. The "
                f"stair pairs all sit in column {STAIR_COLUMN}."
            )
        if target[1] < here[1]:
            raise BotModeError(
                f"Ch22: `_descend_to` walks SOUTH only, and {target} is NORTH of {here} "
                f"(y increases southward). Use `_climb_to` for that."
            )
        nxt = (here[0], here[1] + 1)
        state = _live_metatile_grid(GYM_1F).get(nxt)
        if state == LOCKED_STAIRS:
            raise BotModeError(
                f"Ch22: REFUSING to step onto {nxt} — it still reads LOCKED_STAIRS "
                f"(0x{LOCKED_STAIRS:03X}, MB_SLIDE_SOUTH), which would shove the bot onto the ice "
                "below and fall it from the wrong tile. The puzzle did not complete."
            )
        if state in (CRACKED_ICE, BROKEN_ICE):
            raise BotModeError(
                f"Ch22: REFUSING to step onto {nxt} — it reads 0x{state:03X} (cracked/broken ice). "
                "That is a FALL, and the fall is its own leg. The descent stops one tile short."
            )
        if state is None:
            raise BotModeError(
                f"Ch22: REFUSING to step onto {nxt} — it is off the live metatile grid entirely. "
                "The grid offset or the map is wrong; walking blind here costs the chapter."
            )
        yield from _bounded_step("Down", expect=nxt, map_enum=GYM_1F)
    raise BotModeError(
        f"Ch22: could not descend to {target} within {max_steps} steps — at {_here()}."
    )


def climb_to_juan() -> Generator:
    """(8,6) -> JUAN_STAND (8,3), up the stairs the third unlock just opened.

    ⛔ THIS IS THE GAP `walk_the_ice`'s OWN DOCSTRING USED TO PAPER OVER. The route table ends on
    the last ICE tile (8,6); Juan is three tiles further north, across the (8,5)/(8,4) stair pair.
    Every driver carried its own copy of this loop, so the production chapter had none.
    """
    from modules.modes import BotModeError
    from modules.story.early_game import wait_until_truly_controllable

    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: the climb to Juan needs GYM_1F; standing at {_where()}.")
    if not _at(GYM_1F, JUAN_STAND):
        yield from _climb_to(JUAN_STAND, max_steps=4)
    yield from wait_until_truly_controllable()
    if not _at(GYM_1F, JUAN_STAND):
        raise BotModeError(
            f"Ch22: the climb ended at {_where()}, not on JUAN_STAND {JUAN_STAND}."
        )


def enter_gym() -> Generator:
    """SOOTOPOLIS_CITY -> the gym door (31,32) -> GYM_1F, landing on GYM_ENTRANCE.

    ⛔ The (31,32) warp is one of the ten doors `SootopolisCity_OnLoad` keeps SEALED until
    `FLAG 0x9E` — §Ch21 leg 5's second leader talk is what opens it. A run that arrives here with
    that flag clear cannot enter, and it must say so rather than time out on a walk.
    """
    from modules.modes import BotModeError
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

    if _on_map(GYM_1F):
        yield from wait_until_truly_controllable()
        return
    if not _on_map(MapRSE.SOOTOPOLIS_CITY):
        raise BotModeError(
            f"Ch22: entering the gym starts from SOOTOPOLIS_CITY; standing at {_where()}."
        )
    yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 32), tries=6)
    yield from _navigate_riding_out(GYM_1F, GYM_ENTRANCE, tries=4)
    yield from wait_until_truly_controllable()
    if not _on_map(GYM_1F):
        raise BotModeError(
            f"Ch22: walked the (31,32) gym warp and did not end up on GYM_1F — at {_where()}. If "
            "the door is still sealed, §Ch21 leg 5's second Wallace talk did not complete "
            "(FLAG 0x9E)."
        )


def leave_gym_to_city() -> Generator:
    """GYM_1F -> SOOTOPOLIS_CITY, ending on the apron OUTSIDE the door, never on the warp itself."""
    from modules.modes import BotModeError
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

    if _on_map(MapRSE.SOOTOPOLIS_CITY):
        return
    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: leaving the gym starts from GYM_1F; standing at {_where()}.")
    # ⛔ (31,33) not (31,32): pathing to a DOOR warp ends you back INSIDE. Aim at the apron.
    yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 33), tries=6)
    yield from wait_until_truly_controllable()
    if not _on_map(MapRSE.SOOTOPOLIS_CITY):
        raise BotModeError(f"Ch22: left the gym and did not reach the city — at {_where()}.")


def assert_ch22_preflight() -> None:
    """Refuse the chapter rather than walk it into a wall. ⛔ Called BEFORE the retry loop.

    ‼ §Ch21's own preflight is DEAD CODE — defined and never called by `do_sootopolis_chapter()`.
    §Ch20 calls its own, and that is the placement copied here.
    """
    from modules.memory import get_event_flag
    from modules.modes import BotModeError
    from modules.pokemon_party import get_party

    party = [m for m in get_party() if m is not None]
    if len(party) < 2:
        raise BotModeError(
            f"Ch22: the gym needs more than one usable Pokémon; the party holds {len(party)}. "
            "⛔ There is no heal inside and `allow_escaping` is false on BOTH floors, so a party "
            "that cannot survive cannot leave the room it is standing in."
        )
    if not get_event_flag("RECEIVED_HM_WATERFALL"):
        raise BotModeError(
            "Ch22: `RECEIVED_HM_WATERFALL` is clear, so §Ch21 did not finish. The gym door at "
            "(31,32) is one of the ten Sootopolis doors sealed until that chapter's second "
            "Wallace talk, and entering would be impossible."
        )


def ch22_chapter_done() -> bool:
    """§Ch22 complete: the badge **AND** the bot is not still stranded inside the gym.

    ⛔ `juan_defeated()` ALONE IS NOT A COMPLETION PREDICATE. It is True the instant the badge flag
    is set — while the bot stands on JUAN_STAND, on a 20-tile island, with the exit warp and the
    ladder both unreachable and `allow_escaping` false on both floors. Grading on it would repeat
    §Ch15 (four floors underground), §Ch18 (an eleven-tile island) and §Ch19 (a living room), each
    of which PASSED its own test while stranded.
    ⇒ the second conjunct is POSITION: off the gym floors entirely.
    """
    from modules.map_data import MapRSE as _M

    if not juan_defeated():
        return False
    try:
        return not _on_map(GYM_1F) and not _on_map(_M.SOOTOPOLIS_CITY_GYM_B1F)
    except Exception:  # noqa: BLE001 - a reader that cannot answer must not report "done"
        return False


def do_sootopolis_gym_chapter(report: dict | None = None) -> Generator:
    """§Ch22 — GYM 8, JUAN. heal -> ice -> Juan -> fall -> B1F -> ladder -> out.

    ⛔⛔ THE LEG ORDER IS A FINDING, NOT A PREFERENCE. The fall comes AFTER the badge because
    `SootopolisCity_Gym_1F_EventScript_JuanDefeated` `settrainerflag`s all ten B1F trainers, so the
    post-badge descent is BATTLE-FREE (decomp-verified 2026-09-03). Before the badge that same walk
    costs three forced fights and ~48% of the party's HP, with no heal inside and no escape.
    ‼ And the ice is walked ONCE. `--driver ch22exit` walks it twice because it never fights Juan;
    an orchestrator that copied that shape would pay 2,232 frames and a second exact-cover risk for
    nothing.

    ⛔ A LOSS TO JUAN IS A WHITEOUT, AND IT DOES NOT COME BACK HERE. It unwinds as `StoryAbort` to
    `StoryMode.run`, which clears the latch, exits the Poké Center and re-enters `_play()` from the
    top — so the 3-attempt loop below is for `BotModeError` and NOTHING ELSE (KI-67). On that
    re-entry every leg self-skips on its own state and the puzzle is virgin again (MEASURED), so a
    lost fight costs the walk, never the chapter.
    """
    import os as _os_fault

    from modules.modes import BotModeError
    from modules.story.early_game import (
        StoryAbort,
        _ch14_say,
        _check_abort,
        reraise_if_aborting,
    )

    if report is None:
        report = {}
    if ch22_chapter_done():
        return  # resume-safe

    fault_nodescend = bool(_os_fault.environ.get("POKEBOT_CH22_FAULT_NODESCEND"))
    fault_stranded = bool(_os_fault.environ.get("POKEBOT_CH22_FAULT_STRANDED"))

    assert_ch22_preflight()

    attempts: list[str] = []
    for attempt in range(1, 4):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE the try
        try:
            # ⛔⛔ ARCHIVE THE PREVIOUS ATTEMPT'S READINGS AND START THIS ONE CLEAN. `walk_the_ice`
            # does `report.setdefault("steps", 0)` then `+= 1`, so a shared dict ACCUMULATES: two
            # attempts report `steps=128` and `sections` grows to six, and any check asserting
            # `steps == 64` fails on a CORRECT retry (its own error text even prints "step 65 of
            # 64"). MEASURED 2026-09-03: chapter drive 2 recovered from a lost Juan fight and
            # reported `ice_steps=128`. ⛔ ARCHIVED, NEVER DISCARDED — §Ch21's rule is that the
            # attempt which DIED is the one whose partial readings matter most.
            if "steps" in report:
                report.setdefault("previous_attempts", []).append(
                    {"steps": report.pop("steps"), "sections": report.pop("sections", None)}
                )
            # ⛔ RE-READ POSITION EVERY ATTEMPT. Every leg boundary here is a permanent flag or a
            # map change, so a phase decided once above the loop is stale on attempt 2.
            on_1f = _on_map(GYM_1F)
            on_b1f = _on_map(MapRSE.SOOTOPOLIS_CITY_GYM_B1F)
            badge = juan_defeated()

            # --- L1 HEAL (skipped once inside; there is no Poké Center in the gym) -------------
            if not on_1f and not on_b1f and not badge:
                yield from _heal_before_the_gym(report)
                yield from enter_gym()
                on_1f = True

            # --- L2 THE ICE + L3 THE FIGHT ------------------------------------------------------
            if not badge:
                if not on_b1f:
                    if not _on_map(GYM_1F):
                        yield from enter_gym()
                    # `walk_the_ice` refuses on a partially-walked floor, which is the correct
                    # answer for a mid-gym retry: leave and re-enter for virgin ice.
                    if not _at(GYM_1F, JUAN_STAND):
                        yield from walk_the_ice(report)
                        yield from climb_to_juan()
                    yield from fight_juan(report)
                    badge = juan_defeated()
                else:
                    # On B1F without the badge = a fall happened before the fight. Walk out and
                    # let the next attempt re-enter to virgin ice rather than guessing.
                    yield from walk_b1f_to_ladder(report)
                    yield from _ladder_to_1f()
                    yield from leave_gym_to_city()
                    raise BotModeError(
                        "Ch22: fell to B1F before beating Juan — walked back out to the city so "
                        "the next attempt gets virgin ice. This is a RECOVERY, not a defect."
                    )

            # --- L4 THE MANDATORY FALL + L5 THE WAY OUT ----------------------------------------
            if badge and not _on_map(MapRSE.SOOTOPOLIS_CITY):
                # ⛔⛔ ON GYM_1F THERE ARE **TWO** PLACES TO BE, AND ONLY ONE OF THEM NEEDS A FALL.
                # The ISLAND side is the stair column at or above FALL_STAGING; everything else —
                # including (11,22), the tile the B1F ladder lands on — is the ENTRANCE side, from
                # which the bot simply walks out. Without this split, a retry that begins after the
                # fall has already happened tries to DESCEND from (11,22) and raises the
                # single-column guard, which is correct but reads as a routing bug.
                # ‼ MEASURED by the `POKEBOT_CH22_FAULT_STRANDED` arm: attempts 2 and 3 both failed
                # with "the descent expects a single column; at (11, 22), target (8, 5)" — a
                # confusing cascade over a run whose only real problem was the un-walked exit.
                here = tuple(_here()) if _on_map(GYM_1F) else None
                on_island = here is not None and here[0] == STAIR_COLUMN and here[1] <= FALL_STAGING[1]
                if on_island:
                    if fault_nodescend:
                        raise BotModeError("FAULT NODESCEND: skipping the descent on purpose.")
                    yield from _descend_to(FALL_STAGING, max_steps=4)
                    yield from fall_to_b1f(report)
                if _on_map(MapRSE.SOOTOPOLIS_CITY_GYM_B1F):
                    yield from walk_b1f_to_ladder(report)
                    yield from _ladder_to_1f()
                if not fault_stranded:
                    yield from leave_gym_to_city()
        except StoryAbort:
            # ⛔ RE-RAISED, NEVER RETRIED HERE — the latch is cleared only by `StoryMode.run`, so
            # looping would burn all three attempts in a handful of frames and report three
            # failures, two of them invented (KI-67).
            raise
        except BotModeError as error:  # noqa: BLE001 - reported, never swallowed
            reraise_if_aborting(error)  # ⛔ FIRST statement of the handler
            attempts.append(f"attempt {attempt}: {type(error).__name__}: {str(error)[:200]}")
            _ch14_say(f"Story: Ch22 attempt {attempt} failed — {str(error)[:120]}")
            continue

        if ch22_chapter_done():
            _ch14_say("Story: Ch22 complete — Rain Badge won and out of the gym.")
            return
        attempts.append(
            f"attempt {attempt}: every leg ran but the chapter does not grade done "
            f"(badge={juan_defeated()}, at={_where()})"
        )
    raise BotModeError(
        "Ch22 (Gym 8 — Juan) failed after 3 attempts. " + " | ".join(attempts)
    )


def _heal_before_the_gym(report: dict | None = None) -> Generator:
    """Heal at the Sootopolis Poké Center and ASSERT the party survived the trip.

    ⛔⛔ THE HEAL CAN SHRINK THE PARTY. `heal_in_pokemon_center` calls
    `deposit_dead_weight_if_worth_it()`, and `team_policy.DEAD_WEIGHT_LEVEL_GAP = 8` makes anything
    more than 8 levels behind the best mon deposit-eligible. In the measured §Ch22 party that is
    Swellow (L41) AND Zigzagoon (L19) against Sceptile L50 — and Zigzagoon is NOT HM-exempt,
    because Wailmer shares its Surf. ⇒ assert by PID, and assert the COUNT, because a gym with no
    heal inside and no escape is the worst possible place to discover a 4-mon party.
    """
    from modules.map_data import PokemonCenter
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center
    from modules.pokemon_party import get_party
    from modules.story.early_game import reraise_if_aborting

    if report is None:
        report = {}
    before = {m.personality_value: m.species.name for m in get_party() if m is not None}
    try:
        yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)
    except Exception as error:  # noqa: BLE001
        reraise_if_aborting(error)
        raise BotModeError(
            f"Ch22: the Poké Center heal failed ({type(error).__name__}: {str(error)[:160]}). "
            "⛔ Refusing to enter a gym with no heal and no escape on a party of unknown health."
        ) from error

    after = {m.personality_value: (m.species.name, m.current_hp, m.total_hp)
             for m in get_party() if m is not None}
    report["party_before_heal"] = before
    report["party_after_heal"] = after
    missing = [f"{name}({pid})" for pid, name in before.items() if pid not in after]
    if missing:
        raise BotModeError(
            f"Ch22: the Poké Center trip REMOVED {missing} from the party (a rotation deposit). "
            f"⛔ Refusing to enter the gym short-handed — there is no heal inside and "
            f"`allow_escaping` is false on both floors."
        )
    not_full = [f"{n}={hp}/{mx}" for _pid, (n, hp, mx) in after.items() if hp != mx]
    if not_full:
        raise BotModeError(f"Ch22: heal did not restore the party: {not_full}.")


def _ladder_to_1f() -> Generator:
    """B1F ladder (11,22) -> GYM_1F. ⛔ The witness is the MAP CHANGE, never a coordinate."""
    from modules.map_data import MapRSE as _M
    from modules.modes import BotModeError
    from modules.story.early_game import _walk_through_warp, wait_until_truly_controllable

    if not _on_map(_M.SOOTOPOLIS_CITY_GYM_B1F):
        return
    yield from _walk_through_warp("Down", _M.SOOTOPOLIS_CITY_GYM_B1F.value, timeout_frames=400)
    yield from wait_until_truly_controllable()
    if not _on_map(GYM_1F):
        raise BotModeError(f"Ch22: took the B1F ladder and did not land on GYM_1F — at {_where()}.")
