"""
Sandbox addition (#18): launch-time "updates available" check.

Asks git whether the repository this bot lives in is behind its remote.
Designed for the dashboard GUI: the check runs in a daemon thread (network
must never block launch), the result is a plain int written to a module
global, and the GUI polls it from its existing refresh cycle (Tk calls stay
on the main thread).

Every failure path (no git, not a git checkout, offline, timeout) returns
None and is logged only — the feature is silent unless there IS an update.
"""

import logging
import subprocess
import threading
from pathlib import Path

_logger = logging.getLogger("update_check")

# Result of the async check: None = unknown/none, int > 0 = commits behind.
_commits_behind: "int | None" = None
_check_started = False


def _run_git(args: list, cwd: Path, timeout: float) -> "subprocess.CompletedProcess | None":
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _logger.info("git %s failed: %s", args[0] if args else "?", error)
        return None


def find_repo_root(start: Path) -> "Path | None":
    """Walk up from `start` looking for a .git directory."""
    current = Path(start).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").is_dir():
            return candidate
    return None


def count_commits_behind(repo_root: Path, timeout: float = 30.0) -> "int | None":
    """Fetch the remote and report how many commits HEAD is behind its
    upstream branch. None on any failure (offline, detached, no upstream)."""
    if _run_git(["fetch", "origin"], repo_root, timeout) is None:
        return None
    branch_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root, 10.0)
    if branch_result is None or branch_result.returncode != 0:
        return None
    branch = branch_result.stdout.strip()
    if not branch or branch == "HEAD":  # detached
        return None
    count_result = _run_git(["rev-list", "--count", f"HEAD..origin/{branch}"], repo_root, 10.0)
    if count_result is None or count_result.returncode != 0:
        return None
    try:
        return int(count_result.stdout.strip())
    except ValueError:
        return None


def get_pending_update_count() -> "int | None":
    """Poll the async check's result. None until (and unless) updates exist."""
    return _commits_behind if _commits_behind else None


def start_background_check(bot_root: Path) -> None:
    """Kick off the once-per-launch check. Safe to call repeatedly."""
    global _check_started
    if _check_started:
        return
    _check_started = True

    def _worker() -> None:
        global _commits_behind
        try:
            repo_root = find_repo_root(bot_root)
            if repo_root is None:
                _logger.info("not a git checkout; update check skipped")
                return
            behind = count_commits_behind(repo_root)
            if behind:
                _logger.info("repository is %s commit(s) behind the remote", behind)
                _commits_behind = behind
        except Exception:
            _logger.exception("update check failed")

    threading.Thread(target=_worker, name="update-check", daemon=True).start()
