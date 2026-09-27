# 2026-09-27 — `#26-healmap-lavaridge` F4 (the Flannery heal from below Lavaridge): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/lavaheal`. Mechanism: `ai-research-notes/2026-09-27-healwalk-RECON.md` (a NOTE).

## THE CHANGE UNDER TEST

`early_game.heal_at_lavaridge()` replaces the Flannery segment's
`heal_in_pokemon_center(PokemonCenter.LavaridgeTown)`.
- Outside `LAVARIDGE_MAPS` (the town and its 7 interiors, an explicit set) it runs `do_jagged_descent()`: the
  cable car up, then down Jagged Pass, ending healed at the Lavaridge Poké Center. That is the route the derail
  recovery took 53 times in the batch.
- Inside Lavaridge it is the plain heal.
- Arm `POKEBOT_LAVAHEAL_FAULT_GENERIC=1` always takes the generic heal (the old behaviour).

## THE DRIVE — `--driver lavaheal`

1. Fixture: `lavaridge.ss1`. Loaded before this file was written: LAVARIDGE_TOWN (9,7), badges 1-3,
   `lastHealLocation` Lavaridge. It is unpinned; md5 `c7ef3ec488b425833247c5ed6da3f7fb`, recorded before the drives.
2. Position the bot, using production `_navigate_riding_out`, on ROUTE111 (4,70). That is where run P1r7's heal walk
   began after its training top-up was abandoned.
3. Stage (test-only): the lead's current HP to 50%, so a heal is observable.
4. Run `heal_at_lavaridge()`, bounded to 60,000 frames, recording every map it enters.

## PREDICTIONS

| # | Reading | FIX (default) | GENERIC arm (old behaviour) |
|---|---|---|---|
| L0 | PREMISE: positioned on ROUTE111 before the heal; the lead is below full HP | yes | yes |
| L1 | the heal raises | **no** | **yes**: `HealWalkFailedError` "… LavaridgeTown is BLOCKED …", naming `ROUTE112_CABLE_CAR_STATION` (the batch's 41-of-41 shape) |
| L2 | maps entered include the cable car station AND JAGGED_PASS | **yes** (the ride, then the descent) | the station only (the bounce) |
| L3 | ends in `LAVARIDGE_MAPS` with the lead at full HP | **yes** | **no** (ends on ROUTE112, near (28,28)) |
| L4 | CONTINUE: `calculate_path` from the end tile reaches LAVARIDGE_TOWN (5,16), the first tile `do_lavaridge_gym` walks to | **yes** | (not graded) |

⇒ The driver prints `ACCEPTANCE: PASS` when L0 holds and L1–L4 match the arm's column.

## FALSIFIERS, stated in advance

- **L0 false:** the drive is VACUOUS. The fixture could not be walked to Route 111, or the staging did not land.
  Re-plan; this is not a refutation.
- **The GENERIC arm does NOT raise from ROUTE111 (4,70)** (L1 no): the batch's failure does not reproduce from this
  start. The fix would then be unproven as the cause, whatever the FIX arm does.
- **The FIX arm raises, or ends outside Lavaridge:** `do_jagged_descent` from Route 111 is not the working recovery
  the batch showed. The fix is wrong.
- **A whiteout** during the ride or descent (Jagged Pass trainers) FAILS the run. It is latched, and the verdict still
  prints.

## WHAT THIS DOES NOT SHOW

- Frequency.
- The other two BLOCKED families: Petalburg (53) and Fortree (8). They need their own segment-level fixes.
- One trajectory per arm, replayed; not samples.
