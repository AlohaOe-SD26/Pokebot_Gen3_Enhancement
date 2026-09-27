# 2026-09-27 — RULING 20 Phase 1, increment B (Strength box-first): GRADED

> Predictions: `2026-09-27-r20strengthbox-PREDICTIONS.md` (`8edcedb2`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-strengthbox-{S1-teach-fix,S2-teach-nopref,S3-teach-skipfix,S4-knower-fix,S5-party-fix,S6-sitetwo-fix}.txt`
> + `.stdout.txt`. Fixture `strength_boxfirst_mauville.ss1` (PINNED, md5 `ba23ca04…`, asserted). Driver `--driver strengthbox`.

## RESULT — all six arms as predicted

Graded on the recorded ACTIONS by PID: `_withdraw_hm_learner` calls, `teach_hm_move` calls and
`PCAction.deposit_pokemon_to_box`. The expected deposit was computed before each run with increment A's
`make_room_victim`. The created Swampert gets a new random PID per run, which the driver reads back.

| Arm | Box order (avoid=HM07) | Withdrawn | Taught | Deposited | Other learner | Verdict |
|---|---|---|---|---|---|---|
| **S1** teach / fix | Sceptile, Swampert | **Sceptile 863B0917** | Sceptile (lost Slam; kept Rock Smash) | **Skitty 5CCCD8BE** | Swampert still boxed | **PASS** |
| **S2** teach / `NOLANDPREF` | Sceptile, Swampert | **Swampert** (level order) | Swampert (lost Mud Sport) | Skitty | Sceptile still boxed | **PASS** |
| **S3** teach / `skipfix` | Sceptile, Swampert | nothing | nothing | nothing | both still boxed | **PASS**: the refusal names `['863B0917', <Swampert>]`; no trip |
| **S4** knower / fix | Mightyena, Sceptile | **Mightyena 5C96EA9B** (knows Strength) | **nothing** ("already knows Strength - no teach") | nothing (party 4 → 5) | Sceptile still boxed | **PASS** |
| **S5** party / fix (the ordinary case) | Swampert | **nothing** (`land_hm_learner_slot` = 0, Sceptile in the party) | Sceptile 863B0917 (lost Slam) | nothing | Swampert still boxed; no trip | **PASS** |
| **S6** sitetwo (no centres) | Sceptile, Swampert | nothing | nothing | nothing | both still boxed; no trip | **PASS**: the refusal names both and adds "(no Poké Centre offered here, so not withdrawn)" |

S1 and S2 end at MAUVILLE_CITY (22,6), outside the centre, with four non-adjacent exits reachable ((8,5), (35,5),
(23,14), (32,14)).

## What this proves, and what it does not

- ⭐ **The box-first block is what collects the learner.** S1 and S3 start from the same injected state. With the block
  disarmed (S3) the function refuses and nothing moves; with it (S1) the boxed learner is withdrawn and taught through
  production `heal_in_pokemon_center`.
- ⭐ **The HM07 preference is what picks Sceptile.** S1 vs S2: the same state, and only the arm differs. Without it, the
  higher-level Swampert, the mon that would later carry Waterfall, is withdrawn and spends a slot on Strength.
- The make-room deposit on a full party is increment A's rule (Skitty, the dead weight), never the only Surf carrier.
- **Not shown:**
  - the heal loop end to end from `post_mtpyre.ss1` (the Lilycove stop, then Mauville). The driver calls the
    production function with the centre that loop passes;
  - the in-hideout caller live. S6 calls the same function with no centres, which is what that caller does;
  - frequency. One trajectory per arm.

## Harness incident during this round (not a result)

A first set of runs was abandoned. Stopping the background runner did not stop its `bash` loop, so a second runner
duplicated the arms, and two processes wrote the same S2 log. Both runner shells and their harness processes were
killed; the batch's own processes were checked by start time and left alone. S2–S6 were then re-run by one runner.
S1's log came from one process only and was kept. See `08-MISTAKES.md` (2026-09-27, the runner entry).

A second harness artefact: after each verdict the driver hands off to Manual, and the harness's own
`ManualBotMode` stub lacked the `on_pokenav_call` hook that production's `BotMode` provides. A Match Call on the
restored fixture then raised AttributeError every frame. The S4 and S6 evidence files were TRUNCATED ten lines
after the first such exception (a marker line says how many lines were cut). Every verdict line is before the cut.
The stub now has the hook (`story_harness.py`).
