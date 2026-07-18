#!/usr/bin/env python3
"""
Pokebot_Gen3_Enhancement — self-contained installer / updater / healer
for the CUSTOM bot (custom-pokebot/).

Run:  python install.py               (any Python 3.8+; finds/uses the right
                                       Python 3.11-3.13 for the bot itself)
      python install.py --check-only  (report state, change nothing)
      python install.py --yes         (unattended: auto-confirm, never launches)

One script, three jobs (adapted from the installer-as-codebase pattern in
PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md — git IS the FILES/HASHES
mechanism here):
  install : fresh machine -> find compatible Python, clone the repo ONCE,
            provide a ROM (from the repo, or sideloaded from next to this
            script), pre-install the bot's dependencies.
  update  : existing checkout -> incremental fetch + fast-forward pull
            (only the diff is downloaded — never the whole repo again).
  heal    : ANY tracked file drifted from the repo (edited, corrupted,
            deleted — including this script and the pristine mirror) is
            detected via git and restored on consent. User data (profiles,
            saves, extra ROMs, logs) is untracked and is NEVER touched.

Every run appends a full trace to install.log next to this script; the
console shows the friendly colored summary. Exit code 0 = no failures.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import logging
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

# Windows consoles often default to cp1252, which cannot encode ✓/⚠/✗ —
# reconfigure to UTF-8 (with replacement, never a crash) before any output.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

SCRIPT_VERSION: str = "2026-07-18-CUSTOM-ROBUST-V2"
REPO_URL: str = "https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git"
REPO_DIR_NAME: str = "Pokebot_Gen3_Enhancement"
BOT_DIR_NAME: str = "custom-pokebot"
HERE: Path = Path(__file__).resolve().parent
LOG_FILE: Path = HERE / "install.log"
LOG_MAX_BYTES: int = 1_000_000  # rotate to install.log.old past this

CRITICAL_FILES: list = [
    "pokebot.py",
    "requirements.py",
    "modules/main.py",
    "modules/plugins.py",
    "modules/gui/dashboard_gui.py",
    "plugins/custom_modes_loader.py",
    "plugins/custom_modes/patrol.py",
]

ASSUME_YES: bool = False
log = logging.getLogger("installer")

# Step ledger: name -> "OK" | "WARN" | "FAIL" (worst result wins per step)
STEP_RESULTS: dict = {}
_current_step: str = ""


def _record(level: str) -> None:
    order = {"OK": 0, "WARN": 1, "FAIL": 2}
    if _current_step:
        previous = STEP_RESULTS.get(_current_step, "OK")
        if order[level] > order[previous]:
            STEP_RESULTS[_current_step] = level


def _ok(message: str) -> None:
    print(f"\033[32m  ✓ {message}\033[0m")
    log.info("OK: %s", message)
    _record("OK")


def _warn(message: str) -> None:
    print(f"\033[33m  ⚠ {message}\033[0m")
    log.warning("WARN: %s", message)
    _record("WARN")


def _err(message: str) -> None:
    print(f"\033[31m  ✗ {message}\033[0m")
    log.error("FAIL: %s", message)
    _record("FAIL")


def _dim(message: str) -> None:
    print(f"\033[90m    {message}\033[0m")
    log.info("    %s", message)


def setup_logging() -> None:
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > LOG_MAX_BYTES:
            shutil.move(str(LOG_FILE), str(LOG_FILE.with_suffix(".log.old")))
    except OSError:
        pass  # rotation is best-effort; never block the install on it
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.info("=" * 70)
    log.info("installer %s starting  ·  argv=%s  ·  python=%s", SCRIPT_VERSION, sys.argv, sys.version.split()[0])


def _run(args: list, cwd: Path | None = None, capture: bool = True) -> subprocess.CompletedProcess:
    log.info("run: %s  (cwd=%s)", " ".join(str(a) for a in args), cwd or HERE)
    result = subprocess.run(args, cwd=cwd, capture_output=capture, text=True)
    if capture:
        if result.stdout and result.stdout.strip():
            log.info("  stdout: %s", result.stdout.strip()[:2000])
        if result.stderr and result.stderr.strip():
            log.info("  stderr: %s", result.stderr.strip()[:2000])
    log.info("  exit code: %s", result.returncode)
    return result


def _ask_yes_no(prompt: str) -> bool:
    """input() that tolerates EOF, --yes mode, and PowerShell's piped-BOM quirk."""
    if ASSUME_YES:
        print(f"{prompt}y (--yes)")
        log.info("prompt auto-answered yes (--yes): %s", prompt.strip())
        return True
    try:
        answer = input(prompt).lstrip("﻿").strip().lower() == "y"
        log.info("prompt: %s -> %s", prompt.strip(), "y" if answer else "n")
        return answer
    except EOFError:
        log.info("prompt: %s -> EOF (treated as no)", prompt.strip())
        return False


def step(number: int, total: int, title: str):
    """Decorator-free step runner: prints the banner, catches ALL exceptions so
    one broken step cannot take down the run silently — the error is logged
    with a full traceback, the step is marked FAIL, and the run continues
    (main() aborts explicitly only where continuing makes no sense)."""

    class _StepContext:
        def __init__(self, name: str):
            self.name = name

        def __enter__(self):
            global _current_step
            _current_step = self.name
            STEP_RESULTS.setdefault(self.name, "OK")
            print(f"\n[{number}/{total}]  {title}")
            log.info("--- step %s/%s: %s", number, total, title)
            return self

        def __exit__(self, exc_type, exc, tb):
            global _current_step
            if exc is not None:
                _err(f"Unexpected error in this step: {exc}")
                log.error("traceback:\n%s", "".join(traceback.format_exception(exc_type, exc, tb)))
            _current_step = ""
            return True  # never propagate — the ledger carries the failure

    return _StepContext(title)


# ---------------------------------------------------------------- python
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


# ---------------------------------------------------------------- repo
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
    print(f"       No checkout found - cloning (one time only) into {clone_target}")
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
    """Incremental update: fetch + fast-forward only. Never rebases/merges/resets."""
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
        _ok("Repository is up to date with the remote (incremental check, nothing downloaded).")
    elif behind > 0 and ahead == 0:
        if check_only:
            _warn(f"{behind} update(s) available (re-run without --check-only to apply).")
        else:
            pull = _run(["git", "pull", "--ff-only"], cwd=repo)
            if pull.returncode == 0:
                _ok(f"Updated: pulled {behind} new commit(s) (only the diff was downloaded).")
            else:
                _err("Fast-forward pull failed - resolve manually (git pull). Details in install.log.")
    else:
        _warn(f"Local branch is ahead ({ahead}) of the remote - not touching it. Push or reconcile manually.")


def heal_repo_files(repo: Path, check_only: bool) -> None:
    """Detect drift in ALL tracked files (bot, mirror, docs, this script) and
    restore on consent. Untracked files (profiles, saves, logs, extra ROMs)
    never show up here, so user data cannot be touched."""
    status = _run(["git", "status", "--porcelain=v1"], cwd=repo)
    drifted: list = []
    for line in status.stdout.splitlines():
        if len(line) > 3 and not line.startswith("??"):
            path = line[3:].strip()
            # Renames come as `old -> new`; the file to restore is the new path.
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            # git quotes paths containing spaces/specials and escapes " and \
            # inside — unquote, or `git checkout -- <path>` cannot match them.
            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            drifted.append(path)

    if not drifted:
        _ok("All tracked files match the repository (no drift anywhere).")
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
            _ok("Restored. (Profiles/saves/extra ROMs are untracked and were not touched.)")
        else:
            _err(f"Restore failed: {result.stderr.strip()} (see install.log)")
    else:
        _dim("Left as-is. If these are intentional edits, commit them; see DIVERGENCE-LOG.md.")


# ---------------------------------------------------------------- ROMs
def known_rom_hashes(bot_dir: Path) -> set:
    """Parse the bot's ROM whitelist (SHA-1 hex digests) straight out of
    modules/roms.py — no imports needed, so this works before deps exist."""
    try:
        text = (bot_dir / "modules" / "roms.py").read_text(encoding="utf-8", errors="replace")
        return set(h.lower() for h in re.findall(r"\b[0-9a-fA-F]{40}\b", text))
    except OSError as error:
        log.warning("could not parse ROM whitelist: %s", error)
        return set()


def ensure_rom(bot_dir: Path, check_only: bool) -> None:
    """The bot needs a .gba ROM in custom-pokebot/roms/. Preference order:
    1. ROM(s) already there (the repo ships one, so clones are covered).
    2. Sideload: .gba file(s) sitting next to this script get copied in.
    3. Neither -> clear instructions."""
    roms_dir = bot_dir / "roms"
    existing = sorted(roms_dir.glob("*.gba")) if roms_dir.is_dir() else []
    whitelist = known_rom_hashes(bot_dir)

    def _verify(rom: Path) -> None:
        digest = hashlib.sha1(rom.read_bytes()).hexdigest()
        log.info("ROM %s sha1=%s", rom.name, digest)
        if whitelist and digest in whitelist:
            _ok(f"{rom.name} - verified against the bot's known-good list.")
        elif whitelist:
            _warn(f"{rom.name} - NOT in the bot's known-good list; the bot will refuse it "
                  f"unless added to roms/extra_allowed_roms.txt.")
        else:
            _dim(f"{rom.name} present (whitelist unavailable, skipped verification).")

    if existing:
        for rom in existing:
            _verify(rom)
        return

    sideload = sorted(p for p in HERE.glob("*.gba") if p.is_file())
    if sideload:
        if check_only:
            _warn(f"No ROM in {BOT_DIR_NAME}/roms/ - {len(sideload)} .gba found next to this "
                  f"script (would be copied on a real run).")
            return
        roms_dir.mkdir(parents=True, exist_ok=True)
        for rom in sideload:
            destination = roms_dir / rom.name
            if destination.exists():
                _dim(f"{rom.name} already exists in roms/, skipped.")
                continue
            shutil.copy2(rom, destination)
            _ok(f"Copied {rom.name} into {BOT_DIR_NAME}/roms/ (original left in place).")
            _verify(destination)
        return

    _warn(f"No ROM found. Put your .gba file in {BOT_DIR_NAME}/roms/ "
          f"(or next to this script and re-run - it will be copied in).")


# ---------------------------------------------------------------- deps
def install_dependencies(python: Path, bot_dir: Path) -> bool:
    """Pre-run the bot's own dependency bootstrap (idempotent; hash-gated;
    the fork's smart check only installs what is actually missing).

    When non-interactive (piped stdin or --yes), answer its confirmation
    prompt explicitly instead of letting the child fight over our stdin."""
    command = [str(python), "-c", "from requirements import check_requirements; check_requirements()"]
    log.info("dependency bootstrap: %s (cwd=%s)", " ".join(command), bot_dir)
    if ASSUME_YES or not sys.stdin.isatty():
        result = subprocess.run(command, cwd=bot_dir, input="y\n", text=True)
    else:
        result = subprocess.run(command, cwd=bot_dir)
    log.info("dependency bootstrap exit code: %s", result.returncode)
    return result.returncode == 0


# ---------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description="Pokebot_Gen3_Enhancement custom installer/updater/healer")
    parser.add_argument("--check-only", action="store_true", help="Report state without changing anything.")
    parser.add_argument("--yes", action="store_true", help="Answer yes to all prompts (unattended install/heal).")
    args = parser.parse_args()

    global ASSUME_YES
    ASSUME_YES = args.yes

    setup_logging()
    print(f"\n  Pokebot_Gen3_Enhancement custom installer  ·  {SCRIPT_VERSION}")
    print(f"  Log: {LOG_FILE}")
    print("  " + "=" * 62)

    total = 7
    bot_python: Path | None = None
    repo: Path | None = None

    with step(1, total, "Locating 64-bit Python 3.11-3.13 for the bot"):
        bot_python = find_bot_python()
        if bot_python is None and not args.check_only:
            _warn("No compatible Python found.")
            if offer_python_install():
                bot_python = find_bot_python()
        if bot_python is None:
            _err("The bot needs 64-bit Python 3.11-3.13. Install it, then re-run.")
        else:
            _ok(f"Using {bot_python}")

    with step(2, total, "Checking git"):
        if _run(["git", "--version"]).returncode != 0:
            _err("git is required. Install it from https://git-scm.com/ then re-run.")
        else:
            _ok("git available")

    aborted = False
    if STEP_RESULTS.get("Checking git") == "FAIL" or (bot_python is None and not args.check_only):
        aborted = True  # nothing below can succeed without these

    if not aborted:
        with step(3, total, "Locating repository / applying incremental updates"):
            repo = locate_repo(args.check_only)
            if repo is None:
                if args.check_only:
                    _err("No repository available - re-run without --check-only to clone it.")
                else:
                    _err("Clone failed - check network access/credentials and try a shorter install path.")
            else:
                _dim(f"repo: {repo}")
                sync_repo(repo, args.check_only)

    if repo is not None:
        bot_dir = repo / BOT_DIR_NAME

        with step(4, total, "Verifying repository integrity (self-heal)"):
            heal_repo_files(repo, args.check_only)

        with step(5, total, "Checking for a game ROM"):
            ensure_rom(bot_dir, args.check_only)

        with step(6, total, "Installing/verifying bot dependencies"):
            if args.check_only:
                marker = bot_dir / ".last-requirements-check"
                if marker.exists():
                    _ok("Dependency bootstrap has run before.")
                else:
                    _warn("Dependencies not yet installed (a real run will do it).")
            elif bot_python is not None:
                if install_dependencies(bot_python, bot_dir):
                    _ok("Dependencies present (bot's own smart bootstrap - only missing modules get installed).")
                else:
                    _err("Dependency bootstrap reported an error - see output above and install.log.")

        with step(7, total, "Smoke check"):
            missing = [f for f in CRITICAL_FILES if not (bot_dir / f).exists()]
            if missing:
                for path in missing:
                    _warn(f"missing: {BOT_DIR_NAME}/{path}")
            else:
                _ok(f"{len(CRITICAL_FILES)} critical files present (dashboard GUI + custom modes included)")
            profiles_dir = bot_dir / "profiles"
            profiles = [p for p in profiles_dir.iterdir() if p.is_dir()] if profiles_dir.is_dir() else []
            _dim(f"{len(profiles)} profile(s) found" if profiles else "No profiles yet - created on first launch.")

    # ------- final summary -------
    print("\n  " + "=" * 62)
    worst = "OK"
    for name, result in STEP_RESULTS.items():
        symbol = {"OK": "\033[32m✓\033[0m", "WARN": "\033[33m⚠\033[0m", "FAIL": "\033[31m✗\033[0m"}[result]
        print(f"   {symbol}  {name}")
        if result == "FAIL":
            worst = "FAIL"
        elif result == "WARN" and worst == "OK":
            worst = "WARN"
    log.info("summary: %s", STEP_RESULTS)
    if worst == "FAIL":
        print(f"\n  \033[31mCompleted with failures\033[0m - details above and in {LOG_FILE.name}.")
    elif worst == "WARN":
        print(f"\n  \033[33mCompleted with warnings\033[0m - review above; log: {LOG_FILE.name}.")
    else:
        print("\n  \033[32mAll good.\033[0m Re-run this script anytime to update + heal.")
    print("  " + "=" * 62)

    if repo is not None and not args.check_only and bot_python is not None:
        print(f"\n  To launch:  cd {BOT_DIR_NAME} && \"{bot_python}\" pokebot.py\n")
        # Never auto-launch in --yes/unattended mode - the GUI would block forever.
        if not ASSUME_YES and sys.stdin.isatty() and _ask_yes_no("  Launch the bot now? [y/N] "):
            subprocess.run([str(bot_python), "pokebot.py"], cwd=repo / BOT_DIR_NAME)

    sys.exit(1 if worst == "FAIL" else 0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n  Interrupted by user.")
        log.info("interrupted by user")
        sys.exit(130)
    except Exception as unhandled:  # last-resort net: log it, tell the user where to look
        log.critical("UNHANDLED:\n%s", traceback.format_exc())
        print(f"\n\033[31m  ✗ Unexpected error: {unhandled}\033[0m")
        print(f"  Full details were written to {LOG_FILE}")
        sys.exit(1)
