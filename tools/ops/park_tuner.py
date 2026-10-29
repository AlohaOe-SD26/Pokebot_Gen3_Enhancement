"""THE PARK TOOL: park or resume the 24/7 bot tuner with ONE command that proves its own result.

USER RULING 50 (`06`, 2026-10-28), the user's words: "I do want the safe pause/park feature in the event that I do want
to safely park/pause working on the program ... I do not want this to be paused/parked anymore until I say otherwise!"
Work item: `03` `#28-trainer-improvements` (10); build spec PARK-TOOL-BUILD-SPEC (2026-10-28), plus its fix round.

⛔ THIS TOOL NEVER PARKS ON ITS OWN, and nothing in the project may run `park --apply` unless the USER asked for a park
(nor `resume --apply` unless the user asked for a resume). Nothing schedules it. `status` and the dry runs (`park` and
`resume` WITHOUT `--apply`) only read, write nothing anywhere, and are always safe.

    py -3.12 tools/ops/park_tuner.py status                    # one screen, the verdict first (read-only)
    py -3.12 tools/ops/park_tuner.py park                      # DRY RUN: the steps a park would take, and when
    py -3.12 tools/ops/park_tuner.py park --apply              # park: it WAITS for the running round to end
    py -3.12 tools/ops/park_tuner.py park --apply --no-wait    # only place STOP; a later park --apply finishes
    py -3.12 tools/ops/park_tuner.py resume                    # DRY RUN
    py -3.12 tools/ops/park_tuner.py resume --apply            # resume, or cancel a pending park (even a waiting one)
  Every command: --clone DIR (default C:/Remote Projects/pokebot-learner) and --ops-dir DIR (default
  %LOCALAPPDATA%/pokebot-ops), both for tests. park: --deadline "YYYY-MM-DD hh:mm:ss AM", --poll SECONDS (default 60).
  ⚠ On a RUNNING tuner, park --apply waits IN THE FOREGROUND until the round ends: up to about 13.5 hours. A session
  whose shell limits a foreground command (10 minutes) must run it DETACHED, or run `park --apply --no-wait` now and
  `park --apply` after the round ends (it then parks in about two minutes). A park --apply that is killed while it
  waits leaves STOP in place (the tuner still stops at its boundary) and no report; the next park --apply continues.

WHAT IT ACTS ON (measured 2026-10-28, read-only; build spec section 2)
- The bot tuner runs from its deployment clone (marker `ai-agent/DEPLOYMENT`). Its data: `ai-agent/data/` (learner.log,
  agent.lock = the learner's PID, state.json, cycles.jsonl, runs.jsonl). `ai-agent/STOP` (git-ignored) is read by
  `learner.py` at the top of its loop: the running round finishes, is scored and recorded, then it logs
  `STOP file found: stopping ...` and exits 0, and `run_agent.ps1` does not restart it. run_agent.ps1 itself checks STOP
  before EVERY learner start, its 10-minute crash wait included. ATTENTION.md (findings/) means the learner paused
  itself. The selftest checks these paths, the time format and the log lines against learner.py's own source.
- Three Windows tasks (`Settings.Enabled` is the truth for ON/OFF): Pokebot-AI-Learner-Autostart (logon; runs
  `powershell.exe -NoExit ... run_agent.ps1`: the -NoExit window stays open after the learner exits, the task then still
  reads State "Running", and Start-ScheduledTask is IGNORED while it is open), Pokebot-Ops-Watchdog (every 30 min,
  read-only), Pokebot-Ops-Backup (1:00 AM; writes %LOCALAPPDATA%/pokebot-ops/backup_status.json).
- WHICH PROCESSES ARE THE TUNER: the clone's batch (`x4_headless.py`) and lanes (`sandbox-pokebot`), named by the clone's
  path (any spelling of --clone: relative, 8.3 or \\\\?\\ is expanded first), and the learner and its py.exe launcher,
  whose command line `learner.py run` holds NO path: those count only when they run under the clone's run_agent.ps1
  window (by ParentProcessId) or hold the clone's agent.lock (or launched its holder). Any other `learner.py run` (a
  --dev learner in another checkout, a test's child, a shell loop that greps for the phrase) is listed by status as not
  this clone's, and blocks nothing.

STATUS: the first line is the verdict, then the details, then "What to do next". Exit code = the verdict:
    0 RUNNING              no STOP, the learner alive, the three tasks ON
   61 PARK PENDING         STOP present and something of the tuner still runs (it stops by itself after its round)
   62 PARKED               STOP present, nothing of the tuner runs, all three tasks OFF
   63 PARTLY PARKED        STOP present, nothing runs, some task still ON (it says which, and what park --apply would do)
   64 STOPPED, NOT PARKED  no STOP and nothing runs (it names the reason: ATTENTION.md's reason line or the log's tail)
   65 INCONSISTENT         anything else (e.g. a task OFF while the tuner runs without STOP): the facts are listed
   50 the facts could not be read (an internal error)
  It also shows the park tool's own lock: a park --apply that is WAITING for the round, or a running resume (then the
  next step is always to let that run finish), and it names a STOP that is resume --apply's own on the first line (a
  resume stopped early: the next step is to finish the resume, never to park).

PARK --apply, each step gated on the one before:
 1. REFUSE, changing and writing nothing, when --clone lacks ai-agent/DEPLOYMENT, --deadline does not parse, or another
    park/resume --apply holds the lock. Already PARKED -> verify, say so, exit 0: no second backup.
 2. Place STOP (a text naming this tool, the time and the resume command) and verify it; a STOP already there is KEPT.
 3. If the tuner RUNS (the lock's PID alive and still a learner, or any batch/lane/learner process of the clone): WAIT
    for the clean stop, as park_watch.watch + check did: the STOP line dated at/after STOP was placed, the learner gone,
    no LIVE learner holding agent.lock (a lock naming a dead PID is a crash leftover), no batch or lane, and the round
    that was running RECORDED in state.json, cycles.jsonl and runs.jsonl, on two looks a poll apart. Two exits that log
    no STOP line count as clean too: the learner's restart into new code (exit 3, after which run_agent.ps1 finds STOP),
    and, for a wait that began with no round running, a silent STOP exit with no crash line since STOP. Default
    deadline: current.started + current.minutes + 90 min (a round that starts after the wait began is adopted, and a
    default deadline moves with it); a first good look gets its confirming look even past the deadline. Removed STOP ->
    CANCELLED (this is how resume --apply cancels a waiting park); the deadline -> TIMEOUT, worded from the last look
    (STOP stays: it still stops at its boundary, and a later park --apply finishes); nothing runs but no clean recorded
    stop on 3 looks -> UNEXPECTED. Each of those changes nothing else. --no-wait returns PENDING right after step 2 and
    touches no task. While it waits, its lock says so (phase "waiting"), and status shows it.
 4. If the tuner did NOT run when the command began: no waiting; two looks a poll apart must show nothing runs (if one
    shows it running, step 3's wait applies). A round left unrecorded by a crash is REPORTED, not refused: its data
    stays on disk and the learner recovers it at its next start (adopt_unfinished). The PARKED line says which happened.
 5. STOP is checked once more (gone -> CANCELLED, nothing touched); then switch OFF the autostart and the watchdog;
    verify Settings.Enabled is False for each (a task that will not switch off is reported, and the rest still runs:
    park_watch's rule).
 6. ONE final backup the nightly task's way (`py -3.12 -B <clone>/tools/ops/backup_learner.py`, working folder OUTSIDE
    the clone), VERIFIED: exit 0, backup_status.json fresh and ok, and the zip's runs.jsonl, cycles.jsonl and state.json
    byte-identical (sha256) to the stopped tuner's files; one retry after 2 minutes. Verified -> switch OFF the nightly
    backup task and verify. Not verified -> it is LEFT ON (the 1 AM run retries) and the run says so.
 7. Read the three tasks again, check once more that nothing runs and STOP exists, write the report, print the verdict.
 IDEMPOTENT: park --apply at any point continues from where things are. It NEVER stops or kills the learner, the batch or
 a lane: a park always waits for the round's end (RealEnv has no method that could stop a process).

RESUME --apply:
 0. A park --apply WAITING for the round holds the lock: resume CANCELS it (unless ATTENTION.md exists): it deletes STOP,
    which ends that park's wait as CANCELLED; it waits for that park to release the lock (its poll + 90 s), takes it,
    and goes on below. A lock held by anything else (a park past its wait, another resume) is refused.
 1. REFUSE as for park. ATTENTION.md present -> change NOTHING, print its reason line: the tuner will not start until a
    person fixes the cause and deletes ATTENTION.md (exit 10). This tool never touches ATTENTION.md.
 2. Already RUNNING (no STOP, the learner alive, the three tasks ON) -> "already running", exit 0, nothing changed.
 3. The clone's LEARNER still runs (a PENDING park, or running with a task OFF; a batch or lane alone does not choose
    this step): delete STOP (this CANCELS the park) and verify it is gone, switch ON any task that is OFF and verify,
    check the learner is still alive. NEVER start anything. A learner that had already found STOP (its STOP line is in
    the log) is stopping at its round's end and run_agent.ps1 will not restart it: it is waited for, then step 4 runs.
 4. Nothing of the learner runs:
    a. Autostart State "Running" (the old -NoExit window is open): it is ended ONLY with proof that it is idle (no
       learner, batch or lane process of the clone; no agent.lock, or its PID dead; the window found, with no child but
       conhost.exe), taken BEFORE any change, and ONLY while STOP exists: run_agent.ps1 checks STOP before every learner
       start, so a crash wait that ends during the Stop starts nothing. With no STOP (not parked), resume places one for
       that moment and deletes it again in c. The three tasks are switched ON first (b, still under STOP), then the
       proof is taken again, Stop-ScheduledTask, the State must leave "Running", the window must be gone, and a last
       look must find no learner, batch, lane or live lock of the clone. Anything else -> NEEDS PERSON.
    b. Switch ON the three tasks; verify each.        c. Delete STOP; verify it is gone.
    d. Start the autostart task: NEVER while STOP exists or before the three tasks read ON (re-read just before).
    e. Within 180 s a NEW `learner started (code ...)` line (only log bytes written after the resume began count) and
       agent.lock naming a live learner; then up to 10 minutes for the round's `starting N lanes` line. No start ->
       NEEDS PERSON ("is the old window still open? log off and on, or run run_agent.ps1"); nothing is undone.
 IDEMPOTENT: resume --apply at any point continues from where things are.

EXIT CODES
  park --apply:   0 PARKED (or it already was) | 10 PARTIAL, a person must read the report | 11 PENDING (--no-wait)
                 20 TIMEOUT | 30 CANCELLED | 40 UNEXPECTED | 50 refused, internal error, or INTERRUPTED (Ctrl+C)
  resume --apply: 0 RESUMED, ALREADY RUNNING, PARK CANCELLED, or TASKS ON (it ran; the OFF tasks switched ON, nothing
                 started) | 10 NEEDS PERSON | 50 refused, error, or INTERRUPTED (Ctrl+C)
  status:         one code per verdict (above).    dry runs: 0 (50 when the facts cannot be read).

COMMON RULES
- Lock `<ops>/park/park_tuner.lock` (PID, time, command, phase, poll; O_EXCL) for --apply only: a second --apply is
  refused (except that resume cancels a WAITING park, above); a lock whose PID is dead (or now another program's, or
  unreadable and over a minute old) is replaced, and that is logged.
- Every --apply action is appended to `<ops>/park/park_tuner.log` with a timestamp BEFORE it is printed (a console that
  went away loses no record); the report is `<ops>/park/latest.json` plus `<ops>/park/report-YYYYMMDD-HHMMSS.json`
  (command, start, end, each step, needs_person, notes, the verdict), written even when printing fails.
- Inside the clone it writes ONLY `ai-agent/STOP` (created by park, deleted by resume; resume also places it for the few
  seconds it ends an old window while not parked, step 4a), and only under --apply. It never registers or deletes a
  task, never runs install_ops_tasks.ps1, runs no git but read-only `rev-parse`, never touches ATTENTION.md. Liveness is
  OpenProcess + GetExitCodeProcess: ⛔ never os.kill(pid, 0), which TERMINATES on Windows.
- THE TEST GUARD: while PARK_TUNER_SELFTEST=1 (the selftest sets it), every RealEnv method that CHANGES something
  raises SelftestGuardError before reaching PowerShell, and no file in the REAL clone or REAL ops folder is written.

PROVENANCE. Built from the scratch watcher park_watch.py (2026-10-28: selftest 35/35, mutants 8/8 caught, its cancel
exit run live; source in `ai-research-notes/2026-10-28-PARK-EVIDENCE.md` section 5). Reused, each marked "park_watch"
below: _ps, RealEnv.processes/pid_alive/task_enabled/task_disable/task_enable/run_backup, read_json, last_jsonl,
count_rows, last_stop_line, short, trainer_processes, pid_is_learner, check, watch, disable_verified, verify_backup, and
the park order (park_watch.park -> park_windows). attention_reason follows tools/ops/watchdog.py instead. The fix round
(2026-10-28, an independent mutant sweep and an adversarial review) changed: the cancel of a waiting park, the resume
branch (the learner, not any process), the scoping of `learner.py run`, the lock rule of the clean stop, the PARKED
line, the --clone spelling, the TASKS ON verdict, step 4a's STOP rule and order, the silent STOP exits, the log-line
gate, the confirming look at the deadline, and the log-before-print order.
Gate: py -3.12 tools/story-dev/selftest_park_tuner.py
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

DEFAULT_CLONE = Path("C:/Remote Projects/pokebot-learner")
DEFAULT_OPS = Path(os.environ.get("LOCALAPPDATA", "C:/missing-LOCALAPPDATA")) / "pokebot-ops"
TASKS = {"autostart": "Pokebot-AI-Learner-Autostart", "watchdog": "Pokebot-Ops-Watchdog", "backup": "Pokebot-Ops-Backup"}
TS_FMT = "%Y-%m-%d %I:%M:%S %p"  # learner.log, state.json and backup_status.json all use it (park_watch)
# park_watch, unchanged: the learner's `log("STOP file found: stopping (delete ai-agent/STOP to allow the next start)")`
STOP_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] STOP file found: stopping")
# learner.loop: `log(f"learner started (code {started_sig})")`, a 12-hex code signature
START_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] learner started \(code [0-9a-f]{12}\)")
# learner.run_cycle: `log(f"{tag}: starting {lanes} lanes for {plan['minutes']:.0f} minutes")`
ROUND_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] (?P<tag>ai\d+): starting "
                        r"(?P<lanes>\d+) lanes for (?P<minutes>\d+) minutes")
# learner._loop_body: `log(f"code changed ({started_sig} -> {sig}) and test_agent.py passes: restarting into it")`: the
# learner exits 3 and run_agent.ps1 restarts it at once, after its own STOP check (so with STOP in place it stops there)
RESTART_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] code changed \([0-9a-f]{12} -> "
                          r"[0-9a-f]{12}\) and test_agent\.py passes: restarting into it")
# learner._on_crash: `_say(f"learner CRASHED ({n} of {CRASH_LIMIT} in a row):\n{tb}")` (and "learner CRASHED, and ...")
CRASH_LINE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] learner CRASHED")
TIMESTAMP_LINE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} [AP]M$")  # watchdog.py _TIMESTAMP_LINE
ZIP_MEMBERS = {"runs": "ai-agent/data/runs.jsonl", "cycles": "ai-agent/data/cycles.jsonl",
               "state": "ai-agent/data/state.json"}  # park_watch
SELFTEST_ENV = "PARK_TUNER_SELFTEST"

POLL_S = 60.0                # park: one look a minute while it waits (park_watch)
STABLE_LOOKS = 2             # two good looks a poll apart (park_watch)
UNEXPECTED_LOOKS = 3         # three looks of "nothing runs, but no clean recorded stop" (park_watch)
HEARTBEAT_S = 900.0          # a "waiting" line every 15 minutes (park_watch)
DEADLINE_MARGIN_MIN = 90.0   # the default deadline: started + minutes + 90 (spec 3.2)
BACKUP_RETRY_S = 120.0       # the final backup is retried once after 2 minutes (spec 3.2 step 6)
START_CHECK_S = 180.0        # resume: a new "learner started" line within 3 minutes (spec 3.3 step 4e)
ROUND_CHECK_S = 600.0        # resume: then the round's "starting N lanes" line within 10 minutes
START_POLL_S = 5.0
ROUND_POLL_S = 30.0
WINDOW_GONE_S = 30.0         # resume: the old window must be gone within 30 s of Stop-ScheduledTask
WINDOW_POLL_S = 2.0
LOCK_UNREADABLE_GRACE_S = 60.0
SETTLE_S = 5.0               # resume: after a STOP delete or a STOP placed for the window, a learner (or run_agent.ps1)
#                              that read STOP in that very moment has logged it or started its child by now
LEARNER_EXIT_S = 300.0       # resume: a learner that logged its STOP line must be gone within 5 minutes
LEARNER_EXIT_POLL_S = 10.0
CANCEL_MARGIN_S = 90.0       # resume: a waiting park must end within its poll + 90 s after STOP is deleted
CANCEL_POLL_S = 5.0

PARK_PARKED, PARK_PARTIAL, PARK_PENDING, PARK_TIMEOUT, PARK_CANCELLED, PARK_UNEXPECTED = 0, 10, 11, 20, 30, 40
RESUME_OK, RESUME_NEEDS_PERSON = 0, 10
EXIT_ERROR = 50
STATUS_CODES = {"RUNNING": 0, "PARK PENDING": 61, "PARKED": 62, "PARTLY PARKED": 63, "STOPPED, NOT PARKED": 64,
                "INCONSISTENT": 65}
PARK_VERDICTS = {PARK_PARKED: "PARKED", PARK_PARTIAL: "PARTIAL", PARK_PENDING: "PENDING", PARK_TIMEOUT: "TIMEOUT",
                 PARK_CANCELLED: "CANCELLED", PARK_UNEXPECTED: "UNEXPECTED", EXIT_ERROR: "ERROR"}
VERDICT_TEXT = {
    # PARKED's own line is built by parked_text() from what was proven (the headline carries the caveat)
    "PARKED": "the final backup is verified, and all three Windows tasks are OFF.",
    "PARKED (it already was)": "verified again: STOP in place, nothing runs, all three tasks OFF. No backup was run.",
    "PARTIAL": "the park is NOT complete: a person must read the points below, then run park --apply again.",
    "PENDING": "the STOP file is in place and no task was touched. Run park --apply again to finish the park.",
    "TIMEOUT": "the deadline came before a clean recorded stop. Nothing else was changed: STOP stays, so the tuner still "
               "stops at its next boundary; run park --apply again later to finish (with --deadline if the round "
               "overran).",
    "CANCELLED": "the STOP file was removed (resume --apply cancels a waiting park that way). Nothing else was changed.",
    "UNEXPECTED": "nothing of the tuner runs, but there was no clean recorded stop. Nothing else was changed (STOP "
                  "stays). Read learner.log; park --apply again parks a stopped tuner after two looks.",
    "RESUMED": "the tuner was started and checked.",
    "ALREADY RUNNING": "it was already running. Nothing was changed.",
    "TASKS ON": "it was already running; the task(s) that were OFF are ON again. Nothing was started.",
    "PARK CANCELLED": "the pending park was cancelled: STOP deleted, the tasks ON, the running round goes on.",
    "NEEDS PERSON": "stopped at a step a person must look at (below). Nothing that was done was undone.",
    "INTERRUPTED": "stopped by Ctrl+C. The steps above are what was done; nothing was undone.",
    "ERROR": "an internal error stopped the run (below).",
}
OFF_OK = ("OFF", "already OFF")
ON_OK = ("ON", "already ON")


# ------------------------------------------------------------------------------------------------------------ paths
def _strip_ext(s: str) -> str:
    """A \\\\?\\ (or \\\\?\\UNC\\) prefix dropped, forward slashes turned back: command lines never carry the prefix."""
    s = s.replace("/", "\\")
    if s.startswith("\\\\?\\UNC\\"):
        return "\\\\" + s[8:]
    if s.startswith("\\\\?\\"):
        return s[4:]
    return s


def _long_path(s: str) -> str:
    """Windows' long form of an existing path (8.3 parts such as POKEBO~1 expanded); the input when that fails."""
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        fn = k32.GetLongPathNameW
        fn.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD)
        fn.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(32768)
        n = fn(s, buf, 32768)
        return buf.value if 0 < n < 32768 else s
    except (AttributeError, OSError):
        return s


def clone_spellings(clone) -> list[str]:
    """How process command lines may spell the clone (review F6: a relative, 8.3 or \\\\?\\ --clone passed the
    DEPLOYMENT check but matched none of the 12 lanes). First the absolute long-name path (the path the tool works on),
    then the absolute path as given, then the fully resolved one (a junction's target: learner.py builds the batch's
    paths from Path(__file__).resolve()). Each is compared lower case, with backslashes."""
    a = os.path.abspath(_strip_ext(str(clone)))
    try:
        real = _strip_ext(os.path.realpath(a))
    except (OSError, ValueError):
        real = a
    out: list[str] = []
    for s in (_long_path(a), a, real):
        if s.lower() not in [o.lower() for o in out]:
            out.append(s)
    return out


def _token(s: str) -> str:
    """A folder as Win32_Process command lines spell it: lower case, backslashes, and a closing backslash (so a sibling
    such as ...\\pokebot-learner-old\\ never matches ...\\pokebot-learner\\)."""
    return os.path.normpath(s).lower().replace("/", "\\").rstrip("\\") + "\\"


class Paths:
    """Every path the tool reads or writes, from --clone and --ops-dir (park_watch.Paths, extended)."""

    def __init__(self, clone: Path, ops: Path):
        spellings = clone_spellings(clone)
        self.clone = Path(spellings[0])
        self.agent = self.clone / "ai-agent"
        self.deployment = self.agent / "DEPLOYMENT"
        self.data = self.agent / "data"
        self.stop = self.agent / "STOP"
        self.attention = self.agent / "findings" / "ATTENTION.md"
        self.log = self.data / "learner.log"
        self.lock = self.data / "agent.lock"
        self.state = self.data / "state.json"
        self.cycles = self.data / "cycles.jsonl"
        self.runs = self.data / "runs.jsonl"
        self.ops = Path(os.path.abspath(str(ops)))
        self.backup_status = self.ops / "backup_status.json"
        self.backup_script = self.clone / "tools" / "ops" / "backup_learner.py"
        self.park_dir = self.ops / "park"
        self.tool_lock = self.park_dir / "park_tuner.lock"
        self.tool_log = self.park_dir / "park_tuner.log"
        self.latest = self.park_dir / "latest.json"
        self.tokens: list[str] = []
        for s in spellings:
            if _token(s) not in self.tokens:
                self.tokens.append(_token(s))
        self.token = self.tokens[0]
        self.agent_tokens = [t + "ai-agent\\" for t in self.tokens]


# ------------------------------------------------------------------------------------------------------- the guards
class SelftestGuardError(RuntimeError):
    """Raised INSTEAD of acting while the selftest runs (PARK_TUNER_SELFTEST=1)."""


def selftest_running() -> bool:
    return os.environ.get(SELFTEST_ENV) == "1"


def guard_action(what: str) -> None:
    """THE TEST GUARD (spec 3.4). Every RealEnv method that CHANGES something calls this FIRST: while the selftest runs
    it raises, so no test can switch, start or stop a real task or run a real backup, whatever a bug routes there."""
    if selftest_running():
        raise SelftestGuardError(f"refused under {SELFTEST_ENV}=1: {what}")


def is_under(child: Path, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except (ValueError, OSError):
        return False


def guard_write(path: Path) -> None:
    """The second guard: while the selftest runs, no file in the REAL clone or the REAL ops folder is created, changed
    or deleted (every test works in temp folders)."""
    if selftest_running() and (is_under(path, DEFAULT_CLONE) or is_under(path, DEFAULT_OPS)):
        raise SelftestGuardError(f"refused under {SELFTEST_ENV}=1: a write to {path}")


# ------------------------------------------------------------------------------------------------- the live machine
def _run(argv: list[str], timeout: float, cwd: str | None = None) -> subprocess.CompletedProcess:
    """The ONE place this tool starts a process (the selftest swaps it for a tripwire that records and refuses)."""
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                          cwd=cwd)


def _ps(command: str, timeout: float = 180) -> subprocess.CompletedProcess:
    """park_watch._ps: UTF-8 WITHOUT a BOM (a BOM would make "True" read as "\\ufeffTrue"); a stray one is stripped."""
    full = "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; " + command
    r = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", full], timeout)
    r.stdout = (r.stdout or "").lstrip("\ufeff")
    return r


class RealEnv:
    """Everything that touches the live machine (park_watch.RealEnv, extended), so the selftest can replace it whole.
    READ-ONLY: now, sleep, processes, pid_alive, task_info, task_enabled, git_head. CHANGING, each calling guard_action
    FIRST: task_disable, task_enable, task_start, task_stop, run_backup. There is NO method that stops or kills a
    process: the tool cannot stop the learner, the batch or a lane."""

    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def processes(self) -> list[dict]:  # park_watch, unchanged
        r = _ps("Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine "
                "| ConvertTo-Json -Compress")
        if r.returncode != 0:
            raise RuntimeError(f"process list failed: {r.stderr.strip()[:300]}")
        data = json.loads(r.stdout)
        return data if isinstance(data, list) else [data]

    def pid_alive(self, pid: int) -> bool:  # park_watch, unchanged
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

    def task_info(self, name: str) -> dict:
        """State ('Ready', 'Running', 'Disabled', ...) and Settings.Enabled (the truth for ON/OFF: a disabled task whose
        -NoExit window is still open reads State 'Running'). Raises when the task cannot be read."""
        r = _ps(f"$t = Get-ScheduledTask -TaskName '{name}' -ErrorAction Stop; "
                f"[string]$t.State + '|' + [string]$t.Settings.Enabled")
        state, _, enabled = r.stdout.strip().partition("|")
        if r.returncode != 0 or enabled not in ("True", "False"):
            raise RuntimeError(f"cannot read {name}: {(r.stderr or r.stdout).strip()[:300]}")
        return {"state": state, "enabled": enabled == "True"}

    def task_enabled(self, name: str) -> bool:  # park_watch (the same Settings.Enabled, read through task_info)
        return self.task_info(name)["enabled"]

    def git_head(self, clone: Path) -> str:
        """READ-ONLY `git -C <clone> rev-parse --short HEAD`: the only git this tool ever runs."""
        r = _run(["git", "-C", str(clone), "rev-parse", "--short", "HEAD"], 30)
        return r.stdout.strip() if r.returncode == 0 else f"unknown ({(r.stderr or '').strip()[:80]})"

    def task_disable(self, name: str) -> None:  # park_watch + the guard
        guard_action(f"Disable-ScheduledTask {name}")
        r = _ps(f"Disable-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Disable-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def task_enable(self, name: str) -> None:  # park_watch + the guard
        guard_action(f"Enable-ScheduledTask {name}")
        r = _ps(f"Enable-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Enable-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def task_start(self, name: str) -> None:
        guard_action(f"Start-ScheduledTask {name}")
        r = _ps(f"Start-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Start-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def task_stop(self, name: str) -> None:
        """Ends the task's RUNNING INSTANCE: the idle -NoExit window. Only resume calls it, and only with proof that the
        window is idle (idle_window_proof) and while STOP exists."""
        guard_action(f"Stop-ScheduledTask {name}")
        r = _ps(f"Stop-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
        if r.returncode != 0:
            raise RuntimeError(f"Stop-ScheduledTask {name} failed: {r.stderr.strip()[:300]}")

    def run_backup(self, paths: Paths) -> tuple[int, str]:
        """park_watch.run_backup: the nightly task's own command (`pyw -3.12 -B backup_learner.py`), with py so its
        output is kept. -B: no __pycache__ is written into the clone; the working folder is OUTSIDE the clone."""
        guard_action("the final backup (backup_learner.py)")
        cwd = Path(tempfile.gettempdir())
        if is_under(cwd, paths.clone):
            cwd = paths.ops
        r = _run(["py", "-3.12", "-B", str(paths.backup_script)], 1800, cwd=str(cwd))
        return r.returncode, ((r.stdout or "") + (r.stderr or ""))[-1500:]


# ---------------------------------------------------------------------------------------------------------- reading
def ts(t: datetime) -> str:
    return t.strftime(TS_FMT)


def parse_ts(s) -> datetime | None:
    try:
        return datetime.strptime(str(s), TS_FMT)
    except (TypeError, ValueError):
        return None


def hm(t: datetime | None, now: datetime | None = None) -> str:
    """A 12-hour time for a non-programmer: '4:30 PM', '4:30 AM tomorrow', 'Oct 30, 4:30 AM'."""
    if t is None:
        return "an unknown time"
    s = t.strftime("%I:%M %p").lstrip("0")
    if now is None or t.date() == now.date():
        return s
    if t.date() == (now + timedelta(days=1)).date():
        return f"{s} tomorrow"
    if t.date() == (now - timedelta(days=1)).date():
        return f"{s} yesterday"
    return f"{t.strftime('%b')} {t.day}, {s}"


def as_minutes(x) -> float | None:
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def file_time(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def read_json(path: Path):  # park_watch
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - unreadable reads as None: the caller treats it as "not yet"
        return None


def last_jsonl(path: Path):  # park_watch
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:  # noqa: BLE001
        return None


def count_rows(path: Path, tag: str) -> int | None:  # park_watch
    try:
        n = 0
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.strip() and json.loads(ln).get("source") == tag:
                n += 1
        return n
    except Exception:  # noqa: BLE001
        return None


def last_stop_line(log: Path, since: datetime) -> str | None:  # park_watch, unchanged
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


def last_line_since(log: Path, pattern: re.Pattern, since: datetime) -> str | None:
    """last_stop_line for any of the learner's dated lines: the newest timestamp of a `pattern` line at/after `since`."""
    try:
        with open(log, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 524288))
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    found = None
    for line in text.splitlines():
        m = pattern.match(line)
        if m and parse_ts(m["ts"]) is not None and parse_ts(m["ts"]) >= since:
            found = m["ts"]
    return found


def read_text_head(path: Path, limit: int = 300) -> str | None:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="replace")
    except OSError:
        return None


def read_lock_pid(paths: Paths) -> int | None:
    """The learner's PID from agent.lock (park_watch.baseline's parse); None when absent or unreadable."""
    try:
        return int(paths.lock.read_text(encoding="utf-8").strip().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def attention_reason(paths: Paths) -> str:
    """tools/ops/watchdog.py attention_reason: the learner's ATTENTION.md is a heading, a timestamp, then the reason; the
    first line that is neither is the reason. (park_watch took the LAST line, which in the learner's real format is the
    'Fix the cause, delete this file ...' footer, not the reason.)"""
    try:
        text = paths.attention.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return "(ATTENTION.md is unreadable)"
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not TIMESTAMP_LINE.match(s):
            return s[:300]
    return "(ATTENTION.md holds no reason line)"


def attention_since(paths: Paths, since: datetime) -> bool:  # park_watch.check's "attention" condition
    t = file_time(paths.attention)
    return t is not None and t >= since


def log_size(paths: Paths) -> int:
    try:
        return paths.log.stat().st_size
    except OSError:
        return 0


def log_since(paths: Paths, offset: int) -> str:
    """learner.log as written AFTER byte `offset` (resume's start check counts only lines written after the resume
    began). A log now SHORTER than the offset was replaced after the offset was taken, so all of it is new."""
    try:
        with open(paths.log, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(offset if size >= offset else 0)
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def log_tail(paths: Paths, n: int = 3) -> list[str]:
    try:
        with open(paths.log, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            lines = [ln.strip() for ln in f.read().decode("utf-8", errors="replace").splitlines() if ln.strip()]
        return [ln[:200] for ln in lines[-n:]]
    except OSError:
        return []


def last_match(pattern: re.Pattern, text: str):
    found = None
    for line in text.splitlines():
        m = pattern.match(line)
        if m:
            found = m
    return found


def current_round(paths: Paths) -> dict | None:
    """state.json `current` (the running round: tag, started, lanes, minutes), or None between rounds."""
    st = read_json(paths.state)
    cur = st.get("current") if isinstance(st, dict) else None
    return cur if isinstance(cur, dict) and cur.get("tag") else None


def round_facts(cur: dict | None) -> dict | None:
    if not cur:
        return None
    started, minutes = parse_ts(cur.get("started")), as_minutes(cur.get("minutes"))
    ends = started + timedelta(minutes=minutes) if started is not None and minutes is not None else None
    return {"tag": cur.get("tag"), "started": started, "minutes": minutes, "ends": ends}


def default_deadline(cur: dict | None, now: datetime) -> tuple[datetime, str]:
    """Spec 3.2 step 3: current.started + current.minutes + 90 minutes. With no round running: now + 90 minutes (the
    learner stops at its next boundary); with an unreadable start: now + the round's length (or 720) + 90 minutes."""
    if cur:
        started, minutes = parse_ts(cur.get("started")), as_minutes(cur.get("minutes"))
        if started is not None and minutes is not None:
            return (started + timedelta(minutes=minutes + DEADLINE_MARGIN_MIN),
                    f"round {cur.get('tag')} started {ts(started)} + {minutes:.0f} min + {DEADLINE_MARGIN_MIN:.0f} min")
        length = minutes if minutes is not None else 720.0
        return (now + timedelta(minutes=length + DEADLINE_MARGIN_MIN),
                f"round {cur.get('tag')} has no readable start: now + {length:.0f} min + {DEADLINE_MARGIN_MIN:.0f} min")
    return now + timedelta(minutes=DEADLINE_MARGIN_MIN), f"no round is running: now + {DEADLINE_MARGIN_MIN:.0f} min"


# ------------------------------------------------------------------------------------------- processes and the lock
def _low(p: dict) -> str:
    return (p.get("CommandLine") or "").lower().replace("/", "\\")


def short(p: dict) -> str:  # park_watch
    cmd = (p.get("CommandLine") or "").replace("\n", " ")
    return f"{p.get('ProcessId')} {p.get('Name')} {cmd[:120]}"


def _ancestors(pid, by_pid: dict, limit: int = 32) -> list:
    """The PIDs above `pid` by ParentProcessId, nearest first, while they are in the table (bounded, loop-safe)."""
    out, seen = [], {pid}
    cur = by_pid.get(pid)
    while cur is not None and len(out) < limit:
        parent = cur.get("ParentProcessId")
        if parent in seen or parent not in by_pid:
            break
        out.append(parent)
        seen.add(parent)
        cur = by_pid.get(parent)
    return out


def clone_learners(procs: list[dict], paths: Paths, lock_pid: int | None) -> set:
    """THIS clone's path-less `learner.py run` processes (review F3: the learner and its py.exe launcher hold NO clone
    path, build spec section 2): those under the clone's run_agent.ps1 window (by ParentProcessId), the agent.lock
    holder, and the lock holder's `learner.py run` ancestors (a learner started by hand: its launcher). Any OTHER
    `learner.py run` (a --dev learner in another checkout, a test's child, a shell loop that greps for the phrase) is
    not this clone's."""
    by_pid = {p.get("ProcessId"): p for p in procs}
    windows = {w.get("ProcessId") for w in window_processes(procs, paths)}
    out = set()
    for p in procs:
        pid = p.get("ProcessId")
        if "learner.py run" in _low(p) and (pid == lock_pid or windows & set(_ancestors(pid, by_pid))):
            out.add(pid)
    if lock_pid in by_pid:
        for a in _ancestors(lock_pid, by_pid):
            if "learner.py run" not in _low(by_pid[a]):
                break
            out.add(a)
    return out


def trainer_processes(procs: list[dict], self_pid: int, paths: Paths, lock_pid: int | None = None) -> list[dict]:
    """park_watch.trainer_processes, with the clone's spellings (paths.tokens) where it had the literal
    'pokebot-learner'. The processes that mean the tuner still RUNS: the batch (`x4_headless.py`) and the lanes
    (`sandbox-pokebot`) of the clone, and the clone's learner and py.exe launcher (`learner.py run`, which hold no clone
    path: clone_learners decides which are this clone's; `lock_pid` is agent.lock's PID when it names a live learner).
    NOT counted: the idle `run_agent.ps1` window (-NoExit keeps it open after a stop), the clone's ops tools
    (`tools\\ops\\`: the watchdog and backup tasks, short-lived and read-only on the clone), this tool, and park_watch."""
    learners = clone_learners(procs, paths, lock_pid)
    out = []
    for p in procs:
        if p.get("ProcessId") == self_pid:
            continue
        low = _low(p)
        if "run_agent.ps1" in low or "\\tools\\ops\\" in low or "park_watch.py" in low or "park_tuner.py" in low:
            continue
        mine = any(t in low for t in paths.tokens)
        if ("learner.py run" in low and p.get("ProcessId") in learners) or (
                mine and ("x4_headless.py" in low or "sandbox-pokebot" in low or "learner.py" in low)):
            out.append(p)
    return out


def other_learners(procs: list[dict], trainer: list[dict], self_pid: int) -> list[dict]:
    """The `learner.py run` processes that are NOT this clone's tuner (shown by status; they block nothing)."""
    mine = {p.get("ProcessId") for p in trainer}
    out = []
    for p in procs:
        low = _low(p)
        if p.get("ProcessId") in mine or p.get("ProcessId") == self_pid or "learner.py run" not in low:
            continue
        if not any(x in low for x in ("\\tools\\ops\\", "park_watch.py", "park_tuner.py")):
            out.append(p)
    return out


def lane_processes(trainer: list[dict]) -> list[dict]:
    return [p for p in trainer if "sandbox-pokebot" in _low(p)]


def batch_processes(trainer: list[dict]) -> list[dict]:
    return [p for p in trainer if "x4_headless.py" in _low(p)]


def pid_is_learner(pid: int | None, procs: list[dict]) -> bool:  # park_watch, unchanged
    """The PID is alive AND still the learner (a reused PID belongs to someone else)."""
    if pid is None:
        return False
    for p in procs:
        if p.get("ProcessId") == pid:
            return "learner.py" in (p.get("CommandLine") or "")
    return False


def window_processes(procs: list[dict], paths: Paths) -> list[dict]:
    """The clone's run_agent.ps1 window: the autostart task's `powershell.exe -NoExit ... -File <clone>\\ai-agent\\
    run_agent.ps1`. -NoExit keeps it open after the learner exits, and while it is open the task reads Running."""
    return [p for p in procs if any(t + "run_agent.ps1" in _low(p) for t in paths.agent_tokens)]


def children_of(pid, procs: list[dict]) -> list[dict]:
    return [p for p in procs if p.get("ParentProcessId") == pid and p.get("ProcessId") != pid]


def look(paths: Paths, env) -> dict:
    """One look at what of the tuner RUNS: the process table and the learner's lock (no tasks, no git)."""
    procs = env.processes()
    pid = read_lock_pid(paths)
    alive = pid_is_learner(pid, procs)
    trainer = trainer_processes(procs, os.getpid(), paths, pid if alive else None)
    exists = paths.lock.exists()
    return {"procs": procs, "trainer": trainer, "lock": exists, "lock_pid": pid, "learner_alive": alive,
            "lock_unreadable": exists and pid is None, "runs": alive or bool(trainer),
            "others": other_learners(procs, trainer, os.getpid())}


def idle_window_proof(paths: Paths, env, procs: list[dict]) -> tuple[bool, list[str], list[dict]]:
    """Spec 3.3 step 4a: the old -NoExit window may be ended ONLY with proof that it is IDLE, every part of it: (1) no
    learner, batch or lane process of the clone in the full process table; (2) no agent.lock, or its PID dead; (3) the
    window is found and has no child process other than conhost.exe. Returns (proven, what failed, the windows)."""
    why = []
    lock_pid = read_lock_pid(paths)
    trainer = trainer_processes(procs, os.getpid(), paths, lock_pid if pid_is_learner(lock_pid, procs) else None)
    if trainer:
        why.append(f"tuner processes run: {[short(p) for p in trainer][:3]}")
    if paths.lock.exists():
        pid = read_lock_pid(paths)
        if pid is None:
            why.append("agent.lock exists and names no readable PID")
        elif env.pid_alive(pid):
            why.append(f"agent.lock names PID {pid}, which is alive")
    windows = window_processes(procs, paths)
    if not windows:
        why.append("no run_agent.ps1 window of this clone is in the process table")
    for w in windows:
        kids = [c for c in children_of(w.get("ProcessId"), procs) if (c.get("Name") or "").lower() != "conhost.exe"]
        if kids:
            why.append(f"the window (PID {w.get('ProcessId')}) has a child that is not conhost.exe: "
                       f"{[short(c) for c in kids][:3]}")
    return not why, why, windows


# ------------------------------------------------------------------------------------------- the park tool's lock
def read_tool_lock(paths: Paths) -> dict | None:
    """The park tool's lock as written (pid, since, command, phase, poll): None when absent, {} when unreadable."""
    try:
        holder = json.loads(paths.tool_lock.read_text(encoding="utf-8"))
        return holder if isinstance(holder, dict) else {}
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return {} if paths.tool_lock.exists() else None


def tool_lock_stale(paths: Paths, env, procs: list[dict] | None = None) -> str | None:
    """Why a held park tool lock is a dead run's, or None while it may be a live one's."""
    try:
        holder = json.loads(paths.tool_lock.read_text(encoding="utf-8"))
        pid = holder.get("pid") if isinstance(holder, dict) else None
    except (OSError, ValueError):
        pid = None
    if not isinstance(pid, int) or isinstance(pid, bool):
        try:
            age = time.time() - paths.tool_lock.stat().st_mtime
        except OSError:
            return "it vanished"
        return f"it names no readable PID and is {age:.0f} s old" if age > LOCK_UNREADABLE_GRACE_S else None
    if not env.pid_alive(pid):
        return f"its PID {pid} is not running"
    for p in (env.processes() if procs is None else procs):
        if p.get("ProcessId") == pid:
            if "park_tuner" in (p.get("CommandLine") or "").lower():
                return None
            return f"its PID {pid} now belongs to {p.get('Name')}, not to the park tool"
    return None


def tool_lock_view(paths: Paths, env, procs: list[dict] | None = None) -> dict | None:
    """READ-ONLY, for status and the dry runs: None (no park or resume --apply runs), or the lock's fields plus `stale`
    (why it is a dead run's, or None while it may be a live one's)."""
    holder = read_tool_lock(paths)
    if holder is None:
        return None
    return {**holder, "stale": tool_lock_stale(paths, env, procs)}


def is_waiting_park(view: dict | None) -> bool:
    return (bool(view) and not view.get("stale") and str(view.get("command", "")).startswith("park --apply")
            and isinstance(view.get("pid"), int) and not isinstance(view.get("pid"), bool)
            and view.get("phase") == "waiting")


def waiting_park(paths: Paths, env) -> dict | None:
    """Review F1: the lock's holder when it is a LIVE park --apply WAITING for the round with STOP in place (resume
    --apply cancels exactly that park: deleting STOP ends its wait as CANCELLED), else None."""
    view = tool_lock_view(paths, env)
    return view if is_waiting_park(view) and paths.stop.exists() else None


def tool_lock_text(view: dict | None) -> str:
    if view is None:
        return "no park or resume --apply is running"
    who = f"{view.get('command') or 'a park/resume --apply'} (PID {view.get('pid')}, since {view.get('since')})"
    if view.get("stale"):
        return f"a stale lock of {who}: {view['stale']}; the next --apply replaces it"
    if is_waiting_park(view):
        return f"{who} is WAITING for the round to end: it finishes the park by itself"
    return f"{who} is running (phase {view.get('phase') or 'unknown'})"


# ------------------------------------------------------------------------------------------------ status: the facts
def task_facts(env, name: str) -> dict:
    try:
        info = env.task_info(name)
        return {"state": str(info.get("state")), "enabled": info.get("enabled") is True}
    except Exception as e:  # noqa: BLE001 - a task that cannot be read is a FACT to show, not a crash
        return {"state": "UNREADABLE", "enabled": None, "error": f"{type(e).__name__}: {e}"[:200]}


def gather(paths: Paths, env) -> dict:
    """Everything status shows. READ-ONLY: it creates and changes nothing, not even a folder."""
    f = look(paths, env)
    f["now"] = env.now()
    f["clone"] = paths.clone
    f["deployment"] = paths.deployment.exists()
    f["stop"] = paths.stop.exists()
    f["stop_time"] = file_time(paths.stop) if f["stop"] else None
    f["stop_text"] = read_text_head(paths.stop) if f["stop"] else None
    f["attention"] = paths.attention.exists()
    f["attention_reason"] = attention_reason(paths) if f["attention"] else None
    st = read_json(paths.state)
    f["state_readable"] = isinstance(st, dict)
    f["current"] = current_round(paths)
    f["last_cycle"] = (last_jsonl(paths.cycles) or {}).get("tag")
    f["tasks"] = {key: task_facts(env, name) for key, name in TASKS.items()}
    f["backup"] = read_json(paths.backup_status)
    f["last_report"] = read_json(paths.latest)
    f["tool_lock"] = tool_lock_view(paths, env, f["procs"])
    try:
        f["head"] = env.git_head(paths.clone)
    except Exception as e:  # noqa: BLE001
        f["head"] = f"unknown ({type(e).__name__})"
    f["windows"] = window_processes(f["procs"], paths)
    f["log_tail"] = log_tail(paths, 3)
    return f


def verdict(f: dict) -> str:
    """The six verdicts of spec 3.1, from the facts alone (the docstring lists them)."""
    readable = all(t["enabled"] is not None for t in f["tasks"].values())
    all_on = readable and all(t["enabled"] for t in f["tasks"].values())
    all_off = readable and not any(t["enabled"] for t in f["tasks"].values())
    if f["stop"] and f["runs"]:
        return "PARK PENDING"
    if f["stop"]:
        if not readable:
            return "INCONSISTENT"
        return "PARKED" if all_off else "PARTLY PARKED"
    if not f["runs"]:
        return "STOPPED, NOT PARKED"
    if f["learner_alive"] and all_on:
        return "RUNNING"
    return "INCONSISTENT"


def brief(f: dict, v: str) -> dict:
    rnd = round_facts(f["current"])
    return {"verdict": v, "stop": f["stop"], "lock_pid": f["lock_pid"], "learner_alive": f["learner_alive"],
            "tuner_processes": len(f["trainer"]), "lanes": len(lane_processes(f["trainer"])),
            "round": rnd["tag"] if rnd else None, "attention": f["attention_reason"], "head": f["head"],
            "other_learners": [short(p) for p in f["others"]][:3],
            "tasks": {TASKS[k]: {"state": t["state"], "enabled": t["enabled"]} for k, t in f["tasks"].items()}}


def on_names(f: dict) -> list[str]:
    return [TASKS[k] for k, t in f["tasks"].items() if t["enabled"] is True]


def stop_by_resume(f: dict) -> bool:
    """STOP is the one resume --apply places for a moment while it ends the old window (step 4a): if it is still here,
    that resume stopped before it finished, and the user wants the tuner RUNNING, not parked."""
    return f["stop"] and (f["stop_text"] or "").startswith(RESUME_STOP_MARK)


def headline(f: dict, v: str) -> str:
    line = verdict_headline(f, v)
    if stop_by_resume(f):
        line += " NOTE: this STOP file is resume --apply's own: a resume stopped before it finished."
    return line


def verdict_headline(f: dict, v: str) -> str:
    now, rnd = f["now"], round_facts(f["current"])
    lanes = len(lane_processes(f["trainer"]))
    on = on_names(f)
    if v == "RUNNING":
        what = f"round {rnd['tag']}" if rnd else "between rounds"
        return f"RUNNING: the bot tuner is running ({what}, {lanes} lanes); nothing is parked."
    if v == "PARK PENDING":
        when = (f"round {rnd['tag']}, which should end about {hm(rnd['ends'], now)}" if rnd and rnd["ends"]
                else "between rounds")
        return f"PARK PENDING: the STOP file is in place and the tuner is still running ({when}); then it stops itself."
    if v == "PARKED":
        return "PARKED: the tuner is stopped, the STOP file is in place, and all three Windows tasks are OFF."
    if v == "PARTLY PARKED":
        return (f"PARTLY PARKED: the tuner is stopped and the STOP file is in place, but {', '.join(on)} "
                f"{'is' if len(on) == 1 else 'are'} still ON.")
    if v == "STOPPED, NOT PARKED":
        why = (f"It paused itself: ATTENTION.md says: {f['attention_reason']}" if f["attention"]
               else f"The log's last line: {f['log_tail'][-1] if f['log_tail'] else '(empty)'}")
        restart = ("Its tasks are ON, so a logon restarts it." if f["tasks"]["autostart"]["enabled"] is True
                   else f"{TASKS['autostart']} is OFF, so a logon does NOT restart it.")
        return f"STOPPED, NOT PARKED: nothing of the tuner runs and there is no STOP file. {why} {restart}"
    return "INCONSISTENT: the facts below do not fit one state. Read them before parking or resuming."


def park_rest(f: dict) -> list[str]:
    """What park --apply would still do for a stopped tuner (PARTLY PARKED)."""
    out = [f"switch OFF {TASKS[k]}" for k in ("autostart", "watchdog") if f["tasks"][k]["enabled"] is not False]
    out.append("run and verify the final backup")
    if f["tasks"]["backup"]["enabled"] is not False:
        out.append(f"then switch OFF {TASKS['backup']}")
    return out


def next_step(f: dict, v: str) -> str:
    now, rnd = f["now"], round_facts(f["current"])
    tool = "py -3.12 tools/ops/park_tuner.py"
    when = f" (about {hm(rnd['ends'], now)})" if rnd and rnd["ends"] else ""
    lockv = f.get("tool_lock")
    if v == "PARK PENDING" and is_waiting_park(lockv):
        return (f"nothing: the waiting park --apply (PID {lockv.get('pid')}) finishes the park by itself "
                f"after the round{when}. To cancel the park instead: `{tool} resume --apply` (it deletes STOP, "
                "which ends that waiting park as CANCELLED, then switches ON any task that is OFF).")
    if lockv is not None and not lockv.get("stale"):  # any verdict: a running --apply is let finish, never raced
        return (f"wait: {tool_lock_text(lockv)}; let it finish, then run status again (resume --apply and park "
                "--apply are refused while it holds the park tool's lock).")
    if stop_by_resume(f):
        return ("a resume --apply stopped before it finished: this STOP file is the one it places for a moment while it "
                f"ends the old window. Run `{tool} resume --apply` again to finish the resume"
                + (" once nothing of the tuner runs" if f["runs"] else "") + " (park --apply only if the user asked "
                "for a park).")
    if v == "RUNNING":
        return (f"nothing. To park it (only when the user asks): {tool} park --apply (it waits for the round to end: "
                f"run it detached, or --no-wait now and park --apply after the round).")
    if v == "PARK PENDING":
        return (f"wait: it stops by itself after its round{when}. `{tool} park --apply` finishes the park (it waits: run "
                f"it detached, or after the round). To cancel the park instead: `{tool} resume --apply`.")
    if v == "PARKED":
        return f"nothing. To resume it (only when the user asks): {tool} resume --apply."
    if v == "PARTLY PARKED":
        return f"run `{tool} park --apply` to finish: it would " + ", ".join(park_rest(f)) + "."
    if v == "STOPPED, NOT PARKED":
        if f["attention"]:
            return ("a person must fix the cause named in ATTENTION.md and delete it; then `resume --apply` restarts it "
                    "(or `park --apply` parks it).")
        return f"`{tool} resume --apply` restarts it, or `{tool} park --apply` parks it (only when the user asks)."
    return ("run status again in a minute (a restart can look like this for a moment). If it stays, ask Claude to read "
            "these facts before anyone parks or resumes.")


def backup_text(st, now: datetime) -> str:
    if not isinstance(st, dict):
        return "no backup status yet (no backup_status.json)"
    t = parse_ts(st.get("time"))
    when = hm(t, now) if t else repr(st.get("time"))
    if st.get("ok") is True:
        return f"last run {when}: ok"
    return f"last run {when}: NOT ok ({str(st.get('error'))[:120]})"


def report_text(rep) -> str:
    if not isinstance(rep, dict):
        return "none"
    return f"{rep.get('command')} ended {rep.get('end')}: {rep.get('verdict')} (exit {rep.get('exit')})"


def status_lines(f: dict, v: str) -> list[str]:
    now, rnd = f["now"], round_facts(f["current"])
    lines = [headline(f, v)]
    if f["lock_pid"] is None:
        lk = "agent.lock holds no readable PID" if f["lock"] else "agent.lock is absent"
    elif f["learner_alive"]:
        lk = f"agent.lock names PID {f['lock_pid']}: alive, and it is the learner"
    elif any(p.get("ProcessId") == f["lock_pid"] for p in f["procs"]):
        lk = f"agent.lock names PID {f['lock_pid']}: alive but NOT a learner (a reused PID: a stale lock)"
    else:
        lk = f"agent.lock names PID {f['lock_pid']}: not running (a stale lock)"
    lines.append(f"  Learner:    {lk}")
    if rnd:
        mins = f"{rnd['minutes']:.0f} minutes" if rnd["minutes"] else "? minutes"
        lines.append(f"  Round:      {rnd['tag']}, started {hm(rnd['started'], now)}, {mins}; ends about "
                     f"{hm(rnd['ends'], now)}")
    else:
        lines.append(f"  Round:      none running (the last recorded round: {f['last_cycle'] or 'none'})"
                     + ("" if f["state_readable"] else "; state.json is UNREADABLE"))
    lanes, batches = lane_processes(f["trainer"]), batch_processes(f["trainer"])
    lines.append(f"  Processes:  {len(lanes)} lanes, {len(batches)} batch, "
                 f"{len(f['trainer']) - len(lanes) - len(batches)} learner/launcher")
    if f["others"]:
        lines.append(f"  Others:     {len(f['others'])} 'learner.py run' process(es) that are NOT this clone's tuner (not "
                     f"counted): {[short(p) for p in f['others']][:2]}")
    if f["stop"]:
        first = (f["stop_text"] or "").strip().splitlines()
        lines.append(f"  STOP:       present since {hm(f['stop_time'], now)}: {(first[0] if first else '(empty)')[:90]!r}")
    else:
        lines.append("  STOP:       absent")
    lines.append("  ATTENTION:  " + (f"ATTENTION.md says: {f['attention_reason']}" if f["attention"] else "none"))
    if f["windows"]:
        w = f["windows"][0]
        kids = [c for c in children_of(w.get("ProcessId"), f["procs"]) if (c.get("Name") or "").lower() != "conhost.exe"]
        lines.append(f"  Window:     the tuner's run_agent.ps1 window is open (PID {w.get('ProcessId')}): "
                     + ("it runs the learner" if kids else "idle, so closing it is safe (resume --apply ends it itself)"))
    else:
        lines.append("  Window:     no run_agent.ps1 window of this clone is open")
    for i, (key, name) in enumerate(TASKS.items()):
        t = f["tasks"][key]
        onoff = "ON" if t["enabled"] is True else "OFF" if t["enabled"] is False else f"UNREADABLE ({t.get('error')})"
        lines.append(f"  {'Tasks:' if i == 0 else '':<11} {name}: {onoff} (State {t['state']})")
    lines.append(f"  Backup:     {backup_text(f['backup'], now)}")
    lines.append(f"  Park tool:  {tool_lock_text(f['tool_lock'])}")
    lines.append(f"  Last park/resume: {report_text(f['last_report'])}")
    lines.append(f"  Clone:      HEAD {f['head']} ({os.path.normpath(str(f['clone']))})")
    if not f["deployment"]:
        lines.append("  WARNING:    no ai-agent/DEPLOYMENT in this clone: park --apply and resume --apply REFUSE it")
    if v in ("STOPPED, NOT PARKED", "INCONSISTENT"):
        for i, ln in enumerate(f["log_tail"] or ["(learner.log is empty or unreadable)"]):
            lines.append(f"  {'Log tail:' if i == 0 else '':<11} {ln}")
    lines.append(f"What to do next: {next_step(f, v)}")
    return lines


# ---------------------------------------------------------------------------------------------- writing (--apply)
def append_line(path: Path, line: str) -> None:
    guard_write(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def write_json(path: Path, obj) -> None:
    guard_write(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)


STOP_TEXT = {
    "park --apply": ("STOP placed by tools/ops/park_tuner.py (park --apply) at {at}.\nThe bot tuner reads this file only "
                     "between rounds: its running round finishes and is recorded, then it stops.\nTo resume it (only "
                     "when the user asks): py -3.12 tools/ops/park_tuner.py resume --apply\n"),
    "resume --apply": ("STOP placed by tools/ops/park_tuner.py (resume --apply) at {at}, for the few seconds it ends the "
                       "old idle tuner window (a learner start that races it exits at once); the same resume deletes it "
                       "again before it starts the tuner.\nIf you find it here, that resume stopped early: run py -3.12 "
                       "tools/ops/park_tuner.py resume --apply again (or park --apply to park).\n"),
}
RESUME_STOP_MARK = STOP_TEXT["resume --apply"].split(" at {at}")[0]  # "STOP placed by ... (resume --apply)"


def place_stop(paths: Paths, at: datetime, by: str = "park --apply") -> str:
    """Create ai-agent/STOP with a text naming this tool, the time and the resume command. Exclusive create: a STOP that
    appeared meanwhile is kept, never overwritten. Returns 'placed' or 'already there'."""
    guard_write(paths.stop)
    body = (STOP_TEXT[by].format(at=ts(at)))
    try:
        with open(paths.stop, "x", encoding="utf-8") as fh:
            fh.write(body)
        return "placed"
    except FileExistsError:
        return "already there"


def remove_stop(paths: Paths) -> None:
    guard_write(paths.stop)
    paths.stop.unlink(missing_ok=True)


def acquire_tool_lock(paths: Paths, env, command: str, poll: float | None = None) -> tuple[bool, str]:
    """Spec 3.4: `<ops>/park/park_tuner.lock` (PID, time, command, phase, poll) for --apply only, so one park or resume
    runs at a time. O_EXCL, as backup_learner.acquire_lock. A stale lock is replaced once; the note says so (logged)."""
    guard_write(paths.tool_lock)
    paths.park_dir.mkdir(parents=True, exist_ok=True)
    note = ""
    for attempt in range(2):
        try:
            fd = os.open(paths.tool_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            stale = tool_lock_stale(paths, env)
            if attempt == 0 and stale:
                try:
                    paths.tool_lock.unlink()
                except FileNotFoundError:
                    pass
                note = f"a stale park tool lock was replaced ({stale})"
                continue
            return False, lock_refusal(paths)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "since": ts(env.now()), "command": command, "phase": "starting",
                                 "poll": poll}))
        return True, note
    return False, f"could not take the lock {paths.tool_lock}"


def lock_refusal(paths: Paths) -> str:
    """Why the lock is not ours, and what to do instead (review F1: name the REAL cancel)."""
    held = read_tool_lock(paths) or {}
    cmd = str(held.get("command") or "a park/resume --apply")
    who = f"{cmd} (PID {held.get('pid')}, since {held.get('since')}, phase {held.get('phase') or 'unknown'})"
    if cmd.startswith("park") and held.get("phase") == "waiting" and not paths.stop.exists():
        advice = ("it is ENDING: its STOP file is already gone, so its wait ends as CANCELLED within its next look; run "
                  "status in a minute, then the command again")
    elif cmd.startswith("park") and held.get("phase") == "waiting":
        advice = ("it WAITS for the round and finishes the park by itself; to cancel that park instead, run resume "
                  "--apply (it ends a waiting park as CANCELLED)")
    elif cmd.startswith("park") and held.get("phase") == "parking":
        advice = ("it is past its wait (switching the tasks off and running the final backup, up to about an hour); "
                  "run status after it ends, then resume --apply if the tuner should run")
    elif cmd.startswith("park") and held.get("phase") == "starting":
        advice = "it has just started; run status in a minute"
    elif cmd.startswith("park"):
        advice = "it does not say what it is doing (an older park tool?); run status, and wait for it to finish"
    else:
        advice = "wait for it to finish (a resume takes up to about 15 minutes), then run status"
    return f"another --apply holds the park tool's lock {paths.tool_lock}: {who}; {advice}"


def set_tool_lock_phase(paths: Paths, phase: str) -> bool:
    """Record what this run is doing in its own lock (a resume --apply cancels a park only in phase 'waiting'). Advisory:
    a lock that cannot be rewritten (a reader holding it in that instant) is retried, then left; returns whether set."""
    for _attempt in range(3):
        holder = read_tool_lock(paths)
        if not isinstance(holder, dict) or holder.get("pid") != os.getpid():
            return False
        try:
            write_json(paths.tool_lock, {**holder, "phase": phase})
            return True
        except OSError:
            continue
    return False


def release_tool_lock(paths: Paths) -> None:
    try:
        holder = json.loads(paths.tool_lock.read_text(encoding="utf-8"))
        if isinstance(holder, dict) and holder.get("pid") == os.getpid():
            guard_write(paths.tool_lock)
            paths.tool_lock.unlink()
    except (OSError, ValueError):
        pass


class Run:
    """One --apply run: each line appended to <ops>/park/park_tuner.log and then printed; its steps, the points that need
    a person, notes, and the report written at the end."""

    def __init__(self, paths: Paths, env, command: str):
        self.paths, self.env, self.command = paths, env, command
        self.start = env.now()
        self.steps: list[dict] = []
        self.needs_person: list[str] = []
        self.notes: list[str] = []
        self.verdict: str | None = None
        self.verdict_text: str | None = None
        self.extra: dict = {}
        self.log(f"{command} started (pid {os.getpid()}, clone {paths.clone})")

    def log(self, msg: str) -> None:
        line = f"[{ts(self.env.now())}] {msg}"
        append_line(self.paths.tool_log, line)  # the record FIRST (review F12): a console that went away loses nothing
        try:
            print(line, flush=True)
        except (OSError, ValueError):
            pass

    def step(self, name: str, result: str) -> None:
        self.steps.append({"at": ts(self.env.now()), "step": name, "result": result})
        self.log(f"{name}: {result}")

    def person(self, msg: str) -> None:
        self.needs_person.append(msg)
        self.log(f"NEEDS A PERSON: {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)
        self.log(f"note: {msg}")

    def write_report(self, code: int) -> Path:
        rep = {"command": self.command, "start": ts(self.start), "end": ts(self.env.now()), "verdict": self.verdict,
               "verdict_text": self.verdict_text or VERDICT_TEXT.get(self.verdict or "", ""), "exit": code,
               "steps": self.steps, "needs_person": self.needs_person, "notes": self.notes, **self.extra}
        path, k = self.paths.park_dir / f"report-{self.start:%Y%m%d-%H%M%S}.json", 1
        while path.exists():
            path, k = self.paths.park_dir / f"report-{self.start:%Y%m%d-%H%M%S}-{k}.json", k + 1
        write_json(path, rep)
        write_json(self.paths.latest, rep)
        return path


def finish(run: Run, code: int) -> None:
    """The run's end: the verdict line FIRST, then what needs a person, the notes, and where the report is. The log line
    and the report are each written even when the other, or the console, fails (review F12)."""
    run.verdict = run.verdict or PARK_VERDICTS.get(code, "ERROR")
    try:
        run.log(f"DONE: {run.verdict} (exit {code})")
    except Exception:  # noqa: BLE001 - the report is still written and the verdict still printed
        pass
    try:
        where = f"report: {run.write_report(code)}"
    except Exception as e:  # noqa: BLE001 - the verdict is still printed
        where = f"the report could not be written: {type(e).__name__}: {e}"
    try:
        print()
        print(f"{run.verdict}: {run.verdict_text or VERDICT_TEXT.get(run.verdict, '')} (exit {code})")
        for m in run.needs_person:
            print(f"  NEEDS A PERSON: {m}")
        for m in run.notes:
            print(f"  note: {m}")
        print(f"  {where}")
    except (OSError, ValueError):
        pass


def refuse(msg: str) -> int:
    print(f"REFUSED: {msg}")
    print("Nothing was changed.")
    return EXIT_ERROR


def no_deployment(paths: Paths) -> str | None:
    if not paths.deployment.exists():
        return (f"{paths.clone} has no ai-agent/DEPLOYMENT, so it is not the bot tuner's deployment clone (check "
                "--clone)")
    return None


# ----------------------------------------------------------------------------------------------- park: the wait
def check(paths: Paths, env, base: dict) -> dict:
    """park_watch.check: one full look; `stopped_clean` only when EVERY condition holds. Additions: a wait that began
    with no round running (base tag None, and none adopted since) needs state.json `current` still empty; agent.lock
    blocks only while it names a LIVE learner or cannot be read (review F4: a hard-killed learner leaves a lock naming a
    dead PID, which is a crash leftover, so UNEXPECTED stays reachable); and two exits that log no STOP line are clean
    (review F9): the learner's restart into new code (exit 3: run_agent.ps1 then finds STOP), and, for a wait that began
    with no round, a silent STOP exit (sleep_unless_stopped, the adopt wait, the archive wait) with no crash line."""
    r: dict = {"at": ts(env.now())}
    r["stop_file"] = paths.stop.exists()
    r["stop_line"] = last_stop_line(paths.log, base["stop_mtime"])
    r["attention"] = attention_since(paths, base["stop_mtime"])
    r["restart_line"] = last_line_since(paths.log, RESTART_LINE, base["stop_mtime"])
    r["crash_line"] = last_line_since(paths.log, CRASH_LINE, base["stop_mtime"])
    r["lock"] = paths.lock.exists()
    procs = env.processes()
    r["lock_pid"] = read_lock_pid(paths)
    r["lock_live"] = pid_is_learner(r["lock_pid"], procs)
    r["lock_unreadable"] = r["lock"] and r["lock_pid"] is None
    r["learner_alive"] = pid_is_learner(base["pid"], procs)
    r["trainer_procs"] = [short(p) for p in trainer_processes(procs, os.getpid(), paths,
                                                              r["lock_pid"] if r["lock_live"] else None)]
    st = read_json(paths.state)
    if not isinstance(st, dict):
        r["current"], tags = "UNREADABLE", []
    else:
        cur = st.get("current")
        r["current"] = cur.get("tag") if isinstance(cur, dict) else (None if cur is None else "UNREADABLE")
        tags = [c.get("tag") for c in st.get("cycles", []) if isinstance(c, dict)]
    r["in_state_cycles"] = base["tag"] in tags
    last = last_jsonl(paths.cycles) or {}
    r["cycles_last_tag"], r["cycles_last_runs"] = last.get("tag"), last.get("runs")
    r["runs_rows"] = count_rows(paths.runs, base["tag"]) if base["tag"] else None
    r["nothing_running"] = (not r["lock_live"] and not r["lock_unreadable"] and not r["learner_alive"]
                            and not r["trainer_procs"])
    if base["tag"] is None:
        r["recorded"] = r["current"] is None
    else:
        r["recorded"] = (r["current"] is None and r["in_state_cycles"] and r["cycles_last_tag"] == base["tag"]
                         and r["runs_rows"] is not None and r["runs_rows"] == r["cycles_last_runs"])
    r["quiet_exit"] = base["tag"] is None and r["crash_line"] is None
    r["clean_exit"] = (r["stop_line"] is not None or r["attention"] or r["restart_line"] is not None
                       or r["quiet_exit"])
    r["stopped_clean"] = r["stop_file"] and r["nothing_running"] and r["recorded"] and r["clean_exit"]
    return r


def lock_word(r: dict) -> str:
    if r.get("lock_live"):
        return "held"
    if r.get("lock_unreadable"):
        return "unreadable"
    return "dead-pid" if r.get("lock") else "released"


def summary(r: dict) -> str:  # park_watch
    exit_seen = ("stop-line" if r["stop_line"] else "attention" if r["attention"] else
                 "restart" if r.get("restart_line") else "quiet" if r.get("quiet_exit") else "none")
    return (f"stop_line={r['stop_line']} attention={r['attention']} lock={lock_word(r)} "
            f"learner_alive={r['learner_alive']} procs={len(r['trainer_procs'])} current={r['current']} "
            f"recorded={r['recorded']} exit={exit_seen} crash={r.get('crash_line')} "
            f"(cycles_last={r['cycles_last_tag']} runs={r['cycles_last_runs']} rows={r['runs_rows']})")


def timeout_why(last_r: dict | None, deadline: datetime) -> str:
    """Review F4: the TIMEOUT is worded from the LAST look; it never says 'still running' when nothing ran."""
    if last_r is not None and last_r["nothing_running"]:
        state = (f"nothing of the tuner runs at the deadline {ts(deadline)}, but no clean recorded stop was seen "
                 f"({summary(last_r)})")
    else:
        state = f"the tuner was still running at the deadline {ts(deadline)}"
    return (f"{state}; nothing else was changed (STOP stays, so the tuner still stops at its next boundary). To wait "
            f"longer: park --apply --deadline \"YYYY-MM-DD hh:mm:ss AM\"")


def watch(paths: Paths, env, base: dict, deadline: datetime, log, poll: float = POLL_S,
          stable_needed: int = STABLE_LOOKS, unexpected_needed: int = UNEXPECTED_LOOKS, heartbeat_s: float = HEARTBEAT_S,
          deadline_is_default: bool = False) -> tuple[int, dict]:
    """park_watch.watch, its rules unchanged. Additions: (1) when no round ran as the wait began, a round that starts
    during it is ADOPTED as the one to see recorded (the learner sets `current` seconds to minutes after its STOP check:
    an update fetch, a test run), and a default deadline moves to that round's end + 90 min; (2) 'not stopped yet' is
    logged when it changes or at the heartbeat, not on every poll; (3) review F11: a first good look gets its confirming
    look even past the deadline; (4) review F4: the TIMEOUT is worded from the last look."""
    stable = unexpected = 0
    last_beat = None
    last_line = None
    last_r = None
    while True:
        now = env.now()
        if not paths.stop.exists():
            return PARK_CANCELLED, {"why": "the STOP file was removed: the park is CANCELLED; nothing else was changed",
                                    "deadline": ts(deadline)}
        if now >= deadline and stable == 0:
            return PARK_TIMEOUT, {"why": timeout_why(last_r, deadline), "deadline": ts(deadline),
                                  "nothing_running": bool(last_r and last_r["nothing_running"])}
        if base["tag"] is None:
            cur = current_round(paths)
            if cur:
                base["tag"] = cur["tag"]
                log(f"round {cur['tag']} started after the wait began: it must end and be recorded first")
                if deadline_is_default:
                    deadline, why = default_deadline(cur, now)
                    log(f"the deadline moves to {ts(deadline)} ({why})")
        cheap = (last_stop_line(paths.log, base["stop_mtime"]) is not None or not paths.lock.exists()
                 or base["pid"] is None or not env.pid_alive(base["pid"]))
        if cheap:
            r = check(paths, env, base)
            last_r = r
            if r["stopped_clean"]:
                stable += 1
                unexpected = 0
                log(f"stopped and recorded, look {stable} of {stable_needed}: {summary(r)}")
                if stable >= stable_needed:
                    r["deadline"] = ts(deadline)
                    return PARK_PARKED, r
            else:
                stable = 0
                if r["nothing_running"] and r["stop_file"]:
                    unexpected += 1
                    log(f"nothing runs but not a clean recorded stop ({unexpected} of {unexpected_needed}): {summary(r)}")
                    if unexpected >= unexpected_needed:
                        r["why"] = (f"nothing of the tuner runs, but there was no clean recorded stop on "
                                    f"{unexpected_needed} looks ({summary(r)}); nothing else was changed")
                        return PARK_UNEXPECTED, r
                else:
                    unexpected = 0
                    line = f"not stopped yet: {summary(r)}"
                    if line != last_line or last_beat is None or (now - last_beat).total_seconds() >= heartbeat_s:
                        log(line)
                        last_line, last_beat = line, now
        else:
            stable = unexpected = 0  # the learner still holds its lock and lives: this look is not a good one
            last_r = None
            if last_beat is None or (now - last_beat).total_seconds() >= heartbeat_s:
                log(f"waiting: {base['tag'] or 'the learner'} still running (learner pid {base['pid']} alive, lock "
                    f"held); the deadline is {ts(deadline)}")
                last_beat = now
        env.sleep(poll)


# ---------------------------------------------------------------------------------------- park: Windows (5 to 7)
def disable_verified(env, name: str) -> str:  # park_watch, unchanged
    try:
        env.task_disable(name)
        return "OFF" if env.task_enabled(name) is False else "FAILED: still enabled after Disable-ScheduledTask"
    except Exception as e:  # noqa: BLE001 - reported, never raised: the other steps still run
        return f"FAILED: {e}"


def switch_off(env, name: str) -> str:
    """disable_verified, made idempotent: a task already OFF is left as it is, and says so."""
    try:
        if env.task_enabled(name) is False:
            return "already OFF"
    except Exception as e:  # noqa: BLE001
        return f"FAILED: cannot read it: {e}"
    return disable_verified(env, name)


def switch_on(env, name: str) -> str:
    """The resume twin of switch_off: Enable-ScheduledTask, then Settings.Enabled must read True."""
    try:
        if env.task_enabled(name) is True:
            return "already ON"
        env.task_enable(name)
        return "ON" if env.task_enabled(name) is True else "FAILED: still disabled after Enable-ScheduledTask"
    except Exception as e:  # noqa: BLE001
        return f"FAILED: {e}"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_backup(paths: Paths, started: datetime) -> tuple[bool, str]:  # park_watch, unchanged
    st = read_json(paths.backup_status)
    if not st:
        return False, f"no readable {paths.backup_status}"
    try:
        t = datetime.strptime(st["time"], TS_FMT)
    except (KeyError, ValueError, TypeError):
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
                    return False, f"{member} in {zpath.name} differs from the stopped tuner's file"
    except (OSError, KeyError, zipfile.BadZipFile) as e:
        return False, f"cannot verify {zpath}: {e}"
    return True, f"{zpath} ({st.get('bytes')} bytes): runs.jsonl, cycles.jsonl and state.json byte-identical"


def final_backup(run: Run) -> tuple[bool, str]:
    """park_watch.park's backup loop: the nightly task's way, VERIFIED, one retry after 2 minutes."""
    paths, env = run.paths, run.env
    ok, detail = False, ""
    for attempt in (1, 2):
        started = env.now()
        try:
            rc, out = env.run_backup(paths)
        except Exception as e:  # noqa: BLE001
            rc, out = -1, f"{type(e).__name__}: {e}"
        ok, detail = (False, f"exit {rc}: {out.strip()[-400:]}") if rc != 0 else verify_backup(paths, started)
        run.step(f"final backup, attempt {attempt}", ("VERIFIED: " if ok else "FAILED: ") + detail)
        if ok:
            break
        if attempt == 1:
            env.sleep(BACKUP_RETRY_S)
    return ok, detail


def park_windows(run: Run) -> int:
    """Spec 3.2 steps 5 to 7: park_watch.park, made idempotent. Called ONLY after the verified stop (or two looks at a
    stopped tuner): the autostart and the watchdog OFF; ONE final backup, VERIFIED; only then the nightly backup OFF."""
    env = run.env
    for key in ("autostart", "watchdog"):
        res = switch_off(env, TASKS[key])
        run.step(f"switch OFF {TASKS[key]}", res)
        if res not in OFF_OK:
            run.person(f"{TASKS[key]} was not switched off: {res}")
    ok, detail = final_backup(run)
    run.extra["backup"] = {"verified": ok, "detail": detail}
    if ok:
        res = switch_off(env, TASKS["backup"])
        run.step(f"switch OFF {TASKS['backup']}", res)
        if res not in OFF_OK:
            run.person(f"{TASKS['backup']} was not switched off: {res}")
    else:
        run.step(f"switch OFF {TASKS['backup']}", "LEFT ON: the final backup was not verified (the 1 AM run retries)")
        run.person(f"the final backup failed ({detail[:300]}); {TASKS['backup']} was LEFT ON. park --apply again "
                   "retries the backup")
    return park_final(run, already=False)


def parked_text(run: Run) -> str:
    """Review F5: the PARKED line says what was PROVEN about the round (the headline carries the caveat)."""
    kind, tag = run.extra.get("stop_kind"), run.extra.get("stop_round")
    tail = "the final backup is verified, and all three Windows tasks are OFF."
    if kind == "waited" and tag:
        return f"the tuner stopped after round {tag}, which is recorded; {tail}"
    if kind == "waited":
        return f"the tuner stopped between rounds (no round was running); {tail}"
    if kind == "unrecorded":
        return (f"nothing of the tuner runs; round {tag} was left UNRECORDED (the learner scores it at its next start); "
                f"{tail}")
    return f"nothing of the tuner was running, and no round was left unrecorded; {tail}"


def park_final(run: Run, already: bool) -> int:
    """Spec 3.2 step 7: read the three tasks again, check once more that nothing runs and STOP exists, then the verdict."""
    paths, env = run.paths, run.env
    final = {}
    for key, name in TASKS.items():
        try:
            final[key] = "ON" if env.task_enabled(name) else "OFF"
        except Exception as e:  # noqa: BLE001
            final[key] = f"UNREADABLE: {e}"
    run.extra["final_tasks"] = {TASKS[k]: v for k, v in final.items()}
    lk = look(paths, env)
    stop = paths.stop.exists()
    run.step("final look", f"STOP {'in place' if stop else 'MISSING'}; "
                           f"{'tuner processes RUN' if lk['runs'] else 'nothing of the tuner runs'}; "
                           + ", ".join(f"{TASKS[k]} {v}" for k, v in final.items()))
    if not stop:
        run.person("the STOP file is gone after the park")
    if lk["runs"]:
        run.person(f"a tuner process is running after the park: {[short(p) for p in lk['trainer']][:4]}")
    for key, val in final.items():
        if val != "OFF" and not any(TASKS[key] in m for m in run.needs_person):
            run.person(f"{TASKS[key]} reads {val} at the end of the park")
    if lk["lock"] and not lk["learner_alive"]:
        run.note(f"agent.lock names PID {lk['lock_pid']}, which is not a running learner: a crash leftover that the "
                 "learner replaces at its next start")
    if paths.attention.exists() and not any("ATTENTION" in m for m in run.needs_person):
        run.note(f"ATTENTION.md exists ({attention_reason(paths)}): a resume will need a person to fix the cause and "
                 "delete it first")
    if run.needs_person:
        run.verdict = "PARTIAL"
        return PARK_PARTIAL
    run.verdict = "PARKED (it already was)" if already else "PARKED"
    if not already:
        run.verdict_text = parked_text(run)
    return PARK_PARKED


# ------------------------------------------------------------------------------------------------ park: the command
def keep_or_place_stop(run: Run) -> datetime | None:
    """Spec 3.2 step 2. Returns the time STOP counts from (the floor for the learner's STOP line), or None on failure."""
    paths, env = run.paths, run.env
    if paths.stop.exists():
        t = file_time(paths.stop) or env.now()
        run.step("STOP file", f"kept as it was: it was already there (since {ts(t)}; text: "
                              f"{(read_text_head(paths.stop, 160) or '(empty)').strip()!r})")
        return t.replace(microsecond=0)
    placed_at = env.now().replace(microsecond=0)
    try:
        result = place_stop(paths, placed_at)
    except OSError as e:
        run.person(f"the STOP file could not be placed ({e}); nothing else was changed")
        return None
    if not paths.stop.exists():
        run.person("the STOP file is not there after placing it; nothing else was changed")
        return None
    if result == "already there":  # it appeared between the first look and the write: keep it as found
        t = file_time(paths.stop) or placed_at
        run.step("STOP file", f"kept as it was: it appeared meanwhile (since {ts(t)})")
        return t.replace(microsecond=0)
    run.step("STOP file", f"placed at {ts(placed_at)} and verified; the tuner reads it only between rounds, so the "
                          "running round finishes and is recorded first")
    return placed_at


def park_wait(run: Run, f0: dict, floor: datetime, poll: float, deadline_arg: datetime | None) -> int | None:
    """Spec 3.2 steps 3 and 4. Returns an exit code to stop at, or None to go on to park Windows."""
    paths, env = run.paths, run.env
    runs = f0["runs"]
    if not runs:
        for i in range(STABLE_LOOKS):  # step 4: no waiting; two looks a poll apart must show nothing runs
            if i:
                env.sleep(poll)
            lk = look(paths, env)
            if lk["runs"]:
                run.step("look", f"look {i + 1}: the tuner runs now ({[short(p) for p in lk['trainer']][:2]}): waiting "
                                 "for it as for a running round")
                runs = True
                break
            run.step("look", f"look {i + 1} of {STABLE_LOOKS}: nothing of the tuner runs")
        if not runs:
            cur = current_round(paths)
            last = (last_jsonl(paths.cycles) or {}).get("tag")
            if cur:
                run.note(f"round {cur['tag']} was left UNRECORDED (state.json `current` still names it, and nothing of "
                         f"the tuner runs). That is not a reason to stop the park: its data stays on disk and the "
                         f"learner recovers it at its next start (adopt_unfinished). The last recorded round is {last}.")
                run.extra["stop_kind"], run.extra["stop_round"] = "unrecorded", cur["tag"]
            else:
                run.note(f"no round was left unrecorded (state.json `current` is empty; the last recorded round is "
                         f"{last})")
                run.extra["stop_kind"], run.extra["stop_round"] = "not running", last
            return None
    cur = current_round(paths)  # step 3: wait for the clean stop (park_watch.watch + check)
    base = {"tag": cur["tag"] if cur else None, "pid": read_lock_pid(paths), "stop_mtime": floor}
    if deadline_arg is not None:
        deadline, why = deadline_arg, "given with --deadline"
    else:
        deadline, why = default_deadline(cur, env.now())
    run.extra["deadline"] = ts(deadline)
    run.step("wait", f"waiting for {('round ' + base['tag']) if base['tag'] else 'the learner'} to stop by itself "
                     f"(learner pid {base['pid']}); deadline {ts(deadline)} ({why})")
    code, r = watch(paths, env, base, deadline, run.log, poll=poll, deadline_is_default=deadline_arg is None)
    if r.get("deadline"):
        run.extra["deadline"] = r["deadline"]
    run.extra["wait"] = {k: r.get(k) for k in ("why", "stop_line", "attention", "recorded", "current",
                                               "cycles_last_tag", "runs_rows")}
    if code != PARK_PARKED:
        run.step("wait", r.get("why", "?"))
        run.verdict = PARK_VERDICTS[code]
        if code == PARK_TIMEOUT:
            run.verdict_text = (("nothing of the tuner runs at the deadline, but no clean recorded stop was seen. "
                                 if r.get("nothing_running") else "the tuner was still running at the deadline. ")
                                + "Nothing else was changed: STOP stays, so the tuner still stops at its next "
                                "boundary; run park --apply again later to finish (with --deadline if the round "
                                "overran).")
        return code
    run.step("wait", f"stopped cleanly and recorded on {STABLE_LOOKS} looks: {summary(r)}")
    run.extra["stop_kind"], run.extra["stop_round"] = "waited", base["tag"]
    if r["attention"]:
        run.person(f"the learner wrote ATTENTION.md as it stopped: {attention_reason(paths)}")
    return None


def park_apply(run: Run, no_wait: bool, poll: float, deadline_arg: datetime | None) -> int:
    paths, env = run.paths, run.env
    f0 = gather(paths, env)
    v0 = verdict(f0)
    run.extra["before"] = brief(f0, v0)
    run.step("status at the start", v0)
    if v0 == "PARKED":  # IDEMPOTENT: verify and say so; no second backup
        return park_final(run, already=True)
    floor = keep_or_place_stop(run)
    if floor is None:
        run.verdict = "ERROR"
        return EXIT_ERROR
    if no_wait:
        why = ("it stops by itself after its round" if f0["runs"] else "it is not running now")
        run.step("--no-wait", f"returning now with no task touched ({why}); park --apply again finishes the park")
        run.verdict = "PENDING"
        return PARK_PENDING
    if not set_tool_lock_phase(paths, "waiting"):
        run.note("the park tool's lock could not record 'waiting', so a resume --apply cannot cancel this park while "
                 "it waits (deleting STOP by hand still does)")
    code = park_wait(run, f0, floor, poll, deadline_arg)
    if code is not None:
        return code
    if not paths.stop.exists():  # review F1: a cancel that came after the wait's last look: no task is touched
        run.step("STOP file", "gone before any task was switched off: the park is CANCELLED; nothing else was changed")
        run.verdict = "CANCELLED"
        return PARK_CANCELLED
    set_tool_lock_phase(paths, "parking")
    return park_windows(run)


def cmd_park_apply(paths: Paths, env, a) -> int:
    why = no_deployment(paths)
    if why:
        return refuse(why)
    deadline_arg = None
    if a.deadline:
        deadline_arg = parse_ts(a.deadline)
        if deadline_arg is None:
            return refuse(f"--deadline {a.deadline!r} is not in the form \"YYYY-MM-DD hh:mm:ss AM\"")
    ok, note = acquire_tool_lock(paths, env, "park --apply", a.poll)
    if not ok:
        return refuse(note)
    try:
        run, code = Run(paths, env, "park --apply"), EXIT_ERROR
    except BaseException:  # its first log line could not be written: never leave the lock behind
        release_tool_lock(paths)
        raise
    try:
        if note:
            run.note(note)
        code = park_apply(run, a.no_wait, a.poll, deadline_arg)
    except KeyboardInterrupt:  # a 12-hour wait may be stopped by hand: say so, release the lock, keep STOP
        run.person("INTERRUPTED by Ctrl+C. STOP stays (the tuner still stops at its boundary); park --apply again "
                   "continues from where things are")
        run.verdict, code = "INTERRUPTED", EXIT_ERROR
    except Exception:  # noqa: BLE001 - the report must say WHY
        run.person("INTERNAL ERROR:\n" + traceback.format_exc()[-1500:])
        run.verdict, code = "ERROR", EXIT_ERROR
    finally:
        try:
            finish(run, code)
        finally:
            release_tool_lock(paths)  # whatever happened above, the next run must not find a held lock
    return code


def park_plan(f: dict, no_wait: bool, deadline_arg: datetime | None) -> tuple[list[str], str]:
    now, v, rnd = f["now"], verdict(f), round_facts(f["current"])
    if v == "PARKED":
        return (["check the clone and take the park tool's lock",
                 "verify the park (STOP in place, nothing runs, all three tasks OFF) and say so: no backup, no change"],
                "at once")
    steps = ["check the clone (ai-agent/DEPLOYMENT) and take the park tool's lock (one park or resume at a time)"]
    if f["stop"]:
        steps.append(f"keep the STOP file already there (since {hm(f['stop_time'], now)})")
    else:
        steps.append("place the STOP file (the tuner reads it only BETWEEN rounds: the running round is never cut short)")
    if no_wait:
        steps.append("stop there (--no-wait): exit 11 PENDING, no task touched; park --apply again finishes the park")
        return steps, "at once (the park itself finishes on a later park --apply)"
    if f["runs"]:
        deadline, why = (deadline_arg, "given with --deadline") if deadline_arg else default_deadline(f["current"], now)
        what = (f"round {rnd['tag']} to end (about {hm(rnd['ends'], now)})" if rnd and rnd["ends"]
                else "the learner to stop at its next boundary")
        steps.append(f"wait for {what}, then verify the clean stop on two looks a minute apart (the STOP line in "
                     "learner.log, the learner gone, no live learner holding its lock, no batch or lane, the round "
                     f"recorded in state.json, cycles.jsonl and runs.jsonl); give up at {hm(deadline, now)} ({why}) "
                     "with TIMEOUT and nothing else changed. ⚠ This wait runs IN THE FOREGROUND: run park --apply "
                     "detached, or run park --apply --no-wait now and park --apply after the round")
    else:
        steps.append("look twice, a minute apart, that nothing of the tuner runs (no round to wait for)")
    for key in ("autostart", "watchdog"):
        steps.append(f"switch OFF {TASKS[key]} and verify it" if f["tasks"][key]["enabled"] is not False
                     else f"{TASKS[key]}: already OFF (checked, left as it is)")
    steps.append("run ONE final backup the nightly task's way and verify it (exit 0, a fresh ok status, and runs.jsonl, "
                 "cycles.jsonl and state.json in the zip byte-identical to the stopped tuner's); retry once after 2 min")
    steps.append(f"only after a VERIFIED backup: switch OFF {TASKS['backup']} and verify it (a failed backup leaves it "
                 "ON, and the 1 AM run retries)")
    steps.append("read the three tasks again, check nothing runs and STOP is in place, write the report, print the "
                 "verdict")
    if f["runs"] and rnd and rnd["ends"]:
        return steps, f"about {hm(rnd['ends'] + timedelta(minutes=10), now)} (the round's end plus scoring and the backup)"
    return steps, "within a few minutes" if not f["runs"] else "after the learner stops (unknown)"


def cmd_park_dry(paths: Paths, env, a) -> int:
    deadline_arg = parse_ts(a.deadline) if a.deadline else None
    if a.deadline and deadline_arg is None:
        print(f"--deadline {a.deadline!r} is not in the form \"YYYY-MM-DD hh:mm:ss AM\"")
        return EXIT_ERROR
    f = gather(paths, env)
    v = verdict(f)
    for line in status_lines(f, v):
        print(line)
    print()
    if not f["deployment"]:
        print("DRY RUN of park: park --apply would REFUSE this clone (no ai-agent/DEPLOYMENT). Nothing was changed.")
        return 0
    if f["tool_lock"] is not None and not f["tool_lock"].get("stale"):
        print(f"DRY RUN of park: park --apply would REFUSE now: {tool_lock_text(f['tool_lock'])}. Nothing was changed.")
        return 0
    steps, finish_at = park_plan(f, a.no_wait, deadline_arg)
    print("DRY RUN of park: nothing was changed. `park --apply` would:")
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")
    print(f"It would finish {finish_at}.")
    return 0


# ---------------------------------------------------------------------------------------------------------- resume
def delete_stop_verified(run: Run) -> bool:
    try:
        remove_stop(run.paths)
    except OSError as e:
        run.person(f"the STOP file could not be deleted ({e})")
        return False
    if run.paths.stop.exists():
        run.person("the STOP file is still there after deleting it")
        return False
    run.step("STOP file", "deleted; verified gone")
    return True


def switch_on_all(run: Run) -> bool:
    ok = True
    for name in TASKS.values():
        res = switch_on(run.env, name)
        run.step(f"switch ON {name}", res)
        if res not in ON_OK:
            run.person(f"{name} was not switched on: {res}")
            ok = False
    return ok


def start_allowed(paths: Paths, env) -> tuple[bool, str]:
    """Spec 3.3 step 4d, R5: the start is NEVER called while STOP exists or before the three tasks read ON. Re-read here,
    the tasks first and STOP last, right before the start."""
    off = []
    for name in TASKS.values():
        try:
            if env.task_enabled(name) is not True:
                off.append(name)
        except Exception as e:  # noqa: BLE001
            off.append(f"{name} (unreadable: {e})")
    if paths.stop.exists():
        return False, "the STOP file exists"
    if off:
        return False, f"not ON: {', '.join(off)}"
    return True, ""


def end_idle_window(run: Run) -> bool:
    """Spec 3.3 step 4a: the old window is ended ONLY with the full proof that it is idle (taken again here, after STOP
    and the enables), then verified gone; then a last look must find nothing of the tuner that started meanwhile."""
    paths, env = run.paths, run.env
    proven, why, windows = idle_window_proof(paths, env, env.processes())
    if not proven:
        run.person(f"the old tuner window could NOT be proven idle the second time, so it was not ended: "
                   f"{'; '.join(why)}. STOP is in place and the tasks are ON, so nothing starts; resume --apply again "
                   "once nothing of the tuner runs")
        return False
    pids = [w.get("ProcessId") for w in windows]
    run.step("old window", f"proven idle (PIDs {pids}: no learner, batch or lane; no live agent.lock; no child but "
                           "conhost.exe): ending it with Stop-ScheduledTask while STOP is in place")
    try:
        env.task_stop(TASKS["autostart"])
    except Exception as e:  # noqa: BLE001
        run.person(f"Stop-ScheduledTask {TASKS['autostart']} failed: {e}. Nothing more was changed")
        return False
    waited = 0.0
    while True:
        try:
            state = env.task_info(TASKS["autostart"])["state"]
        except Exception as e:  # noqa: BLE001
            state = f"UNREADABLE ({e})"
        left = [p.get("ProcessId") for p in window_processes(env.processes(), paths) if p.get("ProcessId") in pids]
        if state != "Running" and not left:
            break
        if waited >= WINDOW_GONE_S:
            run.person(f"after Stop-ScheduledTask the task reads {state} and window process(es) {left} remain: close "
                       "the old tuner window by hand, or log off and on. Nothing more was changed")
            return False
        env.sleep(WINDOW_POLL_S)
        waited += WINDOW_POLL_S
    lk = look(paths, env)  # review F8: a learner that started in the last moment is never started on top of
    if lk["runs"] or lk["lock_unreadable"]:
        run.person(f"a tuner process appeared while the old window was being ended "
                   f"({[short(p) for p in lk['trainer']][:3]}, agent.lock {lk['lock_pid']}): it may have been ended "
                   "with the window or left without one. Nothing more was done: STOP stays in place; resume --apply "
                   "again once nothing of the tuner runs")
        return False
    run.step("old window", f"ended: the task reads {state} and the window is gone; nothing of the tuner started")
    return True


def verify_start(run: Run, offset: int) -> int:
    """Spec 3.3 step 4e: a NEW `learner started` line (only log bytes after `offset`, taken when the resume began) and
    agent.lock naming a live learner within 180 s; then the round's `starting N lanes` line within 10 minutes."""
    paths, env = run.paths, run.env
    t0 = env.now()
    while True:
        line = last_match(START_LINE, log_since(paths, offset))
        lk = look(paths, env)
        if line and lk["learner_alive"]:
            run.step("start check", f"a NEW 'learner started' line ({line['ts']}) and agent.lock names the live learner "
                                    f"PID {lk['lock_pid']}")
            break
        if (env.now() - t0).total_seconds() >= START_CHECK_S:
            seen = (f"a new 'learner started' line: {'yes' if line else 'NO'}; agent.lock: {lk['lock_pid']} "
                    f"({'a live learner' if lk['learner_alive'] else 'not a live learner'})")
            run.person(f"no start seen within {START_CHECK_S / 60:.0f} minutes ({seen}). Is the old tuner window still "
                       "open? Log off and on, or run ai-agent\\run_agent.ps1. Nothing was undone: the tasks stay ON "
                       "and STOP stays deleted")
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        env.sleep(START_POLL_S)
    t1 = env.now()
    while True:
        m = last_match(ROUND_LINE, log_since(paths, offset))
        if m:
            run.step("round", f"{m['tag']}: starting {m['lanes']} lanes for {m['minutes']} minutes (logged {m['ts']})")
            run.verdict = "RESUMED"
            return RESUME_OK
        if paths.attention.exists():
            run.person(f"the learner paused itself after the start: ATTENTION.md says: {attention_reason(paths)}")
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        if (env.now() - t1).total_seconds() >= ROUND_CHECK_S:
            lk = look(paths, env)
            said = " | ".join(log_tail(paths, 3))
            if lk["learner_alive"]:
                run.note(f"the learner runs (PID {lk['lock_pid']}) but no round started within "
                         f"{ROUND_CHECK_S / 60:.0f} minutes; the log says: {said}")
                run.verdict = "RESUMED"
                return RESUME_OK
            run.person(f"the learner started but no longer runs, and no round started; the log says: {said}")
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        env.sleep(ROUND_POLL_S)


def stop_floor_of(paths: Paths) -> datetime | None:
    t = file_time(paths.stop)
    return t.replace(microsecond=0) if t is not None else None


def wait_learner_gone(run: Run) -> bool:
    """A learner that logged its STOP line is ending (exit 0): wait, bounded, for it and anything of the tuner to go."""
    waited = 0.0
    while True:
        lk = look(run.paths, run.env)
        if not lk["learner_alive"] and not lk["runs"]:
            run.step("learner", "it has exited at its round's end")
            return True
        if waited >= LEARNER_EXIT_S:
            run.person(f"the learner logged its STOP line but still runs after {LEARNER_EXIT_S / 60:.0f} minutes "
                       f"({[short(p) for p in lk['trainer']][:3]}): nothing more was done; resume --apply again once it "
                       "has exited")
            return False
        run.env.sleep(LEARNER_EXIT_POLL_S)
        waited += LEARNER_EXIT_POLL_S


def restart_stopping_learner(run: Run, line: str, offset: int) -> int:
    """The learner has found STOP (its STOP line `line`): it ends at its round's end with exit 0, and run_agent.ps1 does
    not restart it. A cancel then means: wait for it to exit, and start it again the step-4 way."""
    run.step("learner", f"it had already found STOP (its STOP line: {line}): it is ending at its round's end, and "
                        "run_agent.ps1 does not restart a learner that stopped on STOP; waiting for it to exit, then "
                        "starting it again")
    if not wait_learner_gone(run):
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    return resume_from_stopped(run, gather(run.paths, run.env), offset)


def resume_while_running(run: Run, f0: dict, offset: int, floor: datetime | None, cancelled: bool) -> int:
    """Spec 3.3 step 3, chosen because the clone's LEARNER runs (review F2: a batch or lane alone does not choose it):
    delete STOP (it CANCELS the park), switch ON any task that is OFF, check the learner still runs. NEVER start
    anything. A learner that has already found STOP (its STOP line, at/after STOP's time, is in the log) is stopping at
    its round's end and run_agent.ps1 will not restart it: it is waited for, then started again the step-4 way."""
    paths, env = run.paths, run.env
    line = last_stop_line(paths.log, floor) if floor is not None else None
    if line is None and f0["stop"]:
        if not delete_stop_verified(run):
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        env.sleep(SETTLE_S)  # a learner that found STOP in the moment before the delete has logged it by now
        line = last_stop_line(paths.log, floor) if floor is not None else None
    if line is not None:
        return restart_stopping_learner(run, line, offset)
    if not switch_on_all(run):
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    lk = look(run.paths, run.env)
    if not lk["learner_alive"]:
        line = last_stop_line(paths.log, floor) if floor is not None else None
        if line is not None:  # its STOP line came late (a slow write): it found STOP before the delete all the same
            return restart_stopping_learner(run, line, offset)
        tail = " | ".join(log_tail(paths, 3)) or "(empty)"
        run.person(f"the learner stopped during this resume without a STOP line (agent.lock: {lk['lock_pid']}); "
                   f"nothing was started. The log's last lines: {tail}. Run status; resume --apply again starts it "
                   "once nothing of it runs")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    run.step("learner", f"still running (PID {lk['lock_pid']}); nothing was started")
    run.verdict = "PARK CANCELLED" if (f0["stop"] or cancelled) else "TASKS ON"
    return RESUME_OK


def resume_from_stopped(run: Run, f0: dict, offset: int) -> int:
    """Spec 3.3 step 4: nothing of the learner runs. The old window is ended only after a proof taken before any change
    and only while STOP exists (review F8: run_agent.ps1 checks STOP before every learner start, so a crash wait that
    ends during the Stop starts nothing); the tasks are switched ON first, still under STOP (so the Stop never has to
    work on a DISABLED task); then STOP is deleted, the start, and the start check."""
    paths, env = run.paths, run.env
    window_open = f0["tasks"]["autostart"]["state"] == "Running"
    if window_open:
        proven, why, _w = idle_window_proof(paths, env, f0["procs"])
        if not proven:
            run.person(f"the old tuner window is open ({TASKS['autostart']} reads Running) and could NOT be proven idle, "
                       f"so nothing was changed: {'; '.join(why)}. Run resume --apply again once nothing of the tuner "
                       "runs (status shows what runs)")
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        if not paths.stop.exists():
            try:
                placed = place_stop(paths, env.now().replace(microsecond=0), by="resume --apply")
            except OSError as e:
                run.person(f"the STOP file could not be placed to end the old window safely ({e}); nothing else was "
                           "changed")
                run.verdict = "NEEDS PERSON"
                return RESUME_NEEDS_PERSON
            if not paths.stop.exists():
                run.person("the STOP file is not there after placing it; nothing else was changed")
                run.verdict = "NEEDS PERSON"
                return RESUME_NEEDS_PERSON
            run.extra["window_stop"] = placed
            run.step("STOP file", f"{placed} for a moment: the old window is ended only while STOP exists (a learner "
                                  "start that races it exits at once); it is deleted again before the start")
            env.sleep(SETTLE_S)  # a run_agent.ps1 that passed its STOP check just before is seen with its child now
    if not switch_on_all(run):
        if run.extra.get("window_stop"):
            run.note("the STOP file this resume placed for the old window stays in place, so nothing starts; resume "
                     "--apply again finishes the resume")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    if window_open and not end_idle_window(run):
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    if run.paths.stop.exists() and not delete_stop_verified(run):
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    allowed, why = start_allowed(run.paths, run.env)
    if not allowed:
        run.person(f"the tuner was NOT started: {why}")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    try:
        run.env.task_start(TASKS["autostart"])
    except Exception as e:  # noqa: BLE001
        run.person(f"Start-ScheduledTask {TASKS['autostart']} failed: {e}")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    run.step("start", f"Start-ScheduledTask {TASKS['autostart']}")
    return verify_start(run, offset)


def resume_apply(run: Run, floor: datetime | None = None, cancelled: bool = False) -> int:
    paths, env = run.paths, run.env
    offset = log_size(paths)  # FIRST: only learner.log bytes written after this count as a new start (R6)
    f0 = gather(paths, env)
    v0 = verdict(f0)
    run.extra["before"] = brief(f0, v0)
    run.step("status at the start", v0)
    if f0["attention"]:
        run.person(f"ATTENTION.md says: {f0['attention_reason']}. Nothing was changed: the tuner will not start until a "
                   "person fixes the cause and deletes ATTENTION.md")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    if v0 == "RUNNING" and not cancelled:
        run.step("resume", "already running: nothing was changed")
        run.verdict = "ALREADY RUNNING"
        return RESUME_OK
    floor = floor if floor is not None else stop_floor_of(paths)
    if f0["learner_alive"]:  # review F2: the LEARNER chooses step 3 (not any batch, lane or other checkout's process)
        return resume_while_running(run, f0, offset, floor, cancelled)
    return resume_from_stopped(run, f0, offset)


def cancel_waiting_park(run: Run, holder: dict) -> int:
    """Review F1: a park --apply WAITING for the round holds the lock. Cancel that park the way it was built to be
    cancelled: delete STOP (its wait then ends as CANCELLED and it changes nothing else), wait for it to release the
    lock (its poll + 90 s), take the lock, and go on as resume --apply. ATTENTION.md -> nothing is changed."""
    paths, env = run.paths, run.env
    pid = holder.get("pid")
    run.step("park tool lock", f"held by a park --apply that WAITS for the round (PID {pid}, since "
                               f"{holder.get('since')}): this resume cancels that park")
    if paths.attention.exists():
        run.person(f"ATTENTION.md says: {attention_reason(paths)}. Nothing was changed (the waiting park was NOT "
                   "cancelled): the tuner will not start until a person fixes the cause and deletes ATTENTION.md")
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    floor = stop_floor_of(paths)
    if not delete_stop_verified(run):
        run.verdict = "NEEDS PERSON"
        return RESUME_NEEDS_PERSON
    poll = holder.get("poll")
    limit = (float(poll) if isinstance(poll, (int, float)) and not isinstance(poll, bool) and poll > 0 else POLL_S) \
        + CANCEL_MARGIN_S
    waited = 0.0
    while True:
        if not paths.tool_lock.exists() or not env.pid_alive(pid):
            ok, note = acquire_tool_lock(paths, env, "resume --apply")
            if ok:
                run.step("park tool lock", "the waiting park ended and released its lock; this resume holds it now"
                         + (f" ({note})" if note else ""))
                run.extra["cancelled_park"] = pid
                return resume_apply(run, floor=floor, cancelled=True)
        if waited >= limit:
            run.person(f"the waiting park --apply (PID {pid}) did not end within {limit:.0f} s after STOP was deleted "
                       "(it may have gone past its wait). STOP stays deleted, so the tuner does not stop at its "
                       "boundary; run status, and resume --apply again after that park --apply has ended")
            run.verdict = "NEEDS PERSON"
            return RESUME_NEEDS_PERSON
        env.sleep(CANCEL_POLL_S)
        waited += CANCEL_POLL_S


def cmd_resume_apply(paths: Paths, env, a) -> int:
    why = no_deployment(paths)
    if why:
        return refuse(why)
    ok, note = acquire_tool_lock(paths, env, "resume --apply")
    holder = None
    if not ok:
        holder = waiting_park(paths, env)  # review F1: a WAITING park is cancelled, not refused
        if holder is None:
            return refuse(note)
    try:
        run, code = Run(paths, env, "resume --apply"), EXIT_ERROR
    except BaseException:
        if ok:
            release_tool_lock(paths)
        raise
    try:
        if note and ok:
            run.note(note)
        code = cancel_waiting_park(run, holder) if holder is not None else resume_apply(run)
    except KeyboardInterrupt:
        run.person("INTERRUPTED by Ctrl+C; resume --apply again continues from where things are")
        run.verdict, code = "INTERRUPTED", EXIT_ERROR
    except Exception:  # noqa: BLE001
        run.person("INTERNAL ERROR:\n" + traceback.format_exc()[-1500:])
        run.verdict, code = "ERROR", EXIT_ERROR
    finally:
        try:
            finish(run, code)
        finally:
            release_tool_lock(paths)  # only a lock this run holds (it may never have taken one)
    return code


def resume_plan(paths: Paths, env, f: dict) -> list[str]:
    v = verdict(f)
    if f["attention"]:
        return [f"change NOTHING: ATTENTION.md says: {f['attention_reason']}. The tuner will not start until a person "
                "fixes the cause and deletes ATTENTION.md (exit 10, NEEDS PERSON)"]
    lockv = f["tool_lock"]
    steps = []
    cancelling = False
    if lockv is not None and not lockv.get("stale"):
        if not (is_waiting_park(lockv) and f["stop"]):
            return [f"REFUSE: {tool_lock_text(lockv)}; nothing would be changed"]
        cancelling = True
        steps.append(f"cancel the park --apply that WAITS for the round (PID {lockv.get('pid')}): delete STOP (its wait "
                     "then ends as CANCELLED and it changes nothing else), wait for it to release the park tool's lock, "
                     "and take it")
    elif v == "RUNNING":
        return ["nothing: it is already running (exit 0)"]
    else:
        steps.append("check the clone (ai-agent/DEPLOYMENT) and take the park tool's lock")
    stop = f["stop"] and not cancelling  # a cancel deletes STOP first
    off = [TASKS[k] for k, t in f["tasks"].items() if t["enabled"] is not True]
    if f["learner_alive"]:
        if stop:
            steps.append("delete the STOP file and verify it is gone: this CANCELS the pending park (a learner that has "
                         "already found STOP is waited for and then started again)")
        steps.append(f"switch ON {', '.join(off)} and verify" if off else "the three tasks are already ON: leave them")
        steps.append("check the learner is still alive; start NOTHING (it is running)")
        return steps
    window_open = f["tasks"]["autostart"]["state"] == "Running"
    if window_open:
        proven, why, _w = idle_window_proof(paths, env, f["procs"])
        if not proven:
            steps.append(f"stop there: the old tuner window is open and could NOT be proven idle ({'; '.join(why)}): "
                         "NEEDS PERSON, nothing changed")
            return steps
        if not stop:
            steps.append("place the STOP file for a moment (the old window is ended only while STOP exists, so a "
                         "learner start that races it exits at once)")
    steps.append(f"switch ON {', '.join(off)} and verify" if off else "the three tasks are already ON: leave them")
    if window_open:
        steps.append(f"end the old idle tuner window (Stop-ScheduledTask {TASKS['autostart']}): it is proven idle now, "
                     "and the proof is taken again first; then verify the window is gone and nothing of the tuner "
                     "started meanwhile")
    if stop or window_open:
        steps.append("delete the STOP file and verify it is gone")
    steps.append(f"start {TASKS['autostart']} (never while STOP exists or before the three tasks read ON)")
    steps.append("verify within 3 minutes a NEW 'learner started' line in learner.log and agent.lock naming a live "
                 "learner; then wait up to 10 minutes for the round's 'starting N lanes' line")
    return steps


def cmd_resume_dry(paths: Paths, env, a) -> int:
    f = gather(paths, env)
    v = verdict(f)
    for line in status_lines(f, v):
        print(line)
    print()
    if not f["deployment"]:
        print("DRY RUN of resume: resume --apply would REFUSE this clone (no ai-agent/DEPLOYMENT). Nothing was changed.")
        return 0
    print("DRY RUN of resume: nothing was changed. `resume --apply` would:")
    for i, s in enumerate(resume_plan(paths, env, f), 1):
        print(f"  {i}. {s}")
    return 0


def cmd_status(paths: Paths, env) -> int:
    f = gather(paths, env)
    v = verdict(f)
    for line in status_lines(f, v):
        print(line)
    return STATUS_CODES[v]


# ------------------------------------------------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="park_tuner.py", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Read the module docstring for every step and exit code.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--clone", type=Path, default=DEFAULT_CLONE, help="the deployment clone (default: %(default)s)")
    common.add_argument("--ops-dir", type=Path, default=DEFAULT_OPS, help="the ops folder (default: %(default)s)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("status", parents=[common], help="one screen, the verdict first (read-only)")
    p = sub.add_parser("park", parents=[common], help="DRY RUN unless --apply")
    p.add_argument("--apply", action="store_true", help="really park (only when the user asked for a park)")
    p.add_argument("--no-wait", action="store_true", help="only place STOP and return PENDING (exit 11)")
    p.add_argument("--deadline", default=None, help='give up waiting at "YYYY-MM-DD hh:mm:ss AM" (TIMEOUT, exit 20)')
    p.add_argument("--poll", type=float, default=POLL_S, help="seconds between looks while waiting (default 60)")
    r = sub.add_parser("resume", parents=[common], help="DRY RUN unless --apply")
    r.add_argument("--apply", action="store_true", help="really resume (only when the user asked for a resume)")
    return ap


def main(argv: list[str] | None = None, env=None) -> int:
    a = build_parser().parse_args(argv)
    if getattr(a, "poll", 1.0) <= 0:
        print("--poll must be above 0")
        return EXIT_ERROR
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        try:  # a path the console code page cannot encode must not turn a report line into a crash
            sys.stdout.reconfigure(errors="backslashreplace")
        except (ValueError, OSError):
            pass
    env = RealEnv() if env is None else env
    try:
        paths = Paths(a.clone, a.ops_dir)  # inside the try: --clone's spellings come from Windows' own name lookups
        if a.command == "status":
            return cmd_status(paths, env)
        if a.command == "park":
            return cmd_park_apply(paths, env, a) if a.apply else cmd_park_dry(paths, env, a)
        return cmd_resume_apply(paths, env, a) if a.apply else cmd_resume_dry(paths, env, a)
    except Exception:  # noqa: BLE001 - say why, with the "error" code
        print("INTERNAL ERROR (nothing more was done):")
        print(traceback.format_exc()[-2000:])
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
