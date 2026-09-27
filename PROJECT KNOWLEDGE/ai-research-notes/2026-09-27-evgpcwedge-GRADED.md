# 2026-09-27 — `#27-evgpcwedge` / KI-106: GRADED

> Predictions: `2026-09-27-evgpcwedge-PREDICTIONS.md` (`159094e4`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-evgp-{K1-keepheld,F1-fix}.txt` + `.stdout.txt`.
> Fixture: `post_training.ss1` (PINNED, md5 `2f517f1f790b…`, asserted before the drives).
> Driver: `--driver evgpcwedge`.

## RESULT — both arms as predicted

| # | Reading | K1 KEEPHELD (old behaviour) | F1 FIX |
|---|---|---|---|
| P0 | staging fired | yes — f4236795 at VR1F (2,23), just after Wally; Zigzagoon L19 kept at 1 HP, the rest 0 | identical |
| P1 | whiteout, then the first overworld map | f4239283 → EVER_GRANDE_CITY (0,8) at (27,49) | identical |
| P2 | **PREMISE** — the recovery-start mask | `RECOVERY-HELD: KEPT (fault arm) leaked held inputs 0x0042 at the start of whiteout recovery` (f4239589) | `RECOVERY-HELD: released leaked held inputs 0x0042 at the start of whiteout recovery` (f4239589) |
| P3 | (informational) the south Poké Center (16,12) loaded | **yes** — at (7,8), f4239691: the held Up walked the respawn through the door | no |
| P4 | `could not face` derails | **1 of 1** — `DERAIL #1: Ch23 (Victory Road) failed after 3 attempts. attempt 1: UnreachableDestinationError: Could not reach (9, 15) on MapRSE.VICTORY_ROAD_1F: … still at (7, 4) … (ensure_facing_direction: could not face Down after 1801 pressing …` — the batch P1r8's derail #1, word for word. Then the harness printed `HANG CONFIRMED (20000 frames no progress)` | **0** |
| P5 | **CONTINUE** — VICTORY_ROAD_1F reloaded after the whiteout | no | **yes** — (15,40) at f4239931, 519 frames after the respawn |
| | `ACCEPTANCE` | **PASS** (the bug reproduced) | **PASS** (the fix holds) |

**0x0042 is B + Up**, the exact mask the batch's 25 wedge dumps showed.

## What this proves, and what it does not

- ⭐ **The mechanism, end to end, in production code.** A trainer battle interrupted a `_sampling`-wrapped leg-5 walk
  north, and the party whited out.
  - The mask on the whiteout screen read `0x0000`: the listener's release DID run.
  - Yet the mask at the start of the story's recovery was `0x0042`, so the buttons were re-held after that release.
  - Held Up then walks the respawn into the Poké Center, and Up-before-Down input priority defeats every turn south.
- ⭐ **The fix is load-bearing, and on its own it is sufficient on this path.** The arms are the same trajectory up to
  f4239589, the release point: same staging frame, same whiteout frame, same mask. They diverge ONLY at the release.
  - `_sampling`'s own missing `finally` was deliberately left alone, and F1 shows it is not needed once the recovery seam
    releases.
  - ⛔ The claim "`_sampling` needs a `finally` too" was NOT tested, and is NOT made.
- **Not shown:**
  - Which of the two re-hold routes (the `isolate_inputs` restore, or the navigator's next frame) re-held B+Up. The fix
    clears both at the same seam.
  - Frequency. The batch had n = 1. The next batch should show 0 `could not face` derails and 0 unrequested south-PC
    entries.
- One trajectory, replayed per arm. These are not two samples.

## Side observations (not graded)

- The staged loss was to **Cooltrainer Hope's Roselia L45**, a trainer, as in the batch. The park report called it
  "wild", and the KI-106 recon corrected that.
- F1: the bot's first act after the respawn was to walk back to Victory Road, where it met and tried to catch a wild
  Lairon (a dex catch). That is ordinary.
