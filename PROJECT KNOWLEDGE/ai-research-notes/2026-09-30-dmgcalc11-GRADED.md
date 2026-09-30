# 2026-09-30 — design v2 step 11 (M1) GRADED: the damage audit is INERT and matches the table on every REACHED row; its acceptance is INSUFFICIENT by design, so the calculator is MEASURED, NOT yet CLEARED

⛔ **THE CAVEAT IS THE HEADLINE.** This grades the INSTRUMENT, not the calculator. Only 8 clean whitelisted hits were
seen, against a floor of 300. Every one lies inside the calculator's non-crit [min, max], and none is over
crit_max + 3. That is a sample of 8 and it proves nothing about step 12's KO-safety. The verdict on the calculator
needs step 14's batch with `POKEBOT_R25_DMGAUDIT=1` in both arms (the design's F5 and F8). **Step 12's stage 2 stays
OFF** (F8).

- **Predictions:** `2026-09-30-dmgcalc11-PREDICTIONS.md`, committed `c21ec8df` (5:45 AM, BEFORE any code). Its
  ADDENDUM (`82e34755`) was committed at 8:03:03 AM, AFTER the five arms and BEFORE the base A/B. Its text says
  "~8:05", an estimate written before the commit.
- **Build:** `c44b1def`.
- **Design:** `2026-09-30-dmgcalc11-DESIGN.md` (and its AS BUILT section).
- **Evidence** (`tools/story-dev/evidence/`):
  - `2026-09-30-dmgcalc11-M1B-GRADE.txt`: every grade, every run's line hash, the base A/B, the audits;
  - `2026-09-30-dmgcalc11-M1B-ON-r1-debug.txt`: the raw log, re-auditable. The audit re-run on the committed file
    reproduces ON-r1's audit byte for byte;
  - `2026-09-30-dmgcalc11-GATES.txt`, `-DIFF.txt`, `-SMOKE.txt` and `-ADVERSARIAL-{M1A,AUDIT}.txt`.

## THE RESULT, ARM BY ARM (each against its filed line)

| Arm | Filed | Result |
|---|---|---|
| G-M1a | every row's three literals; the bounds; mutants exact; under 300 s | ✅ PASS. Every literal and all four bucket bounds exact, 83 checks, ~72 s with a pool. ⚠ The no-pool fallback measured ~295 s. ⚠ Two departures from the filed mutant text (review F8): m2 also reddens B-STAGE-CRIT and B-CRIT-REFL, two rows added after filing (the filed text said every Group B row stays green); u7's set and the SW total were corrected after their first run (`-ADVERSARIAL-M1A.txt`). |
| G-AUDIT | every classifier and acceptance row; mutants exact | ✅ PASS. 177 rows and 193 mutants, each set exact on its first run. |
| M1b-OFF ×2 | the two match; 0 lines contain `DMGAUDIT` | ✅ PASS. 371 = 371 lines, 0 and 0. |
| M1b-ON ×2 | = a reproducing OFF on every non-`DMGAUDIT` line; the category rules | ✅ PASS. Both equal OFF on all 371 lines. 86 `DMGAUDIT` lines each, all `^f\d+ \[DMGAUDIT\] `; no `[BATTLE]` line carries one. |
| M1b-FAULT | self-check disagreements > 0 on the named turns, 0 in ON | ✅ PASS on the 2 REACHED named turns: f3190263 reads 16 vs 65, f3198642 reads 27 vs 64. ON has 0 disagreements. |
| M1b-DIFF / EXEC | identical behaviour flag unset; the same `get_battle_state()` count; the code runs | ✅ PASS, but on evidence the first version of this row did NOT cite (review F4). **Flag unset:** `-DIFF.txt` (a) and (b) show the ASTs equal the base once the hooks are removed, and 0 reads and 0 logs; that is equal or stronger than the filed form. **Flag set, the calculator branch:** `-DIFF.txt` (c) CANNOT reach it, because its reads return zeros, so `_prediction` returns `pred=none` before the calculator. Its "the sequence proves every hook body ran" was also wrong for that branch: a raising calculator is caught inside `_prediction` and logs an ordinary BEFORE with `pred=err:<Name>`. The branch is covered instead by gate rows PIN-b1 (a real `BattleState`; numeric `pred=` and `base=`; 0 `get_battle_state()` calls with it rebound in every module), NP-pred-exact and NH-gbs-count (`-GATES.txt`), and live by ON-r1's 22 numeric `pred=` BEFOREs (36 BEFOREs: 22 numeric, 4 `err:Absent`, 10 `none`; 0 `err:<Name>`). |
| M1b-AUDIT | raw count = parsed count in both ON; no cap marker | ✅ PASS. 86 = 86; cap marker absent; 0 `ERR`. |

**The literal grader's own tally is 57 of 70 (`-M1B-GRADE.txt` §4), and every claim below rests on its line-by-line
reading, NOT on that total.** Its 13 FAILs:
- 3 are the CTL literal (15 as filed, 14 seen; see NON-VACUITY);
- 10 are on the unreached Linoone branch or are unregistered:
  - the two Linoone rows, ×2 ON runs;
  - the third named clean turn and its self-check, ×2;
  - "no singles outside the 17", ×2.

## THE TRAJECTORY LEFT THE STEP-0 ONE, AND THE BUILD IS NOT WHY (the ADDENDUM's A/B)

- **Where the runs part:** all seven runs at this worktree share one trajectory: OFF ×2, ON ×2 and FAULT (the last
  three minus their `DMGAUDIT` lines), and BASE ×2 (the base code's two modules loaded in place of the build's).
  - Every one of the 371 frame-stamped lines is identical (sha256[:16] `928db5621b3d2f7c`). ⛔ That is ONE trajectory
    replayed seven times: a DETERMINISM check, not a replication.
  - The Step-0 run (5:27 AM, the wrapper probe at the base code) shares it to f3215340 (Route 119, (35, 90)). It then
    met a wild Linoone at (22, 127), at f3215905. Every build and base run walked on to Route 118 at f3215976.
- **The build did not move the trajectory.**
  - The PRIMARY proof is committed and static: `-DIFF.txt` (a) and (b). The ASTs equal the base once the hooks are
    removed, and with the flag unset every hook returns before any read or log.
  - H1's A/B corroborates it: BASE = OFF.
  - ⚠ The BASE and S0BASE runners were scratch scripts (review F5). Their source, and each run's loader lines ("…
    loaded from 241929d7" and "no dmgaudit module was imported"), are now embedded verbatim in `-M1B-GRADE.txt` §7.
  - Their guard could fire: the build's copies of both modules import `dmgaudit` at module top level. The committed
    successor is `run_with_base_modules.py`.
- **Nor did the Step-0 probe.** Its script (`m1_step0.py`, byte-identical to the copy embedded in `-STEP0.txt`) was
  re-run on the base code (scratch `run_step0_base.py`). It took the SAME no-Linoone trajectory as every other run:
  S0BASE-r1 = OFF-r1 on all 371 lines, and S0BASE-r2 likewise (the evidence file).
  - ⇒ The 5:27 AM divergence did NOT reproduce under the same code, probe and seed. It is a **second measured KI-112
    event**. The first was a Granite Cave warp one frame late, 1 of 3 runs, 2026-09-29. This one is a wild encounter on
    an OVERWORLD walk (Route 119), in 1 of 10 runs of this trajectory.
  - ⚠ **"1 of 10" is NOT a rate** (review F9). The divergent run is also the ONLY run made before 7:46 AM. The other
    nine ran back to back, 7:46 to 8:12 AM. A time-of-day or accumulated-state input fits this pattern as well as a
    random 1-in-10 event does.
  - Its cause is not identified. It goes to `#27-determinism` as evidence.
  - ⚠ **What it means for every pre-registration built from ONE live run:** a per-turn table derived from a single
    trajectory can lose its tail to KI-112.
  - Derive such a table from TWO identical runs SEPARATED IN TIME (or with an unrelated run between them), or state
    which rows lie past the first point where two runs could differ.
- **The filed rule, applied** ("the per-turn table is graded only on a reproducing trajectory"):
  - the 15 rows f3173282 … f3210218 are graded as filed;
  - the two Linoone rows (f3216950, f3217980) are NOT REACHED, and are not counted as PASS;
  - the two singles exits past the divergence were never pre-registered, and are reported, not graded:
    - f3230902: Poochyena, a miss, EXCLUDED `no-damage`;
    - f3231644: the KO, ACCEPTED, 117 in [110, 130].

## THE PER-TURN TABLE: 15 of 15 REACHED ROWS EXACT, 2 NOT REACHED

Every reached row matches its filed verdict, kind, wild or trainer, the foe's HP before and after, and Δ`gBideDmg[1]`
EXACTLY. 14 of the 15 also match their filed reasons; f3193320's reason changed, as recorded in AS BUILT (below). ON-r1
and ON-r2 give identical verdicts.

⚠ **This is NOT an independent test of the classifier (review F3).** Before the arms, the classifier had already been
aligned to this table twice:
- **Offline, by gate row T1.** It asserts every one of these verdicts on the Step-0 reads, with neutral stats and
  types, and predictions fitted to each observation.
- **Live, on the first 10 rows, by the smoke.** There, f3174185 was reversed (EXCLUDED `foe-profile-changed`) until the
  faint rule was added.

The trajectory to f3215340 is byte-identical to Step-0's. So the live 15 of 15 shows two things: that the production
READER reproduces the Step-0 values, and that the full live records (types, abilities, items, statuses, real
predictions) leave every verdict unchanged.

The rows:

- f3173282 excluded, `foe-self-hurt-move` (Self-Destruct).
- f3174185 accepted, KO 87 ∈ [77, 91].
- f3185457 and f3186160: not samples (`our-pp-unchanged`).
- f3186810 excluded, `no-damage` + `foe-held-item`.
- f3187609 excluded, `foe-held-item`.
- f3190263 accepted, 65 ∈ [64, 76].
- f3191078 excluded, `foe-item-action`.
- f3191967 accepted, trainer KO 69 ∈ [64, 76].
- f3193320 excluded (see below).
- f3197066 accepted, 97 ∈ [84, 99].
- f3198642 accepted, 64 ∈ [57, 68].
- f3199547 excluded, `foe-move-zero`.
- f3208167 accepted, 107 ∈ [106, 125].
- f3210218 accepted, 198 ∈ [170, 200].

**f3193320 (Marcel's Shiftry, Harden) is EXCLUDED `foe-after-unobservable`.** The table allowed either verdict, and
the reason change was recorded in the design's AS BUILT section BEFORE the arms (`c44b1def`, 7:46:21 AM; the first arm
started 7:46:41). The faint reset erases the Def-stage read the table's wording relied on.
- **The live BEFORE settles which branch applied:** our Mightyena was paralysed (status1 `0x40`). A quarter of its speed
  85 is 21, below Shiftry's 54, so Harden ran first. The table's own conditional ("else excluded") therefore predicts
  EXCLUDED.
- Its 142 against a crit maximum of 152 is the only probable crit in the run, and it sits in the excluded stratum.

## NON-VACUITY

- **✅ Passed:**
  - ≥ 1 accepted clean hit whose Δbide equals the foe's HP difference: f3190263 and f3198642. The third named one,
    f3216950, is NOT REACHED.
  - ≥ 1 accepted battle-end KO: 4 of them.
  - The doubles stratum in all three Route 123 doubles.
  - The foe-item-action stratum at f3191078.
  - The held-item stratum on Vanessa's Pikachu.
- **⚠ "A CTL line at each of the 15 battle starts" FAILS as filed: 14.** The literal counted the Step-0 trajectory.
  - Its battles after the 12 shared ones were the Linoone (the 13th), a Magma Hideout dex catch and the Team Magma
    grunt (opp 717).
  - The build's trajectory has the same dex catch (map 24,86; a different species) and the same grunt, but no Linoone.
    So its 14 is the Step-0 run's 15 minus the Linoone. (The first version of this note called the Linoone the 15th;
    review F2 corrected it.)
  - On this trajectory each of the 14 `[BATTLE] started` lines has its CTL at the same frame, in all three flagged runs.
- **⚠ A slip IN THE FILED PREDICTIONS, found while grading:** its parenthetical "the five doubles exits" was wrong
  when filed. Step-0's own table lists NINE doubles USE_MOVE exits (26 − 17). The build's trajectory has the same
  nine: 7 excluded `doubles`, f3157762 rejected `our-identity-changed`, and f3165221 not a sample.

## F8 AND THE ACCEPTANCE

- **8 accepted samples** (predicted 7 to 10; the AS BUILT count of "9" assumed the Linoone rows).
- **0 over crit_max + 3.** `max(obs/cmax)` is 0.495: every accepted hit is inside the non-crit [min, max], and none is
  below the non-crit min.
- **The port control** (the decomp-ordered port, replayed from each hit's live `base=`) puts all 8 inside the port's
  [non-crit min, crit max].
- **ACCEPTANCE: INSUFFICIENT** (8 of 300), as predicted; the audit exits 2.
- **The falsifiers:** none fired.
  - No ON line differs from OFF.
  - No `DMGAUDIT` line appears in OFF or under `[BATTLE]`.
  - No reached row's verdict is reversed.
  - FAULT is above ON.
  - No Group B or D literal failed.

## WHAT THIS DOES NOT SHOW

- The calculator's error at scale, or its crit side: 0 accepted crits were seen.
- Doubles: excluded by design; their Δbide includes the partner's hit.
- D1's exposure, which needs a STAB 4× crit.
- ⇒ `ACCEPT_MARGIN` stays a PROPOSAL for the user (F8).
- The `#27-dmgcalcfix` fixes remain unstarted, and the M1a gate's B-BURN, B-REFL and B-KI110-SPA rows are what its
  fixer must keep apart.

## THE REVIEW (2026-09-30; three fresh lenses; each blocker or should-fix finding went to a separate refuter)

Its output is a NOTE (`tools/story-dev/evidence/2026-09-30-dmgcalc11-REVIEW.txt`, verbatim). **No blocker. The production lens found no defect
in the recorder**, and no finding changes a graded result.
- **Production lens:** 2 nits, both fixed in the docs:
  - F1: the design's "no-BEFORE exits" list wrongly included the Safari Pokéblock `break`, and the prediction's object
    was misnamed.
  - F2: `-DIFF.txt` (c) never reaches the calculator (the same finding as grade F4 below).
  - It CHECKED AND FOUND TRUE:
    - every read is pure, and nothing can raise out of a hook;
    - the exit guard cannot fire inside selection or after an action;
    - a cross-battle AFTER is impossible;
    - the entry snapshot is not stale for the prediction's fields;
    - the per-turn log cost is ~1.2 KB against the 30 MB cap;
    - `custom-pokebot` and the mirror are untouched.
- **Audit lens (the classifier):**
  - Two should-fix defects, both confirmed by their refuters:
    - F1: the Marvel Scale stratum keyed on the wrong battler, so M1a's B-MS2 state (the foe's Marvel Scale, us
      statused) was ACCEPTED. Reachable only in Wallace's Milotic fight.
    - F3: a foe's CALLED move (Metronome, Mirror Move, Assist) bypassed every foe-move stratum, so its recoil entered
      Δbide. Reachable at the next gym: Winona's Swablu knows Mirror Move, and our main move is Take Down.
  - F2 (Secret Power is Tier A although its mountain secondary confuses) is confirmed but a nit: the bot never obtains
    TM43.
  - Six nits (F4-F9): the False Swipe clamp window; Flash Fire on a battle's last turn; a live ability that is not the
    species' (Trace); our burn changing; Skull Bash; Future Sight in the self-check; two sample-cost exclusions.
  - **All nine are FIXED in the classifier** (F9a only after its decomp claim was verified). The gate is now 191 rows
    and 220 mutants: each new row is red on the pre-review classifier, and each fix has a reverting mutant
    (`evidence/2026-09-30-dmgcalc11-REVIEW-GATE.txt`).
  - **Re-auditing the graded log after the fixes gives a BYTE-IDENTICAL report,** so no graded number moves. None of
    these cases occurs in the graded run.
- **Grade lens (this note):**
  - Confirmed should-fix:
    - F1: 01/03/04 still said "not graded" (a P1/P5 break);
    - F3: the 15 of 15 was not disclosed as a re-test of a table the classifier had been aligned to (T1, the smoke);
    - F4: the DIFF/EXEC evidence could not reach the calculator branch, and cited the wrong rows.
  - Downgraded to nits by their refuters:
    - F2: the Linoone was the 13th battle, not the 15th;
    - F5: the base runs' provenance;
    - F6: the 57 of 70 tally was never quoted.
  - Nits without a refuter: F7 (the Shiftry reason; the live read settles the branch), F8 (two M1a mutant-text
    departures), F9 ("1 of 10" is not a rate).
  - All are fixed in place above, each marked.
