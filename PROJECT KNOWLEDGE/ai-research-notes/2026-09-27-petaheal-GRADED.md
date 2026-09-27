# 2026-09-27 — `#26-healmap-lavaridge` (Petalburg family): the Norman heal from the Rustboro side — GRADED

> Predictions: `2026-09-27-petaheal-PREDICTIONS.md` (`360e4cc7`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-petaheal-{G1-generic,F1-fix,G1b-generic,F1b-fix}.txt` + `.stdout.txt`.
> Fixture: `norman_done.ss1` (PINNED, md5 `e6fb7d5f…`, asserted before the drives). Driver: `--driver petaheal`.

## THE FIRST PAIR (G1/F1): both SUBJECTS as predicted, both GRADES failed on a DRIVER bug

- **The bug.** The driver staged slot 0 to "50% HP". Slot 0 was a **Shedinja, whose max HP is 1**, so it stayed at 1/1:
  the premise `lead_staged_below_full` was False, and "healed" was unobservable.
- **Every subject reading matched its prediction:**
  - G1 raised the batch's Flat1 error;
  - F1 logged the fallback, took the Woods road and ended in Petalburg.
- **The fix.** Stage the first live mon with at least 2 max HP, then re-run.

## THE RE-RUN (G1b/F1b) — both arms as predicted

| # | Reading | G1b GENERIC (old behaviour) | F1b FIX |
|---|---|---|---|
| P0 | PREMISE: healed in Petalburg, positioned, staged | yes; ROUTE116 (11,7); Blaziken 55/110 | identical |
| P1 | the heal raises | **yes**: `HealWalkFailedError: … the walk to PetalburgCity is BLOCKED … Source (13/31 @ RUSTBORO_CITY) and destination (6/7 @ RUSTBORO_CITY_FLAT1_1F) are not on connected maps`. The batch's 52-event shape | **no** |
| P2 | (logged) the bounce through Flat1 | yes | yes: the generic attempt runs first, as designed |
| P3 | a `PETAHEAL:` event (the fallback ACTED) | **none** | **`PETAHEAL: generic heal failed from map (0, 3); held 0x0000 released; taking the road — HealWalkFailedError`** |
| P4 | PETALBURG_WOODS entered | no | **yes**: ROUTE116 → RUSTBORO_CITY → FLAT1 → RUSTBORO_CITY → ROUTE104 → PETALBURG_WOODS → ROUTE104 → PETALBURG_CITY → PETALBURG_CITY_POKEMON_CENTER_1F → PETALBURG_CITY |
| P5 | end state | RUSTBORO_CITY (13,31); Blaziken 55/110 | PETALBURG_CITY (20,17); **Blaziken 110/110** |
| P6 | CONTINUE: `calculate_path` to the gym door (15,8) | — | **yes** |
| | `ACCEPTANCE` | **PASS** | **PASS** |

- **Frames per drive** (whole drive, including the heal-first and the walk to Route 116): G1b 8,754 and F1b 12,647.
  These are identical to G1/F1: the staging is a memory write and does not change the trajectory.
- **The released mask was 0x0000 here.** The raise left no held input on this path. The release guards the case where
  it does; the gate's fault arm pins it.

## What this proves, and what it does not

- ⭐ **From Route 116, where 40 of the batch's 53 Norman heals began, the fallback reaches Petalburg healed** instead of
  derailing. The common case is unchanged, because the generic heal is tried first and only its failure is caught.
- **Not shown:**
  - frequency;
  - the Route 117 origin (9 of 53), which reaches Rustboro through Verdanturf and Rusturf. The road's own ranking
    covers it, but it was not driven;
  - ⚠ the 1 Meteor Falls bounce (from Route 114). METEOR_FALLS is not in `PETALBURG_ROAD_MAPS`, so the fallback
    re-raises there exactly as before: still a derail, NOT fixed;
  - the Fortree family (8).
- One trajectory per arm, replayed.
