# 2026-09-27 — RULING 20 Phase 1, increment B (box-first counters + the owed-only withdraw): GRADED

> Predictions: `2026-09-27-r20counterbox-PREDICTIONS.md` (`548af179`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-counterbox-{C1-boxfirst-fix,C2-boxfirst-nobox,C3-control-fix,C4-expired-fix,C5-expired-allcounters}.txt`
> + `.stdout.txt`. Fixture `fortree_gym_wedge.ss1` (PINNED, md5 `87d390d7…`, asserted). Driver `--driver counterbox`.

## RESULT — all five as predicted

The subject is production `StoryMode._counter_ladder` (Winona's key, `losses=8`, needed [Rock, Ice, Dragon]), followed
by production `heal_in_pokemon_center(FortreeCity)`. Recorded: planner entries, hunt calls (a stand-in that returns
None without travelling), and the withdraw and deposit ACTIONS, by PID. The created mons get random PIDs per run.

| Arm | Box | Planner / hunt | Ladder | Registered (badge) | Withdrawn | Deposited | Verdict |
|---|---|---|---|---|---|---|---|
| **C1** boxfirst / fix | Slugma (Rock Throw) | **not entered / not called** | True, "box-first Slugma L15 (Rock Throw scores 100)" | Slugma (5), owed | **Slugma** | **Skitty 5CCCD8BE** | **PASS** |
| **C2** boxfirst / `NOBOXCOUNTER` | Slugma | entered / `Slugma@FIERY_PATH` | False ("none found") | nothing | nothing | nothing | **PASS**: Slugma still boxed |
| **C3** control / fix | empty | entered / `Slugma@FIERY_PATH` | False | nothing | nothing | nothing | **PASS** |
| **C4** expired / fix | Machop (slot 0, registered at badge 4) + Slugma (slot 1) | not entered | True, box-first Slugma | Machop (4) + Slugma (5); owed: Slugma only | **Slugma** | Skitty | **PASS** |
| **C5** expired / `ALLCOUNTERS` | same | not entered | True, box-first Slugma | same | **Machop**, the expired counter | Skitty | **PASS**: recon hazard H1 reproduced on demand |

## What this proves, and what it does not

- ⭐ **Box-first is what spares the hunt.** C1 and C2 start from the same injected box; only the production arm differs.
  With the arm, the ladder runs the planner and calls the hunt, and it ends "none found" because the stand-in catches
  nothing. C3 shows C1's skip came from the boxed Slugma, not from the party.
- ⭐ **H1 was a real defect, and the owed-only source fixes it.** In C5 the heal collected the EXPIRED Machop (the first
  box-order match in the never-cleared registry) instead of the Slugma owed now, and it still read as a successful
  withdraw. C4 is the same state with the fix: Slugma.
- The make-room deposit is increment A's rule: Skitty (dead weight), never the owed counter.
- **Not shown:**
  - the ladder reached through `_prepare_for_fight` in a real losing streak (on this save the verdict is "not
    hopeless", because Castform has Powder Snow);
  - the withdrawn counter leading the NEXT attempt (recon H2: the lead is picked before the segment heal);
  - ⚠ recon **H3**: a box-first counter arrives at the level it was boxed at, and nothing trains it before the
    12-loss plateau, the same as today's box-catch path. A design question for later, not built here;
  - frequency. One trajectory per arm.
