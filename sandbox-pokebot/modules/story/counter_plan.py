"""Counter-species planner — KI-23 / punch-list #24-counters.

`StoryMode._boss_plan_is_hopeless(cfg)` (plugins/custom_modes/story_mode.py) detects that
the current team has NO super-effective answer to a boss (Winona overnight run: 198
attempts, 41 losses, never won, party far ABOVE her levels — nothing Electric/Rock/Ice
against her all-Flying line-up) and returns the attacking type names that WOULD work,
e.g. ``["Electric", "Rock", "Ice"]``.

This module turns "I need Ice" into somewhere to actually go: a concrete wild LAND
encounter, on a map, whose OWN type is one of the needed types — ranked so the answer
is something the current run can reach and use, not just something that exists in the
game.

PLANNING ONLY. This does not travel, catch, or train anything (that is a separate,
not-yet-built task) — mixing planning with execution would make neither testable in
isolation.

Reuses (does not rebuild):
  - `modules.encounter_index.get_encounter_index()` — the whole-game reverse
    wild-encounter index (species index -> [ {map, method, rate, level range} ]),
    already built from the ROM's `gWildMonHeaders` for the Hunt Planner (#9).
  - `modules.story.training_areas.TRAINING_GRASS` / `AREA_PREREQ` — verified spin
    tiles and the HM/region gates a caller can pass through the same `allow`
    predicate `best_training_area` already uses (e.g. `story_mode._training_area_allowed`).
"""

from __future__ import annotations

import logging

_log = logging.getLogger("story_counter_plan")


def _team_reference_level() -> "float | None":
    """Average level of the current battle-capable party — used only to prefer a level
    band that is usable without a long grind (ranking tier 4, lowest priority). Fail-safe:
    unknown -> None, which makes that tier neutral rather than raising."""
    try:
        from modules.pokemon_party import get_party

        levels = [mon.level for mon in get_party() if mon is not None and not mon.is_egg]
        if not levels:
            return None
        return sum(levels) / len(levels)
    except Exception:
        return None


def _estimated_cost_frames(species, band_high, rate, team_level):
    """Frames to FIND one of `species` and TRAIN it up to `team_level`, or None.

    Two measured terms, no invented constants:
      * find  — expected encounters to meet the species at `rate`% of that map's table,
                times `FRAMES_PER_WILD_BATTLE` (1433, measured against the emulator).
      * train — `estimate_frames_to_level` from the TOP of the candidate's level band
                (the best realistic catch) to `team_level`, using the real Gen 3 growth
                curve, grinding on wild of roughly its own band.

    Returns None when it cannot be priced (no team level, no band, no rate, or the
    growth-curve lookup fails). ‼ Callers must treat None as UNKNOWN, never as cheap —
    it sorts LAST within its tier, matching `estimate_frames_to_level`'s own contract.
    """
    if team_level is None or band_high is None or not rate or rate <= 0:
        return None
    try:
        from types import SimpleNamespace

        from modules.story.training_areas import (
            FRAMES_PER_WILD_BATTLE,
            estimate_frames_to_level,
        )

        find_frames = (100.0 / float(rate)) * FRAMES_PER_WILD_BATTLE
        as_caught = SimpleNamespace(
            species=species,
            total_exp=species.level_up_type.get_experience_needed_for_level(int(band_high)),
            level=int(band_high),
        )
        train_frames = estimate_frames_to_level(as_caught, int(team_level), int(band_high))
        if train_frames is None:
            return None
        return float(find_frames + train_frames)
    except Exception:
        return None


def find_counter_candidates(needed_type_names, *, allow=None, max_results: int = 5) -> list[dict]:
    """Find catchable species that answer `needed_type_names`, ranked by how USABLE
    they are, not just how "good" they are on paper.

    Each candidate dict carries: `species_name`, `types`, `map_enum`, `tile` (a verified
    TRAINING_GRASS spin tile if this map has one, else None), `level_band` (min, max),
    `encounter_rate`, `reachable` (bool), `score` (float, higher is better — also the
    sort key), plus the two HUNT facts added for phase 2 (2026-07-30):

      * `hunt_tile` — the tile a hunt may actually spin on (`training_areas.
        hunt_ground_tile`), or None. Wider than `tile`, because a catch-and-leave hunt
        needs no heal leg and so admits grounds a training loop must refuse.
      * `huntable`  — `reachable AND hunt_tile is not None`, i.e. "phase 2 could
        actually go and do this", as opposed to "this species answers the type".

    ‼ `huntable` is a SEPARATE FACT FROM `reachable`, and the executor must use it.
    Measured 2026-07-30 over the real ROM tables: the top-ranked Fighting answer for
    Norman is a **Victory Road Hariyama**, and Wattson's Ground answers include the
    Magma Hideout and Mirage Tower — all ranked high because the cost model prices
    "train it to the team's level" at ~0 for a wild that is ALREADY above the team, so
    endgame encounters read as cheap. Ranking is not a gate; `hunt_ground_tile` is.

    RANKING (documented per spec — order matters):
      1. Reachable beats unreachable, always. An ideal counter we cannot walk to is
         worth nothing — this project already shipped a picker
         (`training_areas.best_training_area`) that once proposed a Surf-gated area to a
         pre-Surf party; AREA_PREREQ exists precisely to stop that class of mistake.
      2. Among reachable candidates, prefer a species whose OWN type(s) cover MORE of the
         needed types (e.g. a Rock/Ice dual-type answers two of Winona's weaknesses with
         one catch).
      3. Prefer a verified spin tile (a TRAINING_GRASS entry) over a map we only know by
         name from the encounter index — we can actually stand on the former today.
      4. Prefer a higher wild encounter rate, then a level band close to the current
         team's average level, so the catch is usable without a long grind.

    `allow` is the SAME reachability-predicate contract as `best_training_area`'s:
    `(map_enum, tile, prereq_or_None) -> bool`. Passing the conservative default
    (`allow=None`) never returns a candidate whose map carries an AREA_PREREQ entry at
    all (mirroring `best_training_area`'s own `allow=None` behaviour of never proposing a
    gated area on a guess) — such candidates are dropped, not merely marked unreachable.

    Fail-safe: any read/index error returns `[]`, never raises — a planner that throws
    would turn a diagnosed stop (KI-23) into a crash.
    """
    try:
        needed = {str(n) for n in (needed_type_names or []) if n}
        if not needed:
            return []

        from modules.encounter_index import get_encounter_index
        from modules.map_data import get_map_enum
        from modules.pokemon import get_species_by_index
        from modules.story.training_areas import (
            AREA_PREREQ,
            TRAINING_GRASS,
            hunt_ground_tile,
        )

        tile_by_map = {map_enum: tile for map_enum, tile, _band in TRAINING_GRASS}
        team_level = _team_reference_level()
        index = get_encounter_index()

        candidates: list[dict] = []
        for species_index, locations in index.items():
            try:
                species = get_species_by_index(species_index)
            except Exception:
                continue
            hit_types = {t.name for t in species.types} & needed
            if not hit_types:
                continue  # this species is not one of the types we need

            for loc in locations:
                if loc.get("method") != "Grass":
                    continue  # LAND encounters only (spec)
                try:
                    map_enum = get_map_enum(tuple(loc["map"]))
                except Exception:
                    continue

                prereq = AREA_PREREQ.get(map_enum)
                if allow is None:
                    # Conservative default: never PROPOSE a gated area on a guess —
                    # exact mirror of best_training_area's `continue` under allow=None.
                    if prereq is not None:
                        continue
                    reachable = True
                else:
                    try:
                        reachable = bool(allow(map_enum, tile_by_map.get(map_enum), prereq))
                    except Exception:
                        reachable = False

                tile = tile_by_map.get(map_enum)
                lo, hi = loc.get("min_level"), loc.get("max_level")
                rate = loc.get("rate", 0) or 0

                level_gap = 0.0
                if team_level is not None and lo is not None and hi is not None:
                    level_gap = abs(((lo + hi) / 2) - team_level)

                # ‼ WHAT DOES THIS CANDIDATE ACTUALLY COST? (2026-07-26, measured.)
                # Ranking by encounter rate put a L6-10 Makuhita (50%) ahead of a
                # L20-22 Machop (25%) for a L31 team. Priced with the project's own
                # frame model, that "best" pick costs 363,982 frames to bring to L28
                # versus 98,877 for the Machop — 3.7x worse, and barely better than the
                # 399,000 frames the bot spent LOSING to Norman 21 times in run05. The
                # cheap-to-find mon is not the cheap mon.
                #   find  = expected encounters to meet one, at the measured
                #           frames-per-wild-battle
                #   train = the REAL Gen 3 growth curve from the top of its level band
                #           up to the team's level (`estimate_frames_to_level`)
                # Rate still matters — it just belongs in the small term, not the big
                # one, which is exactly the inversion this fixes.
                est_frames = _estimated_cost_frames(species, hi, rate, team_level)

                # Single composite score reproducing the documented tier order: each
                # tier's multiplier is large enough that no lower tier can outweigh a
                # higher one (type-coverage count and the rate/gap terms are both small
                # relative to the gaps between tiers).
                # TIER = the hard qualifiers, in order: can we get there at all > how
                # many needed types it answers > do we have a verified tile to path to.
                # Kept separate from `score` so cost can rank WITHIN a tier without the
                # rate term drowning it (rate*1000 dwarfed a 20-level gap by ~1000x).
                tier = (
                    (1_000_000_000.0 if reachable else 0.0)
                    + len(hit_types) * 10_000_000.0
                    + (100_000.0 if tile is not None else 0.0)
                )
                # `score` keeps its published meaning (higher is better, full composite)
                # for display and for callers that read it.
                score = tier + rate * 1_000.0 - level_gap

                # Where a HUNT could actually stand (see the docstring): deliberately
                # computed here rather than by the caller, so no executor can forget to
                # ask and walk into an unswept endgame interior. Fails closed.
                try:
                    hunt_tile = hunt_ground_tile(map_enum)
                except Exception:
                    hunt_tile = None

                candidates.append(
                    {
                        "species_name": species.name,
                        "types": [t.name for t in species.types],
                        "map_enum": map_enum,
                        "tile": tile,
                        "level_band": (lo, hi),
                        "encounter_rate": rate,
                        "reachable": reachable,
                        "score": score,
                        "tier": tier,
                        "est_frames": est_frames,
                        "hunt_tile": hunt_tile,
                        "huntable": bool(reachable and hunt_tile is not None),
                    }
                )

        # Tier order first (reachable > type coverage > has a verified tile — see the
        # score comment), then the CHEAPEST candidate within a tier. Candidates whose
        # cost cannot be estimated sort last within their tier rather than first: an
        # unknown cost is not a cheap one (same fail-safe rule as
        # `estimate_frames_to_level`'s own contract). When no cost is estimable at all
        # (e.g. no party to read a level from) every `est_frames` is None and this
        # degrades to the previous rate-then-level-gap ordering carried in `score`.
        candidates.sort(
            key=lambda c: (
                -c["tier"],
                float("inf") if c["est_frames"] is None else c["est_frames"],
                -c["score"],
                c["species_name"],
            )
        )
        return candidates[:max_results]
    except Exception as error:
        _log.warning("find_counter_candidates failed: %s", error)
        return []


def huntable_candidates(cands) -> list:
    """Every candidate phase 2 could actually go and catch, in rank order, DEDUPED by
    destination — the ladder's fallback list.

    ‼ WHY A LIST AND NOT JUST THE BEST (measured 2026-07-30, driven navigation from real
    saves): the top huntable destination is frequently NOT reachable in practice. Wattson's
    is Sandshrew @ ROUTE111 (25,55), whose tile sits north of the Go-Goggles desert, and
    Winona's is Electrike @ ROUTE118 (29,15), which is the KI-24 dual-elevation-bridge case
    — both failed real navigation in 255 frames from their true anchors, while Norman's
    Machop @ FIERY_PATH (18,19) ARRIVED in 2,922. Taking only the best meant two of the
    three bosses burned their one hunt on a destination the bot cannot walk to, when a
    reachable second choice existed further down the list (Wattson also has Nincada
    (Bug/Ground) @ ROUTE116 (11,7), on the corridor the story already walks).

    Deduped by `(map, tile)` because the encounter index lists one entry per species per
    map: six Geodude rows across six Magma Hideout floors are ONE destination, and without
    this a fallback budget would be spent re-walking to the same place.
    """
    try:
        seen = set()
        ordered = []
        for candidate in cands or []:
            if not candidate.get("huntable") or candidate.get("hunt_tile") is None:
                continue
            try:
                # ‼ Key on the map's NAME, not the map object. `MapRSE` members are
                # hashable, but nothing guarantees a caller's `map_enum` is — a stand-in
                # `SimpleNamespace` defines `__eq__`, which sets `__hash__` to None, and
                # the whole function then vanished into its own `except` and returned []
                # (caught 2026-07-30). Names are unique per map, so this is also the
                # correct dedupe key, not merely the safe one.
                map_enum = candidate.get("map_enum")
                key = (getattr(map_enum, "name", str(map_enum)), tuple(candidate["hunt_tile"]))
            except Exception:
                continue
            if key in seen:
                continue
            seen.add(key)
            ordered.append(candidate)
        return ordered
    except Exception as error:
        _log.warning("huntable_candidates failed: %s", error)
        return []


def best_huntable(cands) -> "dict | None":
    """The highest-ranked candidate phase 2 can ACTUALLY go and catch, or None.

    `cands` is assumed already sorted by `find_counter_candidates` (it is the only
    producer), so this is a first-match scan, not a re-rank — the ranking contract
    stays in one place. A caller that gets None has a diagnosis but no action, and
    must fall through to the honest stop rather than inventing a destination.

    ‼ This is the ONLY function an executor should use to pick where to go. Reading
    `cands[0]` instead is the bug this exists to prevent: rank 1 for Norman is a
    Victory Road Hariyama (measured 2026-07-30).
    """
    try:
        for candidate in cands or []:
            if candidate.get("huntable") and candidate.get("hunt_tile") is not None:
                return candidate
        return None
    except Exception as error:
        _log.warning("best_huntable failed: %s", error)
        return None


def summarise_candidates(cands) -> str:
    """Short human-readable line per candidate, for logging."""
    try:
        lines = []
        for c in cands:
            tile = c.get("hunt_tile") or c.get("tile")
            tile_str = f"tile {tile}" if tile is not None else "tile unmapped"
            if not c.get("huntable", False):
                # Say WHY it is only a diagnosis. A log that lists a target the bot
                # will never walk to, with no marker, reads as a plan that failed.
                tile_str += ", NOT HUNTABLE"
            lo, hi = c.get("level_band", (None, None))
            band_str = f"L{lo}-{hi}" if lo is not None and hi is not None else "L?"
            map_enum = c.get("map_enum")
            map_name = getattr(map_enum, "pretty_name", str(map_enum))
            reach_str = "reachable" if c.get("reachable") else "UNREACHABLE"
            types = "/".join(c.get("types", []))
            lines.append(
                f"{c.get('species_name')} ({types}) on {map_name} ({tile_str}, {band_str}, "
                f"{c.get('encounter_rate')}% rate) — {reach_str}"
            )
        return "\n".join(lines)
    except Exception as error:
        _log.warning("summarise_candidates failed: %s", error)
        return ""
