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
| G-M1a | every row's three literals; the bounds; mutants exact; under 300 s | ✅ PASS. Every literal and all four bucket bounds exact, 83 checks, ~72 s with a pool. ⚠ The no-pool fallback measured ~295 s. |
| G-AUDIT | every classifier and acceptance row; mutants exact | ✅ PASS. 177 rows and 193 mutants, each set exact on its first run. |
| M1b-OFF ×2 | the two match; 0 lines contain `DMGAUDIT` | ✅ PASS. 371 = 371 lines, 0 and 0. |
| M1b-ON ×2 | = a reproducing OFF on every non-`DMGAUDIT` line; the category rules | ✅ PASS. Both equal OFF on all 371 lines. 86 `DMGAUDIT` lines each, all `^f\d+ \[DMGAUDIT\] `; no `[BATTLE]` line carries one. |
| M1b-FAULT | self-check disagreements > 0 on the named turns, 0 in ON | ✅ PASS on the 2 REACHED named turns: f3190263 reads 16 vs 65, f3198642 reads 27 vs 64. ON has 0 disagreements. |
| M1b-DIFF / EXEC | identical behaviour flag unset; the same `get_battle_state()` count; the code runs | ✅ PASS, in the AS BUILT form, which is equal or stronger (`-DIFF.txt`): the ASTs equal the base once the hooks are removed; flag unset, 0 reads and 0 logs; flag set, 0 `get_battle_state()` calls; the exact CTL/BEFORE/AFTER sequence. |
| M1b-AUDIT | raw count = parsed count in both ON; no cap marker | ✅ PASS. 86 = 86; cap marker absent; 0 `ERR`. |

## THE TRAJECTORY LEFT THE STEP-0 ONE, AND THE BUILD IS NOT WHY (the ADDENDUM's A/B)

- **Where the runs part:** all seven runs at this worktree share one trajectory: OFF ×2, ON ×2 and FAULT (the last
  three minus their `DMGAUDIT` lines), and BASE ×2 (the base code's two modules loaded in place of the build's).
  - Every one of the 371 frame-stamped lines is identical (sha256[:16] `928db5621b3d2f7c`). ⛔ That is ONE trajectory
    replayed seven times: a DETERMINISM check, not a replication.
  - The Step-0 run (5:27 AM, the wrapper probe at the base code) shares it to f3215340 (Route 119, (35, 90)). It then
    met a wild Linoone at (22, 127), at f3215905. Every build and base run walked on to Route 118 at f3215976.
- **H1 holds: BASE = OFF,** so the build did not move the trajectory.
- **Nor did the Step-0 probe.** Its script (`m1_step0.py`, unchanged) was re-run on the base code (scratch
  `run_step0_base.py`). It took the SAME no-Linoone trajectory as every other run: S0BASE-r1 = OFF-r1 on all 371
  lines, and S0BASE-r2 likewise (the evidence file).
  - ⇒ The 5:27 AM divergence did NOT reproduce under the same code, probe and seed. It is a **second measured KI-112
    event**. The first was a Granite Cave warp one frame late, 1 of 3 runs, 2026-09-29. This one is a wild encounter on
    an OVERWORLD walk (Route 119), 1 of 10 runs of this trajectory.
  - Its cause is not identified. It goes to `#27-determinism` as evidence.
  - ⚠ **What it means for every pre-registration built from ONE live run:** a per-turn table derived from a single
    trajectory can lose its tail to KI-112. Derive such a table from TWO identical runs, or state which rows lie past
    the first point where two runs could differ.
- **The filed rule, applied** ("the per-turn table is graded only on a reproducing trajectory"):
  - the 15 rows f3173282 … f3210218 are graded as filed;
  - the two Linoone rows (f3216950, f3217980) are NOT REACHED, and are not counted as PASS;
  - the two singles exits past the divergence were never pre-registered, and are reported, not graded:
    - f3230902: Poochyena, a miss, EXCLUDED `no-damage`;
    - f3231644: the KO, ACCEPTED, 117 in [110, 130].

## THE PER-TURN TABLE: 15 of 15 REACHED ROWS EXACT, 2 NOT REACHED

Each reached row matches its filed verdict, its reasons, its kind, wild or trainer, the foe's HP before and after, and
Δ`gBideDmg[1]` EXACTLY. ON-r1 and ON-r2 give identical verdicts. The rows:

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
the reason change was recorded in the design's AS BUILT section BEFORE the arms: the faint reset erases the Def-stage
read the table's wording relied on. Its 142 against a crit maximum of 152 is the only probable crit in the run, and it
sits in the excluded stratum.

## NON-VACUITY

- **✅ Passed:**
  - ≥ 1 accepted clean hit whose Δbide equals the foe's HP difference: f3190263 and f3198642. The third named one,
    f3216950, is NOT REACHED.
  - ≥ 1 accepted battle-end KO: 4 of them.
  - The doubles stratum in all three Route 123 doubles.
  - The foe-item-action stratum at f3191078.
  - The held-item stratum on Vanessa's Pikachu.
- **⚠ "A CTL line at each of the 15 battle starts" FAILS as filed: 14.** The literal counted the Step-0 trajectory,
  whose 15th battle was the Linoone. On this trajectory each of the 14 `[BATTLE] started` lines has its CTL at the
  same frame, in all three flagged runs.
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
