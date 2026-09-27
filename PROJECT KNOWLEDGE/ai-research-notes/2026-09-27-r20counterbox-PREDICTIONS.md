# 2026-09-27 — RULING 20 Phase 1, increment B (box-first counters + owed-only withdraw): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/r20phase1`. Recon: `2026-09-27-ruling20-incB-RECON.md` (a NOTE), site "counter".
> Gate green before the drive: `probe_r20_counterbox.py` (pure + wiring; built-in fault arms).

## THE CHANGE UNDER TEST

1. **Box-first in `StoryMode._counter_ladder`.** Right after the once-per-boss "started" mark, and before the planner
   and the ball check, the ladder asks `counter_hunt.box_counter_choice(needed, exclude_pids=<party PIDs>,
   taught=<gym-TM teaches>)`. On a pick it registers the PID exactly as a hunted counter (owed to the current badge
   count), records `box-first …` in `_counter_hunts`, and returns True; the segment's own heal collects it. Arm
   `POKEBOT_R20_FAULT_NOBOXCOUNTER=1` skips it.
2. **`box_counter_choice` (NEW; `box_counter_pid` is unchanged, since a parity gate pins it).** It accepts own-type
   matches, or a damaging move of a needed type scoring base power × 2 × STAB >= 75, ignoring gym-TM-taught pairs. It
   ranks by credible move, then score, then type, then level; not box order.
3. **The heal's counter withdraw collects only OWED counters** (`pc_trip.owed_counter_pids`, recon hazard H1). The
   registry is never cleared, so the full set could re-collect an expired counter that make-room boxed, and
   `find_in_box`'s box order could pick it over the one owed now. Arm `POKEBOT_R20_FAULT_ALLCOUNTERS=1` restores the
   full set. `deposit_protected_pids` now delegates to the same owed set; its arms are unchanged.

## THE DRIVE — `--driver counterbox`

- Fixture `fortree_gym_wedge.ss1` (PINNED, md5 `87d390d7…`, asserted): inside FORTREE_CITY_GYM, 5 badges, box empty.
  Party Mightyena, Sceptile, Swellow, Skitty, Zigzagoon, Castform (6/6).
- A direct call to production `_counter_ladder` on a production `StoryMode()`: Winona's key, `losses=8`,
  needed = [Rock, Ice, Dragon]. Then production `heal_in_pokemon_center(FortreeCity)`.
  - Why direct: through `_prepare_for_fight` the drive is vacuous on this save. Castform's Powder Snow makes the verdict
    "not hopeless", and inside the gym the Winona segment skips prep.
- The hunt is replaced by a recording stand-in that returns None without travelling. The planner
  (`find_counter_candidates`) is wrapped to record entry. Withdraw and deposit ACTIONS are recorded by PID.
- The expected make-room deposit is computed before the heal with increment A's rule. The recon measured it as
  **Skitty 5CCCD8BE** (dead weight).

## PREDICTIONS

| Case (`CB_CASE` / `CB_EXPECT`) | Injection | Predicted |
|---|---|---|
| **boxfirst / fix** | Slugma L15 (Rock Throw) in box slot 0 | planner NOT entered; hunt NOT called; ladder returns **True**; Slugma registered, badge 5, owed; `_counter_hunts` = "box-first Slugma L15 …"; the heal withdraws **Slugma** and deposits **Skitty**; Slugma in the party and gone from the box |
| **boxfirst / nobox** (`POKEBOT_R20_FAULT_NOBOXCOUNTER=1`) | same | planner entered; hunt stand-in called (Slugma @ FIERY_PATH per the recon); ladder returns **False**; nothing registered; **no withdraw**; Slugma still boxed |
| **control / fix** | none | as nobox, minus Slugma: planner entered, hunt called, ladder False, no withdraw. It shows boxfirst's skip came from the box, not from the party |
| **expired / fix** | Machop L15 in slot 0, registered as a counter at badge 4 (expired); Slugma in slot 1 | box-first picks Slugma (Machop answers nothing for Winona); the heal withdraws **Slugma**, NOT Machop; deposit Skitty |
| **expired / allcounters** (`POKEBOT_R20_FAULT_ALLCOUNTERS=1`) | same | the heal withdraws **Machop**, the first box-order match: the H1 defect, reproduced on demand |

**Premise conjuncts:** the fixture premise holds at runtime; `box_counter_choice` returns the injected Slugma before
the ladder runs (every case but control).

**Discriminators, computed before the run:** boxfirst vs control differ only by the injected Slugma; boxfirst/fix vs
nobox only by the production arm; expired/fix vs allcounters only by the production arm, and there the withdrawn PID
must differ (Slugma vs Machop).

## FALSIFIERS

- **boxfirst/fix enters the planner or calls the hunt:** box-first did not fire, or fired after the planner.
- **nobox behaves like fix:** the arm does not remove the block.
- **expired/fix withdraws Machop:** the withdraw source still reads the full registry.
- **allcounters withdraws Slugma:** the arm does not restore the old source, or box order is not what it is claimed to
  be; H1 is then unproven as a defect.
- Any deposit other than the predicted PID: a RESULT; read the failing line first.

## WHAT THIS DOES NOT SHOW

- The ladder reached through `_prepare_for_fight` in a real losing streak.
- The withdrawn counter leading the next attempt. The lead is picked before the segment heal (recon H2), so it leads
  from the attempt after.
- ⚠ **Recon H3 is NOT addressed:** a box-first counter arrives at whatever level it was boxed at. Nothing trains it
  until the 12-loss hard plateau, the same as today's box-catch path. That is a design question for later.
- Frequency. One trajectory per arm.
