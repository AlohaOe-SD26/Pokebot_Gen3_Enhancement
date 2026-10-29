"""GATE: prove tools/ops/park_tuner.py (USER RULING 50; `03` #28-trainer-improvements (10)) parks and resumes the bot
tuner SAFELY, and that `status` and the dry runs change nothing.

WHY THIS EXISTS. A park or a resume is ONE command a future session runs on the user's word, against a learner that has
run for weeks. Its failure modes are quiet and expensive: a park that switches the Windows tasks off while the round
still runs (the round is never recorded, and nothing restarts it); a "final backup" that is stale or holds the wrong
bytes and still switches the nightly backup off for good; a resume that starts a tuner while STOP still exists or a
task is OFF, or ends an old window that was NOT idle; a start check fooled by an OLD log line; a dry run that acts;
and a selftest that touches the REAL tasks. Every test pairs a FAULT arm (the bad condition, which must be caught) with
a CONTROL arm (the good one, which must pass), so a test that cannot fail does not count. Everything runs on a FAKE
clone in a temp folder with a FakeEnv: a clock that sleep() advances, a process table in the REAL command-line shapes
(measured 2026-10-28), the three tasks with State and Enabled, and a backup that writes a real zip and status file.
The real clone, the real tasks and the real %LOCALAPPDATA% are never touched, by two layers: PARK_TUNER_SELFTEST=1 is
set before the tool is loaded (every changing RealEnv method raises), and the tool's only process launchers (_run,
_ps) are swapped for a TRIPWIRE that records and refuses; the last check asserts the tripwire recorded nothing.

THE ANCHORS ARE INDEPENDENT OF THE TOOL (fix round 2026-10-28; an independent sweep found 49 surviving mutants, several
because the fixtures took a value FROM the tool and so agreed with any wrong value): the learner's layout (REL), its
12-hour time format (LEARNER_FMT) and the backup's zip member names (ZIP_NAMES) are typed HERE, every fixture file is
placed at its literal path and every fixture time is written in the learner's format, and test X checks each against
ai-agent/learner.py and tools/ops/backup_learner.py THEMSELVES (both must exist next to this file's repo root: a missing
one is a FAIL, never a skip).

  X  the tool against the LEARNER'S OWN SOURCE (AST; learner.py is never imported) and backup_learner.py: TIME_FMT is
     the 12-hour format typed here and the tool's TS_FMT; a literal PM time parses to the afternoon; learner.py's paths
     (STOP, ATTENTION.md, DEPLOYMENT, agent.lock, learner.log, state.json, cycles.jsonl, runs.jsonl) equal REL and the
     tool's Paths; each of the tool's five log patterns (STOP, start, round, restart, crash) MATCHES a line rendered
     from learner.py's real log()/_say() call (a PM time stamp, sample values), and the code signature is 12 hex.
     FAULT: a learner.py that rewords any one line, moves STOP, ATTENTION.md or DEPLOYMENT, logs 24-hour times or
     widens the signature IS caught. CONTROL: the same learner written differently (annotated constants, log()'s
     parameter and local renamed, a constant repeated) is read alike, so this gate raises no false alarm.
     backup_learner.py's own source_files() names the three verified members as the tool does, and its stamp() parses
     with the tool. WHY: the learner auto-deploys its own code, so a rewording would otherwise break every park and
     resume silently while this gate stayed green (review F10; sweep S21, S31, S32, S50).
  M  process matching on the REAL shapes: the learner, its py.exe launcher (under the clone's run_agent.ps1 window),
     the batch and 12 lanes ARE the tuner; the -NoExit window, conhost, the watchdog (powershell + py), the backup task
     and this tool are NOT. FAULT: a lane of another checkout, a sibling folder 'pokebot-learner-old', another
     checkout's window, a learner-shaped process with this PID; a --dev learner of another checkout, test_agent.py's
     `learner.py run` child and a shell loop that greps for the phrase are NOT this clone's (they are listed as others);
     a hand-started learner counts only once it holds agent.lock (its launcher too). CONTROL: forward-slash lane and
     batch, a full-path learner; FAULT: park_tuner.py / park_watch.py outside tools\\ops naming a lane path. A relative,
     \\\\?\\, forward-slash, upper-case or (where the volume has them) 8.3 --clone sees the 12 lanes, and so does one
     reached through a JUNCTION (where junctions can be made) whose lanes are spelled with its resolved target; FAULT
     end to end: park --apply with a RELATIVE --clone while orphaned lanes run does NOT park (review F3, F6; sweep
     S37-S40).
  RE RealEnv's live-machine code with CANNED PowerShell (a stub that starts nothing; the guard stays on except where a
     stub is already in place): task_info reads 'State|Enabled' and RAISES on a failed or unreadable read; processes()
     turns one object into a list and raises on failure; pid_alive is True for this process and False for an exited
     child (OpenProcess on two PIDs, read-only); run_backup runs `py -3.12 -B <clone>/tools/ops/backup_learner.py` with
     its working folder OUTSIDE the clone (and the ops folder when the temp folder is inside it); git_head runs only
     rev-parse; each changing method sends its exact cmdlet and raises when PowerShell fails. WHY: the selftest never
     reached these lines, and an inverted Enabled or pid_alive would park nothing while reporting PARKED (sweep S58-S61).
  S  each status verdict from its fixture with its exit code, the verdict on the FIRST line, and times in 12-hour form
     (4:30 PM). INCONSISTENT for a dead learner whose batch runs on with the tasks ON (not RUNNING); a waiting park
     --apply is shown, with the real cancel; a dead run's lock is shown STALE; while any --apply holds the lock (a
     resume; a park past its wait) the next step is to let it finish (never a command that would be refused); a STOP
     that is resume --apply's own (a resume stopped early) is named on the first line and the next step is to finish
     the RESUME, never to park; another checkout's learner leaves a PARKED tuner PARKED and is listed; status writes
     NOTHING (review F1, F3; sweep S24, S57).
  D  park and resume WITHOUT --apply change nothing and print the plan in order (resume: the tasks ON before the old
     window is ended); the park plan warns that the wait runs in the foreground; with a WAITING park holding the lock,
     the park dry run says it would refuse and the resume plan starts with the cancel. FAULT: an ACTING run IS seen.
  C1 FAULT no ai-agent/DEPLOYMENT (or only a DEPLOYMENT at the clone ROOT, the wrong place): REFUSED, nothing written;
     a bad --deadline and --poll 0 likewise; a --clone whose spellings cannot be worked out is an INTERNAL ERROR (50),
     never an escaping traceback. CONTROL: the marker at ai-agent/DEPLOYMENT (typed literally) proceeds.
  L1 the lock: a live park/resume --apply holder (a RESUME holder too) refuses a park; an unreadable lock under a minute
     old refuses; dead, reused and old unreadable locks are replaced; a holder alive but missing from the table counts
     as LIVE; the lock is released when the summary or the first log line fails. The CANCEL (review F1): resume --apply
     against a park --apply WAITING for the round deletes STOP, waits for that park to end, takes the lock and reports
     PARK CANCELLED; FAULT: a park past its wait (phase parking), a park lock naming no phase or no usable PID, and a
     waiting park whose STOP is already gone (it is ENDING: no circular advice) are each refused with STOP kept; a
     waiting park that does not end -> NEEDS PERSON; ATTENTION.md -> nothing changed; a second park is told the real
     cancel. The park records phase 'waiting' while it waits and 'parking' after; a STOP deleted after the wait's last
     look -> CANCELLED, no task touched. A console that went away loses no log line and no report (review F12).
  G1 THE TEST GUARD: every changing RealEnv method raises before reaching a process; place_stop, remove_stop,
     write_json, append_line, acquire_tool_lock and release_tool_lock are each REFUSED on a path under the real clone
     or ops folder (pointed at temp stand-ins, so even a missing guard writes only there: sweep S28, S29); a temp path
     is writable; the guard is conditional; the tripwire recorded nothing over the whole run (the LAST check).
  N1 never-scan of the tool's CODE (no kill/terminate, no task (un)registering, Stop-Process, taskkill,
     TerminateProcess, Remove-Item or install_ops_tasks; git only rev-parse). FAULT: a synthetic source IS flagged.
  P1 STOP placed at the LITERAL ai-agent/STOP with its text; a STOP already there kept; place_stop keeps a STOP that
     appears between the check and the write (exclusive create; sweep S50, S51).
  P2 the clean stop: each single broken condition blocks it; a STOP line in the floor's own second counts; an
     ATTENTION.md OLDER than STOP does not; the base learner alive under a command line the matcher misses blocks it;
     runs.jsonl with MORE rows than the cycle's runs is not recorded; agent.lock blocks only while a LIVE learner holds
     it or it cannot be read (a dead PID's lock is a crash leftover: review F4). End to end: the clean stop parks with
     "stopped after round ai0054, which is recorded"; a lock that returns resets the count; no STOP line, not
     recorded, the batch outliving the learner, CANCELLED, TIMEOUT ("still running"), a hard kill -> UNEXPECTED (not
     TIMEOUT); nothing runs at the deadline -> TIMEOUT whose verdict line AND logged reason do NOT say "still running";
     a first good look gets its confirming look past the deadline (review F11), and a learner that comes back holding
     its lock after a first good look resets the count, so the deadline still ends the wait (never an endless one);
     the restart into new code (exit 3) and a silent STOP exit between
     rounds are clean, a crash line between rounds is not (review F9); a re-run over an existing STOP counts the
     learner's STOP line from STOP's own time (sweep S01-S04, S36); ATTENTION exit; Ctrl+C; an adopted round.
  P3 order: no task off before the verified stop; Disable autostart, Disable watchdog, the backup, Disable backup, in
     that order (sweep S05); the backup task only after a VERIFIED backup. FAULT single-fault backups, each with zip
     members named LITERALLY: REFUSED, exit 1, a stale status (a day old, and 3 hours old on the same day), ok false, ok
     MISSING, cycles.jsonl tampered, runs.jsonl 60 bytes short, state.json another document, runs.jsonl missing from
     the zip, a corrupt zip, a zip that is gone (sweep S45-S49). STOP that cannot be placed, or is not there after the
     write -> ERROR 50 with no changing call (sweep S06, S07). During the backup: STOP deleted, a learner started, the
     autostart switched back ON -> PARTIAL, never PARKED (sweep S10-S12). Exactly one dated report (sweep S52).
  P4 the default deadline: started + minutes + 90 (06:00:19 AM from the literal "04:30:19 PM"); --deadline overrides
     it; an adopted round does not move a given one; a torn start uses the round's own length (sweep S20).
  P5 --no-wait places STOP and returns PENDING with no task touched.
  P6 not running: parks after two looks with "no round was left unrecorded"; an unrecorded round is REPORTED and the
     PARKED line says so, never "recorded" (review F5); a learner appearing between the looks is waited for.
  P7 idempotent: a second park --apply runs no backup; after a failed backup a re-run retries it and disables ONLY the
     backup task (sweep S34).
  R1 ATTENTION.md (at the literal ai-agent/findings/ATTENTION.md) -> NEEDS PERSON, nothing changed, on a parked AND on
     a RUNNING tuner (sweep S32, S33).
  R2 already running -> nothing changed; running with a task OFF -> TASKS ON (not "RESUMED": nothing was started;
     review F7); an Enable that silently does nothing -> NEEDS PERSON (sweep S55).
  R3 PARK PENDING -> PARK CANCELLED. The LEARNER chooses this step (review F2): the learner dead with its batch running
     -> NEEDS PERSON with NOTHING changed; a read-only STOP -> NEEDS PERSON (sweep S56); a learner that found STOP
     before the delete, in the moment of it (gone at once, or STILL EXITING at the next look: never PARK CANCELLED),
     or whose STOP line is only seen at the look after the tasks step (the review's probe3 timing) is waited for and
     started again, never "without a STOP line"; one that never exits -> NEEDS PERSON after 5 minutes; another
     checkout's learner on a PARKED tuner does not stop the resume.
  R4 the idle window: the proof's unit arms (a live learner of the clone, a batch, a lane, a live-PID lock, an
     UNREADABLE lock, a python child, no window -> not proven; conhost only, or only another checkout's learner ->
     proven); end to end the tasks are ON and STOP exists AT the Stop-ScheduledTask call, then STOP deleted, started.
     FAULT: a live-PID lock or a python child -> nothing changed; the window gone but the State stuck Running, or the
     State left Running but the window still there, or Stop-ScheduledTask itself failing -> NEEDS PERSON, no start
     (sweep S14, S15). NOT parked (review F8): a STOP naming resume --apply is placed for the Stop and deleted before
     the start; that STOP failing to be placed (raised, or no file after the write) -> nothing changed; a learner that
     starts during that moment, or appears as the window ends -> NEEDS PERSON, never started on top.
  R5 order: at the start call STOP is absent and the three tasks read ON; an Enable that fails, a STOP that cannot be
     deleted, a task that flips OFF -> the start is NEVER called. Unit: start_allowed.
  R6 the start check: an OLD 'learner started' line does not count; no start -> NEEDS PERSON; a dead lock PID ->
     NEEDS PERSON; ATTENTION after the start -> NEEDS PERSON; a learner that dies 5 minutes after its start -> NEEDS
     PERSON (sweep S54); a resume at 1:00 PM reads its PM start and round lines (sweep S22, S23); Ctrl+C -> 50
     INTERRUPTED, the lock released (sweep S43); a log replaced by a shorter one is read from its start (sweep S17).

Run: py -3.12 tools/story-dev/selftest_park_tuner.py      (a few seconds; under 60 s)
"""
from __future__ import annotations

import ast
import contextlib
import ctypes
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

os.environ["PARK_TUNER_SELFTEST"] = "1"  # THE TEST GUARD (spec 3.4): set before the tool is loaded, never unset

ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_PATH = ROOT / "tools" / "ops" / "park_tuner.py"
LEARNER_PY = ROOT / "ai-agent" / "learner.py"
BACKUP_PY = ROOT / "tools" / "ops" / "backup_learner.py"
RESULTS: list[tuple[str, bool, str]] = []
TRIPWIRE: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


class TripwireError(RuntimeError):
    """A test reached a real process launcher of the tool."""


def tripwire_run(argv, timeout=None, cwd=None):
    TRIPWIRE.append("run: " + " ".join(map(str, argv))[:200])
    raise TripwireError(f"the selftest tripwire refused a real process: {list(argv)[:3]}")


def tripwire_ps(command, timeout=180):
    TRIPWIRE.append("powershell: " + str(command)[:200])
    raise TripwireError("the selftest tripwire refused PowerShell")


def load_tool():
    spec = importlib.util.spec_from_file_location("park_tuner_under_test", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._run = tripwire_run  # every process the tool can start goes through these two
    mod._ps = tripwire_ps
    return mod


TOOL = load_tool()
REAL_GUARD_ACTION = TOOL.guard_action
A, W, B = TOOL.TASKS["autostart"], TOOL.TASKS["watchdog"], TOOL.TASKS["backup"]

# The learner's layout, time format and the backup's member names, typed HERE on purpose: a fixture that took them from
# the tool would agree with any wrong value in it (sweep S21, S31, S32, S45, S46, S50). Test X checks each one against
# learner.py and backup_learner.py themselves.
LEARNER_FMT = "%Y-%m-%d %I:%M:%S %p"
REL = {"deployment": "ai-agent/DEPLOYMENT", "stop": "ai-agent/STOP", "attention": "ai-agent/findings/ATTENTION.md",
       "log": "ai-agent/data/learner.log", "lock": "ai-agent/data/agent.lock", "state": "ai-agent/data/state.json",
       "cycles": "ai-agent/data/cycles.jsonl", "runs": "ai-agent/data/runs.jsonl"}
ZIP_NAMES = {"runs": "ai-agent/data/runs.jsonl", "cycles": "ai-agent/data/cycles.jsonl",
             "state": "ai-agent/data/state.json"}


def ts(t: datetime) -> str:
    return t.strftime(LEARNER_FMT)


def ids(procs) -> list:
    return sorted(p["ProcessId"] for p in procs)


# ------------------------------------------------------------------------------------------------- times and shapes
T_ROUND = datetime(2026, 10, 28, 16, 30, 19)          # ai0054 started (state.json current.started, measured)
T_ROUND_TEXT = "2026-10-28 04:30:19 PM"               # ... exactly as learner.py wrote it (typed literally)
ROUND_END = T_ROUND + timedelta(minutes=720)          # 2026-10-29 04:30:19 AM
DEFAULT_DEADLINE = ROUND_END + timedelta(minutes=90)  # 2026-10-29 06:00:19 AM
NOW_S = datetime(2026, 10, 28, 17, 15, 0)             # status and the dry runs: 5:15 PM, the round running
NOW0 = datetime(2026, 10, 29, 4, 0, 0)                # most park runs begin half an hour before the round ends
STOP_AT = datetime(2026, 10, 29, 4, 31, 10)           # the learner's STOP line in the clean-stop scenarios
T_STOP = datetime(2026, 10, 28, 17, 0, 0)             # a STOP placed earlier (a fixture's existing STOP)
T_OLD = datetime(2026, 10, 17, 16, 0, 0)              # an OLD stop line, before any STOP of these tests
NOW_R = datetime(2026, 10, 29, 9, 0, 0)               # resume runs: the morning after
NOW_PM = datetime(2026, 10, 29, 13, 0, 0)             # a resume after noon (sweep S22, S23)

REAL = "C:\\Remote Projects\\pokebot-learner"
PY = "C:\\Users\\me\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
SHAPES = {  # the live tree of 2026-10-28 (build spec section 2), verbatim but for the user folder
    "window": (10588, 3720, "powershell.exe",
               '"powershell.exe" -NoExit -ExecutionPolicy Bypass -File "' + REAL + '\\ai-agent\\run_agent.ps1"'),
    "conhost": (32140, 10588, "conhost.exe", "\\??\\C:\\WINDOWS\\system32\\conhost.exe 0x4"),
    "launcher": (42712, 10588, "py.exe", '"C:\\Windows\\py.exe" -3.12 learner.py run'),
    "learner": (5372, 42712, "python.exe", PY + " learner.py run"),
    "batch": (46944, 5372, "python.exe",
              PY + ' "' + REAL + '\\tools\\story-dev\\x4_headless.py" --build sandbox --lanes 12 --minutes 720.0 '
              '--arms "' + REAL + '\\ai-agent\\runs\\ai0054\\arms.json" --profile-tag ai0054 --out "' + REAL
              + '\\ai-agent\\runs\\ai0054\\batch"'),
    "watchdog_ps": (51000, 1500, "powershell.exe",
                    "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -NonInteractive "
                    '-ExecutionPolicy Bypass -WindowStyle Hidden -File "' + REAL + '\\tools\\ops\\watchdog.ps1"'),
    "watchdog_py": (51001, 51000, "py.exe", 'py -3.12 -B "' + REAL + '\\tools\\ops\\watchdog.py"'),
    "backup_task": (51100, 1500, "pyw.exe", '"C:\\Windows\\pyw.exe" -3.12 -B "' + REAL
                    + '\\tools\\ops\\backup_learner.py"'),
    "tool_main": (51200, 1600, "py.exe", '"C:\\Windows\\py.exe" -3.12 "C:\\Remote Projects\\Pokebot_Gen3_Enhancement'
                  '\\tools\\ops\\park_tuner.py" park --apply'),
    "tool_clone": (51201, 1600, "python.exe", PY + ' "' + REAL + '\\tools\\ops\\park_tuner.py" status'),
    "park_watch": (51300, 1600, "python.exe", PY + ' "C:\\Users\\me\\scratch\\park_watch.py" --live --deadline x'),
}
STARTERS = ["torchic", "mudkip", "treecko", "random"]


def lane_cmd(n: int, clone: str = REAL) -> str:
    return (PY + ' "' + clone + '\\sandbox-pokebot\\pokebot.py" endless-ai0054-H' + str(n) + "-" + STARTERS[(n - 1) % 4]
            + ' -m "Story (ENDLESS RESET)" -s 0 -na -hl --endless-target 0')


def proc(kind: str, clone=None) -> dict:
    pid, ppid, name, cmd = SHAPES[kind]
    if clone is not None:
        cmd = cmd.replace(REAL, str(clone))
    return {"ProcessId": pid, "ParentProcessId": ppid, "Name": name, "CommandLine": cmd}


def lanes(clone=None, n: int = 12) -> list[dict]:
    c = REAL if clone is None else str(clone)
    return [{"ProcessId": 60000 + i, "ParentProcessId": 46944, "Name": "python.exe", "CommandLine": lane_cmd(i, c)}
            for i in range(1, n + 1)]


# -------------------------------------------------------------------------------------------------------- FakeEnv
class FakeEnv:
    """The machine, faked. Every call is recorded in order (`calls`, `events` with the clock); the CHANGING ones are the
    five the tool may make. sleep() advances the clock and runs `on_sleep`. task_start and task_stop record what they
    saw (the literal STOP file and the three tasks' Enabled)."""
    CHANGING = ("task_disable", "task_enable", "task_start", "task_stop", "run_backup")

    CEILING = timedelta(days=3)  # a loop that never ends fails fast instead of hanging the gate (a mutant that ignores
    # the deadline is then an INTERNAL ERROR, exit 50, in seconds)

    def __init__(self, start: datetime, stop_file: Path | None = None):
        self.clock = start
        self.start = start
        self.stop_file = stop_file
        self.procs: list[dict] = []
        self.alive: set[int] = set()
        self.tasks = {n: {"enabled": True, "state": "Ready", "fail_disable": False, "fail_enable": False,
                          "stuck": False, "silent_enable": False} for n in TOOL.TASKS.values()}
        self.backups: list = []  # each: callable(paths, now) -> (rc, out)
        self.on_sleep = None
        self.on_start = None
        self.on_enable = None
        self.on_processes = None
        self.on_task_stop = None
        self.stop_mode = "normal"  # "state_stays": the window goes but State stays Running; "window_stays": the reverse
        self.sleeps: list[float] = []
        self.calls: list[tuple] = []
        self.events: list[tuple] = []
        self.start_seen: list[tuple] = []
        self.stop_seen: list[tuple] = []

    def _rec(self, name: str, *args) -> None:
        self.calls.append((name, args))
        self.events.append((name, args, self.clock))

    def mark(self, what: str) -> None:
        self.events.append(("MARK", (what,), self.clock))

    def changes(self, since: int = 0) -> list[tuple]:
        return [c for c in self.calls[since:] if c[0] in self.CHANGING]

    def _saw(self) -> tuple:
        return (self.stop_file.exists() if self.stop_file else None, {n: t["enabled"] for n, t in self.tasks.items()})

    def now(self):
        return self.clock

    def sleep(self, s):
        self._rec("sleep", s)
        self.clock += timedelta(seconds=s)
        self.sleeps.append(s)
        if self.clock > self.start + self.CEILING:
            raise RuntimeError("FakeEnv: the clock passed 3 days: a loop that never ends")
        if self.on_sleep:
            self.on_sleep(self)

    def processes(self):
        self._rec("processes")
        if self.on_processes:
            self.on_processes(self)
        return [dict(p) for p in self.procs]

    def pid_alive(self, pid):
        self._rec("pid_alive", pid)
        return pid in self.alive

    def task_info(self, name):
        self._rec("task_info", name)
        t = self.tasks[name]
        return {"state": t["state"], "enabled": t["enabled"]}

    def task_enabled(self, name):
        self._rec("task_enabled", name)
        return self.tasks[name]["enabled"]

    def git_head(self, clone):
        self._rec("git_head", str(clone))
        return "c69ee31e"

    def task_disable(self, name):
        self._rec("task_disable", name)
        t = self.tasks[name]
        if t["fail_disable"]:
            raise RuntimeError("Access is denied (fake)")
        if not t["stuck"]:
            t["enabled"] = False
            if t["state"] != "Running":
                t["state"] = "Disabled"

    def task_enable(self, name):
        self._rec("task_enable", name)
        t = self.tasks[name]
        if t["fail_enable"]:
            raise RuntimeError("Access is denied (fake)")
        if t["silent_enable"]:  # Enable-ScheduledTask returns without error and the task stays OFF (sweep S55)
            return
        t["enabled"] = True
        if t["state"] == "Disabled":
            t["state"] = "Ready"
        if self.on_enable:
            self.on_enable(self, name)

    def task_start(self, name):
        self._rec("task_start", name)
        self.start_seen.append(self._saw())
        if self.on_start:
            self.on_start(self)

    def task_stop(self, name):
        self._rec("task_stop", name)
        self.stop_seen.append(self._saw())
        t = self.tasks[name]
        if self.stop_mode != "window_stays":
            wins = {p["ProcessId"] for p in self.procs if "run_agent.ps1" in (p.get("CommandLine") or "")}
            self.procs = [p for p in self.procs if p["ProcessId"] not in wins and p.get("ParentProcessId") not in wins]
            self.alive -= wins
        t["state"] = "Running" if self.stop_mode == "state_stays" else ("Ready" if t["enabled"] else "Disabled")
        if self.on_task_stop:
            self.on_task_stop(self)

    def run_backup(self, paths):
        self._rec("run_backup")
        return self.backups.pop(0)(paths, self.clock)


# --------------------------------------------------------------------------------------------------------- fixture
def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def append(p: Path, text: str) -> None:
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(text)


def set_mtime(p: Path, t: datetime) -> None:
    os.utime(p, (t.timestamp(), t.timestamp()))


def jl(rows) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


STOP_LINE_TEXT = "STOP file found: stopping (delete ai-agent/STOP to allow the next start)"
ATTENTION_TEXT = ("# The learner paused itself\n\n2026-10-29 05:00:00 AM\n\n3 cycles in a row produced no scored runs. "
                  "Read data/learner.log and the newest runs/<tag>/x4.out.txt.\n\nFix the cause, delete this file, then "
                  "start the learner again (`run_agent.ps1`).\n")
TAMPER = {"runs": lambda b: b[:-60], "cycles": lambda b: b + b"tampered\n", "state": lambda b: b'{"cycle": 1}'}


class Fixture:
    """A fake deployment clone at <tmp>/<name>/pokebot-learner and an ops folder <tmp>/<name>/ops that does NOT exist
    unless `ops=True`. Every file is placed at its LITERAL path (REL); `paths` (the tool's Paths) is used ONLY to call
    the tool's functions. Round ai0054 runs (started "2026-10-28 04:30:19 PM", 720 minutes); ai0053 is recorded.
    `between_rounds`: ai0054 is recorded too and no round runs."""

    def __init__(self, tmp: Path, name: str, ops: bool = False, deployment: bool = True, between_rounds: bool = False):
        self.root = tmp / name
        self.clone = self.root / "pokebot-learner"
        self.ops = self.root / "ops"
        for key, rel in REL.items():
            setattr(self, key, self.clone / rel)
        self.park_dir = self.ops / "park"
        self.tool_lock = self.park_dir / "park_tuner.lock"
        self.tool_log = self.park_dir / "park_tuner.log"
        self.latest = self.park_dir / "latest.json"
        self.backup_status = self.ops / "backup_status.json"
        self.paths = TOOL.Paths(self.clone, self.ops)
        if deployment:
            write(self.deployment, "the bot tuner's deployment clone (fake)\n")
        self.rows = [{"source": "ai0053", "batch": "b53", "lane": i, "log": f"l{i}.log"} for i in range(5)]
        cycles = [{"source": "cycle", "tag": "ai0053", "runs": 5}]
        self.state_doc = {"cycle": 54, "current": {"tag": "ai0054", "started": T_ROUND_TEXT, "lanes": 12,
                                                   "minutes": 720.0},
                          "cycles": [{"tag": "ai0052"}, {"tag": "ai0053"}]}
        if between_rounds:
            self.rows += [{"source": "ai0054", "batch": "b54", "lane": i, "log": f"m{i}.log"} for i in range(4)]
            cycles.append({"source": "cycle", "tag": "ai0054", "runs": 4})
            self.state_doc["current"] = None
            self.state_doc["cycles"].append({"tag": "ai0054"})
        write(self.runs, jl(self.rows))
        write(self.cycles, jl(cycles))
        write(self.state, json.dumps(self.state_doc))
        write(self.lock, "5372")
        write(self.log, f"[{ts(T_OLD)}] {STOP_LINE_TEXT}\n"
                        f"[2026-10-28 04:30:17 PM] learner started (code 85e3e9eb57b1)\n"
                        f"[{T_ROUND_TEXT}] ai0054: starting 12 lanes for 720 minutes\n")
        if ops:
            write(self.backup_status, json.dumps({"time": "2026-10-28 01:00:01 AM", "ok": True, "zip": "Z:\\x.zip"}))
        self.args = ["--clone", str(self.clone), "--ops-dir", str(self.ops)]

    def env(self, start: datetime) -> FakeEnv:
        return FakeEnv(start, self.stop)

    def running(self, env: FakeEnv) -> None:
        env.stop_file = self.stop
        env.procs = ([proc(k, self.clone) for k in ("window", "conhost", "launcher", "learner", "batch")]
                     + lanes(self.clone) + [proc("watchdog_ps", self.clone)])
        env.alive = {p["ProcessId"] for p in env.procs}
        env.tasks[A]["state"] = "Running"

    def place_stop(self, at: datetime = T_STOP, text: str = "the user's own STOP\n") -> None:
        write(self.stop, text)
        set_mtime(self.stop, at)

    def stop_cleanly(self, env: FakeEnv, at: datetime, tag: str = "ai0054", runs: int = 4, rows: int | None = None,
                     stop_line: bool = True, window_open: bool = True) -> None:
        """What the learner does at a clean STOP exit: the round recorded (runs.jsonl rows, a cycles.jsonl row,
        state.json current empty and the tag in its cycles), the STOP line logged, the lock released, and every process
        gone but the -NoExit window."""
        self.rows += [{"source": tag, "batch": f"b{tag}", "lane": i, "log": f"g{i}.log"}
                      for i in range(runs if rows is None else rows)]
        write(self.runs, jl(self.rows))
        append(self.cycles, json.dumps({"source": "cycle", "tag": tag, "runs": runs}) + "\n")
        st = json.loads(self.state.read_text(encoding="utf-8"))
        st["current"] = None
        st["cycles"].append({"tag": tag})
        write(self.state, json.dumps(st))
        if stop_line:
            append(self.log, f"[{ts(at)}] {STOP_LINE_TEXT}\n")
        if self.lock.exists():
            self.lock.unlink()
        env.procs = [proc("window", self.clone), proc("conhost", self.clone)] if window_open else []
        env.alive = {q["ProcessId"] for q in env.procs}
        env.mark("stopped")

    def make_stopped(self, env: FakeEnv, window_open: bool = True) -> None:
        self.running(env)
        self.stop_cleanly(env, STOP_AT, window_open=window_open)
        env.tasks[A]["state"] = "Running" if window_open else "Ready"

    def make_parked(self, env: FakeEnv, window_open: bool = True) -> None:
        self.make_stopped(env, window_open)
        self.place_stop(T_STOP, "STOP placed by tools/ops/park_tuner.py (park --apply) at 2026-10-28 05:00:00 PM.\n")
        for name, t in env.tasks.items():
            t["enabled"] = False
            t["state"] = "Running" if (name == A and window_open) else "Disabled"

    def backup(self, rc: int = 0, time: str | None = None, ok: bool = True, tamper: str | None = None,
               drop: str | None = None, corrupt: bool = False, gone: bool = False, ok_key: bool = True, effect=None):
        """A backup that writes a REAL zip of the three files under their LITERAL member names (ZIP_NAMES) and a status
        file. Each failure arm changes exactly ONE thing (the exit code, the status time, ok, one zip member, the zip),
        so each check of verify_backup is needed on its own. `effect(env)` runs first (something happening during the
        backup)."""
        def run(paths, now):
            if effect is not None:
                effect()
            z = self.ops / f"learner-data-{now:%Y%m%d-%H%M%S}.zip"
            z.parent.mkdir(parents=True, exist_ok=True)
            if corrupt:
                z.write_bytes(b"PK\x03\x04 this is not a zip (fake)")
            else:
                with zipfile.ZipFile(z, "w") as zf:
                    for key, member in ZIP_NAMES.items():
                        if key == drop:
                            continue
                        data = getattr(self, key).read_bytes()
                        zf.writestr(member, TAMPER[key](data) if key == tamper else data)
            status = {"time": time or ts(now), "zip": str(z.with_name("gone.zip") if gone else z),
                      "bytes": z.stat().st_size, "error": None if ok else "NEEDS-YOU (fake): runs.jsonl shrank"}
            if ok_key:
                status["ok"] = ok
            write(self.backup_status, json.dumps(status))
            return rc, "OK learner-data (fake)" if rc == 0 else f"exit {rc} (fake)"
        return run

    def good_backup(self, effect=None):
        return self.backup(effect=effect)

    @staticmethod
    def failed_backup(rc: int = 2):
        return lambda paths, now: (rc, "REFUSED: destination drive not present (fake)")

    def learner_starts(self, round_line: bool = True, live: bool = True):
        """The autostart task's effect: a new window and learner, the lock, a NEW 'learner started' line, and (if
        round_line) the round's 'starting 12 lanes' line."""
        def hook(env: FakeEnv):
            env.tasks[A]["state"] = "Running"
            new = [{"ProcessId": 20000, "ParentProcessId": 3720, "Name": "powershell.exe",
                    "CommandLine": proc("window", self.clone)["CommandLine"]},
                   {"ProcessId": 20001, "ParentProcessId": 20000, "Name": "conhost.exe", "CommandLine": "conhost.exe"},
                   {"ProcessId": 20002, "ParentProcessId": 20000, "Name": "py.exe",
                    "CommandLine": SHAPES["launcher"][3]}]
            if live:
                new.append({"ProcessId": 6000, "ParentProcessId": 20002, "Name": "python.exe",
                            "CommandLine": SHAPES["learner"][3]})
            env.procs += new
            env.alive |= {q["ProcessId"] for q in new}
            write(self.lock, "6000")
            append(self.log, f"[{ts(env.clock)}] learner started (code 0123456789ab)\n")
            if round_line:
                append(self.log, f"[{ts(env.clock)}] ai0055: starting 12 lanes for 720 minutes\n")
        return hook


def cli(env: FakeEnv, *argv) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = TOOL.main(list(argv), env=env)
    return code, buf.getvalue()


def snapshot(root: Path) -> dict:
    out = {}
    if root.exists():
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(root).as_posix()
            out[rel] = (sha(p.read_bytes()), p.stat().st_mtime_ns) if p.is_file() else "dir"
    return out


def world(fx: Fixture, env: FakeEnv) -> tuple:
    return (snapshot(fx.root), json.dumps(env.tasks, sort_keys=True), json.dumps(env.procs, sort_keys=True))


def latest(fx: Fixture) -> dict:
    try:
        return json.loads(fx.latest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def enabled(env: FakeEnv) -> dict:
    return {n: t["enabled"] for n, t in env.tasks.items()}


def idx(env: FakeEnv, name: str, arg=None) -> int:
    for i, (n, args, _c) in enumerate(env.events):
        if n == name and (arg is None or arg in args):
            return i
    return -1


def verdict_line(out: str) -> str:
    """The run's final verdict line (the one printed after the blank line), '' when there is none."""
    lines = [ln for ln in out.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if "(exit " in ln and not ln.startswith("[") and not ln.startswith("  "):
            return ln
    return ""


# -------------------------------------------------------------------------------- X: the learner's own source
LEARNER_NAMES = {"deployment": "DEPLOYMENT", "stop": "STOP", "attention": "ATTENTION", "log": "LOG", "lock": "LOCK",
                 "state": "STATE_FILE", "cycles": "CYCLES_FILE", "runs": "RUNS_FILE"}
SAMPLES = {"started_sig": "0123456789ab", "sig": "fedcba987654", "tag": "ai0055", "lanes": 12,
           "plan": {"minutes": 720.0}, "n": 2, "CRASH_LIMIT": 5, "msg": "MSG",
           "tb": "Traceback (most recent call last):\n  RuntimeError: fake"}
SAMPLE_T = datetime(2026, 10, 29, 13, 0, 5)  # a PM time: a pattern that knows only AM fails on it
PATTERNS = ("STOP_LINE", "START_LINE", "ROUND_LINE", "RESTART_LINE", "CRASH_LINE")
REWORDS = {"STOP_LINE": ('log("STOP file found: stopping', 'log("STOP seen: stopping'),
           "START_LINE": ("learner started (code {started_sig})", "learner is up (code {started_sig})"),
           "ROUND_LINE": (": starting {lanes} lanes for", ": launching {lanes} lanes for"),
           "RESTART_LINE": ('passes: restarting into it")', 'passes: restarting now")'),
           "CRASH_LINE": ("learner CRASHED", "learner FAILED")}
PATH_FAULTS = {"stop": ('AI / "STOP"', 'DATA / "STOP"'),
               "attention": ('FINDINGS / "ATTENTION.md"', 'AI / "ATTENTION.md"'),
               "deployment": ('DEPLOYMENT = AI / "DEPLOYMENT"', 'DEPLOYMENT = AI / "data" / "DEPLOYMENT"')}


HARMLESS_SOURCE = '''
import datetime as dt
from pathlib import Path
AI = Path(__file__).resolve().parent
DATA: Path = AI / "data"
FINDINGS = AI / "findings"
RUNS_FILE, CYCLES_FILE, STATE_FILE = DATA / "runs.jsonl", DATA / "cycles.jsonl", DATA / "state.json"
LOCK, LOG, STOP, ATTENTION = DATA / "agent.lock", DATA / "learner.log", AI / "STOP", FINDINGS / "ATTENTION.md"
DEPLOYMENT: Path = AI / "DEPLOYMENT"
SPARE_STOP = AI / "STOP"
TIME_FMT: str = "%Y-%m-%d %I:%M:%S %p"
def now() -> str:
    return dt.datetime.now().strftime(TIME_FMT)
def log(message: str) -> None:
    text = f"[{now()}] {message}"
    print(text)
def code_signature() -> str:
    return h.hexdigest()[:12]
def run():
    log("STOP file found: stopping (delete ai-agent/STOP to allow the next start)")
    log(f"learner started (code {started_sig})")
    log(f"{tag}: starting {lanes} lanes for {plan['minutes']:.0f} minutes")
    log(f"code changed ({started_sig} -> {sig}) and test_agent.py passes: restarting into it")
    _say(f"learner CRASHED ({n} of {CRASH_LIMIT} in a row):\\n{tb}")
'''  # the same learner, written differently: test X must read it exactly as it reads learner.py


def render(node, extra: dict | None = None) -> str | None:
    """A log message as learner.py renders it: a str constant, or an f-string filled with SAMPLES (and `extra`; 'X' for
    any other name or call; nothing is called: no builtins)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    names = {**SAMPLES, **(extra or {})}
    out = []
    for v in node.values:
        if isinstance(v, ast.Constant):
            out.append(str(v.value))
        elif isinstance(v, ast.FormattedValue):
            try:
                val = eval(compile(ast.Expression(v.value), "<learner f-string>", "eval"),  # noqa: S307 - no builtins
                           {"__builtins__": {}}, dict(names))
            except Exception:  # noqa: BLE001
                val = "X"
            spec = render(v.format_spec, extra) if v.format_spec is not None else ""
            try:
                out.append(format(val, spec or ""))
            except Exception:  # noqa: BLE001
                out.append(str(val))
    return "".join(out)


def learner_facts(source: str) -> dict:
    """From learner.py's SOURCE (AST; never imported): TIME_FMT, its path constants relative to the clone, its log()
    line format, and every message its log()/_say() calls log."""
    tree = ast.parse(source)
    names = {"AI": "ai-agent"}  # learner.py's own folder: AI = Path(__file__).resolve().parent
    time_fmt = None

    def path_of(node):
        if isinstance(node, ast.Name):
            return names.get(node.id)
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str)):
            left = path_of(node.left)
            return None if left is None else f"{left}/{node.right.value}"
        return None

    for node in tree.body:  # module-level `X = ...`, `A, B = ..., ...` and annotated `X: T = ...`
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt, val = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            tgt, val = node.target, node.value
        else:
            continue
        pairs = (list(zip(tgt.elts, val.elts)) if isinstance(tgt, ast.Tuple) and isinstance(val, ast.Tuple)
                 and len(tgt.elts) == len(val.elts) else [(tgt, val)])
        for t, v in pairs:
            if not isinstance(t, ast.Name) or t.id == "AI":
                continue
            if t.id == "TIME_FMT" and isinstance(v, ast.Constant):
                time_fmt = v.value
            p = path_of(v)
            if p is not None:
                names[t.id] = p
    lines, prefix, now_ok, sig_len = [], None, False, None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("log", "_say")
                and len(node.args) == 1):
            text = render(node.args[0])
            if text is not None:
                lines.append(text)
        if isinstance(node, ast.FunctionDef) and node.name == "log" and node.args.args:
            msg = {node.args.args[0].arg: "MSG"}  # log()'s message parameter, whatever its name
            for sub in ast.walk(node):  # the line it writes: the f-string that holds the message
                text = render(sub, msg) if isinstance(sub, ast.JoinedStr) else None
                if text is not None and "MSG" in text:
                    prefix = text
        if isinstance(node, ast.FunctionDef) and node.name == "now":
            now_ok = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "strftime"
                         and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id == "TIME_FMT"
                         for c in ast.walk(node))
        if isinstance(node, ast.FunctionDef) and node.name == "code_signature":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Slice)
                        and isinstance(sub.slice.upper, ast.Constant)):
                    sig_len = sub.slice.upper.value
    return {"time_fmt": time_fmt, "paths": {k: names.get(v) for k, v in LEARNER_NAMES.items()}, "lines": lines,
            "prefix": prefix, "now_ok": now_ok, "sig_len": sig_len}


def pattern_hits(facts: dict) -> dict:
    prefix = f"[{SAMPLE_T.strftime(facts['time_fmt'])}] " if facts["time_fmt"] else "[?] "
    return {n: [prefix + ln for ln in facts["lines"] if getattr(TOOL, n).match(prefix + ln)] for n in PATTERNS}


def tool_rel(paths) -> dict:
    return {k: Path(getattr(paths, k)).relative_to(paths.clone).as_posix() for k in REL}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def t_x(tmp: Path) -> None:
    try:
        src = LEARNER_PY.read_text(encoding="utf-8")
    except OSError as e:
        check("X ai-agent/learner.py is readable next to this repo root (missing is a FAIL, never a skip)", False, str(e))
        return
    facts = learner_facts(src)
    check("X CONTROL learner.py's TIME_FMT is the 12-hour format typed in this selftest, its log() writes "
          "'[<now()>] <msg>' with now() = strftime(TIME_FMT), and the tool's TS_FMT is that format (sweep S21)",
          facts["time_fmt"] == LEARNER_FMT and TOOL.TS_FMT == LEARNER_FMT and facts["now_ok"]
          and facts["prefix"] == "[X] MSG", f"{facts['time_fmt']!r} {TOOL.TS_FMT!r} {facts['prefix']!r}")
    check("X CONTROL a literal PM and a 12:30 AM time in the learner's format parse to the afternoon and to just after "
          "midnight", TOOL.parse_ts(T_ROUND_TEXT) == T_ROUND
          and TOOL.parse_ts("2026-10-29 12:30:00 AM") == datetime(2026, 10, 29, 0, 30), "")
    fx = Fixture(tmp, "x_paths")
    check("X CONTROL learner.py's own paths (STOP, ATTENTION.md, DEPLOYMENT, agent.lock, learner.log, state.json, "
          "cycles.jsonl, runs.jsonl) equal the literal layout typed here AND the tool's Paths (sweep S31, S32, S50)",
          facts["paths"] == REL and tool_rel(fx.paths) == REL, f"learner {facts['paths']}\ntool {tool_rel(fx.paths)}")
    hits = pattern_hits(facts)
    for name, what in (("STOP_LINE", "'STOP file found: stopping ...'"), ("START_LINE", "'learner started (code ...)'"),
                       ("ROUND_LINE", "'<tag>: starting N lanes for M minutes'"),
                       ("RESTART_LINE", "'code changed (...) and test_agent.py passes: restarting into it'"),
                       ("CRASH_LINE", "'learner CRASHED ...'")):
        check(f"X CONTROL the tool's {name} matches the line learner.py really logs ({what}, at a PM time)",
              bool(hits[name]), str(hits[name][:1]))
    m = TOOL.ROUND_LINE.match(hits["ROUND_LINE"][0]) if hits["ROUND_LINE"] else None
    check("X CONTROL ROUND_LINE reads the tag, the lanes and the minutes from the learner's real line",
          m is not None and (m["tag"], m["lanes"], m["minutes"]) == ("ai0055", "12", "720"), str(hits["ROUND_LINE"][:1]))
    check("X CONTROL learner.py's code signature is 12 hex (hexdigest()[:12]): what START_LINE requires",
          facts["sig_len"] == 12, str(facts["sig_len"]))
    for name, (old, new) in REWORDS.items():
        f2 = learner_facts(src.replace(old, new))
        h2 = pattern_hits(f2)
        check(f"X FAULT a learner.py that rewords its {name} line ({old!r} -> {new!r}) IS caught: no line matches any "
              "more, while the other four still do", src.count(old) >= 1 and not h2[name]
              and all(h2[n] for n in PATTERNS if n != name), f"{src.count(old)} {[(n, len(h2[n])) for n in PATTERNS]}")
    for key, (old, new) in PATH_FAULTS.items():
        f2 = learner_facts(src.replace(old, new))
        check(f"X FAULT a learner.py whose {key} moved ({old!r} -> {new!r}) IS caught",
              src.count(old) >= 1 and f2["paths"][key] != REL[key] and f2["paths"] != REL, str(f2["paths"][key]))
    f2 = learner_facts(src.replace('"%Y-%m-%d %I:%M:%S %p"', '"%Y-%m-%d %H:%M:%S"'))
    check("X FAULT a learner.py that logs 24-hour times IS caught", src.count('"%Y-%m-%d %I:%M:%S %p"') >= 1
          and f2["time_fmt"] != LEARNER_FMT, str(f2["time_fmt"]))
    f3 = learner_facts(HARMLESS_SOURCE)
    check("X CONTROL harmless ways of writing the same learner (annotated constants, log()'s parameter and its local "
          "renamed, a constant repeated) do NOT trip this gate: a gate with false alarms teaches people to bypass it",
          f3["time_fmt"] == LEARNER_FMT and f3["prefix"] == "[X] MSG" and f3["now_ok"] and f3["paths"] == REL
          and f3["sig_len"] == 12 and all(pattern_hits(f3)[n] for n in PATTERNS), f"{f3}")
    f2 = learner_facts(src.replace("hexdigest()[:12]", "hexdigest()[:16]"))
    check("X FAULT a learner.py with a 16-hex code signature IS caught", f2["sig_len"] == 16, str(f2["sig_len"]))
    try:
        bl = load_module(BACKUP_PY, "backup_learner_for_park_selftest")  # stdlib only, no side effects on import
    except Exception as e:  # noqa: BLE001
        check("X tools/ops/backup_learner.py loads (missing is a FAIL, never a skip)", False, f"{type(e).__name__}: {e}")
        return
    ai = tmp / "x_backup" / "ai-agent"
    for rel in ("data/runs.jsonl", "data/cycles.jsonl", "data/state.json", "data/agent.lock", "data/learner.log"):
        write(ai / rel, "x\n")
    members = {m for m, _p in bl.source_files(ai, None)}
    check("X CONTROL backup_learner.py's own source_files() names runs.jsonl, cycles.jsonl and state.json exactly as "
          "the tool verifies them (ZIP_MEMBERS) and as this selftest's fake backup writes them (sweep S45, S46)",
          set(ZIP_NAMES.values()) <= members and TOOL.ZIP_MEMBERS == ZIP_NAMES
          and "ai-agent/data/agent.lock" not in members, str(sorted(members)))
    check("X CONTROL backup_learner.py's status time (stamp) is the learner's 12-hour format, and the tool parses a PM "
          "stamp back to the afternoon", bl.stamp(SAMPLE_T) == "2026-10-29 01:00:05 PM"
          and TOOL.parse_ts(bl.stamp(SAMPLE_T)) == SAMPLE_T, bl.stamp(SAMPLE_T))


# ----------------------------------------------------------------------------------------------------------- tests
def short_path(p: str) -> str:
    try:
        buf = ctypes.create_unicode_buffer(32768)
        n = ctypes.windll.kernel32.GetShortPathNameW(p, buf, 32768)
        return buf.value if 0 < n < 32768 else p
    except (AttributeError, OSError):
        return p


def t_m(tmp: Path) -> None:
    paths = TOOL.Paths(TOOL.DEFAULT_CLONE, tmp / "m_ops")  # the REAL clone's path: computed only, never written
    tuner = [proc(k) for k in ("launcher", "learner", "batch")] + lanes()
    others = [proc(k) for k in ("window", "conhost", "watchdog_ps", "watchdog_py", "backup_task", "tool_main",
                                "tool_clone", "park_watch")]
    got = TOOL.trainer_processes(tuner + others, os.getpid(), paths)
    check("M CONTROL the learner, its py.exe launcher (under the clone's run_agent.ps1 window), the batch and 12 lanes "
          "(real shapes) ARE the tuner (15)", ids(got) == ids(tuner), str([TOOL.short(p) for p in got]))
    wrong = [TOOL.short(p) for p in got if p in others]
    check("M FAULT-ARMS the window, conhost, the watchdog (powershell + py), the backup task, this tool (main checkout "
          "and clone copy) and park_watch are NOT the tuner", not wrong, str(wrong))
    check("M lane and batch counts from the real shapes: 12 lanes, 1 batch",
          len(TOOL.lane_processes(got)) == 12 and len(TOOL.batch_processes(got)) == 1, "")
    main_lane = {"ProcessId": 70001, "ParentProcessId": 1, "Name": "python.exe",
                 "CommandLine": lane_cmd(1, "C:\\Remote Projects\\Pokebot_Gen3_Enhancement")}
    sibling = {"ProcessId": 70002, "ParentProcessId": 1, "Name": "python.exe",
               "CommandLine": lane_cmd(2, "C:\\Remote Projects\\pokebot-learner-old")}
    me = {"ProcessId": os.getpid(), "ParentProcessId": 10588, "Name": "python.exe", "CommandLine": PY + " learner.py run"}
    stray = TOOL.trainer_processes([main_lane, sibling, me, proc("window")], os.getpid(), paths)
    check("M FAULT a lane of another checkout, a lane of a sibling folder 'pokebot-learner-old', and a learner-shaped "
          "process with this process's own PID are NOT this tuner's", not stray, str([TOOL.short(p) for p in stray]))
    check("M pid_is_learner: CONTROL the learner's PID is the learner; FAULT a reused PID (chrome) and None are not",
          TOOL.pid_is_learner(5372, tuner) and not TOOL.pid_is_learner(5372, [
              {"ProcessId": 5372, "Name": "chrome.exe", "CommandLine": "chrome.exe --type=renderer"}])
          and not TOOL.pid_is_learner(None, tuner), "")
    wins = TOOL.window_processes(tuner + others, paths)
    other_win = {"ProcessId": 70003, "ParentProcessId": 1, "Name": "powershell.exe", "CommandLine":
                 '"powershell.exe" -NoExit -File "C:\\Remote Projects\\Pokebot_Gen3_Enhancement\\ai-agent\\run_agent.ps1"'}
    check("M CONTROL the clone's -NoExit run_agent.ps1 window is found; FAULT another checkout's window is not",
          [w["ProcessId"] for w in wins] == [10588] and not TOOL.window_processes([other_win], paths), str(wins))
    dev_shell = {"ProcessId": 46000, "ParentProcessId": 1, "Name": "powershell.exe", "CommandLine": "powershell.exe"}
    dev = {"ProcessId": 47000, "ParentProcessId": 46000, "Name": "python.exe", "CommandLine": PY + " learner.py run --dev"}
    test_agent = {"ProcessId": 47150, "ParentProcessId": 1, "Name": "python.exe", "CommandLine": PY + " test_agent.py"}
    r21 = {"ProcessId": 47200, "ParentProcessId": 47150, "Name": "python.exe", "CommandLine": PY + " learner.py run"}
    loop = {"ProcessId": 47100, "ParentProcessId": 46100, "Name": "bash.exe",
            "CommandLine": '"C:\\Program Files\\Git\\bin\\bash.exe" -c "until ! powershell -c \\"gcim win32_process\\" '
                           "| grep -q 'learner.py run'; do sleep 60; done\""}
    strangers = [dev_shell, dev, test_agent, r21, loop]
    got2 = TOOL.trainer_processes(tuner + others + strangers, os.getpid(), paths)
    check("M FAULT (review F3) a --dev learner of another checkout, test_agent.py's `learner.py run` child and a shell "
          "loop that greps for 'learner.py run' are NOT this clone's tuner; the real 15 still are",
          ids(got2) == ids(tuner), str([TOOL.short(p) for p in got2 if p not in tuner]))
    check("M CONTROL status lists those three as other learners (not counted)",
          ids(TOOL.other_learners(tuner + others + strangers, got2, os.getpid())) == [47000, 47100, 47200], "")
    shell = {"ProcessId": 48000, "ParentProcessId": 48500, "Name": "powershell.exe", "CommandLine": "powershell.exe"}
    hand_py = {"ProcessId": 48001, "ParentProcessId": 48000, "Name": "py.exe",
               "CommandLine": '"C:\\Windows\\py.exe" -3.12 learner.py run'}
    hand = {"ProcessId": 48002, "ParentProcessId": 48001, "Name": "python.exe", "CommandLine": PY + " learner.py run"}
    without = TOOL.trainer_processes([shell, hand_py, hand], os.getpid(), paths, None)
    with_lock = TOOL.trainer_processes([shell, hand_py, hand], os.getpid(), paths, 48002)
    check("M CONTROL a learner started by hand (no run_agent window) is this clone's once it holds agent.lock, and so is "
          "its py.exe launcher; FAULT without the lock it is not", not without and ids(with_lock) == [48001, 48002],
          f"{ids(without)} {ids(with_lock)}")
    fwd_lane = {"ProcessId": 71001, "ParentProcessId": 1, "Name": "python.exe",
                "CommandLine": PY + ' "C:/Remote Projects/pokebot-learner/sandbox-pokebot/pokebot.py" '
                                    'endless-ai0054-H1-torchic -m "Story (ENDLESS RESET)"'}
    fwd_batch = {"ProcessId": 71002, "ParentProcessId": 1, "Name": "python.exe",
                 "CommandLine": PY + ' "C:/Remote Projects/pokebot-learner/tools/story-dev/x4_headless.py" --build '
                                     'sandbox --lanes 12'}
    full = {"ProcessId": 71003, "ParentProcessId": 1, "Name": "python.exe",
            "CommandLine": PY + ' "C:\\Remote Projects\\pokebot-learner\\ai-agent\\learner.py" run'}
    got3 = TOOL.trainer_processes([fwd_lane, fwd_batch, full], os.getpid(), paths)
    check("M CONTROL a lane and a batch launched with FORWARD slashes, and a learner started by its full path, ARE the "
          "tuner (sweep S40, S37)", ids(got3) == [71001, 71002, 71003] and len(TOOL.lane_processes(got3)) == 1
          and len(TOOL.batch_processes(got3)) == 1, str(ids(got3)))
    pt = {"ProcessId": 72001, "ParentProcessId": 1, "Name": "python.exe",
          "CommandLine": PY + ' "C:\\Users\\me\\scratch\\park_tuner.py" status --note "' + REAL + '\\sandbox-pokebot"'}
    pw = {"ProcessId": 72002, "ParentProcessId": 1, "Name": "python.exe",
          "CommandLine": PY + ' "C:\\Users\\me\\scratch\\park_watch.py" --live --note "' + REAL + '\\sandbox-pokebot"'}
    check("M FAULT park_tuner.py and park_watch.py run OUTSIDE tools\\ops, with the clone's lane folder in their "
          "arguments, are NOT the tuner (their own exclusions: sweep S38, S39)",
          not TOOL.trainer_processes([pt], os.getpid(), paths) and not TOOL.trainer_processes([pw], os.getpid(), paths),
          "")
    real = tmp / "m_alias" / "pokebot-learner"
    real.mkdir(parents=True)
    long_p = TOOL._long_path(str(real))
    shapes = [proc(k, long_p) for k in ("window", "conhost", "launcher", "learner", "batch")] + lanes(long_p)

    def count(spelling: str) -> tuple:
        got_ = TOOL.trainer_processes(shapes, os.getpid(), TOOL.Paths(Path(spelling), tmp / "m_alias_ops"))
        return len(TOOL.lane_processes(got_)), len(TOOL.batch_processes(got_)), len(got_)
    cwd = os.getcwd()
    try:
        os.chdir(real.parent)
        rel_count = count("pokebot-learner")
    finally:
        os.chdir(cwd)
    spellings = {"relative ('pokebot-learner' from its parent)": rel_count,
                 "\\\\?\\ prefixed": count("\\\\?\\" + long_p), "forward slashes": count(long_p.replace("\\", "/")),
                 "upper case": count(long_p.upper())}
    sp = short_path(long_p)
    if sp.lower() != long_p.lower():  # only where the volume has 8.3 names (otherwise there is nothing to test)
        spellings[f"8.3 ({sp})"] = count(sp)
    for label, c in spellings.items():
        check(f"M CONTROL a --clone spelled {label} still sees the 12 lanes, the batch and the learner (review F6)",
              c == (12, 1, 15), str(c))
    try:  # a --clone reached through a JUNCTION: learner.py spells its batch and lanes from Path(__file__).resolve()
        import _winapi
        link = tmp / "m_junction_link"
        _winapi.CreateJunction(str(real.parent), str(link))
    except (ImportError, AttributeError, OSError):
        link = None  # no junctions here: nothing to test (the arm is left out, never passed)
    if link is not None:
        try:
            c = count(str(link / "pokebot-learner"))
        finally:
            os.rmdir(link)  # removes the junction only, never its target
        check("M CONTROL a --clone reached through a JUNCTION sees the lanes spelled with its resolved target (as "
              "learner.py's Path(__file__).resolve() spells them; review F6)", c == (12, 1, 15), str(c))
    fx = Fixture(tmp, "m_f6_park")
    env = fx.env(NOW0)
    fx.running(env)
    gone = {10588, 32140, 42712, 5372}  # the window was closed: the learner is gone, its batch and 12 lanes run on
    env.procs = [p for p in env.procs if p["ProcessId"] not in gone]
    env.alive -= gone
    fx.lock.unlink()
    env.tasks[A]["state"] = "Ready"
    env.backups = [fx.good_backup(), fx.good_backup()]
    try:
        os.chdir(fx.root)
        code, out = cli(env, "park", "--apply", "--deadline", ts(NOW0 + timedelta(minutes=5)), "--clone",
                        "pokebot-learner", "--ops-dir", str(fx.ops))
    finally:
        os.chdir(cwd)
    check("M FAULT end to end (review F6): park --apply with a RELATIVE --clone while the learner is gone and its 12 "
          "lanes run does NOT park: no task touched, no backup (it waits, then TIMEOUT)",
          code == 20 and not env.changes() and set(enabled(env).values()) == {True}, f"code {code} {env.changes()}")


@contextlib.contextmanager
def canned(ps=None, run=None, guard_off: bool = False):
    """RealEnv's own code with CANNED answers: `ps(command)` / `run(argv)` -> (rc, stdout, stderr); they start NOTHING.
    `guard_off` lifts the test guard only while a canned stub is in place (the tripwire still guards the other
    launcher). The tripwires, the guard and tempfile are always put back."""
    saved = (TOOL._ps, TOOL._run, TOOL.guard_action, TOOL.tempfile)
    calls: list = []

    def fake_ps(command, timeout=180):
        calls.append(("ps", command))
        rc, out, err = ps(command)
        return subprocess.CompletedProcess(["powershell"], rc, stdout=out, stderr=err)

    def fake_run(argv, timeout, cwd=None):
        calls.append(("run", list(argv), cwd))
        rc, out, err = run(argv)
        return subprocess.CompletedProcess(list(argv), rc, stdout=out, stderr=err)
    try:
        if ps is not None:
            TOOL._ps = fake_ps
        if run is not None:
            TOOL._run = fake_run
        if guard_off:
            assert ps is not None or run is not None, "the guard is lifted only over a canned stub"
            TOOL.guard_action = lambda what: None
        yield calls
    finally:
        TOOL._ps, TOOL._run, TOOL.guard_action, TOOL.tempfile = saved


def t_re(tmp: Path) -> None:
    env = TOOL.RealEnv()
    name = "Pokebot-PARKTEST-NO-SUCH-TASK"  # even a canned call never names a real task
    with canned(ps=lambda c: (0, "Ready|True\r\n", "")) as calls:
        a, b = env.task_info(name), env.task_enabled(name)
    with canned(ps=lambda c: (0, "Running|False", "")):
        c = env.task_info(name)
    check("RE CONTROL RealEnv.task_info reads Get-ScheduledTask's 'State|Settings.Enabled': Ready|True -> ON, "
          "Running|False -> OFF with State Running (sweep S58)",
          a == {"state": "Ready", "enabled": True} and b is True and c == {"state": "Running", "enabled": False}
          and f"-TaskName '{name}'" in calls[0][1] and "Settings.Enabled" in calls[0][1], f"{a} {b} {c}")
    for label, rc, out in (("a failed read (exit 1, no output)", 1, ""), ("an unreadable answer", 0, "Ready|maybe")):
        try:
            with canned(ps=lambda c_, rc=rc, out=out: (rc, out, "No MSFT_ScheduledTask objects found (fake)")):
                res = f"returned {env.task_info(name)}"
        except RuntimeError as e:
            res = f"raised: {e}"
        check(f"RE FAULT RealEnv.task_info on {label} RAISES: a task that cannot be read never reads OFF (sweep S59)",
              res.startswith("raised: cannot read"), res)
    with canned(ps=lambda c_: (0, json.dumps({"ProcessId": 4, "ParentProcessId": 0, "Name": "System",
                                              "CommandLine": None}), "")):
        one = env.processes()
    with canned(ps=lambda c_: (0, json.dumps([{"ProcessId": 4}, {"ProcessId": 8}]), "")):
        two = env.processes()
    try:
        with canned(ps=lambda c_: (1, "", "Get-CimInstance failed (fake)")):
            env.processes()
        failed = "no raise"
    except RuntimeError:
        failed = "raised"
    check("RE RealEnv.processes: ConvertTo-Json's single object becomes a list of one, a list stays a list; FAULT a "
          "failed listing RAISES", len(one) == 1 and one[0]["ProcessId"] == 4 and len(two) == 2 and failed == "raised",
          f"{one} {two} {failed}")
    child = subprocess.Popen([sys.executable, "-c", "pass"])  # its handle stays open below, so its PID is not reused
    child.wait()
    me_alive, child_alive = env.pid_alive(os.getpid()), env.pid_alive(child.pid)
    check("RE CONTROL RealEnv.pid_alive (OpenProcess + GetExitCodeProcess, read-only): this process is alive; FAULT a "
          "child that has exited is NOT (sweep S60)", me_alive is True and child_alive is False,
          f"{me_alive} {child_alive}")
    del child
    clone = tmp / "re_clone"
    with canned(run=lambda argv: (0, "c69ee31e\n", "")) as calls:
        head = env.git_head(clone)
    check("RE RealEnv.git_head runs ONLY `git -C <clone> rev-parse --short HEAD` and returns its answer",
          head == "c69ee31e" and calls == [("run", ["git", "-C", str(clone), "rev-parse", "--short", "HEAD"], None)],
          str(calls))
    paths = TOOL.Paths(clone, tmp / "re_ops")
    with canned(run=lambda argv: (0, "OK (fake)", ""), guard_off=True) as calls:
        rc, _out = env.run_backup(paths)
    argv, cwd = (calls[0][1], calls[0][2]) if calls else (None, None)
    check("RE RealEnv.run_backup runs the nightly task's backup `py -3.12 -B <clone>/tools/ops/backup_learner.py` with "
          "its working folder OUTSIDE the clone (sweep S61)",
          rc == 0 and argv == ["py", "-3.12", "-B", str(paths.backup_script)] and cwd is not None
          and not TOOL.is_under(Path(cwd), paths.clone), f"{argv} {cwd}")

    class InsideTemp:
        @staticmethod
        def gettempdir():
            return str(paths.clone / "tmp")
    with canned(run=lambda argv: (0, "OK (fake)", ""), guard_off=True) as calls:
        TOOL.tempfile = InsideTemp
        env.run_backup(paths)
    check("RE FAULT a temp folder INSIDE the clone is not used: the backup then runs in the ops folder",
          bool(calls) and calls[0][2] == str(paths.ops), str(calls[:1]))
    for meth, verb in (("task_disable", "Disable-ScheduledTask"), ("task_enable", "Enable-ScheduledTask"),
                       ("task_start", "Start-ScheduledTask"), ("task_stop", "Stop-ScheduledTask")):
        with canned(ps=lambda c_: (0, "", ""), guard_off=True) as calls:
            getattr(env, meth)(name)
        sent = calls[0][1] if calls else ""
        try:
            with canned(ps=lambda c_: (1, "", "Access is denied (fake)"), guard_off=True):
                getattr(env, meth)(name)
            raised = False
        except RuntimeError:
            raised = True
        check(f"RE RealEnv.{meth} sends exactly `{verb} -TaskName '<task>'` and RAISES when PowerShell fails (canned "
              "PowerShell: nothing runs)", len(calls) == 1 and sent.startswith(f"{verb} -TaskName '{name}'") and raised,
              f"{sent!r} {raised}")
    check("RE the tripwires and the test guard are back in place after every canned call",
          TOOL._ps is tripwire_ps and TOOL._run is tripwire_run and TOOL.guard_action is REAL_GUARD_ACTION
          and TOOL.tempfile is tempfile, "")


def t_s(tmp: Path) -> None:
    def status(name, setup, ops=False):
        fx = Fixture(tmp, name, ops=ops)
        env = fx.env(NOW_S)
        setup(fx, env)
        snap = snapshot(fx.root)
        code, out = cli(env, "status", *fx.args)
        clean = snapshot(fx.root) == snap and not env.changes() and (ops or not fx.ops.exists())
        return code, out, out.splitlines()[0] if out else "", clean

    code, out, first, clean = status("s_running", lambda fx, env: fx.running(env))
    check("S CONTROL RUNNING: exit 0, the verdict on the FIRST line with round ai0054 and 12 lanes; the three tasks ON; "
          "the window runs the learner", code == 0 and first.startswith("RUNNING:") and "ai0054" in first
          and "12 lanes" in first and out.count(": ON (State") == 3 and "window is open (PID 10588): it runs the learner"
          in out, out[:900])
    check("S status writes NOTHING: the ops folder is absent after, every file and time equal, no changing call",
          clean, out[:300])
    check("S CONTROL times are 12-hour: the round 'started 4:30 PM' (from the literal \"04:30:19 PM\"), 'ends about "
          "4:30 AM tomorrow'; hm(16:30) is '4:30 PM' (sweep S24)",
          "started 4:30 PM, 720 minutes; ends about 4:30 AM tomorrow" in out
          and TOOL.hm(datetime(2026, 10, 28, 16, 30), NOW_S) == "4:30 PM", out[:600])

    def pending(fx, env):
        fx.running(env)
        fx.place_stop()
    code, out, first, clean = status("s_pending", pending)
    check("S FAULT STOP while it runs is PARK PENDING (61), not RUNNING, with the round's end (4:30 AM tomorrow)",
          code == 61 and first.startswith("PARK PENDING:") and "4:30 AM tomorrow" in first and clean, out[:600])

    def waiting(fx, env, stale=False):
        pending(fx, env)
        holder = proc("tool_main")
        env.procs.append(holder)
        if not stale:
            env.alive.add(holder["ProcessId"])
        write(fx.tool_lock, json.dumps({"pid": holder["ProcessId"], "since": "2026-10-28 05:00:00 PM",
                                        "command": "park --apply", "phase": "waiting", "poll": 60}))
    code, out, first, clean = status("s_waiting", waiting, ops=True)
    nxt = [ln for ln in out.splitlines() if ln.startswith("What to do next")]
    check("S CONTROL (review F1) a park --apply WAITING for the round is shown ('Park tool: ... is WAITING'), and the "
          "next step names the real cancel: resume --apply ends that waiting park", code == 61
          and "Park tool:  park --apply (PID 51200" in out and "is WAITING for the round to end" in out
          and nxt and "the waiting park --apply (PID 51200) finishes the park by itself" in nxt[0]
          and "resume --apply` (it deletes STOP, which ends that waiting park as CANCELLED" in nxt[0] and clean,
          out[-900:])
    def resuming(fx, env):
        pending(fx, env)
        holder = {"ProcessId": 7778, "ParentProcessId": 1, "Name": "py.exe",
                  "CommandLine": '"C:\\Windows\\py.exe" -3.12 tools/ops/park_tuner.py resume --apply'}
        env.procs.append(holder)
        env.alive.add(7778)
        write(fx.tool_lock, json.dumps({"pid": 7778, "since": "2026-10-28 05:14:00 PM", "command": "resume --apply",
                                        "phase": "starting"}))
    code, out, first, clean = status("s_resuming", resuming, ops=True)
    nxt = [ln for ln in out.splitlines() if ln.startswith("What to do next")]
    check("S FAULT a RESUME --apply holds the lock during PARK PENDING: the next step says to let it finish, and never "
          "advises a park or resume --apply that would be refused", code == 61 and nxt
          and "let it finish" in nxt[0] and "resume --apply (PID 7778" in nxt[0]
          and "To cancel the park instead" not in nxt[0] and clean, nxt[0] if nxt else out[-300:])
    code, out, first, clean = status("s_waiting_stale", lambda fx, env: waiting(fx, env, stale=True), ops=True)
    check("S FAULT a park tool lock whose PID is dead is shown as STALE (the next --apply replaces it), and the next "
          "step does not claim a park is waiting", code == 61 and "a stale lock of park --apply" in out
          and "the waiting park --apply" not in out and clean, out[-700:])

    code, out, first, clean = status("s_parked", lambda fx, env: fx.make_parked(env))
    check("S CONTROL PARKED (62): STOP, nothing runs, all three OFF; the old window is shown idle and safe to close",
          code == 62 and first.startswith("PARKED:") and out.count(": OFF (State") == 3
          and "idle, so closing it is safe" in out and "Park tool:  no park or resume --apply is running" in out
          and clean, out[:900])

    def parked_stranger(fx, env):
        fx.make_parked(env)
        env.procs.append({"ProcessId": 47000, "ParentProcessId": 46000, "Name": "python.exe",
                          "CommandLine": PY + " learner.py run --dev"})
        env.alive.add(47000)
    code, out, first, clean = status("s_parked_other", parked_stranger)
    check("S CONTROL (review F3) a --dev learner of another checkout leaves a PARKED tuner PARKED (62), not PARK PENDING; "
          "it is listed as not this clone's", code == 62 and first.startswith("PARKED:")
          and "1 'learner.py run' process(es) that are NOT this clone's tuner" in out and clean, out[:900])

    def partly(fx, env):
        fx.make_parked(env)
        env.tasks[B]["enabled"], env.tasks[B]["state"] = True, "Ready"
    code, out, first, clean = status("s_partly", partly)
    check("S FAULT one task still ON is PARTLY PARKED (63), naming it and what park --apply would still do",
          code == 63 and first.startswith("PARTLY PARKED:") and B in first and "run and verify the final backup" in out
          and f"then switch OFF {B}" in out and clean, out[:900])

    def parking_now(fx, env):  # a park --apply past its wait: two tasks OFF, the backup running
        partly(fx, env)
        env.procs.append(proc("tool_main"))
        env.alive.add(51200)
        write(fx.tool_lock, json.dumps({"pid": 51200, "since": "2026-10-29 04:33:00 AM", "command": "park --apply",
                                        "phase": "parking", "poll": 60}))
    code, out, first, clean = status("s_parking_now", parking_now, ops=True)
    nxt = [ln for ln in out.splitlines() if ln.startswith("What to do next")]
    check("S FAULT PARTLY PARKED while a park --apply is past its wait (it holds the lock, phase parking): the next step "
          "is to let it finish, never 'run park --apply to finish' (that would be refused)", code == 63 and nxt
          and "let it finish" in nxt[0] and "park --apply` to finish" not in nxt[0] and clean, nxt[0] if nxt else "")
    fx = Fixture(tmp, "s_resume_stopped_early")
    env = fx.env(NOW_R)
    fx.make_stopped(env)  # NOT parked, the old window open: resume places its own STOP before it ends the window
    env.tasks[W]["enabled"], env.tasks[W]["state"] = False, "Disabled"
    env.tasks[W]["fail_enable"] = True  # ... and then an Enable fails: the resume stops with its STOP still in place
    code_r, out_r = cli(env, "resume", "--apply", *fx.args)
    snap = snapshot(fx.clone)
    code, out = cli(env, "status", *fx.args)
    first = out.splitlines()[0] if out else ""
    nxt = [ln for ln in out.splitlines() if ln.startswith("What to do next")]
    check("S FAULT a resume that stopped early left ITS OWN STOP (an Enable failed after it placed STOP for the window): "
          "status says so on the FIRST line, and the next step is resume --apply again, never 'run park --apply to "
          "finish' (the user wants the tuner running)", code_r == 10 and fx.stop.exists() and code == 63
          and "resume --apply's own" in first and nxt and "resume --apply` again to finish the resume" in nxt[0]
          and "park --apply` to finish" not in nxt[0] and snapshot(fx.clone) == snap, first + " | " + (nxt[0] if nxt
                                                                                                          else ""))

    def attention(fx, env):
        fx.make_stopped(env)
        write(fx.attention, ATTENTION_TEXT)
    code, out, first, clean = status("s_stopped_att", attention)
    check("S FAULT no STOP and nothing runs is STOPPED, NOT PARKED (64), naming ATTENTION.md's REASON line (not the "
          "'Fix the cause' footer) and that a logon restarts it",
          code == 64 and first.startswith("STOPPED, NOT PARKED:") and "3 cycles in a row produced no scored runs" in first
          and "Fix the cause" not in first and "a logon restarts it" in first and clean, first)
    code, out, first, clean = status("s_stopped_log", lambda fx, env: fx.make_stopped(env))
    check("S CONTROL STOPPED, NOT PARKED without ATTENTION names the log's last line, and lists the log's tail",
          code == 64 and "The log's last line:" in first and "STOP file found: stopping" in first
          and "Log tail:" in out and "ai0054: starting 12 lanes" in out and clean, out[-700:])

    def inconsistent(fx, env):
        fx.running(env)
        env.tasks[W]["enabled"], env.tasks[W]["state"] = False, "Disabled"
    code, out, first, clean = status("s_incons", inconsistent)
    check("S FAULT a task OFF while it runs without STOP is INCONSISTENT (65), not RUNNING",
          code == 65 and first.startswith("INCONSISTENT:") and "Pokebot-Ops-Watchdog: OFF" in out and clean, out[:600])

    def orphaned(fx, env):
        fx.running(env)
        fx.lock.unlink()
        env.procs = [p for p in env.procs if "learner.py" not in p["CommandLine"]]  # the learner died; its batch runs on
    code, out, first, clean = status("s_orphan", orphaned)
    check("S FAULT the learner DEAD while its batch and 12 lanes run on, the tasks ON, no STOP: INCONSISTENT (65), "
          "never RUNNING (sweep S57)", code == 65 and first.startswith("INCONSISTENT:") and clean, first)
    check("S the six verdict exit codes are distinct and none is 1 (a crash) or 2 (a usage error)",
          len(set(TOOL.STATUS_CODES.values())) == 6 and not {1, 2} & set(TOOL.STATUS_CODES.values()),
          str(TOOL.STATUS_CODES))
    fx = Fixture(tmp, "s_detector")
    snap = snapshot(fx.root)
    append(fx.log, "x\n")
    check("S FAULT the 'writes nothing' comparison does SEE a touched file (it is not vacuous)",
          snapshot(fx.root) != snap, "")


def t_d(tmp: Path) -> None:
    def parked(fx, env):
        fx.make_parked(env)
    cases = [("park on a RUNNING tuner", lambda fx, env: fx.running(env), ["park"]),
             ("park on a PARKED tuner", parked, ["park"]),
             ("park --no-wait --deadline ... on a RUNNING tuner", lambda fx, env: fx.running(env),
              ["park", "--no-wait", "--deadline", "2026-10-29 05:00:00 AM"]),
             ("resume on a PARKED tuner with its old window open", parked, ["resume"]),
             ("resume on a RUNNING tuner", lambda fx, env: fx.running(env), ["resume"]),
             ("resume on a STOPPED, NOT PARKED tuner with its old window open", lambda fx, env: fx.make_stopped(env),
              ["resume"])]
    outs = {}
    for i, (label, setup, argv) in enumerate(cases):
        fx = Fixture(tmp, f"d{i}")
        env = fx.env(NOW_S)
        setup(fx, env)
        before = world(fx, env)
        code, out = cli(env, *argv, *fx.args)
        outs[label] = out
        check(f"D CONTROL dry run, {label}: exit 0, 'DRY RUN', and NOTHING changed (files and times, STOP, tasks, "
              f"processes; no changing call; no ops folder)",
              code == 0 and "DRY RUN" in out and world(fx, env) == before and not env.changes() and not fx.ops.exists(),
              f"code {code} changes {env.changes()} ops {fx.ops.exists()}\n{out[-500:]}")
    o = outs["park on a RUNNING tuner"]
    o = o[o.find("DRY RUN"):]  # the plan only (the status block above it is not the plan)
    order = ["place the STOP file", "wait for round ai0054 to end (about 4:30 AM tomorrow)", "6:00 AM tomorrow",
             "IN THE FOREGROUND", f"switch OFF {A}", f"switch OFF {W}", "run ONE final backup", f"switch OFF {B}",
             "read the three tasks"]
    pos = [o.find(s) for s in order]
    check("D the park plan lists the steps IN ORDER (STOP, the wait with its 6:00 AM deadline and the warning that it "
          "runs in the foreground, the two tasks, the backup, the backup task, the final look) and when it would finish",
          all(p >= 0 for p in pos) and pos == sorted(pos) and "It would finish about 4:40 AM tomorrow" in o, str(pos))
    o = outs["resume on a PARKED tuner with its old window open"]
    o = o[o.find("DRY RUN"):]
    order = [f"switch ON {A}", "end the old idle tuner window", "it is proven idle now", "delete the STOP file",
             f"start {A}", "NEW 'learner started' line"]
    pos = [o.find(s) for s in order]
    check("D the resume plan lists the tasks ON FIRST (still under STOP), then the old window (proven idle now), STOP "
          "deleted, the start and the start check, IN ORDER", all(p >= 0 for p in pos) and pos == sorted(pos)
          and "place the STOP file" not in o, str(pos))
    o = outs["resume on a STOPPED, NOT PARKED tuner with its old window open"]
    o = o[o.find("DRY RUN"):]
    order = ["place the STOP file for a moment", "the three tasks are already ON", "end the old idle tuner window",
             "delete the STOP file", f"start {A}"]
    pos = [o.find(s) for s in order]
    check("D the resume plan on a tuner that is NOT parked places STOP for the window's end and deletes it before the "
          "start (review F8)", all(p >= 0 for p in pos) and pos == sorted(pos), str(pos))
    fx = Fixture(tmp, "d_waiting", ops=True)
    env = fx.env(NOW_S)
    fx.running(env)
    fx.place_stop()
    env.procs.append(proc("tool_main"))
    env.alive.add(51200)
    write(fx.tool_lock, json.dumps({"pid": 51200, "since": "2026-10-28 05:00:00 PM", "command": "park --apply",
                                    "phase": "waiting", "poll": 60}))
    before = world(fx, env)
    code_p, out_p = cli(env, "park", *fx.args)
    code_r, out_r = cli(env, "resume", *fx.args)
    out_r = out_r[out_r.find("DRY RUN"):]
    check("D with a park --apply WAITING (it holds the lock): the park dry run says park --apply would REFUSE now; the "
          "resume plan starts with the cancel of that park and then starts nothing (the learner runs); nothing changed",
          code_p == 0 and "park --apply would REFUSE now" in out_p and code_r == 0
          and "1. cancel the park --apply that WAITS for the round (PID 51200)" in out_r
          and "start NOTHING" in out_r and "delete the STOP file and verify" not in out_r
          and world(fx, env) == before and not env.changes(), out_r[:700])
    fx = Fixture(tmp, "d_fault")
    env = fx.env(NOW_S)
    fx.running(env)
    before = world(fx, env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("D FAULT an ACTING run (park --apply --no-wait) on a twin fixture IS seen by the same comparison (STOP and "
          "the ops folder appear)", world(fx, env) != before and fx.stop.exists() and fx.ops.exists(), f"code {code}")


def t_c1(tmp: Path) -> None:
    for argv in (["park", "--apply"], ["resume", "--apply"], ["park", "--apply", "--no-wait"]):
        fx = Fixture(tmp, "c1_" + "_".join(a.strip("-") for a in argv), deployment=False)
        env = fx.env(NOW0)
        fx.running(env)
        snap = snapshot(fx.root)
        code, out = cli(env, *argv, *fx.args)
        check(f"C1 FAULT {' '.join(argv)} on a clone WITHOUT ai-agent/DEPLOYMENT: REFUSED (50), nothing written (no "
              "ops folder, no STOP, every file equal), no changing call",
              code == 50 and "REFUSED" in out and not fx.ops.exists() and not fx.stop.exists()
              and snapshot(fx.root) == snap and not env.changes(), out[:300])
    fx = Fixture(tmp, "c1_root_marker", deployment=False)
    write(fx.clone / "DEPLOYMENT", "a marker at the clone ROOT (the wrong place)\n")
    env = fx.env(NOW0)
    fx.running(env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("C1 FAULT a DEPLOYMENT marker only at the clone ROOT (not ai-agent/DEPLOYMENT) is REFUSED (sweep S31)",
          code == 50 and "REFUSED" in out and not fx.stop.exists() and not env.changes(), out[:300])
    fx = Fixture(tmp, "c1_deadline")
    env = fx.env(NOW0)
    fx.running(env)
    snap = snapshot(fx.root)
    code, out = cli(env, "park", "--apply", "--deadline", "tomorrow at 6", *fx.args)
    check("C1 FAULT a --deadline that does not parse: REFUSED (50) before anything is written",
          code == 50 and "REFUSED" in out and snapshot(fx.root) == snap and not fx.ops.exists() and not env.changes(),
          out[:300])
    fx = Fixture(tmp, "c1_poll")
    env = fx.env(NOW_S)
    fx.running(env)
    code, out = cli(env, "park", "--poll", "0", *fx.args)
    code2, out2 = cli(env, "park", "--apply", "--poll", "0", *fx.args)
    check("C1 FAULT --poll 0 (a wait that would never sleep) is refused (50) in a dry run and under --apply, before "
          "anything is read or written (sweep S42)", code == 50 and code2 == 50 and "--poll must be above 0" in out
          and not fx.ops.exists() and not env.changes() and not env.calls, out[:200])
    fx = Fixture(tmp, "c1_spelling_fails")
    env = fx.env(NOW_S)
    fx.running(env)
    real_spellings = TOOL.clone_spellings

    def unspellable(clone):
        raise ValueError("a --clone Windows cannot spell (fake)")
    TOOL.clone_spellings = unspellable
    try:
        code, out = cli(env, "status", *fx.args)
    except BaseException as e:  # noqa: BLE001 - it escaped the tool: a FAIL line, not a dead gate
        code, out = f"escaped: {type(e).__name__}", ""
    finally:
        TOOL.clone_spellings = real_spellings
    check("C1 FAULT a --clone whose spellings cannot be worked out is an INTERNAL ERROR (50) that says why, never a "
          "traceback escaping the tool", code == 50 and "INTERNAL ERROR" in out and "cannot spell" in out,
          f"code {code}")
    fx = Fixture(tmp, "c1_ok")
    env = fx.env(NOW0)
    fx.running(env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("C1 CONTROL the same run WITH the marker at the literal ai-agent/DEPLOYMENT proceeds (PENDING, 11)",
          code == 11 and (fx.clone / "ai-agent" / "DEPLOYMENT").exists(), out[-300:])
    fx = Fixture(tmp, "c1_status", deployment=False)
    env = fx.env(NOW_S)
    fx.running(env)
    snap = snapshot(fx.root)
    code, out = cli(env, "status", *fx.args)
    check("C1 status on such a clone WARNS that --apply refuses it, and writes nothing",
          "no ai-agent/DEPLOYMENT" in out and snapshot(fx.root) == snap and not fx.ops.exists(), out[-300:])


class BrokenOut(io.TextIOBase):
    """A console that went away: every write raises."""

    def write(self, s):
        raise OSError(22, "the console went away (fake)")

    def flush(self):
        raise OSError(22, "the console went away (fake)")


def t_l1(tmp: Path) -> None:
    def held(name, holder: dict | str, alive: set, procs: list, age_s: float = 0.0, stop=False):
        fx = Fixture(tmp, name)
        env = fx.env(NOW0)
        fx.running(env)
        if stop:
            fx.place_stop()
        env.alive |= alive
        env.procs += procs
        write(fx.tool_lock, holder if isinstance(holder, str) else json.dumps(holder))
        if age_s:
            os.utime(fx.tool_lock, (time.time() - age_s, time.time() - age_s))
        return fx, env

    live_tool = {"ProcessId": 7777, "ParentProcessId": 1, "Name": "py.exe",
                 "CommandLine": '"C:\\Windows\\py.exe" -3.12 tools/ops/park_tuner.py park --apply'}
    for argv in (["park", "--apply", "--no-wait"], ["resume", "--apply"]):
        fx, env = held(f"l1_live_{argv[0]}", {"pid": 7777, "since": "x", "command": "park --apply",
                                              "phase": "starting"}, {7777}, [live_tool])
        lock_before = fx.tool_lock.read_bytes()
        code, out = cli(env, *argv, *fx.args)
        check(f"L1 FAULT {' '.join(argv)} while another park --apply that is NOT waiting holds the lock (a live "
              "park_tuner PID): REFUSED (50), the lock untouched, no STOP change, no changing call",
              code == 50 and "another --apply holds the park tool's lock" in out
              and fx.tool_lock.read_bytes() == lock_before and not fx.stop.exists() and not env.changes(), out[:300])
    resume_tool = {"ProcessId": 7778, "ParentProcessId": 1, "Name": "py.exe",
                   "CommandLine": '"C:\\Windows\\py.exe" -3.12 tools/ops/park_tuner.py resume --apply'}
    fx, env = held("l1_live_resume_holder", {"pid": 7778, "since": "x", "command": "resume --apply",
                                             "phase": "starting"}, {7778}, [resume_tool])
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("L1 FAULT a live RESUME --apply holds the lock: park --apply is REFUSED (50) and told to wait for it, STOP "
          "not placed (sweep S26)", code == 50 and "wait for it to finish" in out and not fx.stop.exists()
          and not env.changes(), out[:300])
    fx, env = held("l1_live_phaseless", {"pid": 7777, "since": "x", "command": "park --apply"}, {7777}, [live_tool],
                   stop=True)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT a live park --apply whose lock names NO phase (an older tool) is NOT cancelled: REFUSED (50), STOP "
          "kept, and the refusal says it does not know what that run is doing (never 'it has just started')",
          code == 50 and fx.stop.exists() and "does not say what it is doing" in out and "just started" not in out,
          out[:400])
    fx, env = held("l1_young", "garbage", set(), [])
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("L1 FAULT an unreadable lock under a minute old (a run writing it) is REFUSED", code == 50, out[:300])
    chrome = {"ProcessId": 7779, "ParentProcessId": 1, "Name": "chrome.exe", "CommandLine": "chrome.exe --type=gpu"}
    for name, holder, alive, procs, age, why in (
            ("l1_dead", {"pid": 7780}, set(), [], 0.0, "its PID 7780 is not running"),
            ("l1_reused", {"pid": 7779}, {7779}, [chrome], 0.0, "now belongs to chrome.exe"),
            ("l1_old", "garbage", set(), [], 120.0, "names no readable PID")):
        fx, env = held(name, holder, alive, procs, age)
        code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
        logged = fx.tool_log.read_text(encoding="utf-8") if fx.tool_log.exists() else ""
        check(f"L1 CONTROL a stale lock ({why}) is REPLACED and that is logged; the run proceeds (11); no lock is left",
              code == 11 and "stale park tool lock was replaced" in logged and why in logged
              and not fx.tool_lock.exists(), out[-400:])
    fx = Fixture(tmp, "l1_unlisted")
    env = fx.env(NOW0)
    env.alive = {7781}  # OpenProcess says it is alive, but the process table does not list it (yet)
    write(fx.tool_lock, json.dumps({"pid": 7781, "since": "x", "command": "park --apply"}))
    check("L1 CONTROL a lock holder that is alive but not (yet) in the process table counts as LIVE, never stale (the "
          "conservative side: sweep S25)", TOOL.tool_lock_stale(fx.paths, env) is None, "")
    # ---- review F1: resume --apply cancels a park --apply that WAITS for the round
    waiting = {"pid": 51200, "since": "2026-10-29 04:00:00 AM", "command": "park --apply", "phase": "waiting",
               "poll": 60}

    def waiting_park(name, ends_after: int | None = 1, phase="waiting", attention=False):
        fx, env = held(name, {**waiting, "phase": phase}, {51200}, [proc("tool_main")], stop=True)
        env.clock = env.start = NOW_S
        if attention:
            write(fx.attention, ATTENTION_TEXT)

        def park_notices(e):  # the waiting park sees STOP gone on its next poll: CANCELLED, lock released, it exits
            if ends_after is not None and not fx.stop.exists() and len(e.sleeps) >= ends_after and fx.tool_lock.exists():
                fx.tool_lock.unlink()
                e.alive.discard(51200)
                e.procs = [p for p in e.procs if p["ProcessId"] != 51200]
                e.mark("park ended")
        env.on_sleep = park_notices
        return fx, env

    fx, env = waiting_park("l1_cancel")
    procs_before = json.dumps([p for p in env.procs if p["ProcessId"] != 51200], sort_keys=True)
    code, out = cli(env, "resume", "--apply", *fx.args)
    rep = latest(fx)
    check("L1 CONTROL (review F1) resume --apply against a park --apply WAITING for the round: STOP deleted (its wait "
          "ends as CANCELLED), the park's lock released, this resume took the lock: PARK CANCELLED (0); the learner "
          "untouched, nothing started or stopped, no lock left", code == 0 and rep.get("verdict") == "PARK CANCELLED"
          and rep.get("cancelled_park") == 51200 and not fx.stop.exists() and not fx.tool_lock.exists()
          and idx(env, "task_start") < 0 and idx(env, "task_stop") < 0 and 0 <= idx(env, "MARK", "park ended")
          and json.dumps([p for p in env.procs if p["ProcessId"] != 51200], sort_keys=True) == procs_before,
          out[-700:])
    fx, env = waiting_park("l1_cancel_parking", phase="parking")
    lock_before = fx.tool_lock.read_bytes()
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT a park --apply PAST its wait (phase 'parking': switching tasks, backing up) is NOT cancelled: "
          "REFUSED (50), STOP kept, its lock untouched, with what to do instead", code == 50 and fx.stop.exists()
          and fx.tool_lock.read_bytes() == lock_before and "past its wait" in out and not env.changes(), out[:400])
    fx, env = waiting_park("l1_cancel_stuck", ends_after=None)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT a waiting park that does NOT end after STOP is deleted: NEEDS PERSON (10) after its poll + 90 s; "
          "its lock is NOT taken over; nothing else changed", code == 10 and not fx.stop.exists()
          and json.loads(fx.tool_lock.read_text(encoding="utf-8")).get("pid") == 51200
          and "did not end within 150 s" in out and not env.changes() and sum(env.sleeps) >= 150, out[-500:])
    fx, env = waiting_park("l1_cancel_attention", attention=True)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT ATTENTION.md while a park waits: NEEDS PERSON (10), the waiting park NOT cancelled (STOP kept, its "
          "lock untouched)", code == 10 and fx.stop.exists() and "the waiting park was NOT cancelled" in out
          and json.loads(fx.tool_lock.read_text(encoding="utf-8")).get("pid") == 51200 and not env.changes(),
          out[-400:])
    fx, env = waiting_park("l1_second_park")
    code, out = cli(env, "park", "--apply", *fx.args)
    check("L1 FAULT a second park --apply while one WAITS is refused (50) and told the real cancel (resume --apply)",
          code == 50 and "to cancel that park instead, run resume --apply" in out and fx.stop.exists(), out[:400])
    fx, env = waiting_park("l1_ending")
    fx.stop.unlink()  # someone already deleted STOP: the waiting park ends as CANCELLED at its next look
    lock_before = fx.tool_lock.read_bytes()
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT a waiting park whose STOP is already gone (it is ending by itself): resume is REFUSED (50) with "
          "'it is ENDING ... run the command again', never the circular 'run resume --apply'; nothing changed",
          code == 50 and "it is ENDING" in out and "to cancel that park instead" not in out
          and fx.tool_lock.read_bytes() == lock_before and not env.changes(), out[:400])
    fx, env = waiting_park("l1_bad_pid")
    write(fx.tool_lock, json.dumps({**waiting, "pid": "x"}))  # a young lock that names no usable PID
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("L1 FAULT a 'waiting' park lock that names no usable PID is never treated as a waiting park: REFUSED (50), "
          "STOP kept (no delete, no wait on a PID that cannot be checked)", code == 50 and fx.stop.exists()
          and not env.changes(), out[:300])
    # ---- the park records its phase in its lock
    fx = Fixture(tmp, "l1_phase")
    env = fx.env(NOW0)
    fx.running(env)
    env.backups = [fx.good_backup()]
    seen = []

    def phase_probe(e):
        seen.append(json.loads(fx.tool_lock.read_text(encoding="utf-8")).get("phase"))
        if e.clock >= STOP_AT and fx.lock.exists():
            fx.stop_cleanly(e, STOP_AT)
    env.on_sleep = phase_probe
    env.backups = [fx.backup(effect=lambda: seen.append(
        "backup:" + json.loads(fx.tool_lock.read_text(encoding="utf-8")).get("phase")))]
    code, out = cli(env, "park", "--apply", *fx.args)
    check("L1 CONTROL the park's lock says 'waiting' while it waits and 'parking' once it switches tasks off and backs "
          "up (a resume cancels only a waiting park)", code == 0 and seen and set(seen[:-1]) == {"waiting"}
          and seen[-1] == "backup:parking", str(seen[-3:]))
    fx = Fixture(tmp, "l1_late_cancel")
    env = fx.env(NOW0)
    fx.running(env)
    env.backups = [fx.good_backup()]
    env.on_sleep = lambda e: fx.stop_cleanly(e, STOP_AT) if e.clock >= STOP_AT and fx.lock.exists() else None
    real_wait = TOOL.park_wait

    def wait_then_cancel(*a, **k):
        code_ = real_wait(*a, **k)
        fx.stop.unlink()  # a resume's cancel lands right after the wait's last look
        return code_
    TOOL.park_wait = wait_then_cancel
    try:
        code, out = cli(env, "park", "--apply", *fx.args)
    finally:
        TOOL.park_wait = real_wait
    check("L1 FAULT (review F1) STOP deleted after the wait's last look, before the tasks: CANCELLED (30), NO task "
          "touched, no backup", code == 30 and not env.changes() and set(enabled(env).values()) == {True}, out[-300:])
    # ---- the lock is released, and the record kept, whatever fails
    fx = Fixture(tmp, "l1_finish_fails")
    env = fx.env(NOW0)
    fx.running(env)
    real_finish = TOOL.finish

    def boom(run, code):
        raise OSError("the console went away (fake)")
    TOOL.finish = boom
    try:
        code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    finally:
        TOOL.finish = real_finish
    check("L1 FAULT the summary itself fails (an OSError while printing): the lock is STILL released, so the next run "
          "is not refused", code == 50 and not fx.tool_lock.exists(), f"code {code}")
    for argv in (["park", "--apply", "--no-wait"], ["resume", "--apply"]):
        fx = Fixture(tmp, f"l1_log_fails_{argv[0]}")
        env = fx.env(NOW0)
        fx.running(env)
        real_append = TOOL.append_line

        def unwritable(path, line):
            raise OSError("the ops folder is not writable (fake)")
        TOOL.append_line = unwritable
        try:
            code, out = cli(env, *argv, *fx.args)
        finally:
            TOOL.append_line = real_append
        check(f"L1 FAULT {argv[0]} --apply cannot write its first log line: an error (50), the lock released, nothing "
              "changed", code == 50 and not fx.tool_lock.exists() and not env.changes()
              and not fx.stop.exists(), f"code {code}")
    fx = Fixture(tmp, "l1_broken_console")
    env = fx.env(NOW0)
    fx.running(env)
    try:
        with redirect_stdout(BrokenOut()):
            code = TOOL.main(["park", "--apply", "--no-wait", *fx.args], env=env)
        crashed = ""
    except BaseException as e:  # noqa: BLE001 - it escaped the tool: a FAIL line, not a dead gate
        code, crashed = None, f"{type(e).__name__}: {e}"
    logged = fx.tool_log.read_text(encoding="utf-8") if fx.tool_log.exists() else ""
    check("L1 FAULT (review F12) a console that went away (every print fails): the run still ends PENDING (11), every "
          "line is in park_tuner.log, the report is written, the lock released",
          code == 11 and not crashed and "park --apply started" in logged and "DONE: PENDING (exit 11)" in logged
          and latest(fx).get("verdict") == "PENDING" and not fx.tool_lock.exists() and fx.stop.exists(),
          f"code {code} {crashed}")


def t_g1(tmp: Path) -> None:
    env = TOOL.RealEnv()
    fake_paths = TOOL.Paths(tmp / "g1clone", tmp / "g1ops")
    name = "Pokebot-PARKTEST-NO-SUCH-TASK"  # a third layer: even an unguarded call would name no real task
    for label, call in (("task_disable", lambda: env.task_disable(name)), ("task_enable", lambda: env.task_enable(name)),
                        ("task_start", lambda: env.task_start(name)), ("task_stop", lambda: env.task_stop(name)),
                        ("run_backup", lambda: env.run_backup(fake_paths))):
        before = len(TRIPWIRE)
        try:
            call()
            got = "no exception"
        except TOOL.SelftestGuardError:
            got = "guard"
        except Exception as e:  # noqa: BLE001
            got = f"{type(e).__name__}: {e}"
        check(f"G1 FAULT RealEnv.{label} under PARK_TUNER_SELFTEST=1 raises SelftestGuardError BEFORE reaching a process "
              "(the tripwire count does not move)", got == "guard" and len(TRIPWIRE) == before, got)
    for label, target in (("the REAL clone's ai-agent/STOP", TOOL.DEFAULT_CLONE / "ai-agent" / "STOP"),
                          ("the REAL ops folder's park log", TOOL.DEFAULT_OPS / "park" / "park_tuner.log")):
        try:
            TOOL.guard_write(target)  # the guard alone: nothing is ever written here
            got = "allowed"
        except TOOL.SelftestGuardError:
            got = "guard"
        check(f"G1 FAULT a write to {label} is refused under the selftest flag", got == "guard", got)
    # every WRITER calls the guard (sweep S28, S29): the real clone and ops folder are pointed at temp STAND-INS, so even
    # a writer that lost its guard writes only there, where this test sees it
    stand_clone, stand_ops = tmp / "g1_standin" / "pokebot-learner", tmp / "g1_standin" / "ops"
    write(stand_clone / "ai-agent" / "DEPLOYMENT", "stand-in\n")
    saved = (TOOL.DEFAULT_CLONE, TOOL.DEFAULT_OPS)
    TOOL.DEFAULT_CLONE, TOOL.DEFAULT_OPS = stand_clone, stand_ops
    try:
        sp = TOOL.Paths(stand_clone, stand_ops)
        genv = FakeEnv(NOW0)
        write(stand_ops / "park" / "mine.lock", json.dumps({"pid": os.getpid()}))
        own_lock = TOOL.Paths(stand_clone, stand_ops)
        own_lock.tool_lock = stand_ops / "park" / "mine.lock"
        stop_kept = stand_clone / "ai-agent" / "STOP_KEEP"
        writers = {
            "place_stop (ai-agent/STOP)": (lambda: TOOL.place_stop(sp, NOW0), lambda: not sp.stop.exists()),
            "write_json (the report)": (lambda: TOOL.write_json(sp.latest, {"x": 1}), lambda: not sp.latest.exists()),
            "append_line (the park log)": (lambda: TOOL.append_line(sp.tool_log, "x"), lambda: not sp.tool_log.exists()),
            "acquire_tool_lock": (lambda: TOOL.acquire_tool_lock(sp, genv, "park --apply"),
                                  lambda: not sp.tool_lock.exists()),
            "release_tool_lock": (lambda: TOOL.release_tool_lock(own_lock), lambda: own_lock.tool_lock.exists()),
        }
        for label, (call, untouched) in writers.items():
            try:
                call()
                got = "no exception"
            except TOOL.SelftestGuardError:
                got = "guard"
            check(f"G1 FAULT {label} on a path under the (stand-in) real clone or ops folder is REFUSED by the guard and "
                  "writes nothing", got == "guard" and untouched(), got)
        write(sp.stop, "a real park's STOP\n")
        try:
            TOOL.remove_stop(sp)
            got = "no exception"
        except TOOL.SelftestGuardError:
            got = "guard"
        check("G1 FAULT remove_stop on the (stand-in) real clone's STOP is REFUSED by the guard: STOP stays (a mis-wired "
              "resume test can never cancel a real park)", got == "guard" and sp.stop.exists(), got)
        del stop_kept
    finally:
        TOOL.DEFAULT_CLONE, TOOL.DEFAULT_OPS = saved
    try:
        TOOL.guard_write(tmp / "g1" / "x")
        ok = True
    except TOOL.SelftestGuardError:
        ok = False
    check("G1 CONTROL a write to a temp path is allowed under the flag", ok, "")
    os.environ.pop(TOOL.SELFTEST_ENV, None)
    try:
        TOOL.guard_action("probe")  # the guard function only: nothing else is called while the flag is off
        ok = True
    except TOOL.SelftestGuardError:
        ok = False
    finally:
        os.environ[TOOL.SELFTEST_ENV] = "1"
    check("G1 CONTROL with the flag OFF the guard lets the real tool act (it is conditional, not a blanket block)",
          ok and os.environ.get(TOOL.SELFTEST_ENV) == "1", "")


NEVER_TEXT = ("Unregister-ScheduledTask", "Register-ScheduledTask", "Stop-Process", "taskkill", "TerminateProcess",
              "Remove-Item", "install_ops_tasks")


def never_findings(source: str) -> list[str]:
    """What the tool's CODE (not its docstrings or comments) must never contain (spec 3.4)."""
    tree = ast.parse(source)
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docs.add(id(first.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in (
                "kill", "terminate", "send_signal"):
            out.append(f"line {node.lineno}: a call to .{node.func.attr}()")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            hits = [w for w in NEVER_TEXT if w.lower() in node.value.lower()]
            if hits:  # one finding per string ("Register-..." is inside "Unregister-...")
                out.append(f"line {node.lineno}: {hits} in a code string")
        if isinstance(node, ast.List) and node.elts and isinstance(node.elts[0], ast.Constant) \
                and node.elts[0].value == "git":
            words = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if "rev-parse" not in words:
                out.append(f"line {node.lineno}: git without rev-parse: {words}")
    return out


BAD_SOURCE = '''
import os
def f(pid):
    os.kill(pid, 0)
def g(c):
    return ["git", "-C", c, "fetch", "--quiet"]
def h(name):
    return f"Unregister-ScheduledTask -TaskName '{name}' -Confirm:$false"
def k(p):
    p.terminate()
'''
GOOD_SOURCE = '''
"""Never os.kill(pid, 0); never Unregister-ScheduledTask, Stop-Process or taskkill; never git fetch."""
import os
# os.kill(pid, 0) would TERMINATE the learner on Windows; Remove-Item is not used either
def f():
    """TerminateProcess and install_ops_tasks.ps1 are mentioned here only."""
    return ["git", "-C", "x", "rev-parse", "--short", "HEAD"]
'''


def t_n1(tmp: Path) -> None:
    real = never_findings(TOOL_PATH.read_text(encoding="utf-8"))
    check("N1 CONTROL the tool's code never kills or terminates, never (un)registers a task, runs no Stop-Process, "
          "taskkill, TerminateProcess, Remove-Item or install_ops_tasks, and its only git is rev-parse", not real,
          str(real))
    bad = never_findings(BAD_SOURCE)
    check("N1 FAULT a synthetic source with os.kill, a .terminate(), git fetch and Unregister-ScheduledTask IS flagged "
          "(4 findings)", len(bad) == 4, str(bad))
    good = never_findings(GOOD_SOURCE)
    check("N1 CONTROL the same words only in a docstring or a comment are NOT flagged", not good, str(good))


def t_p1(tmp: Path) -> None:
    fx = Fixture(tmp, "p1")
    env = fx.env(NOW0)
    fx.running(env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    literal = fx.clone / "ai-agent" / "STOP"
    text = literal.read_text(encoding="utf-8") if literal.exists() else ""
    check("P1 CONTROL STOP placed at the LITERAL ai-agent/STOP (where learner.py reads it; not at the clone root), its "
          "text naming the tool, the time and the resume command (sweep S50)",
          code == 11 and "park_tuner.py" in text and ts(NOW0) in text and "resume --apply" in text
          and not (fx.clone / "STOP").exists(), text or out[-300:])
    fx = Fixture(tmp, "p1_keep")
    env = fx.env(NOW0)
    fx.running(env)
    fx.place_stop(T_STOP, "the user's own STOP\n")
    before = (fx.stop.read_bytes(), fx.stop.stat().st_mtime_ns)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("P1 FAULT a STOP already there is KEPT: the same bytes and time, and the run says so",
          code == 11 and (fx.stop.read_bytes(), fx.stop.stat().st_mtime_ns) == before
          and "kept as it was" in out, out[-300:])
    fx = Fixture(tmp, "p1_race")
    write(fx.stop, "the user's own STOP, written between the check and the write\n")
    res = TOOL.place_stop(fx.paths, NOW0)
    check("P1 FAULT a STOP that appears between the check and the write is KEPT, never overwritten (exclusive create; "
          "sweep S51)", res == "already there" and fx.stop.read_text(encoding="utf-8").startswith("the user's own STOP"),
          res)


def stopped_base(tmp: Path, name: str, **fixture_kw):
    fx = Fixture(tmp, name, **fixture_kw)
    env = fx.env(NOW0)
    fx.running(env)
    fx.place_stop(NOW0)
    base = {"tag": "ai0054", "pid": 5372, "stop_mtime": NOW0}
    fx.stop_cleanly(env, STOP_AT)
    return fx, env, base


def t_p2(tmp: Path) -> None:
    fx, env, base = stopped_base(tmp, "p2_control")
    check("P2 CONTROL the stopped fixture is stopped_clean", TOOL.check(fx.paths, env, base)["stopped_clean"], "")
    other_learner = {"ProcessId": 6000, "ParentProcessId": 1, "Name": "python.exe", "CommandLine": PY + " learner.py once"}
    faults = {
        "a LIVE learner holds agent.lock again (another PID)": lambda fx, env: (
            write(fx.lock, "6000"), env.procs.append(dict(other_learner)), env.alive.add(6000)),
        "agent.lock exists but names no readable PID (being written)": lambda fx, env: write(fx.lock, ""),
        "the learner PID still a learner": lambda fx, env: (env.procs.append(proc("learner", fx.clone)),
                                                             env.alive.add(5372)),
        "the base learner PID alive under a command line the matcher misses ('learner.py once')": lambda fx, env: (
            env.procs.append({"ProcessId": 5372, "ParentProcessId": 1, "Name": "python.exe",
                              "CommandLine": PY + " learner.py once"}), env.alive.add(5372)),
        "a lane process left": lambda fx, env: env.procs.append(lanes(fx.clone, 1)[0]),
        "the batch process left": lambda fx, env: env.procs.append(proc("batch", fx.clone)),
        "state.json current still the round": lambda fx, env: write(fx.state, json.dumps(
            {**json.loads(fx.state.read_text(encoding="utf-8")), "current": {"tag": "ai0054"}})),
        "the tag missing from state.json cycles": lambda fx, env: write(fx.state, json.dumps(
            {**json.loads(fx.state.read_text(encoding="utf-8")), "cycles": [{"tag": "ai0053"}]})),
        "cycles.jsonl's last row another tag": lambda fx, env: append(
            fx.cycles, json.dumps({"source": "cycle", "tag": "ai0055", "runs": 4}) + "\n"),
        "runs.jsonl one row short of the cycle's runs": lambda fx, env: write(fx.runs, jl(fx.rows[:-1])),
        "runs.jsonl one row MORE than the cycle's runs (a duplicate)": lambda fx, env: append(
            fx.runs, json.dumps({"source": "ai0054", "batch": "dup", "lane": 9, "log": "x"}) + "\n"),
        "state.json unreadable": lambda fx, env: write(fx.state, "{not json"),
        "the STOP file removed": lambda fx, env: fx.stop.unlink(),
        "only an OLD STOP line (from before STOP was placed)": lambda fx, env: write(
            fx.log, f"[{ts(T_OLD)}] {STOP_LINE_TEXT}\n"),
        "no STOP line, only an ATTENTION.md OLDER than STOP": lambda fx, env: (
            write(fx.log, f"[{ts(T_OLD)}] {STOP_LINE_TEXT}\n"), write(fx.attention, ATTENTION_TEXT),
            set_mtime(fx.attention, NOW0 - timedelta(days=3))),
    }
    for i, (name, breaker) in enumerate(faults.items()):
        fx, env, base = stopped_base(tmp, f"p2f{i}")
        breaker(fx, env)
        r = TOOL.check(fx.paths, env, base)
        check(f"P2 FAULT {name}: not stopped_clean", not r["stopped_clean"], TOOL.summary(r))
    fx, env, base = stopped_base(tmp, "p2_deadlock")
    write(fx.lock, "5372")  # the learner's PID, dead: a hard kill after its STOP line left the lock behind
    r = TOOL.check(fx.paths, env, base)
    check("P2 CONTROL (review F4) a lock naming a DEAD PID is a crash leftover: it does not block the clean stop",
          r["stopped_clean"] and TOOL.lock_word(r) == "dead-pid", TOOL.summary(r))
    fx, env, base = stopped_base(tmp, "p2_reuse")
    env.procs.append({"ProcessId": 5372, "ParentProcessId": 1, "Name": "chrome.exe", "CommandLine": "chrome.exe"})
    env.alive.add(5372)
    check("P2 CONTROL a reused PID (not learner.py) does not count as the learner",
          TOOL.check(fx.paths, env, base)["stopped_clean"], "")
    fx, env, base = stopped_base(tmp, "p2_noround")
    base = {**base, "tag": None}  # a wait that began with no round running (and none adopted)
    ok_readable = TOOL.check(fx.paths, env, base)["stopped_clean"]
    write(fx.state, "{not json")
    r = TOOL.check(fx.paths, env, base)
    check("P2 a wait that began with NO round: CONTROL state.json readable with `current` empty -> stopped_clean; FAULT "
          "state.json unreadable -> NOT recorded, not stopped_clean", ok_readable and not r["stopped_clean"],
          TOOL.summary(r))
    log = tmp / "p2_same_second.log"
    floor = datetime(2026, 10, 29, 16, 30, 19)
    write(log, f"[2026-10-29 04:30:19 PM] {STOP_LINE_TEXT}\n")
    check("P2 CONTROL a STOP line logged in the floor's OWN second (STOP placed at 4:30:19.4 PM) counts (sweep S01)",
          TOOL.last_stop_line(log, floor) == "2026-10-29 04:30:19 PM", "")

    def e2e(name, hook, *extra, between=False, start=NOW0):
        fx = Fixture(tmp, name, between_rounds=between)
        env = fx.env(start)
        fx.running(env)
        env.backups = [fx.good_backup(), fx.good_backup()]
        env.on_sleep = hook(fx)
        code, out = cli(env, "park", "--apply", *extra, *fx.args)
        return fx, env, code, out

    def clean(fx):
        return lambda e: fx.stop_cleanly(e, STOP_AT) if e.clock >= STOP_AT and fx.lock.exists() else None
    fx, env, code, out = e2e("p2_e2e_clean", clean)
    check("P2 CONTROL end to end: the clean stop at 4:31 AM parks (0): all three OFF, the backup verified, not before; "
          "the PARKED line says the tuner stopped after round ai0054, which is recorded (review F5)",
          code == 0 and set(enabled(env).values()) == {False} and latest(fx).get("backup", {}).get("verified")
          and env.clock >= STOP_AT and "PARKED: the tuner stopped after round ai0054, which is recorded" in out,
          out[-500:])

    def flap(fx):
        st = {"phase": 0}

        def hook(e):
            if e.clock >= STOP_AT and st["phase"] == 0:
                fx.stop_cleanly(e, STOP_AT)
                st["phase"] = 1
            elif st["phase"] == 1:  # a learner took the lock again right after the first good look
                write(fx.lock, "6000")
                e.procs.append(dict(other_learner))
                e.alive.add(6000)
                st["phase"] = 2
            elif st["phase"] == 2:
                fx.lock.unlink()
                e.procs = [p for p in e.procs if p["ProcessId"] != 6000]
                e.alive.discard(6000)
                st["phase"] = 3
        return hook
    fx, env, code, out = e2e("p2_flap", flap)
    good = [ln for ln in out.splitlines() if "stopped and recorded, look" in ln]
    check("P2 FAULT a learner lock that returns between looks resets the count: 3 good looks (look 1 of 2 twice), then 0",
          code == 0 and len(good) == 3 and sum("look 1 of 2" in g for g in good) == 2, f"{code} {len(good)}")

    def assert_untouched(label, fx, env, code, want, stop_should_exist=True):
        check(f"P2 FAULT {label}: exit {want}, NO task touched and no backup run"
              + (", STOP still in place" if stop_should_exist else ""),
              code == want and not env.changes() and set(enabled(env).values()) == {True}
              and fx.stop.exists() == stop_should_exist, f"code {code} changes {env.changes()}")

    fx, env, code, out = e2e("p2_noline", lambda fx: lambda e: fx.stop_cleanly(e, STOP_AT, stop_line=False)
                             if e.clock >= STOP_AT and fx.lock.exists() else None)
    assert_untouched("no fresh STOP line (only the old one) -> UNEXPECTED", fx, env, code, 40)

    def died(fx):
        def hook(e):
            if e.clock >= STOP_AT and fx.lock.exists():
                fx.lock.unlink()
                e.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]
                e.alive = {10588, 32140}
        return hook
    fx, env, code, out = e2e("p2_died", died)
    assert_untouched("the round NOT recorded (the learner died, its batch ended) -> UNEXPECTED", fx, env, code, 40)
    kill_at, batch_end = datetime(2026, 10, 29, 4, 10, 0), datetime(2026, 10, 29, 4, 31, 0)

    def hard_kill(fx):
        st = {"phase": 0}

        def hook(e):  # the window is closed at 4:10: run_agent, the launcher and the learner die, agent.lock STAYS
            if st["phase"] == 0 and e.clock >= kill_at:
                gone = {10588, 32140, 42712, 5372}
                e.procs = [p for p in e.procs if p["ProcessId"] not in gone]
                e.alive -= gone
                e.tasks[A]["state"] = "Ready"
                st["phase"] = 1
            elif st["phase"] == 1 and e.clock >= batch_end:  # the batch and lanes end at the round's end, unrecorded
                e.procs = [p for p in e.procs if "x4_headless" not in p["CommandLine"]
                           and "sandbox-pokebot" not in p["CommandLine"]]
                e.alive = {p["ProcessId"] for p in e.procs}
                st["phase"] = 2
        return hook
    fx, env, code, out = e2e("p2_hard_kill", hard_kill)
    assert_untouched("(review F4) a HARD KILL that leaves agent.lock naming the dead PID, the round unrecorded -> "
                     "UNEXPECTED (40), not a TIMEOUT that says 'still running'", fx, env, code, 40)
    batch_end2 = STOP_AT + timedelta(minutes=10)

    def orphan(fx):
        def hook(e):
            if e.clock >= STOP_AT and fx.lock.exists():  # the learner dies; its batch and lanes run on
                fx.lock.unlink()
                e.procs = [p for p in e.procs if "learner.py" not in p["CommandLine"]]
            elif e.clock >= batch_end2 and any("sandbox-pokebot" in p["CommandLine"] for p in e.procs):
                e.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]  # the batch ends, nothing recorded
                e.alive = {10588, 32140}
                e.mark("batch ended")
        return hook
    fx, env, code, out = e2e("p2_orphan", orphan)
    check("P2 FAULT the learner dies but its batch runs on for 10 minutes: no UNEXPECTED while the lanes still run; "
          "UNEXPECTED (40) only after three looks at nothing running, nothing touched",
          code == 40 and env.clock >= batch_end2 + timedelta(seconds=120) and not env.changes()
          and 0 <= idx(env, "MARK", "batch ended"), f"code {code} at {ts(env.clock)}")
    fx, env, code, out = e2e("p2_cancel", lambda fx: lambda e: fx.stop.unlink()
                             if len(e.sleeps) == 3 and fx.stop.exists() else None)
    assert_untouched("STOP removed while waiting -> CANCELLED", fx, env, code, 30, stop_should_exist=False)
    fx, env, code, out = e2e("p2_timeout", lambda fx: lambda e: None, "--deadline", ts(NOW0 + timedelta(minutes=10)))
    assert_untouched("still running at the deadline -> TIMEOUT", fx, env, code, 20)
    check("P2 the TIMEOUT of a tuner that still runs SAYS it still runs, in its verdict line AND its logged reason "
          "(worded from the last look)", "TIMEOUT: the tuner was still running at the deadline" in out
          and "wait: the tuner was still running at the deadline" in out, verdict_line(out))
    fx, env, code, out = e2e("p2_timeout_idle", died, "--deadline", "2026-10-29 04:32:30 AM")
    check("P2 FAULT (review F4) nothing runs at the deadline but the stop was not clean: TIMEOUT (20) worded from the "
          "last look ('nothing of the tuner runs at the deadline') in its verdict line AND its logged reason, NEVER "
          "'still running'; nothing touched", code == 20 and "TIMEOUT: nothing of the tuner runs at the deadline" in out
          and "still running" not in verdict_line(out) and "wait: nothing of the tuner runs at the deadline" in out
          and "wait: the tuner was still running at the deadline" not in out and not env.changes(), verdict_line(out))
    fx = Fixture(tmp, "p2_comes_back", between_rounds=True)
    env = fx.env(NOW0)
    fx.running(env)
    env.procs = [p for p in env.procs if "x4_headless" not in p["CommandLine"]
                 and "sandbox-pokebot" not in p["CommandLine"]]  # idle between rounds: no batch
    env.alive = {p["ProcessId"] for p in env.procs}
    env.backups = [fx.good_backup()]
    back = {"phase": 0}

    def comes_back(e):
        if back["phase"] == 0:  # it obeys STOP silently between rounds: a first GOOD look follows
            fx.lock.unlink()
            e.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]
            e.alive = {10588, 32140}
            back["phase"] = 1
        elif back["phase"] == 1:  # ... then a learner comes back under the SAME PID, holding its lock (a hand start)
            e.procs.append(proc("learner", fx.clone))
            e.alive.add(5372)
            write(fx.lock, "5372")
            back["phase"] = 2
    env.on_sleep = comes_back
    given = NOW0 + timedelta(minutes=5)
    code, out = cli(env, "park", "--apply", "--deadline", ts(given), *fx.args)
    check("P2 FAULT (review F11) after a FIRST good look a learner comes back holding its lock under the same PID: that "
          "look is not a good one, so the count resets, and the deadline still ends the wait: TIMEOUT (20) at it, never "
          "an endless wait; nothing touched", code == 20 and given <= env.clock < given + timedelta(minutes=2)
          and not env.changes() and "look 1 of 2" in out, f"code {code} at {ts(env.clock)}")
    fx, env, code, out = e2e("p2_confirm", clean, "--deadline", "2026-10-29 04:32:30 AM")
    check("P2 CONTROL (review F11) a clean stop whose FIRST good look (4:32:00 AM) comes just before the deadline "
          "(4:32:30 AM) gets its confirming look: PARKED (0), not TIMEOUT", code == 0
          and set(enabled(env).values()) == {False}, verdict_line(out) or out[-300:])

    def restart_into_new_code(fx):  # exit 3 at the boundary: the round recorded, the restart line, no STOP line
        def hook(e):
            if e.clock >= STOP_AT and fx.lock.exists():
                fx.stop_cleanly(e, STOP_AT, stop_line=False)
                append(fx.log, f"[{ts(STOP_AT)}] code changed (9aae60451ad1 -> 85e3e9eb57b1) and test_agent.py passes: "
                               "restarting into it\n")
        return hook
    fx, env, code, out = e2e("p2_restart", restart_into_new_code)
    check("P2 CONTROL (review F9) the learner's restart into new code at the boundary (exit 3; run_agent.ps1 then finds "
          "STOP and stops) is a clean stop: the round recorded, no STOP line needed -> PARKED (0)",
          code == 0 and set(enabled(env).values()) == {False}, verdict_line(out) or out[-300:])
    exit_at = NOW0 + timedelta(minutes=2)

    def idle_exit(crash: bool):
        def make(fx):
            def hook(e):  # sleep_unless_stopped sees STOP and returns 0 WITHOUT a STOP line (or it crashes)
                if e.clock >= exit_at and fx.lock.exists():
                    if crash:
                        append(fx.log, f"[{ts(e.clock)}] learner CRASHED (1 of 5 in a row):\nTraceback (fake)\n")
                    fx.lock.unlink()
                    e.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]
                    e.alive = {10588, 32140}
            return hook
        return make

    def between(name, crash):
        fx = Fixture(tmp, name, between_rounds=True)
        env = fx.env(NOW0)
        fx.running(env)
        env.procs = [p for p in env.procs if "x4_headless" not in p["CommandLine"]
                     and "sandbox-pokebot" not in p["CommandLine"]]  # idle between rounds: no batch
        env.alive = {p["ProcessId"] for p in env.procs}
        env.backups = [fx.good_backup()]
        env.on_sleep = idle_exit(crash)(fx)
        code, out = cli(env, "park", "--apply", *fx.args)
        return fx, env, code, out
    fx, env, code, out = between("p2_quiet", crash=False)
    check("P2 CONTROL (review F9) a park begun BETWEEN rounds: the idle learner obeys STOP silently (no STOP line) -> "
          "PARKED (0), its line saying it stopped between rounds", code == 0
          and "PARKED: the tuner stopped between rounds" in out, verdict_line(out) or out[-300:])
    fx, env, code, out = between("p2_quiet_crash", crash=True)
    assert_untouched("(review F9) between rounds the learner CRASHES instead (a crash line since STOP) -> UNEXPECTED",
                     fx, env, code, 40)
    fx = Fixture(tmp, "p2_reentry")
    env = fx.env(NOW0)
    fx.running(env)
    fx.place_stop(NOW0 - timedelta(minutes=20))  # STOP from an earlier park --apply (it ended TIMEOUT)
    line_at = NOW0 - timedelta(seconds=5)  # the learner already logged its STOP line and is shutting down
    append(fx.log, f"[{ts(line_at)}] {STOP_LINE_TEXT}\n")
    env.on_sleep = lambda e: fx.stop_cleanly(e, line_at, stop_line=False) if fx.lock.exists() else None
    env.backups = [fx.good_backup()]
    code, out = cli(env, "park", "--apply", *fx.args)
    check("P2 CONTROL a re-run over a STOP that was already there counts the learner's STOP line from STOP's OWN time "
          "(it logged it 5 s before this run): PARKED (0), not UNEXPECTED (sweep S36)", code == 0,
          verdict_line(out) or out[-300:])

    def attention(fx):
        def hook(e):
            if e.clock >= STOP_AT and fx.lock.exists():
                fx.stop_cleanly(e, STOP_AT, stop_line=False)
                write(fx.attention, ATTENTION_TEXT)
                set_mtime(fx.attention, STOP_AT)
        return hook
    fx, env, code, out = e2e("p2_attention", attention)
    rep = latest(fx)
    check("P2 an ATTENTION exit (no STOP line) is a stop: parked with its REASON for a person (10), all three OFF",
          code == 10 and any("3 cycles in a row" in m for m in rep.get("needs_person", []))
          and set(enabled(env).values()) == {False}, json.dumps(rep.get("needs_person")))

    adopt_end = NOW0 + timedelta(minutes=5) + timedelta(minutes=720)

    def adopted(rows_short: bool):
        def make(fx):
            st = {"phase": 0}

            def hook(e):
                if st["phase"] == 0 and e.clock >= NOW0 + timedelta(minutes=5):  # the round starts after the wait began
                    s = json.loads(fx.state.read_text(encoding="utf-8"))
                    s["current"] = {"tag": "ai0055", "started": ts(e.clock), "lanes": 12, "minutes": 720.0}
                    write(fx.state, json.dumps(s))
                    append(fx.log, f"[{ts(e.clock)}] ai0055: starting 12 lanes for 720 minutes\n")
                    st["phase"] = 1
                elif st["phase"] == 1 and e.clock >= adopt_end:
                    fx.stop_cleanly(e, e.clock, tag="ai0055", runs=4, rows=3 if rows_short else 4)
                    st["phase"] = 2
            return hook
        return make
    fx, env, code, out = e2e("p2_adopt", adopted(False), between=True)
    check("P2 CONTROL a round that starts AFTER the wait began is adopted, its default deadline moves with it, and it "
          "parks after the round (0), not at a 90-minute TIMEOUT",
          code == 0 and env.clock >= adopt_end and "round ai0055 started after the wait began" in out
          and "the deadline moves to" in out, out[-600:])
    fx, env, code, out = e2e("p2_adopt_short", adopted(True), between=True)
    check("P2 FAULT the adopted round ends with runs.jsonl one row short: UNEXPECTED (40), nothing touched",
          code == 40 and not env.changes(), f"code {code}")

    def ctrl_c(fx):
        def hook(e):
            raise KeyboardInterrupt
        return hook
    try:
        fx, env, code, out = e2e("p2_ctrlc", ctrl_c)
    except KeyboardInterrupt:  # it escaped the tool: a FAIL line, not a dead gate
        fx, env, code, out = Fixture(tmp, "p2_ctrlc_escaped"), FakeEnv(NOW0), "KeyboardInterrupt escaped", ""
    rep = latest(fx)
    check("P2 FAULT Ctrl+C during the wait: exit 50 with an INTERRUPTED report, the lock released, STOP still in place, "
          "no task touched", code == 50 and rep.get("verdict") == "INTERRUPTED" and not fx.tool_lock.exists()
          and fx.stop.exists() and not env.changes(), f"code {code} {rep.get('verdict')}")


def t_p3(tmp: Path) -> None:
    fx = Fixture(tmp, "p3_order")
    env = fx.env(NOW0)
    fx.running(env)
    env.backups = [fx.good_backup()]
    env.on_sleep = lambda e: fx.stop_cleanly(e, STOP_AT) if e.clock >= STOP_AT and fx.lock.exists() else None
    code, out = cli(env, "park", "--apply", *fx.args)
    i_stop, i_dis = idx(env, "MARK", "stopped"), idx(env, "task_disable")
    i_bk, i_bdis = idx(env, "run_backup"), idx(env, "task_disable", B)
    first_dis_clock = env.events[i_dis][2] if i_dis >= 0 else None
    check("P3 CONTROL no task is switched off before the verified stop (the stop, then two looks a poll apart), and the "
          "nightly backup task only after the verified backup",
          code == 0 and 0 <= i_stop < i_dis and first_dis_clock >= STOP_AT + timedelta(seconds=60)
          and 0 <= i_bk < i_bdis, f"code {code} stop {i_stop} disable {i_dis} backup {i_bk} backup-off {i_bdis}")
    order = [n + (f" {a[0]}" if a else "") for (n, a, _c) in env.events if n in ("task_disable", "run_backup")]
    check("P3 CONTROL the order of the changing calls is the spec's: Disable autostart, Disable watchdog, the final "
          "backup, Disable backup (sweep S05)",
          order == [f"task_disable {A}", f"task_disable {W}", "run_backup", f"task_disable {B}"], str(order))
    reports = sorted(fx.park_dir.glob("report-*.json"))
    printed = [ln.strip()[len("report: "):] for ln in out.splitlines() if ln.strip().startswith("report: ")]
    check("P3 CONTROL exactly ONE dated report-YYYYMMDD-HHMMSS.json is written, and the path the summary prints exists "
          "(sweep S52)", len(reports) == 1 and printed and Path(printed[-1]).exists(), f"{reports} {printed}")

    def stopped_run(name, backups, tweak=None):
        fx = Fixture(tmp, name)
        env = fx.env(NOW_R)
        fx.make_stopped(env)
        env.backups = list(backups) if not callable(backups) else backups(fx, env)
        if tweak:
            tweak(fx, env)
        code, out = cli(env, "park", "--apply", *fx.args)
        return fx, env, code, out

    stale_same_day = ts(NOW_R + timedelta(seconds=60) - timedelta(hours=3))
    for i, (label, make) in enumerate((
            ("REFUSED, nothing written (exit 2) twice", lambda fx, env: [fx.failed_backup(), fx.failed_backup()]),
            ("exit 1 although its status and zip look fine, twice", lambda fx, env: [fx.backup(rc=1), fx.backup(rc=1)]),
            ("a STALE status (a day old) over a good zip, twice",
             lambda fx, env: [fx.backup(time="2026-10-28 01:00:01 AM"), fx.backup(time="2026-10-28 01:00:01 AM")]),
            ("a status 3 HOURS older than the backup, on the SAME day, over a good zip (sweep S48)",
             lambda fx, env: [fx.backup(time=stale_same_day), fx.backup(time=stale_same_day)]),
            ("a status with ok false over a good zip, twice", lambda fx, env: [fx.backup(ok=False), fx.backup(ok=False)]),
            ("a status with NO ok at all over a good zip (sweep S47)",
             lambda fx, env: [fx.backup(ok_key=False), fx.backup(ok_key=False)]),
            ("a zip whose cycles.jsonl differs, twice",
             lambda fx, env: [fx.backup(tamper="cycles"), fx.backup(tamper="cycles")]),
            ("a zip whose runs.jsonl is 60 bytes short (sweep S45)",
             lambda fx, env: [fx.backup(tamper="runs"), fx.backup(tamper="runs")]),
            ("a zip whose state.json is another document (sweep S46)",
             lambda fx, env: [fx.backup(tamper="state"), fx.backup(tamper="state")]),
            ("a zip WITHOUT ai-agent/data/runs.jsonl (sweep S49)",
             lambda fx, env: [fx.backup(drop="runs"), fx.backup(drop="runs")]),
            ("a CORRUPT zip (sweep S49)", lambda fx, env: [fx.backup(corrupt=True), fx.backup(corrupt=True)]),
            ("a status naming a zip that is GONE (sweep S49)",
             lambda fx, env: [fx.backup(gone=True), fx.backup(gone=True)]))):
        fx, env, code, out = stopped_run(f"p3_bk{i}", make)
        check(f"P3 FAULT the final backup fails ({label}): PARTIAL (10), {B} LEFT ON and its Disable NEVER called; the "
              "other two OFF", code == 10 and env.tasks[B]["enabled"] and idx(env, "task_disable", B) < 0
              and not env.tasks[A]["enabled"] and not env.tasks[W]["enabled"], f"code {code}\n{out[-400:]}")
    fx, env, code, out = stopped_run("p3_stuck", lambda fx, env: [fx.good_backup()],
                                     lambda fx, env: env.tasks[W].__setitem__("stuck", True))
    check("P3 FAULT a task that stays ON after Disable-ScheduledTask: PARTIAL (10), it reads ON, the others OFF",
          code == 10 and env.tasks[W]["enabled"] and not env.tasks[A]["enabled"] and not env.tasks[B]["enabled"]
          and "still enabled after Disable-ScheduledTask" in out, f"code {code}")
    fx, env, code, out = stopped_run("p3_raise", lambda fx, env: [fx.good_backup()],
                                     lambda fx, env: env.tasks[A].__setitem__("fail_disable", True))
    check("P3 FAULT a Disable that raises (Access is denied): PARTIAL (10), reported, the rest still done",
          code == 10 and env.tasks[A]["enabled"] and not env.tasks[W]["enabled"] and not env.tasks[B]["enabled"]
          and "Access is denied" in out, f"code {code}")
    fx, env, code, out = stopped_run("p3_retry", lambda fx, env: [fx.failed_backup(), fx.good_backup()])
    tries = [c for (n, a, c) in env.events if n == "run_backup"]
    check("P3 CONTROL a backup that fails once then passes is retried 120 s later and parks (0)",
          code == 0 and len(tries) == 2 and (tries[1] - tries[0]).total_seconds() == 120
          and not env.tasks[B]["enabled"], f"code {code} {tries}")
    during = {
        "STOP deleted during the backup (sweep S10)": lambda fx, env: fx.stop.unlink(),
        "a learner started during the backup (sweep S11)": lambda fx, env: (
            env.procs.extend([proc("launcher", fx.clone), proc("learner", fx.clone)]), env.alive.update({42712, 5372})),
        "the autostart switched back ON during the backup (sweep S12)": lambda fx, env: env.tasks[A].__setitem__(
            "enabled", True),
    }
    for i, (label, effect) in enumerate(during.items()):
        fx, env, code, out = stopped_run(f"p3_during{i}", lambda fx, env, effect=effect: [
            fx.good_backup(effect=lambda: effect(fx, env))])
        check(f"P3 FAULT {label}: the final look flags it: PARTIAL (10), never PARKED", code == 10
              and latest(fx).get("verdict") == "PARTIAL", verdict_line(out) or out[-300:])
    for label, swap in (("raises PermissionError (access denied; sweep S06)", "deny"),
                        ("reports 'placed' but no file is there (sweep S07)", "phantom")):
        fx = Fixture(tmp, f"p3_stop_{swap}")
        env = fx.env(NOW_R)
        fx.make_stopped(env)
        env.backups = [fx.good_backup()]
        real = TOOL.place_stop

        def denied(paths, at, by="park --apply"):
            raise PermissionError(13, "Access is denied (fake)")
        TOOL.place_stop = denied if swap == "deny" else (lambda paths, at, by="park --apply": "placed")
        try:
            code, out = cli(env, "park", "--apply", *fx.args)
        finally:
            TOOL.place_stop = real
        check(f"P3 FAULT on a STOPPED tuner, placing STOP {label}: ERROR (50), NO changing call (no task, no backup)",
              code == 50 and not env.changes() and not fx.stop.exists(), f"code {code} {env.changes()}")


def t_p4(tmp: Path) -> None:
    cur = {"tag": "ai0054", "started": T_ROUND_TEXT, "lanes": 12, "minutes": 720.0}
    got, _why = TOOL.default_deadline(cur, NOW0)
    check("P4 CONTROL the default deadline is started + minutes + 90: from the literal \"2026-10-28 04:30:19 PM\", "
          "2026-10-29 06:00:19 AM", got == DEFAULT_DEADLINE, str(got))
    got, _why = TOOL.default_deadline(None, NOW0)
    check("P4 no round running: now + 90 minutes", got == NOW0 + timedelta(minutes=90), str(got))
    got, _why = TOOL.default_deadline({"tag": "ai0054", "started": "garbage", "minutes": 720.0}, NOW0)
    check("P4 an unreadable start: now + the round's length + 90", got == NOW0 + timedelta(minutes=810), str(got))
    got, _why = TOOL.default_deadline({"tag": "ai0060", "started": "garbage", "minutes": 60.0}, NOW0)
    check("P4 FAULT an unreadable start of a 60-minute round: now + 60 + 90, not now + 720 + 90 (sweep S20)",
          got == NOW0 + timedelta(minutes=150), str(got))
    fx = Fixture(tmp, "p4_default")
    env = fx.env(NOW0)
    fx.running(env)
    code, out = cli(env, "park", "--apply", *fx.args)
    check("P4 CONTROL end to end (it never stops): TIMEOUT (20) at the first look past 06:00:19 AM; the report's "
          "deadline is exactly that; it says how to wait longer (--deadline)",
          code == 20 and latest(fx).get("deadline") == "2026-10-29 06:00:19 AM"
          and DEFAULT_DEADLINE <= env.clock < DEFAULT_DEADLINE + timedelta(seconds=60)
          and 'park --apply --deadline "YYYY-MM-DD hh:mm:ss AM"' in out, f"{code} {ts(env.clock)}")
    fx = Fixture(tmp, "p4_override")
    env = fx.env(NOW0)
    fx.running(env)
    given = datetime(2026, 10, 29, 4, 20, 0)
    code, out = cli(env, "park", "--apply", "--deadline", "2026-10-29 04:20:00 AM", *fx.args)
    check("P4 FAULT --deadline overrides the default: TIMEOUT at 4:20 AM, long before 6:00 AM",
          code == 20 and latest(fx).get("deadline") == "2026-10-29 04:20:00 AM"
          and given <= env.clock < given + timedelta(seconds=60), f"{code} {ts(env.clock)}")
    fx = Fixture(tmp, "p4_given_adopt", between_rounds=True)
    env = fx.env(NOW0)
    fx.running(env)
    given = NOW0 + timedelta(minutes=30)

    def round_starts(e):
        if e.clock >= NOW0 + timedelta(minutes=5) and json.loads(fx.state.read_text(encoding="utf-8"))["current"] \
                is None:
            s = json.loads(fx.state.read_text(encoding="utf-8"))
            s["current"] = {"tag": "ai0055", "started": ts(e.clock), "lanes": 12, "minutes": 720.0}
            write(fx.state, json.dumps(s))
    env.on_sleep = round_starts
    code, out = cli(env, "park", "--apply", "--deadline", ts(given), *fx.args)
    check("P4 FAULT a round adopted during the wait does NOT move a deadline the user GAVE: TIMEOUT at it (30 minutes), "
          "not 13 hours later", code == 20 and given <= env.clock < given + timedelta(seconds=60)
          and latest(fx).get("deadline") == ts(given) and "the deadline moves" not in out, f"{code} {ts(env.clock)}")


def t_p5(tmp: Path) -> None:
    fx = Fixture(tmp, "p5")
    env = fx.env(NOW0)
    fx.running(env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("P5 CONTROL --no-wait places STOP and returns PENDING (11) with NO task touched and no backup",
          code == 11 and fx.stop.exists() and not env.changes() and set(enabled(env).values()) == {True},
          f"code {code} {env.changes()}")
    fx = Fixture(tmp, "p5_stopped")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    code, out = cli(env, "park", "--apply", "--no-wait", *fx.args)
    check("P5 FAULT --no-wait on a tuner that is NOT running still touches no task (it never quietly finishes a park)",
          code == 11 and not env.changes() and set(enabled(env).values()) == {True}, f"code {code} {env.changes()}")


def t_p6(tmp: Path) -> None:
    fx = Fixture(tmp, "p6")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.backups = [fx.good_backup()]
    code, out = cli(env, "park", "--apply", *fx.args)
    i_dis = idx(env, "task_disable")
    sleeps_before = [a for (n, a, c) in env.events[:i_dis] if n == "sleep"] if i_dis >= 0 else None
    check("P6 CONTROL not running at the start: parked (0) after two looks one poll (60 s) apart, no waiting; the PARKED "
          "line says no round was left unrecorded",
          code == 0 and sleeps_before == [(60.0,)] and "look 2 of 2: nothing of the tuner runs" in out
          and "no round was left unrecorded" in verdict_line(out), f"code {code} sleeps {sleeps_before}")
    fx = Fixture(tmp, "p6_unrecorded")
    env = fx.env(NOW_R)
    fx.running(env)
    fx.lock.unlink()
    env.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]  # it crashed mid-round: current still ai0054
    env.alive = {10588, 32140}
    env.backups = [fx.good_backup()]
    code, out = cli(env, "park", "--apply", *fx.args)
    notes = " ".join(latest(fx).get("notes", []))
    line = verdict_line(out)
    check("P6 FAULT a round left UNRECORDED by a crash is REPORTED, not refused: PARKED (0), the note says the learner "
          "recovers it at its next start, and the PARKED line itself says the round was left UNRECORDED, never that it "
          "is recorded (review F5)", code == 0 and "ai0054 was left UNRECORDED" in notes
          and "recovers it at its next start" in notes and "round ai0054 was left UNRECORDED" in line
          and "recorded;" not in line.replace("UNRECORDED", "") and "its round recorded" not in line, line)
    fx = Fixture(tmp, "p6_appears")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.backups = [fx.good_backup()]
    st = {"phase": 0}

    def appears(e):
        if st["phase"] == 0:  # between the two looks someone starts the learner (under the window)
            e.procs += [proc("launcher", fx.clone), proc("learner", fx.clone)]
            e.alive |= {42712, 5372}
            write(fx.lock, "5372")
            st["phase"] = 1
        elif st["phase"] == 1:  # it sees STOP and exits at once
            append(fx.log, f"[{ts(e.clock)}] {STOP_LINE_TEXT}\n")
            fx.lock.unlink()
            e.procs = [proc("window", fx.clone), proc("conhost", fx.clone)]
            e.alive = {10588, 32140}
            e.mark("stopped")
            st["phase"] = 2
    env.on_sleep = appears
    code, out = cli(env, "park", "--apply", *fx.args)
    check("P6 FAULT a learner appearing between the two looks is WAITED for: no task switched off until it has exited "
          "and its stop is verified; then parked (0)",
          code == 0 and 0 <= idx(env, "MARK", "stopped") < idx(env, "task_disable") and len(env.sleeps) >= 3,
          f"code {code} sleeps {len(env.sleeps)}")


def t_p7(tmp: Path) -> None:
    fx = Fixture(tmp, "p7")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.backups = [fx.good_backup()]
    code1, _o = cli(env, "park", "--apply", *fx.args)
    mark = len(env.calls)
    env.backups = []
    code2, out = cli(env, "park", "--apply", *fx.args)
    check("P7 CONTROL a second park --apply on a PARKED tuner: 0, 'it already was', NO backup and no change",
          code1 == 0 and code2 == 0 and "PARKED (it already was)" in out and not env.changes(mark), f"{code1} {code2}")
    fx = Fixture(tmp, "p7_retry")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.backups = [fx.failed_backup(), fx.failed_backup()]
    code1, _o = cli(env, "park", "--apply", *fx.args)
    mark = len(env.calls)
    env.backups = [fx.good_backup()]
    code2, out = cli(env, "park", "--apply", *fx.args)
    backups = [c for c in env.calls[mark:] if c[0] == "run_backup"]
    disables = [c[1][0] for c in env.changes(mark) if c[0] == "task_disable"]
    check("P7 FAULT after a failed backup (10, the nightly task ON) a re-run retries the backup ONCE and finishes (0), "
          "and disables ONLY the backup task (the two already OFF are left as they are: sweep S34)",
          code1 == 10 and code2 == 0 and len(backups) == 1 and not env.tasks[B]["enabled"] and disables == [B],
          f"{code1} {code2} {disables}")


def resume_parked(tmp: Path, name: str, window_open: bool = True, starts: bool = True, start: datetime = NOW_R):
    fx = Fixture(tmp, name)
    env = fx.env(start)
    fx.make_parked(env, window_open)
    if starts:
        env.on_start = fx.learner_starts()
    return fx, env


def t_r1(tmp: Path) -> None:
    fx, env = resume_parked(tmp, "r1")
    write(fx.clone / "ai-agent" / "findings" / "ATTENTION.md", ATTENTION_TEXT)  # where learner.py writes it (literal)
    before = (fx.attention.read_bytes(), fx.attention.stat().st_mtime_ns)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R1 FAULT ATTENTION.md (at the literal ai-agent/findings/ATTENTION.md): NEEDS PERSON (10) with its REASON "
          "line; nothing changed (no task call, STOP still there); ATTENTION.md bytes and time untouched (sweep S32)",
          code == 10 and "3 cycles in a row produced no scored runs" in out and not env.changes()
          and fx.stop.exists() and (fx.attention.read_bytes(), fx.attention.stat().st_mtime_ns) == before, out[-400:])
    fx, env = resume_parked(tmp, "r1_control")
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R1 CONTROL the same parked fixture WITHOUT ATTENTION.md resumes (0)", code == 0, out[-400:])
    fx = Fixture(tmp, "r1_running")
    env = fx.env(NOW_R)
    fx.running(env)
    write(fx.attention, ATTENTION_TEXT)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R1 FAULT ATTENTION.md while the learner still RUNS (it was written at a boundary): NEEDS PERSON (10), not "
          "'ALREADY RUNNING'; nothing changed (sweep S33)", code == 10 and latest(fx).get("verdict") == "NEEDS PERSON"
          and not env.changes(), out[-300:])


def t_r2(tmp: Path) -> None:
    fx = Fixture(tmp, "r2")
    env = fx.env(NOW_R)
    fx.running(env)
    snap = snapshot(fx.clone)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R2 CONTROL already running: 0 'ALREADY RUNNING', the clone unchanged, no changing call",
          code == 0 and "ALREADY RUNNING" in out and snapshot(fx.clone) == snap and not env.changes(), out[-300:])
    fx = Fixture(tmp, "r2_off")
    env = fx.env(NOW_R)
    fx.running(env)
    env.tasks[W]["enabled"], env.tasks[W]["state"] = False, "Disabled"
    code, out = cli(env, "resume", "--apply", *fx.args)
    line = verdict_line(out)
    check("R2 FAULT running with a task OFF: that task switched ON, nothing started (0); the verdict is TASKS ON, never "
          "'RESUMED: the tuner was started' (review F7)",
          code == 0 and env.changes() == [("task_enable", (W,))] and env.tasks[W]["enabled"]
          and line.startswith("TASKS ON:") and "Nothing was started" in line and "was started and" not in line, line)
    fx = Fixture(tmp, "r2_silent")
    env = fx.env(NOW_R)
    fx.running(env)
    env.tasks[W]["enabled"], env.tasks[W]["state"] = False, "Disabled"
    env.tasks[W]["silent_enable"] = True
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R2 FAULT an Enable-ScheduledTask that returns without error but leaves the task OFF: NEEDS PERSON (10), "
          "never TASKS ON / RESUMED (Settings.Enabled is re-read: sweep S55)",
          code == 10 and not env.tasks[W]["enabled"] and "still disabled after Enable-ScheduledTask" in out, out[-300:])


def t_r3(tmp: Path) -> None:
    fx = Fixture(tmp, "r3")
    env = fx.env(NOW_R)
    fx.running(env)
    fx.place_stop()
    env.tasks[B]["enabled"], env.tasks[B]["state"] = False, "Disabled"
    procs_before = json.dumps(env.procs, sort_keys=True)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 CONTROL PARK PENDING: the park CANCELLED (0): STOP deleted, the OFF task ON, the learner untouched, "
          "nothing started or stopped", code == 0 and "PARK CANCELLED" in out and not fx.stop.exists()
          and env.tasks[B]["enabled"] and json.dumps(env.procs, sort_keys=True) == procs_before
          and idx(env, "task_start") < 0 and idx(env, "task_stop") < 0, out[-400:])
    fx = Fixture(tmp, "r3_orphan")
    env = fx.env(NOW_R)
    fx.running(env)
    fx.place_stop()
    fx.lock.unlink()
    env.procs = [p for p in env.procs if "learner.py" not in p["CommandLine"]]  # the learner died; its batch runs on
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 FAULT (review F2) the learner dead but its batch and lanes running, the window open: NEEDS PERSON (10) "
          "with NOTHING changed: STOP kept (the park stays pending), no task touched, nothing started",
          code == 10 and fx.stop.exists() and not env.changes() and "could NOT be proven idle" in out
          and "learner itself is not running" not in out, out[-400:])
    fx = Fixture(tmp, "r3_stuck_stop")
    env = fx.env(NOW_R)
    fx.running(env)
    fx.place_stop()
    os.chmod(fx.stop, stat.S_IREAD)  # a read-only STOP: Windows refuses to delete it
    try:
        code, out = cli(env, "resume", "--apply", *fx.args)
    finally:
        os.chmod(fx.stop, stat.S_IWRITE | stat.S_IREAD)
    check("R3 FAULT a STOP that cannot be deleted on a RUNNING tuner: NEEDS PERSON (10), never PARK CANCELLED (the "
          "tuner would still stop at its boundary: sweep S56)", code == 10 and fx.stop.exists()
          and latest(fx).get("verdict") == "NEEDS PERSON", out[-300:])

    def boundary(name, when: str):
        """PARK PENDING; the round ends and the learner obeys STOP (its STOP line, the round recorded, exit 0: run_agent
        does not restart it) either just BEFORE the resume ('before') or in the moment of the delete ('during')."""
        fx = Fixture(tmp, name)
        env = fx.env(STOP_AT)
        fx.running(env)
        fx.place_stop(T_STOP, "STOP placed by tools/ops/park_tuner.py (park --apply) at 2026-10-28 05:00:00 PM.\n")
        exited = {"done": False}

        def learner_exits(e):
            if not exited["done"]:
                fx.stop_cleanly(e, e.clock)  # its STOP line at/after STOP's time; the window stays open and idle
                exited["done"] = True
        if when == "before":
            append(fx.log, f"[{ts(STOP_AT)}] {STOP_LINE_TEXT}\n")  # it found STOP and is ending as the resume begins
            env.on_sleep = learner_exits
        else:
            env.on_sleep = lambda e: learner_exits(e) if not fx.stop.exists() else None
        env.on_start = fx.learner_starts()
        code, out = cli(env, "resume", "--apply", *fx.args)
        return fx, env, code, out
    fx, env, code, out = boundary("r3_boundary_before", "before")
    check("R3 CONTROL (review F2) the learner had already found STOP when the cancel came: it is waited for, then started "
          "again the step-4 way (the old window ended under STOP, STOP deleted, started): RESUMED (0), never a NEEDS "
          "PERSON that waits for a restart that never comes", code == 0 and latest(fx).get("verdict") == "RESUMED"
          and env.stop_seen and env.stop_seen[0][0] is True and env.start_seen == [(False, {A: True, W: True, B: True})],
          out[-600:])
    fx, env, code, out = boundary("r3_boundary_during", "during")
    check("R3 CONTROL (review F2) the learner found STOP in the very moment of the delete (its line appears during the "
          "settle): seen, waited for, and started again under a STOP placed for the window: RESUMED (0)",
          code == 0 and latest(fx).get("verdict") == "RESUMED" and env.stop_seen and env.stop_seen[0][0] is True
          and env.start_seen and env.start_seen[0][0] is False, out[-600:])
    fx = Fixture(tmp, "r3_boundary_exiting")
    env = fx.env(STOP_AT)
    fx.running(env)
    fx.place_stop(T_STOP, "STOP placed by tools/ops/park_tuner.py (park --apply) at 2026-10-28 05:00:00 PM.\n")
    phase = {"n": 0}

    def exiting(e):
        if phase["n"] == 0 and not fx.stop.exists():  # the settle after the delete: it HAD found STOP and logged it,
            append(fx.log, f"[{ts(e.clock)}] {STOP_LINE_TEXT}\n")  # but its process is still shutting down
            phase["n"] = 1
        elif phase["n"] == 1:  # gone at the next poll
            fx.stop_cleanly(e, e.clock, stop_line=False)
            phase["n"] = 2
    env.on_sleep = exiting
    env.on_start = fx.learner_starts()
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 CONTROL (review F2) the learner found STOP in the moment of the delete and is STILL EXITING at the next "
          "look (its STOP line logged, its process not yet gone): the look after the settle sees the line, the resume "
          "waits for it and starts it again: RESUMED (0), never PARK CANCELLED (that would leave a learner about to "
          "exit for good)", code == 0 and latest(fx).get("verdict") == "RESUMED" and "PARK CANCELLED" not in out
          and env.start_seen and env.start_seen[0][0] is False, verdict_line(out) or out[-400:])
    fx = Fixture(tmp, "r3_boundary_late")  # the reviewer's probe3 timing: its exit and STOP line show only at the
    env = fx.env(STOP_AT)                  # look AFTER the tasks step (a slow log write)
    fx.running(env)
    fx.place_stop(T_STOP, "STOP placed by tools/ops/park_tuner.py (park --apply) at 2026-10-28 05:00:00 PM.\n")
    seen = {"n": 0}

    def late(e):
        seen["n"] += 1
        if seen["n"] == 2:
            fx.stop_cleanly(e, STOP_AT)
    env.on_processes = late
    env.on_start = fx.learner_starts()
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 CONTROL (review F2, probe3's timing) the learner's exit and its STOP line appear only at the look after the "
          "tasks step: recognised (never 'without a STOP line'), waited for, started again: RESUMED (0)",
          code == 0 and latest(fx).get("verdict") == "RESUMED" and "without a STOP line" not in out
          and env.start_seen and env.start_seen[0][0] is False, out[-600:])
    fx = Fixture(tmp, "r3_never_exits")
    env = fx.env(STOP_AT)
    fx.running(env)
    fx.place_stop(T_STOP, "STOP placed by tools/ops/park_tuner.py (park --apply) at 2026-10-28 05:00:00 PM.\n")
    append(fx.log, f"[{ts(STOP_AT)}] {STOP_LINE_TEXT}\n")  # it found STOP, but its process never goes away
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 FAULT a learner that logged its STOP line but still runs after 5 minutes: NEEDS PERSON (10), nothing "
          "started, STOP kept (the wait is bounded)", code == 10 and idx(env, "task_start") < 0
          and idx(env, "task_stop") < 0 and fx.stop.exists() and "still runs after 5 minutes" in out
          and sum(env.sleeps) >= 300, out[-300:])
    fx, env = resume_parked(tmp, "r3_other_learner")
    env.procs.append({"ProcessId": 47000, "ParentProcessId": 46000, "Name": "python.exe",
                      "CommandLine": PY + " learner.py run --dev"})
    env.alive.add(47000)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R3 CONTROL (review F2, F3) a --dev learner of another checkout running beside a PARKED tuner does not stop "
          "the resume: RESUMED (0)", code == 0 and latest(fx).get("verdict") == "RESUMED", out[-400:])


def t_r4(tmp: Path) -> None:
    fx = Fixture(tmp, "r4_unit")
    env = fx.env(NOW_R)
    fx.make_parked(env)
    base = [proc("window", fx.clone), proc("conhost", fx.clone)]
    ok, why, wins = TOOL.idle_window_proof(fx.paths, env, base)
    check("R4 CONTROL unit: the window with only conhost.exe, no lock, nothing of the tuner -> PROVEN idle",
          ok and [w["ProcessId"] for w in wins] == [10588], str(why))
    stranger = {"ProcessId": 47000, "ParentProcessId": 46000, "Name": "python.exe", "CommandLine": PY + " learner.py run"}
    ok, why, _w = TOOL.idle_window_proof(fx.paths, env, base + [stranger])
    check("R4 CONTROL unit: another checkout's learner (not under this window, no lock of this clone) does not block the "
          "proof (review F3)", ok, str(why))
    child = {"ProcessId": 777, "ParentProcessId": 10588, "Name": "python.exe",
             "CommandLine": 'python.exe -c "import time; time.sleep(30)"'}
    for label, procs, lock_text, lock_pid in (
            ("a live learner of the clone (under its window)",
             base + [proc("launcher", fx.clone), proc("learner", fx.clone)], None, None),
            ("a batch", base + [proc("batch", fx.clone)], None, None),
            ("a lane", base + lanes(fx.clone, 1), None, None),
            ("a lock naming a live PID", base + [{"ProcessId": 4242, "ParentProcessId": 1, "Name": "notepad.exe",
                                                  "CommandLine": "notepad.exe"}], "4242", 4242),
            ("an EMPTY agent.lock (a learner writing it: sweep S14)", base, "", None),
            ("a python child of the window", base + [child], None, None),
            ("no window at all", [], None, None)):
        if lock_text is not None:
            write(fx.lock, lock_text)
        if lock_pid:
            env.alive.add(lock_pid)
        ok, why, _w = TOOL.idle_window_proof(fx.paths, env, procs)
        if lock_text is not None:
            fx.lock.unlink()
        if lock_pid:
            env.alive.discard(lock_pid)
        check(f"R4 FAULT unit: {label} -> NOT proven idle", not ok and why, str(why))

    fx, env = resume_parked(tmp, "r4_ok")
    code, out = cli(env, "resume", "--apply", *fx.args)
    i_stop, i_en, i_start = idx(env, "task_stop"), idx(env, "task_enable"), idx(env, "task_start")
    check("R4 CONTROL end to end on a PARKED tuner: the three tasks switched ON FIRST, still under STOP; then "
          "Stop-ScheduledTask (once), seeing STOP present and the three ON; then STOP deleted, started: RESUMED (0)",
          code == 0 and [c for c in env.calls if c[0] == "task_stop"] == [("task_stop", (A,))]
          and 0 <= i_en < i_stop < i_start and env.stop_seen == [(True, {A: True, W: True, B: True})]
          and not fx.stop.exists() and env.start_seen and env.start_seen[0][0] is False, out[-500:])

    def e2e_fault(name, tweak, label):
        fx, env = resume_parked(tmp, name)
        tweak(fx, env)
        code, out = cli(env, "resume", "--apply", *fx.args)
        check(f"R4 FAULT end to end: {label} -> NEEDS PERSON (10), Stop-ScheduledTask NEVER called, nothing changed "
              "(tasks OFF, STOP in place)", code == 10 and idx(env, "task_stop") < 0 and not env.changes()
              and fx.stop.exists() and set(enabled(env).values()) == {False}, out[-400:])

    def live_lock(fx, env):
        write(fx.lock, "4242")
        env.alive.add(4242)
        env.procs.append({"ProcessId": 4242, "ParentProcessId": 1, "Name": "notepad.exe", "CommandLine": "notepad.exe"})
    e2e_fault("r4_lock", live_lock, "a lock naming a live PID")
    e2e_fault("r4_child", lambda fx, env: (env.procs.append(dict(child)), env.alive.add(777)),
              "a python child of the window")
    for mode, label in (("window_stays", "the window does NOT close after Stop-ScheduledTask (the State leaves Running)"),
                        ("state_stays", "the window is gone but the task's State stays Running (sweep S15)")):
        fx, env = resume_parked(tmp, f"r4_{mode}")
        env.stop_mode = mode
        code, out = cli(env, "resume", "--apply", *fx.args)
        check(f"R4 FAULT end to end: {label} -> NEEDS PERSON (10); no start, STOP in place",
              code == 10 and idx(env, "task_stop") >= 0 and idx(env, "task_start") < 0 and fx.stop.exists(), out[-400:])
    # review F8: NOT parked (no STOP) with the old window open: the window is ended only while STOP exists
    fx = Fixture(tmp, "r4_not_parked")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.on_start = fx.learner_starts()
    stop_text: list[str] = []
    env.on_task_stop = lambda e: stop_text.append(fx.stop.read_text(encoding="utf-8") if fx.stop.exists() else "")
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R4 CONTROL (review F8) NOT parked, the old window open: a STOP is placed for the window's end (its text names "
          "resume --apply and says it is deleted again), Stop-ScheduledTask sees STOP present, STOP is deleted before "
          "the start: RESUMED (0)", code == 0 and env.stop_seen and env.stop_seen[0][0] is True and env.start_seen
          and env.start_seen[0][0] is False and not fx.stop.exists() and "placed for a moment" in out
          and stop_text and "(resume --apply)" in stop_text[0] and "deletes it again" in stop_text[0], out[-600:])
    fx = Fixture(tmp, "r4_not_parked_race")
    env = fx.env(NOW_R)
    fx.make_stopped(env)
    env.on_start = fx.learner_starts()

    def racing_start(e):  # run_agent.ps1 passed its STOP check just before STOP was placed: its learner starts now
        if fx.stop.exists() and not any(p["ProcessId"] == 42712 for p in e.procs):
            e.procs += [proc("launcher", fx.clone), proc("learner", fx.clone)]
            e.alive |= {42712, 5372}
    env.on_sleep = racing_start
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R4 FAULT (review F8) a learner that starts in the moment STOP is placed is seen by the second proof: NEEDS "
          "PERSON (10), Stop-ScheduledTask NEVER called, nothing started; STOP stays (it exits at once)",
          code == 10 and idx(env, "task_stop") < 0 and idx(env, "task_start") < 0 and fx.stop.exists(), out[-400:])
    for label, swap in (("raises PermissionError", "deny"), ("reports 'placed' but no file is there", "phantom")):
        fx = Fixture(tmp, f"r4_window_stop_{swap}")
        env = fx.env(NOW_R)
        fx.make_stopped(env)
        real = TOOL.place_stop

        def denied(paths, at, by="park --apply"):
            raise PermissionError(13, "Access is denied (fake)")
        TOOL.place_stop = denied if swap == "deny" else (lambda paths, at, by="park --apply": "placed")
        try:
            code, out = cli(env, "resume", "--apply", *fx.args)
        finally:
            TOOL.place_stop = real
        check(f"R4 FAULT (review F8) NOT parked, and the STOP for the window's end {label}: NEEDS PERSON (10), "
              "Stop-ScheduledTask NEVER called, nothing changed (no task call, no start)",
              code == 10 and not env.changes() and not fx.stop.exists(), f"code {code} {env.changes()}")
    fx, env = resume_parked(tmp, "r4_stop_raises")

    def stop_fails(name):
        env._rec("task_stop", name)
        raise RuntimeError("Stop-ScheduledTask: Access is denied (fake)")
    env.task_stop = stop_fails
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R4 FAULT Stop-ScheduledTask itself fails: NEEDS PERSON (10) naming that failure; no start, STOP in place",
          code == 10 and "Stop-ScheduledTask Pokebot-AI-Learner-Autostart failed" in out and idx(env, "task_start") < 0
          and fx.stop.exists(), out[-300:])
    fx, env = resume_parked(tmp, "r4_appears_after_stop")

    def new_window_learner(e):  # a logon trigger starts a NEW window and learner as the old window ends
        e.procs += [{"ProcessId": 30000, "ParentProcessId": 3720, "Name": "powershell.exe",
                     "CommandLine": proc("window", fx.clone)["CommandLine"]},
                    {"ProcessId": 30001, "ParentProcessId": 30000, "Name": "py.exe",
                     "CommandLine": SHAPES["launcher"][3]}]
        e.alive |= {30000, 30001}
    env.on_task_stop = new_window_learner
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R4 FAULT (review F8) a tuner process that appears as the old window ends: NEEDS PERSON (10), the start "
          "NEVER called on top of it; STOP stays in place", code == 10 and idx(env, "task_start") < 0
          and fx.stop.exists() and "a tuner process appeared while the old window was being ended" in out, out[-400:])


def t_r5(tmp: Path) -> None:
    fx, env = resume_parked(tmp, "r5_ok", window_open=False)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R5 CONTROL at the start call STOP is absent and the three tasks read ON",
          code == 0 and env.start_seen == [(False, {A: True, W: True, B: True})], str(env.start_seen))
    fx, env = resume_parked(tmp, "r5_enable_fails", window_open=False)
    env.tasks[W]["fail_enable"] = True
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R5 FAULT an Enable that fails: NEEDS PERSON (10), the start NEVER called, and STOP still in place (it is "
          "deleted only after the three read ON)", code == 10 and not env.start_seen and fx.stop.exists(),
          out[-300:])
    fx, env = resume_parked(tmp, "r5_stop_stuck", window_open=False)
    os.chmod(fx.stop, stat.S_IREAD)  # a read-only STOP: Windows refuses to delete it
    try:
        code, out = cli(env, "resume", "--apply", *fx.args)
    finally:
        os.chmod(fx.stop, stat.S_IWRITE | stat.S_IREAD)
    check("R5 FAULT a STOP that cannot be deleted: NEEDS PERSON (10), the start NEVER called",
          code == 10 and not env.start_seen and fx.stop.exists(), out[-300:])
    fx, env = resume_parked(tmp, "r5_flip", window_open=False)
    env.on_enable = lambda e, name: e.tasks[W].__setitem__("enabled", False) if name == B else None
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R5 FAULT a task that flips OFF after it was switched ON: the start NEVER called (re-read just before it)",
          code == 10 and not env.start_seen and "NOT started" in out, out[-300:])
    fx = Fixture(tmp, "r5_unit")
    env = fx.env(NOW_R)
    ok1, _ = TOOL.start_allowed(fx.paths, env)
    fx.place_stop()
    ok2, why2 = TOOL.start_allowed(fx.paths, env)
    fx.stop.unlink()
    env.tasks[B]["enabled"] = False
    ok3, why3 = TOOL.start_allowed(fx.paths, env)
    check("R5 unit start_allowed: CONTROL no STOP and all ON -> allowed; FAULT STOP present, a task OFF -> refused",
          ok1 and not ok2 and "STOP" in why2 and not ok3 and B in why3, f"{why2} | {why3}")


def t_r6(tmp: Path) -> None:
    fx, env = resume_parked(tmp, "r6_old", window_open=False, starts=False)  # the log holds an OLD start line

    def silent_learner(e):  # a learner process and its lock appear, but NO new 'learner started' line is logged
        e.procs.append({"ProcessId": 6000, "ParentProcessId": 20002, "Name": "python.exe",
                        "CommandLine": SHAPES["learner"][3]})
        e.alive.add(6000)
        write(fx.lock, "6000")
    env.on_start = silent_learner
    t0 = env.clock
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 FAULT only an OLD 'learner started' line (from before the resume) and a live learner: the old line does "
          "NOT count: NEEDS PERSON (10) after 180 s; nothing undone (the tasks stay ON, STOP stays deleted)",
          code == 10 and "no start seen within 3 minutes" in out and (env.clock - t0).total_seconds() >= 180
          and set(enabled(env).values()) == {True} and not fx.stop.exists() and idx(env, "task_disable") < 0,
          out[-400:])
    fx, env = resume_parked(tmp, "r6_nothing", window_open=False, starts=False)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 FAULT the start does nothing at all: NEEDS PERSON (10), with the old-window and logon advice",
          code == 10 and "Is the old tuner window still open? Log off and on" in out, out[-400:])
    fx, env = resume_parked(tmp, "r6_dead", window_open=False, starts=False)
    env.on_start = fx.learner_starts(live=False)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 FAULT a new line but agent.lock names a dead PID: NEEDS PERSON (10)", code == 10, out[-300:])
    fx, env = resume_parked(tmp, "r6_ok", window_open=False)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 CONTROL a NEW line, a live learner and the round line: RESUMED (0)",
          code == 0 and "RESUMED" in out and "ai0055: starting 12 lanes for 720 minutes" in out, out[-400:])
    fx, env = resume_parked(tmp, "r6_pm", window_open=False, start=NOW_PM)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 CONTROL a resume at 1:00 PM: its PM 'learner started' and 'starting 12 lanes' lines are read: RESUMED (0) "
          "with the round line (sweep S22, S23)", code == 0 and "round: ai0055: starting 12 lanes for 720 minutes "
          "(logged 2026-10-29 01:00:" in out, out[-400:])
    fx, env = resume_parked(tmp, "r6_noround", window_open=False, starts=False)
    env.on_start = fx.learner_starts(round_line=False)
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 CONTROL a live learner but no round within 10 minutes: RESUMED (0) with a note saying so",
          code == 0 and "no round started within 10 minutes" in out, out[-400:])
    fx, env = resume_parked(tmp, "r6_dies", window_open=False, starts=False)
    env.on_start = fx.learner_starts(round_line=False)

    def dies(e):  # 5 minutes after the start the learner is gone (a crash after 'learner started')
        i = idx(e, "task_start")
        if i >= 0 and e.clock >= e.events[i][2] + timedelta(minutes=5) and 6000 in e.alive:
            e.procs = [q for q in e.procs if q["ProcessId"] != 6000]
            e.alive.discard(6000)
            if fx.lock.exists():
                fx.lock.unlink()
    env.on_sleep = dies
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 FAULT a learner that logs 'learner started' and dies 5 minutes later, before any round: NEEDS PERSON (10), "
          "never RESUMED (sweep S54)", code == 10 and latest(fx).get("verdict") == "NEEDS PERSON", out[-300:])
    fx, env = resume_parked(tmp, "r6_attention", window_open=False, starts=False)
    env.on_start = fx.learner_starts(round_line=False)
    env.on_sleep = lambda e: write(fx.attention, ATTENTION_TEXT) if idx(e, "task_start") >= 0 else None
    code, out = cli(env, "resume", "--apply", *fx.args)
    check("R6 FAULT ATTENTION.md written after the start: NEEDS PERSON (10) with its reason",
          code == 10 and "paused itself after the start" in out, out[-300:])
    fx, env = resume_parked(tmp, "r6_ctrlc", window_open=False, starts=False)
    env.on_start = fx.learner_starts(round_line=False)

    def ctrl_c(e):
        if idx(e, "task_start") >= 0:
            raise KeyboardInterrupt
    env.on_sleep = ctrl_c
    try:
        code, out = cli(env, "resume", "--apply", *fx.args)
    except KeyboardInterrupt:  # it escaped the tool: a FAIL line, not a dead gate
        code, out = "KeyboardInterrupt escaped", ""
    check("R6 FAULT Ctrl+C during the resume's start check: exit 50 with an INTERRUPTED report, the lock released "
          "(sweep S43)", code == 50 and latest(fx).get("verdict") == "INTERRUPTED" and not fx.tool_lock.exists(),
          f"code {code}")
    fx = Fixture(tmp, "r6_replaced_log")
    write(fx.log, "[2026-10-28 04:30:17 PM] an old line\n" * 200)
    offset = TOOL.log_size(fx.paths)
    write(fx.log, "[2026-10-29 09:00:05 AM] learner started (code 0123456789ab)\n")  # REPLACED by a shorter log
    got = TOOL.log_since(fx.paths, offset)
    check("R6 CONTROL a learner.log REPLACED by a shorter one after the offset was taken is read from its start: the new "
          "start line is seen (sweep S17)", bool(TOOL.last_match(TOOL.START_LINE, got)), got[:80])


def main() -> int:
    t_start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="parktuner-selftest-", ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        for test in (t_x, t_m, t_re, t_s, t_d, t_c1, t_l1, t_g1, t_n1, t_p1, t_p2, t_p3, t_p4, t_p5, t_p6, t_p7,
                     t_r1, t_r2, t_r3, t_r4, t_r5, t_r6):
            try:
                test(tmp)
            except Exception as ex:  # noqa: BLE001 - a crash is a FAIL with its reason, never a silent pass
                check(f"{test.__name__[2:].upper()} crashed", False,
                      f"{type(ex).__name__}: {ex}\n{traceback.format_exc()[-1200:]}")
    check("G1 CONTROL the tripwire recorded NOTHING over the whole run: no test reached a real process, PowerShell or "
          "git (RealEnv's own code ran only against canned answers)", not TRIPWIRE, str(TRIPWIRE[:3]))
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        line = ("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:600]}")
        print(line.encode("ascii", "backslashreplace").decode("ascii"))
    took = time.perf_counter() - t_start
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks, {len(bad)} failed, {took:.1f} s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
