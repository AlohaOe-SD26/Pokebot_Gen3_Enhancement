"""One-call check-in for the whole project (backlog A1, spec S1-5; LEAN v1, 2026-10-20).

Prints ONE screen (at most 40 lines): the clock, the 24/7 bot tuner, disk, the nightly learner backup (one BACKUP
line from tools/ops/backup_learner.py's status file, backlog O4), the session-free watchdog (one WATCHDOG line: the
first line of its LEARNER-STATUS.txt in the ops folder, 'STALE' when that file is over 70 minutes old, backlog O1),
git, the AI player's frontier and newest evidence, and the in-flight notes. READ-ONLY: it opens files and runs `git`
read commands, never writes, never calls Claude, and never runs `git fetch` unless `--fetch` is given.

Every section is fault-isolated: a section that fails prints `unavailable: <reason>` and the others still print, so a
half-written file of a running learner never breaks a check-in (test T2). Exit code is always 0.

    py -3.12 tools/status.py                    # the check-in
    py -3.12 tools/status.py --started "1:10 PM" --eta-minutes 90
    py -3.12 tools/status.py --json             # the same data for scripts
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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLONE = Path("C:/Remote Projects/pokebot-learner/ai-agent")
MAX_LINES, WIDTH = 40, 118
STAMP = "%Y-%m-%d %I:%M:%S %p"
# backup_learner.py's own ZIP_RE (ASCII [0-9] only), with the timestamp captured
BACKUP_ZIP = re.compile(r"^learner-data-([0-9]{8}-[0-9]{4})\.zip$")


def clock12(t: dt.datetime) -> str:
    return t.strftime("%I:%M %p").lstrip("0")


def span(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    return f"{hours} h {rest // 60} m" if hours else f"{rest // 60} m"


def read_jsonl_tail(path: Path, n: int) -> list[dict]:
    """The last n rows that parse. A row being written right now (truncated) is skipped, never fatal."""
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-(n + 2):]:
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows[-n:]


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                             errors="replace", timeout=20).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, errors="replace",
                          timeout=60)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip().splitlines()[-1][:80] if (proc.stderr or proc.stdout)
                           else f"git {args[0]} exit {proc.returncode}")
    return proc.stdout.strip()


def section(title: str, fn, *args) -> list[str]:
    try:
        return [f"{title}:"] + [f"  {line}" for line in fn(*args)]
    except Exception as error:  # noqa: BLE001 - a check-in must never die on one section (T2)
        return [f"{title}: unavailable: {type(error).__name__}: {str(error)[:70]}"]


def clock_lines(now: dt.datetime, started: str | None, eta_minutes: float | None) -> list[str]:
    parts = [f"now {clock12(now)} ({now:%a %b %d}, this PC's local time)"]
    if started:
        begun = dt.datetime.strptime(f"{now:%Y-%m-%d} {started.strip()}", "%Y-%m-%d %I:%M %p")
        if begun > now:
            begun -= dt.timedelta(days=1)
        parts.append(f"started {clock12(begun)}")
        parts.append(f"elapsed {span((now - begun).total_seconds())}")
        if eta_minutes is not None:
            parts.append(f"ETA {clock12(begun + dt.timedelta(minutes=eta_minutes))}")
    return [" | ".join(parts)]


def learner_lines(clone: Path, now: dt.datetime) -> list[str]:
    data = clone / "data"
    out = []
    lock = data / "agent.lock"
    pid = int(lock.read_text().strip()) if lock.exists() and lock.read_text().strip().isdigit() else None
    alive = pid is not None and pid_alive(pid)
    flags = [name for name in ("STOP",) if (clone / name).exists()]
    flags += ["ATTENTION.md"] if (clone / "findings" / "ATTENTION.md").exists() else []
    out.append(f"process {'RUNNING' if alive else 'NOT RUNNING'} (pid {pid}){' | ' + ', '.join(flags) if flags else ''}")
    try:
        state = json.loads((data / "state.json").read_text(encoding="utf-8"))
        cur = state.get("current") or {}
        began = dt.datetime.strptime(cur["started"], STAMP)
        ends = began + dt.timedelta(minutes=float(cur.get("minutes", 720)))
        out.append(f"cycle {cur.get('tag')} | {cur.get('lanes')} lanes | started {clock12(began)} | ends "
                   f"{clock12(ends)} ({span((ends - now).total_seconds())} left) | failures in a row "
                   f"{state.get('failures', 0)}")
    except Exception as error:  # noqa: BLE001
        out.append(f"cycle: unavailable: {type(error).__name__}: {str(error)[:60]}")
    try:
        rows = [r for r in read_jsonl_tail(data / "cycles.jsonl", 6) if r.get("source") == "cycle"][-3:]
        out.append("last cycles (usable/runs): " + ", ".join(f"{r.get('tag')} {r.get('usable')}/{r.get('runs')}"
                                                             for r in rows))
    except Exception as error:  # noqa: BLE001
        out.append(f"last cycles: unavailable: {type(error).__name__}: {str(error)[:60]}")
    try:
        latest = (clone / "findings" / "LATEST.md").read_text(encoding="utf-8", errors="replace")
        champ = next((l for l in latest.splitlines() if l.startswith("Champions:")), "Champions: ?")
        out.append(f"{champ} (the scripted BOT's, not the AI player's)")
    except Exception as error:  # noqa: BLE001
        out.append(f"champions: unavailable: {type(error).__name__}")
    inbox = clone / "inbox"
    files = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime) if inbox.is_dir() else []
    oldest = f", oldest {span(now.timestamp() - files[0].stat().st_mtime)} old" if files else ""
    consult = "?"
    log = data / "learner.log"
    if log.exists():
        lines = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()[-400:] if "consult:" in l]
        consult = lines[-1].split("] ", 1)[-1][:70] if lines else "no consult in the log tail"
    out.append(f"consult inbox {len(files)} waiting{oldest} | last: {consult}")
    out.append(archive_line(clone))
    return out


def archive_line(clone: Path) -> str:
    """The raw-log archives (backlog O3): how many runs/<tag>/raw.zip exist, the last `learner.py archive-check`, and
    how many cycles the learner HELD for review (read live from data/state.json; '?' when it cannot be read)."""
    try:
        zips = list((clone / "runs").glob("*/raw.zip")) if (clone / "runs").is_dir() else []
        line = f"raw-log archives: {len(zips)} raw.zip"
        check = clone / "data" / "archive_check.json"
        if check.exists():
            rec = json.loads(check.read_text(encoding="utf-8"))
            line += (f" | last archive-check {rec.get('checked')}: {rec.get('archives')} checked, "
                     f"{rec.get('bad')} BAD")
        else:
            line += " | archive-check never run"
        return line + " | " + held_part(clone)
    except Exception as error:  # noqa: BLE001
        return f"raw-log archives: unavailable: {type(error).__name__}: {str(error)[:60]}"


def held_part(clone: Path) -> str:
    """'held for review: N' (+ the first tags) from data/state.json; never raises."""
    try:
        state = json.loads((clone / "data" / "state.json").read_text(encoding="utf-8"))
        held = [c.get("tag", "?") for c in state.get("cycles", []) if isinstance(c, dict) and c.get("held")]
        return f"held for review: {len(held)}" + (f" ({', '.join(held[:4])}) - run archive-check" if held else "")
    except Exception:  # noqa: BLE001
        return "held for review: ?"


def disk_lines(clone: Path) -> list[str]:
    seen, out = set(), []
    for label, path in (("C: (learner, repo)", clone if clone.exists() else REPO),):
        usage = shutil.disk_usage(path)
        if path.anchor in seen:
            continue
        seen.add(path.anchor)
        out.append(f"{label}: {usage.free / 2**30:.0f} GB free of {usage.total / 2**30:.0f} GB")
    return out


def default_backup_status() -> Path:
    """Where the nightly backup (tools/ops/backup_learner.py, backlog O4) writes its status: ops_config.json's
    status_file, with %LOCALAPPDATA% expanded; the documented default if that file cannot be read."""
    try:
        cfg = json.loads((REPO / "tools" / "ops" / "ops_config.json").read_text(encoding="utf-8"))
        return Path(os.path.expandvars(cfg["status_file"]))
    except Exception:  # noqa: BLE001 - a check-in never dies on a config file
        return Path(os.path.expandvars("%LOCALAPPDATA%/pokebot-ops/backup_status.json"))


def newest_zip_age(dest: str | None, now: dt.datetime) -> str:
    """The age of the newest learner-data-YYYYMMDD-HHMM.zip in the backup folder, from its name (the name IS the
    time). On a failed night this is the number that matters: how old the last GOOD copy is."""
    if not dest:
        return "newest zip ?"
    folder = Path(dest)
    if not os.path.isdir(Path(os.path.abspath(folder)).anchor or "."):
        return "newest zip ? (its drive is not present)"
    if not folder.is_dir():
        return "no zip yet"
    names = sorted(p.name for p in folder.iterdir() if BACKUP_ZIP.match(p.name))
    if not names:
        return "no zip yet"
    made = dt.datetime.strptime(BACKUP_ZIP.match(names[-1]).group(1), "%Y%m%d-%H%M")
    return f"newest zip {span((now - made).total_seconds())} old"


def backup_line(path: Path, now: dt.datetime) -> str:
    """ONE line for the nightly learner backup, from its status file: ok / NEEDS-YOU / REFUSED / FAILED, how long ago
    it last ran, the newest zip's age, and the reason. Never raises: an absent file is 'no backup yet' (the task is
    not installed, or has never run), and a file that cannot be read is 'unavailable: <why>', never a false ok."""
    try:
        if not path.exists():
            return f"BACKUP: no backup yet (no {path.name})"
        st = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(st, dict) or not isinstance(st.get("ok"), bool) or not isinstance(st.get("time"), str):
            raise ValueError("not a backup status file (no ok / time)")
        ran = dt.datetime.strptime(st["time"], STAMP)
        error = str(st.get("error") or "")
        if st["ok"]:
            word, why = "ok", ""
        elif error.startswith("NEEDS-YOU"):
            word, why = "NEEDS-YOU", error.split("): ", 1)[-1]
        elif error.startswith("REFUSED"):
            word, why = "REFUSED", error.split(": ", 1)[-1]
        else:
            word, why = "FAILED", error or "no reason recorded"
        line = f"BACKUP: {word} | last run {span((now - ran).total_seconds())} ago | {newest_zip_age(st.get('dest'), now)}"
        return line + (f" | {why}" if why else "")
    except Exception as error:  # noqa: BLE001 - a half-written status file must not break the check-in
        return f"BACKUP: unavailable: {type(error).__name__}: {str(error)[:60]}"


WATCHDOG_STALE_MIN = 70  # the watchdog task runs every 30 minutes: two missed runs plus slack


def default_watchdog_status() -> Path:
    """The copy of the watchdog's status file (tools/ops/watchdog.py, backlog O1) that it keeps in the ops folder:
    ops_config.json's ops_dir, with %LOCALAPPDATA% expanded, + LEARNER-STATUS.txt (the Desktop copy can be moved by
    OneDrive; this one cannot)."""
    try:
        cfg = json.loads((REPO / "tools" / "ops" / "ops_config.json").read_text(encoding="utf-8"))
        return Path(os.path.expandvars(cfg["ops_dir"])) / "LEARNER-STATUS.txt"
    except Exception:  # noqa: BLE001 - a check-in never dies on a config file
        return Path(os.path.expandvars("%LOCALAPPDATA%/pokebot-ops/LEARNER-STATUS.txt"))


def watchdog_line(path: Path, now: dt.datetime) -> str:
    """ONE line for the session-free watchdog: its own first line (OK / NOTE / NEEDS YOU) and when it last checked.
    A file older than WATCHDOG_STALE_MIN says STALE first: a watchdog task that stopped (disabled, its script moved,
    killed at its 5-minute limit) leaves exactly that, an old file that still reads OK. No file at all: the task is not
    registered yet (install_ops_tasks.ps1 -Apply). Never raises."""
    try:
        if not path.exists():
            return f"WATCHDOG: not registered yet (no {path.name} in {path.parent})"
        age = now.timestamp() - path.stat().st_mtime
        first = (path.read_bytes().decode("utf-8", errors="replace").splitlines() or ["(empty file)"])[0].strip()
        if age > WATCHDOG_STALE_MIN * 60:
            return f"WATCHDOG: STALE: last checked {span(age)} ago (due every 30 min: task stopped?) | it said: {first}"
        return f"WATCHDOG: {first} | checked {span(age)} ago"
    except Exception as error:  # noqa: BLE001 - a status file being replaced right now must not break the check-in
        return f"WATCHDOG: unavailable: {type(error).__name__}: {str(error)[:60]}"


def git_lines(repo: Path, clone: Path, fetch: bool) -> list[str]:
    if fetch:
        git(repo, "fetch", "origin", "--quiet")
    dirty = [l for l in git(repo, "status", "--porcelain").splitlines() if l.strip()]
    ahead, behind = git(repo, "rev-list", "--left-right", "--count", "HEAD...origin/main").split()
    head = git(repo, "rev-parse", "--short", "HEAD")
    fetched = repo / ".git" / "FETCH_HEAD"
    age = f"fetched {span(dt.datetime.now().timestamp() - fetched.stat().st_mtime)} ago" if fetched.exists() else "never fetched"
    out = [f"main checkout {head}: {len(dirty)} uncommitted, ahead {ahead} / behind {behind} ({age})"]
    if (clone.parent / ".git").exists():
        out.append(f"learner clone at {git(clone.parent, 'rev-parse', '--short', 'HEAD')} (it fast-forwards between cycles)")
    return out


def ai_lines(repo: Path) -> list[str]:
    out = []
    frontier = repo / "PROJECT KNOWLEDGE" / "ai-frontier.txt"
    out.append(frontier.read_text(encoding="utf-8").strip().splitlines()[0][:WIDTH - 4] if frontier.exists()
               else "AI frontier: (no ai-frontier.txt yet)")
    evidence = repo / "ai_player" / "evidence"
    newest = sorted(evidence.glob("*.txt"), key=lambda p: p.stat().st_mtime)[-3:] if evidence.is_dir() else []
    for path in reversed(newest):
        tail = [l for l in path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()][-1:] or [""]
        out.append(f"{path.name}: {tail[0].strip()[:WIDTH - len(path.name) - 8]}")
    return out


def later_lines(repo: Path) -> list[str]:
    inflight = repo / "PROJECT KNOWLEDGE" / "in-flight"
    notes = sorted(inflight.glob("*.md")) if inflight.is_dir() else []
    return [f"in-flight notes: {', '.join(p.name for p in notes[-3:]) if notes else 'none'}"]


def build(args: argparse.Namespace) -> list[str]:
    now = dt.datetime.strptime(args.now, "%Y-%m-%d %I:%M %p") if args.now else dt.datetime.now()
    lines = ["== PROJECT STATUS (read-only check-in) =="]
    lines += section("CLOCK", clock_lines, now, args.started, args.eta_minutes)
    lines += section("BOT TUNER (24/7 learner, ai-agent/)", learner_lines, args.clone, now)
    lines += section("DISK", disk_lines, args.clone)
    lines.append(backup_line(args.backup_status, now))
    lines.append(watchdog_line(args.watchdog_status, now))
    lines += section("GIT", git_lines, args.repo, args.clone, args.fetch)
    lines += section("AI PLAYER", ai_lines, args.repo)
    lines += section("NOT YET", later_lines, args.repo)
    return [l if len(l) <= WIDTH else l[:WIDTH - 1] + "…" for l in lines][:MAX_LINES]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--clone", type=Path, default=CLONE, help="the learner's ai-agent folder in its deployment clone")
    p.add_argument("--repo", type=Path, default=REPO, help="the main checkout")
    p.add_argument("--fetch", action="store_true", help="run `git fetch` first (off by default)")
    p.add_argument("--backup-status", type=Path, default=default_backup_status(),
                   help="the nightly backup's status file (default: tools/ops/ops_config.json status_file)")
    p.add_argument("--watchdog-status", type=Path, default=default_watchdog_status(),
                   help="the watchdog's status file (default: ops_config.json ops_dir / LEARNER-STATUS.txt)")
    p.add_argument("--started", help='when the current work started, e.g. "1:10 PM"')
    p.add_argument("--eta-minutes", type=float)
    p.add_argument("--now", help='pin the clock for tests, e.g. "2026-10-20 3:41 PM"')
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    lines = build(args)
    if args.json:
        print(json.dumps({"lines": lines}, indent=1))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
