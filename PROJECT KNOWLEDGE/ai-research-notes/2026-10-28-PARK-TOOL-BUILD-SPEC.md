> ✅ **BUILT 2026-10-28** as `tools/ops/park_tuner.py` (gate `tools/story-dev/selftest_park_tuner.py`). The build departs from this spec in ten places, listed in `2026-10-28-PARK-TOOL-BUILD-REPORT.md` section 8.3 (`06` 2026-10-28): where they differ, the code and its docstring win. This file is the spec as written.

# THE PARK TOOL: build spec (2026-10-28; USER RULING 50; `03` `#28-trainer-improvements` (10))

> Status: SPEC. Written by the orchestrating session for the build workflow. The finished tool replaces the manual
> PARK and RESUME steps in `04-HANDOFF.md` ("If stopped mid-task") and the scratch watcher whose source is
> `ai-research-notes/2026-10-28-PARK-EVIDENCE.md` section 5 (`park_watch.py`; also at
> `<scratch>/s53/park/park_watch.py`, the same bytes).

## 1. Why

USER RULING 50 (`06` 2026-10-28), the user's words: "I do want the safe pause/park feature in the event that I do want
to safely park/pause working on the program ... I do not want this to be paused/parked anymore until I say otherwise!"

So: a park or a resume must be ONE command that a future session runs on the user's word and that proves its own
result. Today a park is four manual steps plus a 40 KB scratch script, and a resume is five manual steps.

⛔ The tool never parks on its own, and nothing in the project may run `park --apply` unless the user asked for a park.
The tool's docstring says so.

## 2. The machine it acts on (measured 2026-10-28, read-only)

- The bot tuner runs from its deployment clone `C:/Remote Projects/pokebot-learner` (marker file `ai-agent/DEPLOYMENT`,
  git-ignored). Its data: `ai-agent/data/` (`learner.log`, `agent.lock` = the learner's PID as text, `state.json`,
  `cycles.jsonl`, `runs.jsonl`). The STOP file is `ai-agent/STOP` (git-ignored, `ai-agent/.gitignore:7`).
  `ai-agent/findings/ATTENTION.md` exists when the learner paused itself.
- `state.json` `current` while a round runs: `{"tag": "ai0054", "started": "2026-10-28 04:30:19 PM", "lanes": 12,
  "minutes": 720.0}`; `null` between rounds. `cycles` is the list of finished rounds (`{"tag": ...}` dicts).
- `learner.py` reads STOP only at the top of its loop (before `auto_update`): the running round finishes, is scored and
  recorded, then it logs `STOP file found: stopping (delete ai-agent/STOP to allow the next start)` and exits 0.
  With `ATTENTION.md` present it logs `<path> exists: not starting a cycle until it is resolved and deleted`.
  At start it logs `learner started (code <12 hex>)`; a round starts with `aiNNNN: starting N lanes for M minutes`.
  Log line format: `[YYYY-MM-DD hh:mm:ss AM] message`.
- `ai-agent/run_agent.ps1` loops: `if (Test-Path STOP) { break }`; learner exit 0 -> "Not restarting", break; other
  codes -> restart in 10 minutes. 
- The three Windows tasks (run as the user, no elevation needed to disable/enable; `Settings.Enabled` is the truth):
  - `Pokebot-AI-Learner-Autostart`: LogonTrigger; action `powershell.exe -NoExit -ExecutionPolicy Bypass -File
    "C:\Remote Projects\pokebot-learner\ai-agent\run_agent.ps1"`, working dir the clone's `ai-agent`;
    MultipleInstances IgnoreNew; no time limit. Because of `-NoExit` the window (and so the task's State "Running")
    stays after the learner exits; while it is open, `Start-ScheduledTask` is IGNORED.
  - `Pokebot-Ops-Watchdog` (every 30 min, read-only on the clone; it never restarts the learner).
  - `Pokebot-Ops-Backup` (1:00 AM nightly: `pyw -3.12 -B <clone>/tools/ops/backup_learner.py`; it writes
    `%LOCALAPPDATA%/pokebot-ops/backup_status.json` with `time` (TS format above), `ok`, `zip`, `bytes`, ...).
- The live process tree right now (Get-CimInstance Win32_Process), parent first:
  `powershell.exe -NoExit ... run_agent.ps1` (PID 10588) -> `"C:\Windows\py.exe" -3.12 learner.py run` (42712) ->
  `...\Python312\python.exe learner.py run` (5372, the PID in agent.lock) -> `...python.exe "C:\Remote
  Projects\pokebot-learner\tools\story-dev\x4_headless.py" --build sandbox --lanes 12 --minutes ...` (46944) -> 12 x
  `...python.exe "C:\Remote Projects\pokebot-learner\sandbox-pokebot\pokebot.py" endless-ai0054-H7-treecko -m
  "Story (ENDLESS..."`. Note the learner's own command line holds NO clone path.

## 3. What to build

`tools/ops/park_tuner.py`: Python 3.12, standard library only, Windows. Everything that touches the live machine goes
through ONE env object (`RealEnv`; tests use `FakeEnv`), exactly as `park_watch.py` does. Reuse `park_watch.py`'s
proven pieces where they fit (`_ps`, `RealEnv.pid_alive`, `task_enabled/disable/enable`, `run_backup`,
`last_stop_line`, `trainer_processes`, `pid_is_learner`, `check`, `watch`, `verify_backup`, the park order), and say
in a comment where each came from. Options common to every command: `--clone` (default
`C:/Remote Projects/pokebot-learner`) and `--ops-dir` (default `%LOCALAPPDATA%/pokebot-ops`), both for tests.

### 3.1 `status` (READ-ONLY, always safe)
One screen in plain English, times in 12-hour form (`4:30 PM`), first line the VERDICT:
- `RUNNING` (no STOP, the learner alive, the three tasks ON);
- `PARK PENDING` (STOP present and the learner still running its round; say when the round should end: `started` +
  `minutes`);
- `PARKED` (STOP present, nothing of the tuner runs, all three tasks OFF);
- `PARTLY PARKED` (STOP present, nothing runs, some task still ON: say which and what `park --apply` would still do);
- `STOPPED, NOT PARKED` (no STOP and nothing runs: name the reason found: ATTENTION.md's reason line, or the log's
  last lines; the tasks are ON so a logon restarts it);
- `INCONSISTENT` (anything else, e.g. a task OFF while the tuner runs without STOP): list the facts.
Then the details: the learner (lock PID; alive; still a learner), the round (tag, started, ends about), the lane
count (processes), STOP (present; its time; its text), ATTENTION.md (reason line), each task (State and
Settings.Enabled), the last backup (time, ok), the newest park/resume report (time, command, result), the clone's
HEAD (read-only `git -C <clone> rev-parse --short HEAD`). Last line: "What to do next: ...". A distinct exit code per
verdict, documented in the docstring. It writes NOTHING anywhere.

### 3.2 `park` (DRY RUN unless `--apply`)
Dry run: the status, then the exact steps `--apply` would take, in order, and when it would finish. Writes nothing.

`park --apply`, in this order, each step gated on the one before:
1. Refuse (change nothing) when `--clone` lacks `ai-agent/DEPLOYMENT`, or another park/resume `--apply` holds the lock
   (section 3.4).
2. Place STOP if absent, with a text body naming the tool, the time, and the resume command; verify it exists. A STOP
   already there is kept (log its time and text).
3. If the tuner RUNS (the learner PID alive and still a learner, or any batch/lane process): wait for the clean stop
   exactly as `park_watch.watch` + `check` do (the STOP line dated at/after STOP's mtime, the learner gone, the lock
   released, no batch or lane process, and the round that was running RECORDED in state.json, cycles.jsonl and
   runs.jsonl, on two looks a poll apart). `--deadline "YYYY-MM-DD hh:mm:ss AM"`; default = `current.started` +
   `current.minutes` + 90 minutes. Outcomes: removed STOP -> CANCELLED, nothing else changed; deadline -> TIMEOUT,
   nothing else changed (STOP stays, so it still stops at its boundary; a later `park --apply` finishes); nothing runs
   but not a clean recorded stop on 3 looks -> UNEXPECTED, nothing else changed.
   `--no-wait`: return right after step 2 with a PENDING exit; a later `park --apply` (e.g. after the round) finishes.
4. If the tuner did NOT run when the command began: no waiting; two looks a poll apart must show nothing runs; the
   last round's recorded state is reported as information (a round left unrecorded by a crash is NOT a reason to stop:
   its data stays on disk and the learner recovers it at its next start; say so in the report).
5. Switch OFF `Pokebot-AI-Learner-Autostart` and `Pokebot-Ops-Watchdog`; verify `Settings.Enabled` False for each.
6. ONE final backup, the nightly task's way (`py -3.12 -B <clone>/tools/ops/backup_learner.py`, cwd OUTSIDE the clone),
   VERIFIED: exit 0, `backup_status.json` fresh (time >= the backup's start) and ok, and the zip's
   `ai-agent/data/runs.jsonl`, `cycles.jsonl` and `state.json` byte-identical (sha256) to the stopped tuner's files.
   Retry once after 2 minutes. Verified -> switch OFF `Pokebot-Ops-Backup` and verify. Failed -> LEAVE IT ON (the
   nightly run retries) and say so.
7. Read all three tasks again, check once more that nothing runs and STOP exists, write the report, print the verdict.
IDEMPOTENT: `park --apply` at any point continues from where things are. Already PARKED (STOP, nothing runs, all three
OFF) -> verify and say so, exit 0, no second backup. Backup task still ON after a failed backup -> retry steps 6-7.
The tool NEVER stops or kills the learner, the batch or a lane: a park always waits for the round's end.

### 3.3 `resume` (DRY RUN unless `--apply`)
Dry run: the status, then the exact steps. Writes nothing.

`resume --apply`:
1. Refuse when `--clone` lacks `ai-agent/DEPLOYMENT` or the lock is held. If `ATTENTION.md` exists: change NOTHING,
   print its reason line and "the tuner will not start until a person fixes the cause and deletes ATTENTION.md"
   (NEEDS PERSON exit). Never delete ATTENTION.md.
2. Already RUNNING with no STOP and the tasks ON -> "already running", exit 0, nothing changed.
3. PARK PENDING (the learner still runs; STOP present): this CANCELS the park: delete STOP, verify it is gone, switch
   ON any of the three tasks that is OFF (verify), verify the learner is still alive. Never start anything.
4. Not running:
   a. If the autostart task's State is "Running" (the old `-NoExit` window is open), it may be ended ONLY with proof
      that it is idle: no learner, batch or lane process of the clone in the full process table; no `agent.lock`, or
      its PID dead; and the `run_agent.ps1` process has no child process other than `conhost.exe`. With the proof:
      `Stop-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart`, then verify the State left "Running" and that
      `run_agent.ps1` process is gone. Without the proof: change nothing more, NEEDS PERSON, and say what was seen.
      This happens while STOP still exists, so even a racing start would exit at once.
   b. Switch ON the three tasks; verify `Settings.Enabled` True for each.
   c. Delete STOP; verify it is gone.
   d. `Start-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart`.
   e. Verify within 180 s: a NEW `learner started (code ...)` line (only log bytes written after the resume began
      count) and `agent.lock` naming a live learner PID. Then wait up to 10 minutes for the round's `starting N lanes`
      line (or report what the log says instead). No start seen -> NEEDS PERSON ("is the old window still open? log off
      and on, or run run_agent.ps1"); nothing is undone.
IDEMPOTENT: `resume --apply` at any point continues from where things are.

### 3.4 Common rules
- Lock: `<ops>/park/park_tuner.lock` (PID and time) for `--apply` only; a lock whose PID is dead is replaced (logged).
- Log: every `--apply` action appended to `<ops>/park/park_tuner.log` with a timestamp. Report: `<ops>/park/latest.json`
  plus `<ops>/park/report-YYYYMMDD-HHMMSS.json` (command, start, end, each step's result, needs_person, the verdict).
  `status` and the dry runs write nothing (not even the folder).
- It writes inside the clone ONLY `ai-agent/STOP` (create in park, delete in resume), and only under `--apply`.
- It never deletes or registers a task (no `Unregister-ScheduledTask`, no `Register-ScheduledTask`, never runs
  `install_ops_tasks.ps1`), never runs `git` except read-only `rev-parse`, and never touches `ATTENTION.md`.
- Liveness by `OpenProcess` + `GetExitCodeProcess` (park_watch `pid_alive`); ⛔ never `os.kill(pid, 0)`: on Windows
  it TERMINATES the process.
- PowerShell output is read as UTF-8 without a BOM, and a stray BOM is stripped (park_watch `_ps`).
- THE TEST GUARD: while the selftest runs (an env var it sets, e.g. `PARK_TUNER_SELFTEST=1`), every `RealEnv` method
  that CHANGES something (task enable/disable/start/stop, the backup run) raises instead of acting. The selftest proves
  it (FAULT arm: calling one raises; CONTROL: the read-only ones are not used by the tests at all).
- Exit codes, documented in the docstring. Suggested: `park --apply` 0 PARKED (or already), 10 PARTIAL (needs a
  person), 11 PENDING (`--no-wait`), 20 TIMEOUT, 30 CANCELLED, 40 UNEXPECTED, 50 refused or internal error;
  `resume --apply` 0 RESUMED (or already running, or the pending park cancelled), 10 NEEDS PERSON, 50 refused or error;
  `status` one code per verdict; dry runs 0.
- Output for a non-programmer: short plain-English lines; the verdict first.

## 4. Tests: `tools/story-dev/selftest_park_tuner.py`

A gate in the style of `tools/story-dev/selftest_ops.py`: a docstring listing each test with its WHY; every test has a
FAULT arm (the bad condition, which must be caught) and a CONTROL arm (the good one, which must pass); a fake clone in a
temp folder and a `FakeEnv` (clock, processes, tasks with State and Enabled, a backup that writes a real zip and
status); never the real clone, the real tasks or the real `%LOCALAPPDATA%`. Prints `PASS`/`FAIL` per arm, then
`ALL PASS` and exits 0, or exits 1. Under 60 s. It is appended at the END of `tools/story-dev/run_gates.py`'s gate list
with a WHY comment, by the orchestrator (not by the build agents).

At least these (port park_watch's 35 where they apply):
- S status verdicts: each verdict from its fixture, with its exit code; status writes nothing (the ops folder absent
  after).
- D dry runs: `park` and `resume` without `--apply` change nothing (fixture bytes, STOP, FakeEnv tasks and calls
  identical before and after); FAULT: a variant that acts in a dry run is caught.
- P1 STOP placed with its text; an existing STOP kept as it was.
- P2 the clean-stop verification (park_watch's guards): a returning lock, a leftover lane, an old STOP line from before
  STOP's mtime, an unrecorded round, a reused learner PID, an ATTENTION exit; CANCELLED, TIMEOUT and UNEXPECTED change
  nothing.
- P3 order: tasks switched off only after the verified stop; the backup task only after a verified backup; a failed
  backup (bad exit, stale status, ok false, a tampered zip member) leaves it ON and the exit is PARTIAL; a task that
  stays ON after Disable -> PARTIAL.
- P4 the default deadline is `started` + `minutes` + 90 minutes; `--deadline` overrides it.
- P5 `--no-wait` places STOP and returns PENDING with no task touched.
- P6 not running at start: parks after two looks; an unrecorded round is reported, not refused.
- P7 idempotent: a second `park --apply` -> already PARKED, no second backup; after a failed backup a re-run retries
  the backup and finishes.
- R1 ATTENTION.md -> NEEDS PERSON, nothing changed, ATTENTION.md untouched.
- R2 already running -> nothing changed.
- R3 PARK PENDING -> STOP deleted, the learner untouched, no start called, OFF tasks switched ON.
- R4 the idle window: ended only with the full proof; FAULT arms: a live learner, a batch, a lane, a lock with a live
  PID, a python child of the window -> refused, `Stop-ScheduledTask` NEVER called.
- R5 order: start is never called while STOP exists or before the three tasks read ON.
- R6 the start check: an OLD `learner started` line (before the resume began) does not count; no new line in 180 s ->
  NEEDS PERSON, nothing undone; CONTROL: a new line and a live lock PID -> RESUMED.
- L1 a concurrent `--apply` is refused (the lock); a lock with a dead PID is replaced.
- G1 the test guard: under the selftest flag every mutating `RealEnv` method raises.
- C1 a `--clone` without `ai-agent/DEPLOYMENT` is refused with nothing written.
- M process matching on the REAL command-line shapes in section 2 (the learner, py.exe, the window, the batch, a lane,
  the watchdog `tools\ops\` process, this tool itself), FAULT and CONTROL.

## 5. Proof the build must show (the build agents run all of it)

1. `py -3.12 tools/story-dev/selftest_park_tuner.py` -> `ALL PASS`, exit 0, three runs in a row.
2. Mutants: at least 15 (each guard removed or inverted, the order of two steps swapped, the dry-run gate removed, the
   test guard removed, the idle-window proof weakened, the "new log line" filter removed ...); every one CAUGHT, each
   with the failing test's name; a control run before and after.
3. Live READ-ONLY controls, on the real machine: `status` (must say RUNNING, round ai0054, 12 lanes, the three tasks
   ON); `park` (dry run) and `resume` (dry run). Before and after them, record: the three tasks' State and
   Settings.Enabled, STOP absent, the clone's `git status --porcelain` empty, `<ops>/park/` absent or unchanged. They
   must be identical.

## 6. Forbidden during the build

- ⛔ No `--apply` against the real clone or the real tasks; no STOP placed or deleted in the real clone; no task
  enabled, disabled, started or stopped; no backup run; nothing written into `C:/Remote Projects/pokebot-learner`.
- ⛔ Do not run `ai-agent/test_agent.py` (or any heavy suite): the bot tuner runs 12 lanes on this PC.
- ⛔ Do not edit any file in the main checkout `C:/Remote Projects/Pokebot_Gen3_Enhancement`; build in the scratch
  folder given in the prompt, laid out as `<build>/tools/ops/park_tuner.py` and
  `<build>/tools/story-dev/selftest_park_tuner.py`, so the same relative paths work once copied into the repo.
- No `git add -A`, no destructive git, no commits.
