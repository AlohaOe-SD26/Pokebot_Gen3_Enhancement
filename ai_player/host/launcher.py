"""The launcher: prepare a profile, start the framework headless in AI mode, enforce a wall clock.

WHY A SUBPROCESS: the framework owns its process (`pokebot.py` sets up the emulator, plugins and main
loop, and calls `sys.exit`). Running it as a child lets the AI's own program put a hard wall clock
around every run and kill the whole process tree, so a run can never outlive its budget, and it is
the seam that a standalone build will replace with its own ROM loader (RULING 37 Q1).

The launch line copies the batch runner's (`tools/story-dev/x4_headless.py` `lane_command`):
`pokebot.py <profile> -m <mode> -s 0 -na -hl` = unthrottled, muted, no GUI window (the renderer
stays on). stdin is DEVNULL so `pokebot.py`'s exit handler never waits for "Press Enter".

This module runs in the LAUNCHER process only. It does not import the framework; it finds it on
disk. Nothing here is on a hard-coded absolute path: the build root comes from `--build-root`,
else `AI_PLAYER_BUILD_ROOT`, else `<folder containing ai_player>/sandbox-pokebot`.

WHAT RUNS IS WHAT WAS GATED. The hook imports the `ai_player` this launcher names in
`AI_PLAYER_PACKAGE_ROOT` (its own package), so before starting the framework the launcher runs the
purity gate on exactly that package and that hook (`run_gate`) and refuses to launch on a FAIL
(exit 7) unless told `--allow-ungated` (the plant arms do that on purpose, to fault-test the live
audit on code the static gate refuses). The child's environment drops the variables that would make
Python import code from folders the gate never read (`UNTRUSTED_ENV`).

WHAT COUNTS IS THE VERDICT FILE. After the child exits, the launcher reads `<run_dir>/purity.json`,
written by the instrument from its own counters. A child that exits 0 without a CLEAN verdict file
that agrees with that exit is reported and the launcher exits 8: printed lines can be forged by any
code in the process, the file cannot be written by the AI's own code (gate rule f, and the instrument
accepts only the lifecycle's `finish` as its caller).

THE HTTP SERVER IS OFF FOR EVERY AI RUN (step 0.1, the adversarial review's finding 5). The
framework's HTTP server queues callbacks (`modules/main.py` `work_queue`) that run framework code on
the main thread between the AI's frames, and a profile's `http.yml` may switch it on. Step 0 wrote
`http.yml` only when it CREATED a profile, so an existing profile kept whatever it had. Now the
launcher rewrites it OFF on every run of an ai_player-owned profile, prints that in the run header,
and the session refuses to start (exit 9) if the server is on anyway (a profile the launcher does not
own, or a framework started by hand).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from ai_player import MODE_NAME
from ai_player.options import ENV_FRAMES, ENV_PACKAGE_ROOT, ENV_RUN_DIR, ENV_WALL_DEADLINE, VERDICT_FILE_NAME

__all__ = [
    "ENV_BUILD_ROOT",
    "GATE_REFUSED_EXIT",
    "NO_VERDICT_EXIT",
    "PROFILE_MARKER",
    "UNTRUSTED_ENV",
    "WALL_CLOCK_EXIT",
    "ChildResult",
    "GateRun",
    "LaunchError",
    "bot_command",
    "check_package_resolution",
    "child_env",
    "ensure_profile",
    "force_http_off",
    "hook_path",
    "kill_tree",
    "package_root",
    "read_verdict",
    "resolve_build_root",
    "run_child",
    "run_gate",
    "seed_profile",
    "soft_deadline_margin",
]

ENV_BUILD_ROOT = "AI_PLAYER_BUILD_ROOT"
PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # the folder that CONTAINS `ai_player/`

#: Written into every profile this launcher creates. Only a profile carrying it may have its game
#: state wiped (`--fresh`) or replaced (`--state`), so a person's own profile is never touched.
PROFILE_MARKER = ".ai_player_profile"
#: The template profile the batch runner uses; any profile's `metadata.yml` is a valid fallback,
#: because that file only binds the ROM.
PREFERRED_TEMPLATE = "endless-P1-torchic"
#: The file the emulator resumes from on startup (`modules/libmgba.py`, `LibmgbaEmulator.__init__`).
STATE_FILE = "current_state.ss1"
#: The cartridge save. A "fresh" boot with one present CONTINUES it (`tools/story-dev/livetest.py`).
SAVE_FILE = "current_save.sav"
WALL_CLOCK_EXIT = 124  # the conventional exit code of `timeout(1)`
#: The purity gate failed on the package the child would load, and `--allow-ungated` was not given.
GATE_REFUSED_EXIT = 7
#: The child exited 0, but its instrument's verdict file is missing, not CLEAN, or disagrees.
NO_VERDICT_EXIT = 8
#: Environment variables that make Python import or run code from places the gate never read: a
#: PYTHONPATH folder comes BEFORE the standard library (a `statistics.py` there would be what the
#: allowlisted `import statistics` loads), and a bytecode cache prefix moves `__pycache__` out of the
#: package, where rule (e) checks it.
UNTRUSTED_ENV = ("PYTHONPATH", "PYTHONHOME", "PYTHONPYCACHEPREFIX", "PYTHONSTARTUP")
GATE_TIMEOUT_SECONDS = 180

_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class LaunchError(RuntimeError):
    pass


def resolve_build_root(explicit: str | None = None) -> Path:
    raw = explicit or os.environ.get(ENV_BUILD_ROOT) or str(PACKAGE_ROOT / "sandbox-pokebot")
    root = Path(raw).resolve()
    if not (root / "pokebot.py").is_file():
        raise LaunchError(f"no pokebot.py under build root {root} (set --build-root or {ENV_BUILD_ROOT})")
    return root


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


HTTP_CONFIG = (
    "# Written by ai_player/host/launcher.py on EVERY run of this profile.\n"
    "# OFF: the HTTP server's work_queue callbacks would run framework code between the AI's frames,\n"
    "# and several headless processes cannot share one port anyway.\n"
    "http_server:\n  enable: false\n  ip: 127.0.0.1\n  port: 8888\n"
)


def force_http_off(profile_dir: Path) -> str:
    """Rewrite the profile's `http.yml` with the server OFF, if the launcher owns the profile.
    Returns the run-header line that says what the run will have."""
    if not (profile_dir / PROFILE_MARKER).is_file():
        return (
            f"[AI-RUN] http_server=UNCHANGED: profile {profile_dir.name} is not ai_player-owned, so its http.yml is "
            f"left alone; the session refuses to start (exit 9) if the server is on"
        )
    (profile_dir / "http.yml").write_text(HTTP_CONFIG, encoding="utf-8")
    return f"[AI-RUN] http_server=off (forced: {profile_dir.name}/http.yml rewritten with enable: false)"


def ensure_profile(build_root: Path, name: str, template: str | None = None) -> tuple[Path, str]:
    """Create the profile if missing. Returns (profile dir, a log line saying what was done).

    Copies ONLY `metadata.yml` from a donor profile, as `x4_headless.py` `ensure_lane_profile`
    does. `http.yml` is written by `force_http_off`, on every run, not only here.
    """
    if not _PROFILE_NAME_RE.match(name):
        raise LaunchError(f"profile name {name!r} may only contain letters, digits, '_', '-' and '.'")
    profiles = build_root / "profiles"
    path = profiles / name
    meta = path / "metadata.yml"
    if meta.is_file():
        owned = (path / PROFILE_MARKER).is_file()
        return path, f"[AI-RUN] profile {name} exists (ai_player-owned={owned})"

    donor_dir = profiles / (template or PREFERRED_TEMPLATE)
    if not (donor_dir / "metadata.yml").is_file():
        if template:
            raise LaunchError(f"template profile {template!r} has no metadata.yml")
        candidates = sorted(p.parent for p in profiles.glob("*/metadata.yml"))
        if not candidates:
            raise LaunchError(f"no profile under {profiles} has a metadata.yml to copy the ROM binding from")
        donor_dir = candidates[0]
    path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(donor_dir / "metadata.yml", meta)
    (path / "http.yml").write_text(HTTP_CONFIG, encoding="utf-8")
    (path / PROFILE_MARKER).write_text(
        f"Created by ai_player on {time.strftime('%Y-%m-%d %H:%M:%S')}; ROM binding copied from "
        f"profile '{donor_dir.name}'. The launcher may wipe or replace this profile's game state.\n",
        encoding="utf-8",
    )
    return path, f"[AI-RUN] profile {name} created (metadata.yml copied from '{donor_dir.name}')"


def seed_profile(profile_dir: Path, state: Path | None, fresh: bool) -> str:
    """Put the profile's game state where the run needs it. Returns a log line.

    `fresh`: no state and no cartridge save, so the game boots to the title screen and New Game.
    `state`: the fixture becomes `current_state.ss1`, which the emulator loads at startup, and the
    cartridge save is emptied so nothing from an older run leaks in.
    Neither touches a profile that the launcher did not create.
    """
    if state is None and not fresh:
        return "[AI-RUN] state: resuming whatever the profile already holds"
    if state is not None and fresh:
        raise LaunchError("--state and --fresh are mutually exclusive")
    if not (profile_dir / PROFILE_MARKER).is_file():
        raise LaunchError(
            f"refusing to change game state in {profile_dir.name}: it was not created by ai_player "
            f"(no {PROFILE_MARKER}); use a new profile name"
        )
    for stale in (profile_dir / STATE_FILE, profile_dir / SAVE_FILE):
        if stale.exists():
            stale.unlink()
    states_dir = profile_dir / "states"
    if states_dir.is_dir():
        # Shutdown backups of earlier runs of this disposable profile; the emulator never auto-loads them.
        for backup in states_dir.glob("*.ss1"):
            backup.unlink()
    if state is None:
        return "[AI-RUN] state: FRESH (no current_state.ss1, no current_save.sav) -> title screen / New Game"
    if not state.is_file():
        raise LaunchError(f"state file not found: {state}")
    shutil.copy2(state, profile_dir / STATE_FILE)
    return f"[AI-RUN] state: seeded from {state.name} md5={md5_of(state)} -> {STATE_FILE}"


def bot_command(build_root: Path, profile: str) -> list[str]:
    # NOT `python -s`: the framework's dependencies (confz, ...) live in the USER site-packages on this PC, so `-s`
    # breaks the framework at import (measured 2026-10-07). An `ai_player` shadowing ours from any site directory is
    # refused instead by `check_package_resolution`, which asks the child's own interpreter before launch.
    return [sys.executable, str(build_root / "pokebot.py"), profile, "-m", MODE_NAME, "-s", "0", "-na", "-hl"]


#: Run in the CHILD's interpreter and environment, with the child's path order (the script's folder first, the
#: repo root appended by the hook): which `ai_player` would the framework import?
_RESOLVE_PROBE = ("import sys, importlib.util as u; sys.path.insert(0, sys.argv[1]); sys.path.append(sys.argv[2]); "
                  "s = u.find_spec('ai_player'); print(s.origin if s and s.origin else '')")


def check_package_resolution(build_root: Path, env: dict[str, str]) -> str:
    """Refuse to launch unless the child would import THIS `ai_player`. The hook APPENDS the repo root to `sys.path`
    (so the standard library wins name clashes), which means an `ai_player` found earlier (the script folder,
    site-packages, a .pth entry) would win the import and could write its own CLEAN verdict. The session's in-package
    check cannot catch a package that never runs it, so this check runs from outside, before the child starts."""
    root = package_root()
    expected = (root / "ai_player" / "__init__.py").resolve()
    probe = subprocess.run([sys.executable, "-c", _RESOLVE_PROBE, str(build_root), str(root)], cwd=str(build_root),
                           env=env, capture_output=True, text=True, timeout=60)
    origin = probe.stdout.strip()
    if probe.returncode != 0 or not origin or Path(origin).resolve() != expected:
        raise LaunchError(f"the child would import ai_player from {origin or '(nothing)'}, not {expected} "
                          f"(probe exit {probe.returncode}: {probe.stderr.strip()[:200]})")
    return f"[AI-RUN] package: the child imports ai_player from {origin} (checked before launch)"


def soft_deadline_margin(wall_seconds: float) -> float:
    """How long before the hard kill the mode is asked to end itself (10% of the wall clock, 5-30 s).

    WHY TWO CLOCKS: a run killed from outside cannot print its `[AI-PURITY]` verdict, so a run that
    merely ran out of time would be unverified. The mode watches the SOFT deadline and exits with
    its verdict; the HARD kill stays as the backstop for a run that is truly stuck."""
    return min(30.0, max(5.0, wall_seconds * 0.1), wall_seconds / 2)


def package_root() -> Path:
    """The folder that CONTAINS this launcher's `ai_player/`: the package the child is told to load."""
    return PACKAGE_ROOT


def hook_path(build_root: Path) -> Path:
    return build_root / "plugins" / "custom_modes" / "ai_player_mode.py"


@dataclass
class GateRun:
    exit_code: int
    output: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def findings(self) -> list[str]:
        return [line.strip() for line in self.output.splitlines() if line.strip().startswith("FAIL")]


def run_gate(build_root: Path, package_root: Path = PACKAGE_ROOT) -> GateRun:
    """Run the purity gate (a separate process: the launcher never imports it) on the package the
    child will load and the hook it will run."""
    gate = package_root / "ai_player" / "gates" / "check_purity.py"
    if not gate.is_file():
        return GateRun(2, f"FAIL no purity gate at {gate}: an ungated package")
    cmd = [
        sys.executable, str(gate), "--package", str(package_root / "ai_player"),
        "--hook", str(hook_path(build_root)), "--build-root", str(build_root),
    ]
    env = {k: v for k, v in os.environ.items() if k not in UNTRUSTED_ENV}
    env["PYTHONUTF8"] = "1"
    try:
        done = subprocess.run(cmd, cwd=str(package_root), env=env, capture_output=True, timeout=GATE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return GateRun(2, f"FAIL the purity gate did not finish within {GATE_TIMEOUT_SECONDS}s")
    output = done.stdout.decode("utf-8", errors="replace") + done.stderr.decode("utf-8", errors="replace")
    return GateRun(done.returncode, output)


def read_verdict(run_dir: Path) -> dict | None:
    """The instrument's verdict file for this run, or None when there is none (or it is unreadable)."""
    path = run_dir / VERDICT_FILE_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def child_env(frames: int, run_dir: Path, wall_seconds: float) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in UNTRUSTED_ENV}
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"  # a piped stdout is block-buffered otherwise
    env["COLUMNS"] = "20000"  # rich wraps long lines at ~80 columns when stdout is not a console
    env[ENV_FRAMES] = str(frames)
    env[ENV_RUN_DIR] = str(run_dir)
    env[ENV_PACKAGE_ROOT] = str(PACKAGE_ROOT)
    env[ENV_WALL_DEADLINE] = f"{time.time() + wall_seconds - soft_deadline_margin(wall_seconds):.3f}"
    return env


@dataclass
class ChildResult:
    exit_code: int
    elapsed: float
    killed: bool
    killed_pids: list[int] = field(default_factory=list)
    survivors: list[int] = field(default_factory=list)
    interrupted: bool = False  # Ctrl+C reached the LAUNCHER; the child (no console) was killed


def _process_tree(pid: int) -> list[int]:
    try:
        import psutil
    except ImportError:
        return [pid]
    try:
        root = psutil.Process(pid)
        return [pid] + [child.pid for child in root.children(recursive=True)]
    except psutil.Error:
        return [pid]


def _alive(pids: list[int]) -> list[int]:
    try:
        import psutil
    except ImportError:
        return []
    alive = []
    for pid in pids:
        try:
            if psutil.Process(pid).status() != psutil.STATUS_ZOMBIE:
                alive.append(pid)
        except psutil.Error:
            pass  # gone, which is what we want
    return alive


def kill_tree(proc: subprocess.Popen) -> tuple[list[int], list[int]]:
    """Kill the child and every descendant. Returns (pids targeted, pids still alive afterwards)."""
    pids = _process_tree(proc.pid)
    try:
        import psutil

        for pid in reversed(pids):
            try:
                psutil.Process(pid).kill()
            except psutil.Error:
                pass
    except ImportError:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
        else:
            proc.kill()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass
    time.sleep(0.5)
    return pids, _alive(pids)


def run_child(cmd: list[str], cwd: Path, env: dict[str, str], wall_seconds: float, transcript: Path) -> ChildResult:
    """Run the child, echo its output line by line (and into `transcript`), and enforce the wall clock."""
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    def pump() -> None:
        with open(transcript, "a", encoding="utf-8", errors="replace") as handle:
            assert proc.stdout is not None
            for raw in iter(proc.stdout.readline, b""):
                text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                handle.write(text + "\n")
                handle.flush()
                try:
                    print(text, flush=True)
                except Exception:
                    pass

    reader = threading.Thread(target=pump, name="ai-player-child-output", daemon=True)
    reader.start()
    interrupted = killed = False
    pids: list[int] = []
    survivors: list[int] = []
    deadline = start + wall_seconds
    try:
        # Short waits in a loop: on Windows one long `Popen.wait()` cannot be interrupted, so Ctrl+C used to sit
        # unseen until the wall clock ran out (measured in the step 0.1 delta review).
        while proc.poll() is None:
            if time.monotonic() >= deadline:
                killed = True
                pids, survivors = kill_tree(proc)
                break
            try:
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        # The child runs without a console (CREATE_NO_WINDOW), so the user's Ctrl+C reached only
        # the launcher. Never leave an orphaned emulator behind: kill the tree and say so. (A
        # framework run in a console receives Ctrl+C itself and ends with a verdict: session.py.)
        # If the child already ended on its own, its exit code and verdict stand.
        if proc.poll() is None:
            killed, interrupted = True, True
            pids, survivors = kill_tree(proc)
    reader.join(timeout=10)
    elapsed = time.monotonic() - start
    code = WALL_CLOCK_EXIT if killed and not interrupted else (130 if interrupted else int(proc.returncode))
    return ChildResult(exit_code=code, elapsed=elapsed, killed=killed, killed_pids=pids, survivors=survivors,
                       interrupted=interrupted)
