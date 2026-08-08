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
            AREA_ITEM_PREREQ,
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
            # ‼‼ `#24-movepoolcounters` (user directive 2026-08-07): A COUNTER IS A MOVE, NOT A
            # TYPE. This filter used to be `if not hit_types: continue`, i.e. pure species
            # typing — and that is why **Winona had ZERO huntable candidates**. Measured across
            # all 11 huntable grounds, her needed types (Rock/Ice/Dragon) appear exactly once:
            # Geodude on ROUTE111, via **Rock Smash**, which the `method != "Grass"` filter below
            # then drops. Grass-method matches: 0.
            #
            # A species that LEARNS a counter-type move answers the boss just as well. With this,
            # Winona gains two candidates on grounds the bot already walks:
            #     Baltoy @ ROUTE111  Grass 24% L19-21 — Rock Tomb  at L15
            #     Slugma @ FIERY_PATH Grass 10% L15   — Rock Throw at L15
            # Both are caught ALREADY KNOWING the move (learn level <= the wild's level), and
            # FIERY_PATH is the ground where Norman's hunt already succeeds 6 of 7 times.
            #
            # ‼ THREE GATES, ALL REQUIRED — the unfiltered version is WORSE THAN PURE TYPING.
            # Raw "can learn a move of a needed type" yields +82 for Winona and +47 for Norman,
            # and is nearly all junk: TM13 Ice Beam / TM14 Blizzard (Gen 3 TMs are SINGLE-USE and
            # we almost certainly do not own them) and HM06 Rock Smash at **20 power** — the
            # exact case CREDIBLE_ANSWER_POWER exists to reject. Unfiltered, every Zigzagoon
            # becomes a Norman counter.
            #   1. DAMAGING ONLY — `base_power > 0`. A stat-change, field-effect or pure-status
            #      move cannot answer a type weakness (Growl, Sunny Day, Toxic).
            #      ‼ Judge on base_power, NEVER on the name or on having a secondary effect:
            #      Smog is 20 bp Poison damage with `POISON_HIT`, i.e. DAMAGING.
            #   2. OBTAINABLE WITHOUT A PURCHASE — LEVEL-UP moves only, and only if the wild
            #      already knows it at capture (`entry.level <= loc max level`). No TM/tutor
            #      assumptions, and no dependency on training it up afterwards.
            #   3. CREDIBLE POWER — the same floor the boss-answer test uses.
            move_answer = None
            if not hit_types:
                try:
                    best = None
                    for entry in species.learnset.level_up:
                        mv = entry.move
                        if mv.base_power <= 0 or mv.type.name not in needed:
                            continue
                        if entry.level > _loc_max_level(locations):
                            continue  # it would not know the move when we catch it
                        stab = 1.5 if mv.type.name in {t.name for t in species.types} else 1.0
                        if mv.base_power * 2.0 * stab < _CREDIBLE_ANSWER_POWER:
                            continue
                        if best is None or mv.base_power > best[1].base_power:
                            best = (entry.level, mv)
                    if best is not None:
                        move_answer = best
                except Exception:  # noqa: BLE001 — a learnset hiccup must not kill the plan
                    move_answer = None
            if not hit_types and move_answer is None:
                continue  # neither its type nor its level-up movepool answers this boss

            for loc in locations:
                if loc.get("method") != "Grass":
                    continue  # LAND encounters only (spec)
                try:
                    map_enum = get_map_enum(tuple(loc["map"]))
                except Exception:
                    continue

                # ‼‼ `#24-counterdesertgate` (2026-08-07). ITEM-GATED AREAS ARE REFUSED HERE,
                # by the COUNTER PLANNER ITSELF, and deliberately not by flipping the global
                # `POKEBOT_AREA_ITEM_GATE`.
                #
                # MEASURED, batch `20260807-200030`: **7 hunts to ROUTE111 (25,55) for Baltoy,
                # 0 caught.** `AREA_ITEM_PREREQ` gates Route 111's desert on the Go-Goggles and
                # the spin tile (25,55) sits NORTH of that gate, so the bot treks cross-Hoenn,
                # cannot enter, and spins wherever it stopped — the log fills with Zigzagoons.
                # This module referenced `AREA_ITEM_PREREQ` **zero times**; it consulted only
                # `AREA_PREREQ`, which says `region` for ROUTE111 and passes.
                #
                # ‼ WHY NOT JUST TURN THE EXISTING GATE BACK ON. `_counter_area_allowed` has one
                # behind `POKEBOT_AREA_ITEM_GATE`, OFF BY DEFAULT since 2026-08-04 with the note
                # "THIS GATE COST MORE THAN IT SAVED" — measured against 28 wasted TRAINING
                # relocations per batch. That ruling was about TRAINING, where a bad pick costs
                # one trek and the picker simply tries again. **A COUNTER HUNT GETS ONE ATTEMPT
                # PER BOSS PER RUN** (`_counter_hunts`, the only bound that terminates), so a bad
                # destination does not cost a trek — it costs the boss. Different cost model,
                # different answer; re-flipping the global flag would silently re-litigate a
                # decision that was made on evidence.
                #
                # Fails CLOSED, like every other gate that decides where the bot walks: an
                # unreadable bag refuses the area rather than guessing we own the item.
                item_prereq = AREA_ITEM_PREREQ.get(map_enum)
                if item_prereq is not None:
                    try:
                        from modules.items import get_item_bag, get_item_by_name

                        if get_item_bag().quantity_of(get_item_by_name(item_prereq)) <= 0:
                            continue
                    except Exception:  # noqa: BLE001 - unreadable bag => refuse the area
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
                # Where a HUNT could actually stand (see the docstring): deliberately
                # computed here rather than by the caller, so no executor can forget to
                # ask and walk into an unswept endgame interior. Fails closed.
                # ‼ Computed BEFORE `tier` because huntability is now a RANKING term.
                try:
                    hunt_tile = hunt_ground_tile(map_enum)
                except Exception:
                    hunt_tile = None

                tier = (
                    (1_000_000_000.0 if reachable else 0.0)
                    # ‼‼ HUNTABILITY OUTRANKS TYPE COVERAGE (fixed 2026-08-07). It used to be
                    # absent from `tier` entirely, so a candidate the executor CANNOT ACT ON
                    # outranked one it can, purely for being the right type.
                    #
                    # Measured, and it silently cost Winona her only answer: her list sorted
                    # to 43 candidates led by **Geodude in MAGMA_HIDEOUT** (a type match, no
                    # spin tile, unhuntable) while the one genuinely huntable candidate —
                    # Slugma @ FIERY_PATH via Rock Throw — sat at **rank 42**. Callers use
                    # `max_results=5`, so `best_huntable` never saw it and the run reported
                    # "no huntable counter candidate".
                    #
                    # `huntable` is the executor's ONLY usable set (`huntable_candidates`,
                    # `best_huntable`), so ranking an unhuntable candidate above a huntable
                    # one cannot help any caller. Sits below `reachable` and above type
                    # coverage, keeping the docstring's order honest: get there at all >
                    # can we actually hunt it > how many needed types it answers.
                    + (100_000_000.0 if (reachable and hunt_tile is not None) else 0.0)
                    + len(hit_types) * 10_000_000.0
                    + (100_000.0 if tile is not None else 0.0)
                )
                # `score` keeps its published meaning (higher is better, full composite)
                # for display and for callers that read it.
                score = tier + rate * 1_000.0 - level_gap

                candidates.append(
                    {
                        "species_name": species.name,
                        "types": [t.name for t in species.types],
                        # WHY this species answers the boss. A silent "no" and a silent "yes"
                        # have both cost this project time; the log must be able to say which
                        # rule fired, and a move-answer must never be mistaken for a STAB one.
                        "answer_via": ("type" if hit_types
                                       else f"move:{move_answer[1].name}@L{move_answer[0]}"),
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


#: Mirrors `StoryMode.CREDIBLE_ANSWER_POWER` (story_mode.py). Kept as a literal rather than an
#: import because `counter_plan` must stay importable without the bot-mode plugin (the repros
#: rely on that). If the plugin's floor changes, change this with it.
_CREDIBLE_ANSWER_POWER = 75


def _loc_max_level(locations) -> int:
    """The highest wild level this species reaches anywhere, for the "does it already know the
    move when caught?" test. Uses the species' best location rather than the one being scored:
    the per-location check is applied by the caller's own level band, and being generous here
    only ever ADMITS a candidate that the credible-power and level-band gates still judge."""
    best = 0
    for loc in locations or ():
        try:
            best = max(best, int(loc.get("max_level", 0) or 0))
        except Exception:  # noqa: BLE001
            continue
    return best


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
