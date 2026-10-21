"""Back up the 24/7 learner's small, irreplaceable data OFF the C: drive (backlog O4, build spec S1-2).

WHY THIS EXISTS. The bot tuner (`ai-agent/` in the deployment clone `C:/Remote Projects/pokebot-learner`) keeps its
whole memory in a few files: `data/runs.jsonl` (every scored run), `cycles.jsonl`, `state.json`, the consult log, the
findings and the inbox of proposals. They live only on C:, which is also the disk the learner fills with raw logs.
One failed disk, one bad `reparse`, or one wiped clone loses weeks of runs that cannot be re-played. This tool makes a
nightly zip of those files on a DIFFERENT physical disk (default `E:/pokebot-backups/learner`, a user choice; Z: is
the alternative) and keeps the newest 14.

DESIGN, AND THE REASON FOR EACH PART
- Stdlib only, and it imports NOTHING from the learner: a learner change must never be able to break its own backup,
  and the scheduled task runs this file with `py -3.12 -B` so no `__pycache__` is written into the clone.
- READ-ONLY on the clone. It never writes under the clone (it refuses a destination or a restore target there), so it
  can never create a tracked change that would silently stop the clone's auto-update (spec fact 2).
- REFUSE, never guess: a destination on the same volume as the source (a "backup" on the disk it protects is not a
  backup), under `min_dest_free_gb` free, or not writable -> nothing is written, the status file says why, exit 2.
- A CONSISTENT copy of files the learner is appending to right now: each `.jsonl`/`.log` is read in binary up to the
  size seen when it was opened and trimmed to the last newline. The learner appends without fsync, so the tail can be
  half a line; a backup must hold only whole lines. `state.json` is read and parsed, with retries (it is replaced
  atomically, but a read can still race the replace).
- Each source is opened, read in ONE call and closed at once. While any handle is open on Windows, the learner's own
  `tmp.replace(state.json)` fails with PermissionError, which would stop its loop; sharing delete does not help
  (measured, see `_open_read`). A backup must never be able to hurt the thing it protects, so the hold stays at
  milliseconds and the task runs at 1 AM, inside a batch, when the learner writes no state.
- Write `.part`, VERIFY (zip tests clean, every member's sha256 equals what was captured, every `.jsonl` line parses,
  `state.json` parses), rename, and only THEN apply retention. A failed backup deletes its own `.part` and NEVER prunes
  an old backup: the old ones are then the only good copies.
- Retention touches only files matching `^learner-data-\\d{8}-\\d{4}\\.zip$` (plus this tool's own leftover `.part`
  files of the same stem). Anything else in the folder is never deleted.
- `backup_status.json` (time, zip, bytes, ok, warnings, error) goes to `%LOCALAPPDATA%/pokebot-ops/`, never into the
  clone; the watchdog (S1-4) and tools/status.py read it.

OTHER MODES
- `--restore-check ZIP --into DIR`: the restore drill. Extracts into an EMPTY dir (refuses a non-empty one and any dir
  under the clone), re-checks every sha256 against the manifest, parses every `.jsonl` and `state.json`.
- `--publish-to DIR`: the weekly repo snapshot. Copies LATEST.md, latest.json, DEVELOPER-NOTES.md, runs.jsonl,
  cycles.jsonl and learner.log from the clone into DIR (the MAIN checkout's `ai-agent/published`, committed later by an
  interactive session with explicit paths). learner.log over 5 MB is published as its last 5,000 lines; a data file
  is never cut (it is published whole, with a NOTE when it is over 5 MB). The 24/7 process
  never commits, and nothing is written in the clone (running the learner's own `publish` from the clone would write a
  tracked path there once a snapshot is committed, spec fact 2).

TEST-ONLY SWITCH: `--test-allow-same-volume` turns the same-volume refusal into a loud WARNING recorded in the report
and the status file. It exists so the tool can be exercised against the REAL clone with a scratch destination on C:
(the selftest's temp folders are on C: too). The installed task never passes it (selftest B9 checks the installer).

Exit codes: 0 ok, 1 the backup or check FAILED, 2 REFUSED before writing anything.
Run: py -3.12 -B tools/ops/backup_learner.py [--config F] [--clone D] [--dest D] [--status-file F]
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
ZIP_RE = re.compile(r"^learner-data-\d{8}-\d{4}\.zip$")
PART_RE = re.compile(r"^learner-data-\d{8}-\d{4}\.zip\.part$")
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
    Windows the learner's `tmp.replace(state.json)` fails with PermissionError (WinError 5), and that call sits
    outside the learner's try (learner.py loop, about :510-514) so it would stop the learner. MEASURED 2026-10-21 on
    this PC: opening with FILE_SHARE_DELETE (ctypes CreateFileW) does NOT avoid it, MoveFileEx onto an open target
    is refused either way, so the share-delete open was built, measured and removed. What keeps the risk small is
    the timing: the hold is milliseconds, and at 1 AM the learner is inside a batch, where it writes no state.
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
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def load_config(path: Path) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg["status_file"] = os.path.expandvars(cfg["status_file"])
    return cfg


def write_status(path: Path, status: dict) -> None:
    """tmp + replace, so the watchdog never reads half a status file. A failure here is reported, never raised."""
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


def source_files(clone: Path, ops_dir: Path) -> list[tuple[str, Path]]:
    """(member name, path) for everything the backup holds. data/ minus the lock and *.tmp; findings/; inbox/ (with
    done/ and rejected/); config.json; the ops folder (watchdog samples and state, the backup status)."""
    out: list[tuple[str, Path]] = []
    for sub in ("data", "findings", "inbox"):
        root = clone / sub
        if root.is_dir():
            for p in sorted(root.rglob("*")):
                if p.is_file() and p.name not in EXCLUDE_NAMES and not p.name.endswith(EXCLUDE_SUFFIXES):
                    out.append(("ai-agent/" + p.relative_to(clone).as_posix(), p))
    if (clone / "config.json").is_file():
        out.append(("ai-agent/config.json", clone / "config.json"))
    if ops_dir.is_dir():
        for p in sorted(ops_dir.rglob("*")):
            if p.is_file() and not p.name.endswith(EXCLUDE_SUFFIXES):
                out.append(("pokebot-ops/" + p.relative_to(ops_dir).as_posix(), p))
    return out


def capture(clone: Path, ops_dir: Path, warnings: list[str]) -> dict[str, tuple[bytes, float]]:
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


def previous_runs_lines(dest: Path, exclude: str) -> tuple[int | None, str | None]:
    """runs.jsonl's line count in the newest earlier backup, read from its manifest (None if there is none)."""
    for p in sorted((p for p in dest.iterdir() if ZIP_RE.match(p.name) and p.name != exclude), reverse=True):
        try:
            with zipfile.ZipFile(p) as z:
                man = json.loads(z.read(MANIFEST).decode("utf-8"))
            for m in man["members"]:
                if m["name"] == RUNS_MEMBER:
                    return m.get("lines"), p.name
            return None, p.name
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, KeyError, ValueError):
            continue
    return None, None


# --------------------------------------------------------------------------------------------- the backup
def preflight(clone: Path, dest: Path, min_free: float, allow_same_volume: bool, warnings: list[str]) -> None:
    """Every refusal happens HERE, before a single byte is written to the destination."""
    if not (clone / "data").is_dir():
        raise Refused(f"no data/ under {clone}: is it the learner's ai-agent folder?")
    if is_under(dest, clone.parent):
        raise Refused(f"destination {dest} is inside the clone {clone.parent}: never write there")
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


def apply_retention(dest: Path, keep: int) -> list[str]:
    """Keep the newest `keep` backups by name (the name IS the timestamp). Touch nothing else."""
    ours = sorted(p.name for p in dest.iterdir() if p.is_file() and ZIP_RE.match(p.name))
    gone = ours[:-keep] if keep > 0 and len(ours) > keep else []
    for name in gone:
        (dest / name).unlink()
    return gone


def run_backup(clone: Path, dest: Path, keep: int, min_free: float, status_file: Path,
               allow_same_volume: bool = False, when: dt.datetime | None = None) -> tuple[int, dict]:
    """The nightly job. Returns (exit code, status dict) and always writes the status file."""
    when = when or now_local()
    clone, dest = Path(clone), Path(dest)
    warnings: list[str] = []
    status = {"time": stamp(when), "ok": False, "dest": str(dest), "zip": None, "bytes": 0, "warnings": warnings,
              "error": None}
    final = dest / f"learner-data-{when:%Y%m%d-%H%M}.zip"
    part = final.with_name(final.name + ".part")
    try:
        preflight(clone, dest, min_free, allow_same_volume, warnings)
        for p in dest.iterdir():  # leftovers of a killed run: only our own exact .part names
            if p.is_file() and PART_RE.match(p.name):
                p.unlink()
        if final.exists():
            raise Refused(f"{final.name} already exists (two backups in one minute?)")
        got = capture(clone, status_file.parent, warnings)
        manifest = manifest_for(got, clone, stamp(when))
        write_zip(part, got, manifest)
        errors, _ = verify_zip(part, manifest)
        if errors:
            part.unlink(missing_ok=True)
            status["error"] = "VERIFY FAILED (the new zip was deleted; no old backup was pruned): " + "; ".join(errors[:5])
            print("FAIL " + status["error"])
            write_status(status_file, status)
            return 1, status
        prev, prev_name = previous_runs_lines(dest, final.name)
        now_lines = next((m["lines"] for m in manifest["members"] if m["name"] == RUNS_MEMBER), None)
        if prev is not None and now_lines is not None and now_lines < prev:
            warnings.append(f"WARN runs.jsonl shrank {prev} -> {now_lines} (vs {prev_name}; a reparse may rewrite it)")
        replace_with_retry(part, final)
        pruned = apply_retention(dest, keep)
        status.update(ok=True, zip=str(final), bytes=final.stat().st_size, n_files=manifest["n_files"],
                      bytes_raw=manifest["bytes_raw"], runs_lines=now_lines, pruned=pruned)
        for w in warnings:
            print(w)
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
        status["error"] = f"FAILED (no old backup was pruned): {type(e).__name__}: {e}"
        print(status["error"])
        write_status(status_file, status)
        return 1, status


# --------------------------------------------------------------------------------------------- restore drill
def restore_check(zip_path: Path, into: Path, clone: Path | None) -> int:
    """Extract into an EMPTY folder and prove the backup restores: sha256 per manifest, every .jsonl parses."""
    into = Path(into)
    if clone is not None and is_under(into, Path(clone).parent):
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
    if is_under(to, clone.parent):
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
    ap.add_argument("--test-allow-same-volume", action="store_true",
                    help="TEST ONLY: warn instead of refusing a destination on the learner's own volume")
    ap.add_argument("--restore-check", type=Path, metavar="ZIP")
    ap.add_argument("--into", type=Path)
    ap.add_argument("--publish-to", type=Path, metavar="DIR")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    clone = a.clone or Path(cfg["clone"])
    if a.restore_check:
        if not a.into:
            ap.error("--restore-check needs --into DIR")
        return restore_check(a.restore_check, a.into, clone)
    if a.publish_to:
        return publish(clone, a.publish_to)
    code, _ = run_backup(clone, a.dest or Path(cfg["backup_dir"]), a.keep if a.keep is not None else int(cfg["keep"]),
                         a.min_free_gb if a.min_free_gb is not None else float(cfg["min_dest_free_gb"]),
                         a.status_file or Path(cfg["status_file"]), allow_same_volume=a.test_allow_same_volume)
    return code


if __name__ == "__main__":
    sys.exit(main())
