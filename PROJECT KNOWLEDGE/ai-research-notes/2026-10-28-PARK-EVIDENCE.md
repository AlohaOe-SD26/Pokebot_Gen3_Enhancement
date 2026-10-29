# The bot tuner's PARK watcher: its 2026-10-28 run (CANCELLED by USER RULING 50) and its source, VERBATIM

> **A record, not a spec.** USER RULING 49 scheduled a park for the end of round ai0053; USER RULING 50 cancelled it
> at 2:26 PM by deleting the STOP file, and the watcher took its cancel exit (30) and changed nothing (`06`, `07`
> 2026-10-28). ✅ **REPLACED the same day by the park tool, `tools/ops/park_tuner.py`** (`03`
> `#28-trainer-improvements` (10); `04` PARK; `06` 2026-10-28): park and resume with it, and do not copy the watcher
> out. Section 5 stays as the record of the watcher the tool's park step was ported from.

## Contents
1. The watcher's report (`park_report.json`)
2. The watcher's log (`park_watch.log`)
3. The Windows tasks, the STOP file and the last backup, read when this note was written
4. The runbook written for the park (`PARK-RUNBOOK.md`)
5. The watcher script (`park_watch.py`) and its mutant runner (`mutants.py`)

## 1. The watcher's report

Exit 30 (0 = PARKED, 10 = stopped with something for a person, 20 = timeout, 30 = STOP removed, 40 = stopped unexpectedly, 50 = internal error).

```json
{
  "watch_exit": 30,
  "watch": {
    "why": "the STOP file was removed: the park is CANCELLED; nothing was changed"
  },
  "exit": 30,
  "finished": "2026-10-28 02:26:38 PM"
}
```

## 2. The watcher's log

```text
[2026-10-28 11:27:38 AM] watch started: round ai0053, learner pid 22464, STOP placed 2026-10-28 11:16:22 AM, deadline 2026-10-28 06:30:00 PM
[2026-10-28 11:27:38 AM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 11:42:38 AM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 11:57:38 AM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 12:12:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 12:27:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 12:42:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 12:57:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 01:12:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 01:27:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 01:42:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 01:57:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 02:12:38 PM] waiting: ai0053 still running (learner pid 22464 alive, lock held); the deadline is 2026-10-28 06:30:00 PM
[2026-10-28 02:26:38 PM] DONE: exit 30; report C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8\scratchpad\s53\park\park_report.json
```

## 3. The Windows tasks, the STOP file and the last backup

`Get-ScheduledTask` (`Enabled` is `Settings.Enabled`, the truth for OFF: a disabled task whose window is still open can read `Running`):

```text
2026-10-28 02:33:22 PM

TaskName                       State Enabled
--------                       ----- -------
Pokebot-AI-Learner-Autostart Running    True
Pokebot-Ops-Backup             Ready    True
Pokebot-Ops-Watchdog           Ready    True



STOP file exists: False
```

`%LOCALAPPDATA%/pokebot-ops/backup_status.json`:

```json
{
 "time": "2026-10-28 01:00:01 AM",
 "ok": true,
 "dest": "Z:\\pokebot-backups\\learner",
 "zip": "Z:\\pokebot-backups\\learner\\learner-data-20261028-0100.zip",
 "bytes": 1572284,
 "warnings": [],
 "error": null,
 "pruned": [],
 "n_files": 147,
 "bytes_raw": 13677436,
 "runs_lines": 3314
}
```

## 4. The runbook written for the park

Written for USER RULING 49's park; its exit-0 steps never ran. The exit-30 path it describes is the one taken.

```markdown
# PARK RUNBOOK (2026-10-28, USER RULING 49)

The user approved parking at 4:28 PM. They will be home around 5 PM and start a different project. Before then the park
must be DONE and REPORTED: the tuner stopped, its 3 Windows tasks off, docs final, everything pushed.

## Already done
- 11:16:22 AM: the STOP file was placed at `C:/Remote Projects/pokebot-learner/ai-agent/STOP`. It is git-ignored
  (`ai-agent/.gitignore:7`) and the clone's tree is clean.
- 11:27:38 AM: the watcher started (background task `bzd4apk2e`): `park/park_watch.py --live --deadline "2026-10-28 06:30:00 PM"`.
  - Log: `park/park_watch.log`. Report: `park/park_report.json`.
- Proof:
  - selftest 35/35;
  - mutants 8/8 caught;
  - live `--check-once` read ai0053 as running (15 processes, lock held);
  - `--probe-tasks` switched Pokebot-Ops-Backup off and on through the script's own functions.
- Docs: USER RULING 49 in `06`, PARK SCHEDULED in `07`, and the PARK paragraph plus RESUME steps in `04`. Commit and
  push them after the Tier 1 review.

## E2 + O8 (before the park)
- The code is cherry-picked onto main with --no-commit: b3a54290 and 300ab630, now STAGED.
  - test_agent.py: 357 checks, ALL PASS in main.
- 02, 03, 04 and 05 are already applied (e2o8_docs_a.py). The evidence note `ai-research-notes/2026-10-28-E2-O8-BUILD-EVIDENCE.md` is written.
- The full lane is task `brrzjf10l`, started 12:01 PM, with its log in `s53/lane_e2o8.log`.
  - Do NOT edit 06, 07, 08, CLAUDE.md, ai_player/** or ai-agent/scoring.py while it runs.
- After the lane PASSES:
  1. Run `py -3.12 -I s53/e2o8_docs_b.py` (06, 07, 08 and the 04 lane cell; it refuses unless the lane passed).
  2. Rebuild the rulings index and run its --check.
  3. Run Tier 0, then Tier 1.
  4. Make ONE commit with explicit paths: the code, the evidence note, docs 02-08 and RULINGS.*, plus the lane's `ai_player/evidence` files.
  5. Push. Confirm the clone does NOT update, because STOP is read first.

## When the watcher exits (the notification for task bzd4apk2e)
- On exit 0, the final docs are `py -3.12 -I s53/park_docs_final.py`.
  - It reads the report and learner.log.
  - It refuses unless the park is clean and the live tasks read disabled.
  - It writes 04, 03 and 07.
  - The `--dry-run` passed at 12:10 PM.

### exit 0 (PARKED)
1. Verify independently:
   - `Get-ScheduledTask` Settings.Enabled is False for all 3;
   - no learner, x4 or lane processes;
   - `learner.log` has the STOP line;
   - `backup_status.json` is fresh and ok.
2. `py -3.12 -I s53/park/park_evidence_note.py`: writes `ai-research-notes/2026-10-28-PARK-EVIDENCE.md` (the report,
   the log, learner.log at the stop, the tasks and backup read now, this runbook and the watcher script, verbatim).
3. `py -3.12 -I s53/park_docs_final.py`: 04, 03 and 07. It refuses without the note and without OFF tasks. Its dry run
   at 1:20 PM projected 04 at 65,457 bytes against the 66,403 ceiling, so no trim is needed.
4. Run Tier 0, then Tier 1 (the park diff, P1-P5) and Tier 2 (a cold start from 04 + 00-README only: the first action,
   and could it RESUME with no human input?) in parallel. Fix, re-run Tier 0, and re-run Tier 2 if its finding was
   fixed.
5. `py -3.12 -I s53/park/park_commit_msg.py --tiers "<results>" --cost "<cost>"` writes `s53/commit-park-final.txt`.
   Commit with explicit paths (04, 03, 07 and the new note), using `-F`. Push, then check `git rev-parse HEAD origin/main`.
6. Update the memory file `project-pause-plan.md` with the PARKED state.
7. Report to the user in plain English with 12-hour times: the trainer's idle window is safe to close.

### exit 10 (STOPPED, in part)
Read `needs_person` in the report.
- Backup failed: run `py -3.12 -B "C:/Remote Projects/pokebot-learner/tools/ops/backup_learner.py"` by hand and read
  `%LOCALAPPDATA%/pokebot-ops/backup_status.json`. If it is OK, disable Pokebot-Ops-Backup.
- A task did not switch off: run `Disable-ScheduledTask -TaskName <name>`.
- ATTENTION.md: record its reason in `04` for the resume.

### exit 20 (TIMEOUT at 6:30 PM)
Do NOT kill anything. Report to the user. STOP stays in place, so the tuner stops at its next boundary.

### exit 30 (CANCELLED: STOP removed)
Someone removed it. Report and change nothing.

### exit 40 (STOPPED UNEXPECTEDLY)
Read `learner.log`. The data is safe: `adopt_unfinished` scores an unrecorded batch at the next start. Since the tuner
IS stopped and STOP is in place, it is safe to disable the 3 tasks by hand (after a manual backup). Document it.

### exit 50 (internal error)
Read the log, then do the manual steps:
1. Verify the stop.
2. Run the backup by hand.
3. Disable the 3 tasks.
4. Verify Settings.Enabled is False for each.

## RESUME (later, only when the user says so)
1. Run `Enable-ScheduledTask` for Pokebot-AI-Learner-Autostart, Pokebot-Ops-Watchdog and Pokebot-Ops-Backup.
2. Delete `C:/Remote Projects/pokebot-learner/ai-agent/STOP`.
3. Close the old tuner window. Its -NoExit window keeps the autostart task "Running", so a start is ignored while it
   is open.
4. Run `Start-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart`, or log off and on.
5. Check `learner.log`:
   - "learner started";
   - if E2 + O8 is on main: "code changed ... test_agent.py passes: restarting into it";
   - then "ai0054 ... starting 12 lanes";
   - `state.json.bak` exists;
   - the per-game journal grows as games finish.
```

## 5. The watcher script and its mutant runner

Proof before use: `park_watch.py --selftest` 35/35 PASS; `mutants.py` M1-M8 all CAUGHT; a live `--check-once` read round ai0053 as running (15 tuner processes, lock held); `--probe-tasks` switched `Pokebot-Ops-Backup` off and on through the script's own functions; and on 2026-10-28 its cancel exit ran live (section 2). Run as: `park_watch.py --live --deadline "<YYYY-MM-DD hh:mm:ss AM/PM>"`, after placing the STOP file and while a round runs. It writes its log and report beside itself.

`park_watch.py`:

```python
"""Park watcher for the 2026-10-28 project pause.

The user asked: "4:28pm today works for me ... schedule this safe park/pause for that time but with safety checks ...
it would need to be intelligent and robust to ensure that everything is parked/paused whenever its safe to do so".

HOW IT STAYS SAFE
- The trainer stops ITSELF. Its STOP file (placed 11:16:22 AM) is read by `learner.py` `loop()` only at the top of a
  cycle, before `auto_update`. So the running round finishes, is scored and recorded (`finish_cycle`), and the learner
  exits 0. `run_agent.ps1` then does not restart it, and at any later logon it sees STOP and exits at once.
  THIS SCRIPT NEVER STOPS OR KILLS ANYTHING.
- It WAITS for that, then VERIFIES it from the trainer's own files and the process table, on two looks a poll apart:
  - the "STOP file found: stopping" line in learner.log, dated after the STOP file was placed (or a fresh ATTENTION.md);
  - the learner's PID (from its lock at start) no longer a learner, its lock released, no batch or lane process left;
  - the round that was running at start RECORDED: state.json `current` empty with the tag in its `cycles`,
    cycles.jsonl's last row that tag, and runs.jsonl holding exactly that row's `runs` rows for the tag.
- Only then does it park Windows, each step gated on the one before:
  1. switch OFF the logon autostart and the watchdog, and verify `Settings.Enabled` is False;
  2. run ONE final backup the way the nightly task does, and VERIFY it: exit 0, a fresh ok status, and the zip's
     runs.jsonl, cycles.jsonl and state.json byte-identical to the stopped trainer's files;
  3. switch OFF the nightly backup.
  A failed backup leaves the nightly task ON (tonight's 1 AM run retries it), and the report says so.
- Tasks are DISABLED, never deleted. Resume = Enable-ScheduledTask on the three, delete ai-agent\\STOP, then
  Start-ScheduledTask the autostart.

Exit codes:
- 0 PARKED.
- 10 STOPPED, but parked only in part or with something a person must read (the report says which).
- 20 TIMEOUT: still running at the deadline; nothing changed (STOP stays, so it still stops at its next boundary).
- 30 CANCELLED: the STOP file was removed; nothing changed.
- 40 STOPPED UNEXPECTEDLY: nothing runs, but there is no clean STOP exit or the round is not recorded; nothing changed.
- 50 internal error, or refused to start.

Modes:
- --selftest: fault tests and controls on fixtures.
- --check-once: one live look, no action.
- --probe-tasks: switch the nightly backup off and on again through this script's own functions.
- --live --deadline "YYYY-MM-DD hh:mm:ss AM": the watcher.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from ctypes import wintypes
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLONE = Path("C:/Remote Projects/pokebot-learner")
OPS = Path(os.environ.get("LOCALAPPDATA", "C:/missing-LOCALAPPDATA")) / "pokebot-ops"
TASKS = {"autostart": "Pokebot-AI-Learner-Autostart", "watchdog": "Pokebot-Ops-Watchdog", "backup": "Pokebot-Ops-Backup"}
TS_FMT = "%Y-%m-%d %I:%M:%S %p"  # learner.log, state.json and backup_status.json all use it
STOP_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] STOP file found: stopping")
ZIP_MEMBERS = {"runs": "ai-agent/data/runs.jsonl", "cycles": "ai-agent/data/cycles.jsonl",
               "state": "ai-agent/data/state.json"}
EXIT_PARKED, EXIT_PARTIAL, EXIT_TIMEOUT, EXIT_CANCELLED, EXIT_UNEXPECTED, EXIT_ERROR = 0, 10, 20, 30, 40, 50


class Paths:
    def __init__(self, clone: Path, ops: Path):
        self.clone = clone
        self.agent = clone / "ai-agent"
        self.data = self.agent / "data"
        self.stop = self.agent / "STOP"
        self.attention = self.agent / "findings" / "ATTENTION.md"
        self.log = self.data / "learner.log"
        self.lock = self.data / "agent.lock"
        self.state = self.data / "state.json"
        self.cycles = self.data / "cycles.jsonl"
        self.runs = self.data / "runs.jsonl"
        self.ops = ops
        self.backup_status = ops / "backup_status.json"
        self.backup_script = clone / "tools" / "ops" / "backup_learner.py"


# ------------------------------------------------------------------------------------------------- the live machine
def _ps(command: str, timeout: float = 180) -> subprocess.CompletedProcess:
    """UTF-8 WITHOUT a BOM (a BOM would make "True" read as "\\ufeffTrue"); a stray one is stripped anyway."""
    full = "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; " + command
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", full], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    r.stdout = (r.stdout or "").lstrip("\ufeff")
    return r


class RealEnv:
    """Everything that touches the live machine, so the selftest can replace it whole."""

    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def processes(self) -> list[dict]:
        r = _ps("Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine "
                "| ConvertTo-Json -Compress")
        if r.returncode != 0:
            raise RuntimeError(f"process list failed: {r.stderr.strip()[:300]}")
        data = json.loads(r.stdout)
        return data if isinstance(data, list) else [data]

    def pid_alive(self, pid: int) -> bool:
        """Whether the PID is running. NEVER os.kill(pid, 0) for this: on Windows os.kill with any signal but
        CTRL_C_EVENT / CTRL_BREAK_EVENT calls TerminateProcess, which would KILL the learner."""
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # access denied: it exists; anything else (87): no such process
        try:
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True  # unknown: assume alive (the conservative side)
            return code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)

    def task_enabled(self, name: str) -> bool:
        r = _ps(f"(Get-ScheduledTask -TaskName '{name}' -ErrorAction Stop).Settings.Enabled")
        if r.returncode != 0 or r.stdout.strip() not in ("True", "False"):
            raise RuntimeError(f"cannot read {name}: {(r.stderr or r.stdout).strip()[:300]}")
        return r.stdout.strip() == "True"

    def task_disable(self, name: str) -> None:
        r = _ps(f"Disable-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Disable-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def task_enable(self, name: str) -> None:  # --probe-tasks only
        r = _ps(f"Enable-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Enable-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def run_backup(self, paths: Paths) -> tuple[int, str]:
        """The nightly task's own command (`pyw -3.12 -B backup_learner.py`), with py so its output is kept. -B: no
        __pycache__ is written into the clone; cwd is this folder, never the clone."""
        r = subprocess.run(["py", "-3.12", "-B", str(paths.backup_script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
        return r.returncode, (r.stdout + r.stderr)[-1500:]


# ---------------------------------------------------------------------------------------------------------- reading
def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - unreadable reads as None: the caller treats it as "not yet"
        return None


def last_jsonl(path: Path):
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:  # noqa: BLE001
        return None


def count_rows(path: Path, tag: str) -> int | None:
    try:
        n = 0
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.strip() and json.loads(ln).get("source") == tag:
                n += 1
        return n
    except Exception:  # noqa: BLE001
        return None


def last_stop_line(log: Path, since: datetime) -> str | None:
    """The newest "STOP file found: stopping" timestamp in the log's last 512 KB that is at or after `since`."""
    try:
        with open(log, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 524288))
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    found = None
    for line in text.splitlines():
        m = STOP_LINE.match(line)
        if m and datetime.strptime(m["ts"], TS_FMT) >= since:
            found = m["ts"]
    return found


def short(p: dict) -> str:
    cmd = (p.get("CommandLine") or "").replace("\n", " ")
    return f"{p.get('ProcessId')} {p.get('Name')} {cmd[:120]}"


def trainer_processes(procs: list[dict], self_pid: int) -> list[dict]:
    """Processes that mean the trainer still RUNS: the learner (`learner.py run`; its command line holds no clone path),
    the batch (`x4_headless.py`) and the lanes (`sandbox-pokebot`) of the clone. NOT counted: the idle `run_agent.ps1`
    window (-NoExit keeps it open after a stop), the clone's ops tools (the watchdog and backup tasks: short-lived and
    read-only on the clone), and this script."""
    out = []
    for p in procs:
        if p.get("ProcessId") == self_pid:
            continue
        low = (p.get("CommandLine") or "").lower().replace("/", "\\")
        if "run_agent.ps1" in low or "\\tools\\ops\\" in low or "park_watch.py" in low:
            continue
        if "learner.py run" in low or ("pokebot-learner" in low and ("x4_headless.py" in low or "sandbox-pokebot" in low
                                                                      or "learner.py" in low)):
            out.append(p)
    return out


def pid_is_learner(pid: int | None, procs: list[dict]) -> bool:
    """The PID is alive AND still the learner (a reused PID belongs to someone else)."""
    if pid is None:
        return False
    for p in procs:
        if p.get("ProcessId") == pid:
            return "learner.py" in (p.get("CommandLine") or "")
    return False


def attention_reason(paths: Paths) -> str:
    try:
        lines = [ln.strip() for ln in paths.attention.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return lines[-1][:300] if lines else "(empty)"
    except OSError:
        return "(unreadable)"


# ------------------------------------------------------------------------------------------------------------ logic
def baseline(paths: Paths) -> dict:
    """What the trainer was doing when the watch began: derived from its own files, never hardcoded."""
    if not paths.stop.exists():
        raise SystemExit(f"REFUSED: no STOP file at {paths.stop}; place it first")
    st = read_json(paths.state)
    tag = ((st or {}).get("current") or {}).get("tag")
    if not tag:
        raise SystemExit("REFUSED: no round is running (state.json current is empty): nothing to wait for")
    pid = None
    if paths.lock.exists():
        try:
            pid = int(paths.lock.read_text(encoding="utf-8").strip().split()[0])
        except (ValueError, IndexError, OSError):
            pid = None
    stop_mtime = datetime.fromtimestamp(paths.stop.stat().st_mtime).replace(microsecond=0)
    return {"tag": tag, "pid": pid, "stop_mtime": stop_mtime}


def check(paths: Paths, env, base: dict) -> dict:
    """One full look. `stopped_clean` is True only when every condition holds."""
    r: dict = {"at": env.now().strftime(TS_FMT)}
    r["stop_file"] = paths.stop.exists()
    r["stop_line"] = last_stop_line(paths.log, base["stop_mtime"])
    r["attention"] = (paths.attention.exists()
                      and datetime.fromtimestamp(paths.attention.stat().st_mtime) >= base["stop_mtime"])
    r["lock"] = paths.lock.exists()
    procs = env.processes()
    r["learner_alive"] = pid_is_learner(base["pid"], procs)
    r["trainer_procs"] = [short(p) for p in trainer_processes(procs, os.getpid())]
    st = read_json(paths.state)
    if st is None:
        r["current"], tags = "UNREADABLE", []
    else:
        r["current"] = (st.get("current") or {}).get("tag")
        tags = [c.get("tag") for c in st.get("cycles", []) if isinstance(c, dict)]
    r["in_state_cycles"] = base["tag"] in tags
    last = last_jsonl(paths.cycles) or {}
    r["cycles_last_tag"], r["cycles_last_runs"] = last.get("tag"), last.get("runs")
    r["runs_rows"] = count_rows(paths.runs, base["tag"])
    r["nothing_running"] = not r["lock"] and not r["learner_alive"] and not r["trainer_procs"]
    r["recorded"] = (r["current"] is None and r["in_state_cycles"] and r["cycles_last_tag"] == base["tag"]
                     and r["runs_rows"] is not None and r["runs_rows"] == r["cycles_last_runs"])
    r["clean_exit"] = r["stop_line"] is not None or r["attention"]
    r["stopped_clean"] = r["stop_file"] and r["nothing_running"] and r["recorded"] and r["clean_exit"]
    return r


def summary(r: dict) -> str:
    return (f"stop_line={r['stop_line']} attention={r['attention']} lock={r['lock']} learner_alive={r['learner_alive']} "
            f"procs={len(r['trainer_procs'])} current={r['current']} recorded={r['recorded']} "
            f"(cycles_last={r['cycles_last_tag']} runs={r['cycles_last_runs']} rows={r['runs_rows']})")


def watch(paths: Paths, env, base: dict, deadline: datetime, log, poll: float = 60.0, stable_needed: int = 2,
          unexpected_needed: int = 3, heartbeat_s: float = 900.0) -> tuple[int, dict]:
    stable = unexpected = 0
    last_beat = None
    while True:
        now = env.now()
        if not paths.stop.exists():
            return EXIT_CANCELLED, {"why": "the STOP file was removed: the park is CANCELLED; nothing was changed"}
        if now >= deadline:
            return EXIT_TIMEOUT, {"why": f"still running at the deadline {deadline.strftime(TS_FMT)}; nothing was "
                                         f"changed (STOP stays, so the trainer still stops at its next boundary)"}
        cheap = (last_stop_line(paths.log, base["stop_mtime"]) is not None or not paths.lock.exists()
                 or base["pid"] is None or not env.pid_alive(base["pid"]))
        if cheap:
            r = check(paths, env, base)
            if r["stopped_clean"]:
                stable += 1
                unexpected = 0
                log(f"stopped and recorded, look {stable} of {stable_needed}: {summary(r)}")
                if stable >= stable_needed:
                    return EXIT_PARKED, r
            else:
                stable = 0
                if r["nothing_running"] and r["stop_file"]:
                    unexpected += 1
                    log(f"nothing runs but not a clean recorded stop ({unexpected} of {unexpected_needed}): {summary(r)}")
                    if unexpected >= unexpected_needed:
                        return EXIT_UNEXPECTED, r
                else:
                    unexpected = 0
                    log(f"not stopped yet: {summary(r)}")
        elif last_beat is None or (now - last_beat).total_seconds() >= heartbeat_s:
            log(f"waiting: {base['tag']} still running (learner pid {base['pid']} alive, lock held); the deadline is "
                f"{deadline.strftime(TS_FMT)}")
            last_beat = now
        env.sleep(poll)


def disable_verified(env, name: str) -> str:
    try:
        env.task_disable(name)
        return "OFF" if env.task_enabled(name) is False else "FAILED: still enabled after Disable-ScheduledTask"
    except Exception as e:  # noqa: BLE001 - reported, never raised: the other steps still run
        return f"FAILED: {e}"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_backup(paths: Paths, started: datetime) -> tuple[bool, str]:
    st = read_json(paths.backup_status)
    if not st:
        return False, f"no readable {paths.backup_status}"
    try:
        t = datetime.strptime(st["time"], TS_FMT)
    except (KeyError, ValueError):
        return False, f"status time unreadable: {st.get('time')!r}"
    if t < started.replace(microsecond=0):
        return False, f"status is stale ({st['time']}, the backup started {started.strftime(TS_FMT)})"
    if st.get("ok") is not True:
        return False, f"status ok={st.get('ok')} error={st.get('error')} warnings={st.get('warnings')}"
    zpath = Path(str(st.get("zip")))
    try:
        with zipfile.ZipFile(zpath) as zf:
            for key, member in ZIP_MEMBERS.items():
                live = getattr(paths, key).read_bytes()
                if sha(zf.read(member)) != sha(live):
                    return False, f"{member} in {zpath.name} differs from the stopped trainer's file"
    except (OSError, KeyError, zipfile.BadZipFile) as e:
        return False, f"cannot verify {zpath}: {e}"
    return True, f"{zpath} ({st.get('bytes')} bytes): runs.jsonl, cycles.jsonl and state.json byte-identical"


def park(paths: Paths, env, base: dict, log, retry_wait: float = 120.0) -> tuple[int, dict]:
    rep: dict = {"tasks": {}, "needs_person": []}
    for key in ("autostart", "watchdog"):
        rep["tasks"][key] = disable_verified(env, TASKS[key])
        log(f"{TASKS[key]}: {rep['tasks'][key]}")
        if rep["tasks"][key] != "OFF":
            rep["needs_person"].append(f"{TASKS[key]} was not switched off: {rep['tasks'][key]}")
    ok, detail = False, ""
    for attempt in (1, 2):
        started = env.now()
        try:
            rc, out = env.run_backup(paths)
        except Exception as e:  # noqa: BLE001
            rc, out = -1, f"{type(e).__name__}: {e}"
        ok, detail = (False, f"exit {rc}: {out.strip()[-400:]}") if rc != 0 else verify_backup(paths, started)
        log(f"final backup, attempt {attempt}: {'VERIFIED' if ok else 'FAILED'}: {detail}")
        if ok:
            break
        if attempt == 1:
            env.sleep(retry_wait)
    rep["backup"] = {"verified": ok, "detail": detail}
    if ok:
        rep["tasks"]["backup"] = disable_verified(env, TASKS["backup"])
        log(f"{TASKS['backup']}: {rep['tasks']['backup']}")
        if rep["tasks"]["backup"] != "OFF":
            rep["needs_person"].append(f"{TASKS['backup']} was not switched off: {rep['tasks']['backup']}")
    else:
        rep["tasks"]["backup"] = "LEFT ON (the final backup failed; tonight's 1 AM run retries it)"
        rep["needs_person"].append(f"the final backup failed ({detail}); the nightly backup was LEFT ON")
    final = {}
    for key, name in TASKS.items():
        try:
            final[key] = "ON" if env.task_enabled(name) else "OFF"
        except Exception as e:  # noqa: BLE001
            final[key] = f"UNREADABLE: {e}"
    rep["final_tasks"] = final
    after = check(paths, env, base)
    rep["after"] = {k: after[k] for k in ("stop_file", "nothing_running", "recorded", "trainer_procs", "lock")}
    if not after["stop_file"]:
        rep["needs_person"].append("the STOP file is gone after the park")
    if not after["nothing_running"]:
        rep["needs_person"].append(f"a trainer process is running after the park: {after['trainer_procs']}")
    if after["attention"]:
        rep["needs_person"].append(f"the learner wrote ATTENTION.md: {attention_reason(paths)}")
    return (EXIT_PARKED if not rep["needs_person"] else EXIT_PARTIAL), rep


# --------------------------------------------------------------------------------------------------------- selftest
class FakeEnv:
    def __init__(self, start: datetime):
        self.clock = start
        self.procs: list[dict] = []
        self.alive: set[int] = set()
        self.tasks = {n: {"enabled": True, "fail": False} for n in TASKS.values()}
        self.backups: list = []  # each: a callable(paths, now) -> (rc, out)
        self.on_sleep = None
        self.sleeps = 0

    def now(self):
        return self.clock

    def sleep(self, s):
        self.clock += timedelta(seconds=s)
        self.sleeps += 1
        if self.on_sleep:
            self.on_sleep(self)

    def processes(self):
        return list(self.procs)

    def pid_alive(self, pid):
        return pid in self.alive

    def task_enabled(self, name):
        return self.tasks[name]["enabled"]

    def task_disable(self, name):
        if self.tasks[name]["fail"]:
            raise RuntimeError("Access is denied (fake)")
        self.tasks[name]["enabled"] = False

    def task_enable(self, name):
        self.tasks[name]["enabled"] = True

    def run_backup(self, paths):
        return self.backups.pop(0)(paths, self.clock)


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _set_mtime(p: Path, t: datetime):
    ts = t.timestamp()
    os.utime(p, (ts, ts))


LEARNER = {"ProcessId": 111, "Name": "python.exe", "CommandLine": "python.exe learner.py run"}
LAUNCHER = {"ProcessId": 110, "Name": "py.exe", "CommandLine": '"C:\\Windows\\py.exe" -3.12 learner.py run'}
WRAPPER = {"ProcessId": 100, "Name": "powershell.exe",
           "CommandLine": '"powershell.exe" -NoExit -File "C:\\Remote Projects\\pokebot-learner\\ai-agent\\run_agent.ps1"'}
BATCH = {"ProcessId": 120, "Name": "python.exe",
         "CommandLine": 'python.exe "C:\\Remote Projects\\pokebot-learner\\tools\\story-dev\\x4_headless.py" --lanes 12'}
LANE = {"ProcessId": 130, "Name": "python.exe",
        "CommandLine": 'python.exe "C:\\Remote Projects\\pokebot-learner\\sandbox-pokebot\\pokebot.py" endless-ai0053-H1'}
WATCHDOG = {"ProcessId": 140, "Name": "py.exe",
            "CommandLine": 'py.exe -3.12 -B "C:\\Remote Projects\\pokebot-learner\\tools\\ops\\watchdog.py"'}


class Fixture:
    """A fake clone. T0 = 11:16:22 AM, when STOP was placed; the round ai0053 runs until the scenario stops it."""

    def __init__(self, root: Path):
        self.root = root
        self.paths = Paths(root / "clone", root / "ops")
        self.t0 = datetime(2026, 10, 28, 11, 16, 22)
        p = self.paths
        _write(p.stop, "")
        _set_mtime(p.stop, self.t0)
        self.old_rows = [{"source": "ai0052", "lane": i} for i in range(52)]
        _write(p.runs, "".join(json.dumps(r) + "\n" for r in self.old_rows))
        _write(p.cycles, json.dumps({"source": "cycle", "tag": "ai0052", "runs": 52}) + "\n")
        self.state = {"cycle": 53, "current": {"tag": "ai0053"}, "cycles": [{"tag": "ai0052"}]}
        _write(p.state, json.dumps(self.state))
        _write(p.lock, "111")
        _write(p.log, "[2026-10-17 04:00:00 PM] STOP file found: stopping (an OLD stop, before T0)\n"
                      "[2026-10-28 04:28:25 AM] ai0053: starting 12 lanes for 720 minutes\n")
        p.ops.mkdir(parents=True, exist_ok=True)

    def running(self, env: FakeEnv):
        env.procs = [WRAPPER, LAUNCHER, LEARNER, BATCH, LANE, WATCHDOG]
        env.alive = {100, 110, 111, 120, 130}

    def stop_cleanly(self, env: FakeEnv, at: datetime, runs: int = 4, stop_line: bool = True):
        p = self.paths
        rows = self.old_rows + [{"source": "ai0053", "lane": i} for i in range(runs)]
        _write(p.runs, "".join(json.dumps(r) + "\n" for r in rows))
        with open(p.cycles, "a", encoding="utf-8") as f:
            f.write(json.dumps({"source": "cycle", "tag": "ai0053", "runs": runs}) + "\n")
        self.state = {"cycle": 53, "current": None, "cycles": [{"tag": "ai0052"}, {"tag": "ai0053"}]}
        _write(p.state, json.dumps(self.state))
        if stop_line:
            with open(p.log, "a", encoding="utf-8") as f:
                f.write(f"[{at.strftime(TS_FMT)}] STOP file found: stopping (delete ai-agent/STOP to allow the "
                        f"next start)\n")
        if p.lock.exists():
            p.lock.unlink()
        env.procs = [WRAPPER, WATCHDOG]
        env.alive = {100}

    def good_backup(self, tamper: str | None = None):
        def run(paths: Paths, now: datetime):
            z = paths.ops / f"learner-data-{now.strftime('%H%M%S')}.zip"
            with zipfile.ZipFile(z, "w") as zf:
                for key, member in ZIP_MEMBERS.items():
                    data = getattr(paths, key).read_bytes()
                    zf.writestr(member, data + (b"tampered\n" if key == tamper else b""))
            _write(paths.backup_status, json.dumps({"time": now.strftime(TS_FMT), "ok": True, "zip": str(z),
                                                    "bytes": z.stat().st_size}))
            return 0, "ok"
        return run

    @staticmethod
    def failed_backup(rc: int = 1):
        return lambda paths, now: (rc, "REFUSED: destination drive not present (fake)")


def selftest() -> int:
    results = []

    def case(name: str, cond: bool, detail: str = ""):
        results.append((name, cond, detail))
        print(f"{'PASS' if cond else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}")

    quiet = lambda msg: None  # noqa: E731
    print(f"STOP_LINE compiled pattern: {STOP_LINE.pattern!r}")
    pos = "[2026-10-28 04:29:10 PM] STOP file found: stopping (delete ai-agent/STOP to allow the next start)"
    negs = ["[2026-10-28 04:29:10 PM] STOP file found; exiting.", "STOP file found: stopping",
            "[2026-10-28 16:29:10] STOP file found: stopping", "[2026-10-28 04:29:10 PM]  STOP file found: stopping",
            "[2026-10-28 04:28:25 AM] ai0053: starting 12 lanes for 720 minutes"]
    case("regex: the learner's STOP line matches", bool(STOP_LINE.match(pos)))
    case("regex: 5 near-misses do not match", not any(STOP_LINE.match(n) for n in negs))

    def fresh():
        tmp = Path(tempfile.mkdtemp(prefix="parktest-"))
        fx = Fixture(tmp)
        env = FakeEnv(datetime(2026, 10, 28, 11, 20, 0))
        fx.running(env)
        return fx, env

    stop_at = datetime(2026, 10, 28, 16, 29, 10)
    deadline = datetime(2026, 10, 28, 18, 30, 0)

    # CONTROL: running -> never "stopped"; at the deadline it times out and changes nothing
    fx, env = fresh()
    base = baseline(fx.paths)
    case("baseline derives the tag, pid and STOP time from the files",
         base == {"tag": "ai0053", "pid": 111, "stop_mtime": fx.t0}, str(base))
    r = check(fx.paths, env, base)
    case("CONTROL running: not stopped_clean, not nothing_running", not r["stopped_clean"] and not r["nothing_running"],
         summary(r))
    case("CONTROL the old (pre-STOP) STOP line is not taken as this stop", r["stop_line"] is None)
    case("CONTROL the watchdog's and wrapper's processes are not the trainer's", len(r["trainer_procs"]) == 4,
         str(r["trainer_procs"]))
    code, _ = watch(fx.paths, env, base, deadline, quiet, poll=600)
    case("CONTROL running to the deadline: TIMEOUT, every task still on",
         code == EXIT_TIMEOUT and all(t["enabled"] for t in env.tasks.values()), f"code {code}")

    # THE NORMAL PATH: it stops cleanly at 4:29 PM -> PARKED after two looks; the backup verified; all three off
    fx, env = fresh()
    base = baseline(fx.paths)
    env.on_sleep = lambda e: fx.stop_cleanly(e, stop_at) if e.clock >= stop_at and fx.paths.lock.exists() else None
    code, r = watch(fx.paths, env, base, deadline, quiet, poll=60)
    case("clean stop: the watch returns PARKED-ready (0) after the stop", code == EXIT_PARKED and r["stopped_clean"],
         summary(r))
    case("clean stop: not before 4:29 PM", env.clock >= stop_at, env.clock.strftime(TS_FMT))
    env.backups = [fx.good_backup()]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("park: PARKED, all three tasks OFF, the backup verified",
         code == EXIT_PARKED and rep["final_tasks"] == {"autostart": "OFF", "watchdog": "OFF", "backup": "OFF"}
         and rep["backup"]["verified"], json.dumps(rep["final_tasks"]))

    # STABILITY: a lock that comes back after the first good look (a restart) resets the count
    fx, env = fresh()
    base = baseline(fx.paths)
    state = {"phase": 0}

    def flap(e):
        if e.clock >= stop_at and state["phase"] == 0:
            fx.stop_cleanly(e, stop_at)
            state["phase"] = 1
        elif state["phase"] == 1:
            _write(fx.paths.lock, "222")  # something took the lock again right after the first good look
            state["phase"] = 2
        elif state["phase"] == 2:
            fx.paths.lock.unlink()
            state["phase"] = 3
    env.on_sleep = flap
    looks = []
    code, r = watch(fx.paths, env, base, deadline, looks.append, poll=60)
    good = [m for m in looks if m.startswith("stopped and recorded")]
    case("FAULT a lock that returns between looks resets the stable count (3 good looks, not 2)",
         code == EXIT_PARKED and len(good) == 3 and any("look 1 of 2" in m for m in good[:2]), f"{len(good)} good looks")

    # FAULTS on the stopped state: each single broken condition must block stopped_clean
    def stopped_fixture():
        fx, env = fresh()
        base = baseline(fx.paths)
        fx.stop_cleanly(env, stop_at)
        return fx, env, base

    fx, env, base = stopped_fixture()
    case("CONTROL the stopped fixture is stopped_clean", check(fx.paths, env, base)["stopped_clean"])
    faults = {
        "the lock still present": lambda fx, env: _write(fx.paths.lock, "111"),
        "the learner PID still a learner": lambda fx, env: (env.procs.append(LEARNER), env.alive.add(111)),
        "a lane process left": lambda fx, env: env.procs.append(LANE),
        "the batch process left": lambda fx, env: env.procs.append(BATCH),
        "state.json current still the round": lambda fx, env: _write(
            fx.paths.state, json.dumps({**fx.state, "current": {"tag": "ai0053"}})),
        "the tag missing from state.json cycles": lambda fx, env: _write(
            fx.paths.state, json.dumps({**fx.state, "cycles": [{"tag": "ai0052"}]})),
        "cycles.jsonl's last row another tag": lambda fx, env: open(fx.paths.cycles, "a", encoding="utf-8").write(
            json.dumps({"source": "cycle", "tag": "ai0054", "runs": 4}) + "\n"),
        "runs.jsonl one row short of the cycle's runs": lambda fx, env: _write(
            fx.paths.runs, "".join(json.dumps(r) + "\n" for r in fx.old_rows + [{"source": "ai0053"}] * 3)),
        "state.json unreadable": lambda fx, env: _write(fx.paths.state, "{not json"),
        "the STOP file removed": lambda fx, env: fx.paths.stop.unlink(),
    }
    for name, breaker in faults.items():
        fx, env, base = stopped_fixture()
        breaker(fx, env)
        r = check(fx.paths, env, base)
        case(f"FAULT {name}: not stopped_clean", not r["stopped_clean"], summary(r))

    # PID REUSE: the PID alive but no longer a learner -> the learner is gone
    fx, env, base = stopped_fixture()
    env.procs.append({"ProcessId": 111, "Name": "chrome.exe", "CommandLine": "chrome.exe --type=renderer"})
    env.alive.add(111)
    case("CONTROL a reused PID (not learner.py) does not count as the learner", check(fx.paths, env, base)["stopped_clean"])

    # NO STOP LINE (only the OLD one) though nothing runs and the round is recorded -> UNEXPECTED, nothing changed
    fx, env = fresh()
    base = baseline(fx.paths)
    env.on_sleep = lambda e: (fx.stop_cleanly(e, stop_at, stop_line=False)
                              if e.clock >= stop_at and fx.paths.lock.exists() else None)
    code, r = watch(fx.paths, env, base, deadline, quiet, poll=60)
    case("FAULT no fresh STOP line: UNEXPECTED (40), every task still on",
         code == EXIT_UNEXPECTED and all(t["enabled"] for t in env.tasks.values()), f"code {code}")

    # NOT RECORDED: the learner died, the batch ran out, nothing scored -> UNEXPECTED
    fx, env = fresh()
    base = baseline(fx.paths)

    def died(e):
        if e.clock >= stop_at and fx.paths.lock.exists():
            fx.paths.lock.unlink()
            e.procs, e.alive = [WRAPPER], {100}
    env.on_sleep = died
    code, r = watch(fx.paths, env, base, deadline, quiet, poll=60)
    case("FAULT the round not recorded: UNEXPECTED (40), every task still on",
         code == EXIT_UNEXPECTED and not r["recorded"] and all(t["enabled"] for t in env.tasks.values()), f"code {code}")

    # CANCELLED: STOP removed while waiting
    fx, env = fresh()
    base = baseline(fx.paths)
    env.on_sleep = lambda e: fx.paths.stop.unlink() if e.sleeps == 3 and fx.paths.stop.exists() else None
    code, _ = watch(fx.paths, env, base, deadline, quiet, poll=60)
    case("FAULT STOP removed while waiting: CANCELLED (30), every task still on",
         code == EXIT_CANCELLED and all(t["enabled"] for t in env.tasks.values()), f"code {code}")

    # ATTENTION instead of the STOP line: a stop is a stop -> parked, but a person must read the reason
    fx, env = fresh()
    base = baseline(fx.paths)

    def attention(e):
        if e.clock >= stop_at and fx.paths.lock.exists():
            fx.stop_cleanly(e, stop_at, stop_line=False)
            _write(fx.paths.attention, "# ATTENTION\n2026-10-28 04:29:10 PM\n3 cycles in a row produced no scored runs.\n")
            _set_mtime(fx.paths.attention, stop_at)
    env.on_sleep = attention
    code, r = watch(fx.paths, env, base, deadline, quiet, poll=60)
    env.backups = [fx.good_backup()]
    code2, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("ATTENTION exit: watched as stopped (0), parked with the reason (10), all three OFF",
         code == EXIT_PARKED and code2 == EXIT_PARTIAL and any("ATTENTION" in n for n in rep["needs_person"])
         and set(rep["final_tasks"].values()) == {"OFF"}, json.dumps(rep["needs_person"]))

    # BACKUP FAILS twice -> the nightly backup is LEFT ON; 10
    fx, env, base = stopped_fixture()
    env.backups = [fx.failed_backup(), fx.failed_backup()]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("FAULT the final backup fails twice: the nightly backup LEFT ON, the others OFF (10)",
         code == EXIT_PARTIAL and rep["final_tasks"] == {"autostart": "OFF", "watchdog": "OFF", "backup": "ON"},
         json.dumps(rep["final_tasks"]))

    # BACKUP fails once, then succeeds -> retried, PARKED
    fx, env, base = stopped_fixture()
    env.backups = [fx.failed_backup(), fx.good_backup()]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("CONTROL a backup that fails once then passes: retried, PARKED (0)",
         code == EXIT_PARKED and rep["final_tasks"]["backup"] == "OFF", json.dumps(rep["backup"]))

    # BACKUP exit 0 but the zip's runs.jsonl differs -> not verified, LEFT ON
    fx, env, base = stopped_fixture()
    env.backups = [fx.good_backup(tamper="runs"), fx.good_backup(tamper="runs")]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("FAULT exit 0 but the zip's runs.jsonl differs: not verified, the nightly backup LEFT ON (10)",
         code == EXIT_PARTIAL and rep["final_tasks"]["backup"] == "ON" and "differs" in rep["backup"]["detail"],
         rep["backup"]["detail"][:120])

    # BACKUP exit 0 but its status is stale (an older run's) -> not verified
    fx, env, base = stopped_fixture()

    def stale(paths, now):
        _write(paths.backup_status, json.dumps({"time": "2026-10-28 01:00:01 AM", "ok": True, "zip": "nowhere.zip"}))
        return 0, "ok"
    env.backups = [stale, stale]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("FAULT exit 0 with a STALE status: not verified (10)", code == EXIT_PARTIAL and "stale" in rep["backup"]["detail"],
         rep["backup"]["detail"][:120])

    # A task that cannot be switched off -> reported, the rest still done
    fx, env, base = stopped_fixture()
    env.tasks[TASKS["watchdog"]]["fail"] = True
    env.backups = [fx.good_backup()]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("FAULT the watchdog cannot be switched off: reported (10), autostart and backup still OFF",
         code == EXIT_PARTIAL and rep["final_tasks"] == {"autostart": "OFF", "watchdog": "ON", "backup": "OFF"},
         json.dumps(rep["final_tasks"]))

    # A trainer process that appears AFTER the park -> reported
    fx, env, base = stopped_fixture()
    env.backups = [lambda paths, now: (env.procs.append(LANE), fx.good_backup()(paths, now))[1]]
    code, rep = park(fx.paths, env, base, quiet, retry_wait=1)
    case("FAULT a trainer process after the park: reported (10)",
         code == EXIT_PARTIAL and any("running after the park" in n for n in rep["needs_person"]))

    # baseline refusals
    fx, env = fresh()
    fx.paths.stop.unlink()
    try:
        baseline(fx.paths)
        case("FAULT baseline without STOP refuses", False)
    except SystemExit as e:
        case("FAULT baseline without STOP refuses", "REFUSED" in str(e))
    fx, env = fresh()
    _write(fx.paths.state, json.dumps({"current": None, "cycles": []}))
    try:
        baseline(fx.paths)
        case("FAULT baseline with no round running refuses", False)
    except SystemExit as e:
        case("FAULT baseline with no round running refuses", "REFUSED" in str(e))

    failed = [n for n, ok, _ in results if not ok]
    print(f"\nSELFTEST: {len(results) - len(failed)} of {len(results)} PASS" + (f"; FAILED: {failed}" if failed else ""))
    return 0 if not failed else 1


# -------------------------------------------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-once", action="store_true")
    ap.add_argument("--probe-tasks", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--deadline", default="")
    ap.add_argument("--poll", type=float, default=60.0)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    paths, env = Paths(CLONE, OPS), RealEnv()
    if a.check_once:
        base = baseline(paths)
        print("baseline:", {**base, "stop_mtime": base["stop_mtime"].strftime(TS_FMT)})
        r = check(paths, env, base)
        print(json.dumps(r, indent=1))
        return 0
    if a.probe_tasks:
        name = TASKS["backup"]
        before = env.task_enabled(name)
        try:
            result = disable_verified(env, name)
            print(f"{name}: enabled before={before}; disable_verified -> {result}")
        finally:
            env.task_enable(name)
            print(f"{name}: re-enabled -> enabled={env.task_enabled(name)}")
        return 0 if before and result == "OFF" and env.task_enabled(name) else 1
    if not a.live:
        ap.print_help()
        return 2
    logf = HERE / "park_watch.log"
    report = HERE / "park_report.json"

    def log(msg: str):
        line = f"[{datetime.now().strftime(TS_FMT)}] {msg}"
        print(line, flush=True)
        with open(logf, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    try:
        deadline = datetime.strptime(a.deadline, TS_FMT)
        base = baseline(paths)
        log(f"watch started: round {base['tag']}, learner pid {base['pid']}, STOP placed "
            f"{base['stop_mtime'].strftime(TS_FMT)}, deadline {deadline.strftime(TS_FMT)}")
        code, r = watch(paths, env, base, deadline, log, poll=a.poll)
        out = {"watch_exit": code, "watch": r}
        if code == EXIT_PARKED:
            log("the trainer stopped cleanly and its round is recorded: parking Windows")
            code, rep = park(paths, env, base, log)
            out["park"] = rep
        out["exit"] = code
        out["finished"] = datetime.now().strftime(TS_FMT)
        report.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
        log(f"DONE: exit {code}; report {report}")
        return code
    except SystemExit as e:
        log(str(e))
        return EXIT_ERROR
    except Exception:  # noqa: BLE001
        log(f"INTERNAL ERROR:\n{traceback.format_exc()}")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
```

`mutants.py`:

```python
"""Mutants of park_watch.py: each removes one guard; the selftest must FAIL on every one (and PASS on the original)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent / "park_watch.py"
MUTANTS = {
    "M1 no runs-row count check": ("and r[\"runs_rows\"] is not None and r[\"runs_rows\"] == r[\"cycles_last_runs\"])",
                                   ")"),
    "M2 the stable count never resets": ("            else:\n                stable = 0\n",
                                         "            else:\n                pass\n"),
    "M3 the backup zip never compared": ("                if sha(zf.read(member)) != sha(live):",
                                         "                if False:"),
    "M4 the STOP line's date ignored": ("if m and datetime.strptime(m[\"ts\"], TS_FMT) >= since:", "if m:"),
    "M5 a failed backup still switches the nightly task off": ("    if ok:\n        rep[\"tasks\"][\"backup\"] = disable_verified",
                                                               "    if True:\n        rep[\"tasks\"][\"backup\"] = disable_verified"),
    "M6 the lanes not counted as the trainer": ("or \"sandbox-pokebot\" in low", "or False"),
    "M7 the stale-status check removed": ("    if t < started.replace(microsecond=0):", "    if False:"),
    "M8 the deadline ignored": ("        if now >= deadline:", "        if False:"),
}
src = SRC.read_text(encoding="utf-8")
env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
caught = 0
for name, (old, new) in MUTANTS.items():
    assert src.count(old) == 1, (name, src.count(old))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "park_watch.py"
        p.write_text(src.replace(old, new), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(p), "--selftest"], capture_output=True, text=True, env=env,
                               timeout=240)
            failed = [ln for ln in r.stdout.splitlines() if ln.startswith("FAIL")]
            ok = r.returncode != 0 and bool(failed)
            how = f"{len(failed)} test(s) failed, e.g. {failed[0][:90]!r}" if failed else f"exit {r.returncode}"
        except subprocess.TimeoutExpired:
            ok, how = True, "selftest hung (timeout): caught"
    caught += ok
    print(f"{'CAUGHT ' if ok else 'SURVIVED'} {name}: {how}")
r = subprocess.run([sys.executable, str(SRC), "--selftest"], capture_output=True, text=True, env=env, timeout=240)
print(f"CONTROL original: exit {r.returncode} ({r.stdout.strip().splitlines()[-1]})")
print(f"MUTANTS: {caught} of {len(MUTANTS)} caught")
sys.exit(0 if caught == len(MUTANTS) and r.returncode == 0 else 1)
```
