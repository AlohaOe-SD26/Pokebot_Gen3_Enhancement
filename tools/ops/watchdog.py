"""The learner's session-free watchdog (backlog O1, build spec S1-4): one status file on the Desktop, and a Windows
notification ONLY when the state changes.

WHY THIS EXISTS. The 24/7 bot tuner (`ai-agent/` in the deployment clone `C:/Remote Projects/pokebot-learner`) runs with
no Claude session and no human watching. Every way it stops is SILENT today: the learner process dies, it pauses itself
by writing `findings/ATTENTION.md`, a batch hangs, the disk fills, the nightly backup refuses or goes quiet, or the
archiver (O3) HOLDS a cycle for a human. Without this, each one is found only when someone happens to run
`tools/status.py`, possibly days later. The scheduled task `Pokebot-Ops-Watchdog` runs `watchdog.ps1` every 30 minutes;
that runs this file, and toasts what it asks for.

DESIGN, AND THE REASON FOR EACH PART
- READ-ONLY ON THE CLONE. It never writes under the clone (a tracked change there silently stops the clone's
  auto-update, spec fact 2): every path it writes is checked against the clone by NAME and by file IDENTITY, and a run
  told to write there is REFUSED (exit 2) before anything is written. The task runs it with `-B`, so no `__pycache__`
  appears either. It imports NOTHING from the learner, so a learner change can never break its own watchdog.
- `state.json`, `config.json` and the backup status are read in ONE call that closes at once (`Path.read_bytes`): on
  Windows an open handle makes the learner's `tmp.replace(state.json)` fail (measured for the backup tool, 2026-10-21).
  `state.json` is read ONCE per run and shared by the checks that need it. `learner.log` is stat()ed; it is opened
  only when the no-progress check fires, for one short read of its tail (the learner only ever APPENDS to it, which a
  reader in Python's default share mode never blocks).
- THRESHOLDS COME FROM THE CLONE'S `config.json` (and the running batch's own length in state.json), never from here:
  the stuck limit is `max(cycle_minutes, current.minutes) + 60` (the log is silent for a whole batch, so a fixed limit
  would cry wolf the day O2 lengthens a cycle), the disk alarm is
  `min_free_gb + early_prune_margin_gb` (so the alarm and O7's early archive fire at the same line: 25 + 15 = 40 GB
  today). A key ABSENT from config.json takes the learner's own documented default (`LEARNER_DEFAULTS`: cycle_minutes
  720, min_free_gb 25, early_prune_margin_gb 15), because the learner merges its DEFAULTS under config.json and still
  enforces a missing key; selftest W14 pins these three values against the main checkout's `learner.DEFAULTS`. Disk is
  measured in GiB (2**30), the learner's own unit for `min_free_gb`. A config that cannot be READ is itself NEEDS YOU
  (the learner re-reads it every cycle and would fail the same way), and the threshold checks then say SKIPPED.
- THE STATE. Line 1 is `OK`, `NOTE: <why>` (nothing for the user to do: the user's own STOP file, a pending Windows
  restart, a recent boot or restart) or `NEEDS YOU: <why>`. Line 2 is `checked 12:30 PM PT, next 1:00 PM` (12-hour Los
  Angeles time, the user's format). The detail lines and the restart command follow.
- THE CHECKS. (1) The learner process: a process whose argv names THIS clone's `learner.py` (the relative argument is
  resolved against the process's own working folder) with `run` or `once`. A process that merely mentions those words,
  or runs ANOTHER checkout's learner, is not it. Missing -> re-checked once after 90 s (the learner's exit-code-3
  restart into new code is a blink) -> NEEDS YOU, unless the STOP file exists (NOTE) or the user LOGGED ON under 15
  minutes ago (NOTE: the autostart task waits 2 minutes after LOGON, which can come long after boot when nobody is at
  the PIN screen; the logon time is psutil.users()'s newest session of this user, and the boot time when there is
  none). A learner that was NEEDS YOU "not running" counts as recovered only when 2 checks IN A ROW find it alive
  (`alive_streak` in the state; a crash loop restarts it every 10 minutes and would otherwise flap); until then it
  stays NEEDS YOU, saying it runs again. (2) `findings/ATTENTION.md` -> NEEDS YOU with its reason line. (3) Stuck:
  `learner.log` older than `max(cycle_minutes, current.minutes) + 60` while the learner is alive (the RUNNING batch's
  own length counts: config is re-read per cycle, so a shortened cycle_minutes must not call a long batch stuck).
  (3b) NO PROGRESS while the learner is alive and its log is fresh (it logs "waiting 15 min" every 15 minutes while it
  starts nothing, e.g. too little free RAM for 8 lanes, or another batch running): `state.current` is None and the
  newest cycle FINISHED over `cycle_minutes + 120` min ago, or `state.current` STARTED over
  `max(cycle_minutes, current.minutes) + 120` min ago -> NEEDS YOU naming how long, with learner.log's last line.
  (4) Disk: under the alarm, or a fall of over 10 GB in 6 h -> NEEDS YOU; otherwise a forecast line (least squares
  over up to 72 h, at least 12 samples). The alarm has HYSTERESIS: once raised it clears only above alarm + 2 GB, so
  a disk hovering at the line (O7 archives right there) does not flap. The backup disk's free-space probe is bounded
  to 10 s (a sleeping or failing USB disk must not hang the task into its 5-minute kill). (5) A pending Windows
  restart -> NOTE. (6) The boot time moved (by over 2 minutes: psutil's boot time wobbles) since the last sample ->
  NOTE until 6 h after that boot, with the downtime (and whether Windows logged an unexpected shutdown, event 41,
  best effort). (7) The backup tool's `backup_status.json`: missing, ok false (its REFUSED / NEEDS-YOU / FAILED
  error, quoted) or older than 36 h -> NEEDS YOU. (8) A cycle the archiver HELD for review (`"held"` on a cycle in
  `data/state.json`; the learner then touches nothing of it until a human resolves it) -> NEEDS YOU naming the tags.
  Each check is wrapped: one that raises becomes a NEEDS YOU line naming it, and the others still run.
- NOTIFY ONLY WHEN A NEW PROBLEM APPEARS (alert fatigue is how a watchdog gets ignored). `watchdog_state.json` keeps
  the ids (and texts) of the NEEDS checks: a NEW id joining the set -> one toast; the same set, or a SHRINKING one ->
  no toast (a shrink writes 'resolved since the last check: X; still NEEDS YOU: Y' into the file), but one reminder
  per 24 h while any NEEDS YOU persists; the set emptying -> one "recovered" toast; OK <-> NOTE -> none. The toast
  itself is shown by `watchdog.ps1` (Windows PowerShell 5.1's ToastNotificationManager; Win11 Home has no msg.exe):
  this file prints one `NOTIFY<TAB>title<TAB>body` line per toast. The state is saved BEFORE the toast is shown, so a
  toast that fails to show is not retried; the status file still carries the state. When the state CANNOT be saved,
  the same record goes to a marker file (`watchdog_state.failed.json`) and the next run reads whichever of the two is
  newer, so an unwritable state file does not turn into a NEEDS YOU toast every 30 minutes; the status file says so.
- SAMPLES `{t, free_gb_c, free_gb_backup, alive, boot}` go to `samples.jsonl` in the OPS folder
  (`%LOCALAPPDATA%/pokebot-ops`), trimmed to 14 days and rewritten atomically: outside the clone, so they survive a
  wiped clone, and inside what the nightly backup captures. (The spec's `free_gb_e` is `free_gb_backup` here: the
  backup disk is Z: since USER RULING 42, and the key follows `backup_dir`, not a letter.)
- AUTO-RESTART IS NOT BUILT: a policy choice left to the user (it would make the watchdog a writer). The file says how
  to restart the learner instead.

Exit codes: 0 the watchdog ran (WHATEVER the state: NEEDS YOU is a finding, not a failure); 2 REFUSED (an output path
inside the clone; nothing written); anything else is a crash, which `watchdog.ps1` reports as
`NEEDS YOU: watchdog could not run`.
Run: py -3.12 -B tools/ops/watchdog.py [--config F] [--clone D] [--ops-dir D] [--out F] [--backup-status F]
     [--recheck-seconds S]      (the task runs it through watchdog.ps1, which passes --out on the Desktop)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "ops_config.json"
STATUS_NAME = "LEARNER-STATUS.txt"
STATE_MARKER_NAME = "watchdog_state.failed.json"  # the state record when watchdog_state.json cannot be written
INTERVAL_MIN = 30          # the scheduled task's period: only for the "next" time on line 2
RECHECK_S = 90.0           # the second look before "not running" (an exit-code-3 restart is a blink)
BOOT_GRACE_MIN = 15        # the autostart task waits 2 minutes after LOGON; logon itself can take a while
STUCK_SLACK_MIN = 60       # learner.log may be silent for a whole batch: max(cycle_minutes, current.minutes) + this
PROGRESS_SLACK_MIN = 120   # no cycle started / finished for (cycle length + this) while the learner is alive
#: The learner's own DEFAULTS for the keys this file reads (ai-agent/learner.py DEFAULTS): the learner merges
#: config.json OVER these, so a key absent from config.json is still enforced at this value. Pinned by selftest W14.
LEARNER_DEFAULTS = {"cycle_minutes": 720, "min_free_gb": 25, "early_prune_margin_gb": 15}
DISK_CLEAR_GB = 2.0        # hysteresis: a raised disk alarm clears only above alarm + this
LEARNER_RECOVER_RUNS = 2   # hysteresis: 'not running' is recovered after this many alive checks in a row
DISK_PROBE_TIMEOUT_S = 10.0  # the backup disk's free-space probe (a sleeping USB disk can block for minutes)
LOG_TAIL_BYTES = 4096
DISK_FALL_GB, DISK_FALL_WINDOW_H = 10.0, 6.0
TREND_WINDOW_H, TREND_MIN_SAMPLES = 72.0, 12
TREND_MIN_RATE = 0.05      # GB/day: below this a fitted slope is noise, reported as "no downward trend"
SAMPLES_KEEP_DAYS = 14
BACKUP_MAX_AGE_H = 36.0
REMINDER_H = 24.0
BOOT_JITTER_S = 120.0      # psutil.boot_time() wobbles by a second or two between calls; a reboot moves it by far more
REBOOT_NOTE_H = 6.0
STATE_TRIES, STATE_SLEEP = 3, 1.0
WRITE_TRIES, WRITE_SLEEP = 3, 0.5
GIB = 2 ** 30
TZ = "America/Los_Angeles"
STAMP_FMT = "%Y-%m-%d %I:%M:%S %p"  # the learner's now() and backup_learner.py's stamp()
NEEDS, NOTE, OK = "NEEDS", "NOTE", "OK"
_TIMESTAMP_LINE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} [AP]M$")


# --------------------------------------------------------------------------------------------- probes (patchable)
def clock() -> float:
    """Now, as epoch seconds. The selftest pins it."""
    return time.time()


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def boot_time() -> float:
    import psutil
    return float(psutil.boot_time())


def logon_time() -> float | None:
    """When THIS user's newest logon session started (psutil.users()), or None when Windows lists none for them. The
    learner's autostart task is a LOGON trigger, so the 'just started' grace counts from here, not from boot."""
    import getpass
    import psutil
    me = getpass.getuser().lower()
    starts = [float(u.started) for u in psutil.users()
              if (u.name or "").split("\\")[-1].lower() == me and isinstance(u.started, (int, float))]
    return max(starts) if starts else None


def disk_free_gib(path: Path) -> float | None:
    """Free space on the volume holding `path`, in GiB; None when its drive is not present (an unplugged backup disk)."""
    p = Path(os.path.abspath(path))
    if p.anchor and not os.path.isdir(p.anchor):
        return None
    while not p.exists() and p.parent != p:
        p = p.parent
    return shutil.disk_usage(p).free / GIB


class ProbeTimeout(Exception):
    pass


def disk_free_gib_bounded(path: Path, timeout: float | None = None) -> float | None:
    """`disk_free_gib` with a time limit (default DISK_PROBE_TIMEOUT_S): a sleeping or failing backup disk can block a
    free-space call for minutes, and the scheduled task kills the whole watchdog at 5 minutes, before it writes the
    status file. The probe runs in a daemon thread; on timeout it is abandoned (it cannot be cancelled) and
    ProbeTimeout is raised. A probe that RAISES re-raises here."""
    box: dict = {}

    def work() -> None:
        try:
            box["v"] = disk_free_gib(path)
        except BaseException as e:  # noqa: BLE001 - carried to the caller's thread
            box["e"] = e

    th = threading.Thread(target=work, name="disk-probe", daemon=True)
    th.start()
    th.join(DISK_PROBE_TIMEOUT_S if timeout is None else timeout)
    if th.is_alive():
        raise ProbeTimeout(f"no answer in {DISK_PROBE_TIMEOUT_S if timeout is None else timeout:g} s")
    if "e" in box:
        raise box["e"]
    return box.get("v")


def learner_argv_index(argv: list[str]) -> int | None:
    """The index of the `learner.py` argument when argv runs it with `run` or `once`, else None. An argument is the
    script only when its BASENAME is learner.py: a `-c` string that merely contains the words is one argument whose
    basename is not."""
    for i, a in enumerate(argv):
        if re.split(r"[\\/]", a)[-1].lower() == "learner.py":
            return i if any(x in ("run", "once") for x in argv[i + 1:]) else None
    return None


def learner_pids(agent: Path) -> list[int]:
    """Pids of processes running THIS clone's learner.py with run/once. The script argument is resolved against the
    process's own working folder and compared with `agent/learner.py`, so the main checkout's learner, a test's, or a
    command line that only mentions the words never counts (the real learner runs as `py -3.12 learner.py run` with
    its cwd in the clone's ai-agent, run_agent.ps1)."""
    import psutil
    target = os.path.normcase(os.path.abspath(agent / "learner.py"))
    out = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = p.info["cmdline"] or []
            i = learner_argv_index(argv)
            if i is None:
                continue
            script = argv[i]
            if not os.path.isabs(script):
                script = os.path.join(p.cwd(), script)
            if os.path.normcase(os.path.abspath(script)) == target:
                out.append(p.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            continue
    return out


def restart_pending() -> str | None:
    """Why Windows wants a restart (NOTE only: the learner stops when the PC restarts), or None."""
    if os.name != "nt":
        return None
    import winreg
    hklm = winreg.HKEY_LOCAL_MACHINE
    why = []
    for key, label in ((r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
                        "Windows Update"),
                       (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
                        "a Windows component update")):
        try:
            winreg.CloseKey(winreg.OpenKey(hklm, key))
            why.append(label)
        except OSError:
            pass
    try:
        k = winreg.OpenKey(hklm, r"SYSTEM\CurrentControlSet\Control\Session Manager")
        try:
            value, _kind = winreg.QueryValueEx(k, "PendingFileRenameOperations")
            if value and any(str(v).strip() for v in value):
                why.append("pending file renames")
        finally:
            winreg.CloseKey(k)
    except OSError:
        pass
    return ", ".join(why) or None


def unexpected_shutdown_since(t: float) -> bool | None:
    """Best effort: whether Windows logged Kernel-Power event 41 (the PC stopped without a clean shutdown) since `t`.
    None when it cannot be asked."""
    if os.name != "nt":
        return None
    ms = max(int((clock() - t) * 1000), 60_000)
    q = ("*[System[Provider[@Name='Microsoft-Windows-Kernel-Power'] and (EventID=41) and "
         f"TimeCreated[timediff(@SystemTime) <= {ms}]]]")
    try:
        r = subprocess.run(["wevtutil", "qe", "System", "/q:" + q, "/c:1", "/rd:true", "/f:text"], capture_output=True,
                           text=True, timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    return bool(r.stdout.strip()) if r.returncode == 0 else None


def toast(title: str, body: str) -> None:
    """Ask watchdog.ps1 to show one toast. The selftest replaces this to COUNT the calls (W6)."""
    clean = lambda s: " ".join(str(s).split())  # noqa: E731 - no tab or newline may break the one-line protocol
    _say(f"NOTIFY\t{clean(title)}\t{clean(body)}")


def desktop_dir() -> Path | None:
    """The real Desktop folder (OneDrive-redirected on this PC), the same folder as PowerShell's
    [Environment]::GetFolderPath('Desktop'). watchdog.ps1 passes --out itself; this is the default for a manual run."""
    if os.name != "nt":
        return None
    import ctypes
    buf = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf) == 0 and buf.value:  # DESKTOPDIRECTORY
        return Path(buf.value)
    return None


# --------------------------------------------------------------------------------------------- small helpers
def _say(line: str) -> None:
    if sys.stdout is not None:
        print(line, flush=True)


def la_time(t: float) -> str:
    """12-hour Los Angeles time, the user's format: '12:30 PM'."""
    try:
        from zoneinfo import ZoneInfo
        d = dt.datetime.fromtimestamp(t, ZoneInfo(TZ))
    except Exception:  # noqa: BLE001 - no tz database: local time is the PC's own (it IS in Los Angeles)
        d = dt.datetime.fromtimestamp(t)
    return d.strftime("%I:%M %p").lstrip("0")


def ago(seconds: float) -> str:
    m = max(seconds, 0) / 60
    if m < 90:
        return f"{m:.0f} min"
    if m < 48 * 60:
        return f"{m / 60:.1f} h"
    return f"{m / 1440:.1f} days"


def is_under(child: Path, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def inside(child: Path, parent: Path) -> bool:
    """`child` is `parent` or below it, by NAME or by FILE IDENTITY (the nearest existing folder of `child`, or any of
    its parents, is the same file as `parent`): the backup tool's guard, so an alias spelling cannot slip past."""
    if is_under(child, parent):
        return True
    p = Path(os.path.abspath(child))
    while not p.exists() and p.parent != p:
        p = p.parent
    for q in (p, *p.parents):
        try:
            if os.path.samefile(q, parent):
                return True
        except OSError:
            continue
    return False


def write_atomic(path: Path, text: str) -> None:
    """tmp + replace, so a reader (the user, OneDrive, the backup) never sees half a file; retried for a moment while
    another reader holds it (the backup reads the ops folder at 1 AM)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    for attempt in range(WRITE_TRIES):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt + 1 == WRITE_TRIES:
                raise
            sleep(WRITE_SLEEP)


def read_json(path: Path, tries: int = 1):
    """Parse a JSON file read in one call (no handle stays open). Retried for state.json, which the learner replaces."""
    last: Exception | None = None
    for attempt in range(tries):
        try:
            return json.loads(path.read_bytes().decode("utf-8"))
        except FileNotFoundError:
            raise
        except (OSError, ValueError) as e:
            last = e
            if attempt + 1 < tries:
                sleep(STATE_SLEEP)
    raise ValueError(f"{path.name} did not parse after {tries} read(s): {last}")


def load_samples(path: Path) -> list[dict]:
    rows = []
    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return rows
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and isinstance(row.get("t"), (int, float)):
            rows.append(row)
    return sorted(rows, key=lambda r: r["t"])


def fit_rate_per_day(points: list[tuple[float, float]]) -> float:
    """Least-squares slope of (epoch seconds, GiB) in GiB per day."""
    n = len(points)
    xs = [(t - points[0][0]) / 86400 for t, _ in points]
    ys = [f for _, f in points]
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return 0.0 if den == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def forecast(points: list[tuple[float, float]], floor: float | None) -> str:
    """'79 GB free; falling 6.0 GB/day; 25 GB in 9 days', or why there is no forecast."""
    free = points[-1][1]
    head = f"{free:.0f} GB free"
    if len(points) < TREND_MIN_SAMPLES:
        return f"{head}; a trend needs {TREND_MIN_SAMPLES} samples over up to {TREND_WINDOW_H:.0f} h (have {len(points)})"
    rate = -fit_rate_per_day(points)
    if rate < TREND_MIN_RATE:
        return f"{head}; no downward trend"
    if floor is None:
        return f"{head}; falling {rate:.1f} GB/day"
    if free <= floor:
        return f"{head}; falling {rate:.1f} GB/day; already under {floor:.0f} GB"
    days = (free - floor) / rate
    when = "under 1 day" if days < 1 else f"{days:.0f} days"
    return f"{head}; falling {rate:.1f} GB/day; {floor:.0f} GB in {when}"


def attention_reason(text: str) -> str:
    """The reason line of the learner's ATTENTION.md (`attention()`: a heading, a timestamp, then the reason)."""
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not _TIMESTAMP_LINE.match(s):
            return s[:220]
    return "(ATTENTION.md holds no reason line)"


def cfg_value(cfg: dict, key: str) -> float:
    """config.json's value for `key`, or the learner's own default when the key is absent (the learner merges its
    DEFAULTS under config.json, so an absent key is still enforced)."""
    return float(cfg[key]) if key in cfg else float(LEARNER_DEFAULTS[key])


def parse_stamp(s) -> float:
    """A learner / backup time stamp ('2026-10-21 04:07:12 AM', this PC's local time) as epoch seconds."""
    return dt.datetime.strptime(str(s), STAMP_FMT).timestamp()


def last_log_line(path: Path) -> str:
    """The last non-empty line of learner.log, read from its last LOG_TAIL_BYTES in one short open."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - LOG_TAIL_BYTES))
            tail = fh.read()
    except OSError as e:
        return f"(learner.log unreadable: {e})"
    lines = [ln.strip() for ln in tail.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    return lines[-1][:200] if lines else "(learner.log is empty)"


def prev_needs(prev: dict) -> dict[str, str]:
    """The previous run's NEEDS checks as {id: text}. A state written before 'needs' existed has only its code
    ('NEEDS:a,b'), so its ids are recovered from that, with the id as the text."""
    needs = prev.get("needs")
    if isinstance(needs, dict):
        return {str(k): str(v) for k, v in needs.items()}
    code = str(prev.get("code") or "")
    if code.startswith(NEEDS + ":"):
        return {cid: cid for cid in code.split(":", 1)[1].split(",") if cid}
    return {}


def backup_error_text(err: str) -> str:
    """The backup tool's error, shortened to what a person needs. Its NEEDS-YOU errors open with a long fixed prefix
    ('NEEDS-YOU (the new zip was written, verified and KEPT; NOTHING was pruned): <reason>'): keep the reason."""
    if err.startswith("NEEDS-YOU") and "): " in err:
        err = "NEEDS-YOU: " + err.split("): ", 1)[1]
    return err if len(err) <= 240 else err[:237] + "..."


# --------------------------------------------------------------------------------------------- the run
class Report:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str]] = []  # (level, id, text)
        self.lines: list[str] = []

    def needs(self, cid: str, text: str) -> None:
        self.findings.append((NEEDS, cid, text))

    def note(self, cid: str, text: str) -> None:
        self.findings.append((NOTE, cid, text))

    def level(self) -> str:
        levels = {f[0] for f in self.findings}
        return NEEDS if NEEDS in levels else NOTE if NOTE in levels else OK

    def code(self) -> str:
        lvl = self.level()
        if lvl != NEEDS:
            return lvl
        return NEEDS + ":" + ",".join(sorted({cid for level, cid, _ in self.findings if level == NEEDS}))

    def head(self) -> str:
        lvl = self.level()
        if lvl == OK:
            return "OK"
        texts = [t for level, _c, t in self.findings if level == lvl]
        return ("NEEDS YOU: " if lvl == NEEDS else "NOTE: ") + "; ".join(texts)

    def needs_map(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for level, cid, text in self.findings:
            if level == NEEDS:
                out[cid] = (out[cid] + "; " + text) if cid in out else text
        return out


def decide_notify(prev: dict | None, needs_now: dict | set, now: float) -> str | None:
    """Which toast this run owes, if any: 'needs' when a problem id that the previous run did NOT have joins the NEEDS
    set; 'reminder' once per REMINDER_H while any NEEDS YOU persists with no new id (the same set, or a SHRINKING one:
    a problem leaving is not news that needs a toast, the file says it); 'recovered' when the set empties; None
    otherwise (OK <-> NOTE never toasts: a NOTE asks nothing of the user)."""
    prev = prev or {}
    before = set(prev_needs(prev))
    current = set(needs_now)
    if current:
        if current - before:
            return "needs"
        last = prev.get("last_toast")
        if not isinstance(last, (int, float)) or now - last >= REMINDER_H * 3600:
            return "reminder"
        return None
    return "recovered" if before else None


def check_learner(r: Report, agent: Path, now: float, boot: float | None, ctx: dict) -> None:
    pids = learner_pids(agent)
    if not pids:
        sleep(RECHECK_S)  # a restart into new code (exit 3) is a blink: look once more before calling it dead
        pids = learner_pids(agent)
    ctx["alive"] = bool(pids)
    prev = ctx.get("prev") or {}
    streak = int(prev.get("alive_streak") or 0) + 1 if pids else 0
    ctx["alive_streak"] = streak
    stop = (agent / "STOP").exists()
    if pids:
        r.lines.append(f"learner: running (pid {', '.join(map(str, pids))})")
        if "learner" in prev_needs(prev) and streak < LEARNER_RECOVER_RUNS:
            # HYSTERESIS: a crash loop (run_agent.ps1 restarts it after 10 minutes) must not flap needs/recovered
            r.needs("learner", f"the learner runs again (pid {', '.join(map(str, pids))}) after it was not running; "
                               f"it counts as recovered when {LEARNER_RECOVER_RUNS} checks in a row find it alive "
                               f"({streak} so far)")
        if stop:
            r.note("stop", "a STOP file is present: the learner stops after this batch")
        return
    r.lines.append("learner: NOT running")
    # the grace counts from the LATER of boot and this user's logon (a session listed as older than the boot is stale)
    logon = ctx.get("logon")
    if logon is not None and (boot is None or logon >= boot):
        start, what = logon, "you logged on"
    else:
        start, what = boot, "the PC booted"
    if stop:
        r.note("stop", "the learner is stopped by your STOP file (delete ai-agent\\STOP, then run run_agent.ps1)")
    elif start is not None and now - start < BOOT_GRACE_MIN * 60:
        r.note("boot", f"{what} {ago(now - start)} ago; the learner autostarts 2 minutes after logon")
    else:
        r.needs("learner", "learner is not running")


def check_attention(r: Report, agent: Path) -> None:
    p = agent / "findings" / "ATTENTION.md"
    if p.exists():
        r.needs("attention", "the learner paused itself: "
                + attention_reason(p.read_bytes().decode("utf-8", errors="replace")))


def current_cycle(ctx: dict) -> dict | None:
    """state.json's `current` (the batch the learner is running), when state.json was read and holds one."""
    state = ctx.get("state")
    cur = state.get("current") if isinstance(state, dict) else None
    return cur if isinstance(cur, dict) else None


def cycle_length_min(cfg: dict, ctx: dict) -> tuple[float, str]:
    """The length the RUNNING batch may take: max(config cycle_minutes, current.minutes), and how it was derived.
    config.json is re-read every cycle, so a batch started under a longer cycle_minutes keeps its own length."""
    base = cfg_value(cfg, "cycle_minutes")
    how = f"cycle_minutes {base:g}" + ("" if "cycle_minutes" in cfg else " (the learner's default)")
    cur = current_cycle(ctx)
    try:
        own = float(cur.get("minutes")) if cur and cur.get("minutes") is not None else None
    except (TypeError, ValueError):
        own = None
    if own is not None and own > base:
        return own, f"the running batch's {own:g} min"
    return base, how


def check_stuck(r: Report, agent: Path, cfg: dict | None, now: float, ctx: dict) -> None:
    log = agent / "data" / "learner.log"
    try:
        age = now - log.stat().st_mtime
    except FileNotFoundError:
        age = None
    if not ctx.get("alive"):
        r.lines.append("learner.log: " + ("missing" if age is None else f"last written {ago(age)} ago"))
        return
    if cfg is None:
        r.lines.append("stuck check SKIPPED: the clone's config.json cannot be read")
        return
    length, how = cycle_length_min(cfg, ctx)
    limit = length + STUCK_SLACK_MIN
    if age is None:
        r.needs("stuck", "the learner runs but data/learner.log does not exist")
    elif age > limit * 60:
        r.needs("stuck", f"learner.log silent for {ago(age)} (over {how} + {STUCK_SLACK_MIN} min): the learner may be "
                         "stuck")
    else:
        r.lines.append(f"learner.log: last written {ago(age)} ago (stuck after {limit / 60:.0f} h)")


def check_progress(r: Report, agent: Path, cfg: dict | None, now: float, ctx: dict) -> None:
    """FALSE CALM guard: the learner can stay alive and log 'waiting 15 min' every 15 minutes while it starts no cycle
    for days (too little free RAM for 8 lanes, another batch running), which the log-age check reads as healthy. This
    looks at what the learner actually DID, from state.json: when its newest cycle finished, or when its current one
    started."""
    if not ctx.get("alive"):
        return  # the process check owns a dead learner
    if cfg is None:
        r.lines.append("progress check SKIPPED: the clone's config.json cannot be read")
        return
    if "state_error" in ctx:
        r.lines.append("progress check SKIPPED: data/state.json cannot be read (see above)")
        return
    state = ctx.get("state") or {}
    log = agent / "data" / "learner.log"
    cur = current_cycle(ctx)
    if cur is not None:
        length, how = cycle_length_min(cfg, ctx)
        limit = length + PROGRESS_SLACK_MIN
        try:
            started = parse_stamp(cur.get("started"))
        except ValueError:  # the learner always writes now() here; anything else is not a time to judge by
            r.lines.append(f"progress check SKIPPED: the current cycle {cur.get('tag')} has no readable start time "
                           f"({str(cur.get('started'))[:40]!r})")
            return
        age = now - started
        if age > limit * 60:
            r.needs("progress", f"the learner runs but has not finished a cycle for {ago(age)}: {cur.get('tag')} "
                                f"started {ago(age)} ago (over {how} + {PROGRESS_SLACK_MIN} min); learner.log's last "
                                f"line: {last_log_line(log)}")
        else:
            r.lines.append(f"cycle {cur.get('tag')}: started {ago(age)} ago (overdue after {limit / 60:.0f} h)")
        return
    done = []
    for c in state.get("cycles", []) if isinstance(state.get("cycles"), list) else []:
        if isinstance(c, dict) and c.get("finished"):
            try:
                done.append((parse_stamp(c["finished"]), str(c.get("tag", "?"))))
            except ValueError:
                continue
    if not done:
        r.lines.append("progress: no finished cycle in data/state.json yet")
        return
    finished, tag = max(done)
    base = cfg_value(cfg, "cycle_minutes")
    limit = base + PROGRESS_SLACK_MIN
    idle = now - finished
    if idle > limit * 60:
        r.needs("progress", f"the learner runs but has not started a cycle for {ago(idle)} (the last, {tag}, finished "
                            f"at {la_time(finished)}; over cycle_minutes {base:g} + {PROGRESS_SLACK_MIN} min); "
                            f"learner.log's last line: {last_log_line(log)}")
    else:
        r.lines.append(f"no cycle running; the last ({tag}) finished {ago(idle)} ago (overdue after "
                       f"{limit / 60:.0f} h)")


def check_disk(r: Report, agent: Path, backup_dir: Path | None, cfg: dict | None, now: float, past: list[dict],
               sample: dict, ctx: dict | None = None) -> None:
    drive = Path(os.path.abspath(agent)).drive or "/"
    free = disk_free_gib(agent)
    sample["free_gb_c"] = None if free is None else round(free, 3)
    if backup_dir is not None:
        bdrive = Path(os.path.abspath(backup_dir)).drive or str(backup_dir)
        try:
            bfree = disk_free_gib_bounded(backup_dir)
            r.lines.append(f"backup disk {bdrive} " + ("NOT PRESENT" if bfree is None else f"{bfree:.0f} GB free"))
        except ProbeTimeout as e:
            bfree = None
            r.lines.append(f"backup disk {bdrive}: free space UNKNOWN ({e}: asleep or failing?)")
        sample["free_gb_backup"] = None if bfree is None else round(bfree, 3)
    if free is None:
        r.needs("disk", f"cannot read free space on {drive}")
        return
    floor = None
    if cfg is not None:
        floor = cfg_value(cfg, "min_free_gb")
        margin = cfg_value(cfg, "early_prune_margin_gb")
        alarm = floor + margin
        was_low = "disk_low" in prev_needs((ctx or {}).get("prev") or {})
        why = (f"min_free_gb {floor:g} + margin {margin:g}"
               + ("" if "min_free_gb" in cfg and "early_prune_margin_gb" in cfg else ", the learner's defaults for "
                  "any key config.json lacks"))
        if free < alarm:
            shown = f"{free:.1f}" if alarm - free < 1 else f"{free:.0f}"  # 39.6 must not print as '40' under a 40 alarm
            r.needs("disk_low", f"only {shown} GB free on {drive} (the alarm is under {alarm:.0f} GB: {why}; the "
                                f"learner stops starting batches at {floor:g})")
        elif was_low and free <= alarm + DISK_CLEAR_GB:
            # HYSTERESIS: O7 archives at exactly this line, so free space hovers around it; clearing at the line itself
            # toasted 'NEEDS YOU' / 'recovered' every 30 minutes (review 2026-10-21, attack A)
            r.needs("disk_low", f"only {free:.1f} GB free on {drive}, still within {DISK_CLEAR_GB:g} GB of the alarm "
                                f"({alarm:.0f} GB: {why}); it clears above {alarm + DISK_CLEAR_GB:.0f} GB")
    else:
        r.lines.append("disk alarm SKIPPED: the clone's config.json cannot be read")
    recent = [row["free_gb_c"] for row in past
              if row["t"] >= now - DISK_FALL_WINDOW_H * 3600 and isinstance(row.get("free_gb_c"), (int, float))]
    if recent and max(recent) - free > DISK_FALL_GB:
        r.needs("disk_fall", f"free space on {drive} fell {max(recent) - free:.1f} GB in the last "
                             f"{DISK_FALL_WINDOW_H:.0f} h ({max(recent):.0f} -> {free:.0f} GB)")
    points = [(row["t"], float(row["free_gb_c"])) for row in past
              if row["t"] >= now - TREND_WINDOW_H * 3600 and isinstance(row.get("free_gb_c"), (int, float))]
    points.append((now, free))
    r.lines.append(f"disk {drive} " + forecast(points, floor))


def check_restart_pending(r: Report) -> None:
    why = restart_pending()
    if why:
        r.note("restart", f"Windows has a restart pending ({why}): the learner stops while the PC restarts")
    else:
        r.lines.append("Windows restart pending: no")


def check_reboot(r: Report, boot: float | None, now: float, past: list[dict], prev: dict, state_out: dict) -> None:
    reboot = prev.get("reboot") if isinstance(prev.get("reboot"), dict) else None
    last = past[-1] if past else None
    if boot is not None and last and isinstance(last.get("boot"), (int, float)) \
            and abs(boot - last["boot"]) > BOOT_JITTER_S:
        down = max(boot - last["t"], 0) / 60  # at most this long: the last check ran before the shutdown
        reboot = {"boot": boot, "down_min": round(down), "unexpected": unexpected_shutdown_since(last["t"])}
    if reboot:
        state_out["reboot"] = reboot
        if now - reboot["boot"] < REBOOT_NOTE_H * 3600:
            how = ", an UNEXPECTED shutdown (Windows event 41)" if reboot.get("unexpected") else ""
            r.note("reboot", f"the PC restarted at {la_time(reboot['boot'])} (down at most {reboot['down_min']} min"
                             f"{how})")


def check_backup(r: Report, status_file: Path, now: float) -> None:
    try:
        st = read_json(status_file)
    except FileNotFoundError:
        r.needs("backup", f"no backup has run yet ({status_file.name} does not exist)")
        return
    except ValueError as e:
        r.needs("backup", f"the backup status cannot be read: {e}")
        return
    try:
        t = dt.datetime.strptime(str(st.get("time")), STAMP_FMT).timestamp()
    except ValueError:
        r.needs("backup", f"the backup status has no readable time ({st.get('time')!r})")
        return
    age = now - t
    if not st.get("ok"):
        r.needs("backup", f"the last backup ({ago(age)} ago) did not succeed: "
                          + backup_error_text(str(st.get("error") or "ok is false and no error was recorded")))
    elif age > BACKUP_MAX_AGE_H * 3600:
        r.needs("backup", f"no backup for {ago(age)} (over {BACKUP_MAX_AGE_H:.0f} h): is the Pokebot-Ops-Backup task "
                          "running?")
    else:
        zipname = Path(str(st.get("zip") or "?")).name
        warns = st.get("warnings") or []
        r.lines.append(f"backup: ok {ago(age)} ago ({zipname})" + (f", {len(warns)} warning(s)" if warns else ""))


def load_learner_state(agent: Path, ctx: dict) -> None:
    """Read data/state.json ONCE for every check that needs it (one closed read: no handle may block the learner's
    replace). Sets ctx['state'], or ctx['state_error'] = (kind, message)."""
    try:
        state = read_json(agent / "data" / "state.json", tries=STATE_TRIES)
    except FileNotFoundError:
        ctx["state_error"] = ("missing", "data/state.json does not exist: is the clone path right?")
        return
    except ValueError as e:
        ctx["state_error"] = ("unreadable", f"data/state.json unreadable: {e}")
        return
    if not isinstance(state, dict):
        ctx["state_error"] = ("unreadable", f"data/state.json unreadable: not an object ({type(state).__name__})")
        return
    ctx["state"] = state


def check_held(r: Report, agent: Path, ctx: dict) -> None:
    if "state_error" in ctx:
        r.needs("state", ctx["state_error"][1])
        return
    state = ctx.get("state") or {}
    held = [c for c in state.get("cycles", []) if isinstance(c, dict) and c.get("held")]
    if not held:
        r.lines.append("held cycles: none")
        return
    tags = ", ".join(str(c.get("tag", "?")) for c in held)
    first = held[0]["held"]
    why = str(first.get("reason", "?")) if isinstance(first, dict) else str(first)
    r.needs("held", f"{len(held)} cycle(s) HELD for review: {tags} (first reason: {why[:160]}); nothing of theirs is "
                    "archived or deleted until a human resolves it (README 'Archive')")


def guarded(r: Report, cid: str, fn, *a) -> None:
    """One check that raises must not hide the others, and must not read as healthy."""
    try:
        fn(r, *a)
    except Exception as e:  # noqa: BLE001
        r.needs(cid + "_error", f"the {cid} check failed: {type(e).__name__}: {str(e)[:160]}")


def read_prev_state(state_file: Path, marker: Path) -> dict:
    """The previous run's state: the newer (by its own `t`) of watchdog_state.json and the marker a failed save left
    (watchdog_state.failed.json). The state file is read twice before it counts as unreadable (the 1 AM backup can hold
    it for a moment). Neither readable -> {} (a first run)."""
    found = []
    for path, tries in ((state_file, 2), (marker, 1)):
        try:
            got = read_json(path, tries=tries)
        except (FileNotFoundError, ValueError):
            continue
        if isinstance(got, dict):
            found.append(got)
    if not found:
        return {}
    return max(found, key=lambda d: d.get("t") if isinstance(d.get("t"), (int, float)) else 0)


def run(clone: Path, ops_dir: Path, out: Path | None, backup_status: Path, backup_dir: Path | None,
        interval_min: float = INTERVAL_MIN) -> tuple[int, str]:
    """One watchdog pass. Returns (exit code, the status text). `clone` is the learner's ai-agent folder."""
    agent = Path(clone)
    ops_dir = Path(ops_dir)
    fallback = ops_dir / STATUS_NAME
    samples_file = ops_dir / "samples.jsonl"
    state_file = ops_dir / "watchdog_state.json"
    marker = ops_dir / STATE_MARKER_NAME
    writes = [p for p in (out, fallback, samples_file, state_file, marker) if p is not None]
    bad = [p for p in writes if inside(p, agent.parent)]
    if bad:
        msg = f"REFUSED: {bad[0]} is inside the clone {agent.parent}: the watchdog never writes there"
        _say(msg)
        return 2, msg

    now = clock()
    past = [row for row in load_samples(samples_file) if row["t"] <= now]
    prev = read_prev_state(state_file, marker)
    try:
        boot = boot_time()
    except Exception:  # noqa: BLE001 - no boot time only disables the boot grace and the reboot note
        boot = None
    r = Report()
    ctx: dict = {"prev": prev}
    try:
        ctx["logon"] = logon_time()
    except Exception:  # noqa: BLE001 - no logon time: the grace falls back to the boot time
        ctx["logon"] = None
    sample = {"t": round(now, 1), "free_gb_c": None, "free_gb_backup": None, "alive": None, "boot": boot}
    state_out: dict = {}
    cfg: dict | None = None
    try:
        cfg = read_json(agent / "config.json")
        if not isinstance(cfg, dict):
            raise ValueError(f"config.json is not an object ({type(cfg).__name__})")
    except FileNotFoundError:
        r.needs("config", f"the clone has no config.json ({agent}): is the clone path right?")
    except ValueError as e:
        cfg = None
        r.needs("config", f"the clone's config.json cannot be read: {e}")
    load_learner_state(agent, ctx)

    guarded(r, "learner", check_learner, agent, now, boot, ctx)
    sample["alive"] = ctx.get("alive")
    guarded(r, "attention", check_attention, agent)
    guarded(r, "stuck", check_stuck, agent, cfg, now, ctx)
    guarded(r, "progress", check_progress, agent, cfg, now, ctx)
    guarded(r, "disk", check_disk, agent, backup_dir, cfg, now, past, sample, ctx)
    guarded(r, "restart", check_restart_pending)
    guarded(r, "reboot", check_reboot, boot, now, past, prev, state_out)
    guarded(r, "backup", check_backup, backup_status, now)
    guarded(r, "held", check_held, agent, ctx)

    level, code = r.level(), r.code()
    needs_now = r.needs_map()
    before = prev_needs(prev)
    resolved = [before[cid] for cid in before if cid not in needs_now]
    text_lines = [r.head(), f"checked {la_time(now)} PT, next {la_time(now + interval_min * 60)}"]
    if resolved:
        text_lines.append("resolved since the last check: " + "; ".join(t[:160] for t in resolved)
                          + (f"; still NEEDS YOU: {', '.join(sorted(needs_now))}" if needs_now else ""))
    if level == NEEDS:
        text_lines += [f"also NOTE: {t}" for lv, _c, t in r.findings if lv == NOTE]
    text_lines += r.lines
    run_ps1 = Path(os.path.abspath(agent / "run_agent.ps1"))
    text_lines += [f"To restart the learner: run {run_ps1}  (the watchdog never restarts it by itself)"]

    def write_status(lines: list[str]) -> str:
        body = "\n".join(lines) + "\n"
        wrote = 0
        for target in ([out] if out is not None else []) + [fallback]:
            try:
                write_atomic(target, body)
                wrote += 1
            except OSError as e:
                _say(f"WARN could not write {target}: {e}")
        if not wrote:
            raise OSError("neither the status file nor its fallback copy could be written")
        return body

    text = write_status(text_lines)

    try:
        keep = [row for row in past if row["t"] >= now - SAMPLES_KEEP_DAYS * 86400] + [sample]
        write_atomic(samples_file, "".join(json.dumps(row) + "\n" for row in keep))
    except OSError as e:
        _say(f"WARN could not save the sample: {e}")

    kind = decide_notify(prev, needs_now, now)
    new_state = {"t": now, "code": code, "level": level, "head": text_lines[0][:300],
                 "needs": {cid: t[:300] for cid, t in needs_now.items()},
                 "alive_streak": ctx.get("alive_streak", 0),
                 "since": prev.get("since") if prev.get("code") == code else now,
                 "last_toast": prev.get("last_toast"), "last_toast_kind": prev.get("last_toast_kind"), **state_out}
    if kind:
        new_state.update(last_toast=now, last_toast_kind=kind)
    record = json.dumps(new_state, indent=1)
    try:
        write_atomic(state_file, record)
        if marker.exists():
            try:
                marker.unlink()
            except OSError as e:
                _say(f"WARN could not remove the stale {marker.name}: {e}")
    except OSError as e:
        _say(f"WARN could not save the watchdog state: {e}")
        try:
            write_atomic(marker, record)
            warn = (f"WARN the watchdog state could not be saved ({type(e).__name__}); its record went to {marker} "
                    f"instead, so a toast is not repeated every run. Fix {state_file}.")
        except OSError as e2:
            warn = (f"WARN the watchdog state could not be saved ({type(e).__name__}), nor its marker "
                    f"({type(e2).__name__}): a NEEDS YOU toast may repeat every run. Fix {ops_dir}.")
        _say(warn)
        text_lines.insert(2, warn)
        text = write_status(text_lines)
    _say(text.rstrip("\n"))
    if kind == "needs":
        toast("Pokebot learner: NEEDS YOU", text_lines[0][len("NEEDS YOU: "):])
    elif kind == "reminder":
        toast("Pokebot learner: still NEEDS YOU", text_lines[0][len("NEEDS YOU: "):])
    elif kind == "recovered":
        toast("Pokebot learner: recovered",
              text_lines[0] + ("; resolved: " + "; ".join(t[:120] for t in resolved) if resolved else ""))
    return 0, text


def load_ops_config(path: Path) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("status_file", "ops_dir", "backup_dir"):
        if key in cfg:
            cfg[key] = os.path.expandvars(cfg[key])
    return cfg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--clone", type=Path, help="the learner's ai-agent folder (default: ops_config.json clone)")
    ap.add_argument("--ops-dir", type=Path, help="samples, state and the fallback status (default: ops_config ops_dir)")
    ap.add_argument("--out", type=Path, help="the status file (default: LEARNER-STATUS.txt on the Desktop)")
    ap.add_argument("--backup-status", type=Path, help="backup_status.json (default: ops_config status_file)")
    ap.add_argument("--backup-dir", type=Path, help="the backup folder, for its free space (default: ops_config)")
    ap.add_argument("--recheck-seconds", type=float, default=None,
                    help="the wait before the second process scan (default 90; a test shortens it)")
    ap.add_argument("--interval-minutes", type=float, default=INTERVAL_MIN)
    a = ap.parse_args(argv)
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    if a.recheck_seconds is not None:
        globals()["RECHECK_S"] = a.recheck_seconds
    cfg = load_ops_config(a.config)
    out = a.out
    if out is None:
        desk = desktop_dir()
        out = desk / STATUS_NAME if desk else None
    backup_dir = a.backup_dir or (Path(cfg["backup_dir"]) if cfg.get("backup_dir") else None)
    code, _text = run(a.clone or Path(cfg["clone"]), a.ops_dir or Path(cfg["ops_dir"]), out,
                      a.backup_status or Path(cfg["status_file"]), backup_dir, a.interval_minutes)
    return code


if __name__ == "__main__":
    sys.exit(main())
