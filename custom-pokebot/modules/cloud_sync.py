"""
Sandbox addition (A8): cloud save-sync v2 — desktop ↔ Ally continuity.

Builds on the A1 backup system: the private GitHub repo is the transport
(`cloud-backups/<profile>/`), carrying a small sync manifest (machine,
timestamp, save hash, zip name) next to the newest sync zip.

Safety model (non-negotiable):
- The LAUNCH sync runs in pokebot.py BEFORE any GUI/profile/emulator
  exists, so applying a newer cloud save can never race the emulator. This
  is why it is synchronous (and gated: with `sync.enabled: false` — the
  default — it does nothing and touches no network).
- The EXIT sync runs in the dashboard's close path AFTER
  `emulator.shutdown()` has flushed the save (the stock close path ends in
  os._exit(), so atexit is NOT available — the GUI hook is the only
  correct point).
- Conflicts (both machines progressed) are NEVER auto-resolved: local wins,
  the GUI shows a notice, and the cloud version can be imported as a NEW
  profile with one click.

All git operations are time-boxed, pathspec-scoped to cloud-backups/, and
fail soft (offline = log + carry on).
"""

import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from modules import backup_manager
from modules.backup_manager import _console_log, _logger, load_config

MANIFEST_NAME = "sync_manifest.json"
LAST_SYNC_NAME = ".last_sync.json"

# Launch-sync results per profile name, read by the GUI:
#   {"state": "disabled|no-cloud|up-to-date|applied|conflict|offline|error",
#    "detail": str, "cloud": manifest-dict|None}
_launch_status: dict = {}


# ---------------------------------------------------------------- helpers
def _git(*args: str, timeout: int = 60, binary: bool = False):
    """Run git in the repo root; None on any execution failure (logged)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(backup_manager.REPO_ROOT), *args],
            capture_output=True,
            text=not binary,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _logger.warning("sync: git %s failed to run (%s)", " ".join(args), error)
        return None
    if not binary:
        _logger.info("sync: git %s -> %s %s", " ".join(args), result.returncode, (result.stderr or "").strip()[:300])
    return result


def _current_branch() -> str:
    result = _git("rev-parse", "--abbrev-ref", "HEAD", timeout=15)
    if result is not None and result.returncode == 0 and result.stdout.strip() not in ("", "HEAD"):
        return result.stdout.strip()
    return "main"


def _show_text(ref: str) -> "str | None":
    result = _git("show", ref, timeout=20)
    if result is not None and result.returncode == 0:
        return result.stdout
    return None


def _show_bytes(ref: str) -> "bytes | None":
    result = _git("show", ref, timeout=60, binary=True)
    if result is not None and result.returncode == 0:
        return result.stdout
    return None


def _save_hash(profile_path: Path) -> "str | None":
    save_file = Path(profile_path) / "current_save.sav"
    try:
        if save_file.is_file():
            return hashlib.sha1(save_file.read_bytes()).hexdigest()
    except OSError as error:
        _logger.warning("sync: could not hash %s (%s)", save_file, error)
    return None


def _read_last_sync(profile_path: Path) -> "dict | None":
    try:
        marker = Path(profile_path) / LAST_SYNC_NAME
        if marker.is_file():
            data = json.loads(marker.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, ValueError) as error:
        _logger.warning("sync: unreadable %s (%s)", LAST_SYNC_NAME, error)
    return None


def _write_last_sync(profile_path: Path, save_sha1: "str | None", manifest_timestamp: str) -> None:
    try:
        (Path(profile_path) / LAST_SYNC_NAME).write_text(
            json.dumps({"save_sha1": save_sha1, "manifest_timestamp": manifest_timestamp}), encoding="utf-8"
        )
    except OSError as error:
        _logger.warning("sync: could not write %s (%s)", LAST_SYNC_NAME, error)


def _machine_name(config: dict) -> str:
    name = (config.get("sync") or {}).get("machine_name")
    if name:
        return str(name)
    import platform

    return platform.node() or "unknown-machine"


def _read_cloud_manifest(profile_name: str, branch: str, use_origin: bool) -> "dict | None":
    """Newest manifest visible: origin ref first (fetched), then working tree."""
    if use_origin:
        text = _show_text(f"origin/{branch}:cloud-backups/{profile_name}/{MANIFEST_NAME}")
        if text is not None:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    data["_from"] = "origin"
                    return data
            except ValueError:
                _logger.warning("sync: origin manifest for %s is not valid JSON", profile_name)
    try:
        local_manifest = backup_manager.CLOUD_BACKUP_ROOT / profile_name / MANIFEST_NAME
        if local_manifest.is_file():
            data = json.loads(local_manifest.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_from"] = "worktree"
                return data
    except (OSError, ValueError):
        pass
    return None


def _materialize_cloud_zip(profile_name: str, manifest: dict, branch: str) -> "Path | None":
    """Get the manifest's zip as a real file (temp dir), from origin's object
    database if needed — the working tree may never have been pulled."""
    zip_name = manifest.get("zip")
    if not zip_name or "/" in str(zip_name) or "\\" in str(zip_name):
        return None
    worktree_zip = backup_manager.CLOUD_BACKUP_ROOT / profile_name / zip_name
    if manifest.get("_from") == "worktree" and worktree_zip.is_file():
        return worktree_zip
    blob = _show_bytes(f"origin/{branch}:cloud-backups/{profile_name}/{zip_name}")
    if blob is None and worktree_zip.is_file():
        return worktree_zip
    if blob is None:
        return None
    temp_dir = Path(tempfile.mkdtemp(prefix="pokebot-sync-"))
    temp_zip = temp_dir / zip_name
    try:
        temp_zip.write_bytes(blob)
    except OSError as error:
        _logger.warning("sync: could not materialize cloud zip (%s)", error)
        return None
    return temp_zip


def _apply_zip_over_profile(zip_path: Path, profile_path: Path) -> None:
    """Extract a sync zip OVER an existing profile. Only ever called from the
    launch path, before any emulator exists. Zip-slip guarded."""
    profile_path = Path(profile_path)
    resolved_target = profile_path.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            destination = (profile_path / member).resolve()
            if destination != resolved_target and resolved_target not in destination.parents:
                raise ValueError(f"Sync archive contains an unsafe path: {member}")
        archive.extractall(profile_path)


# ---------------------------------------------------------------- launch
def run_launch_sync() -> None:
    """Called from pokebot.py BEFORE the GUI/profile/emulator exist.
    Applies newer cloud saves to unchanged local profiles; flags conflicts.
    Does nothing (and touches no network) unless a profile opts in."""
    global _launch_status
    _launch_status = {}

    profiles_dir = backup_manager.BOT_ROOT / "profiles"
    if not profiles_dir.is_dir():
        return
    candidates = []
    for entry in sorted(profiles_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        config = load_config(entry)
        sync = config.get("sync") or {}
        if sync.get("enabled") and sync.get("sync_on_launch", True):
            candidates.append((entry, config))
        else:
            _launch_status[entry.name] = {"state": "disabled", "detail": "", "cloud": None}
    if not candidates:
        return

    _console_log(f"cloud sync: checking {len(candidates)} profile(s)…")
    fetch = _git("fetch", "origin", timeout=25)
    use_origin = fetch is not None and fetch.returncode == 0
    if not use_origin:
        _console_log("cloud sync: could not reach the remote — using local state only", "warning")
    branch = _current_branch()

    for profile_path, config in candidates:
        name = profile_path.name
        try:
            _launch_status[name] = _launch_sync_one(profile_path, name, branch, use_origin)
        except Exception as error:  # one broken profile must not block the launch
            _logger.exception("sync: launch sync failed for %s", name)
            _launch_status[name] = {"state": "error", "detail": str(error), "cloud": None}
        state = _launch_status[name]
        if state["state"] == "applied":
            _console_log(f"cloud sync: '{name}' updated from the cloud ({state['detail']})")
        elif state["state"] == "conflict":
            _console_log(f"cloud sync: '{name}' CONFLICT — local kept; import available in the GUI", "warning")


def _launch_sync_one(profile_path: Path, name: str, branch: str, use_origin: bool) -> dict:
    manifest = _read_cloud_manifest(name, branch, use_origin)
    if manifest is None:
        return {"state": "no-cloud" if use_origin else "offline", "detail": "", "cloud": None}

    cloud_hash = manifest.get("save_sha1")
    cloud_ts = str(manifest.get("timestamp") or "")
    cloud_machine = str(manifest.get("machine") or "?")
    local_hash = _save_hash(profile_path)
    last = _read_last_sync(profile_path)

    if cloud_hash == local_hash:
        _write_last_sync(profile_path, local_hash, cloud_ts)
        return {"state": "up-to-date", "detail": "", "cloud": manifest}

    local_unchanged = last is not None and last.get("save_sha1") == local_hash
    fresh_local = local_hash is None
    if not (local_unchanged or fresh_local):
        # Local progressed AND cloud differs -> both sides moved (or we have
        # no baseline to prove otherwise). Never clobber.
        return {"state": "conflict", "detail": f"cloud from {cloud_machine} @ {cloud_ts}", "cloud": manifest}
    if local_unchanged and str(last.get("manifest_timestamp") or "") >= cloud_ts:
        # Rollback guard: the cloud manifest is not newer than the baseline we
        # already synced to — applying it would move the save BACKWARDS.
        return {"state": "conflict", "detail": f"cloud is older ({cloud_machine} @ {cloud_ts})", "cloud": manifest}

    zip_path = _materialize_cloud_zip(name, manifest, branch)
    if zip_path is None:
        return {"state": "error", "detail": "cloud zip unavailable", "cloud": manifest}

    # Safety net: snapshot the local profile before overwriting it.
    backup_manager.create_backup(profile_path, reason="presync")
    _apply_zip_over_profile(zip_path, profile_path)
    _write_last_sync(profile_path, cloud_hash, cloud_ts)
    return {"state": "applied", "detail": f"from {cloud_machine} @ {cloud_ts}", "cloud": manifest}


def get_status(profile_name: str) -> "dict | None":
    return _launch_status.get(profile_name)


# ---------------------------------------------------------------- exit
def sync_on_exit(profile) -> "str | None":
    """Called from the dashboard close path AFTER emulator.shutdown() flushed
    the save (atexit never runs — the close path ends in os._exit).
    Returns a short human status, or None when sync is off."""
    if profile is None:
        return None
    profile_path = Path(profile.path)
    config = load_config(profile_path)
    sync = config.get("sync") or {}
    if not sync.get("enabled") or not sync.get("sync_on_exit", True):
        return None

    name = profile_path.name
    local_hash = _save_hash(profile_path)
    if local_hash is None:
        return "sync skipped (no save yet)"
    last = _read_last_sync(profile_path)
    if last is not None and last.get("save_sha1") == local_hash:
        return "sync: already up to date"

    zip_path = backup_manager.create_backup(profile_path, reason="sync")
    if zip_path is None:
        return "sync FAILED (backup could not be created)"

    # Integrate the remote FIRST: another machine's sync commit contains
    # cloud-backups files at the very paths we are about to write — writing
    # ours first would make the fast-forward pull refuse ("untracked files
    # would be overwritten"). Pull failures (offline) are tolerated.
    _git("pull", "--ff-only", timeout=60)

    cloud_dir = backup_manager.CLOUD_BACKUP_ROOT / name
    cloud_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, cloud_dir / zip_path.name)
    backup_manager._prune(cloud_dir, backup_manager._to_int((config.get("cloud") or {}).get("github_retention"), 3))

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "machine": _machine_name(config),
        "timestamp": timestamp,
        "save_sha1": local_hash,
        "zip": zip_path.name,
        "format": 1,
    }
    try:
        (cloud_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except OSError as error:
        return f"sync FAILED (could not write manifest: {error})"

    add = _git("add", "-A", "--", "cloud-backups")
    if add is None or add.returncode != 0:
        return "sync FAILED (git add)"
    status = _git("status", "--porcelain", "--", "cloud-backups")
    if status is not None and status.returncode == 0 and status.stdout.strip():
        commit = _git("commit", "-m", f"sync: {name} from {manifest['machine']} {timestamp}", "--", "cloud-backups")
        if commit is None or commit.returncode != 0:
            return "sync FAILED (git commit)"
    push = _git("push", timeout=300)
    if push is not None and push.returncode == 0:
        # The baseline is recorded ONLY after a successful push. Recording it
        # on a failed push would make this machine believe the cloud has its
        # save — and a later launch would "helpfully" roll it back to the
        # older cloud version (proven by the test battery).
        _write_last_sync(profile_path, local_hash, timestamp)
        _console_log(f"cloud sync: pushed '{name}' ({zip_path.name})")
        return "sync: pushed to cloud"
    _console_log("cloud sync: push failed — committed locally, will reach the cloud next time", "warning")
    return "sync: committed locally (push failed — will retry next time)"


# ---------------------------------------------------------------- conflict escape hatch
def import_cloud_as_new_profile(profile_name: str, new_profile_name: str) -> Path:
    """Materialize the conflicting cloud version and restore it as a NEW
    profile (never touching the local one). Raises ValueError with a
    readable message on failure."""
    status = _launch_status.get(profile_name)
    manifest = (status or {}).get("cloud")
    if not manifest:
        raise ValueError("No cloud version is known for this profile (no conflict recorded this launch).")
    zip_path = _materialize_cloud_zip(profile_name, manifest, _current_branch())
    if zip_path is None:
        raise ValueError("The cloud archive could not be retrieved (offline?).")
    return backup_manager.restore_backup(zip_path, new_profile_name)
