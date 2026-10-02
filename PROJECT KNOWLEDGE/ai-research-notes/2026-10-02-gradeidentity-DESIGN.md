# 2026-10-02 — `#27-gradeidentity` (KI-119): DESIGN + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** This fixes the GRADER, not the bot.
- Step 14's batch was graded by tools that misread the 27 runs following a Hall-of-Fame boot. A re-grade with the
  fixed tools is still **EXPLORATORY**: the tools were revised after the batch. Only a recorded user ruling makes it
  confirmatory.
- The fix also adds a fail-closed rule, so this label cannot be forgotten.

**Recon:** `tools/story-dev/evidence/2026-10-02-boxfirst-gradeid-RECON.txt`, ANGLE 4 (a read-only agent; a NOTE). The
coordinator re-verified:
- `battle_log.run_identity` (`battle_log.py:739-764`) takes the FIRST non-empty `[hb]`.
- `batch14_checks.load`'s `visit` hook runs on every log, excluded ones included (`batch14_checks.py:652-657`). So E1-E5,
  STOP-3 and the M1b pool already read all 78 logs, and `2026-10-02-batch14-GRADED.md`'s claim that the pool covered
  only the 51 graded runs is WRONG. It gets an erratum.

## What the stale boot corrupts (measured over all 78 logs by the recon)

- **Before the run's `Story: choosing X!` line,** the 27 stale-boot logs hold only these line types: `[BADGE]` (8, at
  f301), `[BALLS]`, `[MAP]`, `[PARTY]`, `[RESUMED]`, `[STEP]`, and `[hb]` (one of them with the saved party's
  `ids=`). No battle, catch, money, purchase or DMGAUDIT line comes before the choosing line in any log.
- **Two readers are corrupted:**
  - `run_identity` (species and PID → DECISION F8 and the clusters);
  - `batch14_checks.extract`'s `[BADGE]` reader (D-funnel badges and badge frames; D-lead's Stone-Badge tag).
- ⚠ **Skipping the stale `[BADGE]` lines is NOT enough.** The bot's badge recorder marked all 8 as recorded at the
  boot, so those runs never log a real `[BADGE]` line. A skip-only fix turns them into silent 0-badge runs.
  - Two sources agree and recover the badges: the leader-win frames, which match `[BADGE]` in 51 of 51 fresh logs; and
    each `[CATCH] end` line's own `badges=` field, which matches the leader-win count at the catch on 723 of 723
    lines.
  - The production badge recorder's assumption ("a hard reset means flags all back to 0", false for a HoF save) is a
    SEPARATE bot item, not this build.

## The build (tools only; no bot code, no emulator)

1. **`battle_log.run_start(lines)`:** the index of the first `Story: choosing X!` line, or None.
   - Not the New Game step: the stale `[hb]` comes after it.
   - Not the party clear: fresh logs have none, and mid-run misreads exist.
2. **`run_identity`:** species and PID from the first non-empty `[hb]` AFTER `run_start`. No choosing line gives
   None, with NO fallback to the old reading. `hold` and `chosen` are unchanged.
3. **`compare_arms`:**
   - A log with no choosing line is `no_starter`.
   - **`GRADER_REVISIONS`, fail-closed:** a list of (date, reason). Any batch whose ARMS.json `started` predates a
     revision gets an EXPLORATORY status naming it, and only a recorded user ruling lifts that. This supersedes
     `2026-10-01-batch14-T23-PREDICTIONS.md:49-50`'s identity rule (a `06` entry).
4. **`batch14_checks.extract`:**
   - PROGRESS fields are read only after `run_start`: money, map, era, leg 11, the Rustboro errand, badges, catches.
   - CORRECTNESS reads stay whole-log: battles and E1-E5, the monitor, STOP-3's tail, DMGAUDIT, weaken.
   - Badges come from leader-win frames; the catch's Stone-Badge tag comes from its own `badges=` field.
   - `[BADGE]` becomes a CONTROL: count the runs with `[BADGE]` lines before `run_start` ("poisoned"), and the
     un-poisoned runs whose `[BADGE]` set disagrees with the leader-win set.
5. **`batch14_tables`:** prints the badge source and the two control counts.
6. **Gates:** `probe_compare_arms.py` and `probe_batch14_checks.py` gain rows on REAL lines.
   - A committed excerpt `evidence/2026-10-02-gradeidentity-STALEBOOT.txt` holds the stale-boot lines from the 27 logs
     (L16 `…-040658`, L02 `…-010951` and `…-015003`). x4-runs is gitignored, so the gate quotes the excerpt, with a
     provenance check against the raw logs when they exist.
   - Rows: the stale identity, `run_start`, an empty `[hb]` after the choosing line, `run_record` on the stale
     fixture, the no-choosing case, the EXPLORATORY revision status, `extract` on the stale run (badges from leader
     wins, catch tags from `badges=`), money before the start ignored, correctness before the start still reported,
     and the control counts.
   - Revert mutants with exact red sets written BEFORE their first run, including KI-119's literal skip-only badge
     fix, and mention-only comments that must redden nothing.
7. **The re-grade:** run all three tools on `20261001-210001` and commit the outputs. Add an erratum and an addendum to
   `2026-10-02-batch14-GRADED.md`.

## PREDICTIONS

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| GI-1 | the two gates on the UNFIXED tools, then the fixed tools; then `run_gates.py` | Unfixed: exactly the new stale-boot, boundary, badge and revision rows are red, and every pre-existing row passes. Fixed: all rows pass, every mutant reddens exactly its pre-written set, and the full suite passes | an old row red on unfixed tools; a new row passing on unfixed tools; any red after the fix; a mutant mismatch; a suite FAIL |
| GI-2 | `compare_arms.py 20261001-210001` with the fixed tools | It reproduces the 2026-10-02 scratch corrected re-grade EXACTLY. 78 logs; usable A 40, B 38; excluded 0; clusters A 37, B 33. C1 A .032, B .930, Δ +.898 [+.442, +1.479] PASS. C2 θA .625, θB .662, Δ +.037, 95% CI [−.018, +.093], reading NOT LOWER, and the status says **EXPLORATORY (grader revised after the batch)**. C5 Δ −.0014 [−.0071, +.0048]. No harm flag | any value different from the scratch re-grade; a CONFIRMATORY status |
| GI-3 | `batch14_checks.py` and `batch14_tables.py` on the same batch | 0 excluded. E1-E5, STOP-3 and D-M1b UNCHANGED from the frozen grade (they already read all 78 logs; the M1b pool still has 194,304 accepted and 1 FAIL sample). Controls: 27 poisoned runs and 0 disagreeing. No run reads 8 badges at f301. Badge maxima A {1:1, 2:1, 3:2, 5:8, 6:2, 7:3, 8:23}, B {3:2, 4:9, 6:10, 7:3, 8:14}; D-lead A 1/801, B 40/726 (the recon's proposed-table figures) | a changed E-row, STOP-3 or M1b figure; poisoned ≠ 27; a disagreement > 0; badge or D-lead figures different from the recon's proposal (then read why before choosing) |
| GI-4 | the three tools on the SMOKE batch `20261001-090649` | Every number is identical to its pre-fix output (it has no stale boot). Its status is now EXPLORATORY, because it started before the revision | any changed number; no EXPLORATORY label |
| GI-5 | an INDEPENDENT adversarial pass on the diff and the gates | every non-equivalent mutant of `run_start`, `run_identity`, the badge reconstruction, the progress/correctness split and the revision rule reddens a row | a non-equivalent survivor |
