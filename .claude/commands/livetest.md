# /livetest — Conduct Live Tests (batch story-bot validation + report)

The user says **"Conduct Live Tests"** (optionally with a count and/or scope, e.g.
"Conduct Live Tests: 10", "/livetest 5 post_rival.ss1"). Default count: **10**.
Default scope: **fresh** (new game → the current story frontier).

## What to do

1. **Pre-flight**
   - Confirm no other heavy emulator work is running on this machine (ASK the user if
     they are mid-test on the GUI — batch lanes compete for CPU and would pollute
     their run's timing).
   - Check `tools/story-dev/livetest.py`'s `END_MARKERS` matches the CURRENT
     content-end message in `StoryMode._play` (it must be updated whenever the story
     frontier moves — a stale marker reports every run as INCOMPLETE).
   - Estimate + tell the user the wall-clock (fresh → frontier ≈ 20–35 min/run
     unthrottled; with the default 3 lanes a 10-run batch ≈ 1.5–2.5 h; scoped runs
     from a checkpoint are far faster).

2. **Run the batch** (background task; babysit, don't block):
   ```
   cd tools/story-dev
   PYTHONUTF8=1 py -3.12 livetest.py --count <N> [--lanes 3] [--state fresh|<save.ss1>]
   ```
   Output: `tools/story-dev/livetest-runs/<stamp>/run##/{run.log, stdout.txt,
   summary.json}` + a batch `summary.json`. Runs are isolated in `repro-live<K>`
   profiles — they can never touch the user's real save or committed checkpoints.

3. **Produce the LIVE TEST REPORT** (the deliverable — review it WITH the user before
   fixing anything). Read the batch summary first; open individual run.log files only
   where the summary flags anomalies (keep context lean). Report structure:
   - **Batch scorecard**: N runs → how many reached the frontier / hung / dropped to
     Manual / timed out; median frames + wall time.
   - **Per-run one-liners**: outcome, starter, notable events (shinies, catches,
     whiteouts, derail counts, where it ended).
   - **Issue clusters** — for EVERY anomaly:
     * frequency (x/N runs) + the context signature (segment, map, party/starter
       state, what preceded it),
     * classification: **universal bug** (same failure regardless of context) vs
       **nuanced situation** (only under specific circumstances — needs DETECTION of
       that circumstance + a targeted branch, NOT a blanket change) vs **known
       issue** (already in 05-KNOWN-ISSUES) vs **benign variance**,
     * evidence quotes (log lines + frame numbers),
     * proposed fix + regression risk, explicitly noting what the fix must NOT change.
   - **Recommendation order** for fixes.
4. **Discuss with the user.** Apply fixes only after their OK, one item at a time, each
   with the standard reproduce → fix → prove loop (playbook), then re-run a focused
   batch to confirm the fix and check for regressions.

## Rules
- NEVER run batch lanes while the user is live-testing on the same machine without
  their explicit OK.
- Never point lanes at the user's real profile. Never set SAVE_POST_RIVAL.
- Batch artifacts under `livetest-runs/` are gitignored scratch — the REPORT's
  substance goes into the PROJECT KNOWLEDGE docs (known-issues/mistakes) as usual.
- If a run hangs, the harness's HANG CONFIRMED stops it and the timeout kill is the
  backstop — never leave zombie emulator processes (verify with tasklist if unsure).
