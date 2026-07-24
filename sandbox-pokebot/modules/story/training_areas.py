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
