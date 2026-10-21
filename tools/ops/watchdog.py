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
  `learner.log` is only stat()ed, never opened.
- THRESHOLDS COME FROM THE CLONE'S `config.json`, never from here: the stuck limit is `cycle_minutes + 60` (the log is
  silent for a whole batch, so a fixed limit would cry wolf the day O2 lengthens a cycle), the disk alarm is
  `min_free_gb + early_prune_margin_gb` (the margin is O7's key; until the learner has it, 15, the value O7's spec fixes,
  so the alarm and O7's early archive fire at the same line: 25 + 15 = 40 GB today). Disk is measured in GiB (2**30),
  the learner's own unit for `min_free_gb`. A config that cannot be read is itself NEEDS YOU (the learner re-reads it
  every cycle and would fail the same way); a missing key SKIPS that check and says so.
- THE STATE. Line 1 is `OK`, `NOTE: <why>` (nothing for the user to do: the user's own STOP file, a pending Windows
  restart, a recent boot or restart) or `NEEDS YOU: <why>`. Line 2 is `checked 12:30 PM PT, next 1:00 PM` (12-hour Los
  Angeles time, the user's format). The detail lines and the restart command follow.
- THE CHECKS. (1) The learner process: a process whose argv names THIS clone's `learner.py` (the relative argument is
  resolved against the process's own working folder) with `run` or `once`. A process that merely mentions those words,
  or runs ANOTHER checkout's learner, is not it. Missing -> re-checked once after 90 s (the learner's exit-code-3
  restart into new code is a blink) -> NEEDS YOU, unless the STOP file exists (NOTE) or the PC booted under 15 minutes
  ago (NOTE: autostart waits 2 minutes after logon). (2) `findings/ATTENTION.md` -> NEEDS YOU with its reason line.
  (3) Stuck: `learner.log` older than `cycle_minutes + 60` while the learner is alive. (4) Disk: under the alarm, or a
  fall of over 10 GB in 6 h -> NEEDS YOU; otherwise a forecast line (least squares over up to 72 h, at least 12
  samples). (5) A pending Windows restart -> NOTE. (6) The boot time moved (by over 2 minutes: psutil's boot time
  wobbles) since the last sample -> NOTE until 6 h after that boot, with the downtime (and whether Windows logged an unexpected shutdown, event 41, best effort). (7) The backup tool's
  `backup_status.json`: missing, ok false (its REFUSED / NEEDS-YOU / FAILED error, quoted) or older than 36 h -> NEEDS
  YOU. (8) A cycle the archiver HELD for review (`"held"` on a cycle in `data/state.json`; the learner then touches
  nothing of it until a human resolves it) -> NEEDS YOU naming the tags. Each check is wrapped: one that raises
  becomes a NEEDS YOU line naming it, and the others still run.
- NOTIFY ONLY ON A CHANGE (alert fatigue is how a watchdog gets ignored). The state code is the level plus the ids of
  the NEEDS checks, kept in `watchdog_state.json`: entering NEEDS YOU, or a DIFFERENT set of problems -> one toast;
  the same NEEDS YOU -> one reminder per 24 h; leaving NEEDS YOU -> one "recovered" toast; OK <-> NOTE -> none. The
  toast itself is shown by `watchdog.ps1` (Windows PowerShell 5.1's ToastNotificationManager; Win11 Home has no
  msg.exe): this file prints one `NOTIFY<TAB>title<TAB>body` line per toast. The state is saved BEFORE the toast is
  shown, so a toast that fails to show is not retried; the status file still carries the state.
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
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "ops_config.json"
STATUS_NAME = "LEARNER-STATUS.txt"
INTERVAL_MIN = 30          # the scheduled task's period: only for the "next" time on line 2
RECHECK_S = 90.0           # the second look before "not running" (an exit-code-3 restart is a blink)
BOOT_GRACE_MIN = 15        # the autostart task waits 2 minutes after logon; logon itself can take a while
STUCK_SLACK_MIN = 60       # learner.log may be silent for a whole batch: cycle_minutes + this
EARLY_PRUNE_MARGIN_GB = 15.0  # O7's default margin, used only while the clone's config has no early_prune_margin_gb
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


def disk_free_gib(path: Path) -> float | None:
    """Free space on the volume holding `path`, in GiB; None when its drive is not present (an unplugged backup disk)."""
    p = Path(os.path.abspath(path))
    if p.anchor and not os.path.isdir(p.anchor):
        return None
    while not p.exists() and p.parent != p:
        p = p.parent
    return shutil.disk_usage(p).free / GIB


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


def decide_notify(prev: dict | None, code: str, level: str, now: float) -> str | None:
    """Which toast this run owes, if any: 'needs' on entering NEEDS YOU or a different set of problems, 'reminder'
    once per REMINDER_H while the same NEEDS YOU persists, 'recovered' on leaving it, None otherwise (OK <-> NOTE
    never toasts: a NOTE asks nothing of the user)."""
    prev = prev or {}
    was_needs = prev.get("level") == NEEDS
    if level == NEEDS:
        if not was_needs or prev.get("code") != code:
            return "needs"
        last = prev.get("last_toast")
        if not isinstance(last, (int, float)) or now - last >= REMINDER_H * 3600:
            return "reminder"
        return None
    return "recovered" if was_needs else None


def check_learner(r: Report, agent: Path, now: float, boot: float | None, ctx: dict) -> None:
    pids = learner_pids(agent)
    if not pids:
        sleep(RECHECK_S)  # a restart into new code (exit 3) is a blink: look once more before calling it dead
        pids = learner_pids(agent)
    ctx["alive"] = bool(pids)
    stop = (agent / "STOP").exists()
    if pids:
        r.lines.append(f"learner: running (pid {', '.join(map(str, pids))})")
        if stop:
            r.note("stop", "a STOP file is present: the learner stops after this batch")
        return
    r.lines.append("learner: NOT running")
    if stop:
        r.note("stop", "the learner is stopped by your STOP file (delete ai-agent\\STOP, then run run_agent.ps1)")
    elif boot is not None and now - boot < BOOT_GRACE_MIN * 60:
        r.note("boot", f"the PC booted {ago(now - boot)} ago; the learner autostarts 2 minutes after logon")
    else:
        r.needs("learner", "learner is not running")


def check_attention(r: Report, agent: Path) -> None:
    p = agent / "findings" / "ATTENTION.md"
    if p.exists():
        r.needs("attention", "the learner paused itself: "
                + attention_reason(p.read_bytes().decode("utf-8", errors="replace")))


def check_stuck(r: Report, agent: Path, cfg: dict | None, now: float, ctx: dict) -> None:
    log = agent / "data" / "learner.log"
    try:
        age = now - log.stat().st_mtime
    except FileNotFoundError:
        age = None
    if not ctx.get("alive"):
        r.lines.append("learner.log: " + ("missing" if age is None else f"last written {ago(age)} ago"))
        return
    if cfg is None or "cycle_minutes" not in cfg:
        r.lines.append("stuck check SKIPPED: no cycle_minutes in the clone's config.json")
        return
    limit = float(cfg["cycle_minutes"]) + STUCK_SLACK_MIN
    if age is None:
        r.needs("stuck", "the learner runs but data/learner.log does not exist")
    elif age > limit * 60:
        r.needs("stuck", f"learner.log silent for {ago(age)} (over cycle_minutes {cfg['cycle_minutes']} + "
                         f"{STUCK_SLACK_MIN} min): the learner may be stuck")
    else:
        r.lines.append(f"learner.log: last written {ago(age)} ago (stuck after {limit / 60:.0f} h)")


def check_disk(r: Report, agent: Path, backup_dir: Path | None, cfg: dict | None, now: float, past: list[dict],
               sample: dict) -> None:
    drive = Path(os.path.abspath(agent)).drive or "/"
    free = disk_free_gib(agent)
    sample["free_gb_c"] = None if free is None else round(free, 3)
    if backup_dir is not None:
        bfree = disk_free_gib(backup_dir)
        sample["free_gb_backup"] = None if bfree is None else round(bfree, 3)
        bdrive = Path(os.path.abspath(backup_dir)).drive or str(backup_dir)
        r.lines.append(f"backup disk {bdrive} " + ("NOT PRESENT" if bfree is None else f"{bfree:.0f} GB free"))
    if free is None:
        r.needs("disk", f"cannot read free space on {drive}")
        return
    floor = None
    if cfg is not None and "min_free_gb" in cfg:
        floor = float(cfg["min_free_gb"])
        margin = float(cfg.get("early_prune_margin_gb", EARLY_PRUNE_MARGIN_GB))
        alarm = floor + margin
        if free < alarm:
            r.needs("disk_low", f"only {free:.0f} GB free on {drive} (the alarm is under {alarm:.0f} GB: min_free_gb "
                                f"{floor:g} + margin {margin:g}; the learner stops starting batches at {floor:g})")
    else:
        r.lines.append("disk alarm SKIPPED: no min_free_gb in the clone's config.json")
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


def check_held(r: Report, agent: Path) -> None:
    try:
        state = read_json(agent / "data" / "state.json", tries=STATE_TRIES)
    except FileNotFoundError:
        r.needs("state", "data/state.json does not exist: is the clone path right?")
        return
    except ValueError as e:
        r.needs("state", f"data/state.json unreadable: {e}")
        return
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


def run(clone: Path, ops_dir: Path, out: Path | None, backup_status: Path, backup_dir: Path | None,
        interval_min: float = INTERVAL_MIN) -> tuple[int, str]:
    """One watchdog pass. Returns (exit code, the status text). `clone` is the learner's ai-agent folder."""
    agent = Path(clone)
    ops_dir = Path(ops_dir)
    fallback = ops_dir / STATUS_NAME
    samples_file = ops_dir / "samples.jsonl"
    state_file = ops_dir / "watchdog_state.json"
    writes = [p for p in (out, fallback, samples_file, state_file) if p is not None]
    bad = [p for p in writes if inside(p, agent.parent)]
    if bad:
        msg = f"REFUSED: {bad[0]} is inside the clone {agent.parent}: the watchdog never writes there"
        _say(msg)
        return 2, msg

    now = clock()
    past = [row for row in load_samples(samples_file) if row["t"] <= now]
    try:
        prev = read_json(state_file)
        prev = prev if isinstance(prev, dict) else {}
    except (FileNotFoundError, ValueError):
        prev = {}
    try:
        boot = boot_time()
    except Exception:  # noqa: BLE001 - no boot time only disables the boot grace and the reboot note
        boot = None
    r = Report()
    ctx: dict = {}
    sample = {"t": round(now, 1), "free_gb_c": None, "free_gb_backup": None, "alive": None, "boot": boot}
    state_out: dict = {}
    cfg: dict | None = None
    try:
        cfg = read_json(agent / "config.json")
    except FileNotFoundError:
        r.needs("config", f"the clone has no config.json ({agent}): is the clone path right?")
    except ValueError as e:
        r.needs("config", f"the clone's config.json cannot be read: {e}")

    guarded(r, "learner", check_learner, agent, now, boot, ctx)
    sample["alive"] = ctx.get("alive")
    guarded(r, "attention", check_attention, agent)
    guarded(r, "stuck", check_stuck, agent, cfg, now, ctx)
    guarded(r, "disk", check_disk, agent, backup_dir, cfg, now, past, sample)
    guarded(r, "restart", check_restart_pending)
    guarded(r, "reboot", check_reboot, boot, now, past, prev, state_out)
    guarded(r, "backup", check_backup, backup_status, now)
    guarded(r, "held", check_held, agent)

    level, code = r.level(), r.code()
    text_lines = [r.head(), f"checked {la_time(now)} PT, next {la_time(now + interval_min * 60)}"]
    if level == NEEDS:
        text_lines += [f"also NOTE: {t}" for lv, _c, t in r.findings if lv == NOTE]
    text_lines += r.lines
    run_ps1 = Path(os.path.abspath(agent / "run_agent.ps1"))
    text_lines += [f"To restart the learner: run {run_ps1}  (the watchdog never restarts it by itself)"]
    text = "\n".join(text_lines) + "\n"

    wrote = 0
    for target in ([out] if out is not None else []) + [fallback]:
        try:
            write_atomic(target, text)
            wrote += 1
        except OSError as e:
            _say(f"WARN could not write {target}: {e}")
    if not wrote:
        raise OSError("neither the status file nor its fallback copy could be written")

    try:
        keep = [row for row in past if row["t"] >= now - SAMPLES_KEEP_DAYS * 86400] + [sample]
        write_atomic(samples_file, "".join(json.dumps(row) + "\n" for row in keep))
    except OSError as e:
        _say(f"WARN could not save the sample: {e}")

    kind = decide_notify(prev, code, level, now)
    new_state = {"code": code, "level": level, "head": text_lines[0][:300],
                 "since": prev.get("since") if prev.get("code") == code else now,
                 "last_toast": prev.get("last_toast"), "last_toast_kind": prev.get("last_toast_kind"), **state_out}
    if kind:
        new_state.update(last_toast=now, last_toast_kind=kind)
    try:
        write_atomic(state_file, json.dumps(new_state, indent=1))
    except OSError as e:
        _say(f"WARN could not save the watchdog state: {e}")
    _say(text.rstrip("\n"))
    if kind == "needs":
        toast("Pokebot learner: NEEDS YOU", text_lines[0][len("NEEDS YOU: "):])
    elif kind == "reminder":
        toast("Pokebot learner: still NEEDS YOU", text_lines[0][len("NEEDS YOU: "):])
    elif kind == "recovered":
        toast("Pokebot learner: recovered", text_lines[0])
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
