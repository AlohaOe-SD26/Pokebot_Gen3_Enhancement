"""Training-area level spectrum — groundwork for area-appropriate training.

USER DIRECTIVE (2026-07-21, Option 1): to train an under-levelled team member
EFFICIENTLY, send it to a grass area whose wild Pokémon are around its own level, so
it wins WINNABLE fights for FULL XP — rather than swap-training (half XP) everywhere.
`SwapTrainBattleStrategy` (see plugins/custom_modes/story_mode.py) remains the robust
fallback that works in ANY area; this table is what a future `train_team` will consult
to PREFER a suitable area when one is reachable.

Each entry: ``(map, spin_tile, (min_wild_level, max_wild_level))``.
  * Levels are the Emerald tall-grass encounter ranges for that map.
  * ``spin_tile`` is a verified tall-grass tile to spin on, or ``None`` if that map's
    tile hasn't been mapped yet (planning §AA "map-as-reached" — fill it in when the
    bot next reaches that map, then move the entry into ``TRAINING_GRASS``).

STATUS: data + query helper only. NOT yet wired into `train_team` — that integration
(route the low mon to the best area, train, and progress upward as it levels, with
swap-train as fallback) is punch-list #24-trainmap.
"""

import math

from modules.map_data import MapRSE

# Areas with a VERIFIED spin tile — usable for area-appropriate training today.
TRAINING_GRASS: list[tuple] = [
    (MapRSE.ROUTE101, (9, 9), (2, 3)),   # tile used by travel_to_route103()
    (MapRSE.ROUTE102, (9, 2), (3, 5)),   # PETALBURG_TRAINING_GRASS (Ch12 Norman prep;
    # two-way swept from the Petalburg PC door (20,16), 2026-07-24 — hosts Lotad, a
    # Surf learner, which the 12c HM hunt needs reachable from Petalburg)
    (MapRSE.ROUTE103, (5, 7), (2, 4)),   # ROUTE103_GRASS_TILE (Segment 1 training)
    (MapRSE.ROUTE116, (11, 7), (6, 8)),  # RUSTBORO_TRAINING_GRASS (pre-Roxanne)
    (MapRSE.ROUTE117, (31, 16), (13, 14)),  # ROUTE117_TRAINING_GRASS (Ch9 Wattson prep;
    # two-way swept FROM the real entry 2026-07-22 — the Mauville-frontier ground)
    # ‼ ROUTE114 (15-18) is DEMOTED to PENDING: the candidate tile (18,29) passed a
    # same-map two-way check but is unreachable from EVERY real story anchor tested
    # (Mauville / Fallarbor / Rustboro / Petalburg, 2026-07-24). Same-map connectivity
    # does not imply the story can get there — re-derive from a Fallarbor-side anchor
    # before promoting.
    (MapRSE.ROUTE111, (25, 55), (19, 22)),  # ‼ FALLARBOR-SIDE ONLY: this tile is NORTH of
    # the Go-Goggles desert, which splits Route 111 in two. Verified 2026-07-24: reachable
    # from Fallarbor, NOT from Mauville/Rustboro/Petalburg, and NO Mauville-side Route 111
    # grass exists (y>88 scan found none). The caller's reachability predicate is what keeps
    # this honest — never assume "same map" means "we can get there".
    (MapRSE.ROUTE115, (6, 53), (23, 26)),  # post-Norman band; same-map two-way verified
    # vs. (6, 45) (dist 8) on norman_done.ss1, 2026-07-24
    (MapRSE.ROUTE118, (29, 15), (24, 27)),  # post-Norman band; same-map two-way verified
    # vs. (27, 9) (dist 8) on norman_done.ss1, 2026-07-24
    (MapRSE.ROUTE119, (21, 109), (24, 27)),  # post-Norman band; same-map two-way verified
    # vs. (21, 101) (dist 8) on norman_done.ss1, 2026-07-24
    (MapRSE.ROUTE121, (44, 14), (25, 28)),  # post-Norman band (highest mapped); same-map
    # two-way verified vs. (48, 10) (dist 8) on norman_done.ss1, 2026-07-24
]

# Level ranges known, spin tile still to be MAPPED (fill tile as the map is reached):
PENDING_GRASS: list[tuple] = [
    (MapRSE.ROUTE104, None, (4, 6)),
    (MapRSE.PETALBURG_WOODS, None, (5, 6)),
    (MapRSE.RUSTURF_TUNNEL, None, (5, 6)),  # Whismur (no grass — cave; here for ref)
    (MapRSE.GRANITE_CAVE_1F, (35, 11), (6, 10)),  # cave-floor encounters (Zubat/Makuhita/
    # Abra/Geodude); the ONLY wild source reachable from Dewford before Surf — Route 106 /
    # Route 107 / Dewford itself are SURF-ONLY (no land table at all; probed 2026-07-22).
    # Kept out of TRAINING_GRASS until the spin tile is validated live.
    #
    # ‼ DEEPER FLOORS — DECOMP-VERIFIED 2026-07-26, BLOCKED ON ONE THING (see below).
    # User request: train on B1F/B2F rather than 1F, which is the weakest floor.
    # Encounter tables (src/data/wild_encounters.json, rate 10 = 5.56 %/step):
    #   B1F  Zubat 30 / Aron 40 / Abra 10 / Makuhita 10 / Sableye 10   L9-11
    #   B2F  Zubat 30 / Aron 40 / Abra 10 / Sableye 20                 L10-12
    # Neither floor is gated by any HM, item or flag (B2F's scripts.inc is `.byte 0`).
    # Flash is locked behind Badge 2 so both are dark pre-Brawly — COSMETIC ONLY,
    # collision and pathing are unaffected.
    #
    # Spin tiles below were derived by decoding map.bin (collision/elevation) +
    # metatile_attributes.bin and flood-filling with the game's own rules. Both are
    # MB_CAVE with MB_CAVE-or-wall on all four sides, ~4 steps from their arrival ladder.
    #
    # ‼ B1F's 62 CRACKED-FLOOR TILES ARE ALL UNREACHABLE ON FOOT. They sit north of the
    # muddy slope at (9,9)/(9,10), which cannot be climbed without the Mach Bike, so the
    # 126-tile arrival region (y=11..22) contains ZERO of them. Do not send the bot north
    # of that slope, and do not let it train here on a bike.
    (MapRSE.GRANITE_CAVE_B1F, (3, 18), (9, 11)),   # 1-wide N-S corridor, walls BOTH sides
    # for (3,18) and its partner (3,17), so a stray left/right input is a physical no-op.
    # 4 steps from the arrival ladder (4,21); 11 tiles from the nearest cracked floor.
    (MapRSE.GRANITE_CAVE_B2F, (28, 17), (10, 12)),  # dead-end nook vs the east wall,
    # partner (28,16); 4 steps from the (28,21) ladder. B2F has ZERO cracked floors and
    # 203 MB_CAVE tiles in this pocket. Corroborated independently: upstream
    # `modules/modes/rock_smash.py:409` already navigates to GRANITE_CAVE_B2F (28,21).
    #
    # ‼ WHY THESE ARE STILL PENDING AND NOT PROMOTED: `_CAVE_EXITS` / `_CAVE_ENTRANCES`
    # in `early_game.py` are SINGLE-HOP tables — one warp in, one warp out. B1F and B2F
    # are two and three hops deep from Route 106, so promoting them without first making
    # that threading chain-aware would break the post-training HEAL: the global navigator
    # cannot cross warp levels, and that exact failure already dropped two real-hardware
    # runs to Manual (2026-07-22, see `_exit_training_cave_if_inside`). Make the entry and
    # exit chain-aware FIRST, then promote — and validate live, because this is
    # navigation code and this project's regressions live there.
]


def best_training_grass(mon_level: int):
    """Return the ``(map, spin_tile)`` best suited to levelling a mon of ``mon_level``
    for FULL XP, or ``None`` if no MAPPED area fits (caller then falls back to
    swap-training wherever it already is).

    Heuristic: a mon trains well where it can WIN yet the wilds still give worthwhile
    XP — roughly, where the wild band tops out at or just above the mon's level. We
    pick the mapped area whose max wild level is closest to ``mon_level + 1`` while the
    mon can still handle the low end (``mon_level >= min - 1``). Prefer the HIGHER area
    on ties (more XP per battle)."""
    best = None
    best_score = None
    for map_enum, tile, (lo, hi) in TRAINING_GRASS:
        if tile is None:
            continue
        # ‼ REFUSE NO-RETURN GROUNDS FIRST. A training loop must be able to walk BACK to
        # a Poké Center to heal; a ground that cannot strands the run. Checked before the
        # reachability predicate because `allow` answers "can I get there", which is TRUE
        # for these — being reachable is exactly what makes them dangerous.
        if _return_blocked(map_enum) is not None:
            continue
        if mon_level < lo - 1:
            continue  # wilds too strong — the mon would lose here
        score = (abs((mon_level + 1) - hi), -hi)  # closeness to mon_level+1, then higher area
        if best_score is None or score < best_score:
            best, best_score = (map_enum, tile), score
    return best


# ‼ STORY-STAGE GATE (2026-07-24). Level fit alone is NOT enough: the richest bands sit
# behind HM gates, so a naive "highest winnable band" sends a pre-Surf, Petalburg-standing
# team to Route 121 (past Lilycove). Areas listed here are only legal once the party can
# actually get there. "surf" = the water routes east/north of Mauville and the Route 115
# coast — all unreachable on foot. Everything absent from this dict is on-foot reachable
# once its region has been visited (the corridor the story already walked).
#   "surf"   = across water; needs a party mon that actually KNOWS Surf (badge alone is
#              not enough — map_path.can_surf() requires the move).
#   "region" = on-foot but POSITION-gated: only reachable from part of the map/world, so it
#              is legal only when a live reachability check says so (Route 111's grass is
#              north of the desert = Fallarbor-side only). Marked so the conservative
#              `allow=None` default refuses to propose it on a guess.
AREA_PREREQ: dict = {
    MapRSE.ROUTE111: "region",
    MapRSE.ROUTE115: "surf",
    MapRSE.ROUTE118: "surf",
    MapRSE.ROUTE119: "surf",
    MapRSE.ROUTE121: "surf",
}


#: ‼ ONE-WAY / NO-RETURN GROUNDS — maps you can REACH but cannot get BACK from, so they
#: can never host a training or hunting loop (which must return to a Poké Center to heal).
#: A ground whose return leg fails strands the run; that is the exact class that dropped
#: two real-HW runs to Manual (2026-07-22) and it is what this table exists to prevent.
#:
#: ‼‼ WHY THIS TABLE EXISTS AT ALL (user directive 2026-07-26). Every fact below was
#: ALREADY KNOWN — recorded 2026-07-23 in 03-PUNCH-LIST/04-HANDOFF as "LAVARIDGE HAS NO
#: REACHABLE TRAINING GRASS ... Jagged Pass cannot be re-entered from the town (one-way
#: ledges) and Route 112's lower grass has no return path". It lived only in PROSE, in
#: documents nobody reads while choosing a tile, so on 2026-07-26 it was re-derived from
#: scratch by a full two-way probe cycle — after the same session had *quoted* the Jagged
#: Pass half and still asserted Fiery Path was "traversable both ways". Prose did not stop
#: it; a table the picker consults does. ADD TO THIS TABLE, never to a doc alone.
#:
#: Measured evidence for each entry is in the value string. `best_training_area` and
#: `best_training_grass` refuse these outright, before any reachability predicate runs.
NO_RETURN_GROUNDS: dict = {
    # Two-way sweep 2026-07-23 (tools/story-dev/jaggedgrass_probe.py): Jagged Pass is
    # entered by DESCENDING one-way ledges from Mt. Chimney and cannot be re-entered from
    # Lavaridge. Re-confirmed 2026-07-26 by probe_counter_tiles.py --nav, which reached
    # JAGGED_PASS (14,40) and then could not path WITHIN the map to (16,22).
    MapRSE.JAGGED_PASS: (
        "one-way ledges from Mt. Chimney; not re-enterable from Lavaridge "
        "(sweep 2026-07-23, re-confirmed 2026-07-26)"
    ),
    # Route 112's LOWER section (the Fiery Path south door side) cannot path back to
    # Lavaridge. Measured 2026-07-26 and the asymmetry is stark on the identical pair:
    #   Lavaridge (9,6) -> ROUTE112 (11,36) = OK, 60 waypoints
    #   ROUTE112 (11,36) -> Lavaridge (9,6) = FAIL
    # so a heal trip from there cannot complete. Recorded in prose 2026-07-23 as
    # "Route 112's lower grass has no return path".
    MapRSE.ROUTE112: (
        "lower section cannot path back to Lavaridge (ledges); Lavaridge->door OK at 60 "
        "waypoints, door->Lavaridge FAILS (measured 2026-07-26; prose 2026-07-23)"
    ),
    # Reached from Lavaridge and exits cleanly onto ROUTE112 (both legs PASS,
    # story_harness --driver fierycave 2026-07-26) — but it inherits Route 112's problem:
    # the heal leg to Lavaridge then fails, so it cannot host a training loop. It remains
    # a fine CATCH-AND-LEAVE hunting ground (#24-counters phase 2), which needs no heal
    # trip; that is a different use and must not go through this picker.
    MapRSE.FIERY_PATH: (
        "reachable and exitable (both legs PASS, story_harness --driver fierycave "
        "2026-07-26), but the onward heal leg to Lavaridge fails — see ROUTE112. Usable "
        "for catch-and-leave hunting, NOT for a training loop (measured 2026-07-26)"
    ),
}


def _return_blocked(map_enum) -> "str | None":
    """Reason this ground can be reached but not returned FROM, or None if it is fine."""
    return NO_RETURN_GROUNDS.get(map_enum)


def best_training_area(team_level: int, *, min_wild_max: int = 0, allow=None):
    """Pick the training area best matched to `team_level` for FULL-xp grinding.

    Returns ``(map_enum, tile, (lo, hi))`` or ``None``. Only areas whose max wild level
    is > ``min_wild_max`` are considered, so a caller can say "only bother if it beats
    what I already have". Winnability guard: never pick an area whose LOW end is above
    the trainee (``team_level >= lo - 1``). Among the winnable, richer-than-min areas,
    prefer the one whose HIGH end is closest to ``team_level`` without a hard cap —
    ties break toward the HIGHER band (more xp per battle).

    ``allow`` is a REACHABILITY predicate ``(map_enum, tile, prereq_or_None) -> bool`` and
    is what keeps the answer honest — see AREA_PREREQ. It receives the TILE too, because
    "the map is reachable" does not imply "that tile is": Route 111's grass sits north of
    the Go-Goggles desert, which splits the map in two. Callers that cannot evaluate story
    state may pass ``allow=None``, which then only permits areas with NO prerequisite
    (the conservative default: never propose an HM-gated area on a guess)."""
    best = None
    best_score = None
    for map_enum, tile, (lo, hi) in TRAINING_GRASS:
        if tile is None:
            continue
        # ‼ REFUSE NO-RETURN GROUNDS FIRST — same rule as `best_training_grass`. These
        # ARE reachable, which is precisely why `allow` cannot catch them: the problem is
        # getting BACK to heal. See NO_RETURN_GROUNDS for the measured evidence.
        if _return_blocked(map_enum) is not None:
            continue
        if hi <= min_wild_max:
            continue  # doesn't beat the floor the caller already has
        if team_level < lo - 1:
            continue  # wilds too strong — the trainee would lose here
        prereq = AREA_PREREQ.get(map_enum)
        if allow is None:
            if prereq is not None:
                continue  # conservative default — unreachable unless proven otherwise
        elif not allow(map_enum, tile, prereq):
            continue
        score = (abs(hi - team_level), -hi)  # closeness to team_level, then higher band
        if best_score is None or score < best_score:
            best, best_score = (map_enum, tile, (lo, hi)), score
    return best


# ‼ FRAME-COST ESTIMATOR (2026-07-24, punch-list #24). Both the evo-lookahead and the
# "topup" branch in story_mode.py budgeted grinds purely in LEVELS (``mon.level + 3``),
# but the real cost is FRAMES and frames-per-level varies enormously with where you grind.
# Live consequence: a fresh run decided a L33 Combusken should reach L36 (Blaziken); the
# only reachable grass was Route 102 at L3-5 wilds. tools/story-dev/probe_training_economics.py
# measured, on the captured save that produced this failure: 28.7 xp/battle and 1433
# frames/battle on that patch -> ~300 battles -> ~430,000 frames for those 3 levels alone.
# The run burned ~2,000,000 frames total and hit the frame cap one level short. The same 3
# levels on a properly-matched (e.g. L19-22) patch would cost several times less.

#: Measured average frames for ONE wild battle (tools/story-dev/probe_training_economics.py
#: Section 4, via the FAITHFUL story_harness.py --driver traintest102 on Route 102, save
#: prenorman_fodder_grind.ss1): 83 real XP events, avg 1433 frames/battle (min 155, max
#: 3948, median 1380). MEASURED against the real emulator, not modelled.
FRAMES_PER_WILD_BATTLE = 1433

# The formula probe_training_economics.py validated is XP = floor(base_exp_yield * foe_level
# / 7), using the DEFEATED wild's own base_exp_yield/level (NOT the trainee's level — xp/battle
# does not scale with who is training). `estimate_frames_to_level`'s signature only carries a
# scalar `wild_level` (no map), so it cannot read a real per-area encounter table the way the
# probe does — instead it uses a single CALIBRATED average base_exp_yield standing in for "a
# typical early wild", chosen so this formula reproduces the probe's own MEASURED Route 102
# figure (28.7 xp/battle at wild_level≈4): 28.7 = X * 4 / 7  =>  X ≈ 50.2. This is MODELLED,
# not measured — a caller that already has a real map/encounter table available should prefer
# reading it directly (see probe_training_economics.py Section 3) over this approximation.
_CALIBRATED_AVG_WILD_BASE_EXP_YIELD = 50.2


def estimate_frames_to_level(mon, target_level: int, wild_level) -> "int | None":
    """Estimate the FRAMES needed to grind ``mon`` from its current exp to ``target_level``
    on wild grass whose strongest wild is ``wild_level`` (e.g. the return value of
    `story_mode.py`'s ``_wild_land_max`` for the local/chosen training patch).

    Numbers used, and their provenance:
      * Exp still needed: ``mon.species.level_up_type.get_experience_needed_for_level(
        target_level) - mon.total_exp`` — the REAL Gen 3 growth curve (the same API
        ``probe_training_economics.py`` and ``modules/daycare.py`` use), not a hand-rolled
        curve.
      * Expected xp/battle: MODELLED as ``_CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild_level
        / 7`` — see the constant's comment above for the calibration and its provenance.
      * Frames/battle: ``FRAMES_PER_WILD_BATTLE`` (1433) — MEASURED, see above.

    Returns the estimated frame count (``0`` if ``mon`` is already at/above
    ``target_level``), or ``None`` if the cost cannot be estimated (missing/invalid
    ``wild_level``, or the growth-curve lookup failed). Callers MUST treat ``None`` as
    "unknown", never as "cheap" — fail safe and do not commit to the grind."""
    if wild_level is None or wild_level <= 0:
        return None
    try:
        needed_exp = mon.species.level_up_type.get_experience_needed_for_level(target_level) - mon.total_exp
    except Exception:
        return None
    if needed_exp <= 0:
        return 0
    xp_per_battle = _CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild_level / 7
    if xp_per_battle <= 0:
        return None
    battles_needed = math.ceil(needed_exp / xp_per_battle)
    return battles_needed * FRAMES_PER_WILD_BATTLE
