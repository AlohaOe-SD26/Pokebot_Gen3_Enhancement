"""Back up the 24/7 learner's small, irreplaceable data OFF the C: drive (backlog O4, build spec S1-2).

WHY THIS EXISTS. The bot tuner (`ai-agent/` in the deployment clone `C:/Remote Projects/pokebot-learner`) keeps its
whole memory in a few files: `data/runs.jsonl` (every scored run), `cycles.jsonl`, `state.json`, the consult log, the
findings and the inbox of proposals. They live only on C:, which is also the disk the learner fills with raw logs.
One failed disk, one bad `reparse`, or one wiped clone loses weeks of runs that cannot be re-played. This tool makes a
nightly zip of those files on a DIFFERENT physical disk (`Z:/pokebot-backups/learner`, the 4 TB HDD, chosen by the user
on 2026-10-21, USER RULING 42; set in `ops_config.json`) and keeps the newest 14.

DESIGN, AND THE REASON FOR EACH PART
- Stdlib only, and it imports NOTHING from the learner: a learner change must never be able to break its own backup,
  and the scheduled task runs this file with `-3.12 -B` so no `__pycache__` is written into the clone.
- READ-ONLY on the clone. It never writes under the clone (it refuses a destination or a restore target there), so it
  can never create a tracked change that would silently stop the clone's auto-update (spec fact 2).
- REFUSE, never guess: a destination on the same volume as the source (a "backup" on the disk it protects is not a
  backup), under `min_dest_free_gb` free, or not writable -> nothing is written, the status file says why, exit 2.
- A CONSISTENT copy of files the learner is appending to right now: each `.jsonl`/`.log` is read in binary up to the
  size seen when it was opened and trimmed to the last newline. The learner appends without fsync, so the tail can be
  half a line; a backup must hold only whole lines. `state.json` is read and parsed, with retries (it is replaced
  atomically, but a read can still race the replace).
- Each source is opened, read in ONE call and closed at once. While any handle is open on Windows, the learner's own
  `tmp.replace(state.json)` fails with PermissionError; sharing delete does not help (measured, see `_open_read`). A
  backup must never be able to hurt the thing it protects, so the hold stays at milliseconds. That makes a collision
  RARE, not impossible: the 1 AM start is NOT guaranteed to fall inside a batch (review 2026-10-21: cycle boundaries
  drift and reset on every restart), and 40 back-to-back backups against a looping writer made 502 of its 12,187
  replaces fail. The real fix is a retried replace on the LEARNER's side (review finding 2), not anything here.
- Write `.part`, VERIFY (zip tests clean, every member's sha256 equals what was captured, every `.jsonl` line parses,
  `state.json` parses), rename, and only THEN consider retention. A failed backup deletes its own `.part` and NEVER
  prunes an old backup: the old ones are then the only good copies.
- RETENTION IS HELD (the new zip is KEPT, nothing is pruned, status ok false with a `NEEDS-YOU` reason, exit 1 so Task
  Scheduler shows a failure) when the capture looks like a LOSS rather than a backup: runs.jsonl was not captured at
  all, or it has FEWER lines than the largest copy in any existing backup, or an existing backup is named LATER than
  now (the clock went backwards). WHY: a wiped clone or a bad reparse produces a perfectly valid zip of the damage,
  and pruning on it deletes one good copy a night until none is left (review finding 0 measured exactly that: after
  15 such nights, 0 of 14 zips still held runs.jsonl). Compared with the LARGEST copy, not the newest, because a held
  night's own zip would otherwise become the baseline and pruning would resume the next night. To release a
  legitimate shrink (a reparse run on purpose), move the older, larger zips into a sub-folder of the destination:
  neither retention nor this comparison looks inside one.
- Retention touches only files matching `^learner-data-[0-9]{8}-[0-9]{4}\\.zip$`, and never the zip this run wrote.
  The sweep removes only this tool's own `.part` files of that stem, and only when they are over an hour old. ASCII
  `[0-9]`, never a bare `\\d`: in a str pattern `\\d` matches any Unicode digit, and such a name took a keep slot.
- ONE RUN AT A TIME: an `O_EXCL` lock file (`.backup_learner.lock`) in the destination. A second run is REFUSED (exit
  2), because two concurrent runs in one minute deleted each other's `.part`. A lock over 2 hours old (a killed run)
  is stale and replaced, with a WARN.
- The OPS FOLDER (`ops_dir` in ops_config.json, `%LOCALAPPDATA%/pokebot-ops`: the watchdog's samples and state once
  S1-4 exists, the backup status) is captured too. It is an EXPLICIT key (it used to be the status file's folder,
  implicitly), and preflight REFUSES a destination or a clone under it and an ops tree over 200 MB: a destination
  inside it made each zip contain every earlier one (review finding 3: 52 KB to 3.4 GB in 19 runs, read into RAM).
- `backup_status.json` (time, zip, bytes, ok, warnings, error) goes to `%LOCALAPPDATA%/pokebot-ops/`, never into the
  clone. It will be read by the S1-4 watchdog and tools/status.py.

OTHER MODES
- `--restore-check ZIP --into DIR`: the restore drill. Extracts into an EMPTY dir (refuses a non-empty one and any dir
  under the clone), re-checks every sha256 against the manifest, parses every `.jsonl` and `state.json`.
- `--publish-to DIR`: the weekly repo snapshot. Copies LATEST.md, latest.json, DEVELOPER-NOTES.md, runs.jsonl,
  cycles.jsonl and learner.log from the clone into DIR (the MAIN checkout's `ai-agent/published`, committed later by an
  interactive session with explicit paths). learner.log over 5 MB is published as its last 5,000 lines; a data file
  is never cut (it is published whole, with a NOTE when it is over 5 MB). The 24/7 process
  never commits, and nothing is written in the clone (running the learner's own `publish` from the clone would write a
  tracked path there once a snapshot is committed, spec fact 2).
- Both modes REFUSE a `\\\\?\\` or UNC (`\\\\server\\share`) target outright, and test "inside the clone" by NAME and
  by IDENTITY (`os.path.samefile` of the target's nearest existing folder and each of its parents against the clone).
  WHY: `\\\\?\\C:\\...` and `\\\\localhost\\C$\\...` spellings of the clone passed a name-only check (review finding 5).

TEST-ONLY SWITCH: `--test-allow-same-volume` turns the same-volume refusal into a loud WARNING recorded in the report
and the status file. It exists so the tool can be exercised against the REAL clone with a scratch destination on C:
(the selftest's temp folders are on C: too). The installed task never passes it (selftest B9 checks the installer).

Exit codes: 0 ok; 1 the backup or check FAILED, or NEEDS-YOU (retention held, the new zip kept); 2 REFUSED before
writing anything to the destination.
Run: py -3.12 -B tools/ops/backup_learner.py [--config F] [--clone D] [--dest D] [--status-file F] [--ops-dir D]
The scheduled task runs it windowless through pyw.exe: print() is then a no-op, and the status file is the record.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import time
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "ops_config.json"
# [0-9], never a bare \d: in a str pattern \d matches any Unicode digit (review finding 7).
ZIP_RE = re.compile(r"^learner-data-[0-9]{8}-[0-9]{4}\.zip$")
PART_RE = re.compile(r"^learner-data-[0-9]{8}-[0-9]{4}\.zip\.part$")
LOCK_NAME = ".backup_learner.lock"
LOCK_STALE_S = 2 * 3600  # a lock older than this is a killed run's and is replaced
PART_STALE_S = 3600  # the sweep removes only a .part older than this (a younger one may belong to a live run)
OPS_MAX_BYTES = 200 * 1024 * 1024  # the ops tree is read into RAM; anything bigger is not just ops files
MANIFEST = "MANIFEST.json"
APPEND_SUFFIXES = (".jsonl", ".log")  # files the learner APPENDS to: trimmed to the last newline
EXCLUDE_NAMES = {"agent.lock"}
EXCLUDE_SUFFIXES = (".tmp",)
STATE_MEMBER = "ai-agent/data/state.json"
RUNS_MEMBER = "ai-agent/data/runs.jsonl"
STATE_RETRIES = 3
STATE_RETRY_SLEEP = 1.0  # seconds; the selftest sets 0
REPLACE_RETRIES = 5
REPLACE_RETRY_SLEEP = 2.0
PUBLISH_FILES = (("findings", "LATEST.md"), ("findings", "latest.json"), ("findings", "DEVELOPER-NOTES.md"),
                 ("data", "runs.jsonl"), ("data", "cycles.jsonl"), ("data", "learner.log"))
PUBLISH_MAX_BYTES = 5 * 1024 * 1024
PUBLISH_TAIL_LINES = 5000
# Only the LOG is cut to its tail (the spec's rule). runs.jsonl is never cut: measured 2026-10-21 at 10.2 MB in 2,586
# lines (about 3.9 KB a line), a tail of it would publish a partial history that reads as the whole one.
PUBLISH_TAIL_FILES = {"learner.log"}
NEEDS_YOU = "NEEDS-YOU (the new zip was written, verified and KEPT; NOTHING was pruned): "


class Refused(Exception):
    """A precondition failed: nothing was written to the destination."""


# --------------------------------------------------------------------------------------------- probes (patchable)
def volume_id(path: Path) -> int:
    """The volume a path lives on (Windows: the volume serial). The selftest injects this to fake another disk."""
    return os.stat(nearest_existing(path)).st_dev


def free_gb(path: Path) -> float:
    """Free space at a path, in GB (the selftest injects this to fake a full or an empty disk)."""
    return shutil.disk_usage(nearest_existing(path)).free / 1e9


def nearest_existing(path: Path) -> Path:
    p = Path(path).resolve()
    while not p.exists() and p.parent != p:
        p = p.parent
    return p


def _open_read(path: Path):
    """The ONE place a source file is opened (the selftest wraps it to append to a file mid-copy, B2).

    Every caller reads the whole bounded content in one call and closes at once, because while ANY handle is open on
    Windows the learner's `tmp.replace(state.json)` fails with PermissionError (WinError 5). MEASURED 2026-10-21 on
    this PC: opening with FILE_SHARE_DELETE (ctypes CreateFileW) does NOT avoid it, MoveFileEx onto an open target
    is refused either way, so the share-delete open was built, measured and removed. The millisecond hold makes a
    collision rare, NOT impossible (the review's looping writer hit it 502 times in 12,187 replaces under 40
    back-to-back backups); only a retry on the learner's side removes it.
    """
    return open(path, "rb")


# --------------------------------------------------------------------------------------------- small helpers
def now_local() -> dt.datetime:
    return dt.datetime.now()


def stamp(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%d %I:%M:%S %p")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def is_under(child: Path, parent: Path) -> bool:
    """`child` is `parent` or below it, by NAME after resolve(). Blind to alias spellings: see `inside`."""
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def under_by_identity(child: Path, parent: Path) -> bool:
    """`child` is `parent` or below it, by FILE IDENTITY: the nearest existing folder of `child`, or any of its parents,
    is the same file as `parent` (os.path.samefile). Catches spellings resolve() does not normalise (review finding 5:
    `\\\\?\\C:\\...`, `\\\\localhost\\C$\\...`); False when `parent` does not exist."""
    try:
        p = nearest_existing(child)
    except OSError:
        return False
    for q in (p, *p.parents):
        try:
            if os.path.samefile(q, parent):
                return True
        except OSError:
            continue
    return False


def inside(child: Path, parent: Path) -> bool:
    """The guard every "never write there" check uses: by name OR by identity."""
    return is_under(child, parent) or under_by_identity(child, parent)


def alias_target_reason(target: Path) -> str | None:
    """A `\\\\?\\`, `\\\\.\\` or UNC target is refused outright for --restore-check and --publish-to: both write only to
    a local folder in the main checkout or a scratch dir, and such spellings are how a name check gets bypassed."""
    s = os.fspath(target)
    if s.startswith(("\\\\", "//")):
        return f"{s} is a \\\\?\\ or UNC path: restore and publish targets must be plain local paths"
    return None


def load_config(path: Path) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("status_file", "ops_dir"):
        if key in cfg:
            cfg[key] = os.path.expandvars(cfg[key])
    return cfg


def write_status(path: Path, status: dict) -> None:
    """tmp + replace, so a reader never sees half a status file. A failure here is reported, never raised."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(status, indent=1), encoding="utf-8")
        os.replace(tmp, path)
    except OSError as e:
        print(f"WARN could not write the status file {path}: {e}")


# --------------------------------------------------------------------------------------------- capture
def read_append_file(path: Path) -> bytes:
    """Read up to the size seen at open, then trim to the last newline: only whole lines, even mid-append."""
    with _open_read(path) as fh:
        size = os.fstat(fh.fileno()).st_size
        data = fh.read(size)
    cut = data.rfind(b"\n")
    return data[:cut + 1] if cut >= 0 else b""


def read_state(path: Path) -> bytes:
    """state.json is replaced atomically by the learner, but a read can race the replace: parse, retry 3 times."""
    last = None
    for attempt in range(STATE_RETRIES):
        try:
            with _open_read(path) as fh:
                data = fh.read()
            json.loads(data.decode("utf-8"))
            return data
        except (OSError, ValueError) as e:
            last = e
            if attempt + 1 < STATE_RETRIES:
                time.sleep(STATE_RETRY_SLEEP)
    raise RuntimeError(f"state.json did not parse after {STATE_RETRIES} reads: {last}")


def ops_files(ops_dir: Path) -> list[Path]:
    """Every file of the ops folder that the backup captures. ONE walker for both the capture and the 200 MB cap, so
    the cap measures exactly what would be read. Symlinked and junctioned folders are not followed."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ops_dir, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))
                             and not os.path.isjunction(os.path.join(dirpath, d)))
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if p.is_file() and not f.endswith(EXCLUDE_SUFFIXES):
                out.append(p)
    return out


def ops_tree_bytes(ops_dir: Path) -> int:
    total = 0
    for p in ops_files(ops_dir):
        try:
            total += p.stat().st_size
        except OSError:
            continue
    return total


def source_files(clone: Path, ops_dir: Path | None) -> list[tuple[str, Path]]:
    """(member name, path) for everything the backup holds. data/ minus the lock and *.tmp; findings/; inbox/ (with
    done/ and rejected/); config.json; the ops folder when one is given."""
    out: list[tuple[str, Path]] = []
    for sub in ("data", "findings", "inbox"):
        root = clone / sub
        if root.is_dir():
            for p in sorted(root.rglob("*")):
                if p.is_file() and p.name not in EXCLUDE_NAMES and not p.name.endswith(EXCLUDE_SUFFIXES):
                    out.append(("ai-agent/" + p.relative_to(clone).as_posix(), p))
    if (clone / "config.json").is_file():
        out.append(("ai-agent/config.json", clone / "config.json"))
    if ops_dir is not None and ops_dir.is_dir():
        for p in ops_files(ops_dir):
            out.append(("pokebot-ops/" + p.relative_to(ops_dir).as_posix(), p))
    return out


def capture(clone: Path, ops_dir: Path | None, warnings: list[str]) -> dict[str, tuple[bytes, float]]:
    """Read every source into memory (about 10 MB today), consistently. A file that vanishes mid-walk (a proposal
    moved to inbox/done/) is a warning, not a failure."""
    got: dict[str, tuple[bytes, float]] = {}
    for name, path in source_files(clone, ops_dir):
        try:
            mtime = path.stat().st_mtime
            if name == STATE_MEMBER:
                data = read_state(path)
            elif path.suffix in APPEND_SUFFIXES:
                data = read_append_file(path)
            else:
                with _open_read(path) as fh:
                    data = fh.read()
        except FileNotFoundError:
            warnings.append(f"WARN {name} vanished during the copy (moved by the learner?)")
            continue
        got[name] = (data, mtime)
    if STATE_MEMBER not in got:
        raise RuntimeError("the clone has no data/state.json: is --clone the learner's ai-agent folder?")
    return got


def manifest_for(got: dict[str, tuple[bytes, float]], clone: Path, created: str) -> dict:
    members = []
    for name, (data, _m) in got.items():
        row = {"name": name, "size": len(data), "sha256": sha256(data)}
        if name.endswith(".jsonl"):
            row["lines"] = data.count(b"\n")
        members.append(row)
    return {"tool": "backup_learner.py", "created": created, "clone": str(clone), "n_files": len(members),
            "bytes_raw": sum(m["size"] for m in members), "members": members}


def write_zip(part: Path, got: dict[str, tuple[bytes, float]], manifest: dict) -> None:
    with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, (data, mtime) in got.items():
            t = time.localtime(max(mtime, 315532800))
            info = zipfile.ZipInfo(name, date_time=t[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        z.writestr(MANIFEST, json.dumps(manifest, indent=1))


# --------------------------------------------------------------------------------------------- verify
def parse_jsonl(name: str, data: bytes) -> str | None:
    """None if every non-blank line parses (the learner's own load_jsonl rule), else the first failure."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        return f"{name}: not UTF-8 ({e})"
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                json.loads(line)
            except ValueError as e:
                return f"{name}: line {i} does not parse ({e})"
    if data and not data.endswith(b"\n"):
        return f"{name}: ends in a partial line"
    return None


def verify_zip(path: Path, expect: dict | None = None) -> tuple[list[str], dict]:
    """Every check the restore needs. Returns (errors, manifest). `expect` = the manifest written (a fresh backup);
    without it (a restore drill) the zip's own manifest is the reference."""
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad is not None:
                return [f"zip member {bad} fails its CRC"], {}
            man = json.loads(z.read(MANIFEST).decode("utf-8"))
            if expect is not None and man != expect:
                errors.append("the zip's manifest differs from the one written")
            ref = expect if expect is not None else man
            want = {m["name"]: m for m in ref["members"]}
            names = set(z.namelist()) - {MANIFEST}
            if names != set(want):
                errors.append(f"member set differs: missing {sorted(set(want) - names)[:5]}, "
                              f"extra {sorted(names - set(want))[:5]}")
            for name in sorted(names & set(want)):
                data = z.read(name)
                if len(data) != want[name]["size"] or sha256(data) != want[name]["sha256"]:
                    errors.append(f"{name}: bytes differ from the source captured")
                    continue
                if name.endswith(".jsonl"):
                    err = parse_jsonl(name, data)
                    if err:
                        errors.append(err)
                if name == STATE_MEMBER:
                    try:
                        json.loads(data.decode("utf-8"))
                    except ValueError as e:
                        errors.append(f"{name}: does not parse ({e})")
            if STATE_MEMBER not in names:
                errors.append("no data/state.json in the zip")
            return errors, man
    except (zipfile.BadZipFile, zlib.error, EOFError, OSError, KeyError, ValueError) as e:
        # zlib.error is what a flipped byte inside DEFLATE data raises, from testzip() itself (found by B6/B7: it
        # escaped this handler at first, so a corrupt zip was reported as a generic failure, not as VERIFY FAILED).
        return [f"unreadable zip: {type(e).__name__}: {e}"], {}


def our_backups(dest: Path) -> list[str]:
    """The names retention may consider: plain FILES directly in `dest` matching ZIP_RE, sorted (the name IS the
    timestamp). Sub-folders are never looked into, which is how a human sets a backup aside."""
    return sorted(p.name for p in dest.iterdir() if p.is_file() and ZIP_RE.match(p.name))


def largest_previous_runs(dest: Path, exclude: str) -> tuple[int | None, str | None]:
    """The LARGEST runs.jsonl line count held by any readable earlier backup (and that backup's name), read from the
    manifests; (None, None) when no earlier backup holds runs.jsonl. The largest, not the newest: see `runs_hold`."""
    best: tuple[int | None, str | None] = (None, None)
    for name in our_backups(dest):
        if name == exclude:
            continue
        try:
            with zipfile.ZipFile(dest / name) as z:
                man = json.loads(z.read(MANIFEST).decode("utf-8"))
            lines = next((m.get("lines") for m in man["members"] if m["name"] == RUNS_MEMBER), None)
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, KeyError, ValueError, TypeError):
            continue
        if lines is not None and (best[0] is None or lines >= best[0]):
            best = (lines, name)
    return best


# --------------------------------------------------------------------------------------------- retention holds
def runs_hold(dest: Path, final_name: str, now_lines: int | None) -> list[str]:
    """Reasons NOT to prune tonight because the capture looks like a loss of runs.jsonl (review finding 0).

    Prune only when runs.jsonl WAS captured and no earlier backup holds more lines. Compared with the LARGEST earlier
    copy, not the newest: a held night's own zip would otherwise become the next night's baseline, pruning would
    resume, and the good copies would still be gone 14 nights later."""
    prev, prev_name = largest_previous_runs(dest, final_name)
    if now_lines is None:
        if prev is not None:
            return [f"runs.jsonl was NOT captured, but {prev_name} holds {prev} lines: a wiped or partial clone? "
                    "Check the clone's data/runs.jsonl; pruning resumes on the first night it is back whole"]
        return ["runs.jsonl was NOT captured and no earlier backup holds one: is --clone / ops_config clone the "
                "learner's ai-agent folder? Nothing is pruned until a backup holds runs.jsonl"]
    if prev is not None and now_lines < prev:
        return [f"runs.jsonl shrank {prev} -> {now_lines} (vs {prev_name}): a bad reparse or a truncated file? If "
                "the shrink is intended, move the older, larger zips into a sub-folder of the destination (retention "
                "never looks inside one) and pruning resumes"]
    return []


def clock_hold(dest: Path, final_name: str) -> list[str]:
    """A reason NOT to prune tonight when an existing backup is named LATER than this run's own name: the clock went
    backwards (an RTC reset, a bad time sync), so sorting by name would rank tonight's zip as the OLDEST (review
    finding 1: it deleted the zip it had just verified)."""
    future = [n for n in our_backups(dest) if n > final_name]
    if future:
        return [f"{len(future)} backup(s) are named LATER than now ({future[-1]} vs {final_name}): did the clock go "
                "backwards? Fix the clock, or move those zips into a sub-folder; pruning resumes after that"]
    return []


# --------------------------------------------------------------------------------------------- the backup
def preflight(clone: Path, dest: Path, ops_dir: Path | None, min_free: float, allow_same_volume: bool,
              warnings: list[str]) -> None:
    """Every refusal happens HERE, before a single byte is written to the destination."""
    if not (clone / "data").is_dir():
        raise Refused(f"no data/ under {clone}: is it the learner's ai-agent folder?")
    if inside(dest, clone.parent):
        raise Refused(f"destination {dest} is inside the clone {clone.parent}: never write there")
    if ops_dir is not None:
        if inside(dest, ops_dir):
            raise Refused(f"destination {dest} is under the ops folder {ops_dir}, which every backup captures: each "
                          "zip would contain every earlier one")
        if inside(clone, ops_dir):
            raise Refused(f"the clone {clone} is under the ops folder {ops_dir}: it would be captured twice")
        size = ops_tree_bytes(ops_dir) if ops_dir.is_dir() else 0
        if size > OPS_MAX_BYTES:
            raise Refused(f"the ops folder {ops_dir} holds {size / 1e6:,.0f} MB, over the {OPS_MAX_BYTES / 1e6:,.0f} "
                          "MB cap: something that is not ops data is in it")
    if volume_id(dest) == volume_id(clone):
        if not allow_same_volume:
            raise Refused(f"destination {dest} is on the SAME volume as the learner ({clone}): "
                          "a backup on the disk it protects is not a backup")
        warnings.append("WARN TEST FLAG --test-allow-same-volume: the same-volume refusal was BYPASSED; "
                        "this zip is on the learner's own disk")
    free = free_gb(dest)
    if free < min_free:
        raise Refused(f"destination {dest} has {free:.1f} GB free, under min_dest_free_gb {min_free}")
    try:
        dest.mkdir(parents=True, exist_ok=True)
        probe = dest / f".write-probe-{os.getpid()}"
        probe.write_bytes(b"x")
        probe.unlink()
    except OSError as e:
        raise Refused(f"destination {dest} is not writable: {e}")


def acquire_lock(dest: Path, warnings: list[str]) -> Path:
    """One backup at a time per destination (review finding 6: two runs in one minute deleted each other's .part).
    O_EXCL create; a lock older than LOCK_STALE_S is a killed run's and is replaced once. Raises Refused otherwise."""
    lock = dest / LOCK_NAME
    for attempt in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except FileNotFoundError:
                continue  # released between the two calls: try once more
            if attempt == 0 and age > LOCK_STALE_S:
                warnings.append(f"WARN a stale lock {lock.name} ({age / 3600:.1f} h old, a killed run?) was replaced")
                lock.unlink(missing_ok=True)
                continue
            raise Refused(f"another backup holds {lock} ({max(age, 0) / 60:.0f} min old): two runs at once could "
                          "delete each other's work")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "since": stamp(now_local())}))
        return lock
    raise Refused(f"could not take the lock {lock}")


def release_lock(lock: Path) -> None:
    try:
        lock.unlink(missing_ok=True)
    except OSError as e:
        print(f"WARN could not remove the lock {lock}: {e} (the next run treats it as stale after 2 hours)")


def sweep_stale_parts(dest: Path) -> list[str]:
    """Remove leftovers of a KILLED run: only this tool's own .part names, and only when over PART_STALE_S old, so a
    live run's .part is never touched even if the lock was removed by hand."""
    gone = []
    for p in dest.iterdir():
        if p.is_file() and PART_RE.match(p.name):
            try:
                if time.time() - p.stat().st_mtime > PART_STALE_S:
                    p.unlink()
                    gone.append(p.name)
            except FileNotFoundError:
                continue
    return gone


def replace_with_retry(src: Path, dst: Path) -> None:
    """An antivirus scanner can hold a fresh zip for a moment: retry, then let the error surface."""
    for attempt in range(REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt + 1 == REPLACE_RETRIES:
                raise
            time.sleep(REPLACE_RETRY_SLEEP)


def apply_retention(dest: Path, keep: int, protect: str | None = None, gone: list[str] | None = None) -> list[str]:
    """Keep the newest `keep` backups by name (the name IS the timestamp). Touch nothing else, and never `protect` (the
    zip this run just wrote: review finding 1). Each deletion is appended to `gone` as it happens, so a failure
    half-way is reported truthfully."""
    gone = [] if gone is None else gone
    ours = our_backups(dest)
    for name in (ours[:-keep] if keep > 0 and len(ours) > keep else []):
        if name == protect:
            continue
        (dest / name).unlink()
        gone.append(name)
    return gone


def run_backup(clone: Path, dest: Path, keep: int, min_free: float, status_file: Path,
               allow_same_volume: bool = False, when: dt.datetime | None = None,
               ops_dir: Path | None = None) -> tuple[int, dict]:
    """The nightly job. Returns (exit code, status dict) and always writes the status file. `ops_dir` None captures no
    ops folder (main() always passes the config's)."""
    when = when or now_local()
    clone, dest = Path(clone), Path(dest)
    ops_dir = Path(ops_dir) if ops_dir is not None else None
    warnings: list[str] = []
    pruned: list[str] = []
    status = {"time": stamp(when), "ok": False, "dest": str(dest), "zip": None, "bytes": 0, "warnings": warnings,
              "error": None, "pruned": pruned}
    final = dest / f"learner-data-{when:%Y%m%d-%H%M}.zip"
    part = final.with_name(final.name + ".part")
    lock = None
    try:
        preflight(clone, dest, ops_dir, min_free, allow_same_volume, warnings)
        lock = acquire_lock(dest, warnings)
        for name in sweep_stale_parts(dest):
            warnings.append(f"WARN removed {name}, a killed run's leftover")
        if final.exists():
            raise Refused(f"{final.name} already exists (two backups in one minute?)")
        got = capture(clone, ops_dir, warnings)
        manifest = manifest_for(got, clone, stamp(when))
        write_zip(part, got, manifest)
        errors, _ = verify_zip(part, manifest)
        if errors:
            part.unlink(missing_ok=True)
            status["error"] = "VERIFY FAILED (the new zip was deleted; no old backup was pruned): " + "; ".join(errors[:5])
            print("FAIL " + status["error"])
            write_status(status_file, status)
            return 1, status
        replace_with_retry(part, final)
        now_lines = next((m["lines"] for m in manifest["members"] if m["name"] == RUNS_MEMBER), None)
        # the size is taken BEFORE retention, so nothing below can turn a good backup into a crash on final.stat()
        status.update(zip=str(final), bytes=final.stat().st_size, n_files=manifest["n_files"],
                      bytes_raw=manifest["bytes_raw"], runs_lines=now_lines)
        holds = runs_hold(dest, final.name, now_lines) + clock_hold(dest, final.name)
        for w in warnings:
            print(w)
        if holds:
            status["error"] = NEEDS_YOU + " | ".join(holds)
            print(status["error"])
            write_status(status_file, status)
            return 1, status
        apply_retention(dest, keep, protect=final.name, gone=pruned)
        status["ok"] = True
        print(f"OK {final.name}: {manifest['n_files']} files, {manifest['bytes_raw']:,} bytes raw -> "
              f"{status['bytes']:,} bytes zipped; runs.jsonl {now_lines} lines; pruned {len(pruned)} old backup(s)")
        write_status(status_file, status)
        return 0, status
    except Refused as e:
        status["error"] = f"REFUSED: {e}"
        print(status["error"])
        write_status(status_file, status)
        return 2, status
    except Exception as e:  # noqa: BLE001 - the status file must say WHY, whatever it was
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        what = "no old backup was pruned" if not pruned else f"{len(pruned)} old backup(s) were pruned before it"
        status["error"] = f"FAILED ({what}): {type(e).__name__}: {e}"
        print(status["error"])
        write_status(status_file, status)
        return 1, status
    finally:
        if lock is not None:
            release_lock(lock)


# --------------------------------------------------------------------------------------------- restore drill
def restore_check(zip_path: Path, into: Path, clone: Path | None) -> int:
    """Extract into an EMPTY folder and prove the backup restores: sha256 per manifest, every .jsonl parses."""
    into = Path(into)
    reason = alias_target_reason(into)
    if reason:
        print(f"REFUSED: {reason}")
        return 2
    if clone is not None and inside(into, Path(clone).parent):
        print(f"REFUSED: {into} is inside the clone {Path(clone).parent}: a restore drill never writes there")
        return 2
    if into.exists() and any(into.iterdir()):
        print(f"REFUSED: {into} is not empty (a restore drill never mixes with existing files)")
        return 2
    errors, man = verify_zip(Path(zip_path))
    if errors:
        print("FAIL " + "; ".join(errors[:5]))
        return 1
    into.mkdir(parents=True, exist_ok=True)
    root = into.resolve()
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            target = (root / name).resolve()
            if not is_under(target, root):
                print(f"FAIL member {name!r} would escape the target folder")
                return 1
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))
    bad = []
    for m in man["members"]:
        data = (root / m["name"]).read_bytes()
        if sha256(data) != m["sha256"]:
            bad.append(f"{m['name']}: restored bytes differ")
        elif m["name"].endswith(".jsonl") and parse_jsonl(m["name"], data):
            bad.append(parse_jsonl(m["name"], data))
    state = json.loads((root / STATE_MEMBER).read_text(encoding="utf-8"))
    if bad:
        print("FAIL " + "; ".join(bad[:5]))
        return 1
    runs = next((m.get("lines") for m in man["members"] if m["name"] == RUNS_MEMBER), None)
    print(f"OK restore-check {Path(zip_path).name}: {len(man['members'])} files restored into {into}, every sha256 "
          f"matches, every .jsonl parses; runs.jsonl {runs} lines; state.json has {len(state.get('cycles', []))} cycles")
    return 0


# --------------------------------------------------------------------------------------------- weekly snapshot
def publish(clone: Path, to: Path) -> int:
    """Copy the snapshot files from the clone into `to` (the MAIN checkout). Never writes in the clone."""
    to = Path(to)
    reason = alias_target_reason(to)
    if reason:
        print(f"REFUSED: {reason}")
        return 2
    if inside(to, clone.parent):
        print(f"REFUSED: {to} is inside the clone {clone.parent}; the snapshot goes to the MAIN checkout (spec fact 2)")
        return 2
    to.mkdir(parents=True, exist_ok=True)
    total = 0
    for sub, name in PUBLISH_FILES:
        src = clone / sub / name
        if not src.is_file():
            print(f"  skip {sub}/{name} (absent)")
            continue
        if src.suffix in APPEND_SUFFIXES:
            data = read_append_file(src)
        else:
            with _open_read(src) as fh:
                data = fh.read()
        note = ""
        if len(data) > PUBLISH_MAX_BYTES and name in PUBLISH_TAIL_FILES:
            lines = data.splitlines(keepends=True)
            if len(lines) > PUBLISH_TAIL_LINES:
                data = b"".join(lines[-PUBLISH_TAIL_LINES:])
                note = f" (over 5 MB: last {PUBLISH_TAIL_LINES:,} of {len(lines):,} lines)"
        elif len(data) > PUBLISH_MAX_BYTES:
            note = " (NOTE: over 5 MB, published WHOLE: a cut data file would look like the full history)"
        (to / name).write_bytes(data)
        total += len(data)
        print(f"  {name}: {len(data):,} bytes{note}")
    print(f"published {total:,} bytes into {to}; commit it with explicit paths")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--clone", type=Path, help="the learner's ai-agent folder (default: ops_config.json)")
    ap.add_argument("--dest", type=Path, help="the backup folder (default: ops_config.json backup_dir)")
    ap.add_argument("--keep", type=int)
    ap.add_argument("--min-free-gb", type=float)
    ap.add_argument("--status-file", type=Path)
    ap.add_argument("--ops-dir", type=Path, help="the ops folder to capture too (default: ops_config.json ops_dir)")
    ap.add_argument("--test-allow-same-volume", action="store_true",
                    help="TEST ONLY: warn instead of refusing a destination on the learner's own volume")
    ap.add_argument("--restore-check", type=Path, metavar="ZIP")
    ap.add_argument("--into", type=Path)
    ap.add_argument("--publish-to", type=Path, metavar="DIR")
    a = ap.parse_args(argv)
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        # a path or file name the console code page cannot encode must not turn a report line into a crash
        sys.stdout.reconfigure(errors="backslashreplace")
    cfg = load_config(a.config)
    clone = a.clone or Path(cfg["clone"])
    if a.restore_check:
        if not a.into:
            ap.error("--restore-check needs --into DIR")
        return restore_check(a.restore_check, a.into, clone)
    if a.publish_to:
        return publish(clone, a.publish_to)
    if a.ops_dir is None and "ops_dir" not in cfg:
        print(f"REFUSED: {a.config} has no ops_dir (the ops folder is an explicit key; see its _ops_dir)")
        return 2
    code, _ = run_backup(clone, a.dest or Path(cfg["backup_dir"]), a.keep if a.keep is not None else int(cfg["keep"]),
                         a.min_free_gb if a.min_free_gb is not None else float(cfg["min_dest_free_gb"]),
                         a.status_file or Path(cfg["status_file"]), allow_same_volume=a.test_allow_same_volume,
                         ops_dir=a.ops_dir or Path(cfg["ops_dir"]))
    return code


if __name__ == "__main__":
    sys.exit(main())
