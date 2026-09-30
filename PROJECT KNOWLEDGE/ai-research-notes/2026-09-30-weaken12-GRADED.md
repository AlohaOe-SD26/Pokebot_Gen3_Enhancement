# 2026-09-30 — design v2 step 12 (weaken-to-catch) GRADED: every pre-registered arm held on its reproducing run (34 of 34); the weaken turn acted where predicted, and at every DAMAGE turn for exactly the lead's level, never a KO; its KO bound is load-bearing. Stage 1 will still almost never act in a real run.

⛔ **THE CAVEAT IS THE HEADLINE.**
- Stage 1 acted live only through a TEST lever (`--set-lead-move`): no pinned party lead holds an exact-damage, sleep or
  paralysis move.
- Stage 2 (`POKEBOT_R25_WEAKEN_CALC`) stays OFF, because step 11 measured the calculator and did not clear it.
- This grade shows three things:
  - on this fixture the machinery is INERT with the flags unset, and no DAMAGE turn KO'd. General safety rests on the gate AS FOLDED (`378a33b3`): the graded build `18b32bcc` still had PD1, a real KO path the adversarial pass found;
  - it acts exactly as designed when a move exists;
  - the bound is what prevents the KO.
- It does NOT show that weakening raises the catch rate in a real run (that is step 14's), or that stage 2 is safe.

**Inputs:**
- Predictions: `2026-09-30-weaken12-PREDICTIONS.md`, committed `1f52cfd9` BEFORE any production code.
- Build: `18b32bcc` (the table below). The folded build `378a33b3` was re-run, with the same results (its section
  below).
- Design: `2026-09-30-weaken12-DESIGN.md`.
- Evidence (`tools/story-dev/evidence/`):
  - `2026-09-30-weaken12-STEP0.txt` (the base-code reads);
  - `2026-09-30-weaken12-ARMS.txt` (every run's hash, both grades, the W-OBS divergence, the grader and the runner,
    verbatim);
  - `2026-09-30-weaken12-ST-ON-debug.txt` (the acting arm's raw log; every `[WEAKEN]` line replays);
  - `2026-09-30-weaken12-ADVERSARIAL.txt` and `-FOLD.txt` (the gate's pass and its fold);
  - `2026-09-30-weaken12-RERUN.txt` (the arms on `378a33b3`; its grader and runners, verbatim);
  - `2026-09-30-weaken12-REVIEW.txt` (the build's three-lens review).

## THE RESULT, ARM BY ARM (each against its filed line)

| Arm | Filed | Result |
|---|---|---|
| G-W | every W-row and fault; COVERAGE; < 300 s | ✅ 127 rows, 9 faults, 103 mutants, 0 uncovered, ~4 s with a pool. All 9 fault sets matched on their first run; 102 of 103 mutant sets did (M42 was corrected openly). The adversarial mutant pass is reported in its own section. |
| W-OFF ×2 | each = NL Step-0 (sha `e444a33991bd7720`); 0 `WEAKEN` lines | ✅ both exactly, so the build with the flags unset changes NOTHING against the base code |
| W-OBS | = W-OFF on every line without `WEAKEN`; 11 OBS lines, all THROW, 0 `first=1`; only inside catch battles; values = the raw record; replays | ⚠ **FAILED AS FILED on its first run, on two transient `[BALLS]` telemetry lines only** (below). ✅ **Its re-run under the filed decision rule (D15) passes every check.** |
| W-OBSCALC | as W-OBS; stage-2 verdicts measured | ✅ every check; all 11 `would=THROW`, as predicted (no stage-2 plain hit was admissible on this trajectory). ⚠ Those checks could not show that stage 2 RAN (review F4). A check added in the re-run's grade reads the reasons: every non-ender decision shows stage 2's own rejections (`bound@…`, `progress@…`), and W-OBS shows `no-damage-move` (`-RERUN.txt`). |
| ST-ON | = ST-OFF up to f165971; DAMAGE with Seismic Toss; Δbide 15; the Taillow at 6/21; 0 `res=Won` | ✅ exactly. The f165971 `[TURN 0]` line reads `UseMove:Seismic Toss(pp2)`; DMGAUDIT's BEFORE shows `mv[0]` = 69; Δbide = 15; the Taillow at 6. Both DAMAGE turns in the run did exactly the lead's level. 0 KOs. |
| DR-ON | = DR-OFF on EVERY line (the whole run); THROW with the floor as its reason at f140685 | ✅ exactly: sha `414d58ba95536d55`, identical to the DR Step-0 run. The reason read `dmg:floor@1\|st:no-status-move`. |
| DR-FAULT | Dragon Rage at f140685; Δbide 40; the Taillow faints | ✅ `act=DAMAGE move=Dragon_Rage`, BEFORE `mv[0]` = 82, Δbide 40, `[CATCH] end … res=Won`. **The bound is load-bearing:** without it, the same turn KOs the wanted target. |

## THE ONE LITERAL FAILURE, AND WHY THE ARM IS STILL GRADED

- **What differed:** the first W-OBS run differs from W-OFF1 ONLY in two `[BALLS]` telemetry lines. W-OFF1, W-OFF2,
  W-OBSCALC, the re-run and the base-code Step-0 all log a one-frame garbage ball count (`21 -> 24720 -> 21`) at
  f272106-7, during a map transition. The first W-OBS run did not.
- **The gameplay was identical:** with every `[BALLS]` line removed, all five flag-unset or observe runs are identical
  frame for frame (sha `604d29c10ae293d5`).
- **The grading rule, filed before the arms:** "a lone divergent run is re-run, never graded" (the design's D15, from
  step 11). The re-run equals W-OFF1 on every line, the transient included. As filed, then, the first run's check is a
  FAIL, and the ARM passes on its reproducing run.
- **A lead for KI-112 (UNVERIFIED):** `[BALLS]` compares per-frame logger samples. A run that misses the one garbage
  frame suggests `debug_logger.on_frame` did not run on that frame, i.e. frames emulated with no Python observer. The
  same mechanism would explain KI-112's gameplay divergences ("a warp one frame late"). This is the third KI-112
  observation, and the first one confined to telemetry. It goes to `#27-determinism`.

## PREDICTION SLIPS FOUND AFTER FILING (none changes a verdict)

- W52 was filed as "THROW (half)". The design's order checks the one-throw chance first, and at 11/22 that chance is
  0.624 ≥ 0.5, so the gate asserts THROW with the reason `odds`. The half rule is pinned by the builder's row WB52.
- The predictions' arithmetic `16711680//145 = 115253` should read 115252; no later step changes.
- ST-ON's "every later decision THROW (the damage cap)": the later verdicts are THROW, with the reason `odds`
  (the Taillow at 6/21 has p ≈ 0.785).
- W38, W51 and W58f cannot isolate the rule their names suggest, because an earlier rule decides them. The builder
  added rows that do isolate them (WB38; W58e; WBorder).
- **A filed W-row CHANGED with the fold** (review F9): PD5 raised the horizon's slack from 4 to 8, so H is 76, and
  W42b's filed snapshot (total PP 70, filed DAMAGE) now reads THROW. The row was moved to total PP 78, just above H.
  The ST discriminator's H is now 78 instead of the filed 70; its verdict is unchanged (105 > 78).
- **COVERAGE is a weak check** (the adversarial pass; review F10). It asks only that every row be in SOME fault's or
  mutant's set. The stronger form, where every row is reddened by a mutant of its own claimed rule, was NOT built.
  The vacuous rows were relabelled with the row that isolates each rule instead. Recorded, not hidden.

## THE BUILDER'S DESIGN-GAP DECISIONS (recorded; the design owner's rulings in `06`)

- The damage and status caps each block only their own branch.
- **"No progress"**: a DAMAGE or STATUS turn after which, at a later turn's decision, the target's HP is not lower and
  it gained no status. Two such turns make the rest of the battle THROW-ONLY, so two misses end status attempts before
  a third try.
- The battle-type DEFER covers every flag except IS_MASTER and RECORDED_IS_MASTER (wider than the design's list).
- Stage 2's divergence exclusions are conservative: any live Flash Fire, any Charge, and badge 7 with a special move.
- Among admissible moves, the largest guaranteed damage wins, and a tie goes to the lowest slot.

## THE ADVERSARIAL PASS ON THE GATE, ITS FIXES, AND THE ARMS RE-RUN ON THE FIXED COMMIT (`378a33b3`)

- **The pass** (`evidence/2026-09-30-weaken12-ADVERSARIAL.txt`): the gate caught 37 of 139 mutants. The worst miss
  was the KO floor's off-by-one.
- **It found five production defects, all FIXED** (the design's AS BUILT section; `-FOLD.txt`):
  - PD1, a Trace faint-switch copying the target's Rough Skin: a real KO path;
  - PD2 Pain Split, PD3 confusion berries, PD4 a Sand Stream member: latent;
  - PD5 RECHARGE in stage 2 and the horizon slack.
  - The gate is now 211 rows, 9 faults and 196 mutants; all 205 pre-written sets matched on the first run.
  - The full suite: 135 of 135.
- **The arms re-run on `378a33b3`** (`evidence/2026-09-30-weaken12-RERUN.txt`): **every arm passes against the
  reproducing OFF run (35 of 36 checks).**
  - **The one failure is W-OFF1's literal hash, and W-OFF1 is the lone divergent OFF run.** It missed the same one-frame
    garbage `[BALLS]` read that the first W-OBS run missed on `18b32bcc`, this time with every flag UNSET.
  - W-OFF2 and W-OFF3 reproduce each other (sha `e444a33991bd7720`, the base code's own hash) under the filed rule
    ("the two OFF runs must match each other first, else a third").
  - ⇒ The telemetry divergence is the harness's (KI-112), not the weaken code's.
  - ST-ON, DR-ON and DR-FAULT are identical to their runs on the unfixed build on every frame-stamped line outside
    `WEAKEN`/`DMGAUDIT`, and every `[WEAKEN]` verdict head (act, move, reason) is identical. Only the snapshot
    JSON differs, by the new `item_effect` field. So the fixes change no decision on these trajectories, as
    predicted. (The first version said "BYTE-IDENTICAL"; review F3 corrected it.)

## THE BUILD'S THREE-LENS REVIEW (2026-09-30; `evidence/2026-09-30-weaken12-REVIEW.txt`, verbatim; every blocker or should-fix went to a refuter)

- **One BLOCKER, confirmed: this note's claims, not the code.** The status lines (03, 04, 07) said "ST-ON acted once …
  for exactly 15". The grader's own count was TWO: 15 on the Taillow, then 17 on a later Skitty, each exactly the
  lead's level, neither a KO. Every status line and this note's title now say so.
- **Should-fix, confirmed and fixed:**
  - F2: the SAFE claim is scoped to this fixture and the folded gate.
  - F3: "byte-identical" reworded to what the hashes compare.
  - F4: a grader check now reads the reasons, and shows stage 2 ran in W-OBSCALC.
  - F5: 06's over-justification corrected (the per-branch caps permit status after damage), and 01's wording.
  - F6: the v2 note and 04 name the seeds 2-3 narrowing.
  - W12-S1: the Struggle horizon bounds the THROW phase only. A trapped Run costs no turn, and ordinary failed flees
    are unbounded. The post-abandonment residual is recorded in 06, and the comments are corrected.
- **Refuted to nits:** GAME-1, the same PD5 rationale; F6's v2-note half.
- **Nits folded:**
  - W12-N1: DAMAGE now honours `banned_moves` (a production change);
  - F7: KI-112's wording;
  - F8: two half-remapped citation ranges, now both ends;
  - F9: W42b's change disclosed;
  - F10: COVERAGE recorded as weak;
  - F11: the re-run's grader and runners embedded;
  - F12: the handoff's leftover wording;
  - GAME-2: the Wonder Guard wording.
- **The code fixes' proof** (`evidence/2026-09-30-weaken12-REVIEW-FIX.txt`):
  - the gate: 213 rows, 9 faults, 198 mutants, every new set exact on the first run;
  - the author's own REPLAY: all 59 logged verdicts of the arms on `378a33b3` replayed through the fixed module
    give the same verdict, move and reason;
  - so the `banned_moves` change alters no decision on the graded trajectories. The default list bans none of the
    moves involved.

