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
    (MapRSE.ROUTE103, (5, 7), (2, 4)),   # ROUTE103_GRASS_TILE (Segment 1 training)
    (MapRSE.ROUTE116, (11, 7), (6, 8)),  # RUSTBORO_TRAINING_GRASS (pre-Roxanne)
]

# Level ranges known, spin tile still to be MAPPED (fill tile as the map is reached):
PENDING_GRASS: list[tuple] = [
    (MapRSE.ROUTE102, None, (3, 5)),
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
