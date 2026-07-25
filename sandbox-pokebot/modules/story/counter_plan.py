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


def find_counter_candidates(needed_type_names, *, allow=None, max_results: int = 5) -> list[dict]:
    """Find catchable species that answer `needed_type_names`, ranked by how USABLE
    they are, not just how "good" they are on paper.

    Each candidate dict carries: `species_name`, `types`, `map_enum`, `tile` (a verified
    TRAINING_GRASS spin tile if this map has one, else None), `level_band` (min, max),
    `encounter_rate`, `reachable` (bool), `score` (float, higher is better — also the
    sort key).

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
        from modules.story.training_areas import AREA_PREREQ, TRAINING_GRASS

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

                # Single composite score reproducing the documented tier order: each
                # tier's multiplier is large enough that no lower tier can outweigh a
                # higher one (type-coverage count and the rate/gap terms are both small
                # relative to the gaps between tiers).
                score = (
                    (1_000_000_000.0 if reachable else 0.0)
                    + len(hit_types) * 10_000_000.0
                    + (100_000.0 if tile is not None else 0.0)
                    + rate * 1_000.0
                    - level_gap
                )

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
                    }
                )

        candidates.sort(key=lambda c: (-c["score"], c["species_name"]))
        return candidates[:max_results]
    except Exception as error:
        _log.warning("find_counter_candidates failed: %s", error)
        return []


def summarise_candidates(cands) -> str:
    """Short human-readable line per candidate, for logging."""
    try:
        lines = []
        for c in cands:
            tile = c.get("tile")
            tile_str = f"tile {tile}" if tile is not None else "tile unmapped"
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
