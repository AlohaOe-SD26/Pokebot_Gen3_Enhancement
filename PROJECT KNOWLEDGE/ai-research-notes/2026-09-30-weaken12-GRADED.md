# 2026-09-30 — design v2 step 12 (weaken-to-catch) GRADED: every pre-registered arm held on its reproducing run (34 of 34); the weaken turn acted exactly once where predicted, and its KO bound is load-bearing. Stage 1 will still almost never act in a real run.

⛔ **THE CAVEAT IS THE HEADLINE.**
- Stage 1 acted live only through a TEST lever (`--set-lead-move`): no pinned party lead holds an exact-damage, sleep or
  paralysis move.
- Stage 2 (`POKEBOT_R25_WEAKEN_CALC`) stays OFF, because step 11 measured the calculator and did not clear it.
- This grade shows three things:
  - the machinery is SAFE and INERT;
  - it acts exactly as designed when a move exists;
  - the bound is what prevents the KO.
- It does NOT show that weakening raises the catch rate in a real run (that is step 14's), or that stage 2 is safe.

**Inputs:**
- Predictions: `2026-09-30-weaken12-PREDICTIONS.md`, committed `1f52cfd9` BEFORE any production code.
- Build: `18b32bcc`.
- Design: `2026-09-30-weaken12-DESIGN.md`.
- Evidence (`tools/story-dev/evidence/`):
  - `2026-09-30-weaken12-STEP0.txt` (the base-code reads);
  - `2026-09-30-weaken12-ARMS.txt` (every run's hash, both grades, the W-OBS divergence, the grader and the runner,
    verbatim);
  - `2026-09-30-weaken12-ST-ON-debug.txt` (the acting arm's raw log; every `[WEAKEN]` line replays).

## THE RESULT, ARM BY ARM (each against its filed line)

| Arm | Filed | Result |
|---|---|---|
| G-W | every W-row and fault; COVERAGE; < 300 s | ✅ 127 rows, 9 faults, 103 mutants, 0 uncovered, ~4 s with a pool. All 9 fault sets matched on their first run; 102 of 103 mutant sets did (M42 was corrected openly). The adversarial mutant pass is reported in its own section. |
| W-OFF ×2 | each = NL Step-0 (sha `e444a33991bd7720`); 0 `WEAKEN` lines | ✅ both exactly, so the build with the flags unset changes NOTHING against the base code |
| W-OBS | = W-OFF on every line without `WEAKEN`; 11 OBS lines, all THROW, 0 `first=1`; only inside catch battles; values = the raw record; replays | ⚠ **FAILED AS FILED on its first run, on two transient `[BALLS]` telemetry lines only** (below). ✅ **Its re-run under the filed decision rule (D15) passes every check.** |
| W-OBSCALC | as W-OBS; stage-2 verdicts measured | ✅ every check; all 11 `would=THROW`, as predicted (no stage-2 plain hit was admissible on this trajectory) |
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

## THE BUILDER'S DESIGN-GAP DECISIONS (recorded; the design owner's rulings in `06`)

- The damage and status caps each block only their own branch.
- **"No progress"**: a DAMAGE or STATUS turn after which, at a later turn's decision, the target's HP is not lower and
  it gained no status. Two such turns make the rest of the battle THROW-ONLY, so two misses end status attempts before
  a third try.
- The battle-type DEFER covers every flag except IS_MASTER and RECORDED_IS_MASTER (wider than the design's list).
- Stage 2's divergence exclusions are conservative: any live Flash Fire, any Charge, and badge 7 with a special move.
- Among admissible moves, the largest guaranteed damage wins, and a tie goes to the lowest slot.
