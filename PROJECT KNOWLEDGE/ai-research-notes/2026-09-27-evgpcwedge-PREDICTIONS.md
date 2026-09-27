# 2026-09-27 — `#27-evgpcwedge` / KI-106: PRE-REGISTERED PREDICTIONS (filed BEFORE any drive)

> Branch `wt/evgpcwedge`. Recon, a NOTE: four read-only Claude agents (our code, batch logs, decomp, an adversarial
> refuter). The mechanism below is what they converged on; this file is what a drive must confirm or refute.

## THE MECHANISM UNDER TEST (from the recon, not yet driven)

1. A battle interrupts a `_sampling`-wrapped §Ch23 walk north. The walk is holding B+Up.
2. The party whites out. The whiteout listener releases held buttons (`_listeners.py:544`).
3. Held buttons come back afterwards, by one of two routes:
   - `isolate_inputs` restores the interrupted handler's saved mask;
   - or the navigator's next frame re-holds B+Up.
4. `_sampling` raises the abort with no `finally`, so nothing releases the buttons.
5. The story's run-loop recovery never clears held buttons.
6. Held Up walks the respawn tile, Ever Grande (27,49), through the Poké Center door to (7,4).
7. Emerald reads a held Up before Down (`field_control_avatar.c`), so every `ensure_facing_direction(Down)` fails.

**Draw is NOT the cause.** The batch's two other Draws recovered normally, and the game routes a DREW outcome exactly
like LOST.

## THE FIX

At the top of `StoryMode.run()`'s `except BotModeError` handler, the entry point of BOTH the whiteout recovery and the
derail recovery, the story now calls `context.emulator.reset_held_buttons()`. When the mask it released is non-zero, it
logs `RECOVERY-HELD: released leaked held inputs 0x…`.

Arm `POKEBOT_RECOVERY_FAULT_KEEPHELD=1` skips the release, and still logs the mask as `KEPT (fault arm)`. So both arms
record the same PREMISE reading.

## THE DRIVE — `--driver evgpcwedge`

- The production `StoryMode`, i.e. `storyresume` plus a per-frame hook, from the PINNED `post_training.ss1`.
- That fixture sits at VR1F (15,39), with Wally NOT beaten and `lastHealLocation` = EVER_GRANDE_CITY (0,8) at (27,49).
  This was read from SaveBlock1 +0x1C before this file was written.
- **Staging (test-only):** once `DEFEATED_WALLY_VICTORY_ROAD` is set and the player has stood controllable on VR1F for
  30 frames, the hook writes the party's current HP (data[86:88]):
  - every member except the lowest-level one → 0;
  - the lowest-level one → 1.
  This forces a loss on the rest of leg 5's walk north toward (9,15).
- **Why that is faithful to the batch:** the batch's P1r8 met Cooltrainer Hope at (2,15) on exactly this walk; 16 run
  logs show `vs Roselia L45` there. Everything downstream of the staging is unmodified production.

## PREDICTIONS

| # | Reading | KEEPHELD (the old behaviour) | FIX |
|---|---|---|---|
| P0 | the staging fired | yes | yes |
| P1 | a whiteout AFTER the staging, and the first overworld map after it is EVER_GRANDE_CITY (0,8) | yes | yes |
| P2 | **PREMISE:** a `RECOVERY-HELD` event at the start of the WHITEOUT recovery whose mask includes Up (0x0040) | yes, `KEPT (fault arm)` | yes, `released` |
| P3 | INFORMATIONAL, NOT GRADED: map (16,12), the south Poké Center, loads after the whiteout | expected yes; the player walks to (7,4) | either. The story may enter to heal ON PURPOSE (the batch's other 746 post-whiteout Centre visits ran the nurse script), and that is not the wedge |
| P4 | derails whose text contains `could not face` | **≥ 1**; the run then derails on repeat | **0** |
| P5 | **CONTINUE:** VICTORY_ROAD_1F (24,43) loads again after the whiteout; that is what §Ch23's re-fired leg 5 walks to | **no** (within the budget) | **yes** |

⇒ The driver prints `ACCEPTANCE: PASS` when P0–P2 hold and P4–P5 match the arm's column. P3 is logged but not graded.

## FALSIFIERS, stated in advance

- **P2 false in BOTH arms** (no leaked mask, or no Up bit at the recovery start): the drive is VACUOUS for this fix.
  The leak did not reproduce on this path. That is a NON-RESULT, not a refutation. Re-plan: stage the whiteout
  differently, or instrument `isolate_inputs`.
- **P2 true but KEEPHELD does not wedge** (P4 = 0): Up at the recovery start is NOT sufficient. Some later step
  clears it, and the batch's wedge needs another ingredient. ⇒ the fix is unproven as the cause.
- **FIX still wedges** (P4 ≥ 1): the release at the recovery seam is too early or in the wrong place. A later
  re-hold, e.g. a still-suspended listener restoring its mask after the story's handler runs, survives it. ⇒ the fix
  is wrong.
- **The whiteout does not land at Ever Grande:** the premise is broken, and the readings say nothing about KI-106.

## WHAT THIS DRIVE DOES NOT SHOW

- Frequency. The batch had n = 1.
- Which of the two re-hold routes put B+Up back. The fix clears both at the same seam. The refuter's `isolate_inputs`
  logging is the discriminator for that, and it is not needed to prove this fix.
