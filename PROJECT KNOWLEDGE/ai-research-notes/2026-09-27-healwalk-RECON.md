# 2026-09-27 — the heal-walk "BLOCKED" derails (`#26-healmap-lavaridge`, Petalburg, Fortree): RECON (a NOTE, not truth)

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** Four read-only Claude agents took four angles: our code, batch
> forensics, the warp graph and decomp, and an adversarial agent. Nothing was driven. Every BFS figure is a decomp
> simulation. It refines `2026-09-26-batch0926-FORENSICS.md`'s mechanism and corrects two of its counts.

## THE COUNT (batch `#26-batch0926`, 38 runs)

**115 heal-walk BLOCKED derails**, every one naming the boss's own town:

| Town | Derails | Bounce shape | Other |
|---|---|---|---|
| Petalburg | 53 | 52 through Rustboro Flat1, 1 through Meteor Falls | – |
| Lavaridge | 54 | 41 through the cable car station, 8 through the Mauville Poké Center | 5 `Cannot reach LAVARIDGE_TOWN` |
| Fortree | 8 | 1 through the Glass Workshop | 6 stuck at the sealed Desert Ruins door, ROUTE111 (29,88); 1 `Cannot reach` |

- **At least 109 of the 115 come from the hardcoded heal in a gym segment.** Each follows `Story: lead vs Fire`,
  `Normal` or `Flying`. The calls are the Flannery heal (`story_mode.py`, LavaridgeTown), the Norman heal
  (PetalburgCity) and the Winona heal (FortreeCity).
- **53 of the 54 Lavaridge derails RECOVERED**: the derail re-runs the chapter, which rides the cable car and walks
  down Jagged Pass (`do_jagged_descent`), median about 2,840 frames. The 54th ended run P1r7.

## THE MECHANISM, in two layers

1. **The bounce.** This is SUPPORTED by all four angles. It is the old note's account, with corrections:
   - `_staged_progress_warp` accepts a candidate at the SAME graph distance, i.e. a lateral move. It then breaks
     ties on the building's raw warp count, so it walks into a zero-progress building: Flat1, the Mauville Poké
     Center, or the cable car station.
   - Inside, the planned exit is the mat the bot is standing on. That mat is an `MB_SOUTH_ARROW_WARP` (read from the
     decomp).
   - The step-off loop presses Down, which fires the exit, so the leg SUCCEEDED.
   - The code then re-navigates to the inside mat from outside without re-checking the map. That produces "not on
     connected maps", which the heal code classifies as BLOCKED.
   - **In short: a successful exit is read as a failure.**
2. **The real cause, for Lavaridge: no route exists for the generic navigator.** This is SUPPORTED by the decomp tile
   BFS and by the adversarial angle.
   - Before Flannery, Route 112 is split by one-way ledges. Lavaridge is reachable from below ONLY by the scripted
     cable car plus the one-way Jagged Pass descent.
   - The warp graph counts Route 112 → Lavaridge as one hop.
   - ⇒ **Fixing the bounce alone only changes the message.** The bot would stand on Route 112 and raise
     `Cannot reach LAVARIDGE_TOWN`, which the 5 variant-B events already show.

## WHY THE BOT KEEPS STARTING THE HEAL WALK FROM THE WRONG SIDE (the P1r7 loop)

- **The training top-up (MAINTAIN) before Flannery picks ROUTE111 (25,55).** That spot is Go-Goggles-gated before
  Flannery (decomp BFS), and it was abandoned 45 of 48 times in the batch.
- **The "drop this ground" memory never matched.** It was written under the map where the walk DIED (Route 111) and
  read from the map the next pick happens on (Lavaridge). P1r7 re-walked that ground 19 times.
- **Each cycle then ran the Flannery heal from Route 111, and derailed.** Five cycles with no EXP change ended the run:
  about (5/6)^5 ≈ 0.40 from each reset, by the code's own arithmetic.
- ✅ **FIXED 2026-09-27** (`probe_trainblock_origin.py`). The memory is now written under BOTH the death map and the
  map the ground was chosen from.

## FIX OPTIONS THE CODE ANGLE LISTED, and their risks

| # | Fix | Effect | Risk |
|---|---|---|---|
| F1 | Stop the false failure after the step-off | Relabels the 103 bounces; does not remove them | A shared path: every `navigate_to_anywhere` user |
| F1b | Deprioritise re-taking the warp just arrived on | Needed with F1 for the Woods | A shared path; the Rusturf ping-pong trap lives here |
| F2 | Exclude dead-end buildings in `_staged_progress_warp` | Saves frames, not derail slots | Candidate churn. ⚠ The naive "all exits go back to the same map" test is wrong both ways: it bans Petalburg Woods and Fiery Path, and misses Flat1 (stairs). The correct test is a closure test with arrival-tile clusters |
| F3 | Model split maps in the warp graph | Helps Petalburg only | The largest regression surface; still cannot express the cable car |
| **F4** | **At the segment: if not in Lavaridge, run `do_jagged_descent()` (which heals) instead of the generic heal** | **Removes the 54 Lavaridge derails without spending a derail slot. It IS the recovery that works 53 of 54 times** | Local. `do_jagged_descent` returns without healing when already in Lavaridge, so the caller must still heal then |
| F5 | Fix the blacklist key | Ends the P1r7-style loop | ✅ DONE (both keys) |

## FIXTURE PLAN (from the log angle)

- **Lavaridge (cable car):** from `lavaridge.ss1`, which is pre-Flannery (badges 1-3, verified by loading it,
  unpinned). Walk out through Route 112 into Route 111 (13,61), then call
  `heal_in_pokemon_center(PokemonCenter.LavaridgeTown)`. Every start tile tried gives the same error.
- **Petalburg:** from ROUTE116 (11,7), call `heal_in_pokemon_center(PokemonCenter.PetalburgCity)`.
  - Control: the Rustboro heal from the same tile succeeds; it did 11 of 11 in the batch.
  - No pinned save stands on Route 116.
- **Fortree (Desert Ruins):** from `flannery_done.ss1`, stand on FIERY_PATH (18,19). `Route111_OnLoad` seals
  (29,87) unless `FLAG_REGI_DOORS_OPENED` is set (read from the decomp).

## SIDE FINDINGS

- The comment in `training_areas.py` that calls ROUTE111 (25,55) "reachable from Fallarbor" is contradicted by the
  decomp BFS, once the sandstorm triggers are modelled as walls.
- `HUNTING_GROUNDS[FIERY_PATH]` says the hunt "never walks" the heal leg back to Lavaridge, but the Flannery and
  Winona segments do exactly that.
- The two dead heal-map keys (`_training_area_heal_map`'s ROUTE112 and FIERY_PATH rows) are confirmed dead, with 5
  consumers rather than 3.
