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
from ai_player.game_memory import MemoryBook, MemoryFileError, read_book
from ai_player.options import ENV_FRAMES, ENV_PACKAGE_ROOT, ENV_RUN_DIR, ENV_WALL_DEADLINE, VERDICT_FILE_NAME
from ai_player.paths import AppPaths

__all__ = [
    "END_CLASSES",
    "ENV_BUILD_ROOT",
    "GATE_REFUSED_EXIT",
    "LAUNCHES_SCHEMA",
    "NO_VERDICT_EXIT",
    "PROFILE_MARKER",
    "UNTRUSTED_ENV",
    "WALL_CLOCK_EXIT",
    "ChildResult",
    "ContinueCheck",
    "GateRun",
    "LaunchError",
    "archive_memory",
    "bot_command",
    "check_package_resolution",
    "child_env",
    "classify_end",
    "ensure_profile",
    "force_http_off",
    "hook_path",
    "kill_tree",
    "memory_check",
    "package_root",
    "read_launches",
    "read_verdict",
    "record_launch",
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


def seed_profile(profile_dir: Path, state: Path | None, fresh: bool, continue_game: bool = False,
                 game: AppPaths | None = None) -> str:
    """Put the profile's game state where the run needs it. Returns a log line.

    `fresh`: no state and no cartridge save, so the game boots to the title screen and New Game.
    `state`: the fixture becomes `current_state.ss1`, which the emulator loads at startup, and the
    cartridge save is emptied so nothing from an older run leaks in.
    Neither touches a profile that the launcher did not create.

    (R1 + R2, build spec 2026-10-29 D10, D11) `game`: the AI's files of this game (`paths.py` AppPaths).
    `continue_game` (`--continue`): the cartridge save is the truth, so `current_state.ss1` is DELETED (a state is tied
    to the build and carries RAM: a person's game is its save) and `current_save.sav` is kept; the AI plays the title
    itself. It needs the marker and a cartridge save (`memory_check` has already judged the memory file). `fresh` and
    `state` ARCHIVE an existing memory file (and `launches.jsonl`) into `retired/` (`archive_memory`: renamed, never
    deleted or rewritten). A start with NO flag on a game that has a memory file is REFUSED: it would load the last clean
    close's `.ss1` beside a newer cartridge save (two truths about one game).
    """
    if continue_game:
        if state is not None or fresh:
            raise LaunchError("--continue cannot be given with --state or --fresh")
        if not (profile_dir / PROFILE_MARKER).is_file():
            raise LaunchError(f"refusing to continue in {profile_dir.name}: it was not created by ai_player "
                              f"(no {PROFILE_MARKER})")
        cart = profile_dir / SAVE_FILE
        if not cart.is_file() or cart.stat().st_size == 0:
            raise LaunchError(f"--continue needs the cartridge save {SAVE_FILE} in {profile_dir.name}, and there is none")
        dropped = profile_dir / STATE_FILE
        had = dropped.exists()
        if had:
            dropped.unlink()
        return (f"[AI-RUN] state: CONTINUE ({STATE_FILE} {'removed' if had else 'absent'}; {SAVE_FILE} kept, "
                f"{cart.stat().st_size} bytes): the AI plays the title and continues its save")
    if state is None and not fresh:
        if game is not None and game.memory_jsonl.exists():
            raise LaunchError(f"{profile_dir.name} holds the AI's memory of a game ({game.memory_jsonl}): start it with "
                              f"--continue, or archive it with --fresh or --state (a start with no flag would load the last "
                              f"clean close's {STATE_FILE} beside a newer cartridge save)")
        return "[AI-RUN] state: resuming whatever the profile already holds"
    if state is not None and fresh:
        raise LaunchError("--state and --fresh are mutually exclusive")
    if not (profile_dir / PROFILE_MARKER).is_file():
        raise LaunchError(
            f"refusing to change game state in {profile_dir.name}: it was not created by ai_player "
            f"(no {PROFILE_MARKER}); use a new profile name"
        )
    archived = archive_memory(game) if game is not None else []
    for stale in (profile_dir / STATE_FILE, profile_dir / SAVE_FILE):
        if stale.exists():
            stale.unlink()
    states_dir = profile_dir / "states"
    if states_dir.is_dir():
        # Shutdown backups of earlier runs of this disposable profile; the emulator never auto-loads them.
        for backup in states_dir.glob("*.ss1"):
            backup.unlink()
    told = f"; the AI's memory archived: {', '.join(archived)}" if archived else ""
    if state is None:
        return f"[AI-RUN] state: FRESH (no current_state.ss1, no current_save.sav) -> title screen / New Game{told}"
    if not state.is_file():
        raise LaunchError(f"state file not found: {state}")
    shutil.copy2(state, profile_dir / STATE_FILE)
    return f"[AI-RUN] state: seeded from {state.name} md5={md5_of(state)} -> {STATE_FILE}{told}"


# ---------------------------------------------------------------------- R1 + R2: the AI's memory of a game, and ruling 52
#: (D20) `launches.jsonl`'s schema (its header line, D9: a NEWER one is refused, the file left as it is)
LAUNCHES_SCHEMA = 1
#: (D12 (a)) how the newest session of a memory file ended -> may it be continued. KILLED: no verdict and no launcher line
#: (the operator, the OS, a power cut). INVOLUNTARY: the process ended without the AI choosing it. CHOSEN: the AI ended the
#: run (`play: done:` / `play: stuck:`). BUDGET: the frame budget or the wall clock (interim, pending the user's U2). NOT
#: CLEAN: a purity or framework end. UNKNOWN: the session's run folder is gone and no launcher line names it.
END_CLASSES = ("KILLED", "INVOLUNTARY", "CHOSEN", "BUDGET", "NOT CLEAN", "UNKNOWN")
_INVOLUNTARY = ("crash", "frame-budget", "parked-manual", "abandoned", "interrupted", "interrupted-unresponsive")


@dataclass(frozen=True)
class ContinueCheck:
    """What `memory_check` found: `ok` (a continue may start), `why` (the sentence it prints), the newest save line, how
    the newest session ended (`END_CLASSES`) and the battles lost after the newest save (D12 (e))."""

    ok: bool
    why: str
    newest: dict | None = None
    end_class: str | None = None
    undone: int = 0


def read_launches(path: Path) -> list[dict]:
    """The `launch_end` lines of a `launches.jsonl` (read only; [] when there is none). A NEWER schema raises
    `LaunchError` with the file left as it is (D9); an unreadable line raises too (it is the launcher's own file)."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    out: list[dict] = []
    for number, raw in enumerate(lines, 1):
        try:
            line = json.loads(raw)
        except ValueError as error:
            raise LaunchError(f"{path}: line {number} cannot be read ({error})") from error
        if number == 1:
            version = line.get("schema_version") if isinstance(line, dict) and line.get("kind") == "header" else None
            if not isinstance(version, int):
                raise LaunchError(f"{path}: the first line is not a launches header")
            if version > LAUNCHES_SCHEMA:
                raise LaunchError(f"{path} was written by a newer program (schema {version}; this launcher reads "
                                  f"{LAUNCHES_SCHEMA}): refused, the file is left as it is")
            continue
        if isinstance(line, dict) and line.get("kind") == "launch_end":
            out.append(line)
    return out


def record_launch(game: AppPaths, run_dir: Path, result: ChildResult, verdict: dict | None) -> dict:
    """(D20) Append how this child ended to the game's `launches.jsonl` (its header first, for a new file): the exit
    code, whether the LAUNCHER hard-killed it at its wall clock, whether Ctrl+C interrupted it, and the verdict file's
    `exit_reason` (None: the child left no verdict). If the launcher itself is killed it writes nothing, which reads as
    KILLED, as it should."""
    facts = (verdict or {}).get("facts") or {}
    line = {"kind": "launch_end", "run_dir": str(run_dir), "exit_code": int(result.exit_code),
            "hard_kill": bool(result.killed and not result.interrupted), "interrupted": bool(result.interrupted),
            "exit_reason": facts.get("exit_reason") if verdict is not None else None,
            "ended": time.strftime("%Y-%m-%dT%H:%M:%S")}
    path = game.launches_jsonl
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding="utf-8") as handle:
        if new:
            handle.write(json.dumps({"kind": "header", "schema_version": LAUNCHES_SCHEMA}) + "\n")
        handle.write(json.dumps(line, ensure_ascii=True) + "\n")
    return line


def archive_memory(game: AppPaths) -> list[str]:
    """(D10) Move the game's `memory.jsonl` and `launches.jsonl` into `retired/` (`AppPaths.retired_path`: renamed,
    never deleted, never overwritten). Returns what was moved, as `<name> -> <archive>`."""
    moved: list[str] = []
    for path in (game.memory_jsonl, game.launches_jsonl):
        if not path.exists():
            continue
        target = game.retired_path(path.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
        moved.append(f"{path.name} -> {target}")
    return moved


def classify_end(book: MemoryBook, launches: list[dict]) -> tuple[str, str, bool]:
    """(D12 (a)) How the NEWEST session of the memory file ended: (class, in words, may it be continued). From three
    records, in this order of trust: the LAUNCHER's own line for the session's `run_dir` (`launches.jsonl`), else the
    run's verdict file (`purity.json`, written only by `lifecycle.finish`: an external kill leaves none), and the AI's own
    `end` line, which adds only whether the end came right after a save (`at_save`). A harness session (no lifecycle) is
    judged by its `end` line alone. CHOSEN and BUDGET are refused unless `at_save`, and refused with no `end` line (fail
    closed); a run folder that is gone with no launcher line is UNKNOWN (refused: a kill cannot be told from a choice).
    (R1 fix round, review R-2) A CHOSEN end of a continue that STOPPED BEFORE IT RESTORED ANYTHING (a bound or a failed
    read, `_stopped_before_restore`) is looked THROUGH: the session before it decides, since that continue changed nothing
    a later one could undo. Without this a timeout made the game impossible ever to continue again."""
    session = book.last_session()
    if session is None:
        return "UNKNOWN", "the memory file names no session", False
    sessions = book.sessions()
    for _ in range(len(sessions)):  # bounded: each pass steps one session back
        kind, words, allowed, reason = _classify_session(book, session, launches)
        earlier = _session_before(sessions, session)
        if kind != "CHOSEN" or earlier is None or not _stopped_before_restore(book, session, reason):
            return kind, words, allowed
        session = earlier
    return "UNKNOWN", "the memory file's sessions could not be followed back", False


#: the play brain's end when its continue stopped (`mode.py` HandsBrain._continue), without the `play: ` in front
_CONTINUE_STOPPED = "stuck: the continue stopped:"


def _session_before(sessions: list[dict], session: dict) -> dict | None:
    at = next((i for i, item in enumerate(sessions) if item is session), None)
    return sessions[at - 1] if at else None


def _stopped_before_restore(book: MemoryBook, session: dict, reason: str | None) -> bool:
    """(R1 fix round, review R-2) Session `session` was a CONTINUE that stopped before it restored anything: the host's
    own record of its end (`reason`: the launcher line's or the verdict's, or the `end` line's for a harness session) is
    the continue's stop; the AI's `end` line says `stopped_before_restore` (a bound or a failed read, not one of the
    spec's stops) and not chosen; it continued no save (`continued_from` None); and no `save` or `lost` line follows its
    session line (it played nothing)."""
    end = book.end_of(session["n"])
    if session.get("how") != "continue" or session.get("continued_from") is not None or end is None:
        return False
    if not end.get("stopped_before_restore") or end.get("chosen"):
        return False
    texts = [str(reason or ""), str(end.get("reason") or "")]
    if not all((text[len("play: "):] if text.startswith("play: ") else text).startswith(_CONTINUE_STOPPED)
               for text in texts):
        return False
    at = next(i for i, line in enumerate(book.lines) if line is session)
    return not any(line["kind"] in ("save", "lost") for line in book.lines[at + 1:])


def _classify_session(book: MemoryBook, session: dict, launches: list[dict]) -> tuple[str, str, bool, str | None]:
    """How session `session` ended (`classify_end`'s table, one session), and the reason it was judged by."""
    end = book.end_of(session["n"])
    at_save = bool(end is not None and end.get("at_save"))
    after = " right after a save" if at_save else ""
    if session.get("host") == "harness":
        if end is None:
            return "KILLED", f"harness session {session['n']} has no end line: it was killed", True, None
        # a continue stopped before its restore is judged as the chosen end it is, then looked through (classify_end)
        chosen = end.get("chosen") or end.get("stopped_before_restore")
        kind = "CHOSEN" if chosen else "BUDGET" if end.get("budget") else "INVOLUNTARY"
        allowed = kind == "INVOLUNTARY" or at_save
        return kind, f"harness session {session['n']} ended '{end.get('reason')}'{after}", allowed, end.get("reason")
    run_dir = session.get("run_dir")
    line = next((item for item in reversed(launches) if item.get("run_dir") == run_dir), None) if run_dir else None
    if line is not None:
        if line.get("interrupted"):
            return "INVOLUNTARY", f"session {session['n']} was interrupted (Ctrl+C reached the launcher)", True, None
        if line.get("hard_kill"):
            return ("BUDGET", f"session {session['n']} was killed by the launcher at its wall clock{after}", at_save,
                    None)
        reason = line.get("exit_reason")
    elif run_dir and Path(run_dir).is_dir():
        verdict = read_verdict(Path(run_dir))
        reason = ((verdict or {}).get("facts") or {}).get("exit_reason") if verdict is not None else None
        if verdict is None:
            return ("KILLED", f"session {session['n']} left no verdict file and no launcher line: killed from outside",
                    True, None)
    else:
        return ("UNKNOWN", f"session {session['n']}'s run folder {run_dir} is gone and no launcher line names it: a kill "
                           f"cannot be told from a chosen end", False, None)
    if reason is None:
        return "KILLED", f"session {session['n']}'s child left no verdict: killed from outside", True, None
    reason = str(reason)
    if reason in _INVOLUNTARY:
        return "INVOLUNTARY", f"session {session['n']} ended '{reason}'", True, reason
    if reason.startswith(("play: done:", "play: stuck:")):
        kind = "CHOSEN"
    elif reason.startswith("play: stopped:") or reason == "wall-clock":
        kind = "BUDGET"
    else:
        return "NOT CLEAN", f"session {session['n']} ended '{reason}'", False, reason
    if end is None:
        return (kind, f"session {session['n']} ended '{reason}' with no end line of the AI's (refused: fail closed)", False,
                reason)
    return kind, f"session {session['n']} ended '{reason}'{after}", at_save, reason


def memory_check(game: AppPaths) -> ContinueCheck:
    """(D11, D12) May this game be CONTINUED? Reads `memory.jsonl` and `launches.jsonl` read only: a newer schema is
    refused (the files left byte-identical), a memory file with no save line is refused, and how the newest session ended
    decides (`classify_end`). Also counts the battles lost after the newest save, which the continue undoes (D12 (e))."""
    try:
        book = read_book(game.memory_jsonl)
    except MemoryFileError as error:
        return ContinueCheck(False, f"the memory file cannot be continued: {error}")
    if book is None:
        return ContinueCheck(False, f"there is no memory file to continue ({game.memory_jsonl})")
    newest = book.newest_save()
    if newest is None:
        return ContinueCheck(False, "the memory file holds no save line: nothing to continue")
    try:
        launches = read_launches(game.launches_jsonl)
    except LaunchError as error:
        return ContinueCheck(False, str(error), newest)
    kind, words, allowed = classify_end(book, launches)
    undone = len(book.undone_losses(newest["id"]) or [])
    if not allowed:
        return ContinueCheck(False, f"a continue would reload after a {kind} end ({words}): USER RULING 52",
                             newest, kind, undone)
    return ContinueCheck(True, words, newest, kind, undone)


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
