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
import os as _os

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
    # ‼ `#24-progressiongate` (user-identified 2026-08-08). FIERY_PATH is reachable ONLY through
    # ROUTE112, and the Mauville→Route 112 corridor is sealed by a Rock Smash rock at ROUTE111
    # (18,101) — measured under `#24-smashroute`. Rock Smash FIELD USE requires the Dynamo Badge
    # (decomp: `src/party_menu.c:122`, `FIELD_MOVE_ROCK_SMASH, // FLAG_BADGE03_GET`), which is
    # WATTSON's badge. So every Fiery Path species is unobtainable until Wattson is beaten.
    # Without this line the counter planner offered Numel @ FIERY_PATH as Wattson's ONLY answer —
    # circular: the counter for Wattson sits behind Wattson.
    # ‼ This also correctly gates TRAINING there, which was equally impossible pre-badge.
    MapRSE.FIERY_PATH: "rocksmash",
    MapRSE.ROUTE111: "region",
    MapRSE.ROUTE115: "surf",
    MapRSE.ROUTE118: "surf",
    MapRSE.ROUTE119: "surf",
    MapRSE.ROUTE121: "surf",
}


#: ‼ AREA **ITEM** PREREQUISITES — a within-map split that no move unlocks (added 2026-08-02).
#:
#: `KNOWN_GATES` in `region_reach` gates map-PAIR EDGES and its values are FIELD MOVES, so it
#: cannot express either half of this: the barrier is INSIDE one map, and the key is an ITEM.
#: `is_map_reachable(ROUTE111)` is therefore correctly True — Route 111's southern half is
#: walkable from Mauville — while the training tile (25,55) sits NORTH of the Go-Goggles
#: desert and is not.
#:
#: ‼ MEASURED COST OF NOT HAVING THIS (batch5, `x4-runs/20260801-075805`): **28 events** of
#: `ROUTE111 (25, 55) is not reachable from here — dropping it as a training option for the
#: rest of this run`, i.e. roughly one wasted cross-Hoenn trek PER RUN. The oracle said yes,
#: the map disagreed, and the run paid for the trip to find out.
#:
#: ‼ THE FACT WAS ALREADY WRITTEN DOWN — TWICE — AND NEITHER COPY WAS QUERYABLE:
#: `counter_plan.huntable_candidates` ("whose tile sits north of the Go-Goggles desert") and
#: `early_game` ("it is Go-Goggles-gated by a script"). That is exactly the failure
#: `NO_RETURN_GROUNDS`' own header warns about — prose in a table nobody queries. This table
#: is queried.
#:
#: ‼ DELIBERATELY CONSERVATIVE. Strictly, the tile is also reachable from the FALLARBOR side
#: without goggles, so requiring the item can refuse a legitimately-walkable case. That is the
#: right trade and it is the same asymmetry this module already argues elsewhere: a false NO
#: costs one skipped relocation (the picker takes the next area), a false YES costs a whole
#: wasted trek — and the bot is on the SOUTH side for the boss preps that consult this.
AREA_ITEM_PREREQ: dict = {
    MapRSE.ROUTE111: "Go-Goggles",
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


#: ‼ CATCH-AND-LEAVE HUNTING GROUNDS (#24-counters phase 2, added 2026-07-30).
#:
#: A counter HUNT is not a training loop and must not be judged by the same rule. A
#: training loop needs three legs — reach the ground, spin on it, and walk BACK to a
#: Poké Center to heal — which is why `NO_RETURN_GROUNDS` exists. A hunt needs only
#: TWO: reach the ground and LEAVE it. So a ground can be illegal for `train_team`
#: and still perfectly legal here, and `NO_RETURN_GROUNDS`' own FIERY_PATH entry says
#: exactly that in prose ("a fine CATCH-AND-LEAVE hunting ground ... which needs no
#: heal trip; that is a different use and must not go through this picker").
#: This table is that different use, made consultable — prose in a table nobody
#: queries is the mistake NO_RETURN_GROUNDS' own header warns about.
#:
#: Each entry: ``map -> (spin_tile, measured evidence)``. Nothing goes in here on a
#: guess: the standing prevention rule is that a tile is adopted only after it is
#: proven FROM THE REAL ENTRY POINT, in both directions of the legs it needs.
HUNTING_GROUNDS: dict = {
    # Legs 1 and 2 both PASS from the real pre-Norman anchor: `story_harness.py
    # lavaridge --driver fierycave` walked Lavaridge -> FIERY_PATH (18,19) and then
    # back OUT of the cave onto Route 112 (2026-07-26). Only its leg 3 — the onward
    # heal trip Route 112 -> Lavaridge — fails, and a hunt never takes that leg.
    # This is the Norman answer's only home: Machop lives on FIERY_PATH (L15-16) and
    # JAGGED_PASS (L20-22), and Jagged Pass is no-return in the strong sense (it
    # cannot even path WITHIN itself — see NO_RETURN_GROUNDS).
    MapRSE.FIERY_PATH: (
        (18, 19),
        "Lavaridge -> (18,19) and (18,19) -> out of the cave both PASS "
        "(story_harness --driver fierycave, 2026-07-26); only the onward heal leg "
        "to Lavaridge fails, which a catch-and-leave hunt never walks",
    ),
}


def hunt_ground_tile(map_enum, *, require_driven: bool | None = None) -> "tuple | None":
    """The tile a COUNTER HUNT may stand on to spin for wild encounters on `map_enum`,
    or None if this map is not a proven hunting ground.

    ‼ WHITELIST, DELIBERATELY — it fails CLOSED. The counter planner ranks candidates
    over the WHOLE-GAME encounter index, so its raw output includes places the story
    has no business walking into mid-run: measured 2026-07-30, the top-ranked Fighting
    answer for Norman is a Victory Road Hariyama, and the Ground answers for Wattson
    include the Magma Hideout and Mirage Tower. Those rank high precisely BECAUSE they
    are endgame — the cost model prices "train it up to the team's level" at ~0 for a
    wild that is already above the team, so deep-game encounters look CHEAP.
    A blacklist of such places would be an ever-growing list of game facts written from
    memory (the one thing this project forbids); a whitelist needs no claim about
    Mirage Tower at all — it is simply not a ground anyone has swept, so it is refused.

    Two sources, both evidence-backed:
      * `TRAINING_GRASS` — two-way swept spin tiles (the strongest evidence we hold).
      * `HUNTING_GROUNDS` — reach-and-leave grounds, proven for this weaker requirement.

    A ground in `NO_RETURN_GROUNDS` is refused unless `HUNTING_GROUNDS` explicitly
    clears it, so JAGGED_PASS and ROUTE112 stay refused while FIERY_PATH does not.

    ‼‼ `require_driven` — MEASURED 2026-08-08, batch `20260808-095721`. **The two sources are
    NOT equally strong for a HUNT, and treating them as such cost 28 wasted cross-Hoenn treks
    in one batch.** Conversion by destination:

        Machop @ FIERY_PATH   (HUNTING_GROUNDS)   5 hunts,  5 caught  = 100%
        every other ground    (TRAINING_GRASS)   28 hunts,  0 caught  =   0%
        `could not reach` 72 / `Could not find a path` 45 / `hunt found nothing` 0

    **They are TRAVEL failures.** `TRAINING_GRASS` tiles were two-way swept for TRAINING, from
    TRAINING anchors; a counter hunt fires from wherever a BOSS is fought, which is a different
    journey the sweep never measured. `HUNTING_GROUNDS` is the table that encodes *driven,
    reach-and-leave* evidence, it has one entry, and that entry is the only rung that converts.
    Reusing a whitelist across two different questions is how a fails-closed gate quietly became
    fails-open.

    ‼ Why this is a NARROWING and not a loss: the counter hunt is bounded to **one attempt per
    boss per run**, so an unreachable destination does not cost a trek — it costs the boss. An
    honest immediate "no huntable candidate" is strictly better than a wasted journey that ends
    in the same stop. Widening again is a matter of SWEEPING more grounds from real boss anchors
    and adding them here — never of relaxing this flag.

    Default: strict for the counter hunt (the only caller). `POKEBOT_HUNT_ANYGROUND=1` restores
    the old permissive behaviour so the regression can be re-measured without reverting code.
    """
    import os as _os

    if require_driven is None:
        require_driven = _os.environ.get("POKEBOT_HUNT_ANYGROUND", "0").strip() not in ("1", "true", "yes")
    try:
        entry = HUNTING_GROUNDS.get(map_enum)
        if entry is not None:
            tile = entry[0]
            return tuple(tile) if tile is not None else None
        if require_driven:
            # Only DRIVEN reach-and-leave evidence counts (see the note above). A
            # TRAINING_GRASS tile proves we can stand and spin there; it does not prove a
            # hunt can GET there from a boss anchor, which is the journey that failed 28/28.
            return None
        if _return_blocked(map_enum) is not None:
            return None  # no-return and not cleared for hunting — refuse
        for candidate_map, tile, _band in TRAINING_GRASS:
            if candidate_map is map_enum and tile is not None:
                return tuple(tile)
        return None
    except Exception:
        # Fail CLOSED: an unreadable table must never widen where the bot may walk.
        return None


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


#: Which rule decides "is the local patch fodder?" (KI-31).
#:
#: ``"xp_rate"`` — **THE DEFAULT since 2026-07-29 (user directive).** Relocate when the better
#:                 area at least `XP_RATE_RELOCATE_RATIO`×es the xp rate. Fixes the measured
#:                 hole (teams at/below L17 could never relocate). Still not validated
#:                 end-to-end — see the note on `FODDER_RULE` below.
#: ``"legacy"``  — `local_max + FODDER_LEVEL_GAP < team_max`. The previous default; set
#:                 `POKEBOT_FODDER_RULE=legacy` to get it back, e.g. to A/B a regression.
#:
#: ‼ WHY A FLAG AND NOT A FIX. The legacy rule compares the WILD level to the TEAM level,
#: but this module's own calibrated model says `xp/battle = 50.2 * wild_level / 7` — xp is
#: proportional to the WILD level and does not depend on the team at all. Measured against
#: the real TRAINING_GRASS bands, teams **below ~L17** can never relocate (5 + 12 = 17), so a
#: L15 team on Route 102's L3-5 wilds forgoes a **2.8x** speedup. Above L17 the rule works.
#:
#: BUT the conservatism is DELIBERATE: `tools/story-dev/repro_fodder_grass.py` records the
#: contract — *"WATTSON / ROXANNE / an early team -> UNCHANGED 'train locally' (the whole
#: point of the conservative gap: proven-good prep must not move)"* — and L10-17 is exactly
#: those bosses. That repro needs a real ROM + save state, so it CANNOT run on the dev box.
#: Flipping the rule blind would gamble the user's overnight batches on an unrunnable test.
#: Hence: both rules live here, the pure decision is exhaustively testable without an
#: emulator, and the switch defaults to the proven behaviour.
#: ‼ SET IT WITHOUT EDITING CODE:  POKEBOT_FODDER_RULE=xp_rate
#: The first version of this flag was a bare constant, which meant running the A/B required
#: hand-editing this file on the batch machine — and `install.py`'s self-healing step does
#: `git checkout -- <drifted>`, so that edit could be REVERTED by the very installer the
#: user was told to run. An env var is immune to that, needs no code change on a remote
#: machine, and disappears when the shell closes.
#: ‼ DEFAULT FLIPPED TO "xp_rate" (user directive 2026-07-29).
#: The user runs the bot by DOUBLE-CLICKING `install_sandbox.py`, which cannot set an
#: environment variable — so an env-var-only switch meant the intended rule never actually
#: ran. Requiring a shell to get the intended behaviour is a broken interface, and the
#: earlier lesson applies: a flag whose only interface is inconvenient will silently sit at
#: the wrong value. Making it the default is the honest fix — every launch path (double-click,
#: GUI, CLI, x4 lane) now agrees, and `POKEBOT_FODDER_RULE=legacy` is the documented way back.
#:
#: ‼ RESIDUAL RISK, STATED PLAINLY: `repro_fodder_grass.py` — the test that governs this
#: decision, and the reason the default was `legacy` until now — STILL HAS NOT BEEN RUN, on
#: any machine. It needs a real ROM + save state. The rules provably differ only for teams at
#: or below L17 and only at boss prep (see `repro_fodder_rule.py`), so the blast radius is
#: bounded and every run reports the active rule in its log header — but this is a
#: user-directed default, not a validated one. If early-game prep regresses, set
#: `POKEBOT_FODDER_RULE=legacy` and say so.
_VALID_FODDER_RULES = ("legacy", "xp_rate")
FODDER_RULE = _os.environ.get("POKEBOT_FODDER_RULE", "xp_rate").strip().lower()
if FODDER_RULE not in _VALID_FODDER_RULES:
    # ‼ FAIL LOUDLY. A silent fallback here would be the worst possible outcome for an A/B:
    # a typo'd value would quietly run the LEGACY rule while the operator believed they were
    # testing the new one, and we would draw a confident conclusion from the wrong data.
    raise ValueError(
        f"POKEBOT_FODDER_RULE={FODDER_RULE!r} is not one of {_VALID_FODDER_RULES}. "
        "Refusing to guess — an unnoticed fallback would invalidate the A/B it was set for."
    )


def active_fodder_rule_banner() -> str:
    """One line naming the active rule, for the run header.

    ‼ WHY: without this, a log gives no way to tell WHICH rule produced it, so an A/B
    cannot be attributed after the fact. Any experiment whose variable is invisible in the
    output is not an experiment.
    """
    how = "env POKEBOT_FODDER_RULE" if "POKEBOT_FODDER_RULE" in _os.environ else "default"
    extra = f", ratio {XP_RATE_RELOCATE_RATIO}x" if FODDER_RULE == "xp_rate" else ""
    return f"Story: training-relocation rule = {FODDER_RULE} ({how}{extra})"

#: For ``FODDER_RULE = "xp_rate"``: how much better the candidate area's xp rate must be.
#: 2.0 = "at least halves the grind". Chosen because xp/battle is exactly proportional to
#: wild level, so a 2x band is a 2x rate — a plainly-worth-a-walk win. It needs no travel
#: measurement, which matters: travel cost is still UNMEASURED (`story_mode.py:576`), so the
#: rule is deliberately set to fire only on large wins.
XP_RATE_RELOCATE_RATIO = 2.0


def xp_per_battle(wild_level) -> float:
    """Modelled xp for one wild KO at `wild_level`. Proportional to the WILD level — it does
    NOT depend on the trainee (see `_CALIBRATED_AVG_WILD_BASE_EXP_YIELD`'s provenance)."""
    if not wild_level or wild_level <= 0:
        return 0.0
    return _CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild_level / 7


def relocation_floor(local_max: int, trainee_levels, fodder_gap: int) -> int:
    """Minimum wild level worth RELOCATING FOR, keyed to the mons actually being trained.

    ‼ THIS USED TO BE `max(local_max, team_max_now - FODDER_LEVEL_GAP)` INLINE IN
    `_prepare_for_fight`, AND `team_max_now` IS THE WRONG MON. It is the party's strongest
    member, but the mons in `need` are the stragglers. Measured in batch4
    (`x4-runs/20260731-201554`), a typical Norman party is `Marshtomp L35 / Ninjask L30 /
    Swellow L32 / Poochyena L12 / Shedinja L20` and `need` is the L12 and L20. Keying the
    floor to L35 demands wilds above L23, which rejects **ROUTE111 (L19-22)** — the one
    area reachable in that part of Hoenn — even though L19-22 is near-ideal for a L20
    trainee. The bot then printed `no better area is available` and skipped prep entirely:
    **167 times in one batch**, every one of them on ROUTE102's L3-4 grass.

    ‼ ONLY THE FLOOR MOVES. `train_team` runs with SWAP-TRAIN on, so a STRONGER team-mate
    does the fighting — `best_training_area`'s own `team_level` argument (winnability and
    scoring) is correctly the team max, and keying THAT to the trainee would be a second
    bug. This function answers a different question: "is somewhere worth walking to?"

    Never drops below `local_max` — relocating to something no better than the patch we are
    standing on is pure travel for nothing.
    """
    levels = [lv for lv in (trainee_levels or []) if lv is not None]
    if not levels:
        return local_max
    return max(local_max, max(levels) - fodder_gap)


def local_patch_is_fodder(local_max, team_max, fodder_level_gap, *,
                          best_available_max=None, rule: str = None) -> bool:
    """Is the LOCAL grass not worth grinding? PURE — no ROM, no emulator, no walking.

    Extracted from `story_mode._prepare_for_fight` so the decision can be tested
    exhaustively off-emulator (KI-31).

    ⛔⛔ THE DEFAULT IS ``"xp_rate"``, NOT ``"legacy"`` — CORRECTED 2026-09-09. This docstring used to
    say *"behaviour under the default rule is byte-for-byte the legacy expression it replaced"*, and
    the branch comment below still said ``"legacy" (default)``. **Both were false**:
    ``FODDER_RULE = _os.environ.get("POKEBOT_FODDER_RULE", "xp_rate")`` (see the constant above).
    ‼ The two rules are NOT equivalent. ``"xp_rate"`` returns **False (not fodder)** whenever
    ``best_available_max`` is falsy, so a caller that has not yet looked for an alternative gets NO
    relocation at all — where ``"legacy"`` would have compared levels and possibly relocated.
    ⇒ anyone reasoning about when this bot relocates from the old wording got it backwards; that
    misled a design brief on 2026-09-09 and three reviewers had to correct it.

    `best_available_max` is the HIGH band of the best reachable alternative, or None if the
    caller has not looked yet — the ``"xp_rate"`` rule needs it; ``"legacy"`` ignores it.
    """
    if local_max is None:
        return False
    rule = rule or FODDER_RULE
    if rule == "xp_rate":
        if not best_available_max:
            return False
        local_rate = xp_per_battle(local_max)
        if local_rate <= 0:
            return True
        return xp_per_battle(best_available_max) / local_rate >= XP_RATE_RELOCATE_RATIO
    # ⛔ "legacy" is NOT the default (the default is "xp_rate" — see FODDER_RULE above and
    # the docstring). This is the exact ORIGINAL test, kept and reachable via
    # POKEBOT_FODDER_RULE=legacy, which is the documented way to A/B a regression.
    return local_max + fodder_level_gap < team_max


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
