"""
Sandbox addition (A1): profile Backup & Restore.

Protects the data that actually matters — save files, savestates, stats.db
and per-profile configs — as timestamped zip archives:

  local:  sandbox-pokebot/backups/<profile>/<timestamp>_<reason>.zip
  cloud:  (opt-in via backup.yml)
          github        -> repo-root cloud-backups/<profile>/ committed and
                           pushed to the private repo (your repo IS the cloud)
          synced_folder -> any OneDrive/Dropbox/Google-Drive directory

Restores always go into a NEW profile name — a loaded profile is live in
the emulator and must never be overwritten underneath it.

Everything here is self-contained (yaml + stdlib only), fails soft (a
broken cloud push never breaks the local backup; one unreadable file never
breaks the archive) and logs hybridly: console prints for the user, a full
trace to logs/backup.log.
"""

import logging
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml

BOT_ROOT: Path = Path(__file__).resolve().parent.parent  # sandbox-pokebot/
REPO_ROOT: Path = BOT_ROOT.parent
LOCAL_BACKUP_ROOT: Path = BOT_ROOT / "backups"
CLOUD_BACKUP_ROOT: Path = REPO_ROOT / "cloud-backups"
CONFIG_FILE_NAME: str = "backup.yml"

# Directories inside a profile that are bulky and reproducible — not backed up.
EXCLUDED_DIR_NAMES = {"screenshots", "stream"}
EXCLUDED_SUFFIXES = {".log"}

DEFAULT_CONFIG: dict = {
    "enabled": True,
    "retention": 10,           # local zips kept per profile
    "auto_on_shiny": True,     # backup automatically whenever a shiny is logged
    "interval_hours": 2.0,     # timed auto-backup while the bot runs (0 = off)
    "cloud": {
        "github": False,           # commit+push newest backups to this repo
        "github_retention": 3,     # cloud copies kept in the repo per profile
        "synced_folder": None,     # e.g. C:/Users/you/OneDrive/PokebotBackups
        "synced_retention": 10,
    },
}

_logger = logging.getLogger("backup")
if not _logger.handlers:
    log_dir = BOT_ROOT / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_dir / "backup.log", maxBytes=512_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    except OSError:
        pass  # logging must never break the bot


def _console_log(message: str, level: str = "info") -> None:
    print(f"[backup] {message}")
    getattr(_logger, level, _logger.info)(message)


def load_config(profile_path: "Path | None" = None) -> dict:
    """Global backup.yml, whole-file-overridden by profiles/<name>/backup.yml
    (matching upstream's config layering convention). Malformed or missing
    files fall back to safe defaults, key by key."""

    def _read(path: Path) -> "dict | None":
        try:
            if path.is_file():
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
                _logger.warning("config %s is not a mapping; ignored", path)
        except Exception as error:
            _logger.warning("config %s unreadable (%s); using defaults", path, error)
        return None

    raw = None
    if profile_path is not None:
        raw = _read(Path(profile_path) / CONFIG_FILE_NAME)
    if raw is None:
        raw = _read(BOT_ROOT / CONFIG_FILE_NAME)
    if raw is None:
        raw = {}

    config = {**DEFAULT_CONFIG, **raw}
    config["cloud"] = {**DEFAULT_CONFIG["cloud"], **(raw.get("cloud") or {})}
    return config


def _profile_files(profile_path: Path):
    for path in sorted(profile_path.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(profile_path)
        if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        yield path, relative


def create_backup(profile_path: "Path | str", reason: str = "manual") -> "Path | None":
    """Zip the profile's valuable data. Returns the zip path, or None if
    disabled/failed. Individual unreadable files are skipped, never fatal."""
    profile_path = Path(profile_path)
    config = load_config(profile_path)
    if not config.get("enabled", True):
        _logger.info("backups disabled; skipping (%s)", reason)
        return None
    if not profile_path.is_dir():
        _console_log(f"profile folder not found: {profile_path}", "error")
        return None

    profile_name = profile_path.name
    target_dir = LOCAL_BACKUP_ROOT / profile_name
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_path = target_dir / f"{timestamp}_{re.sub(r'[^A-Za-z0-9_-]', '', reason) or 'manual'}.zip"

    archived = 0
    skipped = 0
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, relative in _profile_files(profile_path):
                try:
                    archive.write(path, arcname=str(relative))
                    archived += 1
                except OSError as error:
                    skipped += 1
                    _logger.warning("skipped %s (%s)", relative, error)
    except Exception as error:
        _console_log(f"backup FAILED: {error}", "error")
        zip_path.unlink(missing_ok=True)
        return None

    if archived == 0:
        _console_log(f"nothing to back up in {profile_name}; removed empty archive", "warning")
        zip_path.unlink(missing_ok=True)
        return None

    size_kb = zip_path.stat().st_size // 1024
    _console_log(
        f"backed up '{profile_name}' ({archived} files, {size_kb} KB, reason: {reason})"
        + (f", {skipped} unreadable file(s) skipped" if skipped else "")
    )
    _prune(target_dir, int(config.get("retention", 10)))

    cloud = config.get("cloud", {})
    try:
        if cloud.get("github"):
            _cloud_github(zip_path, profile_name, int(cloud.get("github_retention", 3)))
    except Exception as error:  # never let cloud problems undo a good local backup
        _console_log(f"GitHub cloud backup failed (local backup is safe): {error}", "warning")
    try:
        folder = cloud.get("synced_folder")
        if folder:
            _cloud_synced_folder(zip_path, profile_name, Path(folder), int(cloud.get("synced_retention", 10)))
    except Exception as error:
        _console_log(f"synced-folder backup failed (local backup is safe): {error}", "warning")

    return zip_path


def _prune(directory: Path, keep: int) -> None:
    zips = sorted(directory.glob("*.zip"), key=lambda p: p.name, reverse=True)
    for old in zips[max(keep, 1):]:
        try:
            old.unlink()
            _logger.info("pruned %s", old.name)
        except OSError as error:
            _logger.warning("could not prune %s (%s)", old.name, error)


def _cloud_github(zip_path: Path, profile_name: str, keep: int) -> None:
    """Your private repo IS the cloud: copy the zip into cloud-backups/,
    prune, then stage ONLY that folder, commit and push. All failures are
    logged and non-fatal (offline machines still get local backups)."""
    cloud_dir = CLOUD_BACKUP_ROOT / profile_name
    cloud_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, cloud_dir / zip_path.name)
    _prune(cloud_dir, keep)

    def _git(*args: str) -> subprocess.CompletedProcess:
        result = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True)
        _logger.info("git %s -> %s %s", " ".join(args), result.returncode, (result.stderr or "").strip()[:400])
        return result

    # Stage only the cloud-backups tree (additions AND prunes), nothing else.
    if _git("add", "-A", "--", "cloud-backups").returncode != 0:
        _console_log("git add failed for cloud backup", "warning")
        return
    commit = _git("commit", "-m", f"backup: {profile_name} {zip_path.stem}")
    if commit.returncode != 0:
        if "nothing to commit" in (commit.stdout + commit.stderr):
            _logger.info("cloud backup produced no changes to commit")
        else:
            _console_log("git commit failed for cloud backup", "warning")
        return
    if _git("push").returncode == 0:
        _console_log(f"cloud backup pushed to repo (cloud-backups/{profile_name}/{zip_path.name})")
    else:
        _console_log("git push failed — backup is committed locally and will push next time", "warning")


def _cloud_synced_folder(zip_path: Path, profile_name: str, folder: Path, keep: int) -> None:
    destination = folder / profile_name
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, destination / zip_path.name)
    _prune(destination, keep)
    _console_log(f"backup mirrored to synced folder ({destination})")


def list_backups(profile_name: str) -> list:
    """Local + repo-cloud backups for a profile, newest first.
    Returns dicts: {path, source, label}."""
    entries = []
    for source, root in (("local", LOCAL_BACKUP_ROOT), ("cloud", CLOUD_BACKUP_ROOT)):
        directory = root / profile_name
        if directory.is_dir():
            for zip_file in directory.glob("*.zip"):
                entries.append(
                    {
                        "path": zip_file,
                        "source": source,
                        "label": f"[{source}] {zip_file.stem}  ({zip_file.stat().st_size // 1024} KB)",
                    }
                )
    entries.sort(key=lambda entry: entry["path"].name, reverse=True)
    return entries


def seconds_since_last_backup(profile_name: str) -> "float | None":
    newest = None
    directory = LOCAL_BACKUP_ROOT / profile_name
    if directory.is_dir():
        for zip_file in directory.glob("*.zip"):
            modified = zip_file.stat().st_mtime
            if newest is None or modified > newest:
                newest = modified
    return None if newest is None else max(0.0, time.time() - newest)


def restore_backup(zip_path: "Path | str", new_profile_name: str) -> Path:
    """Extract a backup into a NEW profile folder. Refuses to touch any
    existing profile (the loaded one is live in the emulator). Guards
    against zip-slip. Returns the new profile path; raises ValueError with
    a user-readable message on any refusal."""
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise ValueError(f"Backup file not found: {zip_path}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,38}", new_profile_name or ""):
        raise ValueError("Profile names may only contain letters, digits, spaces, '-' and '_' (max 39 chars).")

    target = BOT_ROOT / "profiles" / new_profile_name
    if target.exists():
        raise ValueError(f"Profile '{new_profile_name}' already exists — restores only go into a NEW profile.")

    target.mkdir(parents=True)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                destination = (target / member).resolve()
                if not str(destination).startswith(str(target.resolve())):
                    raise ValueError(f"Backup contains an unsafe path: {member}")
            archive.extractall(target)
    except Exception:
        shutil.rmtree(target, ignore_errors=True)  # never leave a half-restored profile
        raise

    _console_log(f"restored {zip_path.name} into new profile '{new_profile_name}'")
    return target
