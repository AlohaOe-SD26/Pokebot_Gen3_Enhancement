# E2 + O8 build: the evidence, VERBATIM (2026-10-28)

> **A record, not a spec.** The build workflow's own outputs, copied here because its scratch folder lives only on
> the PC that ran it. The spec is `2026-10-28-E2-O8-BUILD-SPEC.md`; the summary is `07` 2026-10-28. Code: branch
> `worktree-wf_a6332466-c61-1` commits `b3a54290` (build) + `300ab630` (fix round), applied to `main` as ONE commit.
> **Corrected since (2026-10-28, Tier 1 review):** §5's and §6's view of a gate flake (F6: the build "waits for the next push") is incomplete:
> a restarted tuner runs the new code UNTESTED, because a new process takes the code on disk as its starting version (`05` KI-127).

## Contents
1. The builder's report: tests, RD1, RD2, deviations, open items
2. RD1/RD2 predictions and run output (`tools/ops/replay_learner_recovery.py`)
3. The builder's mutant run (32 of 32)
4. The independent mutant sweep (87 mutants, 23 survivors)
5. The adversarial review (verdict SHIP, F1-F7)
6. The fix round (all 23 survivors and F1-F4, F7 fixed; F5, F6 left) and its re-run
7. The last lines of the builder's final suite run
8. The serial re-run of all 27 fix-round mutants on the committed code (after the Tier 1 review)
9. A flaky archive check found by that re-run (R7b): measured, and nothing lost

## 1. The builder's report

**Tests:**

```text
test_agent.py (run in the worktree with PYTHONUTF8=1 and no bytecode): 329 checks, of which 328 pass and 1 fails. The one failure is P1 ('--arms must run from a MAIN checkout ... has no .git directory'). P1 fails because this is a git worktree, and it fails the same way at the starting commit f9fffb68 (265 checks, of which 264 pass and P1 fails). In a main checkout or the clone it should pass. Every other existing check passes unchanged.

The four new groups have 64 checks, all passing, each with FAULT and CONTROL arms: test_o8_torn 12 checks (1.7 s), test_o8_state 12 (0.7 s), test_o8_breaker 15 (2.4 s), test_e2_journal 25 (5.3 s).

Wall time, measured back to back in identical scratch layouts with alternating runs:
- BEFORE (f9fffb68): 37.0 s and 36.9 s (265 checks)
- AFTER: 49.9 s and 50.5 s (329 checks)
That is about 13 s added; the spec's target was 15 s or less. Earlier single runs in the worktree itself gave 45.6 s before and 49-50 s after; the machine is shared with the live 12-lane learner, so timings vary.

Mutants: 32 of 32 killed. Every guard in spec §4 was deleted in turn, plus a few extra (fsync of an append, the bad-line skip, the cycles.jsonl row dedupe, the journal's start filter, its stable window, and the rule that it never takes a lane's newest log). They ran in junctioned scratch copies against a control copy whose only failure was P1. Each mutant failed at least one check that targets its guard.

Stability: under 8 parallel copies the new groups first failed J9 once, a test-only race. With a stable window of 0, a log copied a moment earlier can carry a Windows mtime a few ms ahead of time.time(). I fixed it by back-dating the fixture logs 30 s (age_logs). After that, 16 of 16 parallel runs passed.

The existing check R15 CONTROL also failed in some parallel mutant runs. It uses the real process scan, so another suite's stand-in lane processes named endless-ai0003-* make it read 'in use'. That is cross-run interference from the parallel harness, not this change. It never failed in a serial run.
```

**RD1:**

```text
Predictions were printed before the run (saved as scratchpad/rd-predictions.txt). PASS: the result matched every prediction.

ai0031's raw.zip and plan.json were copied out of the clone (read-only) and unzipped into scratch, with dup_of members restored and mtimes set from the zip. No copied batch logs exist.

recover_records returned 24 records, recovered = '24 from lane profiles, 0 from the journal'. Per lane in ARMS order H1-H12: [2,1,1,2,2,3,1,3,4,1,2,2], as predicted.
- The 12 logs that are not the newest in their lane are complete and usable: 12 complete, 12 usable.
- The 12 newest logs: 0 complete (none reached the Champion or derail #5), so all 12 are censored.
- Total usable: 12; champions: 0. Every record has source ai0031, a genome_id and batch 20261017-023005.

Following U2, nothing was written to the clone and no backfill tool was built. Ran twice, at about 9:51 AM and about 11 AM, with identical results.
```

**RD2:**

```text
Predictions were printed before the run. PASS on ai0049, ai0050, ai0051 and ai0052, run before ai0049's raw logs are archived at about 4:28 PM. Comparison was by identity (batch, lane, log), field for field, against the clone's runs.jsonl.

| cycle | clone rows | journaled (= its not-newest rows) | (a) diffs | (b) with journal | (b) without journal |
|---|---|---|---|---|---|
| ai0049 | 55 | 43 | 0 | 55 records (12 profile + 43 journal), 0 diffs | 55 from profiles, 0 diffs |
| ai0050 | 59 | 47 | 0 | 59, 0 diffs | 59, 0 diffs |
| ai0051 | 52 | 40 | 0 | 52, 0 diffs | 52, 0 diffs |
| ai0052 | 52 | 40 | 0 | 52, 0 diffs | 52, 0 diffs |

- (a) is journal_games with a stable window of 0; every journaled record equals its clone row.
- In (b), the key set equals the clone's rows exactly, censored newest logs included.
- Safety: a (size, mtime) snapshot of each cycle's clone batch folder and lane profiles showed 0 files changed.
- The compare function was fault-tested separately: an altered field, a missing row, an extra row and a flipped 'complete' were each reported.

There were no RD2 differences. Ran twice with identical results.
```

**Deviations from the spec:**

- state.json.bak is replaced through its own alias, _os_replace_bak, not _os_replace. Through _os_replace the existing R20 check (an exact count of 3 replace attempts on state.json) would fail. ST9 patches this alias.
- state.json's shape check accepts a MISSING 'cycle' key (a present one must be an int; 'cycles' must be a list). The existing R12 fixture saves {'cycles': [...]} with no 'cycle', and the strict check broke R12. The .bak is restored only with an int cycle, as the spec requires. Production states always carry 'cycle'.
- The cycle row gets 'recovered' only when the recovery case produced at least one record. A recovery that finds nothing leaves today's row unchanged.
- The 'created' rebuild from endless-<tag>-* applies when ARMS.json EXISTS but is unreadable, as in spec §2a. A MISSING ARMS.json keeps today's [batch]: the batch runner writes ARMS.json before any lane spawns.
- In the crash handler the count is written first, then the log line 'learner CRASHED (n of 5 in a row)' plus the traceback. The spec lists the log first, but the line needs n. If the count cannot be written, the line says so and the handler returns 1.
- The top ATTENTION check returns 0 WITHOUT clearing the count (BK5 requires 'count unchanged'). The spec's 'clean exit ... ATTENTION' reset is the in-loop ATTENTION return; that one and all other normal 0/3 exits clear it.
- In `once` mode a crash is now caught, logged and returned as 1, uncounted. Today a Python traceback exits with 1, so the exit code is the same.
- repair_jsonl returns one of four status strings ('clean', 'repaired', 'refused', 'failed') and never raises or exits. If the atomic rewrite fails after the .bad append, a retry can append the same bad lines to .bad again: duplicates, never loss.
- The guards became small patchable helpers so the FAULT arms can remove them by patching. The helpers are _paused, _crash_update, _on_crash, _loop_body, _run_batch, _load_plan, _read_arms, _tag_profiles, _unseen, _cycle_row_exists, _journal_records, _arms_since, _lane_profile_logs, _newest_started_cycle, _guarded, _say and _fsync, plus the constant JOURNAL_SINCE_SLACK_S = 6.0. crash_count() and compare_journal() are public.
- For T6 (journal handled in runs mode), my code ignores a refusal in journal mode. The FAULT arm shows the bad lines NOT moved, rather than an ATTENTION or a stop.
- J7 and J11 use drive_cycle_long, a fake batch that lives 0.8 s and writes batch/ENDED, so 'journaled WHILE the batch ran' and 'ran to its end' can be observed. The O6 tests keep the existing drive_cycle. J11 also makes the Popen crash-count reset raise, because otherwise mutant M24 (the clear guard) would survive.
- loop_box's run_cycle stub plants STOP, so a mutant that wrongly reaches the cycle loop ENDS instead of spinning. The first sweep hung on M02 because of this; the processes were killed by command-line match, and only this session's own scratch processes.
- The RD tool sets each restored file's mtime from the zip's date_time, so the journal's start filter sees roughly the original times. The spec does not specify this.
- learner.py's working copy is LF and the index is LF (autocrlf true), so the committed content is unaffected. git diff --stat shows 853 lines for learner.py; ignoring whitespace it is 666 added and 33 removed, mostly because loop()'s old body was dedented into _loop_body.
- PROJECT KNOWLEDGE docs (02, 03, 04, 05, 06, 07) were not edited, as instructed; the main session writes them. Nothing was pushed, and main was not touched.

**Open items it handed back:**

- Docs per the Definition of Done are still to do in the main session: 02, 03 (#28-trainer-improvements item 1), 04, 05 and 07. 06 needs entries for §2a's recovery choice, §2b's .bak check and §2c's breaker choices, plus the deviations above (the _os_replace_bak alias, the relaxed state.json shape check, 'recovered' only with at least one record, the top ATTENTION check not clearing the count).
- The commit is on worktree branch worktree-wf_a6332466-c61-1 and is not pushed. Deploying means merging to main and pushing; the learner picks it up at the next cycle boundary only if test_agent.py passes IN THE CLONE. P1 fails here only because this is a worktree; confirm P1 passes in a main checkout or the clone before pushing.
- Post-deploy checks (spec §5), read-only, after the boundary: learner.log shows 'test_agent.py passes: restarting into it'; state.json.bak exists; crashes.json is absent or 0; runs/<new tag>/games.jsonl gains lines; at cycle end the log shows '<tag>: game journal: N of N journaled games match the batch's records'.
- R15 CONTROL (an existing O3 check) is sensitive to OTHER suites' fake lane processes running at the same time. It only matters if two test_agent.py runs ever overlap on this PC, for example a manual run during the clone's restart gate. This is pre-existing and was left as is.
- Scratch evidence is in C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad: rd-predictions.txt, rd-run1.txt, rd-run2.txt, mut3.txt (32/32), final.txt, before.txt, mutants.py and time_base.py. The folders mut1, mut2, mut3 and timing contain NTFS junctions to the worktree's tools/ and sandbox-pokebot/. If they are deleted, remove the junctions first (or use rmdir on them), so a recursive delete cannot follow them into the worktree.

## 2. RD1/RD2: predictions (printed before the run), then the run

```text
REGISTERED PREDICTIONS (written before any check runs):
  RD1 ai0031: recover_records returns 24 records (the 24 profile logs of its manifest, all under profiles/endless-ai0031-H*/debug-logs); per lane in ARMS order H1-H12: 2,1,1,2,2,3,1,3,4,1,2,2
  RD1 ai0031: the 12 logs that are NOT the newest of their lane are complete (12 complete at least); each lane's newest log is complete only if it reached the Champion or derail #5 (count reported)
  RD1 ai0031: recovered = '24 from lane profiles, 0 from the journal'; every record has source 'ai0031', a genome_id, and batch '20261017-023005'
  RD2(a) ai0049: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0049: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0050: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0050: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0051: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0051: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0052: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0052: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  SAFETY: no file under the clone's batch folders or lane profiles changes size or mtime
```

```text
REGISTERED PREDICTIONS (written before any check runs):
  RD1 ai0031: recover_records returns 24 records (the 24 profile logs of its manifest, all under profiles/endless-ai0031-H*/debug-logs); per lane in ARMS order H1-H12: 2,1,1,2,2,3,1,3,4,1,2,2
  RD1 ai0031: the 12 logs that are NOT the newest of their lane are complete (12 complete at least); each lane's newest log is complete only if it reached the Champion or derail #5 (count reported)
  RD1 ai0031: recovered = '24 from lane profiles, 0 from the journal'; every record has source 'ai0031', a genome_id, and batch '20261017-023005'
  RD2(a) ai0049: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0049: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0050: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0050: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0051: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0051: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0052: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0052: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  SAFETY: no file under the clone's batch folders or lane profiles changes size or mtime

RESULTS (this checkout's learner code, C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_a6332466-c61-1; clone C:\Remote Projects\pokebot-learner read-only; scratch C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\rd-run1):
RD1 ai0031: 115 files restored from raw.zip; copied batch logs present: False
RD1 ai0031: 24 records; recovered = '24 from lane profiles, 0 from the journal'
RD1 ai0031: per lane (ARMS order): [2, 1, 1, 2, 2, 3, 1, 3, 4, 1, 2, 2]
RD1 ai0031: not-newest 12 (complete 12, usable 12); newest 12 (complete 0: [])
RD1 ai0031: usable in total 12; champions 0; walls ['Ch# (Victory Road) failed after # attempts. attempt #: BotModeError: C', 'E4 refused: League basket short', 'Story: global watchdog', 'boss wall: Juan', 'boss wall: Norman', 'boss wall: Tate & Liza', 'boss wall: this boss', 'no derail recorded']
[2026-10-28 09:51:04 AM] ai0049: game journal: 43 finished game(s) recorded (43 so far)
RD2 ai0049: clone rows 55 (not newest 43); journaled 43 (43 read back); with journal: 55 records (12 from lane profiles, 43 from the journal); without: 55 records (55 from lane profiles, 0 from the journal); 22.3 s
RD2 ai0049: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 09:51:27 AM] ai0050: game journal: 47 finished game(s) recorded (47 so far)
RD2 ai0050: clone rows 59 (not newest 47); journaled 47 (47 read back); with journal: 59 records (12 from lane profiles, 47 from the journal); without: 59 records (59 from lane profiles, 0 from the journal); 22.2 s
RD2 ai0050: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 09:51:49 AM] ai0051: game journal: 40 finished game(s) recorded (40 so far)
RD2 ai0051: clone rows 52 (not newest 40); journaled 40 (40 read back); with journal: 52 records (12 from lane profiles, 40 from the journal); without: 52 records (52 from lane profiles, 0 from the journal); 21.6 s
RD2 ai0051: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 09:52:11 AM] ai0052: game journal: 40 finished game(s) recorded (40 so far)
RD2 ai0052: clone rows 52 (not newest 40); journaled 40 (40 read back); with journal: 52 records (12 from lane profiles, 40 from the journal); without: 52 records (52 from lane profiles, 0 from the journal); 23.3 s
RD2 ai0052: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0

ALL RD CHECKS PASS
```

Run 2 (about 10:06 AM) differs from run 1 (about 9:51 AM) only in its timestamps, its scratch paths and the elapsed seconds per cycle; every count is the same (checked 2026-10-28 by normalising those three and diffing: 0 other differences). Run 2 follows.

```text
REGISTERED PREDICTIONS (written before any check runs):
  RD1 ai0031: recover_records returns 24 records (the 24 profile logs of its manifest, all under profiles/endless-ai0031-H*/debug-logs); per lane in ARMS order H1-H12: 2,1,1,2,2,3,1,3,4,1,2,2
  RD1 ai0031: the 12 logs that are NOT the newest of their lane are complete (12 complete at least); each lane's newest log is complete only if it reached the Champion or derail #5 (count reported)
  RD1 ai0031: recovered = '24 from lane profiles, 0 from the journal'; every record has source 'ai0031', a genome_id, and batch '20261017-023005'
  RD2(a) ai0049: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0049: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0050: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0050: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0051: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0051: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  RD2(a) ai0052: every journaled record equals its clone runs.jsonl row field for field (0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows
  RD2(b) ai0052: recover_records without a journal AND with (a)'s journal: key set == the clone's rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)
  SAFETY: no file under the clone's batch folders or lane profiles changes size or mtime

RESULTS (this checkout's learner code, C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_a6332466-c61-1; clone C:\Remote Projects\pokebot-learner read-only; scratch C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\rd-run2):
RD1 ai0031: 115 files restored from raw.zip; copied batch logs present: False
RD1 ai0031: 24 records; recovered = '24 from lane profiles, 0 from the journal'
RD1 ai0031: per lane (ARMS order): [2, 1, 1, 2, 2, 3, 1, 3, 4, 1, 2, 2]
RD1 ai0031: not-newest 12 (complete 12, usable 12); newest 12 (complete 0: [])
RD1 ai0031: usable in total 12; champions 0; walls ['Ch# (Victory Road) failed after # attempts. attempt #: BotModeError: C', 'E4 refused: League basket short', 'Story: global watchdog', 'boss wall: Juan', 'boss wall: Norman', 'boss wall: Tate & Liza', 'boss wall: this boss', 'no derail recorded']
[2026-10-28 10:05:59 AM] ai0049: game journal: 43 finished game(s) recorded (43 so far)
RD2 ai0049: clone rows 55 (not newest 43); journaled 43 (43 read back); with journal: 55 records (12 from lane profiles, 43 from the journal); without: 55 records (55 from lane profiles, 0 from the journal); 23.5 s
RD2 ai0049: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 10:06:22 AM] ai0050: game journal: 47 finished game(s) recorded (47 so far)
RD2 ai0050: clone rows 59 (not newest 47); journaled 47 (47 read back); with journal: 59 records (12 from lane profiles, 47 from the journal); without: 59 records (59 from lane profiles, 0 from the journal); 23.1 s
RD2 ai0050: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 10:06:45 AM] ai0051: game journal: 40 finished game(s) recorded (40 so far)
RD2 ai0051: clone rows 52 (not newest 40); journaled 40 (40 read back); with journal: 52 records (12 from lane profiles, 40 from the journal); without: 52 records (52 from lane profiles, 0 from the journal); 23.5 s
RD2 ai0051: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0
[2026-10-28 10:07:09 AM] ai0052: game journal: 40 finished game(s) recorded (40 so far)
RD2 ai0052: clone rows 52 (not newest 40); journaled 40 (40 read back); with journal: 52 records (12 from lane profiles, 40 from the journal); without: 52 records (52 from lane profiles, 0 from the journal); 24.5 s
RD2 ai0052: (a) 0 difference(s); (b) with journal 0, without 0; clone files changed: 0

ALL RD CHECKS PASS
```

## 3. The builder's mutant run

```text
CONTROL: 1 FAILED (329 checks, 50.2 s); failing in this layout: ["FAIL P1 a 6-arm, 24-lane arms file passes x4_headless's preflight"]
KILLED   M01 newline guard (append_jsonl): 4 FAILED (329 checks, 55.0 s); new failures: ['FAIL J12 a log older than ARMS.json `started` is neither journaled nor recovered; CONTROL: the fresh logs are', 'FAIL T2 the newline guard: the appended row stays a line of its own: 4 rows readable', 'FAIL T4 a torn cycles.jsonl tail: run_cycle returns True, the cycle is scored, and its new cycles.jsonl row is readable']
KILLED   M02 startup repair: 3 FAILED (329 checks, 54.5 s); new failures: ["FAIL T3 5 bad lines in runs.jsonl: repair returns 'refused' and leaves the file byte-unchanged; loop() writes ATTENTION (restore from the nightly backup) and returns 0 without starting a cycle", 'FAIL T5 loop() repairs runs.jsonl at start: returns 0 (STOP), runs.jsonl.bad holds the fragment, runs.jsonl = the good lines byte for byte']
KILLED   M03 journal-mode repair without a limit: 2 FAILED (329 checks, 55.0 s); new failures: ['FAIL T6 games.jsonl with 5 bad lines: all 5 moved to games.jsonl.bad, no ATTENTION, no exit, and a-0, a-1 are still journaled']
KILLED   M04 .bak write: 2 FAILED (318 checks, 52.6 s); new failures: ['FAIL crash in <lambda> #19']
KILLED   M05 .bak write guard: 3 FAILED (329 checks, 54.9 s); new failures: ['FAIL R15 CONTROL: once those processes are gone the next boundary archives both', "FAIL ST9 the backup's replace locked on every try: save_state returns, state.json holds the new state, a log line names the failure"]
KILLED   M06 .bak restore: 2 FAILED (318 checks, 53.9 s); new failures: ['FAIL crash in <lambda> #19']
KILLED   M07 .bak restore's runs check: 2 FAILED (329 checks, 55.2 s); new failures: ["FAIL ST8 a stale backup is refused: StateUnreadable names '47' and 'ai0053', and nothing is renamed or rewritten"]
KILLED   M08 lock-holder restore of state.json: 6 FAILED (323 checks, 54.6 s); new failures: ["FAIL ST1 0 bytes: FAULT today's load_state RAISES; guarded: the backup's dict is returned, state.json restored, the bad file kept as state.json.bad.1", "FAIL ST2 the first half: FAULT today's load_state RAISES; guarded: the backup's dict is returned, state.json restored, the bad file kept as state.json.bad.1", "FAIL ST3 4 KB of NUL: FAULT today's load_state RAISES; guarded: the backup's dict is returned, state.json restored, the bad file kept as state.json.bad.1"]
KILLED   M09 top ATTENTION check: 3 FAILED (329 checks, 55.1 s); new failures: ['FAIL BK5 ATTENTION.md planted + a bad state: returns 0 at once, the count unchanged, no state file touched', 'FAIL R15 CONTROL: once those processes are gone the next boundary archives both']
KILLED   M10 outer except (the breaker): 15 FAILED (329 checks, 54.3 s); new failures: ['FAIL BK-C CONTROL: a healthy state + STOP returns 0 with no crash, no ATTENTION, count 0; a crash in `once` returns 1 and is NOT counted', 'FAIL BK1 FAULT: with no limit, 5 crashes write no ATTENTION and the retries go on', "FAIL BK1 state.json and its backup both bad: loop() returns 1,1,1,1,0; ATTENTION says 'crashed 5 times' and names StateUnreadable; 5 tracebacks in learner.log; the count is reset to 0"]
KILLED   M11 crash counter: 8 FAILED (329 checks, 54.2 s); new failures: ["FAIL BK1 state.json and its backup both bad: loop() returns 1,1,1,1,0; ATTENTION says 'crashed 5 times' and names StateUnreadable; 5 tracebacks in learner.log; the count is reset to 0", 'FAIL BK2 load_config raising is counted the same way (1 of 5) and no update is attempted', 'FAIL BK3 3 crashes, then a batch is LAUNCHED (the real run_cycle), then 4 crashes: no ATTENTION, count 4']
KILLED   M12 handler's update step: 3 FAILED (329 checks, 54.2 s); new failures: ['FAIL BK4 a pushed fix: the crash handler fast-forwards (once), sees new code whose tests pass and returns 3 (restart into it); no ATTENTION; the count is kept at 1', 'FAIL BK4b the fetched update FAILS test_agent.py: return 0, ATTENTION says so, the count is reset']
KILLED   M13 reset at Popen: 4 FAILED (329 checks, 55.9 s); new failures: ['FAIL BK3 3 crashes, then a batch is LAUNCHED (the real run_cycle), then 4 crashes: no ATTENTION, count 4', 'FAIL J11 journal_games AND the crash-count reset raising, with log() raising in their handler: run_cycle returns True, the cycle is scored, the fake batch ran to its end (exit 0)', 'FAIL R15 CONTROL: once those processes are gone the next boundary archives both']
KILLED   M14 reset when the breaker writes ATTENTION: 3 FAILED (329 checks, 55.5 s); new failures: ["FAIL BK1 state.json and its backup both bad: loop() returns 1,1,1,1,0; ATTENTION says 'crashed 5 times' and names StateUnreadable; 5 tracebacks in learner.log; the count is reset to 0", 'FAIL R15 CONTROL: once those processes are gone the next boundary archives both']
KILLED   M15 reset on a clean exit: 2 FAILED (329 checks, 54.9 s); new failures: ['FAIL BK7 3 crashes, a clean STOP run (returns 0), then 4 crashes: no ATTENTION']
KILLED   M16 reset when the fetched update fails its tests: 2 FAILED (329 checks, 54.5 s); new failures: ['FAIL BK4b the fetched update FAILS test_agent.py: return 0, ATTENTION says so, the count is reset']
KILLED   M17 recovery: 5 FAILED (329 checks, 56.1 s); new failures: ['FAIL J10 adopt_unfinished journals a-0, a-1 during its waiting polls (batch_running True for 2 polls)', "FAIL J4 a kill mid-cycle: adopt's rows = today's parse_batch over the profile logs as collect_logs would copy them, row for row; 3 usable; `recovered` set; the tested proposal moved to done/; the torn journal tail in games.jsonl.bad; the journal deleted after the save", 'FAIL J5 FAULT: with the dedupe patched out, the re-adopt appends every key twice']
KILLED   M18 swap: 3 FAILED (329 checks, 56.2 s); new failures: ["FAIL J4 a kill mid-cycle: adopt's rows = today's parse_batch over the profile logs as collect_logs would copy them, row for row; 3 usable; `recovered` set; the tested proposal moved to done/; the torn journal tail in games.jsonl.bad; the journal deleted after the save", 'FAIL J5 FAULT: with the dedupe patched out, the re-adopt appends every key twice']
KILLED   M19 dedupe of runs.jsonl rows: 3 FAILED (329 checks, 55.8 s); new failures: ["FAIL J5 recovery re-adopt (a death between the append and the save): runs.jsonl's key set = J4's, each key once; ONE cycles.jsonl row", "FAIL J5b normal re-adopt (copied logs): the key set = the first adopt's, each once; one cycle row"]
KILLED   M20 dedupe of the cycles.jsonl row: 3 FAILED (329 checks, 55.9 s); new failures: ["FAIL J5 recovery re-adopt (a death between the append and the save): runs.jsonl's key set = J4's, each key once; ONE cycles.jsonl row", "FAIL J5b normal re-adopt (copied logs): the key set = the first adopt's, each once; one cycle row"]
KILLED   M21 run_cycle's journal call: 4 FAILED (329 checks, 56.6 s); new failures: ['FAIL J11 journal_games AND the crash-count reset raising, with log() raising in their handler: run_cycle returns True, the cycle is scored, the fake batch ran to its end (exit 0)', "FAIL J7 FAULT: one journal record altered before the compare -> the line says '1 of 2' and names its key", "FAIL J7 the normal path (real run_cycle): a-0 and a-1 were journaled WHILE the batch ran; the rows = today's parse_batch of the copied batch; the compare line says '2 of 2'; the journal is deleted; the cycle is scored"]
KILLED   M22 adopt-loop journal call: 2 FAILED (329 checks, 56.6 s); new failures: ['FAIL J10 adopt_unfinished journals a-0, a-1 during its waiting polls (batch_running True for 2 polls)']
KILLED   M23 journal guard: 2 FAILED (329 checks, 55.5 s); new failures: ['FAIL J11 journal_games AND the crash-count reset raising, with log() raising in their handler: run_cycle returns True, the cycle is scored, the fake batch ran to its end (exit 0)']
KILLED   M24 clear guard: 2 FAILED (329 checks, 55.4 s); new failures: ['FAIL J11 journal_games AND the crash-count reset raising, with log() raising in their handler: run_cycle returns True, the cycle is scored, the fake batch ran to its end (exit 0)']
KILLED   M25 plan.json guard: 3 FAILED (329 checks, 56.0 s); new failures: ["FAIL J13 (a) a half-written plan.json: moved to plan.json.bad, `current` cleared, adopt returns None; (b) a half-written ARMS.json at finish: it returns, and `created` = batch + exactly this cycle's two profiles", 'FAIL R15 CONTROL: once those processes are gone the next boundary archives both']
KILLED   M26 ARMS.json guard at finish: 4 FAILED (329 checks, 55.9 s); new failures: ["FAIL J13 (a) a half-written plan.json: moved to plan.json.bad, `current` cleared, adopt returns None; (b) a half-written ARMS.json at finish: it returns, and `created` = batch + exactly this cycle's two profiles", 'FAIL J13 FAULT: without the rebuild, an unreadable ARMS.json leaves `created` without the lane profiles (never archived: a disk leak)', 'FAIL R15 CONTROL: once those processes are gone the next boundary archives both']
KILLED   M27 created rebuild: 2 FAILED (329 checks, 55.5 s); new failures: ["FAIL J13 (a) a half-written plan.json: moved to plan.json.bad, `current` cleared, adopt returns None; (b) a half-written ARMS.json at finish: it returns, and `created` = batch + exactly this cycle's two profiles"]
KILLED   M28 load_jsonl skips a bad line (no raise): 5 FAILED (318 checks, 53.2 s); new failures: ["FAIL J4 a kill mid-cycle: adopt's rows = today's parse_batch over the profile logs as collect_logs would copy them, row for row; 3 usable; `recovered` set; the tested proposal moved to done/; the torn journal tail in games.jsonl.bad; the journal deleted after the save", 'FAIL J5 FAULT: with the dedupe patched out, the re-adopt appends every key twice', "FAIL J5 recovery re-adopt (a death between the append and the save): runs.jsonl's key set = J4's, each key once; ONE cycles.jsonl row"]
KILLED   M29 fsync of an append: 3 FAILED (329 checks, 56.0 s); new failures: ['FAIL R15 CONTROL: once those processes are gone the next boundary archives both', "FAIL T-C CONTROL: a healthy CRLF file ending \\r\\n: 0 bad lines, load = today's load, repair is a no-op (no .bad, same bytes and mtime), an append writes the same bytes as today's, and it is fsynced"]
KILLED   M30 the journal's start filter: 2 FAILED (329 checks, 57.0 s); new failures: ['FAIL J12 a log older than ARMS.json `started` is neither journaled nor recovered; CONTROL: the fresh logs are']
KILLED   M31 the journal's stable window: 2 FAILED (329 checks, 56.9 s); new failures: ['FAIL J2 logs modified within JOURNAL_STABLE_S (120 s) are NOT journaled yet']
KILLED   M32 the journal never takes a lane's newest log: 11 FAILED (329 checks, 56.5 s); new failures: ["FAIL J1 two polls journal only a-0, a-1 (never a lane's newest a-2 / b-1), no duplicate; a new a-3 makes a-2 journal-able at the next poll", 'FAIL J10 adopt_unfinished journals a-0, a-1 during its waiting polls (batch_running True for 2 polls)', 'FAIL J12 a log older than ARMS.json `started` is neither journaled nor recovered; CONTROL: the fresh logs are']

32 of 32 mutants killed
```

## 4. The independent mutant sweep

**MUTANT SWEEP: E2 + O8 build** (commit b3a54290, diffed against f9fffb68)

**Counts: 87 mutants, 64 CAUGHT, 23 SURVIVED.** 40 mutants (25 caught) are extras beyond the spec's list. The 47 for the spec §4 guards and their variants split 39 caught, 8 survived.

**Every one-per-guard deletion in the spec's §4 list was CAUGHT.** The one exception is the adopt-loop journal guard, which survived (M17a2).

**Control and method**
- The unmutated copy passes: `ALL PASS (329 checks, ~51 s)`. It also passed 4 times in parallel.
- A copy needs an empty `.git` directory. The worktree's `.git` is a file, and check P1 (the `--arms` preflight) refuses that. This is a copying fix; no code changed.
- Each mutant was a fresh copy: `ai-agent`, `tools`, `sandbox-pokebot` and the repo-root files, without data, runs, profiles, `__pycache__` or the other large folders.
- Every anchor matched exactly once and every mutant compiled, so no CAUGHT comes from a syntax error.
- **Parallel-run noise:** I ran 5 mutants at once. Check R15 (the process-scan check) then failed spuriously in 36 runs. Eight mutants had R15 as their only failure, so I re-ran those serially and all eight became SURVIVED. They are reported as SURVIVED below.
- X18 was my own broken edit (a TypeError from a tuple missing its comma). I fixed it and re-ran it. M10ef was added after the first pass.
- The scratch dirs are deleted, and the worktree is unchanged. I did not touch the main checkout or the learner clone.

Paths are in `ai-agent/learner.py` unless noted. A guard "removed" by `except Exception` → `except ZeroDivisionError` means the handler no longer fires.

**Spec-list mutants (M-series)**

| Mutant | Edit | Result | Failing checks |
|---|---|---|---|
| M01 | newline guard in `append_jsonl` deleted | CAUGHT | T2, T4 |
| M01i | that guard inverted (`!=` to `==`) | CAUGHT | T2, T4, T-C |
| M02 | startup repair call deleted (`if repair_jsonl(...)=="refused"` to `if False`) | CAUGHT | T3, T5 |
| M02b | repair runs but its "refused" ATTENTION branch is dead | CAUGHT | T3 |
| M03 | journal-mode `repair_jsonl(path, None)` deleted | CAUGHT | T6, J4 |
| M03b | journal-mode repair given `MAX_BAD_LINES` | CAUGHT | T6 |
| M04 | `.bak` write deleted in `save_state` | CAUGHT | check #19 crashed (`FileNotFoundError` on the `.bak`), not a named check |
| M04g | `.bak` write's try/except removed | CAUGHT | ST9 |
| M05 | `.bak` restore deleted (`if _LOCK_HELD:` to `if False`) | CAUGHT | ST1-ST4, plus a crash in check #19 |
| M05b | restore by any process (`if True`) | CAUGHT | ST7 |
| M05c | bad `state.json` not set aside before restore | CAUGHT | ST1-ST4 |
| M06 | `.bak` runs check deleted (`if bak["cycle"] < newest` to `if False`) | CAUGHT | ST8 |
| M06i | that check's boundary `<` to `<=` | **SURVIVED** | none |
| M07 | top ATTENTION check deleted (`if _paused()` to `if False`) | CAUGHT | BK5 |
| M08 | outer `except` removed, so the crash handler is never entered | CAUGHT | BK1, BK2, BK3, BK4, BK4b, BK5, BK6, BK7, BK-C |
| M09 | counter deleted (`n = _note_crash(error)` to `n = 1`) | CAUGHT | BK1, BK2, BK3, BK4, BK5, BK7 |
| M09b | `CRASH_LIMIT = 10**9` | CAUGHT | BK1, BK2, BK3, BK7 |
| M09c | limit boundary `n < CRASH_LIMIT` to `<=` | CAUGHT | BK1, BK3 |
| M10 | handler update step deleted (`rc = _crash_update(...)` to `None`) | CAUGHT | BK4, BK4b |
| M10b | `_crash_update`'s `auto_update` test deleted | **SURVIVED** | none |
| M10c | its "code unchanged" early return deleted | **SURVIVED** | none |
| M10d | its `tests_pass` gate bypassed (always restarts) | CAUGHT | BK4b |
| M10e | its config-read guard removed (alone) | **SURVIVED** | none |
| M10f | the handler's `exc3` guard removed (alone) | **SURVIVED** | none |
| M10ef | both M10e and M10f removed together | CAUGHT | BK2 |
| M11a | reset on Popen deleted in `_run_batch` | CAUGHT | BK3, J11 |
| M11b | reset after ATTENTION deleted in `_on_crash` | CAUGHT | BK1 |
| M11b2 | reset after ATTENTION deleted in `_crash_update` | CAUGHT | BK4b |
| M11c | clean-exit reset deleted in `loop()` | CAUGHT | BK7 |
| M11ci | clean-exit condition inverted | CAUGHT | BK7 |
| M11cr | clean-exit reset no longer fires on `RESTART_CODE` (3) | **SURVIVED** | none |
| M12 | recovery deleted (`recover_records` call to `[], None`) | CAUGHT | J4, J5, J10 |
| M13 | swap deleted (journal record never replaces the profile record) | CAUGHT | J4, J5 |
| M13b | journal-only records (log gone) not added | CAUGHT | J6 |
| M14 | `_unseen` dedupe bypassed | CAUGHT | J5, J5b |
| M14b | cycle-row dedupe deleted | CAUGHT | J5, J5b |
| M14c | within-batch dedupe (`have.add`) deleted | **SURVIVED** | none |
| M15 | `run_cycle` journal call deleted | CAUGHT | J7, J11 |
| M16 | adopt-loop journal call deleted | CAUGHT | J10 |
| M17a | journal guard removed in `_run_batch` | CAUGHT | J11 |
| M17a2 | journal guard removed in the adopt loop | **SURVIVED** | none |
| M17b | clear guard removed in `_run_batch` | CAUGHT | J11 |
| M17c | `_guarded`'s inner `log()` try removed | CAUGHT | J11 |
| M17d | `_guarded`'s outer except removed | CAUGHT | J11 |
| M18 | `plan.json` guard removed (raw `json.loads` in adopt) | CAUGHT | J13 |
| M19 | `ARMS.json` guard removed in `finish_cycle` | CAUGHT | J13 (two checks) |
| M20 | `created` rebuild deleted (`_tag_profiles` to `[]`) | CAUGHT | J13 |

**Extra mutants (X-series)**

| Mutant | Edit | Result | Failing checks |
|---|---|---|---|
| X01 | journal stable-window test deleted | CAUGHT | J2 |
| X02 | newest-log exclusion `[:-1]` deleted | CAUGHT | T6, J1, J2, J3, J4, J6, J7, J10, J12 |
| X03 | profile-log start filter deleted | CAUGHT | J12 |
| X03b | recovery's start filter deleted (`since = None`) | CAUGHT | J12 |
| X04 | journal known-key skip deleted | CAUGHT | J1, J7, J10 |
| X04b | `known.add` deleted | **SURVIVED** | none |
| X04c | load of known keys from the journal deleted | CAUGHT | T6, J1 |
| X05 | `compare_journal` call deleted | CAUGHT | J7, J8 |
| X06 | `_drop_journal` call deleted | CAUGHT | J4, J7 |
| X07 | blank-piece skip in `_split_jsonl` deleted | CAUGHT | T1, T6, T-C |
| X08 | bad line raises again in `_split_jsonl` | CAUGHT | J4, J5, plus a crash in check #18 |
| X09 | state shape check (dict + `cycles` list) deleted | CAUGHT | only a crash in check #19 (`AttributeError`), not a named ST check |
| X09b | state int-`cycle` check deleted | **SURVIVED** | none |
| X10 | `_LOCK_HELD = True` removed from `acquire_lock` | **SURVIVED** | none |
| X11 | `once`-mode branch of the crash handler deleted | CAUGHT | BK-C |
| X12 | counter-write-failure guard (`exc2`) removed | CAUGHT | BK6 |
| X13 | ATTENTION-write-failure guard (`exc4`) removed | **SURVIVED** | none |
| X14 | `cmd_status` `StateUnreadable` catch removed | **SURVIVED** | none |
| X15 | `_run_batch` kill-on-`BaseException` disabled | CAUGHT | J11 |
| X16 | cycle row's `recovered` field deleted | CAUGHT | J4 |
| X17 | per-(lane, log) dedupe in `_journal_records` deleted | **SURVIVED** | none |
| X18 | `_newest_started_cycle` ignores `PROFILES` | **SURVIVED** | none |
| X18b | `_newest_started_cycle` ignores `RUNS` | CAUGHT | ST8 |
| X19 | `.bad` fsync in `repair_jsonl` deleted | **SURVIVED** | none |
| X20 | repair no longer keeps good lines byte for byte | CAUGHT | T1, T5 |
| X21 | `append_jsonl` fsync deleted | CAUGHT | T-C |
| X22 | `_atomic_write` fsync deleted | CAUGHT | ST-C |
| X23 | journal builds records with `last_in_lane=True` | **SURVIVED** | none |
| X24 | `journal_games` unreadable-ARMS early return deleted | **SURVIVED** | none |
| X25 | repair limit ignored | CAUGHT | T3, T6 |
| X25b | repair limit boundary `>` to `>=` | **SURVIVED** | none |
| X26 | `scoring.py`: profile `lane_logs` branch dead | CAUGHT | J4, J5, J6, J9, J12 |
| X27 | `scoring.py`: `lane_logs` result reversed instead of sorted | CAUGHT | J4 |
| X28 | `state.json` write made non-atomic | CAUGHT | R20, ST-C |
| X29 | `attention()` write made non-atomic | **SURVIVED** | none |
| X30 | `arms.json` write in `run_cycle` made non-atomic | **SURVIVED** | none |
| X31 | crash-counter write made non-atomic | **SURVIVED** | none |
| X32 | `_clear_crashes` made a no-op | CAUGHT | BK1, BK3, BK4b, BK7 |
| X33 | `_note_crash` never keeps `first` | **SURVIVED** | none |
| X34 | `_paused()` logs but returns False | CAUGHT | BK5 |

**Survivors that matter**
- **M17a2:** the adopt-loop journal call has no raising test. J10 only checks that it is called. The spec's J11 covers `run_cycle`, not the adopt loop.
- **M10b, M10c:** nothing runs the crash handler with `auto_update` on and the code signature unchanged, or with `auto_update` off. BK4 only changes the signature.
- **M10e, M10f:** the two guards are redundant with each other. Either one alone survives, and removing both is caught by BK2.
- **M11cr:** the spec says the count clears on a clean return of 0 or 3. Only the 0 path is tested.
- **X10:** no check shows that the real `acquire_lock` makes `loop()` restore from the `.bak`. The ST tests set `_LOCK_HELD` directly.
- **M06i:** the ST fixtures never have a `.bak` whose cycle equals the newest started cycle. That is the normal case after a clean save.
- **X23:** the J3 fixture games all end in Champion or derail #5, so censoring the newest game makes no difference. Nothing pins that the journal's records are uncensored.
- **X18, X24, X09b, X17, X14, X13:** their branches are not exercised.
- **X19, X29, X30, X31:** atomicity and fsync are asserted only for `append_jsonl`, `_atomic_write` and `save_state`.
- **X04b:** this is effectively equivalent. `journal_games` reloads `known` from the journal whenever it is empty, so the `.add` is redundant.
- **M14c, X25b, X33:** a within-batch duplicate, a boundary at exactly the limit, and the `first` timestamp are untested. All three are low value.

## 5. The adversarial review

**Verdict: SHIP.** I found nothing that can kill or orphan the live batch, corrupt or double-count data, wrongly stop a learner that should run, or let the deploy gate touch real git, processes or RAM. All findings below are gaps in the tests or docs, plus small edge cases; the code behaves correctly today. F1's fixture fix takes a minute and is worth folding in before the push.

## What I re-ran
I re-ran everything in a scratch copy made with `git archive b3a54290` under the scratchpad. I wrote nothing in the worktree, the main checkout or the clone.

- **Suite:** 329 checks pass. One check, P1, fails only in the copy because it has no `.git` folder (an environment artifact, not the build).
- **Suite time:** about 62 s against 45.9 s for the old suite (265 checks), so about 16-20 s added. The spec's target was 15 s or less; the gate's timeout is 600 s.
- **RD1/RD2:** I ran these against the clone read-only (`--rd1 --rd2 ai0049 ai0050 ai0051 ai0052`) and every check passed:
  - ai0031: 24 records, per lane 2,1,1,2,2,3,1,3,4,1,2,2; 12 not-newest records, all complete; 0 newest complete.
  - ai0049-52: journal and recovery match the clone's rows by identity, with or without the journal: 55/59/52/52 rows, 0 differences, 0 clone files changed.
  - The RD logic is sound. Note that RD2(b) cannot tell the swap from no swap on intact logs; that proves faithfulness only. J9 is the test that covers the swap.
- **Live compatibility:** I read the clone's files. `state.json` is a dict with int `cycle` 53 and a list `cycles`. `runs.jsonl` has 3,366 lines ending `\r\n`. The new loaders accept both, so the startup repair is a no-op.
- **Mutants:** 23 run, one code change each.
  - Killed (13): m03, m07, m08, m09, m10, m11, m14, m15, m17, m18, m19, m22, m23. m03 removes `proc.kill`; m07 and m08 touch the reset after the batch launches; m09 and m19 remove the dedupes; m10 removes the journal delete; m17 removes the fsync; m22 lets any process restore; m23 removes the first ATTENTION check.
  - Killed (3) where the R15 failure in each was an artifact of my parallel runs: m06, m16, m17 (m17 is also in the list above). m06 effectively survived, because R15 was its only failure. m16 is genuinely killed by J4 and m17 by ST-C.
  - Survived (8): m01, m02, m04, m05, m06, m12, m13, m21.

## Findings

**F1, MAJOR (a test gap; the code is correct today).** The normal restore case is never tested: a backup whose `cycle` equals the newest started cycle.
- `ai-agent/learner.py:399`: `if bak["cycle"] < newest:`
- `ai-agent/test_agent.py:3303`: ST1-ST4 and ST6 use `good = dict(GOOD_STATE, cycle=5, ...)` with no `runs/ai0005`, so `newest` is 0. ST8 tests only the refuse direction (47 against ai0053).
- **Scenario:** mutant m21 changes `<` to `<=` and all 329 checks pass. In production a backup at cycle 53 with `runs/ai0053` present would then always be refused. A torn `state.json` would mean StateUnreadable, 5 crashes, then ATTENTION, and the core O8 feature would be silently dead.
- **Fix:** create `runs/ai0005` (and an `endless-ai0005-*` profile) in the ST1-ST4/ST6 fixtures, and add a FAULT arm for `<=`.

**F2, MINOR (test gaps; each mutant passes all 329 checks).**
- **m01:** `learner.py:511` sets `_LOCK_HELD = True` in `acquire_lock`, but every ST test sets `learner._LOCK_HELD = True` by hand (`test_agent.py:3312` and others). No test restores through the real lock, so if the flag were lost the restore would silently happen only in memory. Fix: one ST arm that calls `acquire_lock()`.
- **m02:** the adopt-loop guard at `learner.py:1345` (`_guarded(f"{tag}: game journal", lambda: journal_games(tag, cdir / "batch", known))`) can be removed. J10 never makes the journal raise during adopt. Fix: a J10 arm where `journal_games` raises.
- **m13:** the shape check at `learner.py:336` (`isinstance(st.get("cycles"), list)`) is untested for a dict with no `cycles`, which would then raise later at `state["cycles"]`. Fix: add `{}` to the ST contents.
- **m06, m12, m04, m05:**
  - m06: the PROFILES half of `_newest_started_cycle` can be dropped.
  - m12: the slack sign in `_arms_since` can be flipped.
  - m04: the fsync of the `.bad` file can be removed.
  - m05: `release_lock` can stop clearing the flag.

  All four have low impact.

**F3, MINOR (the README overclaims).** `README.md:108` says "A crash anywhere in the learner's start-up or loop is counted", but these run before the counted `try`:
- `learner.py:1958` `started_sig = code_signature()`
- `learner.py:1959` `log(f"learner started (code {started_sig})")`
- lock acquisition
- import-time errors

A full disk, or a pushed import error that reaches a reboot, retries every 10 minutes forever and never reaches the breaker or its update step. Fix: name these exceptions in the README, or move the two lines inside the `try`.

**F4, MINOR (the journal can be deleted with nothing recorded).** `learner.py:1092` calls `_drop_journal(tag)` unconditionally after `save_state`. If `recover_records` raises (`:1057`) or the normal `parse_batch` fails (`:1049`), the records are `[]`, the cycle is saved with 0 runs, and the journal (possibly the only whole-parse copy) is deleted. Fix: delete it only when every journal key is in `runs.jsonl`; otherwise rename it to `games.jsonl.kept`.

**F5, MINOR (a stale crash count can survive a rollback).** `_crash_update` returns RESTART and keeps the count by design. Pre-O8 code never clears `data/crashes.json`. After an automatic rollback at count n < 5 and a later redeploy, a new startup crash loop trips ATTENTION after 5 − n crashes. Fix: treat the count as 0 when `last` is more than about 60 minutes old (longer than the 10-minute retry), which also catches other stale-count paths.

**F6, MINOR (an unexplained gate flake).**
- One failure in about 10 sequential runs of the unmodified build ("1 FAILED (329 checks, 65.9 s)"). I did not capture which check failed, and it did not recur in 6 reruns.
- Under parallel suite runs, R15 (`test_agent.py:1232`, a real process scan) fails three times, from the other suites' fake lanes and batch runners. That check predates this build. I suspect the one failure was this same R15 sensitivity to other suites running on the machine, since other agents may be running the suite now.
- At the deploy boundary a gate flake sets `refused_sig`, which is never retested, so a flake means the build waits for the next push.

**F7, MINOR (wording).** After a refused update is on disk, a single crash makes `_crash_update` see a new signature, run `tests_pass()` (which fails) and write ATTENTION: "The learner was crash-looping and the update it fetched … FAILS". The stop is the spec's intended behaviour, but "crash-looping" is wrong after one crash. Fix: reword the message.

## Lenses with no defect found
1. **The live learner:** `_run_batch` matches `subprocess.run`, and only a BaseException (Ctrl-C or exit) or `proc.wait` failing reaches `proc.kill` (J11 and m03 confirm). The dedupe and the one-row-per-tag check hold (m09, m19). A torn line now produces a `.bad` file instead of a stop.
2. **The deploy gate:** every new `loop()` test runs through `loop_box`, which stubs `update_checkout`, `tests_pass` and `code_signature`. The process scan is stubbed and lanes are fixed at 8. The older loop tests use `auto_update=False` or `single=True`, so the crash handler's update step is never reached with real git. No unbounded waits.
3. **Backward compatibility:** old-code `state.json`, JSONL files and `plan.json` load unchanged. A cycle without `games.jsonl` adopts through J8 or recovers from profiles alone.

Files:
- Spec: `C:/Remote Projects/Pokebot_Gen3_Enhancement/PROJECT KNOWLEDGE/ai-research-notes/2026-10-28-E2-O8-BUILD-SPEC.md`
- Build: `C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_a6332466-c61-1\ai-agent\learner.py`, `test_agent.py`, `README.md`
- Mutation harness and results: `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\mutate.py`, `mutants.json`, `mutants2.json`, `mutA.txt`, `mutB.txt`, `mutC.txt`

VERDICT: SHIP

## 6. The fix round

FIX ROUND RESULT: E2 + O8 (branch worktree-wf_a6332466-c61-1, commit **300ab630**, not pushed)

All 23 surviving mutants and all the review findings are handled, except two minor findings left for a decision (F5, F6). I re-ran every survivor I addressed as one edit in a fresh scratch copy (PYTHONDONTWRITEBYTECODE=1, `-B`), and each one is now CAUGHT. 28 mutants were run in total: the 23 sweep survivors plus 5 of the reviewer's (m05, m12, m13, m21 = M06i) and the F4 revert. The unmutated copy passed with "ALL PASS (357 checks, 50.5 s)", P1 included.

**Survived mutants: all FIXED (the failing check is what kills each one)**
- **M06i / F1 / m21:** ST1–ST4, ST4b, ST4c and ST6 now create `runs/ai0005` and `endless-ai0005-H1-mudkip`. Each one also checks that the newest started cycle equals the backup's cycle 5, so the test really hits the boundary. Caught by 7 ST checks.
- **M10b:** caught by a new BK1 check that the handler makes 0 update calls with `auto_update` off.
- **M10c:** caught by BK4c, a control where the fetch brings nothing new, so the tests do not run and loop() returns 1.
- **M10e:** caught by BK2, which now requires the update step's own log line ("config.json is unreadable") and requires that the outer guard's line is absent.
- **M10f:** caught by BK2b. Its FAULT arm calls `_crash_update` directly, and it raises when `code_signature` raises. The guarded arm returns 1, counts 1, and the log names the failed update step.
- **M11cr:** caught by two new BK7 arms where the clean run is a restart that returns 3. The FAULT arm (no clear) ends in ATTENTION; the guarded arm gives `([1,1,1], 3, [1,1,1,1], False)`.
- **M14c:** caught by J5c (a duplicate key inside one call to `_unseen`).
- **M17a2 / m02:** caught by J10b, where the journal call raises during the adopt wait. In the FAULT arm (guard removed) adopt raises; in the guarded arm it waits both polls, logs the failure and scores 4 rows.
- **X04b:** this was NOT equivalent, as the sweep had thought. When `known` starts non-empty it is never reloaded, so the next poll re-journals the same game. Caught by J1b, which keeps one `known` set across three polls: the mutant gives (0,1,1) where the code gives (0,1,0).
- **X09b:** caught by ST4c (a `cycle` that is not an int).
- **m13 / X09:** caught by ST4b (a dict with no `cycles`).
- **X10 / m01 and m05:** caught by ST10, which uses the real `acquire_lock` and `release_lock`. Its FAULT arm writes the lock file without setting the flag, so the backup is used in memory only.
- **X13:** caught by BK9. The ATTENTION write fails, so loop() returns 1 five times and the count stays at 5.
- **X14:** caught by ST11 (`status` with an unreadable state).
- **X17:** caught by J3b (a key journaled twice is used once, the first record).
- **X18 / m06:** caught by ST8b, where only the lane profile survives. Its FAULT arm reads `runs/` alone and restores the stale backup.
- **X19 / m04:** caught by a T1 check of the fsync count (2).
- **X23:** caught by J1. a-2 has no end; once it is journaled it must be complete and usable, and equal to `lane_record(last_in_lane=False)`.
- **X24:** caught by J13b (a torn ARMS.json means 0 games journaled and no exception).
- **X25b:** caught by T3b (exactly 3 bad lines are repaired).
- **X29:** caught by BK1's write recorder (ATTENTION.md must go through `_atomic_write`).
- **X30:** caught by J7's write recorder (arms.json, plan.json, state.json and its backup).
- **X31:** this survived the first re-run. The BK1 recorder was masked because `_clear_crashes` also writes crashes.json. BK8 now records the writes of `_note_crash` alone (3 atomic crashes.json writes), and the re-run is CAUGHT.
- **X33:** caught by BK8 (`first` is kept).
- **Review m12 (the slack's sign flipped):** caught by J12b. A log modified 3 s before `started` is journaled and recovered. Its FAULT arm uses no slack and drops that log.

**Review findings**
- **F1 (MAJOR): FIXED,** as M06i above.
- **F2 (MINOR): FIXED,** covered by m01, m02, m13, m06, m12, m04 and m05 above.
- **F3 (MINOR): FIXED in the README.** The breaker only counts crashes after the lock is held and `learner started` has been logged. Import errors, the lock, the code signature and that first log line are retried uncounted every 10 minutes by `run_agent.ps1`. I did not change the code: moving them inside the `try` would leave `started_sig` undefined in the crash handler.
- **F4 (MINOR): FIXED in code.** `_drop_journal` now deletes `games.jsonl` only when every journaled (source, batch, lane, log) is in runs.jsonl. Otherwise it renames it to `games.jsonl.kept` (never overwriting) and logs that. It never raises. J14 tests it: its FAULT arm (the old unconditional delete) deletes the journal after recording 0 of its 2 games; the guarded arm keeps it byte for byte. Mutant "F4" (reverting this) is CAUGHT. J4 and J7 still show a fully recorded journal is deleted.
- **F7 (MINOR): FIXED.** The message now reads "The learner crashed and the update it fetched … FAILS test_agent.py".
- **F5 (MINOR): LEFT.** A stale crash count after a rollback to pre-O8 code is real, but the effect is only an early ATTENTION. Fixing it with a time window would change the spec's "in a row" rule, so that is the spec owner's call.
- **F6 (MINOR): LEFT.** R15 is a real process scan that can fail when other suites run on the same machine. It predates this build, and so does `refused_sig`, which is in f9fffb68. 10 suite runs across this round reported no failure that was not caused by a mutant (the base, the worktree and the scratch control); the one P1 failure is a worktree artifact (below).

**Final `ai-agent/test_agent.py` in the worktree:** 1 FAILED (357 checks, 50.7 s). The one failure is P1: "has no .git directory", because a worktree's `.git` is a file. This is the same environment artifact the sweep and the review reported. In the scratch copy, which has a `.git` directory, the same code gives ALL PASS (357 checks, 50.5 s).

**Commit:** 300ab630, staging only `ai-agent/learner.py`, `ai-agent/test_agent.py` and `ai-agent/README.md`. Message: "fix: E2 + O8 review round - tests kill the sweep's survivors, the journal is kept when the cycle recorded fewer games, README crash-count scope", ending with both required lines. The suite grew from 329 checks to 357 and takes about 51 s.

I did not write to the main checkout or the learner clone, and the scratch copy is deleted.

Files are in C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\e2o8fix:
- harness.py
- muts.py
- results.txt

**The fix round's own re-run of the survivors (`e2o8fix/results.txt`):**

```text
control: CONTROL rc=0 | ALL PASS (357 checks, 54.6 s) | 
M06i: CAUGHT rc=1 | 7 FAILED (357 checks, 51.1 s) | FAIL ST1 0 bytes: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the backup's di || FAIL ST2 the first half: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the back || FAIL ST3 4 KB of NUL: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the backup' || FAIL ST4 valid JSON, not a state (a list): FAULT today's load_state returns a list; guarded, with the backup's cycle 5 EQUAL to the newest started cyc || FAIL ST4b a dict with no `cycles`: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the newest || FAIL ST4c a `cycle` that is not an int: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cy
M10b: CAUGHT rc=1 | 1 FAILED (357 checks, 51.9 s) | FAIL BK1 with auto_update OFF the crash handler never fetches (0 updates); the counter and ATTENTION.md are both written atomically (through _atomic_w
M10c: CAUGHT rc=1 | 1 FAILED (357 checks, 51.8 s) | FAIL BK4c CONTROL: the fetch brings nothing new (same code signature): no test run, no restart, no ATTENTION; returns 1 (the 10-minute retry) with the
M10e: CAUGHT rc=1 | 1 FAILED (357 checks, 51.6 s) | FAIL BK2 load_config raising is counted the same way (1 of 5) and no update is attempted: the update step's OWN guard says so ('config.json is unreada
M10f: CAUGHT rc=1 | 1 FAILED (357 checks, 51.1 s) | FAIL BK2b FAULT: the update step itself RAISES here (so the handler's own guard is load-bearing); guarded: loop() returns 1, the crash is counted (1),
M11cr: CAUGHT rc=1 | 1 FAILED (357 checks, 51.3 s) | FAIL BK7 3 crashes, a clean RESTART into new code (returns 3), then 4 crashes: no ATTENTION (exit 3 is clean too)  -> ([1, 1, 1], 3, [1, 0, 0, 0], Tru
M14c: CAUGHT rc=1 | 1 FAILED (357 checks, 52.1 s) | FAIL J5c _unseen: a key twice in the same list is kept once, a key already in runs.jsonl not at all  -> 2
M17a2: CAUGHT rc=1 | 1 FAILED (357 checks, 52.5 s) | FAIL J10b the journal raising at both waiting polls: adopt waits both polls, logs the failure, then scores the cycle from the lane profiles (returns T
X04b: CAUGHT rc=1 | 1 FAILED (357 checks, 51.0 s) | FAIL J1b one `known` set across three polls (as _run_batch keeps it): 0, then a-3 once, then 0; the journal holds each key once  -> (0, 1, 1, [(1, 'a-
X09b: CAUGHT rc=1 | 1 FAILED (357 checks, 51.5 s) | FAIL ST4c a `cycle` that is not an int: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the n
m13: CAUGHT rc=1 | 1 FAILED (357 checks, 51.6 s) | FAIL ST4b a dict with no `cycles`: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the newest
X10: CAUGHT rc=1 | 1 FAILED (357 checks, 51.2 s) | FAIL ST10 the real acquire_lock: the holder restores state.json from the backup; after the real release_lock the same tear is read from the backup in 
m05: CAUGHT rc=1 | 1 FAILED (357 checks, 51.7 s) | FAIL ST10 the real acquire_lock: the holder restores state.json from the backup; after the real release_lock the same tear is read from the backup in 
X13: CAUGHT rc=1 | 1 FAILED (357 checks, 51.9 s) | FAIL BK9 the 5th crash's ATTENTION write fails: loop() returns 1 (the retry, no traceback escapes), the log says so, and the count is NOT reset (5), s
X14: CAUGHT rc=1 | 1 FAILED (357 checks, 51.7 s) | FAIL ST11 `status` with state.json and its backup both unreadable: prints 'STATE UNREADABLE', the rest of the status, and returns 0  -> ("RAISED State
X17: CAUGHT rc=1 | 1 FAILED (357 checks, 51.1 s) | FAIL J3b a (lane, log) journaled twice: _journal_records returns it ONCE, the first line's record  -> [13750, 13000, -1]
X18: CAUGHT rc=1 | 1 FAILED (357 checks, 51.3 s) | FAIL ST8b only the lane profile endless-ai0053-H1-mudkip proves cycle 53 started: the backup is refused, naming it, and state.json is left as it was  
X19: CAUGHT rc=1 | 1 FAILED (357 checks, 51.2 s) | FAIL T1 the repair forces BOTH writes onto the disk: the .bad file and the rewritten file (2 fsyncs)  -> 1
X23: CAUGHT rc=1 | 1 FAILED (357 checks, 51.2 s) | FAIL J1 a journaled game is never censored: a-2 (no Champion, no 5th derail) is journaled complete + usable, = lane_record(last_in_lane=False)  -> [(F
X24: CAUGHT rc=1 | 1 FAILED (357 checks, 51.4 s) | FAIL J13b journal_games with a half-written ARMS.json: returns 0, writes no games.jsonl, raises nothing  -> RAISED TypeError("'NoneType' object is not
X25b: CAUGHT rc=1 | 1 FAILED (357 checks, 51.5 s) | FAIL T3b exactly MAX_BAD_LINES (3) bad lines: repaired (the limit is 'more than'), all 3 moved to runs.jsonl.bad, the good lines kept byte for byte  -
X29: CAUGHT rc=1 | 1 FAILED (357 checks, 51.3 s) | FAIL BK1 with auto_update OFF the crash handler never fetches (0 updates); the counter and ATTENTION.md are both written atomically (through _atomic_w
X30: CAUGHT rc=1 | 1 FAILED (357 checks, 51.2 s) | FAIL J7 run_cycle writes arms.json, plan.json and state.json (+ its backup) atomically (through _atomic_write)  -> ['plan.json', 'state.json', 'state.
X31: SURVIVED rc=0 | ALL PASS (357 checks, 51.1 s) | 
X33: CAUGHT rc=1 | 1 FAILED (357 checks, 51.4 s) | FAIL BK8 three crashes: count 1,2,3; `first` stays the first crash's time, `last` and `last_error` move on  -> ([1, 2, 3], {'count': 3, 'first': 'T3',
m12: CAUGHT rc=1 | 1 FAILED (357 checks, 51.2 s) | FAIL J12b a log modified 3 s before ARMS.json `started` (within collect_logs' 5 s) is journaled and recovered  -> (False, False)
F4: CAUGHT rc=1 | 1 FAILED (357 checks, 50.9 s) | FAIL J14 the recovery failed (0 runs recorded): games.jsonl is kept byte for byte as games.jsonl.kept and the log says so; CONTROL J4/J7: a journal wh
```

## 7. The last lines of the builder's final suite run (`final.txt`)

```text
PASS J2 FAULT: with a stable window of 0, logs modified just now are journaled
PASS J2 logs modified within JOURNAL_STABLE_S (120 s) are NOT journaled yet
PASS J3 each journal record equals today's parse_batch record of the copied log (+ genome_id), every field
PASS J4 FAULT: with recovery patched out, a kill mid-cycle scores 0 rows (ai0031 on 2026-10-17)
PASS J4 a kill mid-cycle: adopt's rows = today's parse_batch over the profile logs as collect_logs would copy them, row for row; 3 usable; `recovered` set; the tested proposal moved to done/; the torn journal tail in games.jsonl.bad; the journal deleted after the save
PASS J5 recovery re-adopt (a death between the append and the save): runs.jsonl's key set = J4's, each key once; ONE cycles.jsonl row
PASS J5 FAULT: with the dedupe patched out, the re-adopt appends every key twice
PASS J5b FAULT: with the dedupe patched out, a normal re-adopt appends each key twice
PASS J5b normal re-adopt (copied logs): the key set = the first adopt's, each once; one cycle row
PASS J6 the lane profiles deleted: recovery gives the journal's records only (a-0, a-1, equal to today's)
PASS J7 FAULT: one journal record altered before the compare -> the line says '1 of 2' and names its key
PASS J7 the normal path (real run_cycle): a-0 and a-1 were journaled WHILE the batch ran; the rows = today's parse_batch of the copied batch; the compare line says '2 of 2'; the journal is deleted; the cycle is scored
PASS J8 CONTROL: adopting an old-code cycle (copied logs, no games.jsonl) records exactly today's rows, no `recovered`, and the compare line says 0 of 0
PASS J9 FAULT: with the swap removed, a-1's row is the CUT log's (= today's parse of the cut log)
PASS J9 a-1's profile log cut by the crash: its row is the journal's whole record, which differs from today's parse of the cut log
PASS J10 FAULT: with the adopt-loop journal call removed, nothing is journaled before scoring
PASS J10 adopt_unfinished journals a-0, a-1 during its waiting polls (batch_running True for 2 polls)
PASS J11 FAULT: with the guards removed, a journal failure RAISES out of run_cycle and the batch is killed
PASS J11 journal_games AND the crash-count reset raising, with log() raising in their handler: run_cycle returns True, the cycle is scored, the fake batch ran to its end (exit 0)
PASS J12 FAULT: with the start filter removed, a profile log from an hour before the batch is journaled and recovered
PASS J12 a log older than ARMS.json `started` is neither journaled nor recovered; CONTROL: the fresh logs are
PASS J13 FAULT: today's code RAISES on a half-written plan.json (adopt) and ARMS.json (finish)
PASS J13 FAULT: without the rebuild, an unreadable ARMS.json leaves `created` without the lane profiles (never archived: a disk leak)
PASS J13 (a) a half-written plan.json: moved to plan.json.bad, `current` cleared, adopt returns None; (b) a half-written ARMS.json at finish: it returns, and `created` = batch + exactly this cycle's two profiles
1 FAILED (329 checks, 50.2 s)
```

## 8. The serial re-run of all 27 fix-round mutants on the committed code (added 2026-10-28 after the Tier 1 review)

**Why:** §6's saved `results.txt` shows X31 SURVIVED, and no saved row shows it CAUGHT after BK8 was tightened (§6's
prose says it was). §6 also says "28 mutants", while its listing and `muts.py` hold 27: the 23 sweep survivors
(M06i among them, which is also the review's m21, the double count), 3 more of the review's (m05, m12, m13) and a
revert of the F4 fix. So every one of the 27 (`e2o8fix/muts.py`, unchanged) was re-run SERIALLY on the exact code of
this item's commit: the index tree `4daf192f1b53c2f8879702a006f94e1b7165de0d` (`git write-tree`), archived into a scratch copy with an empty `.git`
(so check P1 runs), a fresh copy of `ai-agent/` per mutant, and a CONTROL run before and after. The verdict rule is
§6's: CAUGHT = a FAIL line, a non-zero exit or a crash.

**Result:** 27 of 27 CAUGHT, both controls ALL PASS (1:30 PM to 1:55 PM 2026-10-28). X31 is CAUGHT by BK8.

```text
started 2026-10-28 01:30:57 PM
setup: index tree 4daf192f1b53c2f8879702a006f94e1b7165de0d; base/ has 6245 archive entries (tools, sandbox-pokebot, 8 root files); src-ai-agent/ has 14 files
mutants: 27 from C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\e2o8fix\muts.py
control-1: CONTROL rc=0 | ALL PASS (357 checks, 51.6 s) | 
M06i: CAUGHT rc=1 | 7 FAILED (357 checks, 50.0 s) | FAIL ST1 0 bytes: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the backup's di || FAIL ST2 the first half: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the back || FAIL ST3 4 KB of NUL: FAULT today's load_state RAISES; guarded, with the backup's cycle 5 EQUAL to the newest started cycle (runs/ai0005): the backup' || FAIL ST4 valid JSON, not a state (a list): FAULT today's load_state returns a list; guarded, with the backup's cycle 5 EQUAL to the newest started cyc || FAIL ST4b a dict with no `cycles`: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the newest || FAIL ST4c a `cycle` that is not an int: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cy
M10b: CAUGHT rc=1 | 1 FAILED (357 checks, 50.6 s) | FAIL BK1 with auto_update OFF the crash handler never fetches (0 updates); the counter and ATTENTION.md are both written atomically (through _atomic_w
M10c: CAUGHT rc=1 | 1 FAILED (357 checks, 49.4 s) | FAIL BK4c CONTROL: the fetch brings nothing new (same code signature): no test run, no restart, no ATTENTION; returns 1 (the 10-minute retry) with the
M10e: CAUGHT rc=1 | 1 FAILED (357 checks, 49.3 s) | FAIL BK2 load_config raising is counted the same way (1 of 5) and no update is attempted: the update step's OWN guard says so ('config.json is unreada
M10f: CAUGHT rc=1 | 1 FAILED (357 checks, 49.4 s) | FAIL BK2b FAULT: the update step itself RAISES here (so the handler's own guard is load-bearing); guarded: loop() returns 1, the crash is counted (1),
M11cr: CAUGHT rc=1 | 1 FAILED (357 checks, 49.2 s) | FAIL BK7 3 crashes, a clean RESTART into new code (returns 3), then 4 crashes: no ATTENTION (exit 3 is clean too)  -> ([1, 1, 1], 3, [1, 0, 0, 0], Tru
M14c: CAUGHT rc=1 | 1 FAILED (357 checks, 49.4 s) | FAIL J5c _unseen: a key twice in the same list is kept once, a key already in runs.jsonl not at all  -> 2
M17a2: CAUGHT rc=1 | 1 FAILED (357 checks, 49.5 s) | FAIL J10b the journal raising at both waiting polls: adopt waits both polls, logs the failure, then scores the cycle from the lane profiles (returns T
X04b: CAUGHT rc=1 | 1 FAILED (357 checks, 49.1 s) | FAIL J1b one `known` set across three polls (as _run_batch keeps it): 0, then a-3 once, then 0; the journal holds each key once  -> (0, 1, 1, [(1, 'a-
X09b: CAUGHT rc=1 | 1 FAILED (357 checks, 49.2 s) | FAIL ST4c a `cycle` that is not an int: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the n
m13: CAUGHT rc=1 | 1 FAILED (357 checks, 49.5 s) | FAIL ST4b a dict with no `cycles`: FAULT today's load_state returns a dict that is not a state; guarded, with the backup's cycle 5 EQUAL to the newest
X10: CAUGHT rc=1 | 1 FAILED (357 checks, 49.0 s) | FAIL ST10 the real acquire_lock: the holder restores state.json from the backup; after the real release_lock the same tear is read from the backup in 
m05: CAUGHT rc=1 | 1 FAILED (357 checks, 49.4 s) | FAIL ST10 the real acquire_lock: the holder restores state.json from the backup; after the real release_lock the same tear is read from the backup in 
X13: CAUGHT rc=1 | 1 FAILED (357 checks, 49.6 s) | FAIL BK9 the 5th crash's ATTENTION write fails: loop() returns 1 (the retry, no traceback escapes), the log says so, and the count is NOT reset (5), s
X14: CAUGHT rc=1 | 1 FAILED (357 checks, 49.1 s) | FAIL ST11 `status` with state.json and its backup both unreadable: prints 'STATE UNREADABLE', the rest of the status, and returns 0  -> ("RAISED State
X17: CAUGHT rc=1 | 1 FAILED (357 checks, 49.3 s) | FAIL J3b a (lane, log) journaled twice: _journal_records returns it ONCE, the first line's record  -> [13750, 13000, -1]
X18: CAUGHT rc=1 | 2 FAILED (357 checks, 49.3 s) | FAIL R7b FAULT: an original that differs from the manifest (delete not started) -> originals kept, zip and manifest set aside  -> ['raw.manifest.json' || FAIL ST8b only the lane profile endless-ai0053-H1-mudkip proves cycle 53 started: the backup is refused, naming it, and state.json is left as it was  
X19: CAUGHT rc=1 | 1 FAILED (357 checks, 49.0 s) | FAIL T1 the repair forces BOTH writes onto the disk: the .bad file and the rewritten file (2 fsyncs)  -> 1
X23: CAUGHT rc=1 | 1 FAILED (357 checks, 49.3 s) | FAIL J1 a journaled game is never censored: a-2 (no Champion, no 5th derail) is journaled complete + usable, = lane_record(last_in_lane=False)  -> [(F
X24: CAUGHT rc=1 | 1 FAILED (357 checks, 49.2 s) | FAIL J13b journal_games with a half-written ARMS.json: returns 0, writes no games.jsonl, raises nothing  -> RAISED TypeError("'NoneType' object is not
X25b: CAUGHT rc=1 | 1 FAILED (357 checks, 49.2 s) | FAIL T3b exactly MAX_BAD_LINES (3) bad lines: repaired (the limit is 'more than'), all 3 moved to runs.jsonl.bad, the good lines kept byte for byte  -
X29: CAUGHT rc=1 | 1 FAILED (357 checks, 49.4 s) | FAIL BK1 with auto_update OFF the crash handler never fetches (0 updates); the counter and ATTENTION.md are both written atomically (through _atomic_w
X30: CAUGHT rc=1 | 1 FAILED (357 checks, 49.3 s) | FAIL J7 run_cycle writes arms.json, plan.json and state.json (+ its backup) atomically (through _atomic_write)  -> ['plan.json', 'state.json', 'state.
X31: CAUGHT rc=1 | 1 FAILED (357 checks, 48.9 s) | FAIL BK8 three crashes: count 1,2,3; `first` stays the first crash's time, `last` and `last_error` move on; each count is written atomically (3 crashe
X33: CAUGHT rc=1 | 1 FAILED (357 checks, 49.3 s) | FAIL BK8 three crashes: count 1,2,3; `first` stays the first crash's time, `last` and `last_error` move on; each count is written atomically (3 crashe
m12: CAUGHT rc=1 | 1 FAILED (357 checks, 49.2 s) | FAIL J12b a log modified 3 s before ARMS.json `started` (within collect_logs' 5 s) is journaled and recovered  -> (False, False)
F4: CAUGHT rc=1 | 1 FAILED (357 checks, 49.1 s) | FAIL J14 the recovery failed (0 runs recorded): games.jsonl is kept byte for byte as games.jsonl.kept and the log says so; CONTROL J4/J7: a journal wh
control-2: CONTROL rc=0 | ALL PASS (357 checks, 49.4 s) | 
TALLY on index tree 4daf192f1b53c2f8879702a006f94e1b7165de0d: 27 mutants {'CAUGHT': 27}; controls CONTROL-OK, CONTROL-OK
finished 2026-10-28 01:55:12 PM
```

**The harness (`harness_main.py`), verbatim:**

```python
"""Re-run the E2 + O8 fix round's 27 mutants (`scratchpad/e2o8fix/muts.py`, unchanged) SERIALLY on the code that is
STAGED on `main` -- the exact code of the item's commit -- because the fix round's saved results.txt shows X31 SURVIVED
and no saved row shows it caught after BK8 was tightened (Tier 1 finding (c)1, 2026-10-28).

usage: py -3.12 -I harness_main.py
  1. `git write-tree` (index -> a tree object; changes no ref, no index entry) and `git archive` of that tree's
     tools/, sandbox-pokebot/ and root files into base/ (tracked content only), plus an empty base/.git so P1 runs;
  2. a CONTROL run of the unmutated ai-agent/ from the same tree, then each mutant in a fresh copy, then a CONTROL again;
  3. prints one row per run (the fix round's own row format) and a final tally line.
The verdict rule is the fix round's: CAUGHT = any FAIL line, a non-zero exit or a crash; SURVIVED = ALL PASS.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
MUTS_DIR = HERE.parent.parent / "e2o8fix"
BASE = HERE / "base"
SRC = HERE / "src-ai-agent"


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(MAIN), *args], input=data, capture_output=True, check=True).stdout


def extract(tree: str, paths: list[str], dest: Path) -> int:
    tar = git("archive", "--format=tar", tree, "--", *paths)
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        tf.extractall(dest, filter="data")
        return len(tf.getmembers())


def setup() -> str:
    tree = git("write-tree").decode().strip()
    for d in (BASE, SRC):
        if d.exists():
            shutil.rmtree(d)
    BASE.mkdir(parents=True)
    (BASE / ".git").mkdir()
    roots = [ln for ln in git("ls-tree", "--name-only", tree).decode("utf-8").splitlines()
             if git("cat-file", "-t", f"{tree}:{ln}").decode().strip() == "blob"]
    n = extract(tree, ["tools", "sandbox-pokebot", *roots], BASE)
    tmp = HERE / "_src"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    extract(tree, ["ai-agent"], tmp)
    shutil.move(str(tmp / "ai-agent"), str(SRC))
    shutil.rmtree(tmp)
    print(f"setup: index tree {tree}; base/ has {n} archive entries (tools, sandbox-pokebot, {len(roots)} root files); "
          f"src-ai-agent/ has {sum(1 for _ in SRC.rglob('*') if _.is_file())} files", flush=True)
    return tree


def run_one(name: str, mut: dict | None) -> str:
    d = BASE / "ai-agent"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(SRC, d)
    if mut is not None:
        f = d / mut.get("file", "learner.py")
        t = f.read_text(encoding="utf-8")
        n = t.count(mut["old"])
        if n != 1:
            row = f"{name}: BAD ANCHOR count {n}"
            print(row, flush=True)
            return "BAD"
        f.write_text(t.replace(mut["old"], mut["new"]), encoding="utf-8")
        compile(f.read_text(encoding="utf-8"), str(f), "exec")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run([sys.executable, "-B", "test_agent.py"], cwd=d, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        out, rc = r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        out, rc = "TIMEOUT", -9
    fails = [ln for ln in out.splitlines() if ln.startswith("FAIL ")]
    tail = [ln for ln in out.splitlines() if "PASS (" in ln or "FAILED (" in ln]
    crashed = "Traceback (most recent call last)" in out and not tail
    verdict = "CONTROL" if mut is None else ("CAUGHT" if fails or rc != 0 or crashed else "SURVIVED")
    print(f"{name}: {verdict} rc={rc} | {tail[-1] if tail else '(no summary)'} | "
          + " || ".join(x[:150] for x in fails)[:900], flush=True)
    if crashed:
        print(out[-1500:], flush=True)
    return verdict if mut is not None else ("CONTROL-OK" if rc == 0 and not fails and tail else "CONTROL-BAD")


def main() -> None:
    print("started", datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"), flush=True)
    tree = setup()
    sys.path.insert(0, str(MUTS_DIR))
    from muts import MUTS
    print(f"mutants: {len(MUTS)} from {MUTS_DIR / 'muts.py'}", flush=True)
    results = {"control-1": run_one("control-1", None)}
    for name, mut in MUTS.items():
        results[name] = run_one(name, mut)
    results["control-2"] = run_one("control-2", None)
    muts = {k: v for k, v in results.items() if not k.startswith("control")}
    tally = {v: sum(1 for x in muts.values() if x == v) for v in sorted(set(muts.values()))}
    print(f"TALLY on index tree {tree}: {len(muts)} mutants {tally}; controls {results['control-1']}, "
          f"{results['control-2']}", flush=True)
    print("finished", datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"), flush=True)


if __name__ == "__main__":
    main()
```

## 9. A flaky archive check found by that re-run (R7b): measured, and nothing lost (added 2026-10-28)

**Seen:** §8's X18 row fails R7b (O3's "an original that differs from the manifest", 2026-10-21) besides its own
ST8b. X18 does not touch the archive code. Two X18-only re-runs: R7b PASS, ST8b FAIL (below). E2 + O8 changes none of
`_in_use`, `QUIET_MINUTES`, R7b or `make_raw_cycle` (`git diff --cached`), so the flake predates it.

**First explanation, REFUTED:** a file lock on the fresh zip outlasting the sandbox's 0.01 s rename wait. A loop of
R7b's own steps failed with production's 2.0 s wait (1 of 300) and not with the test's (0 of 300).

**Root cause, measured:** the failing iteration's FIRST prune never archived the cycle and logged no error; the
second prune then archived the CHANGED original (the zip holds the appended line), verified it and deleted the
originals, so the test's "set aside" path never ran. `O3Sandbox` sets `QUIET_MINUTES = 0`, so `_in_use`'s cutoff
is `time.time()`, which on Python 3.12 is the 15.6 ms system clock: a just-written file's mtime read LATER than it in
2633 of 20000 writes. Instrumenting the action (`_in_use`'s verdict in the first prune), 1500 iterations: 17 FAIL, every one
with a BUSY first prune ("... modified within the last 0 min"); BUSY in 17 iterations in all.

**Rate:** 1 of 31 serial suite runs today; 18 of 2100 loop runs. **Impact:** test-only (production's
`QUIET_MINUTES` is 60) and nothing is lost; but the deploy gate runs this suite, so it joins R15 in KI-127.

**X18 alone, twice (`x18_twice.py`):**

```text
--- X18 run 1: rc=1
    [2026-10-28 01:56:29 PM] prune FAILED (nothing more is archived this boundary; the next one retries):
    [2026-10-28 01:56:30 PM] prune FAILED (nothing more is archived this boundary; the next one retries):
    PASS R7 setup: a crash after the rename leaves raw.zip + manifest + the originals, not flagged
    PASS R7 raw.zip + originals -> re-verified against them, then the originals deleted
    PASS R7 FAULT: a CORRUPT raw.zip + manifest + all originals -> originals kept, zip AND manifest set aside as .bad.1
    PASS R7 CONTROL: the next prune re-archives the kept originals correctly
    PASS R7b FAULT: an original that differs from the manifest (delete not started) -> originals kept, zip and manifest set aside
    PASS R7c setup: a crash after the rename leaves raw.zip with NO manifest beside every original
    PASS R7c FAULT: no manifest + a zip with a corrupt member -> every original kept, the zip set aside as raw.zip.bad.1 byte-intact, nothing flagged
    PASS R7c FAULT: no manifest + a zip with a missing member -> every original kept, the zip set aside as raw.zip.bad.1 byte-intact, nothing flagged
    PASS R7c CONTROL: no manifest + a zip that matches the originals exactly -> manifest written, then deleted
    PASS R7c CONTROL: the next prune archives the set-aside cycles afresh; the .bad.1 files stay byte-intact
    PASS ST8 FAULT: without the runs check a STALE backup (cycle 47 while runs/ai0053 exists) is restored
    PASS ST8 a stale backup is refused: StateUnreadable names '47' and 'ai0053', and nothing is renamed or rewritten
    PASS ST8b FAULT: reading runs/ alone, a stale backup (cycle 47) is restored when only endless-ai0053-* is left
    FAIL ST8b only the lane profile endless-ai0053-H1-mudkip proves cycle 53 started: the backup is refused, naming it, and state.json is left as it was  -> ({'cycle': 47, 'cycles': [{'tag': 'ai0005'}], 'current': None, 'failures': 0, 'parser_version': 4, 'design_next': 3}, False)
    1 FAILED (357 checks, 49.5 s)
--- X18 run 2: rc=1
    [2026-10-28 01:57:19 PM] prune FAILED (nothing more is archived this boundary; the next one retries):
    [2026-10-28 01:57:19 PM] prune FAILED (nothing more is archived this boundary; the next one retries):
    PASS R7 setup: a crash after the rename leaves raw.zip + manifest + the originals, not flagged
    PASS R7 raw.zip + originals -> re-verified against them, then the originals deleted
    PASS R7 FAULT: a CORRUPT raw.zip + manifest + all originals -> originals kept, zip AND manifest set aside as .bad.1
    PASS R7 CONTROL: the next prune re-archives the kept originals correctly
    PASS R7b FAULT: an original that differs from the manifest (delete not started) -> originals kept, zip and manifest set aside
    PASS R7c setup: a crash after the rename leaves raw.zip with NO manifest beside every original
    PASS R7c FAULT: no manifest + a zip with a corrupt member -> every original kept, the zip set aside as raw.zip.bad.1 byte-intact, nothing flagged
    PASS R7c FAULT: no manifest + a zip with a missing member -> every original kept, the zip set aside as raw.zip.bad.1 byte-intact, nothing flagged
    PASS R7c CONTROL: no manifest + a zip that matches the originals exactly -> manifest written, then deleted
    PASS R7c CONTROL: the next prune archives the set-aside cycles afresh; the .bad.1 files stay byte-intact
    PASS ST8 FAULT: without the runs check a STALE backup (cycle 47 while runs/ai0053 exists) is restored
    PASS ST8 a stale backup is refused: StateUnreadable names '47' and 'ai0053', and nothing is renamed or rewritten
    PASS ST8b FAULT: reading runs/ alone, a stale backup (cycle 47) is restored when only endless-ai0053-* is left
    FAIL ST8b only the lane profile endless-ai0053-H1-mudkip proves cycle 53 started: the backup is refused, naming it, and state.json is left as it was  -> ({'cycle': 47, 'cycles': [{'tag': 'ai0005'}], 'current': None, 'failures': 0, 'parser_version': 4, 'design_next': 3}, False)
    1 FAILED (357 checks, 49.5 s)
```

**R7b's own steps, 300 per arm (`r7b_loop.py`; summary and failure lines):**

```text
ARM A (test, 0.01 s): 0 FAIL of 300 (79 s)
  B (production, 2.0 s) iteration 223: FAIL {'after_prune1': ['batch'], 'after_prune2': ['raw.manifest.json', 'raw.zip'], 'batch_survived': False, 'a1_appended_in_zip': {'raw.zip': True}, 'c1': {'archived': True, 'pruned': True, 'held': None}, 'prune1_exc': [], 'prune2_exc': []}
ARM B (production, 2.0 s): 1 FAIL of 300 (80 s)
```

**The clock (`clock_probe.py`):**

```text
python 3.12.4; time.time(): GetSystemTimeAsFileTime(), resolution 0.015625
mtime LATER than time.time() read after the write: 2633 of 20000 writes; worst lead 0.000 ms
```

**The instrumented loop, 1500 iterations (`r7b_instrumented.py`; summary and every iteration it printed):**

```text
  iteration 231: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 614: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 735: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 759: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 776: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', -0.01610565185546875)]
  iteration 812: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 827: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 885: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 897: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', -0.013825416564941406)]
  iteration 982: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', -0.015877485275268555)]
  iteration 1136: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', -0.015757322311401367)]
  iteration 1262: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 1294: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 1298: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 1399: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', -0.015744924545288086)]
  iteration 1415: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/debug-logs/big.log was modified within the last 0 min', 2.384185791015625e-07)]
  iteration 1432: FAIL; ai0001's first-prune _in_use: [('ai0001', 'profiles/endless-ai0001-H1-torchic/badge-log.json was modified within the last 0 min', 2.384185791015625e-07)]
R7b x 1500: 17 FAIL, of which 17 had a BUSY first prune; the first prune called ai0001 BUSY in 17 iterations in all (388 s)
```

**The three scripts, verbatim:**

```python
"""R7b in a loop, with the suite's OWN helpers, on a fresh UNMUTATED copy of the committed ai-agent/ (src-ai-agent/,
from index tree 4daf192f): how often does it fail, and when it fails, is anything LOST?
  arm A: R7b exactly as the suite runs it (O3Sandbox: REPLACE_WAIT_S = 0.01 s, 5 tries)
  arm B: the same with production's REPLACE_WAIT_S (2.0 s)
Per failure: d1's listing, whether batch/ survived, whether ANY raw.zip* holds the appended line (no loss), c1's flags,
and the exception lines the two prunes logged.
usage: py -3.12 -I r7b_loop.py N"""
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src-ai-agent"
D = HERE / "base" / "ai-agent"  # harness_main's scratch base (tools/, sandbox-pokebot/, .git), refreshed UNMUTATED
if D.exists():
    shutil.rmtree(D)
shutil.copytree(SRC, D)
os.chdir(D)
sys.path.insert(0, str(D))
import test_agent as T  # noqa: E402  (main() is guarded)

learner = T.learner
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
APPENDED = b"one more line written after the archive\n"
keep1 = {"keep_raw_cycles": 1, "max_archives_per_prune": 3}  # test_o3_archive's keep1
tmp_all = Path(tempfile.mkdtemp(prefix="r7b-loop-")).resolve()
T.GLOBAL_ROOT = tmp_all / "global"
T.patch_learner_paths(T.GLOBAL_ROOT)


def exc_lines(text: str) -> list[str]:
    return [ln.strip()[:200] for ln in text.splitlines()
            if ln and not ln.startswith((" ", "\t", "Traceback", "[")) and ("Error" in ln or "Exception" in ln)]


def one(tmp: Path, wait: float) -> tuple[bool, dict]:
    with T.O3Sandbox(tmp):
        learner.REPLACE_WAIT_S = wait
        c1, c2 = T.make_raw_cycle(tmp, "ai0001"), T.make_raw_cycle(tmp, "ai0002")
        real_delete = learner._delete_ours
        learner._delete_ours = lambda c: (_ for _ in ()).throw(RuntimeError("simulated crash before the delete"))
        learner.prune(keep1, {"cycles": [c1, c2]})
        learner._delete_ours = real_delete
        log1 = learner.LOG.read_text(encoding="utf-8") if learner.LOG.exists() else ""
        d1 = learner.RUNS / "ai0001"
        after1 = sorted(p.name for p in d1.iterdir())
        with open(d1 / "batch" / "L01" / "debug-logs" / "a-1.log", "ab") as fh:
            fh.write(APPENDED)
        changed = T.raw_view(tmp, "ai0001")
        learner.prune(keep1, {"cycles": [c1, c2]})
        log2 = (learner.LOG.read_text(encoding="utf-8") if learner.LOG.exists() else "")[len(log1):]
        ok = (T.raw_view(tmp, "ai0001") == changed and (d1 / "raw.zip.bad.1").exists()
              and (d1 / "raw.manifest.json.bad.1").exists() and not c1.get("pruned"))
        info = {}
        if not ok:
            holds = {}
            for z in sorted(d1.glob("raw.zip*")):
                try:
                    with zipfile.ZipFile(z) as zf:
                        holds[z.name] = any(APPENDED in zf.read(n) for n in zf.namelist() if n.endswith("a-1.log"))
                except Exception as exc:  # noqa: BLE001
                    holds[z.name] = f"unreadable: {type(exc).__name__}"
            info = {"after_prune1": after1, "after_prune2": sorted(p.name for p in d1.iterdir()),
                    "batch_survived": (d1 / "batch").exists(), "a1_appended_in_zip": holds,
                    "c1": {k: c1.get(k) for k in ("archived", "pruned", "held")},
                    "prune1_exc": exc_lines(log1), "prune2_exc": exc_lines(log2)}
        return ok, info


for arm, wait in (("A (test, 0.01 s)", 0.01), ("B (production, 2.0 s)", 2.0)):
    fails, t0 = [], time.time()
    for i in range(N):
        tmp = tmp_all / f"{arm[0]}{i:03d}"
        try:
            ok, info = one(tmp, wait)
        except Exception as exc:  # noqa: BLE001
            ok, info = False, {"crash": repr(exc)}
        if not ok:
            fails.append((i, info))
            print(f"  {arm} iteration {i}: FAIL {info}", flush=True)
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"ARM {arm}: {len(fails)} FAIL of {N} ({time.time() - t0:.0f} s)", flush=True)
shutil.rmtree(tmp_all, ignore_errors=True)
```

```python
"""Does a file written JUST NOW get an mtime LATER than time.time() read right after the write (Python 3.12, Windows)?
If yes, `_in_use` with QUIET_MINUTES = 0 (cutoff = time.time()) can call a quiet cycle busy, by clock granularity."""
import sys
import tempfile
import time
from pathlib import Path

d = Path(tempfile.mkdtemp(prefix="clock-probe-"))
f = d / "x.log"
N = 20000
later = 0
worst = 0.0
for i in range(N):
    f.write_bytes(b"x" * 64)
    now = time.time()
    m = f.stat().st_mtime
    if m > now:
        later += 1
        worst = max(worst, m - now)
f.unlink()
d.rmdir()
info = time.get_clock_info("time")
print(f"python {sys.version.split()[0]}; time.time(): {info.implementation}, resolution {info.resolution}")
print(f"mtime LATER than time.time() read after the write: {later} of {N} writes; worst lead {worst * 1000:.3f} ms")
```

```python
"""R7b in a loop (the suite's own helpers, the committed code, O3Sandbox exactly as the suite runs it), with the ACTION
instrumented: `_in_use`'s verdict for ai0001 in the FIRST prune, and its newest original's mtime minus the cutoff.
A failing iteration whose first-prune verdict is "... modified within the last 0 min" proves the clock-granularity skip.
usage: py -3.12 -I -B r7b_instrumented.py N"""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE / "base" / "ai-agent"
if D.exists():
    shutil.rmtree(D)
shutil.copytree(HERE / "src-ai-agent", D)
os.chdir(D)
sys.path.insert(0, str(D))
import test_agent as T  # noqa: E402

learner = T.learner
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
keep1 = {"keep_raw_cycles": 1, "max_archives_per_prune": 3}
tmp_all = Path(tempfile.mkdtemp(prefix="r7b-instr-")).resolve()
T.GLOBAL_ROOT = tmp_all / "global"
T.patch_learner_paths(T.GLOBAL_ROOT)
real_in_use = learner._in_use
calls: list[tuple[str, str | None, float]] = []


def spy(tag, cdir, originals, cmds):
    why = real_in_use(tag, cdir, originals, cmds)
    lead = max((f.stat().st_mtime for f in originals.values()), default=0.0) - time.time()
    calls.append((tag, why, lead))
    return why


fails, busy_first, t0 = [], 0, time.time()
for i in range(N):
    tmp = tmp_all / f"i{i:04d}"
    with T.O3Sandbox(tmp):
        learner._in_use = spy
        try:
            c1, c2 = T.make_raw_cycle(tmp, "ai0001"), T.make_raw_cycle(tmp, "ai0002")
            real_delete = learner._delete_ours
            learner._delete_ours = lambda c: (_ for _ in ()).throw(RuntimeError("simulated crash before the delete"))
            calls.clear()
            learner.prune(keep1, {"cycles": [c1, c2]})
            first = [c for c in calls if c[0] == "ai0001"]
            learner._delete_ours = real_delete
            d1 = learner.RUNS / "ai0001"
            with open(d1 / "batch" / "L01" / "debug-logs" / "a-1.log", "ab") as fh:
                fh.write(b"one more line written after the archive\n")
            changed = T.raw_view(tmp, "ai0001")
            learner.prune(keep1, {"cycles": [c1, c2]})
            ok = (T.raw_view(tmp, "ai0001") == changed and (d1 / "raw.zip.bad.1").exists()
                  and (d1 / "raw.manifest.json.bad.1").exists() and not c1.get("pruned"))
        finally:
            learner._in_use = real_in_use
    was_busy = bool(first) and first[0][1] is not None
    busy_first += was_busy
    if not ok:
        fails.append((i, was_busy))
        print(f"  iteration {i}: FAIL; ai0001's first-prune _in_use: {first}", flush=True)
    elif was_busy:
        print(f"  iteration {i}: pass, but the first prune called ai0001 BUSY: {first}", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
print(f"R7b x {N}: {len(fails)} FAIL, of which {sum(b for _, b in fails)} had a BUSY first prune; the first prune "
      f"called ai0001 BUSY in {busy_first} iterations in all ({time.time() - t0:.0f} s)", flush=True)
shutil.rmtree(tmp_all, ignore_errors=True)
```
