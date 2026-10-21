"""The Emerald AI strategy learner. It runs 24/7 on this PC and spends no AI credits.

Each CYCLE:
1. sizes itself to the machine (lanes = parallel games, in fours, one per starter for each strategy);
2. picks one strategy per four lanes (`brain.choose_arms`): the current best as the control, an inbox proposal, then
   the next rows of a screening design that measures every knob's own effect;
3. runs them side by side through the story bot's own batch runner (`tools/story-dev/x4_headless.py --arms`), which
   plays real games in the emulator and refuses anything malformed;
4. turns the logs into small run records (`scoring.py`), updates what it has learned and rewrites
   `findings/LATEST.md` (`report.py`);
5. optionally asks Claude for advice (`consult.py`, off by default);
6. ARCHIVES its own old raw logs (backlog O3, 2026-10-21): the newest `keep_raw_cycles` cycles stay raw; each older
   cycle's `batch/` AND its lane profiles (`profiles/<name>/...`: badge-log.json, stats.db and the saves are the AI's
   experience data, backlog A6) are zipped to `runs/<tag>/raw.zip` (+ `raw.manifest.json`), the zip is VERIFIED
   against the originals, and only then are the originals deleted. A profile file byte-identical to a batch file of the
   same name (the lane's debug logs, copied into `batch/`) is not stored twice: the manifest names it `dup_of` that
   member. No original (batch or profile) is deleted unless its exact bytes (name, size, CRC32) are in a verified
   archive, stored or through `dup_of`, and no archive file is ever overwritten or deleted. A cycle still in use is
   skipped until it is quiet; one whose state the code cannot prove safe is HELD for a human (`archive-check`).
   Accepted residual risk: see `archive_cycle` (a write landing in the ~0.1 s between the last re-check and the delete).
   Before each cycle, if free disk is under `min_free_gb + early_prune_margin_gb` (40 GB by default), the same
   archive runs early with only the newest 2 cycles kept raw (backlog O7, `early_archive`).
7. appends one row to `data/ops.jsonl` (backlog O6, `OPS_KEYS`): how long the cycle and its boundary took, the CPU
   and disk it used. A failed measurement is a null field plus `ops_error`, never a failed cycle.

Resilience:
- If the learner dies mid-cycle, the batch keeps running. The next start ADOPTS it: it waits for that batch to end,
  then scores it, so no cycle is lost.
- Between cycles, if its own code has changed and `test_agent.py` passes, it exits with code 3 so the wrapper
  restarts it into the new code. If the tests fail, it keeps running the old code and says so.

Safety: it never edits code and never runs git. It writes only inside `ai-agent/`, plus the batch runner's lane
profiles, which it deletes later by exact name. One instance at a time (a lock). It waits instead of starting while
another batch is running, stops cleanly when the `STOP` file exists, and after repeated failures pauses and writes
`findings/ATTENTION.md` instead of retrying forever.

Commands (run from this folder with `py -3.12 learner.py <command>`):
  run        the 24/7 loop (what `run_agent.ps1` starts)
  once       exactly one cycle, then exit
  plan       show the next cycle's strategies and the exact batch command, without running anything
  ingest D   add an existing batch directory's runs as data (e.g. step 14's)
  reparse    re-read every batch whose raw logs still exist with the current parser (after a parser upgrade)
  report     rewrite findings/LATEST.md from the data
  status     where the learner is now
  publish    copy the findings and data into published/, small enough to commit for a cloud session
  archive    archive every cycle outside keep_raw_cycles now; for when the learner is STOPPED (it refuses while the
             24/7 learner holds its lock, and a learner starting meanwhile waits for it, up to LOCK_WAIT_MAX_MIN)
  archive-check  re-verify every runs/<tag>/raw.zip against its manifest and list HELD cycles (read-only; exit 1 on
             any BAD or HELD)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import traceback
import zipfile
import zlib
from pathlib import Path

import psutil

AI = Path(__file__).resolve().parent
sys.path.insert(0, str(AI))
import brain  # noqa: E402
import consult  # noqa: E402
import knowledge as K  # noqa: E402
import report  # noqa: E402
import scoring  # noqa: E402

REPO = AI.parent
STORY_DEV = REPO / "tools" / "story-dev"
PROFILES = REPO / "sandbox-pokebot" / "profiles"
DATA, FINDINGS, INBOX, RUNS, PUBLISHED = AI / "data", AI / "findings", AI / "inbox", AI / "runs", AI / "published"
RUNS_FILE, CYCLES_FILE, STATE_FILE = DATA / "runs.jsonl", DATA / "cycles.jsonl", DATA / "state.json"
#: The ops ledger (backlog O6): one row per finished cycle, how long it took and what it cost the machine. A file of its
#: own, NOT cycles.jsonl, so the readers of cycles.jsonl (`report.write`, `publish`) never see a new field (test O6-3).
OPS_FILE = DATA / "ops.jsonl"
LOCK, LOG, STOP, ATTENTION = DATA / "agent.lock", DATA / "learner.log", AI / "STOP", FINDINGS / "ATTENTION.md"
RESTART_CODE = 3
#: The raw-log archive of one cycle (backlog O3): `runs/<tag>/raw.zip` with its `raw.manifest.json`. A zip is written as
#: `.part`, verified, then renamed. One that cannot be trusted is SET ASIDE as `raw.zip.bad.<k>` (its manifest as
#: `raw.manifest.json.bad.<k>`), k the smallest unused integer: a set-aside file is never overwritten, renamed or deleted.
ARCHIVE, ARCHIVE_PART, MANIFEST = "raw.zip", "raw.zip.part", "raw.manifest.json"
#: Below this much free disk no archive can be written safely: archive nothing, delete nothing, start no batch.
ARCHIVE_FLOOR_GB = 2.0
#: A cycle is archived (or its delete resumed) only once it is QUIET: no batch runner or lane process names it, and no
#: original was modified within this many minutes. An orphaned lane still appending to an old cycle's log is the
#: demonstrated hazard (O3 review, 2026-10-21).
QUIET_MINUTES = 60
#: A rename or replace is retried for a transient lock (an antivirus scan holds a new file briefly; a reader holding
#: state.json open blocks os.replace on Windows). Module constants, so a TEST can shorten the wait.
REPLACE_TRIES, REPLACE_WAIT_S = 5, 2.0
#: A learner starting while a manual `learner.py archive` holds the lock WAITS for it (polling), up to this long.
LOCK_POLL_S, LOCK_WAIT_MAX_MIN = 30.0, 120.0
_os_replace = os.replace
_os_rename = os.rename

DEFAULTS = {
    "lanes": "auto", "max_lanes": 24, "reserve_threads": 4, "reserve_ram_gb": 8, "ram_per_lane_gb": 1.5,
    "cycle_minutes": 720, "keep_raw_cycles": 3, "min_free_gb": 25, "design": "screen", "auto_update": True,
    "max_archives_per_prune": 3, "keep_archive_cycles": 0, "early_prune_margin_gb": 15,
    "objective": "human_balanced",
    "wait_if_other_bots_running": True, "idle_wait_minutes": 15, "max_consecutive_failures": 3,
    "max_proposals_per_cycle": 1, "two_flip_prob": 0.3,
    "consult": {"enabled": False, "max_calls_per_day": 2, "model": "sonnet", "max_usd_per_call": 0.75,
                "timeout_minutes": 20, "max_waiting_proposals": 6},
}


#: config `objective` -> the run-record field the learner ranks by (USER RULINGS 32/33, `HUMAN-PLAY-DESIGN.md`).
OBJECTIVES = {"progress": "score", "human_balanced": "human_score"}


def score_key(cfg: dict) -> str:
    return OBJECTIVES.get(str(cfg.get("objective", "human_balanced")), "human_score")


#: The learner's time stamps (state.json, cycles.jsonl, learner.log, ops.jsonl): 12-hour local time.
TIME_FMT = "%Y-%m-%d %I:%M:%S %p"


def now() -> str:
    return dt.datetime.now().strftime(TIME_FMT)


def log(msg: str) -> None:
    line = f"[{now()}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:  # a cp1252 console or pipe cannot show every file name; the log file is UTF-8
        print(line.encode("ascii", "backslashreplace").decode("ascii"), flush=True)
    DATA.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    path = AI / "config.json"
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8"))
        for k, v in user.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    if "_override_lanes" in DEFAULTS:
        cfg["lanes"] = DEFAULTS["_override_lanes"]
    if "_override_minutes" in DEFAULTS:
        cfg["cycle_minutes"] = DEFAULTS["_override_minutes"]
    return cfg


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"cycle": 0, "cycles": [], "current": None, "failures": 0}


def save_state(state: dict) -> None:
    """Write state.json atomically. The replace is retried on PermissionError: on Windows any process holding
    state.json open (tools/status.py, a watchdog, an editor) makes os.replace fail for that moment."""
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, default=str), encoding="utf-8")
    _replace_with_retry(tmp, STATE_FILE)


def code_signature(folder: Path = AI) -> str:
    """A hash of the learner's own Python files: it changes when anyone edits the code."""
    h = hashlib.sha1()
    for p in sorted(folder.glob("*.py")):
        h.update(p.name.encode() + b"\0" + p.read_bytes())
    return h.hexdigest()[:12]


#: The learner RUNS only from a deployment checkout: a separate full clone (2026-10-03), so commits made while
#: developing never move the HEAD its batches run on. The batch runner's freeze watch aborts a cycle when HEAD moves,
#: and a docs-only commit on the main checkout killed cycle ai0002 that way. This file (git-ignored) marks the clone.
DEPLOYMENT = AI / "DEPLOYMENT"


def update_commands() -> list[list[str]]:
    """The ONLY git the learner runs: in its own clone, between cycles, fetch and fast-forward. A fast-forward
    cannot discard anything, and the clone carries no local work."""
    return [["git", "-C", str(REPO), "fetch", "--quiet", "origin"],
            ["git", "-C", str(REPO), "merge", "--ff-only", "--quiet", "origin/main"]]


def update_checkout() -> str:
    """Fast-forward the deployment clone to origin/main. Returns a one-line outcome for the log."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=120)
    try:
        if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            return "update: skipped, the deployment clone has tracked changes (it should never have any)"
        before = git("rev-parse", "--short", "HEAD").stdout.strip()
        for cmd in update_commands():
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return f"update: `{' '.join(cmd[3:])}` failed: {(r.stderr or r.stdout).strip()[:200]}"
        after = git("rev-parse", "--short", "HEAD").stdout.strip()
        return f"update: {before} -> {after}" if before != after else ""
    except Exception as exc:
        return f"update: failed: {exc!r}"


def tests_pass() -> bool:
    try:
        return subprocess.run([sys.executable, str(AI / "test_agent.py")], cwd=AI, capture_output=True,
                              timeout=600).returncode == 0
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------- safety checks
def _lock_holder() -> tuple[int, list[str]] | None:
    """(pid, cmdline) of the LIVE learner process named in the lock file, or None (no lock, a stale one, or a pid now
    used by a process that is not a learner)."""
    if not LOCK.exists():
        return None
    try:
        pid = int(LOCK.read_text().strip())
    except (ValueError, OSError):
        return None
    if pid == os.getpid() or not psutil.pid_exists(pid):
        return None
    try:
        cmd = psutil.Process(pid).cmdline()
    except psutil.Error:
        return None
    return (pid, cmd) if "learner.py" in " ".join(cmd) else None


def _is_manual_archive(cmd: list[str]) -> bool:
    """True for a `learner.py archive` command line (not `archive-check`, which takes no lock)."""
    return any(a.endswith("learner.py") and b == "archive" for a, b in zip(cmd, cmd[1:]))


def acquire_lock() -> str | None:
    """None if this process now holds the lock, else why not.

    KNOWN LIMIT (re-verify 2026-10-21, measured): the check and the write are two steps, not one atomic create. Two
    processes that start within milliseconds of each other BOTH take the lock (12 of 12 trials; a start 0.5 s later is
    refused, 3 of 3). The starts here are a human's `learner.py archive` and the Task Scheduler / `run_agent.ps1` start,
    seconds or more apart, so this is accepted for now; the fix is an O_CREAT|O_EXCL create (as
    `tools/ops/backup_learner.py` does) with a stale-lock replace."""
    DATA.mkdir(parents=True, exist_ok=True)
    holder = _lock_holder()
    if holder:
        return f"another learner is running (pid {holder[0]})"
    LOCK.write_text(str(os.getpid()))
    return None


def acquire_lock_waiting_for_archive() -> str | None:
    """`acquire_lock`, except that a lock held by a manual `learner.py archive` is WAITED for (STOP-aware, polling
    every LOCK_POLL_S, giving up after LOCK_WAIT_MAX_MIN) instead of refused: `run_agent.ps1` treats a refusal (exit 2)
    as 'another learner runs' and stops for good. Returns None (lock held), "STOP", or why not.

    GIVING UP writes findings/ATTENTION.md with the real reason before returning (re-verify 2026-10-21, F8): the exit 2
    that follows makes `run_agent.ps1` print 'Another learner is already running' and stop, which is not what
    happened, and without ATTENTION.md that stop was visible nowhere else (test R21)."""
    why = acquire_lock()
    if not why:
        return None
    holder = _lock_holder()
    if holder is None:  # the holder exited between the two looks: the lock is free now
        return acquire_lock()
    if not _is_manual_archive(holder[1]):
        return why
    log(f"the lock is held by a manual `learner.py archive` (pid {holder[0]}); waiting for it to finish "
        f"(up to {LOCK_WAIT_MAX_MIN:.0f} min)")
    end = time.time() + 60 * LOCK_WAIT_MAX_MIN
    while time.time() < end:
        if not sleep_unless_stopped(LOCK_POLL_S / 60):
            return "STOP"
        why = acquire_lock()
        if not why:
            log("the manual archive finished; the learner took the lock")
            return None
        holder = _lock_holder()
        if holder and not _is_manual_archive(holder[1]):
            return why
    log(f"gave up waiting for the manual archive after {LOCK_WAIT_MAX_MIN:.0f} min: not starting (exit 2)")
    holder = _lock_holder()
    attention(f"The learner did NOT start: a manual `learner.py archive` "
              f"({'pid ' + str(holder[0]) if holder else 'its pid is gone now'}) still held the learner's lock after "
              f"{LOCK_WAIT_MAX_MIN:.0f} min of waiting. The learner exited with code 2, which `run_agent.ps1` reports "
              f"as 'Another learner is already running' and does not retry; no second learner was running. Let the "
              f"archive finish (or stop it), delete this file, then start the learner again.")
    return why or "the lock is still held"


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def _cmdlines():
    me = os.getpid()
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            if p.info["pid"] != me:
                yield p.info["pid"], " ".join(p.info["cmdline"] or [])
        except (psutil.Error, TypeError):
            continue


def other_bots_running() -> tuple[list[str], list[str]]:
    """(BATCHES, SINGLES) running on this PC now. A batch (`x4_headless.py`) or a harness drive (`story_harness.py`) is
    active work the learner must not compete with: it waits. A single bot (`pokebot.py`, e.g. a GUI window left open)
    only costs a lane's worth of CPU: the learner reserves a thread for each. Lanes of a batch are not singles."""
    batches, singles = [], []
    for pid, cmd in _cmdlines():
        if "x4_headless.py" in cmd or "story_harness.py" in cmd:
            batches.append(f"pid {pid}: {cmd[:120]}")
        elif "pokebot.py" in cmd and "--endless-target" not in cmd:
            singles.append(f"pid {pid}: {cmd[:120]}")
    return batches, singles


def batch_running(cdir: Path, cmds: list[tuple[int, str]] | None = None) -> bool:
    """True while the batch runner that writes into `cdir` is alive. `cmds`: a `_cmdlines()` snapshot to reuse (one
    process scan costs about 0.5 s)."""
    return any("x4_headless.py" in cmd and str(cdir) in cmd for _, cmd in (_cmdlines() if cmds is None else cmds))


def size_lanes(cfg: dict, singles: int = 0) -> tuple[int, str]:
    """(lanes, why). A multiple of 4 (one lane per starter for each strategy), measured now. `singles` = other single
    bots running, one thread reserved for each."""
    if str(cfg["lanes"]) != "auto":
        return int(cfg["lanes"]) // 4 * 4, "fixed in config.json"
    logical = psutil.cpu_count(logical=True) or 4
    free_gb = psutil.virtual_memory().available / 2 ** 30
    by_cpu = logical - int(cfg["reserve_threads"]) - singles
    by_ram = int((free_gb - float(cfg["reserve_ram_gb"])) / float(cfg["ram_per_lane_gb"]))
    n = max(0, min(int(cfg["max_lanes"]), by_cpu, by_ram)) // 4 * 4
    return n, f"auto: {logical} threads, {free_gb:.0f} GB free -> cpu {by_cpu}, ram {by_ram}, cap {cfg['max_lanes']}"


def free_gb() -> float:
    return shutil.disk_usage(AI).free / 2 ** 30


def attention(reason: str) -> None:
    FINDINGS.mkdir(parents=True, exist_ok=True)
    ATTENTION.write_text(f"# The learner paused itself\n\n{now()}\n\n{reason}\n\nFix the cause, delete this file, "
                         f"then start the learner again (`run_agent.ps1`).\n", encoding="utf-8")
    log(f"PAUSED for attention: {reason}")


# -------------------------------------------------------------------------------------------- ops ledger (backlog O6)
#: The keys of every `data/ops.jsonl` row, in order. Times are TIME_FMT strings; `minutes` runs from `started` to
#: `finished` (the moment the batch was scored, the same value as the cycle's `finished` in cycles.jsonl) and
#: `gap_minutes` from the PREVIOUS cycle's `finished` to this `started`, so consecutive rows tile the clock: a gap holds
#: the previous boundary's consult, archive and update plus every idle wait. `cpu_avg` is the whole machine's CPU % over
#: the batch. `learner_gb` is what the learner holds on disk after this boundary's archive: `runs/` (raw logs and zips)
#: plus its lane profiles (`endless-ai*`). `archive_seconds`/`archive_bytes`: how long this boundary's prune took and
#: the bytes of the `raw.zip` files it wrote. A field that could not be measured is null and `ops_error` says why;
#: `ops_error` is null when every field was measured.
OPS_KEYS = ("tag", "started", "finished", "minutes", "free_gb_start", "free_gb_end", "learner_gb", "cpu_avg",
            "consult_seconds", "boot_time", "gap_minutes", "archive_seconds", "archive_bytes", "ops_error")
#: How often the CPU sampler reads `psutil.cpu_percent` while a batch runs. A module constant so a test can shorten it.
CPU_SAMPLE_S = 60.0
#: The `learner_gb` size walk gives up (null + ops_error) after this long, so a slow disk never delays a boundary
#: by more than this.
SIZE_WALK_CAP_S = 20.0


class _CpuSampler(threading.Thread):
    """Samples the machine's CPU % every CPU_SAMPLE_S while a batch runs (a daemon thread: `subprocess.run` blocks the
    main one). WHY a thread: the batch is one blocking call of up to 12 hours, and an average needs readings across it.

    psutil is imported INSIDE the sampler's `try` (spec S1-3): any failure of it, at import or at a call, ends only the
    sampler and leaves `cpu_avg` null with the reason in `error`. It does NOT make psutil optional for the learner,
    which imports it at the top for the lock and process checks; it keeps a failing sampler from ever failing a cycle."""

    def __init__(self) -> None:
        super().__init__(name="ops-cpu-sampler", daemon=True)
        self.halt = threading.Event()
        self.samples: list[tuple[float, float]] = []  # (cpu %, seconds that reading covers)
        self.error: str | None = None

    def run(self) -> None:
        try:
            import psutil as ps  # noqa: PLC0415 - lazy on purpose, see the class docstring
            ps.cpu_percent(None)  # primes psutil: the first reading without an interval is meaningless
            last = time.monotonic()
            while not self.halt.wait(CPU_SAMPLE_S):
                pct, t = float(ps.cpu_percent(None)), time.monotonic()
                self.samples.append((pct, t - last))
                last = t
            pct, t = float(ps.cpu_percent(None)), time.monotonic()  # the tail since the last full interval
            if t > last:
                self.samples.append((pct, t - last))
        except Exception as exc:  # noqa: BLE001 - a sampler failure is a null field, never a failed cycle
            self.error = f"cpu_avg: {exc!r}"[:200]

    def finish(self) -> float | None:
        """Stop sampling; the time-weighted average CPU %, or None (and `error` set) when there is none."""
        self.halt.set()
        self.join(timeout=5)
        if self.is_alive():
            self.error = self.error or "cpu_avg: the sampler did not stop within 5 s"
            return None
        total = sum(w for _, w in self.samples)
        if self.error or total <= 0:
            self.error = self.error or "cpu_avg: no sample was taken"
            return None
        return round(sum(p * w for p, w in self.samples) / total, 1)


def _measured(errors: list[str], name: str, fn):
    """fn(), or None with `name: <error>` appended to `errors`. Every ops field is read through this, so one failing
    measurement nulls that field only."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - the ledger never fails a cycle
        errors.append(f"{name}: {exc!r}"[:200])
        return None


def _parse_time(text: str) -> float:
    return dt.datetime.strptime(text, TIME_FMT).timestamp()


def ops_start(state: dict) -> dict:
    """Taken just before a batch starts: the start time, free disk, the gap since the previous cycle finished, and a
    running CPU sampler. NEVER raises (a failure becomes nulls plus the reason, carried to the row by `errors`)."""
    ops: dict = {"errors": []}
    try:
        ops["t0"], ops["started"] = time.time(), now()
        ops["free_gb_start"] = _measured(ops["errors"], "free_gb_start", lambda: round(free_gb(), 1))
        prev = [c for c in state.get("cycles", []) if isinstance(c, dict) and c.get("finished")]
        ops["gap_minutes"] = _measured(ops["errors"], "gap_minutes", lambda: round(
            (ops["t0"] - _parse_time(prev[-1]["finished"])) / 60, 1)) if prev else None
        sampler = _CpuSampler()
        sampler.start()
        ops["sampler"] = sampler
    except Exception as exc:  # noqa: BLE001
        ops["errors"].append(f"ops_start: {exc!r}"[:200])
    return ops


def ops_batch_ended(ops: dict | None) -> None:
    """Stop the CPU sampler the moment the batch returns (or raises). NEVER raises."""
    try:
        sampler = (ops or {}).pop("sampler", None)
        if sampler is not None:
            ops["cpu_avg"] = sampler.finish()
            if sampler.error:
                ops["errors"].append(sampler.error)
    except Exception as exc:  # noqa: BLE001
        try:
            ops["errors"].append(f"cpu_avg: {exc!r}"[:200])
        except Exception:  # noqa: BLE001 - `ops` itself is unusable; the row then says so
            pass


def _tree_bytes(roots: list[Path], deadline: float) -> int:
    """Bytes of every regular file under `roots`, no link followed; raises TimeoutError past `deadline`."""
    total, stack = 0, [r for r in roots if r.is_dir()]
    while stack:
        if time.monotonic() > deadline:
            raise TimeoutError(f"size walk over its {SIZE_WALK_CAP_S:.0f} s cap")
        with os.scandir(stack.pop()) as it:
            for e in it:
                if e.is_dir(follow_symlinks=False):
                    stack.append(Path(e.path))
                elif e.is_file(follow_symlinks=False):
                    total += e.stat(follow_symlinks=False).st_size
    return total


def learner_bytes() -> int:
    """The learner's own disk use: `runs/` plus its lane profiles (`endless-ai*`), capped at SIZE_WALK_CAP_S."""
    deadline = time.monotonic() + SIZE_WALK_CAP_S
    return _tree_bytes([RUNS] + sorted(PROFILES.glob("endless-ai*")), deadline)


def _ops_row(tag: str, ops: dict | None, finished: str, t_fin: float, consult_s: float | None,
             archive: dict | None) -> dict:
    """The ops row for cycle `tag`. `ops` is None for an ADOPTED cycle (the learner that started it died, so its
    start-side fields were never measured: they are null and `ops_error` says so)."""
    errors = list((ops or {}).get("errors", [])) if ops is not None else [
        "adopted: the learner that started this cycle died, so started, minutes, free_gb_start, gap_minutes and "
        "cpu_avg were never measured"]
    ops = ops or {}
    t0 = ops.get("t0")
    row = {"tag": tag, "started": ops.get("started"), "finished": finished,
           "minutes": round((t_fin - t0) / 60, 1) if t0 else None,
           "free_gb_start": ops.get("free_gb_start"),
           "free_gb_end": _measured(errors, "free_gb_end", lambda: round(free_gb(), 1)),
           "learner_gb": _measured(errors, "learner_gb", lambda: round(learner_bytes() / 2 ** 30, 2)),
           "cpu_avg": ops.get("cpu_avg"),
           "consult_seconds": consult_s,
           "boot_time": _measured(errors, "boot_time", _boot_time),
           "gap_minutes": ops.get("gap_minutes"),
           "archive_seconds": (archive or {}).get("seconds"), "archive_bytes": (archive or {}).get("bytes")}
    row["ops_error"] = "; ".join(errors)[:1000] or None
    return row


def _boot_time() -> str:
    import psutil as ps  # noqa: PLC0415 - lazy like the sampler's, so its failure is this field's alone
    return dt.datetime.fromtimestamp(ps.boot_time()).strftime(TIME_FMT)


def write_ops_row(tag: str, ops: dict | None, finished: str, t_fin: float, consult_s: float | None,
                  archive: dict | None) -> None:
    """Append cycle `tag`'s row to data/ops.jsonl. THE LEDGER CAN NEVER FAIL A CYCLE: it is called after the cycle is
    scored and saved, a row that cannot be built becomes a row of nulls with `ops_error`, and a row that cannot be
    written is logged. NEVER raises."""
    try:
        row = _ops_row(tag, ops, finished, t_fin, consult_s, archive)
    except Exception as exc:  # noqa: BLE001
        row = dict.fromkeys(OPS_KEYS)
        row.update(tag=tag, finished=finished, ops_error=f"the ops row could not be built: {exc!r}"[:300])
    try:
        append_jsonl(OPS_FILE, [row])
    except Exception as exc:  # noqa: BLE001
        try:
            log(f"{tag}: could not write its data/ops.jsonl row ({exc!r}); the cycle itself is recorded")
        except Exception:  # noqa: BLE001
            pass


# ------------------------------------------------------------------------------------------------------------- inbox
def read_inbox() -> list[dict]:
    """Valid waiting proposals, oldest first. An invalid one is moved to inbox/rejected/ with the reason."""
    out = []
    for path in sorted(INBOX.glob("*.json"), key=lambda p: p.stat().st_mtime):
        try:
            p = json.loads(path.read_text(encoding="utf-8"))
            errors = K.validate_genes(p.get("genes", {})) if isinstance(p.get("genes"), dict) else ["no genes"]
        except ValueError as exc:
            errors = [f"not JSON: {exc}"]
        if errors:
            (INBOX / "rejected").mkdir(exist_ok=True)
            shutil.move(str(path), INBOX / "rejected" / path.name)
            (INBOX / "rejected" / (path.stem + ".why.txt")).write_text("\n".join(errors), encoding="utf-8")
            log(f"inbox: rejected {path.name}: {errors}")
            continue
        p["_file"] = path.name
        out.append(p)
    return out


# ------------------------------------------------------------------------------------------------------------- cycle
def plan_cycle(cfg: dict, state: dict, lanes: int) -> dict:
    records = load_jsonl(RUNS_FILE)
    proposals = read_inbox()
    k = lanes // 4
    design, design_name = None, None
    if cfg.get("design") in ("screen", "pb12"):
        design_name, rows = brain.screen_rows()
        if rows:
            # A new knob changes the design's size; its row pointer then starts again at row 1.
            start = int(state.get("design_next", 0)) if state.get("design_name", "pb12") == design_name else 0
            design = {"rows": rows, "next": start}
    picks = brain.choose_arms(k, brain.summarize(records, score_key(cfg)), proposals, random.Random(),
                              float(cfg["two_flip_prob"]), int(cfg["max_proposals_per_cycle"]), design)
    n = state["cycle"] + 1
    while any(PROFILES.glob(f"endless-ai{n:04d}-*")) or (RUNS / f"ai{n:04d}").exists():
        n += 1
    tag = f"ai{n:04d}"
    names = [chr(ord("A") + i) for i in range(len(picks))]
    # A proposal counts as used when its genome runs this cycle, whoever picked it (it may equal the incumbent).
    running = {brain.genome_id(g) for g, _ in picks}
    used = [p.get("_file") for p in proposals if brain.genome_id(p["genes"]) in running]
    return {"n": n, "tag": tag, "lanes": lanes, "minutes": float(cfg["cycle_minutes"]),
            "design_next": design["next"] if design else state.get("design_next", 0),
            "design_name": design_name if design else state.get("design_name"),
            "arms": {name: {"genome": brain.genome_id(g), "label": brain.label(g), "why": why,
                            "env": brain.full_env(g)} for name, (g, why) in zip(names, picks)},
            "proposal_files": [f for f in used if f]}


def batch_command(plan: dict, cdir: Path) -> list[str]:
    return [sys.executable, str(STORY_DEV / "x4_headless.py"), "--build", "sandbox", "--lanes", str(plan["lanes"]),
            "--minutes", str(plan["minutes"]), "--arms", str(cdir / "arms.json"), "--profile-tag", plan["tag"],
            "--out", str(cdir / "batch")]


def run_cycle(cfg: dict, state: dict, lanes: int) -> bool:
    plan = plan_cycle(cfg, state, lanes)
    tag, cdir = plan["tag"], RUNS / plan["tag"]
    cdir.mkdir(parents=True)
    spec = {"comment": f"ai-agent cycle {tag}: " + "; ".join(f"{a}={v['label']}" for a, v in plan["arms"].items()),
            "arms": {a: v["env"] for a, v in plan["arms"].items()}}
    (cdir / "arms.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (cdir / "plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    state["cycle"] = plan["n"]
    state["design_next"] = plan["design_next"]
    state["design_name"] = plan.get("design_name")
    state["current"] = {"tag": tag, "started": now(), "lanes": lanes, "minutes": plan["minutes"]}
    save_state(state)
    for a, v in plan["arms"].items():
        log(f"{tag} arm {a} = {v['genome']} {v['label']} | {v['why']}")
    env = {k: v for k, v in os.environ.items() if not k.startswith("POKEBOT_")}
    env["PYTHONUTF8"] = "1"
    log(f"{tag}: starting {lanes} lanes for {plan['minutes']:.0f} minutes")
    ops = ops_start(state)  # the ops ledger (O6): never raises
    try:
        with open(cdir / "x4.out.txt", "w", encoding="utf-8") as out:
            rc = subprocess.run(batch_command(plan, cdir), cwd=STORY_DEV, env=env, stdout=out,
                                stderr=subprocess.STDOUT).returncode
    finally:
        ops_batch_ended(ops)  # stops the CPU sampler even when the batch call raises
    return finish_cycle(cfg, load_state(), plan, rc, ops)


def finish_cycle(cfg: dict, state: dict, plan: dict, rc, ops: dict | None = None) -> bool:
    """Score a finished batch and record it. Used both after a normal run and when ADOPTING an orphaned one (`ops`
    None: its start was never measured). Last, it appends the cycle's `data/ops.jsonl` row, which never fails it."""
    tag = plan["tag"]
    batch = RUNS / tag / "batch"
    records = []
    if (batch / "ARMS.json").exists():
        try:
            records = scoring.parse_batch(batch, tag)
        except Exception:  # a half-written batch must not kill the learner; the reason goes to the log
            log(f"{tag}: parsing failed:\n{traceback.format_exc()}")
    for r in records:
        r["genome_id"] = brain.genome_id(r["genome"])
    append_jsonl(RUNS_FILE, records)
    usable = sum(1 for r in records if r.get("usable"))
    meta = json.loads((batch / "ARMS.json").read_text(encoding="utf-8")) if (batch / "ARMS.json").exists() else {}
    created = [str(batch)] + [str(PROFILES / ln["profile"]) for ln in meta.get("lanes", [])]
    t_fin = time.time()
    cycle = {"source": "cycle", "tag": tag, "finished": now(), "exit": rc, "lanes": plan["lanes"],
             "runs": len(records), "usable": usable,
             "arms_label": ", ".join(f"{a}={v['genome']}" for a, v in plan["arms"].items()),
             "code_commit": meta.get("code_commit"), "created": created, "pruned": False}
    append_jsonl(CYCLES_FILE, [{k: v for k, v in cycle.items() if k != "created"}])
    state["cycles"].append(cycle)
    state["current"] = None
    ok = usable > 0
    if ok:
        for f in plan.get("proposal_files", []):
            (INBOX / "done").mkdir(parents=True, exist_ok=True)
            if (INBOX / f).exists():
                shutil.move(str(INBOX / f), INBOX / "done" / f)
    save_state(state)
    log(f"{tag}: batch exit {rc}; {len(records)} runs logged, {usable} scored")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status=f"after cycle {tag}")
    t_consult = time.monotonic()
    log(consult.maybe_consult(cfg, REPO, AI, tag))
    consult_s = round(time.monotonic() - t_consult, 1)
    archive = prune(cfg, state)
    write_ops_row(tag, ops, cycle["finished"], t_fin, consult_s, archive)
    return ok


def adopt_unfinished(cfg: dict) -> bool | None:
    """If a previous learner died mid-cycle, finish that cycle: wait for its batch, then score it.
    None = nothing to adopt; False = STOP appeared while waiting; True/False otherwise = the cycle's outcome."""
    state = load_state()
    cur = state.get("current")
    if not cur:
        return None
    tag = cur["tag"]
    cdir = RUNS / tag
    if tag in {c.get("tag") for c in state["cycles"]} or not (cdir / "plan.json").exists():
        log(f"adopt: {tag} has no plan or is already recorded; clearing it")
        state["current"] = None
        save_state(state)
        return None
    if batch_running(cdir):
        log(f"adopt: {tag}'s batch is still running (the previous learner stopped mid-cycle); waiting for it")
        while batch_running(cdir):
            if not sleep_unless_stopped(2):
                return False
    log(f"adopt: scoring {tag}")
    plan = json.loads((cdir / "plan.json").read_text(encoding="utf-8"))
    return finish_cycle(cfg, state, plan, "adopted")


def _same_path(a: Path, b: Path) -> bool:
    """Equal after normalising separators and, on Windows, case (the file system there ignores case)."""
    return os.path.normcase(os.path.normpath(str(a))) == os.path.normcase(os.path.normpath(str(b)))


def _ours(c: dict, p: Path) -> bool:
    """A path this learner created for cycle `c`, by exact name: its `runs/<tag>/batch` or a lane profile
    `endless-<tag>-*`. Nothing else is ever archived or deleted (test R2). Names compare with casefold and folders with
    os.path.normcase, so a case or separator variant of the SAME folder is still recognised (O3 review finding 8)."""
    tag, name = c["tag"], p.name.casefold()
    return (_same_path(p.parent, RUNS / tag) and name == "batch") or \
           (_same_path(p.parent, PROFILES) and name.startswith(f"endless-{tag}-".casefold()))


def _profile_dirs(c: dict) -> list[Path]:
    """The lane profiles of cycle `c` that `_delete_ours` would delete: every `created` path `_ours` accepts as a
    profile (so never its `batch/`), each folder once (a case or separator variant of the same path is one folder)."""
    out, seen = [], set()
    for p in map(Path, c.get("created", [])):
        key = os.path.normcase(os.path.normpath(str(p)))
        if _ours(c, p) and p.name.casefold() != "batch" and key not in seen:
            seen.add(key)
            out.append(p)
    return out


class ArchiveError(RuntimeError):
    """An archive could not be written or verified, or a delete stopped part-way. No original was lost."""


def _member(name: str, size: int, crc: int) -> dict:
    return {"name": name, "size": size, "crc32": crc}


def _plain(m: dict) -> dict:
    """A manifest member without its `dup_of`: what an original read from disk is compared with."""
    return _member(m["name"], m["size"], m["crc32"])


def _is_link(p: Path) -> bool:
    """A symlink or an NTFS junction (an unreadable entry counts as one: it is never entered)."""
    try:
        return p.is_symlink() or p.is_junction()
    except OSError:
        return True


def _originals(batch: Path) -> list[Path]:
    """Every regular file under `batch`, found WITHOUT following links: a symlink or junction (to a folder or a file) is
    skipped and never entered. `shutil.rmtree` does not follow them either, so the archive's scope equals the delete's
    scope (O3 review finding 6). A folder that cannot be listed raises, so a scan is never silently partial."""
    def fail(error: OSError) -> None:
        raise error

    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(batch, onerror=fail, followlinks=False):
        d = Path(dirpath)
        dirnames[:] = [n for n in dirnames if not _is_link(d / n)]
        out += [d / n for n in filenames if not _is_link(d / n) and (d / n).is_file()]
    return sorted(out)


def _cycle_originals(c: dict) -> dict[str, Path]:
    """member name -> file, for EVERY original of cycle `c`, sorted by name: each regular file under `runs/<tag>/batch`
    (named `batch/<rel>`) and under each lane profile of `_profile_dirs` (named `profiles/<profile>/<rel>`), found by
    `_originals` (no link followed). These are exactly the files `_delete_ours` deletes, so the archive's scope equals
    the delete's scope: before 2026-10-21 (re-verify F6) the profiles were deleted UNARCHIVED, and with them
    badge-log.json, stats.db and the saves, which exist nowhere else. A missing folder contributes nothing."""
    cdir = RUNS / c["tag"]
    out: dict[str, Path] = {}
    if (cdir / "batch").is_dir():
        out.update({f.relative_to(cdir).as_posix(): f for f in _originals(cdir / "batch")})
    for p in _profile_dirs(c):
        if p.is_dir():
            out.update({f"profiles/{p.name}/{f.relative_to(p).as_posix()}": f for f in _originals(p)})
    return dict(sorted(out.items()))


def _stat_sig(files: list[Path]) -> dict[str, tuple[int, int]]:
    """path -> (size, mtime_ns): taken before an archive reads the originals and again just before the delete, so an
    original written to (or a new one created) in between is never deleted."""
    return {str(f): (st.st_size, st.st_mtime_ns) for f in files for st in [f.stat()]}


def _crc_of(f: Path) -> tuple[int, int]:
    crc, size = 0, 0
    with open(f, "rb") as fh:
        while chunk := fh.read(1 << 20):
            crc, size = zlib.crc32(chunk, crc), size + len(chunk)
    return size, crc


def _scan_originals(originals: dict[str, Path]) -> list[dict]:
    """(name, size, CRC32) of each original file, read from disk, in `originals`' order."""
    return [_member(name, *_crc_of(f)) for name, f in originals.items()]


def _dup_key(m: dict) -> tuple[str, int, int]:
    return m["name"].rsplit("/", 1)[-1], m["size"], m["crc32"]


def _dup_index(members: list[dict]) -> dict[tuple[str, int, int], str]:
    """(file name, size, CRC32) -> the first STORED `batch/` member with them: what a profile file may be `dup_of`."""
    index: dict[tuple[str, int, int], str] = {}
    for m in members:
        if m["name"].startswith("batch/") and not m.get("dup_of"):
            index.setdefault(_dup_key(m), m["name"])
    return index


def _plan_members(scanned: list[dict]) -> list[dict]:
    """The manifest members for originals scanned from disk: a `profiles/` member whose file name, size and CRC32
    equal a `batch/` member's is `dup_of` it (stored once: a lane's debug logs are copied into `batch/`, so storing both
    doubles the zip for nothing); every other member is stored. Deterministic, so an interrupted archive re-plans the
    same members from the same bytes (recovery case 2)."""
    index = _dup_index(scanned)
    out = []
    for m in scanned:
        target = index.get(_dup_key(m)) if m["name"].startswith("profiles/") else None
        out.append(dict(m, dup_of=target) if target else m)
    return out


def _copy_member(zf: zipfile.ZipFile, src: Path, name: str) -> dict:
    """Stream one file into the zip, computing its CRC32 from the bytes read (never trusting the zip's own)."""
    info = zipfile.ZipInfo.from_file(src, name, strict_timestamps=False)
    info.compress_type = zipfile.ZIP_DEFLATED
    info._compresslevel = 6  # read by zipfile's compressor for a ZipInfo opened for writing (3.12 and 3.13)
    crc, size = 0, 0
    with open(src, "rb") as fin, zf.open(info, "w", force_zip64=True) as fout:
        while chunk := fin.read(1 << 20):
            crc, size = zlib.crc32(chunk, crc), size + len(chunk)
            fout.write(chunk)
    return _member(name, size, crc)


def verify_archive(zpath: Path, members: list[dict]) -> str | None:
    """None if `zpath` holds EXACTLY the stored `members` (those without `dup_of`: same names, sizes and CRC32s; no
    extra and no missing member), every member decompresses to its stored CRC (`testzip`), and every `dup_of` member's
    target IS in the zip with that member's size and CRC32 (so its bytes are there, under the target's name);
    otherwise the reason. Never raises."""
    try:
        with zipfile.ZipFile(zpath) as zf:
            bad = zf.testzip()
            if bad is not None:
                return f"member {bad} fails its CRC"
            infos = zf.infolist()
            got = {i.filename: i for i in infos}
            want = {m["name"]: m for m in members if not m.get("dup_of")}
            if len({m["name"] for m in members}) != len(members):
                return "the manifest names one member twice"
            if len(infos) != len(got) or len(got) != len(want) or set(got) != set(want):
                return f"members differ: {len(infos)} in the zip, {len(want)} expected"
            for name, m in want.items():
                if got[name].file_size != m["size"]:
                    return f"{name}: size {got[name].file_size} != {m['size']}"
                if got[name].CRC != m["crc32"]:
                    return f"{name}: CRC {got[name].CRC:08x} != the source's {m['crc32']:08x}"
            for m in members:
                if m.get("dup_of"):
                    t = got.get(m["dup_of"])
                    if t is None:
                        return f"{m['name']}: its dup_of {m['dup_of']} is not in the zip"
                    if t.file_size != m["size"] or t.CRC != m["crc32"]:
                        return (f"{m['name']}: its dup_of {m['dup_of']} holds size {t.file_size} CRC {t.CRC:08x}, "
                                f"not {m['size']} {m['crc32']:08x}")
    except Exception as exc:  # noqa: BLE001 - an unreadable zip is a failed verification, never a crash
        return f"unreadable: {exc!r}"[:200]
    return None


def _replace_with_retry(src: Path, dst: Path) -> None:
    """os.replace, retried REPLACE_TRIES times REPLACE_WAIT_S apart on PermissionError (a transient antivirus lock, or a
    reader holding `dst` open). For files that MAY be replaced (state.json, archive_check.json), never for an archive."""
    for attempt in range(1, REPLACE_TRIES + 1):
        try:
            _os_replace(src, dst)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES:
                raise
            log(f"replace {src.name} -> {dst.name} is locked (attempt {attempt}/{REPLACE_TRIES}); retrying")
            time.sleep(REPLACE_WAIT_S)


def _rename_no_overwrite(src: Path, dst: Path) -> None:
    """Rename `src` to `dst`, NEVER replacing an existing `dst`: it is checked first, and os.rename also refuses on
    Windows. Retried like `_replace_with_retry` on PermissionError. Every archive file is placed through this."""
    for attempt in range(1, REPLACE_TRIES + 1):
        if os.path.lexists(dst):
            raise FileExistsError(f"{dst} already exists: an archive file is never overwritten")
        try:
            _os_rename(src, dst)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES:
                raise
            log(f"rename {src.name} -> {dst.name} is locked (attempt {attempt}/{REPLACE_TRIES}); retrying")
            time.sleep(REPLACE_WAIT_S)


def _remove_part(part: Path) -> None:
    try:
        part.unlink(missing_ok=True)
    except OSError as exc:
        log(f"could not remove {part} ({exc!r}); the next prune removes it")


def _read_manifest(path: Path) -> dict | None:
    """The manifest, or None when it cannot be read or any member is not a well-formed {name, size, crc32} (plus, for
    a profile file stored once through its batch twin, a string `dup_of`)."""
    try:
        man = json.loads(path.read_text(encoding="utf-8"))
        members = man.get("members")
        ok = isinstance(members, list) and all(
            isinstance(m, dict) and isinstance(m.get("name"), str) and isinstance(m.get("size"), int)
            and isinstance(m.get("crc32"), int) and isinstance(m.get("dup_of", ""), str) for m in members)
        return man if ok else None
    except (OSError, ValueError, AttributeError):
        return None


def _write_manifest(cdir: Path, tag: str, members: list[dict]) -> None:
    dups = [m for m in members if m.get("dup_of")]
    man = {"tag": tag, "written": now(), "n_files": len(members), "n_stored": len(members) - len(dups),
           "n_dup": len(dups), "bytes_raw": sum(m["size"] for m in members),
           "bytes_zip": (cdir / ARCHIVE).stat().st_size, "members": members}
    tmp = cdir / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    _rename_no_overwrite(tmp, cdir / MANIFEST)


def _set_aside(cdir: Path) -> str:
    """Rename `raw.zip` and `raw.manifest.json` (whichever exist) to `<name>.bad.<k>`, k the smallest integer >= 1 used
    by neither. Never overwrites; nothing ever renames or deletes a `.bad.<k>` file. Returns the zip's new name."""
    k = 1
    while any(os.path.lexists(cdir / f"{n}.bad.{k}") for n in (ARCHIVE, MANIFEST)):
        k += 1
    for n in (ARCHIVE, MANIFEST):
        if os.path.lexists(cdir / n):
            _rename_no_overwrite(cdir / n, cdir / f"{n}.bad.{k}")
    return f"{ARCHIVE}.bad.{k}"


def _set_aside_logged(tag: str, cdir: Path, reason: str) -> str:
    name = _set_aside(cdir)
    log(f"{tag}: raw.zip cannot be trusted ({reason}); SET ASIDE as {name} (kept forever). Every original is still on "
        f"disk; they are archived afresh at the next prune")
    return f"set aside as {name}: {reason}"


def _hold(c: dict, reason: str) -> str:
    """HOLD a cycle the code cannot prove safe: touch no file, flag it for a human, keep the learner running."""
    c["held"] = {"reason": reason, "since": now()}
    log(f"{c['tag']}: HELD FOR REVIEW: {reason}. NOTHING of this cycle is archived or deleted until a human looks "
        f"(README 'Archive': resolve it, then remove 'held' from this cycle in data/state.json while the learner is "
        f"stopped)")
    return f"HELD: {reason}"


def _in_use(tag: str, cdir: Path, originals: dict[str, Path], cmds: list[tuple[int, str]]) -> str | None:
    """Why cycle `tag` must not be archived or deleted yet, or None when it is QUIET: no batch runner writes into it,
    no process (an orphaned lane) names its profiles `endless-<tag>-`, and no original (a batch file OR a lane-profile
    file: a lane writes its profile's save, stats.db and logs) changed within QUIET_MINUTES."""
    if batch_running(cdir, cmds):
        return "its batch runner is alive"
    marker = f"endless-{tag}-"
    for pid, cmd in cmds:
        if marker in cmd:
            return f"process {pid} names {marker}*"
    cutoff = time.time() - 60 * QUIET_MINUTES
    for name, f in originals.items():
        if f.stat().st_mtime > cutoff:
            return f"{name} was modified within the last {QUIET_MINUTES} min"
    return None


def _delete_ours(c: dict) -> None:
    """Delete every `created` path of cycle `c` that `_ours` accepts (its batch/, then its lane profiles), and nothing
    else. Errors are ignored here: the caller checks what is left and raises (a partial delete is recovery case 4)."""
    for p in map(Path, c.get("created", [])):
        if _ours(c, p) and p.exists():
            shutil.rmtree(p, ignore_errors=True)


#: archive_cycle outcomes that did no archive work: not counted toward max_archives_per_prune.
NOT_AN_ATTEMPT = ("no raw logs", "in use", "HELD")


def archive_cycle(c: dict, cmds: list[tuple[int, str]] | None = None) -> str:
    """Archive one cycle's originals, then delete them: every file of its `batch/` and of its lane profiles (by `_ours`;
    `_cycle_originals` names them `batch/<rel>` and `profiles/<profile>/<rel>` inside the zip).

    THE INVARIANT: NO original (batch or profile) is deleted unless its exact bytes (name, size, CRC32) are in a
    VERIFIED archive: stored as a zip member, or (a profile file byte-identical to a batch file of the same name,
    `_plan_members`) recorded in the manifest as `dup_of` a stored member that `verify_archive` checks has its size and
    CRC32. No archive file is ever overwritten or deleted. What the code cannot prove safe is HELD (`_hold`): no file
    touched.

    Fresh: write `raw.zip.part` (batch members first, then each profile file: `dup_of` its batch twin, else stored) ->
    verify it against the CRC32s read from the originals -> rename (never over an existing file) to `raw.zip` -> write
    `raw.manifest.json` -> re-check that no original changed -> delete -> check nothing is left -> set the flags.
    Before ANY archive or delete the cycle must be quiet (`_in_use`; skipped this boundary otherwise, not held).
    Recovery, when `raw.zip` exists beside originals O (batch AND profile files; M = the manifest's members):
      1. a manifest file that cannot be read -> HOLD;
      2. no manifest (deletion never starts before it is written): the zip verifies EXACTLY against O, planned as a
         fresh archive plans it -> write the manifest and delete; otherwise SET ASIDE the zip (`_set_aside`) and archive
         afresh at the next prune;
      3. every manifest member is still an original (the delete had not started): the zip verifies against M and O == M
         -> delete; otherwise SET ASIDE the zip and its manifest (every original is still on disk; a manifest written
         before profiles were archived lacks them, so it is set aside and the cycle archived afresh);
      4. some manifest member is gone (a delete stopped part-way; the zip is the ONLY copy of those): the zip verifies
         against M, every remaining original equals its manifest entry and there is no extra original -> resume the
         delete; otherwise HOLD.

    ACCEPTED RESIDUAL RISK (re-verify 2026-10-21, measured): the last re-stat and the delete are not one atomic step. A
    write that lands AFTER the re-stat is deleted with its file; measured 0.16 ms from the re-stat to the start of the
    delete and 118 ms to its end, on a batch shaped like a real one (96 files, 1.6 GB; measured before the profiles were
    archived: the delete now also removes 12-16 profiles of about 46 MB and 13 files each, so its end comes later). Its
    preconditions: the writer was silent for QUIET_MINUTES (60 min), holds no open handle on the file, and no process
    command line names the cycle (`_in_use`). Closing it (rename the folder away, re-stat the renamed tree, then
    delete) is not built.

    Returns what happened; raises (no original lost, no `.part` left) when an archive cannot be written or verified or
    a delete stops part-way. `cmds`: a `_cmdlines()` snapshot shared by one prune (a scan costs about 0.5 s)."""
    tag = c["tag"]
    cdir = RUNS / tag
    batch, zpath, part, mpath = cdir / "batch", cdir / ARCHIVE, cdir / ARCHIVE_PART, cdir / MANIFEST
    if os.path.lexists(batch):
        if _is_link(batch) or not batch.is_dir():
            return _hold(c, "runs/<tag>/batch is a link, a junction or a file, not a plain folder")
        if not any(_ours(c, p) and p.name.casefold() == "batch" for p in map(Path, c.get("created", []))):
            return _hold(c, "runs/<tag>/batch exists on disk but no `created` entry of this cycle names it")
    for p in _profile_dirs(c):
        if os.path.lexists(p) and (_is_link(p) or not p.is_dir()):
            return _hold(c, f"lane profile {p.name} is a link, a junction or a file, not a plain folder")
    originals = _cycle_originals(c)
    why = _in_use(tag, cdir, originals, list(_cmdlines()) if cmds is None else cmds)
    if why:
        return f"in use ({why}); retried next boundary"
    if not originals:  # no file in batch/ OR in any lane profile: only empty folders are left to delete (tests R1/R2)
        _delete_ours(c)
        if zpath.exists():
            c["archived"] = True
        c["pruned"] = True
        return "no raw logs (no file in batch/ or its lane profiles) to archive; deleted its empty leftovers"
    sig = _stat_sig(list(originals.values()))
    if zpath.exists():
        sources = _scan_originals(originals)
        o = {s["name"]: s for s in sources}
        if not os.path.lexists(mpath):  # case 2
            planned = _plan_members(sources)
            reason = verify_archive(zpath, planned)
            if reason:
                return _set_aside_logged(tag, cdir, f"no manifest, and it does not match the originals exactly: "
                                                    f"{reason}")
            _write_manifest(cdir, tag, planned)
            how = "completed an interrupted archive (raw.zip verified exactly against the originals; manifest written)"
        else:
            man = _read_manifest(mpath)
            if man is None:  # case 1
                return _hold(c, f"{MANIFEST} exists but cannot be read")
            m = {x["name"]: _plain(x) for x in man["members"]}
            reason = verify_archive(zpath, man["members"])
            missing = sorted(set(m) - set(o))
            if not missing:  # case 3: the delete had not started
                if not reason and o != m:
                    reason = "the originals differ from the manifest"
                if reason:
                    return _set_aside_logged(tag, cdir, reason)
                how = "resumed: raw.zip re-verified against its manifest and the identical originals"
            else:  # case 4: a delete stopped part-way; raw.zip is the only copy of the missing originals
                extra = sorted(set(o) - set(m))
                changed = sorted(n for n in o if n in m and o[n] != m[n])
                if reason or extra or changed:
                    return _hold(c, f"a delete stopped part-way ({len(missing)} of {len(m)} archived originals are "
                                    f"gone) and " + (f"raw.zip fails verification: {reason}" if reason else
                                                     f"the remaining originals no longer match the manifest: "
                                                     f"changed {changed[:3]}, new {extra[:3]}"))
                how = "resumed an interrupted delete: raw.zip re-verified against its manifest and the remaining originals"
    else:
        if os.path.lexists(mpath):  # a manifest without its zip: a set-aside interrupted between its two renames
            log(f"{tag}: {MANIFEST} without its raw.zip; set aside as {_set_aside(cdir).replace(ARCHIVE, MANIFEST)}")
        cdir.mkdir(parents=True, exist_ok=True)  # runs/<tag>/ may be gone while its lane profiles remain
        try:
            with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6,
                                 strict_timestamps=False) as zf:
                members = [_copy_member(zf, f, name) for name, f in originals.items() if name.startswith("batch/")]
                index = _dup_index(members)  # every batch member is stored before any profile file is planned
                for name, f in originals.items():
                    if name.startswith("batch/"):
                        continue
                    size, crc = _crc_of(f)
                    target = index.get((name.rsplit("/", 1)[-1], size, crc))
                    members.append(dict(_member(name, size, crc), dup_of=target) if target else
                                   _copy_member(zf, f, name))
            reason = verify_archive(part, members)
            if reason:
                raise ArchiveError(f"{tag}: the new archive failed verification: {reason}")
            _rename_no_overwrite(part, zpath)
        except BaseException:
            _remove_part(part)
            raise
        _write_manifest(cdir, tag, members)
        how = "archived"
    # written to (or a file added) while it was being read, in batch/ OR a lane profile: delete nothing
    if _stat_sig(list(_cycle_originals(c).values())) != sig:
        log(f"{tag}: an original changed while it was being archived; NOTHING deleted, retried next boundary")
        return "changed while archiving: nothing deleted; retried next boundary"
    _delete_ours(c)
    left = [p.name for p in [batch] + _profile_dirs(c) if os.path.lexists(p)]
    if left:
        raise ArchiveError(f"{tag}: raw.zip is verified but {left[:3]} could not be fully deleted; retried next prune")
    c["archived"] = c["pruned"] = True
    man = _read_manifest(mpath) or {}
    raw, packed = man.get("bytes_raw", 0), man.get("bytes_zip", 0)
    return (f"{how}: {man.get('n_files')} files ({man.get('n_stored', '?')} stored, {man.get('n_dup', '?')} dup_of a "
            f"batch file), {raw / 2**20:.0f} MB -> {packed / 2**20:.1f} MB; raw logs and lane profiles deleted")


def prune(cfg: dict, state: dict) -> dict:
    """Archive, then delete, the raw logs and lane profiles of all but the newest `keep_raw_cycles` cycles (at most
    `max_archives_per_prune` archives a call, which bounds the cycle-boundary delay). Only paths this learner created
    and recorded, and only names it would have created. HELD cycles are skipped (and listed once per call). It NEVER
    raises an Exception into the loop: the WHOLE body is guarded, a failure is logged and the next boundary retries,
    and no original is ever deleted without a verified archive. Under ARCHIVE_FLOOR_GB free it does nothing at all.

    Returns {"seconds": wall time of this call, "bytes": total size of the `raw.zip` files it WROTE} for the ops
    ledger (O6): a zip that did not exist before a cycle's archive and exists after it counts, even if the delete
    after it then failed (its bytes are on disk). A failed prune still returns what it measured up to the failure."""
    stats = {"seconds": 0.0, "bytes": 0}
    t0 = time.monotonic()
    try:
        _prune(cfg, state, stats)
    except Exception:  # noqa: BLE001 - never into the loop
        try:
            log(f"prune FAILED (nothing more is archived this boundary; the next one retries):\n"
                f"{traceback.format_exc()}")
        except Exception:  # noqa: BLE001 - even the log may be unwritable; the loop must go on
            pass
    stats["seconds"] = round(time.monotonic() - t0, 2)
    return stats


def _zip_written(zpath: Path, existed: bool) -> int:
    """Bytes of `zpath` if this archive attempt created it, else 0. Never raises (an unreadable size counts 0)."""
    try:
        return 0 if existed or not zpath.exists() else zpath.stat().st_size
    except OSError:
        return 0


def _prune(cfg: dict, state: dict, stats: dict | None = None) -> None:
    stats = {"seconds": 0.0, "bytes": 0} if stats is None else stats
    every = state.get("cycles", [])
    cycles = [c for c in every if isinstance(c, dict) and c.get("tag")]
    for c in cycles:  # a `.part` is never live outside archive_cycle: one left over is from a killed run
        if c.get("held"):  # a HELD cycle's folder is touched by nobody but a human
            continue
        part = RUNS / c["tag"] / ARCHIVE_PART
        if part.exists():
            _remove_part(part)
            log(f"{c['tag']}: removed a leftover {ARCHIVE_PART} (an archive interrupted earlier; its raw logs are "
                f"intact)")
    free = free_gb()
    if free < ARCHIVE_FLOOR_GB:
        log(f"prune: only {free:.1f} GB free, below the {ARCHIVE_FLOOR_GB} GB an archive needs: archiving and "
            f"deleting NOTHING")
        return
    keep, cap = int(cfg["keep_raw_cycles"]), int(cfg.get("max_archives_per_prune", 3))
    attempts, cmds = 0, None
    for c in every[:-keep] if keep > 0 else every:
        if not isinstance(c, dict) or not c.get("tag") or c.get("pruned") or c.get("held"):
            continue
        if attempts >= cap:
            log(f"prune: {cap} archive(s) this boundary (max_archives_per_prune); the rest wait for the next one")
            break
        if cmds is None:
            cmds = list(_cmdlines())  # one process scan per boundary
        zpath = RUNS / c["tag"] / ARCHIVE
        had_zip = zpath.exists()
        try:
            outcome = archive_cycle(c, cmds)
            if not outcome.startswith(NOT_AN_ATTEMPT):
                attempts += 1
            log(f"{c['tag']}: {outcome} (its run records are kept)")
        except Exception:  # noqa: BLE001 - never into the loop; the raw logs stay and the next boundary retries
            attempts += 1
            log(f"{c['tag']}: archiving FAILED, its raw logs are KEPT and it is retried at the next boundary:\n"
                f"{traceback.format_exc()}")
        finally:
            stats["bytes"] += _zip_written(zpath, had_zip)
        save_state(state)  # per cycle: a crash after this archive cannot lose its flags
    held = [c["tag"] for c in cycles if c.get("held")]
    if held:
        log(f"prune: held for review: {', '.join(held)} (nothing of theirs is touched; `learner.py archive-check` "
            f"lists why)")
    save_state(state)


def disk_guard(cfg: dict, state: dict) -> bool:
    """Before a batch: True = enough free disk to start it. Under `min_free_gb` it ARCHIVES every cycle but the
    newest (never a delete without a verified archive); if still short it writes ATTENTION.md and the learner stops.
    Under ARCHIVE_FLOOR_GB prune archives and deletes nothing, so the learner stops with the raw logs intact.
    prune never raises, but reading free disk or writing ATTENTION.md can: `loop` guards this call (it logs, starts no
    batch, waits idle_wait_minutes and tries again)."""
    if free_gb() >= float(cfg["min_free_gb"]):
        return True
    prune({**cfg, "keep_raw_cycles": 1, "max_archives_per_prune": 10 ** 6}, state)
    free = free_gb()
    if free >= float(cfg["min_free_gb"]):
        return True
    if free < ARCHIVE_FLOOR_GB:
        attention(f"Only {free:.1f} GB free on this disk: below the {ARCHIVE_FLOOR_GB} GB an archive needs, so the "
                  f"learner archived and deleted NOTHING and did not start the next batch. Free some space.")
    else:
        attention(f"Only {free:.0f} GB free on this disk after archiving old raw logs; config min_free_gb is "
                  f"{cfg['min_free_gb']}.")
    return False


#: The early archive keeps this many newest cycles raw (spec S1-3), whatever `keep_raw_cycles` says.
EARLY_KEEP_RAW = 2


def early_archive(cfg: dict, state: dict) -> dict | None:
    """O7, called by `loop` BEFORE `disk_guard`: when free disk is under `min_free_gb + early_prune_margin_gb` (25 + 15
    = 40 GB by default), run the ordinary archive `prune` with `keep_raw_cycles` EARLY_KEEP_RAW (2).

    WHY: with keep_raw_cycles 20 the raw logs and lane profiles hold about 26 GB (measured on the clone 2026-10-21,
    the S1-3 real run), and the only other relief is `disk_guard` at 25 GB,
    which stops the learner if archiving all but one cycle is not enough. Archiving earlier, while there is room to
    write the zips, keeps the learner running. It is `prune` itself, so it ARCHIVES and never deletes without a
    verified archive (O3), skips HELD cycles and cycles not yet quiet, does nothing under ARCHIVE_FLOOR_GB, and keeps
    the per-call cap `max_archives_per_prune` (it runs at every loop pass, idle waits included, so it continues at the
    next pass). Returns prune's {"seconds", "bytes"} when it ran, None when free disk is above the threshold. prune
    never raises; reading free disk can, and `loop` guards this call like `disk_guard`."""
    margin = float(cfg.get("early_prune_margin_gb", DEFAULTS["early_prune_margin_gb"]))
    threshold = float(cfg["min_free_gb"]) + margin
    free = free_gb()
    if free >= threshold:
        return None
    log(f"early archive: {free:.1f} GB free, under min_free_gb + early_prune_margin_gb = {threshold:.0f} GB: archiving "
        f"all but the newest {EARLY_KEEP_RAW} cycles (up to {cfg.get('max_archives_per_prune', 3)} this pass)")
    stats = prune({**cfg, "keep_raw_cycles": EARLY_KEEP_RAW}, state)
    log(f"early archive: {stats['seconds']:.0f} s, {stats['bytes'] / 2 ** 20:.1f} MB of zips written; "
        f"{free_gb():.1f} GB free now")
    return stats


def sleep_unless_stopped(minutes: float) -> bool:
    """False if STOP appeared while waiting."""
    end = time.time() + 60 * minutes
    while time.time() < end:
        if STOP.exists():
            return False
        time.sleep(min(30.0, max(0.0, end - time.time())))
    return True


def loop(single: bool, dev: bool = False) -> int:
    if not DEPLOYMENT.exists() and not dev:
        print(f"This is not the learner's deployment checkout ({DEPLOYMENT} is missing). The learner runs from its own "
              f"clone so development commits cannot abort its batches: see README.md 'Where it runs'. Pass --dev to "
              f"run here anyway (smoke tests only).")
        return 2
    why = acquire_lock_waiting_for_archive()  # a manual `learner.py archive` is waited for, not refused (O3 review)
    if why == "STOP":
        return 0
    if why:
        print(why)
        return 2
    started_sig, refused_sig = code_signature(), None
    log(f"learner started (code {started_sig})")
    try:
        if load_state().get("parser_version") != scoring.PARSER_VERSION and not single:
            # A parser upgrade arrived (e.g. through auto_update): re-read every retained batch once.
            cmd_reparse()
            st = load_state()
            st["parser_version"] = scoring.PARSER_VERSION
            save_state(st)
        adopted = adopt_unfinished(load_config())
        if adopted is False and STOP.exists():
            return 0
        while True:
            if STOP.exists():
                log("STOP file found: stopping (delete ai-agent/STOP to allow the next start)")
                return 0
            if ATTENTION.exists():
                log(f"{ATTENTION} exists: not starting a cycle until it is resolved and deleted")
                return 0
            if load_config().get("auto_update") and not single:
                msg = update_checkout()
                if msg:
                    log(msg)
            sig = code_signature()
            if not single and sig != started_sig and sig != refused_sig:
                if tests_pass():
                    log(f"code changed ({started_sig} -> {sig}) and test_agent.py passes: restarting into it")
                    return RESTART_CODE
                refused_sig = sig
                log(f"code changed ({sig}) but test_agent.py FAILS: keeping the running version {started_sig}")
            cfg, state = load_config(), load_state()
            try:
                early_archive(cfg, state)  # O7: archive early under min_free_gb + margin, before the floor path
                room = disk_guard(cfg, state)
            except Exception:  # noqa: BLE001 - a failed disk check must not kill the 24/7 process; start no batch
                log(f"disk check FAILED: no batch started; trying again in {cfg['idle_wait_minutes']} min:\n"
                    f"{traceback.format_exc()}")
                if single or not sleep_unless_stopped(float(cfg["idle_wait_minutes"])):
                    return 0
                continue
            if not room:
                return 0
            batches, singles = other_bots_running()
            if not cfg["wait_if_other_bots_running"]:
                batches = []
            lanes, how = size_lanes(cfg, len(singles))
            if batches or lanes < 8:
                log(f"waiting {cfg['idle_wait_minutes']} min: " + (f"another batch is running: {batches[:3]}"
                                                                    if batches else
                                                                    f"only {lanes} lanes available ({how})"))
                if single or not sleep_unless_stopped(float(cfg["idle_wait_minutes"])):
                    return 0
                continue
            log(f"lanes = {lanes} ({how})" + (f"; {len(singles)} single bot(s) open, a thread reserved for each"
                                              if singles else ""))
            try:
                ok = run_cycle(cfg, state, lanes)
            except Exception:
                log(f"cycle crashed:\n{traceback.format_exc()}")
                state = load_state()
                state["current"] = None
                save_state(state)
                ok = False
            state = load_state()
            state["failures"] = 0 if ok else state.get("failures", 0) + 1
            save_state(state)
            if state["failures"] >= int(cfg["max_consecutive_failures"]):
                attention(f"{state['failures']} cycles in a row produced no scored runs. Read data/learner.log and "
                          f"the newest runs/<tag>/x4.out.txt.")
                return 0
            if single:
                return 0 if ok else 1
            if not ok and not sleep_unless_stopped(10):
                return 0
    finally:
        release_lock()


# ---------------------------------------------------------------------------------------------------------- commands
def cmd_ingest(batch_dir: str) -> int:
    path = str(Path(batch_dir).resolve())
    state = load_state()
    if path not in state.setdefault("ingested", []):
        state["ingested"].append(path)
        save_state(state)
    existing = {(r.get("batch"), r.get("lane"), r.get("log")) for r in load_jsonl(RUNS_FILE)}
    records = [r for r in scoring.parse_batch(Path(path), "ingest")
               if (r.get("batch"), r.get("lane"), r.get("log")) not in existing]
    for r in records:
        r["genome_id"] = brain.genome_id(r["genome"])
    append_jsonl(RUNS_FILE, records)
    if records:
        append_jsonl(CYCLES_FILE, [{"source": "ingest", "tag": f"ingest {records[0]['batch']}", "finished": now(),
                                    "exit": "-", "runs": len(records), "path": path,
                                    "usable": sum(1 for r in records if r["usable"]), "arms_label": "step-14 arms"}])
    log(f"ingested {len(records)} new runs from {path}")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="ingested")
    return 0


def cmd_reparse() -> int:
    """Re-read every batch whose raw logs still exist; keep the records of batches already pruned."""
    state = load_state()
    sources = {}
    for c in state["cycles"]:
        b = RUNS / c["tag"] / "batch"
        if (b / "ARMS.json").exists():
            sources[str(b)] = c["tag"]
    for p in state.get("ingested", []):
        if (Path(p) / "ARMS.json").exists():
            sources[p] = "ingest"
    fresh, covered = [], set()
    for path, label in sources.items():
        recs = scoring.parse_batch(Path(path), label)
        for r in recs:
            r["genome_id"] = brain.genome_id(r["genome"])
        fresh += recs
        if recs:  # a batch whose logs are gone yields nothing: its OLD records must then be kept, not dropped (R9)
            covered.add(json.loads((Path(path) / "ARMS.json").read_text(encoding="utf-8")).get("stamp"))
    old = load_jsonl(RUNS_FILE)
    kept = [r for r in old if r.get("batch") not in covered]
    write_jsonl(RUNS_FILE, kept + fresh)
    log(f"reparse: {len(fresh)} records re-read from {len(sources)} batches; {len(kept)} kept from pruned batches")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="reparsed")
    return 0


def cmd_plan() -> int:
    cfg, state = load_config(), load_state()
    batches, singles = other_bots_running()
    lanes, how = size_lanes(cfg, len(singles))
    print(f"lanes = {lanes} ({how}); other batches: {batches or 'none'}; single bots: {len(singles)}")
    if lanes < 8:
        print("fewer than 8 lanes available: the learner would wait")
        return 0
    plan = plan_cycle(cfg, state, lanes)
    for a, v in plan["arms"].items():
        print(f"arm {a}: {v['genome']} {v['label']}\n    why: {v['why']}")
    print("command:", " ".join(batch_command(plan, RUNS / plan["tag"])))
    return 0


def cmd_status() -> int:
    state, cfg = load_state(), load_config()
    cur = state.get("current")
    alive = bool(cur) and batch_running(RUNS / cur["tag"])
    pid = LOCK.read_text().strip() if LOCK.exists() else None
    learner_alive = bool(pid) and pid.isdigit() and psutil.pid_exists(int(pid))
    print(f"learner process: {'RUNNING (pid ' + pid + ')' if learner_alive else 'NOT running'}")
    print(f"current cycle: {cur}; its batch is {'RUNNING' if alive else 'not running'}")
    print(f"cycles started: {state['cycle']}; failures in a row: {state.get('failures', 0)}; "
          f"design row next: {state.get('design_next', 0)}")
    print(f"runs recorded: {len(load_jsonl(RUNS_FILE))}; free disk: {free_gb():.0f} GB; "
          f"raw cycles kept: {cfg['keep_raw_cycles']}; archived cycles: {len(list(RUNS.glob('*/' + ARCHIVE)))}")
    held = held_cycles()
    print(f"held for review: {len(held)}" + (f" ({', '.join(t for t, _ in held)}; `learner.py archive-check` says why)"
                                              if held else ""))
    print(f"STOP file: {STOP.exists()}; ATTENTION: {ATTENTION.exists()}; consult: {cfg['consult']['enabled']}")
    print(f"findings: {FINDINGS / 'LATEST.md'}")
    return 0


def cmd_archive() -> int:
    """Archive every cycle outside keep_raw_cycles now; meant for when the learner is STOPPED. It takes the learner's
    lock, so it REFUSES while the 24/7 learner runs (its own prune would race this one); `acquire_lock` replaces only a
    STALE lock. A learner started meanwhile WAITS for it (`acquire_lock_waiting_for_archive`), up to LOCK_WAIT_MAX_MIN."""
    why = acquire_lock()
    if why:
        print(f"archive refused: {why}. The running learner archives at each cycle boundary by itself.")
        return 2
    try:
        cfg, state = load_config(), load_state()
        prune({**cfg, "max_archives_per_prune": 10 ** 6}, state)
        print(f"archived; see {LOG}")
        return 0
    finally:
        release_lock()


def cmd_archive_check() -> int:
    """READ-ONLY re-verification of every `runs/<tag>/raw.zip` against its manifest: one OK/BAD line per zip, then one
    `HELD <tag> <reason>` line per cycle held for review; exit 1 on any BAD or HELD. Its result (with a timestamp, the
    held count and the count of set-aside `raw.zip.bad.<k>`) also goes to `data/archive_check.json`, which
    `tools/status.py` shows."""
    lines, bad = [], 0
    for zpath in sorted(RUNS.glob(f"*/{ARCHIVE}")):
        tag = zpath.parent.name
        man = _read_manifest(zpath.parent / MANIFEST)
        reason = verify_archive(zpath, man["members"]) if man else f"no readable {MANIFEST}"
        if reason:
            bad += 1
            lines.append(f"BAD {tag} {reason}")
        else:
            lines.append(f"OK {tag} {len(man['members'])} {zpath.stat().st_size}")
    n_archives = len(lines)
    held = held_cycles()
    lines += [f"HELD {tag} {reason}" for tag, reason in held]
    set_aside = len(list(RUNS.glob(f"*/{ARCHIVE}.bad.*")))
    print("\n".join(lines) if lines else "no archives yet")
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "archive_check.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps({"checked": now(), "archives": n_archives, "bad": bad, "held": len(held),
                               "set_aside": set_aside, "lines": lines}, indent=1), encoding="utf-8")
    _replace_with_retry(tmp, out)
    return 1 if bad or held else 0


def held_cycles() -> list[tuple[str, str]]:
    """(tag, reason) of every cycle HELD for review (`_hold`). An unreadable state.json is reported as one."""
    try:
        return [(c["tag"], str((c["held"] or {}).get("reason", "?"))) for c in load_state().get("cycles", [])
                if isinstance(c, dict) and c.get("held")]
    except Exception as exc:  # noqa: BLE001 - a check that cannot read the state must not say "nothing held"
        return [("?", f"data/state.json unreadable: {exc!r}"[:160])]


def cmd_publish() -> int:
    PUBLISHED.mkdir(exist_ok=True)
    for src in [FINDINGS / "LATEST.md", FINDINGS / "latest.json", FINDINGS / "DEVELOPER-NOTES.md", RUNS_FILE,
                CYCLES_FILE, LOG]:
        if src.exists():
            shutil.copy2(src, PUBLISHED / src.name)
    print(f"copied into {PUBLISHED}; commit that folder (explicit paths) for a cloud session to read it")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "once", "plan", "ingest", "reparse", "report", "status", "publish",
                                        "archive", "archive-check"])
    ap.add_argument("batch_dir", nargs="?")
    ap.add_argument("--lanes", default=None, help="override config.json's lanes for this process (e.g. a smoke test)")
    ap.add_argument("--minutes", type=float, default=None, help="override config.json's cycle_minutes")
    ap.add_argument("--dev", action="store_true", help="allow run/once outside the deployment clone (smoke tests)")
    a = ap.parse_args()
    if a.lanes is not None:
        DEFAULTS["_override_lanes"] = a.lanes
    if a.minutes is not None:
        DEFAULTS["_override_minutes"] = a.minutes
    if a.command in ("run", "once"):
        return loop(single=a.command == "once", dev=a.dev)
    if a.command == "ingest":
        if not a.batch_dir:
            ap.error("ingest needs a batch directory")
        return cmd_ingest(a.batch_dir)
    if a.command == "report":
        report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="report")
        print(FINDINGS / "LATEST.md")
        return 0
    return {"plan": cmd_plan, "status": cmd_status, "publish": cmd_publish, "reparse": cmd_reparse,
            "archive": cmd_archive, "archive-check": cmd_archive_check}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
