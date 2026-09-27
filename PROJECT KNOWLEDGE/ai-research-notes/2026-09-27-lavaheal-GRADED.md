# 2026-09-27 — `#26-healmap-lavaridge` F4 (the Flannery heal from below Lavaridge): GRADED

> Predictions: `2026-09-27-lavaheal-PREDICTIONS.md` (`8ceb4929`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-lavaheal-{G1-generic,F1-fix}.txt` + `.stdout.txt`.
> Fixture: `lavaridge.ss1` (unpinned; md5 `c7ef3ec4…` recorded before the drives). Driver: `--driver lavaheal`.

## RESULT — both arms as predicted

| # | Reading | G1 GENERIC (old behaviour) | F1 FIX |
|---|---|---|---|
| L0 | PREMISE: positioned, and the lead staged | ROUTE111 (4,70); Marshtomp 45/90 | identical |
| L1 | the heal raises | **yes**: `HealWalkFailedError: heal_in_pokemon_center: the walk to LavaridgeTown is BLOCKED … Source (28/28 @ ROUTE112) and destination (6/11 @ ROUTE112_CABLE_CAR_STATION) are not on connected maps`. This is the batch's 41-of-41 shape, word for word | **no** |
| L2 | maps entered | ROUTE111 → ROUTE112 → ROUTE112_CABLE_CAR_STATION → ROUTE112 (the bounce) | ROUTE111 → ROUTE112 → ROUTE112_CABLE_CAR_STATION → MT_CHIMNEY_CABLE_CAR_STATION → MT_CHIMNEY → **JAGGED_PASS** → ROUTE112 → LAVARIDGE_TOWN → **LAVARIDGE_TOWN_POKEMON_CENTER_1F** → LAVARIDGE_TOWN |
| L3 | end state | ROUTE112 (28,28); lead still 45/90 | LAVARIDGE_TOWN (9,7); **lead 90/90** |
| L4 | CONTINUE: `calculate_path` to LAVARIDGE_TOWN (5,16), `do_lavaridge_gym`'s first target | no path (from Route 112) | **yes** |
| | `ACCEPTANCE` | **PASS** (the bug reproduced) | **PASS** (the fix holds) |

Frames for the whole drive, positioning included: G1 2,060; F1 6,089.

## What this proves, and what it does not

- ⭐ **The Flannery heal no longer fails from below Lavaridge.** From exactly where run P1r7's heal walk began, the
  generic heal raises the batch's error, while `heal_at_lavaridge()` rides the cable car, descends Jagged Pass and
  ends healed in Lavaridge, ready for the gym walk. That is the recovery the derail used 53 times, now without
  spending a derail slot.
- The arms are the same trajectory up to the heal call: same fixture, same positioning, same staging.
- **Not shown:**
  - frequency (the next batch should show 0 `the walk to LavaridgeTown is BLOCKED` derails);
  - the Petalburg (53) and Fortree (8) BLOCKED families, which need their own segment-level fixes;
  - a whiteout on a Jagged Pass trainer mid-descent. `do_jagged_descent` already handles the Fallarbor respawn, but
    it was not driven here.
- One trajectory per arm, replayed; these are not samples.
