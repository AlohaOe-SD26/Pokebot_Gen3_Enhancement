# 2026-09-26 — `#26-carleestage` — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> Pre-registration per the `story-drive` protocol. A reading that contradicts a prediction is a
> RESULT, not a driver failure. Graded in `…-carleestage-GRADED.md` after the drive.

## The claim under test

In 9 of the 39 badge-8 runs of the 2026-09-15 corpus, §Ch23 leg 4 (`cross_to_ever_grande`) died with
`UnreachableDestinationError: Could not reach (101, 26) on ROUTE128 … still at (101, 25)`.
**Hypothesis (PLAUSIBLE, from the decomp + one organic log):** the bot, approaching the channel
stage `CHANNEL_STAGE = (101,26)` from the north, is spotted at (101,25) by BOTH Harrison (patrols
x=101, y 19-25, sight 4) and Carlee (x=101, y 26-32, sight 4) — the organic log shows a DOUBLE battle
at (101,25) (`UseMoveAgainstRightSideOpponent`). Approaching trainers stop ADJACENT and are re-typed to
face-direction (`trainer_see.c`), so Carlee ends ON (101,26); the planner refuses a path to an
occupied tile, and `_navigate_riding_out`'s fail-fast ("the field is idle … retrying cannot change the
result") raises. ✅ Measured from the decomp layout: the water at y=25 is open x=97..105, so the bot
is NOT boxed in — only its exact target is occupied.

## The fix under test

Phase 2 of leg 4: if staging raises `UnreachableDestinationError` while the bot is on ROUTE128,
**adjacent** (Manhattan 1) to `CHANNEL_STAGE`, and a live object event stands ON `CHANNEL_STAGE`,
accept the current tile as the stage (recording which object and where), and continue to phase 3,
whose target (the waterfall base) is never an NPC tile. Anything else still raises. A skip-the-fix
fault arm `POKEBOT_CH23_FAULT_NOSTAGEFIX=1` disables the acceptance.

## The instrument

`--driver ch23stage` from `post_depart_sootopolis.ss1`: for each offset k in a range, reload the
fixture, idle `k*13` frames (to shift RNG and the two patrols), run PRODUCTION's
`cross_to_ever_grande` and stop once `R4-STAGE` is taken or the leg raises; log per k: outcome, end
tile, and every live object's `current_coords` + `local_id` on ROUTE128. `CH23STAGE_FULL=1` runs the
whole leg instead of stopping at the stage.

## Predictions

| # | prediction | falsifier |
|---|---|---|
| P1 | Under `NOSTAGEFIX=1`, at least one offset in 0..23 reproduces the organic signature: raise `Could not reach (101, 26)` with the bot at (101,25) and an object on (101,26). (Organic rate 9/39 ≈ 23 %; P(0 of 24) ≈ 0.2 % if the fixture's arrivals resemble organic ones.) | 0 of 24 reproduce ⇒ the fixture cannot reach the failing state; the fix is then UNPROVEN, not proven — fall back to an injected arm or a new fixture. |
| P2 | In every reproducing offset the occupant of (101,26) is Carlee (`local_id` of `Route128_EventScript_Carlee`, spawn (101,29)) and Harrison stands at (101,24). | the occupant is someone else, or the bot is not adjacent ⇒ the mechanism is not the one hypothesised; do not ship the adjacency rule as written. |
| P3 | With the fix (no fault arm), every reproducing offset takes `R4-STAGE` at (101,25) with `stage_occupied_by` recorded. | any reproducing offset still raises ⇒ the fix does not cover the real shape. |
| P4 | With `CH23STAGE_FULL=1` and the fix, the reproducing offsets complete leg 4: `ACCEPTANCE`-grade conjuncts — ended above the falls, on `VR_APRON (18,42)`, respawn armed to EVER_GRANDE, and a non-zero continuation path. | the bot stages but cannot continue (e.g. boxed later in the channel) ⇒ acceptance at the stage is a false fix; revert. |
| P5 | For offsets that do NOT reproduce, the fix arm and the fault arm are BIT-IDENTICAL up to the stage (same end tile, same frame count) — the fix is inert on the ordinary path. | any difference on a non-reproducing offset ⇒ the fix changed ordinary behaviour; investigate before shipping. |
| P6 | No offset shows a NEW failure mode under the fix that it does not show under the fault arm. | a new failure ⇒ the fix is harmful somewhere. |

⚠ Offsets replayed from ONE fixture are DIFFERENT trajectories (RNG differs per idle frame), but they
share one party and one approach; this measures the MECHANISM, not the organic frequency.
