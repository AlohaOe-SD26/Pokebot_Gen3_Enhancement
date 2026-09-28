# 2026-09-28 — `#27-r101standstill` GRADED: the Surf-learner hunt no longer spins on a tile that cannot roll an encounter

> Predictions: `2026-09-28-r101standstill-PREDICTIONS.md` (`5f401422`, before the fix). Fix: `b3e61560`. Driver:
> `--driver r101hunt` on `norman_done.ss1` (`e6fb7d5f36db`), `--set-balls 20`, `--frames 45000`. Evidence:
> `tools/story-dev/evidence/2026-09-28-r101hunt-*.txt`. Readings are what the code ACTED on: the `(map, tile)` passed to
> `_navigate_riding_out`, and the tile under the player when the spin starts.

## RESULTS — every graded reading matched its prediction

| Arm | Code | Ground passed to navigation | Spin tile | Battles in the spin | Exit |
|---|---|---|---|---|---|
| INDOOR (from Wally's house `(8,0)`) | unfixed | `ROUTE101 (9,9)` | `Normal`, no encounters | **0** in 15,000 frames | the bound |
| OUTDOOR (control) | unfixed | `ROUTE103 (5,7)` | `Tall Grass` | 5 | a learner caught (`slot 5`) |
| INDOOR | fixed | `ROUTE101 (12,10)` | `Tall Grass` | **13** in 15,000 frames | the bound (no Zigzagoon rolled; a frequency question, as predicted) |
| INDOOR + `POKEBOT_R101_FAULT_OLDTILE=1` | fixed | `ROUTE101 (9,9)` | (never spun) | 0 | **named raise on arrival**: "Cannot hunt a Surf learner on ROUTE101 (9, 9): the tile under the player (Normal at (9, 9)) cannot roll a wild land encounter …" |

Premise conjuncts TRUE in every arm: no Surf learner in the party, party room, and (INDOOR) the hunt starting in
`(8,0)`.

**WHAT IT PROVES.**
- The mechanism, end to end: from indoors the fallback picks the table's first row, and that row's tile could never
  roll an encounter.
- The outdoor control takes a real grass ground and catches.
- The fix moves the indoor hunt onto grass: 0 → 13 battles.
- The arrival assertion is live code: the fault arm raises by name instead of spinning to the watchdog.

## DEVIATION FROM THE PRE-REGISTRATION (disclosed)

The pre-registered spin bound was 20,000 frames. The first unfixed INDOOR run was killed by the harness's own
`HANG CONFIRMED (20000 frames no progress). Stopping.` before its bound closed, so it printed no verdict. Its no-progress
dumps still show the standstill: the stack `ensure_hm_learner → _story_spin → spin`, at (9,9). It is kept as
`…-unfixed-INDOOR-first-run-hangstop.txt`. The bound was lowered to 15,000 for EVERY graded arm. The graded run was then
repeated with the same code.

## ALSO FOUND

`_hm_hunting_grounds` was offering the Surf hunt `ROUTE118 (29,15)` and `ROUTE119 (21,109)`: OCEAN-WATER tiles, where
a land species can never appear. The gate's fault arm F2 shows it; the filter now drops them. Three `TRAINING_GRASS`
rows (Routes 115, 118, 119) sit on water although the table calls itself "land-only". Those rows are filed as
`#27-waterrows`.

## WHAT THIS DOES NOT SHOW

- A catch rate on Route 101. Zigzagoon is about 10% of its slots.
- The separate P4r1/P4r7 fast-fail (Route 104, provisioning and Woods routing), which is not this bug.
- That `_story_spin`'s own bail counts in the right units. The recon measured that it counts stop-condition CALLS, not
  frames. That is shared code and would need its own A/B.
