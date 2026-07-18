#!/usr/bin/env python3
"""
Pokebot_Gen3_Enhancement — self-contained installer / updater / healer.

Run:  python install.py            (any Python 3.8+; it finds/uses the right
                                    Python 3.11-3.13 for the bot itself)
      python install.py --check-only   (report state, change nothing)

One script, three jobs (adapted from the installer-as-codebase pattern in
PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md — here, git IS the
FILES/HASHES mechanism, so this script drives git instead of base64 blobs):
  install : fresh machine -> find compatible Python, clone the repo,
            pre-install the bot's dependencies.
  update  : existing checkout -> fetch + fast-forward pull (never destructive).
  heal    : tracked files drifted from the repo (edited/corrupted/deleted)
            are detected via git and can be restored on consent. User data
            (profiles/, roms/, saves) is untracked/gitignored and is NEVER
            touched.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Windows consoles often default to cp1252, which cannot encode ✓/⚠/✗ —
# reconfigure to UTF-8 (with replacement, never a crash) before any output.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

SCRIPT_VERSION: str = "2026-07-17-INITIAL-V1"
REPO_URL: str = "https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git"
REPO_DIR_NAME: str = "Pokebot_Gen3_Enhancement"
BOT_DIR_NAME: str = "custom-pokebot"
HERE: Path = Path(__file__).resolve().parent

CRITICAL_FILES: list = [
    "pokebot.py",
    "requirements.py",
    "modules/main.py",
    "modules/plugins.py",
    "plugins/custom_modes_loader.py",
    "plugins/custom_modes/patrol.py",
]


def _ok(message: str) -> None:
    print(f"\033[32m  ✓ {message}\033[0m")


def _warn(message: str) -> None:
    print(f"\033[33m  ⚠ {message}\033[0m")


def _err(message: str) -> None:
    print(f"\033[31m  ✗ {message}\033[0m")


def _dim(message: str) -> None:
    print(f"\033[90m    {message}\033[0m")


def _run(args: list, cwd: Path | None = None, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=capture, text=True)


ASSUME_YES: bool = False


def _ask_yes_no(prompt: str) -> bool:
    """input() that tolerates EOF, --yes mode, and PowerShell's piped-BOM quirk."""
    if ASSUME_YES:
        print(f"{prompt}y (--yes)")
        return True
    try:
        # PowerShell 5.1 prepends a UTF-8 BOM to the first line it pipes to
        # a native process — strip it or a piped "y" never matches.
        return input(prompt).lstrip("﻿").strip().lower() == "y"
    except EOFError:
        return False


def find_bot_python() -> Path | None:
    """Find a 64-bit Python 3.11-3.13 (what the bot's own bootstrap requires)."""
    candidates: list = []

    launcher = _run(["py", "-0p"])
    if launcher.returncode == 0:
        for line in launcher.stdout.splitlines():
            match = re.match(r"\s*-V:(\d+)\.(\d+)(?:-\d+)?\s+\*?\s+(.+?)\s*$", line)
            if match and int(match.group(1)) == 3 and 11 <= int(match.group(2)) <= 13:
                candidates.append(Path(match.group(3)))

    for name in ("python3.13", "python3.12", "python3.11", "python"):
        which = _run(["where" if sys.platform == "win32" else "which", name])
        if which.returncode == 0:
            candidates.extend(Path(p) for p in which.stdout.splitlines() if p.strip())

    seen: set = set()
    for candidate in candidates:
        if candidate in seen or not candidate.exists():
            continue
        seen.add(candidate)
        probe = _run(
            [str(candidate), "-c", "import platform,struct;print(platform.python_version());print(struct.calcsize('P')*8)"]
        )
        if probe.returncode != 0:
            continue
        lines = probe.stdout.splitlines()
        if len(lines) >= 2 and lines[1].strip() == "64":
            version_parts = lines[0].strip().split(".")
            if len(version_parts) >= 2 and version_parts[0] == "3" and 11 <= int(version_parts[1]) <= 13:
                return candidate
    return None


def offer_python_install() -> bool:
    """No compatible Python found: offer a winget install (Windows only)."""
    if sys.platform != "win32":
        _dim("Install Python 3.12 (64-bit) with your package manager, then re-run.")
        return False
    if _run(["winget", "--version"]).returncode != 0:
        _dim("Install Python 3.12 (64-bit) from https://www.python.org/downloads/ then re-run.")
        return False
    if not _ask_yes_no("  Install Python 3.12 now via winget? [y/N] "):
        _dim("Install Python 3.11-3.13 (64-bit) manually, then re-run this script.")
        return False
    result = subprocess.run(["winget", "install", "-e", "--id", "Python.Python.3.12"])
    return result.returncode == 0


def locate_repo(check_only: bool) -> Path | None:
    """Return the repo root: this checkout if the script lives in one, else clone."""
    if (HERE / ".git").is_dir() and (HERE / BOT_DIR_NAME).is_dir():
        return HERE
    clone_target = HERE / REPO_DIR_NAME
    if (clone_target / ".git").is_dir():
        return clone_target
    if check_only:
        _warn("No checkout found here (--check-only: not cloning).")
        return None
    print(f"       No checkout found - cloning into {clone_target}")
    # core.longpaths: the repo contains sprite paths that exceed Windows'
    # 260-char MAX_PATH in deeper folders - without this the checkout fails.
    result = subprocess.run(["git", "clone", "-c", "core.longpaths=true", REPO_URL, str(clone_target)])
    if result.returncode != 0:
        # A failed clone leaves a broken half-checkout that would be mistaken
        # for a real repo on the next run - remove it.
        shutil.rmtree(clone_target, ignore_errors=True)
        return None
    _run(["git", "config", "core.longpaths", "true"], cwd=clone_target)
    return clone_target


def sync_repo(repo: Path, check_only: bool) -> None:
    """Fetch and fast-forward if behind. Never rebases, resets, or merges."""
    fetch = _run(["git", "fetch", "origin"], cwd=repo)
    if fetch.returncode != 0:
        _warn("Could not reach the remote (offline?) - continuing with local state.")
        return

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()
    counts = _run(["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"], cwd=repo)
    if counts.returncode != 0:
        _warn(f"Branch `{branch}` has no origin counterpart - skipping update check.")
        return
    ahead, behind = (int(n) for n in counts.stdout.split())

    if behind == 0 and ahead == 0:
        _ok("Repository is up to date with the remote.")
    elif behind > 0 and ahead == 0:
        if check_only:
            _warn(f"{behind} update(s) available (re-run without --check-only to apply).")
        else:
            pull = _run(["git", "pull", "--ff-only"], cwd=repo)
            if pull.returncode == 0:
                _ok(f"Updated: pulled {behind} new commit(s).")
            else:
                _err("Fast-forward pull failed - resolve manually (git pull).")
    else:
        _warn(f"Local branch is ahead ({ahead}) of the remote - not touching it. Push or reconcile manually.")


def heal_bot_files(repo: Path, check_only: bool) -> None:
    """Detect tracked-file drift under the bot dir; restore only with consent."""
    status = _run(["git", "status", "--porcelain=v1", "--", BOT_DIR_NAME], cwd=repo)
    drifted: list = []
    for line in status.stdout.splitlines():
        if len(line) > 3 and not line.startswith("??"):
            drifted.append(line[3:].strip())

    if not drifted:
        _ok(f"All tracked files in {BOT_DIR_NAME}/ match the repository (no drift).")
        return

    _warn(f"{len(drifted)} tracked file(s) differ from the repository:")
    for path in drifted[:20]:
        _dim(f"~ {path}")
    if len(drifted) > 20:
        _dim(f"... and {len(drifted) - 20} more")

    if check_only:
        _dim("(--check-only: not restoring)")
        return
    if _ask_yes_no(f"  Restore these {len(drifted)} file(s) to the repository version? [y/N] "):
        result = _run(["git", "checkout", "--", *drifted], cwd=repo)
        if result.returncode == 0:
            _ok("Restored. (Your profiles/ROMs/saves are untracked and were not touched.)")
        else:
            _err(f"Restore failed: {result.stderr.strip()}")
    else:
        _dim("Left as-is. If these are intentional edits, commit them; see DIVERGENCE-LOG.md.")


def install_dependencies(python: Path, bot_dir: Path) -> bool:
    """Pre-run the bot's own dependency bootstrap (idempotent; hash-gated).

    The bootstrap asks "Install those modules? [y/N]" on its first run. When
    we're non-interactive (piped stdin or --yes), answer it explicitly
    instead of letting the child fight over our stdin.
    """
    command = [str(python), "-c", "from requirements import check_requirements; check_requirements()"]
    if ASSUME_YES or not sys.stdin.isatty():
        result = subprocess.run(command, cwd=bot_dir, input="y\n", text=True)
    else:
        result = subprocess.run(command, cwd=bot_dir)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Pokebot_Gen3_Enhancement installer/updater/healer")
    parser.add_argument("--check-only", action="store_true", help="Report state without changing anything.")
    parser.add_argument("--yes", action="store_true", help="Answer yes to all prompts (unattended install/heal).")
    args = parser.parse_args()

    global ASSUME_YES
    ASSUME_YES = args.yes

    print(f"\n  Pokebot_Gen3_Enhancement installer  ·  {SCRIPT_VERSION}")
    print("  " + "=" * 62)

    # [1/6] Compatible Python for the bot
    print("\n[1/6]  Locating 64-bit Python 3.11-3.13 for the bot")
    bot_python = find_bot_python()
    if bot_python is None and not args.check_only:
        _warn("No compatible Python found.")
        if offer_python_install():
            bot_python = find_bot_python()
    if bot_python is None:
        _err("The bot needs 64-bit Python 3.11-3.13. Install it, then re-run.")
        if not args.check_only:
            sys.exit(1)
    else:
        _ok(f"Using {bot_python}")

    # [2/6] Git available
    print("\n[2/6]  Checking git")
    if _run(["git", "--version"]).returncode != 0:
        _err("git is required. Install it from https://git-scm.com/ then re-run.")
        sys.exit(1)
    _ok("git available")

    # [3/6] Repo present + updates
    print("\n[3/6]  Locating repository / applying updates")
    repo = locate_repo(args.check_only)
    if repo is None:
        if args.check_only:
            _err("No repository available - re-run without --check-only to clone it.")
        else:
            _err("Clone failed - check network access/credentials and try a shorter install path.")
        sys.exit(1)
    _dim(f"repo: {repo}")
    sync_repo(repo, args.check_only)
    bot_dir = repo / BOT_DIR_NAME

    # [4/6] Heal drifted tracked files
    print(f"\n[4/6]  Verifying {BOT_DIR_NAME}/ integrity (git drift check)")
    heal_bot_files(repo, args.check_only)

    # [5/6] Bot dependencies (the bot's own bootstrap, pre-run)
    print("\n[5/6]  Installing/verifying bot dependencies")
    if args.check_only:
        marker = bot_dir / ".last-requirements-check"
        _ok("Dependency bootstrap has run before.") if marker.exists() else _warn(
            "Dependencies not yet installed (first launch or install.py will do it)."
        )
    elif bot_python is not None:
        if install_dependencies(bot_python, bot_dir):
            _ok("Dependencies present (bot's own bootstrap, hash-gated + idempotent).")
        else:
            _err("Dependency bootstrap reported an error - see output above.")

    # [6/6] Smoke check + user data status
    print("\n[6/6]  Smoke check")
    missing = [f for f in CRITICAL_FILES if not (bot_dir / f).exists()]
    if missing:
        for path in missing:
            _warn(f"missing: {BOT_DIR_NAME}/{path}")
    else:
        _ok(f"{len(CRITICAL_FILES)} critical files present (incl. custom modes)")
    roms = list((bot_dir / "roms").glob("*.gba")) if (bot_dir / "roms").is_dir() else []
    profiles_dir = bot_dir / "profiles"
    profiles = [p for p in profiles_dir.iterdir() if p.is_dir()] if profiles_dir.is_dir() else []
    _ok(f"{len(roms)} ROM(s) found") if roms else _warn(f"No ROMs yet - place your .gba files in {BOT_DIR_NAME}/roms/")
    _dim(f"{len(profiles)} profile(s) found" if profiles else "No profiles yet - created on first launch.")

    print("\n  " + "=" * 62)
    _ok("Done. Re-run this script anytime to update + heal.")
    print("  " + "=" * 62)
    if not args.check_only and bot_python is not None:
        print(f"\n  To launch:  cd {BOT_DIR_NAME} && \"{bot_python}\" pokebot.py\n")
        # Never auto-launch in --yes/unattended mode — the GUI would block forever.
        if not ASSUME_YES and sys.stdin.isatty() and _ask_yes_no("  Launch the bot now? [y/N] "):
            subprocess.run([str(bot_python), "pokebot.py"], cwd=bot_dir)


if __name__ == "__main__":
    main()
