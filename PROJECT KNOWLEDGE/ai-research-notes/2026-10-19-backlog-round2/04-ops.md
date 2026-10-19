# Backlog round 2, angle 4: the 24/7 bot tuner and the PC (operations) (2026-10-19)

A NOTE, not a decision, and not a source of truth (see `00-READ-THIS-FIRST.md`). Candidates for the user and Claude to
rank. Nothing in the clone or the repo was changed to produce it; every number below was read from the live clone
(`C:/Remote Projects/pokebot-learner/ai-agent`), the Windows event log or the code, on 2026-10-19.

- **Read for this note:** `ai-agent/README.md`, `learner.py` (loop, guards, prune), `consult.py`, `config.json`,
  `data/runs.jsonl` (2,293 learner-cycle runs), `data/cycles.jsonl`, `data/consult_log.jsonl`, the last 200 log
  lines, `findings/DEVELOPER-NOTES.md`, the scheduled-task settings, and the System event log.
- **Not repeated from `2026-10-18-improvement-backlog.md` or `#28-trainer-improvements`:** per-game recording (E2),
  the consult cap, successive halving, a heartbeat and stuck-lane detector, experience records (A6), the daily
  summary, one temp-folder factory (B4), a status script (A1). Where an item below sharpens one of those, it says so.
- **Priorities:** A = high value per token, B = correctness, C = nice to have.

## What the data says first (the facts the items rest on)

1. **The "25 % of games cut off" is not luck. It is exactly one game per lane per cycle.**
   - In every cycle checked, `runs - usable == lanes`: ai0034 50-38 = 12 (12 lanes), ai0033 57-45 = 12, ai0032
     54-42 = 12, ai0030 49-37 = 12, ai0029 45-37 = 8 (8 lanes), ai0028 30-22 = 8, ai0027 and ai0026 55-39 = 16 (16
     lanes), ai0014 65-49 = 16.
   - Overall: 544 of 2,293 runs (23.7 %) were not usable; 380 of those 544 carry the last-derail label "unreachable
     target" and 88 "no derail recorded" (they were simply still playing).
2. **The clone's disk is steady; the PC's disk is not.** The learner keeps about 23 GB (`runs/` 16 GB plus lane
   profiles 6.9 GB), about 1.4 GB per cycle (the README says "about 4 GB"). Drive C: is 1,782 of 1,861 GB used (96 %),
   79 GB free. Nothing records disk over time.
3. **The 2026-10-17 "power cut" is only partly known.** The System log shows an UNEXPECTED shutdown at 6:50:03 AM
   (events 41 and 6008), a boot at about 3:55 PM, two restarts started by Windows servicing (`TrustedInstaller`, 3:56
   and 3:57 PM), and the learner back at 4:00:28 PM. The PC was down about 9 hours. Power loss and a crash look the
   same from here.
4. **CPU load with 12 lanes is 38 %** (4-second sample: 37.9 % of 32 threads; RAM 11 %). The PC is not maxed.
5. **The raw logs are almost all text and compress about 37 to 1** (three `stdout.txt` files: 247 MB to 7 MB). A
   whole retained cycle is 1.37 GB, of which 812 MB is `.txt` and 558 MB is `.log`.
6. **The consult stopped saying anything new about a week ago.** `DEVELOPER-NOTES.md` is 34,481 bytes in 31 entries;
   the entries from 2026-10-11 to 10-19 restate one message (knobs are exhausted; Tate & Liza / KI-122; ball supply;
   the League basket), and `CLAUDE.md` tells every session to read that file first.

---

## A. Highest value per token

**O1. An INDEPENDENT WATCHDOG that tells the user, with no Claude session.** (A)
- **Evidence:**
  - `ATTENTION.md`, the pause on disk below 25 GB and the pause after 3 empty cycles all end in a FILE inside the
    clone (`learner.py` `attention()`); the user learns of them only when a Claude session runs `status`, which
    spends usage.
  - `run_agent.ps1` stops for good on exit codes 0 and 2, and the autostart task has `RestartCount 0`, a logon
    trigger only, and runs a `-NoExit` PowerShell window; closing that window ends the loop.
  - ⇒ A dead or paused learner cannot report that it is dead. The planned daily summary (item 9) lives inside the
    learner, so it dies with it.
- **What:** a second tiny scheduled task, every 30 minutes, that is NOT the learner and needs only PowerShell. It
  checks: process alive, `learner.log` last-write age (over 13 hours means stuck), `ATTENTION.md`, disk, "Windows
  restart pending". It writes one file the user can open, `Desktop\LEARNER-STATUS.txt`, whose first line is `OK` or
  `NEEDS YOU: <reason>`, and raises a Windows notification only when the state CHANGES.
- **Benefit:** a health check costs the user a glance, not a Claude turn. **Cost:** about 80 lines and one task.
  **Risk:** none for the learner (read-only); alert fatigue is avoided by notifying on change only.
- **Sharpens:** A1 (a status script needs a session; this is push-based and session-free).

**O2. The cut-off is structural, so the first fix is a CONFIG change: longer cycles (after E2).** (A)
- **Evidence:** fact 1. Discarding exactly `lanes` games a cycle is a constant cost per cycle, so the share falls as
  the cycle lengthens. Per lane, a 12-hour cycle plays about 4.2 games and discards 1.
- **What:**
  - Step 1: `cycle_minutes` 720 to 1440 (read every cycle, no restart). Estimated: cut share 24 % to about 12 %, and
    usable games per day about 76 to 88 (+16 %), for the same power. This assumes game lengths stay as they are.
  - Do it WITH or AFTER E2 (per-game recording), because a power cut then costs up to 24 hours otherwise.
  - Honest trade: half as many new strategies tested per day (3 a day instead of 6), twice as many runs per strategy;
    a plateaued ranking loses little. It also halves consult calls and auto-update points (that saves usage).
- ⛔ **Do not "stop starting games that cannot finish":** that turns each discarded game into an idle lane. The
  usable count is unchanged. It saves only power. Only longer cycles, or a lane that carries its game across the
  boundary, gain games.
- **Cost:** one config line and a watch; **Risk:** the cadence change, and the larger power-cut exposure without E2.
- **Sharpens:** `#28-trainer-improvements` item 2 (the cause and the cheap lever were not named).

**O3. COMPRESS the raw logs instead of deleting them, and do it before the next prune.** (A)
- **Evidence:** facts 2 and 5. `prune()` keeps 12 cycles and deletes the rest: the log shows ai0001 to ai0022 already
  gone and one more lost every 12 hours (`pruned the raw logs of ai0022`, 2026-10-19 04:03 AM). The `config.json`
  note "12 keeps every raw log until the next interactive session" is stale: it is a rolling 6-day window.
  Those logs are the raw material of the experience records (A6, USER RULING 41); a pruned cycle cannot be mined later.
- **What:** `prune()` gzips each cycle's `.txt` and `.log` files into one archive per cycle, verifies it (read back,
  length check), and only then removes the originals. Estimated 40 to 60 MB per cycle, so ALL future cycles can be
  kept for under 2 GB a month, and the current 12 retained cycles shrink from 16 GB to well under 1 GB (about 15 GB
  freed). The `.gz` of the oldest cycles is the input A6 reads.
- **Cost:** about 30 lines and one fault test (a kill mid-gzip must leave the originals intact). **Risk:** low if the
  original is removed only after verification. The `.log` files were not measured; the `stdout.txt` ratio was.
- **Interim, no code:** `keep_raw_cycles` 12 to 20 costs about 11 GB of the 79 GB free. Compression is better.

**O4. BACK UP the learner's irreplaceable data off the C: drive.** (A)
- **Evidence:** the project rule is "nothing may exist only on this machine" (`CLAUDE.md`, wrap-up). `data/`
  (`runs.jsonl` 8.9 MB, `state.json`, `cycles.jsonl`, `consult_log.jsonl`) and `findings/` are git-ignored, so the
  record of all 2,371 games (the teacher's whole corpus, and the input of USER RULING 41) exists once, on a drive that
  is 96 % full.
- **What:** one nightly job: zip `data/` and `findings/` (estimated 2 to 3 MB) to `E:` (47 GB free) and keep the
  newest 14; plus, weekly, `learner.py publish` and a commit of the published snapshot with explicit paths, so the
  repo holds a cloud-safe copy.
- **Benefit:** a disk failure or a bad edit cannot erase 5 weeks of games. **Cost:** a small script and one task.
  **Risk:** none (copies only). Never write to `E:` if free space is under 10 GB.

**O5. A NOVELTY GATE on the consult, and a rolling developer-notes file.** (A)
- **Evidence:** fact 6, and `consult.py` `maybe_consult()`: its only guards are the daily cap and the waiting-proposal
  cap. 16 consecutive notes say the same thing, each call costs 20 to 29 seconds of a Claude session reading
  `README.md`, `LATEST.md`, `05-KNOWN-ISSUES.md` and the decision-points map, and the notes file grows about 1.1 KB
  per call, so every session start pays about 9,000 tokens now and more tomorrow.
  - Proposals are served oldest first (`read_inbox`: sorted by modification time), so 7 are waiting (the oldest,
    `claude-ai0028-2`, written 2026-10-16) and each is run 3 to 4 days after the ranking it was written against.
- **What:**
  - Skip the call unless a cheap local digest changed since the last consult: the top-3 genome ids, the wall shares
    rounded to 2 points, and the count of new scored runs (at least 40).
  - Before appending a note, compare its key terms (KI ids, wall names) to the last 3; if they overlap, append one
    line, "unchanged since <date>, <N> consults", not a paragraph.
  - Keep the newest 5 notes in `DEVELOPER-NOTES.md` and move older ones to an archive file; expire a proposal older
    than 3 days and drop one whose knob set equals a waiting one.
  - A forced consult once a week, so a real change cannot hide.
- **Benefit:** about one call a day saved, and a notes file a session reads in about 1,500 tokens instead of 9,000.
  **Cost:** small. **Risk:** missing a real change, bounded by the weekly forced call and the 40-run rule.
- **Sharpens:** C1 and `#28-trainer-improvements` item 3 (only the count cap shipped; priority, expiry and
  duplicates did not).

**O6. An OPS LEDGER row per cycle: the foundation for forecasting, reports and diagnosis.** (A)
- **Evidence:** `cycles.jsonl` rows hold only `source, tag, finished, exit, lanes, runs, usable, arms_label,
  code_commit, pruned`. No start time, no disk, no CPU, no consult time, no boot time. Because of that, the disk
  fall of 81 to 58 GB in one day cannot be reconstructed from any file, and "did a development session slow the
  lanes?" cannot be answered.
- **What:** add per cycle: `started`, `minutes`, `free_gb_start/end`, `learner_gb`, `cpu_avg`, `frames_per_lane_sec`,
  `consult_seconds`, `boot_time`, `downtime_minutes`. All read from `psutil` and file sizes at points the loop already
  passes.
- **Benefit:** O1, O7, O9 and the weekly report all read it. **Cost:** small; **Risk:** none.

**O7. DISK FORECAST plus a mid-cycle guard (detect, where B4 prevents).** (A)
- **Evidence:** fact 2, and `learner.py` `loop()`: `free_gb() < min_free_gb` is tested once per cycle, 12 hours
  apart. The drop of 81 to 58 GB (and the 24.3 GB of temp folders left by step 5.2) came from OUTSIDE the learner. A
  disk that fills mid-cycle corrupts the games in flight, and the first sign is a paused learner a day later.
- **What:** the O1 watchdog samples free GB every 30 minutes and states the trend: "79 GB free; falling 6 GB/day;
  25 GB in 9 days" in `LEARNER-STATUS.txt`. At under 40 GB free, or a fall of over 10 GB in 6 hours, it writes
  `NEEDS YOU` and the learner (on its next boundary) prunes to `keep_raw_cycles 2` BEFORE the 25 GB floor, not after.
  Correct the README figure of 4 GB a cycle.
- **Benefit:** the user sees a slope, not a surprise. **Cost:** small given O1 and O6. **Risk:** none.
- **Sharpens:** B4 (a factory prevents the leak; nothing detects the next one).

## B. Correctness

**O8. TORN-WRITE RESILIENCE: a power cut mid-write must not turn into a silent crash loop.** (B)
- **Evidence (from reading the code; not reproduced):**
  - `load_jsonl()` (`learner.py` line 118) and `load_state()` (line 137) call `json.loads` with no `try`.
  - `append_jsonl()` is a plain append with no flush or fsync, and `save_state()` replaces a temp file without an
    fsync.
  - One truncated last line in `runs.jsonl` or an empty `state.json` would make `finish_cycle` or the startup raise.
    `run_agent.ps1` then waits 10 minutes and tries again FOREVER, with no counter and no `ATTENTION.md`.
  - The 2026-10-17 unclean shutdown recovered only because nothing was being written at that moment.
- **What:** skip and log an unparsable line (keep it in a `.bad` file); keep `state.json.bak`; fsync before the
  replace; cap the wrapper's crash retries at 5, then write `ATTENTION.md`. Fault tests (the project's own standard):
  a truncated last line, a zero-byte `state.json`, a crash at start; each must end with the learner running or paused
  with a stated reason.
- **Cost:** small. **Risk:** low.

**O9. A BOT-CODE FINGERPRINT, a short smoke after an update, and a SAFE ROLLBACK.** (B)
- **Evidence:**
  - `code_commit` in the run records is the git commit, and it changes with every docs commit (ai0030 `dc6b476b`,
    ai0033 `226a70bd`, ai0034 `babad02e`), so no ranking can tell "same bot" from "docs changed".
  - `auto_update` applies any pushed commit between cycles with only `test_agent.py` (the learner's own offline
    tests) as a gate; a broken BOT commit is found only after 3 empty cycles, which is 36 hours and an `ATTENTION.md`
    pause (`max_consecutive_failures` 3).
  - ai0001 and ai0002 were 100 % unusable.
- **What:**
  - Record a `bot_fingerprint` per run (a hash of the files the batch actually imports) and bucket the ranking by it,
    with a warning when it changes.
  - After an update that changed the fingerprint, run a 1-lane, 10-minute smoke game BEFORE committing 12 lanes for
    12 hours. On failure, move the clone back with a detached switch to the last good commit (nothing is edited or
    discarded in a clone with no local changes), remember the bad commit so the next update skips it, and write
    `NEEDS YOU` through O1.
- ⚠ This adds a git verb to the learner; the rule "its only git is fetch plus fast-forward" needs a user ruling.
- **Cost:** medium. **Risk:** medium (a wrong rollback), so build it with a fault test (a deliberately broken commit).

**O10. A SENSITIVITY ROW for the discarded games (they are censored, not missing).** (B)
- **Evidence:** the game in flight at the deadline is, by construction, the longer kind (the inspection effect), and
  the ranking uses only usable runs. The 544 discarded games are not trivial: 333 reached 4 or more badges and 184
  reached 8 or more (the last log record: Ever Grande City, 8 badges, cut at the deadline). The cut share differs by
  starter: Treecko 27 % (n=706) against Torchic 21 % (n=835), about 2.7 standard errors apart, and Treecko is the
  starter with the best scores.
  - The cut share by genome is flat (19 to 27 %, n 30 to 120), so the effect on the CURRENT ranking is probably
    small. This is a check, not a known defect.
- **What:** `report.py` adds one row: the ranking with the cut games counted as "reached at least this far", and a
  line "top-3 order unchanged: yes/no". The fields already exist in the run record (`progress`, `score`).
- **Cost:** small. **Risk:** none. **Benefit:** a free answer to "is the 24 % hiding something?".

## C. Nice to have, or the user's call

**O11. A PLAIN-ENGLISH WEEKLY REPORT for the user, with a PLATEAU METER (also the energy question).** (B)
- **Evidence:** `LATEST.md` is a 12 KB table of genome ids, written for Claude. The ranking has been flat: the top
  12 genomes sit within 0.02 (consult note, 2026-10-15), the leaders' estimates run 0.380 to 0.408 with standard
  errors of 0.02 to 0.04, and Champion is 15 % of scored runs. The user needs one number to decide "keep running,
  redirect, or rest".
- **What:** `WEEKLY.md` (and the first lines of `LEARNER-STATUS.txt`): games this week, Champion trend, "the last time a
  strategy beat the leader by more than noise: <date>", downtime in hours, disk slope, and at most two decisions
  asked of the user. When the meter says "nothing new expected", it recommends one of: redirect lanes to experience
  coverage (C2), run fewer lanes, or pause until the AI player gives it something to test.
- **Energy:** nothing is measured in watts (no sensor on this PC). What is known: High performance plan, never sleep,
  38 % CPU, 20 of 32 threads idle. If the user wants numbers, a plug meter for one day settles it. Do not change the
  lane count on a guess; USER RULING 38 sets 12.
- **Cost:** small given O6. **Risk:** none. **Sharpens:** `#28-trainer-improvements` item 9 and C2.

**O12. A BOOT LEDGER, and a corrected incident record.** (C)
- **Evidence:** fact 3. The docs and the punch list call 2026-10-17 "a power cut"; the log proves only an unexpected
  shutdown. The autostart task has a logon trigger and `LogonType Interactive`, so it also needs the user logged
  in. Windows Update active hours are 5 AM to 10 PM, so an update restart is allowed from 10 PM to 5 AM, mid-cycle.
  No "restart pending" flag is set now (both registry keys are absent).
- **What:**
  - At each learner start, log the boot time and whether the last shutdown was unclean (`psutil.boot_time()` and the
    Kernel-Power 41 / 6008 events), and write "down from X to Y (N hours)" into O6's row.
  - Show "Windows restart pending: yes/no" in O1, so the user picks the moment, between cycles.
  - Amend `#28-trainer-improvements` item 1 to say "unexpected shutdown (cause unknown)".
- **User's choice, not code:** Windows Settings, Update, "Advanced options", pause updates before a long run.
  The BIOS and auto-login choices are already E3.
- **Cost:** small. **Risk:** none.

**O13. LANE SCHEDULING: fewer control lanes, and a feasibility probe for paired seeds.** (C)
- **Evidence:** arm A (the incumbent) takes 4 of 12 lanes every cycle, a third of the compute, although the incumbent
  has 37 to 61 runs and a standard error of 0.017 to 0.023. Run-to-run noise (0.02 to 0.04) is larger than most knob
  effects (0.01 to 0.03; "most effects are under 2 se", consult note 2026-10-12), and the ranking is plateaued.
- **What:**
  - Cheap: once the incumbent's standard error is under 0.02, run it on 4 lanes only every other cycle (one lane
    per starter) and give the freed 4 lanes to the screening design. This is the control-arm half of "successive
    halving" (item 4).
  - Probe first (small): can `x4_headless` pin the game's random seed, given that the game reads the host clock
    (KI-112)? If yes, run every arm of a cycle on the SAME seeds per starter (common random numbers), which cuts the
    variance of arm differences. If not, drop this half. No run record holds a seed today.
- **Cost:** a probe, then medium. **Risk:** medium (the control is what detects drift between cycles; keep a floor
  of one lane per starter every other cycle).

---

## Suggested order (Claude's call, for the lean phase)

1. **O3** (compress before the next prune; time-limited, because data is lost every 12 hours) and **O4** (backup),
   both a few lines and no risk.
2. **O6** (ledger), then **O1** and **O7** (watchdog and disk slope) on top of it: the user's glance replaces Claude's
   check-ins.
3. **O5** (novelty gate): saves usage on every session start and every consult.
4. **O8** and **O2** together with E2 (per-game recording), as one change set with fault tests: torn write, power cut
   mid-game, cycle length.
5. **O9**, **O10**, **O11**, **O12**, **O13** as the learner work in `#28-trainer-autonomy` allows. O9 needs a user
   ruling on the new git verb.

## Things I did NOT find to be problems (so nobody re-checks them)

- Cycle boundaries are tight: about 30 to 80 seconds between one batch ending and the next starting (consult, prune
  and update included), under 0.2 % of a cycle.
- The autostart works (`Pokebot-AI-Learner-Autostart`, state Running), `MultipleInstances IgnoreNew` and
  `ExecutionTimeLimit PT0S` are right, and the lock file protected a second start in the tests recorded in the README.
- `runs.jsonl` growth (about 3.8 KB a run, 0.4 MB a day) and `state.json` (68 KB) are not a storage concern.
- Lane sizing reads the PC each cycle and the config cap is the binding limit (12), not the hardware.
- Not checked: whether the `claude` CLI call in `consult.py` also loads the clone's `CLAUDE.md` despite
  `--setting-sources user` (if it does, every consult carries about 500 lines of rules it does not need; one test
  call would show it).
