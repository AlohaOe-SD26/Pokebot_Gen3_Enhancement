# The park tool: build report (2026-10-28)

> **How to read this note.** Sections 1-8 are the build workflow's report, verbatim (its agents wrote them). Paths like `../sweep/`, `../review/`, `../fixround/` and `build/` were that session's scratch folders and are NOT in the repo; the two `tools/...` files are, byte for byte (sha256 in 8.1). Section 0, just below, is the orchestrating session's own checks after the workflow ended. The tool is `tools/ops/park_tuner.py`; decisions: `06` 2026-10-28; spec: `2026-10-28-PARK-TOOL-BUILD-SPEC.md`.

## 0. The orchestrator's checks (2026-10-28, after the fix round)

- **Installed** into the repo at the same paths; sha256 `5381b498be821d2701a457e3431b36583682e450f9cd6fdb4f5acc40bdf36585` and `86cc1d28714477116c2766da8004b837ef9b57428d0d770c4f27bf75c4201732`, equal to 8.1.
- **The selftest from the repo, three runs in a row:** ALL PASS (263 checks, 0 failed) each time, exit 0, about 8 s each (8:37 PM).
- **All mutants re-run SERIALLY by the orchestrator** (`mutants_final.py`, unchanged, on byte-identical copies): 173 run, CAUGHT 172, EQUIVALENT (proved on 28 real process shapes) 1 (M33), SURVIVED 0; the unmutated controls before and after ALL PASS (263 checks); 8:38 to 9:10 PM, harness exit 0.
- **Live READ-ONLY controls, two rounds, with the INSTALLED tool** (`status`, `park` and `resume` without `--apply`, under `PARK_TUNER_SELFTEST=1`, the evidence script before and after): both rounds `differences: NONE: identical`; all exits 0; `RUNNING: the bot tuner is running (round ai0054, 12 lanes); nothing is parked.`
- **The probe that answered the build's open question 1** (a THROWAWAY task, never a Pokebot-* task; 5:53 PM). The script:

```powershell
# Live probe on a THROWAWAY task only (never a Pokebot-* task): does Stop-ScheduledTask end the running instance of a
# DISABLED task? (park_tuner.py resume, step 4a, in the parked case: the -NoExit window open, the task disabled.)
# Arm FAULT-SHAPE: start, disable, stop. Arm CONTROL: start, stop (enabled). The probe task copies the autostart
# task's settings (LogonTrigger, IgnoreNew, no time limit) and runs a hidden 10-minute sleep. It is unregistered at the
# end, and any probe process left alive is reported (and ended by PID only if its command line carries the marker).
$ErrorActionPreference = 'Stop'
$marker = 'ParkToolProbeMarker-' + (Get-Date -Format 'yyyyMMddHHmmss')
$name = 'ZZ-' + $marker
function Probe-Proc { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$marker*" -and $_.Name -eq 'powershell.exe' } }
function Show($label) {
    $t = Get-ScheduledTask -TaskName $name
    $p = @(Probe-Proc)
    "{0,-34} State={1,-8} Enabled={2,-5} probe processes={3} {4}" -f $label, $t.State, $t.Settings.Enabled, $p.Count, (($p | ForEach-Object { $_.ProcessId }) -join ',')
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Sleep -Seconds 600; '$marker'`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings | Out-Null
try {
    foreach ($arm in @('DISABLED (the parked case)', 'ENABLED (control)')) {
        "--- arm: $arm"
        Start-ScheduledTask -TaskName $name
        Start-Sleep -Seconds 3
        Show 'after Start-ScheduledTask'
        if ($arm -like 'DISABLED*') {
            Disable-ScheduledTask -TaskName $name | Out-Null
            Start-Sleep -Seconds 1
            Show 'after Disable-ScheduledTask'
        }
        try {
            Stop-ScheduledTask -TaskName $name
            'Stop-ScheduledTask: returned without error'
        } catch {
            "Stop-ScheduledTask: ERROR: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 3
        Show 'after Stop-ScheduledTask'
        if ($arm -like 'DISABLED*') {
            Enable-ScheduledTask -TaskName $name | Out-Null
            Start-Sleep -Seconds 1
            Show 'after Enable-ScheduledTask'
            $left = @(Probe-Proc)
            if ($left.Count) {
                try { Stop-ScheduledTask -TaskName $name; 'second Stop-ScheduledTask (now enabled): returned' } catch { "second Stop: ERROR: $($_.Exception.Message)" }
                Start-Sleep -Seconds 3
                Show 'after the second Stop'
            }
        }
    }
} finally {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    $left = @(Probe-Proc)
    foreach ($p in $left) { Stop-Process -Id $p.ProcessId -Force; "ended leftover probe process $($p.ProcessId)" }
    "unregistered $name; probe processes left: $(@(Probe-Proc).Count); Pokebot-* tasks untouched:"
    Get-ScheduledTask -TaskName 'Pokebot-*' | ForEach-Object { "  $($_.TaskName) State=$($_.State) Enabled=$($_.Settings.Enabled)" }
}
```

Its output and reading, verbatim:

```text
probe_stop_disabled.ps1, run 2026-10-28 5:53 PM by the orchestrating session (live, on a THROWAWAY task only), verbatim:

--- arm: DISABLED (the parked case)
after Start-ScheduledTask          State=Running  Enabled=True  probe processes=1 27588
after Disable-ScheduledTask        State=Running  Enabled=False probe processes=1 27588
Stop-ScheduledTask: returned without error
after Stop-ScheduledTask           State=Disabled Enabled=False probe processes=0
after Enable-ScheduledTask         State=Ready    Enabled=True  probe processes=0
--- arm: ENABLED (control)
after Start-ScheduledTask          State=Running  Enabled=True  probe processes=1 43816
Stop-ScheduledTask: returned without error
after Stop-ScheduledTask           State=Ready    Enabled=True  probe processes=0
unregistered ZZ-ParkToolProbeMarker-20261028175351; probe processes left: 0; Pokebot-* tasks untouched:
  Pokebot-AI-Learner-Autostart State=Running Enabled=True
  Pokebot-Ops-Backup State=Ready Enabled=True
  Pokebot-Ops-Watchdog State=Ready Enabled=True

Reading: Stop-ScheduledTask ends the running instance of a DISABLED task (the builder's open question 1): the process is
gone and the State goes Running -> Disabled. Disabling a task does NOT end its running instance (State stays Running,
Enabled False): a parked tuner whose -NoExit window is still open reads State Running + Enabled False, so the PARKED
test must read Settings.Enabled, never State.
```

> Built by the build agent for the orchestrator, against `PARK-TOOL-BUILD-SPEC.md` (USER RULING 50; `03`
> `#28-trainer-improvements` (10)). Everything lives in this scratch build folder. NOTHING was written into the main
> checkout or into the deployment clone. No `--apply` ran against the real machine. No STOP was placed or deleted, no
> task was switched, started or stopped, and no backup was run. The only commands that touched the live machine were
> read-only: `status`, `park` and `resume` without `--apply`, `Get-ScheduledTask`, `Get-CimInstance Win32_Process`, and
> `git status` / `rev-parse` on the clone.

## 1. What was built

| file | lines | bytes | sha256 |
|---|---|---|---|
| `tools/ops/park_tuner.py` | 1738 | 90,270 | `475d4efbeadd4bb47706cb64327a3fbc2e3532274c2743c950192722e20b8ec1` |
| `tools/story-dev/selftest_park_tuner.py` | 1474 | 84,991 | `1655fc21a7b52033cbe9eca979cf394f19dfc372da9f95c3d3a3ff63e4627d84` |
| `mutants_builder.py` (build only, not for the repo) | 325 | 19,900 | `d5e6d72ec153c908f0c8fddadbba7e42f76749866bc38019378891de90145ea4` |

- **To install:** copy the two `tools/...` files into the repo at the same relative paths. The selftest finds the tool by
  `Path(__file__).resolve().parent.parent.parent / "tools/ops/park_tuner.py"`, the same way `selftest_ops.py` does, so
  it works unchanged in the repo. The orchestrator appends it to `run_gates.py` (spec section 4). Standard library only,
  Python 3.12, Windows.
- **Evidence files** (in `../`, the parktool folder):
  - `three_runs.txt`
  - `mutants_run1.txt`, `mutants_run2.txt`, plus `mutants_results.json` here
  - `live_before*.txt`, `live_after*.txt`, `live_*.txt`, `live2_*.txt`, `live3_*.txt`
  - `live_evidence.ps1`, the read-only evidence script
  - `demo_outputs.py`, which prints the tool's output in the main scenarios on the selftest's FakeEnv

### 1.1 What the tool does, in one screen

`py -3.12 tools/ops/park_tuner.py status | park [--apply] [--no-wait] [--deadline T] [--poll S] | resume [--apply]`,
plus `--clone` and `--ops-dir` on every command. The docstring has every step and exit code. The docstring also states
that the tool never parks on its own, and that nothing may run `park --apply` unless the user asked for a park.

- **status** is read-only and writes nothing, not even a folder. The verdict is the first line, then the details, then
  "What to do next".
  - Exit codes: RUNNING 0, PARK PENDING 61, PARKED 62, PARTLY PARKED 63, STOPPED, NOT PARKED 64, INCONSISTENT 65, and
    50 when the facts cannot be read.
  - The details: the learner (lock PID, alive, still a learner); the round (tag, started, ends about); the lanes, batch
    and learner processes; STOP (time and text); ATTENTION.md (its reason line); the -NoExit window (idle or running the
    learner); each task (State and Enabled); the last backup; the newest park/resume report; the clone's HEAD; and, for
    STOPPED / INCONSISTENT, the log's tail.
- **park --apply** (exits 0 / 10 / 11 / 20 / 30 / 40 / 50):
  1. Refuse when there is no DEPLOYMENT, the deadline is bad, or the lock is held. Already PARKED: verify and say so, no
     second backup.
  2. Place STOP, or keep the one already there.
  3. If the tuner runs, wait for the clean stop, using park_watch's `watch` + `check` rules.
  4. If it does not run, two looks one poll apart.
  5. Switch OFF the autostart and the watchdog, verified.
  6. ONE final backup, verified (exit 0, a fresh ok status, and the three data files byte-identical in the zip), with
     one retry. Only then switch OFF the nightly backup task; a failed backup leaves it ON.
  7. The final look, the report, the verdict.

  It has no way to stop or kill a process: `RealEnv` has no such method.
- **resume --apply** (exits 0 / 10 / 50):
  1. ATTENTION.md present: change nothing (NEEDS PERSON).
  2. Already running: nothing to do.
  3. Running (a pending park, or a task OFF): delete STOP, switch ON the OFF tasks, check the learner is alive. Start
     nothing.
  4. Stopped:
     - (a) End the old -NoExit window only with the full idle proof, then verify it is gone.
     - (b) The three tasks ON, verified.
     - (c) STOP deleted, verified.
     - (d) Start, re-checked just before: never with STOP present or a task OFF.
     - (e) Within 180 s, a NEW `learner started` line (counted only from log bytes written after the resume began) and
       a live learner in agent.lock; then up to 10 minutes for `starting N lanes`.
- **Common:**
  - The lock `<ops>/park/park_tuner.lock`, O_EXCL. A stale lock is replaced, and that is logged.
  - The log `<ops>/park/park_tuner.log`. The report `<ops>/park/latest.json` plus `report-YYYYMMDD-HHMMSS.json`.
  - Inside the clone it writes ONLY `ai-agent/STOP`. It never registers or deletes a task, runs no git but
    `rev-parse`, and never touches ATTENTION.md.
- **The test guard:** under `PARK_TUNER_SELFTEST=1`, every changing `RealEnv` method raises `SelftestGuardError` before
  reaching PowerShell. A second guard, `guard_write`, refuses any write to the REAL clone or ops folder.

### 1.2 Where each park_watch piece went (each is marked "park_watch" in the source)

| park_watch | park_tuner | change |
|---|---|---|
| `_ps` | `_ps` (through `_run`, the one process launcher) | none (the selftest's tripwire replaces `_run`/`_ps`) |
| `RealEnv.processes`, `pid_alive` | same | none (OpenProcess + GetExitCodeProcess, never os.kill) |
| `task_enabled`, `task_disable`, `task_enable` | same, plus `task_info`, `task_start`, `task_stop` | the changing ones call `guard_action` first; `task_info` reads State and Enabled in one call |
| `run_backup` | same | `guard_action` first; working folder %TEMP% (outside the clone) |
| `read_json`, `last_jsonl`, `count_rows`, `last_stop_line`, `short`, `pid_is_learner` | same | none |
| `trainer_processes` | same | the clone's path (with a closing backslash) as a parameter instead of the literal `pokebot-learner`; this tool excluded too |
| `attention_reason` | replaced | `tools/ops/watchdog.py`'s rule (park_watch returned the footer, see 7.5) |
| `check` | same | a wait begun with no round needs `current` empty and a readable state.json |
| `watch` | same rules | adopts a round that starts during the wait (and moves a DEFAULT deadline with it); quieter log |
| `disable_verified`, `verify_backup` | same | wrapped by `switch_off` (idempotent); a `TypeError` caught in the time parse |
| `park` | `park_windows` + `park_final` | idempotent (already OFF stays OFF; already PARKED does no backup) |
| `baseline` | `park_wait` | the base is derived from the files when the wait begins; no refusal when no round runs |

## 2. The tests: 129 checks in 20 tests (`selftest_park_tuner.py`)

Every test has FAULT arms (the bad condition, which must be caught) and CONTROL arms (the good one, which must pass).
Everything runs on a fake clone in temp folders with a FakeEnv. The FakeEnv has a clock that `sleep()` advances (and a
3-day ceiling, so a loop that never ends fails fast), a process table in the REAL command-line shapes measured today,
the three tasks with State and Enabled, and backups that write a real zip and status file. Three layers keep the real
machine out:
- `PARK_TUNER_SELFTEST=1` is set before the tool is loaded.
- The tool's `_run`/`_ps` are swapped for a recording tripwire.
- Every path is a temp path.

The LAST check asserts the tripwire recorded nothing.

| test | checks | FAULT arms / CONTROL arms |
|---|---|---|
| M | 6 | CONTROL the learner, its py.exe launcher, the batch and 12 lanes (real shapes) ARE the tuner. FAULT: the window, conhost, the watchdog's two processes, the backup task, this tool (main checkout and clone copy) and park_watch are not; nor are a lane of another checkout, a sibling `pokebot-learner-old`, or a learner-shaped process with this PID. A reused PID is not the learner. Another checkout's window is not this clone's. |
| S | 10 | Each verdict from its fixture with its exit code, on the FIRST line. The FAULT arms are the neighbouring states: STOP while running is not RUNNING; one task ON is not PARKED; a task OFF while running is INCONSISTENT. ATTENTION's REASON line is shown, not its footer; without it, the log tail. CONTROL: status writes nothing (no ops folder, every byte and time equal, no changing call). FAULT: that comparison does see a touched file. |
| D | 8 | CONTROL: five dry runs (park on RUNNING and on PARKED, park with --no-wait and --deadline, resume on PARKED with the window, resume on RUNNING) change nothing, and print the plan in order with its deadline and finish time. FAULT: an acting run on a twin fixture IS seen by the same comparison. |
| C1 | 6 | FAULT: no `ai-agent/DEPLOYMENT` -> park --apply, resume --apply and park --apply --no-wait are REFUSED (50) with nothing written. FAULT: a bad --deadline is refused before anything. CONTROL: with DEPLOYMENT the run proceeds. CONTROL: status warns and writes nothing. |
| L1 | 9 | FAULT: a live park_tuner lock refuses park and resume (the lock untouched, nothing changed); an unreadable lock under a minute old refuses. CONTROL: a dead PID's lock, a reused PID's lock and an old unreadable lock are replaced, and that is logged. FAULT: the summary fails, or the first log line cannot be written (park and resume) -> the lock is still released, nothing changed. |
| G1 | 10 | FAULT: each of the five changing RealEnv methods raises SelftestGuardError before reaching a process (the tripwire count does not move); writes to the REAL clone's STOP and the REAL ops log are refused. CONTROL: a temp path is writable; the guard is conditional (flag off -> it lets the tool act); the tripwire recorded nothing over the whole run. |
| N1 | 3 | CONTROL: the tool's CODE (AST; docstrings and comments excluded) never kills or terminates, never (un)registers a task, never runs Stop-Process, taskkill, TerminateProcess, Remove-Item or install_ops_tasks, and its only git is rev-parse. FAULT: a synthetic source with each IS flagged (4 findings). CONTROL: mentions only in a docstring or comment are not flagged. |
| P1 | 2 | CONTROL: STOP is placed with the tool, the time and the resume command. FAULT: an existing STOP is kept, the same bytes and time. |
| P2 | 25 | Unit: 11 single faults each block stopped_clean (the lock; the learner PID; a lane; the batch; current; the state's cycles; cycles.jsonl's tag; runs.jsonl one short; an unreadable state; STOP removed; only an OLD STOP line). CONTROL: the clean fixture; a reused PID; a no-round wait with a readable state (FAULT: unreadable). End to end: CONTROL the clean stop parks (0). FAULT: a returning lock needs 3 looks; no fresh STOP line -> 40; not recorded -> 40; the batch outliving the learner -> no UNEXPECTED while lanes run; STOP removed -> 30; the deadline -> 20 (each with no task touched and no backup); an ATTENTION exit -> 10 with the reason; Ctrl+C -> 50 INTERRUPTED (the lock released, STOP kept). CONTROL: an adopted round parks after 12 h (the deadline moved). FAULT: the adopted round one row short -> 40. |
| P3 | 9 | CONTROL: no task is switched off before the verified stop plus two looks; the backup task only after the verified backup. FAULT, five single-fault backups (REFUSED; exit 1 over a good-looking status; a STALE status over a good zip; ok false over a good zip; a tampered member) -> 10, the backup task LEFT ON, its Disable never called. FAULT: a task stuck ON, or a Disable that raises -> 10. CONTROL: fail once, then pass, retried 120 s later -> 0. |
| P4 | 6 | Unit: started + minutes + 90 = 06:00:19 AM for ai0054; no round -> now + 90; an unreadable start -> now + 720 + 90. CONTROL end to end: TIMEOUT at the first look past it, the exact deadline in the report, and it says how to wait longer. FAULT: --deadline overrides it; an adopted round does NOT move a given deadline. |
| P5 | 2 | CONTROL: --no-wait on a running tuner -> 11, STOP placed, no task touched. FAULT: on a tuner that is not running it still touches no task. |
| P6 | 3 | CONTROL: stopped at the start -> parked after exactly one 60 s poll between two looks. FAULT: an unrecorded round is REPORTED ("recovers it at its next start"), not refused; a learner appearing between the looks is waited for (no task off before it exits). |
| P7 | 2 | CONTROL: a second park --apply -> 0 "it already was", no backup, no change. FAULT: after a failed backup a re-run retries ONCE and finishes. |
| R1 | 2 | FAULT: ATTENTION.md -> 10 with its reason; nothing changed; ATTENTION.md and STOP untouched. CONTROL: without it the same fixture resumes. |
| R2 | 2 | CONTROL: already running -> 0, the clone unchanged, no changing call. FAULT: running with a task OFF -> only that task switched ON, nothing started. |
| R3 | 2 | CONTROL: PARK PENDING -> STOP deleted, the OFF task ON, the learner untouched, nothing started or stopped. FAULT: the learner dead but its batch running -> STOP deleted, then 10, nothing started. |
| R4 | 11 | Unit: CONTROL conhost only -> proven idle. FAULT: a live learner, a batch, a lane, a live-PID lock, a python child, or no window -> not proven. End to end: CONTROL Stop-ScheduledTask FIRST, then the three ON, STOP deleted, started -> 0. FAULT: a live-PID lock or a python child -> 10 and Stop-ScheduledTask NEVER called; a window that does not close -> 10, no enable, no start. |
| R5 | 5 | CONTROL: at the start call STOP is absent and the three tasks read ON. FAULT: an Enable fails (STOP stays), STOP cannot be deleted, or a task flips OFF after being switched ON -> the start is NEVER called. Unit: start_allowed. |
| R6 | 6 | FAULT: a live learner, but only an OLD `learner started` line -> 10 after 180 s, nothing undone; the start does nothing -> 10 with the logon advice; a new line but a dead lock PID -> 10; ATTENTION after the start -> 10. CONTROL: a new line, a live learner and the round line -> 0; no round in 10 min but alive -> 0 with a note. |

## 3. The selftest: three runs in a row (`../three_runs.txt`, verbatim)

```text
--- run 1: exit 0, wall 4.1 s, 129 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git, not even through a read-only RealEnv method
ALL PASS (129 checks, 0 failed, 4.0 s)
--- run 2: exit 0, wall 4.0 s, 129 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git, not even through a read-only RealEnv method
ALL PASS (129 checks, 0 failed, 3.8 s)
--- run 3: exit 0, wall 4.0 s, 129 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git, not even through a read-only RealEnv method
ALL PASS (129 checks, 0 failed, 3.9 s)
```

## 4. Mutants (`mutants_builder.py`; final run `../mutants_run2.txt` and `mutants_results.json`)

How the harness works:
- Each mutant is ONE exact text replacement that must hit EXACTLY ONCE (the harness refuses otherwise).
- The mutated tool and the UNCHANGED selftest go into a fresh repo-shaped temp folder.
- CAUGHT means the selftest exited non-zero with FAIL lines; the failing check names are recorded.
- It runs serially, with a CONTROL run of the unmutated tool before and after.
- No mutant can reach the machine: the flag and the tripwire are in place before any test runs.

**Final run: 51 mutants, 50 CAUGHT, 1 proved EQUIVALENT (M33), 0 survived.** The controls before and after were both
`ALL PASS (129 checks, 0 failed, 3.9 s)`, exit 0. Wall time 226 s. Harness exit 0.

### 4.1 The table

| id | what it changes | result | failing checks (first two; total) |
|---|---|---|---|
| M01 | the dry-run gate removed: `park` without --apply ACTS | CAUGHT | D CONTROL dry run, park on a RUNNING tuner ...; D CONTROL dry run, park on a PARKED tuner ... (+2 more) |
| M02 | the dry-run gate removed: `resume` without --apply ACTS | CAUGHT | D CONTROL dry run, resume on a PARKED tuner with its old window open ...; D CONTROL dry run, resume on a RUNNING tuner ... (+1 more) |
| M03 | THE TEST GUARD removed (RealEnv's changing methods no longer refuse) | CAUGHT | G1 FAULT RealEnv.task_disable under PARK_TUNER_SELFTEST=1 raises ...; G1 FAULT RealEnv.task_enable ... (+4 more: the other methods and the tripwire check) |
| M04 | the write guard removed | CAUGHT | G1 FAULT a write to the REAL clone's ai-agent/STOP is refused ...; G1 FAULT a write to the REAL ops folder's park log is refused ... |
| M05 | idle-window proof: a lock naming a LIVE PID ignored | CAUGHT | R4 FAULT unit: a lock naming a live PID -> NOT proven idle; R4 FAULT end to end: a lock naming a live PID -> ... Stop-ScheduledTask NEVER called |
| M06 | idle-window proof: any child of the window allowed | CAUGHT | R4 FAULT unit: a python child of the window ...; R4 FAULT end to end: a python child of the window ... |
| M07 | idle-window proof: tuner processes ignored | CAUGHT | R4 FAULT unit: a live learner ...; R4 FAULT unit: a batch ... (+1 more: a lane) |
| M08 | the "new log line" filter removed (the start check reads learner.log from byte 0) | CAUGHT | R6 FAULT only an OLD 'learner started' line (from before the resume) and a live learner: the old line does NOT count ... |
| M09 | the STOP line's date ignored [park_watch M4] | CAUGHT | P2 FAULT only an OLD STOP line ...; P2 FAULT no fresh STOP line (only the old one) -> UNEXPECTED ... |
| M10 | no runs.jsonl row-count check [park_watch M1] | CAUGHT | P2 FAULT runs.jsonl one row short ...; P2 FAULT the adopted round ends with runs.jsonl one row short ... |
| M11 | the stable-look count never resets [park_watch M2] | CAUGHT | P2 FAULT a lock that returns between looks resets the count ... |
| M12 | a failed backup still switches the nightly task OFF [park_watch M5] | CAUGHT | P3 FAULT the final backup fails (REFUSED ...); P3 FAULT the final backup fails (exit 1 although its status and zip look fine ...) (+4 more) |
| M13 | the backup zip never compared [park_watch M3] | CAUGHT | P3 FAULT the final backup fails (a zip whose cycles.jsonl differs, twice) ... |
| M14 | the stale-status check removed [park_watch M7] | CAUGHT | P3 FAULT the final backup fails (a STALE status (an older run's time) over a good zip, twice) ... |
| M15 | the deadline ignored [park_watch M8] | CAUGHT | P2 FAULT still running at the deadline -> TIMEOUT ...; P4 CONTROL end to end (it never stops) ... (+2 more) |
| M16 | resume ORDER swapped: STOP deleted before the three tasks are ON | CAUGHT | R5 FAULT an Enable that fails: ... STOP still in place (it is deleted only after the three read ON) |
| M17 | park ORDER swapped: the nightly backup task OFF before the final backup | CAUGHT | P3 CONTROL no task is switched off before the verified stop ...; P3 FAULT the final backup fails (REFUSED ...) (+5 more) |
| M18 | park ORDER swapped: the autostart OFF before the wait | CAUGHT | P2 FAULT no fresh STOP line ... NO task touched ...; P2 FAULT the round NOT recorded ... NO task touched ... (+7 more) |
| M19 | start allowed while STOP exists | CAUGHT | R5 unit start_allowed: ... FAULT STOP present, a task OFF -> refused |
| M20 | start allowed while a task is OFF | CAUGHT | R5 FAULT a task that flips OFF after it was switched ON: the start NEVER called ...; R5 unit start_allowed ... |
| M21 | the re-check just before the start removed | CAUGHT | R5 FAULT a task that flips OFF after it was switched ON: the start NEVER called ... |
| M22 | ATTENTION.md ignored by resume | CAUGHT | R1 FAULT ATTENTION.md: NEEDS PERSON (10) with its REASON line; nothing changed ... |
| M23 | no ai-agent/DEPLOYMENT check | CAUGHT | C1 FAULT park --apply on a clone WITHOUT ai-agent/DEPLOYMENT ...; C1 FAULT resume --apply ... (+1 more) |
| M24 | a held park-tool lock never refuses | CAUGHT | L1 FAULT park --apply --no-wait while another ... holds the lock ...; L1 FAULT resume --apply while another ... (+1 more) |
| M25 | only ONE look at a stopped tuner | CAUGHT | P6 CONTROL not running at the start: parked (0) after two looks ...; P6 FAULT a learner appearing between the two looks is WAITED for ... |
| M26 | the already-PARKED shortcut removed | CAUGHT | P7 CONTROL a second park --apply on a PARKED tuner: 0, 'it already was', NO backup and no change |
| M27 | --no-wait ignored | CAUGHT | C1 CONTROL the same run WITH ai-agent/DEPLOYMENT proceeds (PENDING, 11); L1 CONTROL a stale lock ... the run proceeds (11) ... (+6 more) |
| M28 | an unrecorded round REFUSED instead of reported | CAUGHT | P6 FAULT a round left UNRECORDED by a crash is REPORTED, not refused ... |
| M29 | a STOP removed while waiting not noticed | CAUGHT | P2 FAULT STOP removed while waiting -> CANCELLED: exit 30 ... |
| M30 | the "old window is gone" verification removed | CAUGHT | R4 FAULT end to end: the window does NOT close after Stop-ScheduledTask -> NEEDS PERSON (10) ... |
| M31 | a reused PID counted as the learner | CAUGHT | M pid_is_learner: ... FAULT a reused PID (chrome) and None are not; P2 CONTROL a reused PID ... (+1 more) |
| M32 | the lanes not counted as the tuner [park_watch M6] | CAUGHT | M CONTROL the learner, its py.exe launcher, the batch and 12 lanes ...; M lane and batch counts ... (+3 more) |
| M33 | the idle -NoExit window counted as the tuner (its exclusion removed) | **EQUIVALENT (proved)** | none: see 4.2 |
| M34 | status WRITES (it creates the ops/park folder) | CAUGHT | S status writes NOTHING ...; S FAULT STOP while it runs is PARK PENDING ... (+10 more) |
| M35 | resume STARTS the task while the tuner still runs | CAUGHT | R2 FAULT running with a task OFF ... nothing started (0); R3 CONTROL PARK PENDING ... nothing started or stopped |
| M36 | resume step 3's learner-alive check INVERTED | CAUGHT | R2 FAULT running with a task OFF ...; R3 CONTROL PARK PENDING ... (+1 more) |
| M37 | PARKED no longer requires all three tasks OFF | CAUGHT | S FAULT one task still ON is PARTLY PARKED (63) ...; P7 FAULT after a failed backup ... retries the backup ONCE ... |
| M38 | status's exit code ignores the verdict | CAUGHT | S FAULT STOP while it runs is PARK PENDING (61) ...; S CONTROL PARKED (62) ... (+4 more) |
| M39 | the learner's own command line (`learner.py run`, no clone path) not matched | CAUGHT | M CONTROL the learner, its py.exe launcher, the batch and 12 lanes ...; R4 FAULT unit: a live learner ... |
| M40 | a step-5 result check INVERTED | CAUGHT | P2 CONTROL end to end: the clean stop at 4:31 AM parks (0) ...; P2 FAULT a lock that returns between looks ... (+8 more) |
| M41 | ATTENTION.md's reason taken from the timestamp line | CAUGHT | S FAULT ... STOPPED, NOT PARKED (64), naming ATTENTION.md's REASON line ...; P2 an ATTENTION exit ... (+1 more) |
| M42 | no retry of the final backup | CAUGHT | P3 CONTROL a backup that fails once then passes is retried 120 s later and parks (0) |
| M43 | one good look is enough (STABLE_LOOKS 2 -> 1) | CAUGHT | P2 FAULT a lock that returns between looks ...; P3 CONTROL no task is switched off before the verified stop ... (+2 more) |
| M44 | a leftover batch or lane no longer blocks "nothing running" | CAUGHT | P2 FAULT a lane process left ...; P2 FAULT the batch process left ... (+1 more) |
| M45 | the lock NOT released when the summary itself fails | CAUGHT | L1 FAULT the summary itself fails (an OSError while printing): the lock is STILL released ... |
| M46 | Ctrl+C during park --apply not handled | CAUGHT | P2 FAULT Ctrl+C during the wait: exit 50 with an INTERRUPTED report, the lock released ... |
| M47 | the clone's ops tools (`tools\ops\`) counted as the tuner (backup_learner.py holds "learner.py") | CAUGHT | M CONTROL ... ARE the tuner (15); M FAULT-ARMS ... the backup task ... are NOT the tuner |
| M48 | the lock left behind when park --apply cannot write its first log line | CAUGHT | L1 FAULT park --apply cannot write its first log line: an error (50), the lock released, nothing changed |
| M49 | "nothing runs but not clean" counted while lanes still run | CAUGHT | P2 FAULT the learner dies but its batch runs on for 10 minutes: no UNEXPECTED while the lanes still run ... |
| M50 | an adopted round moves a deadline the user GAVE | CAUGHT | P4 FAULT a round adopted during the wait does NOT move a deadline the user GAVE ... |
| M51 | a no-round wait treats an UNREADABLE state.json as recorded | CAUGHT | P2 a wait that began with NO round: CONTROL ... FAULT state.json unreadable -> NOT recorded ... |

The spec's required kinds are all present:
- each guard removed or inverted (M05-M07, M09-M15, M19-M24, M29-M31, M36, M40, M44, M49-M51);
- the order of two steps swapped (M16, M17, M18);
- the dry-run gate removed (M01, M02);
- the test guard removed (M03, M04);
- the idle-window proof weakened (M05, M06, M07, M30);
- the "new log line" filter removed (M08).

### 4.2 M33 is EQUIVALENT, and how that was proved

Run 1 (44 mutants, an earlier version of the files) caught 43; M33 survived. The cause is a redundant guard, not a weak
test.
- The window's measured command line,
  `"powershell.exe" -NoExit -ExecutionPolicy Bypass -File "C:\Remote Projects\pokebot-learner\ai-agent\run_agent.ps1"`,
  holds the clone path but none of `learner.py run`, `x4_headless.py`, `sandbox-pokebot` or `learner.py`.
- So `trainer_processes`' INCLUSION rule already rejects it, and the `run_agent.ps1` exclusion is defense in depth.

The harness PROVES this mechanically (`prove_trainer_equivalence`):
- It loads the original and the mutated tool and runs `trainer_processes` on all 28 real shapes plus spellings of the
  window (forward slashes, lower and upper case, the full powershell path).
- Result: "PROVED on 28 real shapes and window spellings: the original and the mutant count the same 15 tuner processes,
  and no window".

The exclusion that IS load-bearing is `tools\ops\`, because the nightly backup's `backup_learner.py` contains
`learner.py` plus the clone path. M47 was added for it, and it is CAUGHT.

The same reasoning shows the `park_tuner.py` / `park_watch.py` exclusions are also defense in depth on the measured
shapes. No mutant was written for them.

### 4.3 What changed between run 1 and run 2 (each new mutant guards a test added for it)

- M33's analysis and its proof; M47 for the load-bearing exclusion.
- New code, each with a test and a mutant: the lock released when the summary fails (M45) or the first log line cannot
  be written (M48); Ctrl+C handled (M46).
- Gaps found by reasoning about plausible bugs, each closed with a test and a mutant: UNEXPECTED counted mid-batch
  (M49); a given --deadline moved by an adopted round (M50); a no-round wait with an unreadable state.json (M51).
- Earlier, before run 1, the backup failure arms were rebuilt so each breaks ONE thing. A stale status now points at a
  GOOD zip, and an exit-1 run leaves a good-looking status. Otherwise "stale check removed" and "exit code ignored"
  would have survived, masked by the zip check.
- Also before run 1, R6's old-line arm was rebuilt so that a live learner appears but logs nothing new. Then only the
  byte-offset filter can reject the OLD `learner started` line. In the first version the dead lock also failed the
  check, which would have hidden M08.

## 5. Live READ-ONLY controls on the real machine

Three bracketed rounds. Each one: `live_evidence.ps1` before; then `status`, `park` and `resume`, all WITHOUT `--apply`;
then `live_evidence.ps1` after. The evidence covers:
- the three tasks' State and `Settings.Enabled`;
- STOP and ATTENTION.md;
- `%LOCALAPPDATA%\pokebot-ops\park`;
- the clone's `git --no-optional-locks status --porcelain` (`--no-optional-locks` so git does not even refresh the
  index) and HEAD;
- agent.lock;
- the learner.log size.

The last round ran the FINAL bytes (sha256 `475d4efb...0b8ec1`).

```text
round 1  before 05:30:19 PM / after 05:30:59 PM   -> differences: NONE: identical
round 2  (timed)                                  -> differences: NONE: identical
round 3  before 05:38:51 PM / after 05:39:05 PM   -> differences: NONE: identical   (final tool bytes)

after (round 3), identical to before:
task Pokebot-AI-Learner-Autostart: State=Running Enabled=True
task Pokebot-Ops-Watchdog: State=Ready Enabled=True
task Pokebot-Ops-Backup: State=Ready Enabled=True
STOP exists: False
ATTENTION.md exists: False
ops park folder exists: False
clone git status --porcelain: [] (0 lines)
clone HEAD: c69ee31e
agent.lock: 5372
learner.log bytes: 73767

round 3: park_tuner.py status (no --apply): exit 0, 3832 ms
         park_tuner.py park   (no --apply): exit 0, 3812 ms
         park_tuner.py resume (no --apply): exit 0, 3776 ms
```

`status` (final tool, verbatim). The spec requires RUNNING, round ai0054, 12 lanes and the three tasks ON; it says so:

```text
RUNNING: the bot tuner is running (round ai0054, 12 lanes); nothing is parked.
  Learner:    agent.lock names PID 5372: alive, and it is the learner
  Round:      ai0054, started 4:30 PM, 720 minutes; ends about 4:30 AM tomorrow
  Processes:  12 lanes, 1 batch, 2 learner/launcher
  STOP:       absent
  ATTENTION:  none
  Window:     the tuner's run_agent.ps1 window is open (PID 10588): it runs the learner
  Tasks:      Pokebot-AI-Learner-Autostart: ON (State Running)
              Pokebot-Ops-Watchdog: ON (State Ready)
              Pokebot-Ops-Backup: ON (State Ready)
  Backup:     last run 1:00 AM: ok
  Last park/resume: none
  Clone:      HEAD c69ee31e (C:\Remote Projects\pokebot-learner)
What to do next: nothing. To park it (only when the user asks): py -3.12 tools/ops/park_tuner.py park --apply (it waits for the round to end).
```

`park` dry run (after the same status block):

```text
DRY RUN of park: nothing was changed. `park --apply` would:
  1. check the clone (ai-agent/DEPLOYMENT) and take the park tool's lock (one park or resume at a time)
  2. place the STOP file (the tuner reads it only BETWEEN rounds: the running round is never cut short)
  3. wait for round ai0054 to end (about 4:30 AM tomorrow), then verify the clean stop on two looks a minute apart (the STOP line in learner.log, the learner gone, its lock released, no batch or lane, the round recorded in state.json, cycles.jsonl and runs.jsonl); give up at 6:00 AM tomorrow (round ai0054 started 2026-10-28 04:30:19 PM + 720 min + 90 min) with TIMEOUT and nothing else changed
  4. switch OFF Pokebot-AI-Learner-Autostart and verify it
  5. switch OFF Pokebot-Ops-Watchdog and verify it
  6. run ONE final backup the nightly task's way and verify it (exit 0, a fresh ok status, and runs.jsonl, cycles.jsonl and state.json in the zip byte-identical to the stopped tuner's); retry once after 2 min
  7. only after a VERIFIED backup: switch OFF Pokebot-Ops-Backup and verify it (a failed backup leaves it ON, and the 1 AM run retries)
  8. read the three tasks again, check nothing runs and STOP is in place, write the report, print the verdict
It would finish about 4:40 AM tomorrow (the round's end plus scoring and the backup).
```

`resume` dry run: `DRY RUN of resume: nothing was changed. resume --apply would: 1. nothing: it is already running
(exit 0)`.

The main checkout's HEAD moved from c69ee31e to f9474661 during the build, and its tree is clean. That is the
orchestrator's own commit; this build wrote nothing there and ran no git command that writes.

## 6. Deviations from the spec, and why

1. **Status exit codes:** RUNNING 0, PARK PENDING 61, PARKED 62, PARTLY PARKED 63, STOPPED NOT PARKED 64, INCONSISTENT
   65, and 50 when the facts cannot be read. The spec asked for one distinct code per verdict without numbers. 1 and 2
   were avoided: Python exits 1 on a crash and argparse exits 2 on a usage error.
2. **`--no-wait` is literal:** it returns PENDING (11) right after step 2 even when the tuner is not running. It NEVER
   touches a task (P5 FAULT arm).
3. **The STOP-line floor when the tool places STOP:** the tool's clock at placement, truncated to the second, not the
   file's mtime. For a STOP already there it IS the mtime (park_watch). It is the same instant in real use, and it lets
   the selftest use a fake clock.
4. **Process matching uses `--clone`:** the clone's path plus a closing backslash, where park_watch used the literal
   `pokebot-learner`. It is identical for the default clone, and a sibling folder `pokebot-learner-old` no longer
   matches.
5. **`attention_reason` follows `tools/ops/watchdog.py`:** the first line that is neither a heading nor a timestamp.
   park_watch took the LAST line, which in the learner's real ATTENTION.md format (`learner.py attention()`) is the
   "Fix the cause, delete this file ..." footer.
6. **Additions to park_watch's `watch`:**
   - (a) A round that starts AFTER the wait began is adopted as the round to see recorded. This covers a park started
     between rounds: the learner sets `current` seconds to minutes after its STOP check, during an update fetch or a
     test run. A DEFAULT deadline moves with it; a given `--deadline` never does.
   - (b) "Not stopped yet" is logged when it changes or at the 15-minute heartbeat, not every minute.
   - (c) TIMEOUT and CANCELLED report the effective deadline.
7. **`check()` with no round at the start:** a wait that began with no round needs state.json readable with `current`
   empty, instead of a recorded round.
8. **Verdict edges:**
   - PARK PENDING = STOP present and ANYTHING of the tuner runs (including the learner dead while its batch runs),
     whatever the tasks read.
   - STOPPED, NOT PARKED = no STOP and nothing runs, whatever the tasks read. Its headline says whether a logon restarts
     it.
   - The spec's parentheticals describe the usual cases; everything else is INCONSISTENT.
9. **resume step 3 also covers running without STOP but with a task OFF.** This state falls between spec steps 2 and 3.
   It switches that task ON and starts nothing (R2 FAULT arm).
10. **resume step 4e:** a live learner but no round line within 10 minutes is RESUMED (0) with a note quoting the log.
    It may be waiting for another batch, or restarting into new code. A learner gone by then is NEEDS PERSON.
11. **Step 5 does not block step 6:** a task that will not switch OFF is reported (PARTIAL) and the backup still runs.
    This is park_watch's rule, with its test ported. The safety gates the spec names hold: no task OFF before the
    verified stop, and the backup task OFF only after a verified backup.
12. **Additions beyond the spec, all tested:**
    - Ctrl+C becomes INTERRUPTED (50): the lock released, STOP kept.
    - The lock is released even when the summary or the first log line fails.
    - A lock whose PID now belongs to another program, or that is unreadable and over a minute old, counts as stale.
    - Status shows a "Window:" line, a "Log tail:" for STOPPED / INCONSISTENT, and TIMEOUT tells how to wait longer.
    - A second guard for FILES (`guard_write`) and the tripwire on `_run`/`_ps`.
    - The N1 never-scan.
13. **Dry runs exit 50** when the facts cannot be read or `--deadline` does not parse; the spec says dry runs exit 0.
14. **More mutants than asked:** 51, where the spec asked for at least 15. One is proved equivalent (section 4.2).

## 7. Open questions for the orchestrator

1. **Stop-ScheduledTask on a DISABLED task's running instance is unverified live.** This is the parked case: the
   -NoExit window is open and the task is disabled. Probing it was forbidden during the build. If Windows refuses,
   resume stops at NEEDS PERSON with the error and changes nothing more; closing the window by hand then lets
   `resume --apply` continue. Worth one supervised look at the first real resume.
2. **A residual race in resume step 4a when NOT parked (no STOP).**
   - `run_agent.ps1` in its 10-minute crash sleep looks idle (only conhost.exe). If it restarts the learner between the
     proof and Stop-ScheduledTask (a window of about 1-2 s), that new learner could be ended with the window during its
     start.
   - While parked, STOP makes a racing start exit at once (the spec's argument).
   - Ruling wanted: accept it, or allow 4a only while STOP exists.
3. **Some STOP exits leave no log line.** The learner's exits on STOP outside the loop top log no `STOP file found`
   line: `sleep_unless_stopped` during an idle wait, the adopt wait, the post-failure wait, and the archive-lock wait.
   - A park started while NO round runs can therefore end UNEXPECTED (40). Re-running `park --apply` then parks it after
     two looks.
   - A one-line learner-side log on those paths would make it clean. That is a learner change, out of scope here.
4. **Confirm the status exit codes** (0, 61-65), or renumber them before anything scripts against them.
5. **`park --apply` can wait in the foreground up to ~13.5 hours.** A session should run it in the background, or run
   `--no-wait` now and `park --apply` after the round.
6. **`run_gates.py` registration** is the orchestrator's (spec section 4). Suggested WHY comment: "the park tool must never
   switch a task before a verified stop, never switch off the nightly backup before a verified backup, never start the
   tuner while STOP exists or a task is OFF, and its selftest must never touch the real machine".

## 8. FIX ROUND (2026-10-28, the same evening)

> The fix round agent, working from the independent mutant sweep (`../sweep/`: 66 mutants, **49 survived**, none of
> them equivalent) and the adversarial review (`../review/`: verdict FIX, findings F1-F12, 10 spec gaps). The rules
> were the build's: NOTHING was written into the main checkout or the deployment clone, no `--apply` ran against the
> real machine, no STOP was placed or deleted, no task was switched, started or stopped, no backup ran, and no heavy
> suite ran. The only commands that touched the live machine were read-only: `status`, `park` and `resume` without
> `--apply`, `Get-ScheduledTask`, `Get-CimInstance Win32_Process`, `git status` / `rev-parse` on the clone, and one
> read of the clone's `runs.jsonl` / `cycles.jsonl` (the review's own `probe_rows.py`).
>
> **Headline: every review finding and every sweep survivor is fixed, each with a FAULT arm that fails on the old
> behaviour (shown by a revert mutant) and a CONTROL arm that passes. Ten spec gaps were fixed in the code; they are
> deviations from the spec, listed in 8.3. Section 8.4 has the proof, and 8.5 lists what stays open.**

### 8.1 The files now

| file | lines | bytes | sha256 |
|---|---|---|---|
| `tools/ops/park_tuner.py` | 2277 | 123,657 | `5381b498be821d2701a457e3431b36583682e450f9cd6fdb4f5acc40bdf36585` |
| `tools/story-dev/selftest_park_tuner.py` | 2807 | 171,862 | `86cc1d28714477116c2766da8004b837ef9b57428d0d770c4f27bf75c4201732` |
| `mutants_final.py` (fix-round harness, not for the repo) | 440 | 31,076 | `5e7a4881a9a30d4b6c60859c0d9151e3946ea53b4b6ace4f092f1d21150f7e81` |

- **To install:** the same two `tools/...` files at the same relative paths.
- **New:** the selftest's test X reads the repo's own `ai-agent/learner.py` (by AST, never imported) and imports
  `tools/ops/backup_learner.py` (stdlib only, no side effects). Both are already in the repo.
- `build/ai-agent/learner.py` (`8b1ebc37...`) and `build/tools/ops/backup_learner.py` (`fae90250...`) are
  byte-identical COPIES of the main checkout's files. They exist only so the scratch layout runs: **do not install
  them.** A missing file fails test X; it is never skipped.
- The builder's originals are kept for diffing at `../fixround/orig/` (`475d4efb...`, `1655fc21...`).
- Tool diff: +704 / -165 lines. Selftest: 129 checks became **263**, and it still runs in about 8 s (limit 60 s).

### 8.2 What was fixed, and the arm that proves each

**The review's findings (all 12 fixed).** "Revert" names the mutant in `mutants_final.txt` that puts the old behaviour
back into the final code; each must be CAUGHT (8.4).

| id | the change (park_tuner.py) | the arms that prove it | revert |
|---|---|---|---|
| F1 MAJOR | A park --apply now records its phase in its lock (`waiting` from STOP on, `parking` from the first Disable), with its poll. `resume --apply` against a live park --apply in phase `waiting` with STOP in place CANCELS it: it checks ATTENTION.md, deletes STOP (that park's designed CANCELLED path), waits up to the park's poll + 90 s for it to release the lock, takes the lock and goes on as a resume (verdict PARK CANCELLED). A park in any other phase, or whose lock names no usable PID, is refused with advice that names the real next step. `park_apply` checks STOP once more before the first Disable (gone -> CANCELLED, no task touched). `status` and the dry runs show the lock ("Park tool: park --apply (PID N, since T) is WAITING ..."), and the PARK PENDING advice names the real cancel. Functions: `cmd_resume_apply`, `waiting_park`, `cancel_waiting_park`, `resume_apply`, `acquire_tool_lock`, `set_tool_lock_phase`, `lock_refusal`, `tool_lock_view`/`_text`, `gather`, `next_step`, `resume_plan`, `cmd_park_dry`, `park_apply` | L1 CONTROL cancel -> PARK CANCELLED; L1 FAULT phase `parking`, phase-less lock, unusable PID, STOP already gone ("ENDING"), a park that never ends, ATTENTION.md; L1 the phases recorded; L1 late cancel -> CANCELLED; S waiting / stale / resume-holder; D waiting | R-F1a..g, N04, N07, N08, N14, N15, N17 |
| F2 MAJOR | Resume's step 3 is chosen by the clone's LEARNER (`learner_alive`), never by any tuner process. A learner that has already found STOP (its STOP line at/after STOP's time) is waited for (5 min, bounded) and started again the step-4 way. It is looked for before the delete, after a 5 s settle, and once more after the tasks step (the review's probe3 timing). A learner gone without a STOP line -> NEEDS PERSON, with the log's tail and no false claim that run_agent.ps1 restarts it. Functions: `resume_apply`, `resume_while_running`, `restart_stopping_learner`, `wait_learner_gone` | R3 FAULT learner dead + batch running -> nothing changed; R3 CONTROL boundary before / during / still exiting at the next look / late -> RESUMED (never PARK CANCELLED); R3 FAULT never exits; R3 CONTROL another checkout's learner | R-F2a..c, N05, N06, N16, N19 |
| F3 MINOR | A path-less `learner.py run` counts only when it runs under the clone's run_agent.ps1 window (by ParentProcessId), holds the clone's agent.lock, or launched its holder. Any other one is listed by status as "not this clone's" and blocks nothing. Functions: `_ancestors`, `clone_learners`, `trainer_processes` (new signature with `paths` and `lock_pid`), `other_learners`, `look`, `check`, `idle_window_proof`, `status_lines` | M FAULT --dev learner / test child / grep loop; M CONTROL hand-started learner + launcher via the lock; S CONTROL PARKED with another learner listed; R4 unit; R3 | R-F3, N01, N02, N03 |
| F4 MINOR | `check()`: agent.lock blocks the clean stop only while a LIVE learner holds it, or it cannot be read; a dead PID's lock is a crash leftover, so UNEXPECTED is reachable after a hard kill. TIMEOUT is worded from the last look, and never says "still running" when nothing ran. Functions: `check`, `lock_word`, `summary`, `timeout_why`, `park_wait` | P2 CONTROL dead-PID lock; P2 FAULT live lock, unreadable lock; P2 hard kill -> UNEXPECTED (40); P2 TIMEOUT wording both ways, in the verdict line AND the logged reason | R-F4a, R-F4b, N12 |
| F5 MINOR | The PARKED line says what was proven: "stopped after round X, which is recorded" only after the waited clean stop. Otherwise "stopped between rounds", "nothing ... was running, and no round was left unrecorded", or "round X was left UNRECORDED ...". PARTIAL no longer claims the tuner is stopped. Functions: `parked_text`, `park_wait`, `park_final`, `VERDICT_TEXT` | P2 e2e clean; P6 CONTROL and FAULT (unrecorded); P2 between rounds | R-F5 |
| F6 MINOR | --clone is turned into its spellings before matching: absolute (a relative --clone), \\\\?\\ stripped, 8.3 parts expanded (GetLongPathNameW), and the resolved path (a junction's target). Tokens match any of them. Functions: `_strip_ext`, `_long_path`, `clone_spellings`, `_token`, `Paths`, `window_processes` | M CONTROL relative, \\\\?\\, forward-slash, upper case, 8.3, junction; M FAULT end to end: a RELATIVE --clone with orphaned lanes does NOT park | R-F6, N18 |
| F7 MINOR | Running with a task OFF: verdict **TASKS ON** ("... Nothing was started."), never "RESUMED: the tuner was started". `resume_while_running`, `VERDICT_TEXT` | R2 FAULT | R-F7 |
| F8 MINOR | Step 4a happens only while STOP exists. When not parked, resume places a STOP of its own: its text names resume --apply and says resume deletes it again. run_agent.ps1 checks STOP before EVERY learner start, its 10-minute crash wait included. The proof is taken before any change, then again after a 5 s settle. After the window is gone, a last look must find no learner, batch, lane or live lock, and STOP is deleted only then. `resume_from_stopped`, `place_stop(by=)`, `end_idle_window` | R4 CONTROL not parked; R4 FAULT a racing start during the settle; R4 FAULT a learner appearing as the window ends; R4 FAULT that STOP cannot be placed (2 ways); R4 FAULT Stop-ScheduledTask fails | R-F8a..c, N09, N10, N11, N20, N21 |
| F9 MINOR | Two STOP exits that log no STOP line count as clean: the restart into new code (`code changed ... restarting into it`, exit 3, after which run_agent.ps1 finds STOP), and, for a wait that began with no round, a silent STOP exit with no `learner CRASHED` line since STOP. Functions: `RESTART_LINE`, `CRASH_LINE`, `last_line_since`, `check` | P2 CONTROL restart -> PARKED; P2 CONTROL between rounds -> PARKED; P2 FAULT a crash between rounds -> UNEXPECTED | R-F9a..c |
| F10 MINOR | Selftest test X ties the tool to `ai-agent/learner.py` itself (AST): TIME_FMT and log()'s line format; the eight paths; each of the five log patterns must match a line rendered from the learner's real f-string at a PM time; the 12-hex signature. The FAULT arms reword the learner's source. A CONTROL reads the same learner written differently (annotated constants, renamed parameter and local, a repeated constant) alike, so the gate gives no false alarm. That arm was fault-tested by weakening its parser twice: it fails both times (`../fixround/faulttest_x_parser.py`). It also ties the tool to `backup_learner.py`: `source_files()` member names, and `stamp()` | X (23 checks) | R-F10a..f |
| F11 NIT | A first good look gets its confirming look even past the deadline. A look at a learner still holding its lock resets the count. `watch` | P2 CONTROL confirm; P2 FAULT a learner that comes back holding its lock after a first good look: the count resets and the deadline still ends the wait (this reset is what makes the confirming-look rule terminate) | R-F11, N13 |
| F12 NIT | `Run.log` appends to the log BEFORE it prints, and a failed print is ignored. `finish` writes the log line, the report and the summary each on its own. The docstring, the park plan and status warn that park --apply waits in the foreground: run it detached, or use --no-wait. | L1 FAULT broken console; D the plan's warning | R-F12a, R-F12b |

**Found by this round's own re-read, and fixed the same way.**

| what was wrong | the change | the arm | mutant |
|---|---|---|---|
| A resume that stopped early (e.g. an Enable failed) after placing its own STOP for the window left a state that status called PARTLY PARKED with "run park --apply to finish". A cold session would PARK a tuner the user wanted running. | `stop_by_resume`, `headline`, `next_step`, `RESUME_STOP_MARK`: such a STOP is named on the FIRST line, and the next step is "run resume --apply again to finish the resume" | S FAULT end to end (a real resume stops early, then status) | N22 |
| The "let the running --apply finish" advice existed for PARK PENDING only. During PARTLY PARKED, for example, while a park is in its `parking` phase, status advised a park --apply that would be refused. | `next_step`: any verdict with a live non-stale lock holder gives the wait advice | S FAULT PARTLY PARKED with a park in phase `parking` | N17, N23 |
| `Paths(...)`, which now asks Windows for --clone's spellings, was built outside `main`'s try: a --clone that cannot be spelled escaped as a traceback | `main`: built inside the try (INTERNAL ERROR, exit 50, with the reason) | C1 FAULT | N24 |

**The sweep's 49 survivors (all now CAUGHT; 8.4).** Most survived for one reason. A fixture took its value FROM the
tool: STOP's path, the DEPLOYMENT and ATTENTION.md paths, the time format, and the zip member names. So a wrong value
round-tripped. The selftest now types each one itself (REL, LEARNER_FMT, ZIP_NAMES), places every file at its literal
path and writes every time in the learner's format, and test X checks those against learner.py and backup_learner.py.
The others lacked an arm.

| survivors | the new arm(s) |
|---|---|
| S21, S22, S23, S24 | X (TIME_FMT, PM lines); literal "04:30:19 PM" fixtures (P4, S); R6 a resume at 1:00 PM; S 12-hour times |
| S31, S32, S50 | X paths; C1 marker only at the clone root; R1 literal ATTENTION.md; P1 literal ai-agent/STOP |
| S45, S46, S47, S48, S49 | P3 backups with LITERAL member names: runs.jsonl 60 bytes short, state.json another document, ok missing, 3 h stale on the same day, runs.jsonl missing from the zip, a corrupt zip, a zip that is gone |
| S58, S59, S60, S61 | RE: RealEnv with canned PowerShell (Enabled read and raised on failure), pid_alive on this process and an exited child, run_backup's working folder |
| S10, S11, S12, S05, S06, S07, S52, S34 | P3 during the backup (STOP gone, a learner started, a task back ON); P3 the order; P3 STOP not placed / not there; P3 one dated report; P7 only the backup task disabled |
| S01, S02, S03, S04, S36 | P2 units (same second, old ATTENTION.md, a base learner the matcher misses, extra rows); P2 re-entry over an old STOP |
| S14, S15, S54, S55, S56, S57, S33, S43, S17, S20, S42 | R4 empty lock; R4 window gone / State stuck; R6 dies at 5 min; R2 silent Enable; R3 read-only STOP; S orphaned batch; R1 running + ATTENTION; R6 Ctrl+C; R6 replaced log; P4 60-minute round; C1 --poll 0 |
| S25, S26, S28, S29, S37, S38, S39, S40, S51 | L1 alive-but-unlisted holder; L1 resume holder; G1 every writer refused at a (stand-in) real path; M forward slashes, full-path learner, park_tuner/park_watch outside tools\\ops; P1 the exclusive create |

**What the real data says about one tightened rule (S04).** The clean stop needs runs.jsonl's rows for the round to
EQUAL the cycle's `runs`. The review's read-only `probe_rows.py` on the clone shows this holds for all 52 learner
rounds. The only mismatch is a manual `ingest` row from 2026-10-01, which is not a learner round. So `>=` would only
loosen a rule that is exact in practice.

### 8.3 The spec gaps the review raised, fixed in the code (deviations from the spec)

1. **3.3 step 3 vs 3.4: a waiting park could not be cancelled.** It now can: resume --apply cancels a park --apply in
   phase `waiting` (F1). Spec 3.4's "one --apply at a time" is kept: the resume only deletes STOP until the park has
   released the lock.
2. **3.3 step 4a, not parked: the crash-wait race.** It is closed: the window is ended only while STOP exists, and
   resume places STOP itself when it must (F8). Spec 3.4 says resume only DELETES STOP. Now it also places one for a
   few seconds, and deletes it before the start. If a run stops in between, that STOP stays, so the tuner stays
   stopped (the safe side), and the STOP's text says how to finish.
3. **3.3 step 3: the learner, not any process, chooses the step;** the learner-alive check comes BEFORE any change (F2).
4. **3.2 step 3: "the lock released" became "no LIVE learner holds the lock (or it is unreadable)"** (F4).
5. **3.2 step 3: silent STOP exits.** The exit-3 restart and a between-rounds silent exit are clean (F9). A silent exit
   while a round was current (the adopt wait) stays UNEXPECTED, which is right: that round IS unrecorded. A re-run then
   parks it, with the UNRECORDED note.
6. **Section 2: `learner.py run` is scoped to the clone** (F3).
7. **--clone spelling: resolved, not refused** (F6). The review's other option, forbidding --clone with --apply, was
   not taken, because canonical spellings fix the cause. Probe8b shows the review's 8.3 example
   `C:\REMOTE~1\POKEBO~1` is, on this machine, the MAIN CHECKOUT (Pokebot_Gen3_Enhancement), not the clone. So "0 of
   15" was the right answer for it. The clone's real short name, `C:\REMOTE~1\PO7209~1`, sees all 15.
8. **The PARKED line carries the caveat** (F5).
9. **4a before 4b reversed: the three tasks are switched ON first, still under STOP,** so Stop-ScheduledTask never has
   to work on a DISABLED task's running instance. The build's open question 1 (unmeasured live) is now moot.
10. **Section 4: the gate cross-checks the learner's real log lines, paths and time format** (F10, test X).

### 8.4 The proof (all on the frozen bytes in 8.1)

**1. The selftest, three runs in a row** (`../fixround/three_runs_final.py` -> `../fixround/three_runs_final.txt`,
verbatim):

```text
park_tuner.py sha256 5381b498be821d2701a457e3431b36583682e450f9cd6fdb4f5acc40bdf36585
selftest_park_tuner.py sha256 86cc1d28714477116c2766da8004b837ef9b57428d0d770c4f27bf75c4201732
--- run 1 (started 08:31:05 PM): exit 0, wall 8.0 s, 263 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git (RealEnv's own code ran only against canned answers)
ALL PASS (263 checks, 0 failed, 7.8 s)
--- run 2 (started 08:31:13 PM): exit 0, wall 8.0 s, 263 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git (RealEnv's own code ran only against canned answers)
ALL PASS (263 checks, 0 failed, 7.9 s)
--- run 3 (started 08:31:21 PM): exit 0, wall 8.0 s, 263 check lines, 0 FAIL lines; its last 2 lines verbatim:
PASS G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or git (RealEnv's own code ran only against canned answers)
ALL PASS (263 checks, 0 failed, 7.8 s)
```

**2. The mutants, re-run SERIALLY against the final code** (`mutants_final.py`, table `mutants_final.txt`, data
`mutants_final.json`; run 7:59:32 PM to 8:30:48 PM, harness exit 0):

```text
CONTROL before (unmutated): exit 0, ALL PASS (263 checks, 0 failed, 8.7 s)
CONTROL after (unmutated):  exit 0, ALL PASS (263 checks, 0 failed, 8.6 s)
MUTANTS: 173 run; CAUGHT 172, EQUIVALENT (proved) 1, SURVIVED 0 []; controls both ALL PASS
by group: builder 46 CAUGHT + 1 EQUIVALENT (M33); builder* (re-expressed) 4 CAUGHT; sweep 61 CAUGHT;
          sweep* (re-expressed) 5 CAUGHT; fix-revert 32 CAUGHT; new-code 24 CAUGHT
```

- **What ran.** All 51 builder mutants; all 66 sweep mutants (the 49 survivors, and the 17 the sweep had already
  caught, as a regression check); a revert of every fix (32 `R-` mutants); and 24 `N-` mutants of the code this round
  added.
- **Re-expressed (9).** Nine old mutant texts no longer exist in the fixed code, so they were re-expressed as the
  same fault on the new code: M15, M16, M39, M44, S03, S19, S33, S56, S63. Each row says how.
- **M33 is EQUIVALENT, proved mechanically as in the build.** The original and the mutant count the same 15 tuner
  processes and no window on 28 real shapes and window spellings: the inclusion rule already rejects every window
  shape.
- **This is the second full run on these files' line.** Run A (`../fixround/out/runA_*`, against the previous selftest
  bytes, with the same tool) caught 169, and three survived: R-F2c, N12 and N13. Each was a gap in a NEW arm, not an
  equivalent mutant:
  - **R-F2c:** a learner still exiting when the next look comes was untested.
  - **N12:** TIMEOUT's logged reason, as distinct from its verdict line, was unchecked.
  - **N13:** the not-cheap look's reset is what makes the confirming-look rule end. Without it, a learner that comes
    back after a first good look would make the wait endless.

  Three arms were added for them; a targeted check showed each caught (`../fixround/check_some.py`); then this full
  run B.
- **Earlier partial runs.** Four earlier full-run attempts were stopped part-way to fold in late fixes and arms
  (after 67 mutants, about 1 minute, 21 mutants and about 5 minutes). Their output counts for nothing, but the first
  is kept as `../fixround/out/preview_run_superseded_files_67of162.txt` (67 caught, 0 survived).

**3. The live READ-ONLY controls** (`../fixround/live/live_controls.ps1`; two bracketed rounds, the final tool
`5381b498...`). Each round:
- Before: the builder's read-only `live_evidence.ps1`.
- Then `park_tuner.py status`, `park` and `resume`, all WITHOUT `--apply`, run with `PARK_TUNER_SELFTEST=1` as a
  safety net (any changing RealEnv method or write into the real clone or ops folder would have raised).
- After: `live_evidence.ps1` again.

```text
round 1  before 08:31:39 PM / after 08:31:51 PM  -> differences: NONE: identical
round 2  before 08:32:03 PM / after 08:32:15 PM  -> differences: NONE: identical
status exit 0 (3389 / 3274 ms), park exit 0 (3173 / 3197 ms), resume exit 0 (3232 / 3241 ms)

after (round 2), identical to before:
task Pokebot-AI-Learner-Autostart: State=Running Enabled=True
task Pokebot-Ops-Watchdog: State=Ready Enabled=True
task Pokebot-Ops-Backup: State=Ready Enabled=True
STOP exists: False
ATTENTION.md exists: False
ops park folder exists: False
clone git status --porcelain: [] (0 lines)
clone HEAD: c69ee31e
agent.lock: 5372
learner.log bytes: 74638
```

`status` (final tool, verbatim). It says RUNNING, round ai0054, 12 lanes, and the three tasks ON, as spec 5.3 asks:

```text
RUNNING: the bot tuner is running (round ai0054, 12 lanes); nothing is parked.
  Learner:    agent.lock names PID 5372: alive, and it is the learner
  Round:      ai0054, started 4:30 PM, 720 minutes; ends about 4:30 AM tomorrow
  Processes:  12 lanes, 1 batch, 2 learner/launcher
  STOP:       absent
  ATTENTION:  none
  Window:     the tuner's run_agent.ps1 window is open (PID 10588): it runs the learner
  Tasks:      Pokebot-AI-Learner-Autostart: ON (State Running)
              Pokebot-Ops-Watchdog: ON (State Ready)
              Pokebot-Ops-Backup: ON (State Ready)
  Backup:     last run 1:00 AM: ok
  Park tool:  no park or resume --apply is running
  Last park/resume: none
  Clone:      HEAD c69ee31e (C:\Remote Projects\pokebot-learner)
What to do next: nothing. To park it (only when the user asks): py -3.12 tools/ops/park_tuner.py park --apply (it waits for the round to end: run it detached, or --no-wait now and park --apply after the round).
```

The `park` dry run printed the plan with the foreground warning in step 3 and "It would finish about 4:40 AM
tomorrow". The `resume` dry run printed "1. nothing: it is already running (exit 0)". The ops folder's other files
are the watchdog's own (written at its 8:30 PM run); no `park` folder was created.

**4. The review's own probes, re-run on the final bytes** (`../fixround/review_new/`, output `probe_outputs_new.txt`;
the probes run on a FakeEnv copy, never the real machine):

| probe | before (the review) | now |
|---|---|---|
| 1 cancel while a park waits | resume REFUSED, STOP kept | 1b (the lock the fixed park writes): status shows the waiting park; resume -> **PARK CANCELLED (0)**, STOP gone, the park's lock released. probe1 as written (a lock with NO phase, which the fixed park never writes) is still refused, with "it does not say what it is doing" |
| 2 a task OFF while running | "RESUMED: ... started" | **TASKS ON (0)**: "Nothing was started" |
| 3 the boundary race | NEEDS PERSON, "run_agent.ps1 restarts ..." (false) | the STOP line is recognised, the learner waited for, the window ended under STOP, started; it ends NEEDS PERSON only because this probe's fake start does nothing ("no start seen"). R3's arm, with a start, gives RESUMED |
| 4 a hard kill | TIMEOUT "still running" | **UNEXPECTED (40)**, `lock=dead-pid` |
| 5 / 5b strangers | counted as this clone's | not counted; PARKED stays PARKED; resume -> RESUMED; park -> PARKED (5 calls the old signature) |
| 7 / 7b silent exit; deadline | UNEXPECTED; TIMEOUT | **PARKED** "stopped between rounds"; **PARKED** after the confirming look (7 has no fake backup, so it ends PARTIAL there) |
| 8 / 8b spellings | relative, 8.3, \\\\?\\ saw 0 of 15 | all see 15; the review's 8.3 example is the main checkout (0 of 15 is right); the clone's real `PO7209~1` sees 15 |
| 9 a relative --clone, orphaned lanes | PARKED with 12 lanes running | **TIMEOUT (20)**, no task touched, 12 lanes counted |
| 10 the headline | "its round recorded" over an UNRECORDED note | "**round ai0054 was left UNRECORDED** (the learner scores it at its next start)" |

### 8.5 What stays open (for the orchestrator)

1. **The first real resume should be watched.** Live Enable / Stop-ScheduledTask behaviour on these tasks stays
   unmeasured (it was forbidden). Resume now enables BEFORE it stops the old window, so Stop always acts on an ENABLED
   task (the build's open question 1 is moot). Any failure there ends NEEDS PERSON with STOP still in place.
2. **The status exit codes (61-65) are unchanged.** They are the orchestrator's call (the build's open question 4).
3. **The selftest now reads `ai-agent/learner.py` and imports `tools/ops/backup_learner.py`.** A learner change that
   rewords a log line, moves a path or changes its time format will turn this gate RED. That is the point (F10). The
   fix is to update the tool's pattern together with the learner. Harmless rewrites do not trip it (the X CONTROL
   above).
4. **Two known edges are left as they are, both on the safe side:**
   - A learner started BY HAND outside the task's window is not counted until it writes agent.lock (about a second
     after it starts). The two-look rule and the lock cover it.
   - A silent STOP exit while a round was current (the adopt wait) ends UNEXPECTED. That is right, because that round
     is unrecorded; a re-run parks it with the UNRECORDED note.
5. **The review's other options, not taken:**
   - F9's learner-side fix (a log line on every STOP return) is a learner change, out of scope.
   - F6's "forbid --clone with --apply": --clone is resolved instead.
6. **`run_gates.py` registration is the orchestrator's** (spec section 4). The selftest runs in about 8 s, writes
   only temp folders, and the build's suggested WHY comment still fits.
7. **A session must run `park --apply` DETACHED, or use `--no-wait`** and then `park --apply` after the round. The
   docstring, the dry-run plan and status's next step all say so.
