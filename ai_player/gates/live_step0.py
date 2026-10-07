"""LIVE PROOF of AI-player build step 0 (purity scaffolding): every arm through the real CLI.

    py -3.12 ai_player/gates/live_step0.py [--arms A,P,B,...]

Each arm runs `py -3.12 -m ai_player run ...` (the real launcher, the real purity gate the launcher
runs first, the real headless framework, the real hook) under a wall clock, grades the run, prints
PASS/FAIL with the evidence lines, and writes the whole transcript to
`ai_player/evidence/<date>-step0-<ARM>.txt`. Exit 0 only if every arm passed.

WHAT A RUN IS GRADED FROM: the instrument's VERDICT FILE (`<run_dir>/purity.json`, written by
`platform/attribution.py` from its own counters, and only when `lifecycle.finish` asks). Printed lines
are evidence for people, and each arm checks that the printed `[AI-PURITY]` line agrees with the file,
but no grade rests on a line the AI's own code could have printed (arm XE prints a forged one). The
driver picks the run directory itself (`--run-dir`), so it never reads a path the child printed.
Launcher lines are trusted only when printed BEFORE the child started (the first `[AI-GATE]` line).

THREE KINDS OF FAULT ARM
* SWITCH arms set an `AI_PLAYER_FAULT_*` variable that the AI's own code reads (`options.py`), so
  the fault runs the production path.
* PLANT arms (X*) copy the package to a temporary folder, add a `_plant.py` that does one forbidden
  thing from inside the brain (`tick(step, session)` is called every brain step), and run THAT copy
  through the real launcher with `--allow-ungated` (the launcher gates the copy and, rightly, refuses
  it otherwise: arm XR proves that). Each plant arm grades BOTH halves on the same plant where both
  apply: the static gate must FAIL the copy with the predicted rule in `_plant.py`, and the live audit
  must catch the action. The real package is only read.
* RUNTIME-ONLY plants (XE, XY, XZ) attack the EVIDENCE rather than the game, with code the static gate
  has no rule against by design (printing a line, replacing the session's lifecycle). Their guard is
  the verdict file and the launcher's check of it; the static result is recorded, not graded.

PRE-REGISTERED PREDICTIONS (written before the graded runs; the grade code below encodes them)
-----------------------------------------------------------------------------------------------
Honesty note: A..XT were graded PASS on the previous instrument (the second verifier re-ran all 20).
The instrument, lifecycle and launcher changed since (layer 3, the verdict file, sealing, the gate in
the launcher), so every arm is re-run. The new arms (XB, XG, XK, XE, XY, XZ, XR) are predicted cold,
except that XB and XG are the second verifier's own plants VB and VP, whose OLD results are known
(VB: static PASS + live CLEAN; VP: static PASS + live BREACH via ai_unrouted_presses).

A   normal, fresh New Game, 3000 frames. PREDICT exit 0, `reason=step0-placeholder`, every breach
    counter 0 (incl. ai_bot_calls), ai_presses=0, real_frames>=3000, verdict CLEAN; gate PASS on the
    real package before launch; the verdict file names the real package.
P   CONTROL (`AI_PLAYER_CONTROL_TAP=1`), fresh: PREDICT ai_presses=50 EXACTLY, ai_unrouted_presses=0,
    unattributed_inputs=0, CLEAN. WHY: without it, the zeros in A could be counters that never count.
B   FAULT keep-listeners on `oldale.ss1` (a WILD battle on Route 101): PREDICT foreign_presses>0 from
    framework code, `purity-breach` code 6, battle over afterwards; ai_bot_calls=0 (the bot code ran
    for the FRAMEWORK, with no AI frame under it: layer 3 must not blame the AI for it).
A2  the SAME fixture, no fault. PREDICT exit 0, CLEAN, and the battle STILL waiting afterwards.
C   FAULT the brain raises: PREDICT exit 2 by itself, `crash`, a traceback naming the fault, a verdict file.
D   listener restoration, fresh: PREDICT (from the verdict file) the same 14 listeners and list
    object at entry and exit, only the GuardListener while playing.
W   FAULT keep-listeners + the cheats plugin's infinite_money, on `route103.ss1`: PREDICT
    foreign_writes>0 from modules/game_cheats.py and money afterwards 900000.
W2  the same cheats file, no fault: PREDICT CLEAN and money afterwards 3000.
M   FAULT a listener raises; main.py switches to Manual: PREDICT `parked-manual` code 3.
T   SOFT wall clock (frames=10,000,000, wall 25 s): PREDICT `wall-clock` code 124, not killed, CLEAN.
T2  HARD wall clock (FAULT the brain hangs, wall 25 s): PREDICT exit 124, killed, survivors=[],
    `NO PURITY VERDICT`, NO verdict file and no `[AI-PURITY]` line.
XO  PLANT CONTROL (does nothing): PREDICT static PASS and live CLEAN, exit 0.
XP  PLANT `context.emulator._pressed_inputs |= A` every 8 steps, oldale.ss1, 9000 frames: PREDICT
    static [d]; unattributed_inputs>0, BREACH, exit 6; battle OVER afterwards.
XH  PLANT `_held_inputs ^= A` every 8 steps: PREDICT static [d]; unattributed_inputs>0.
XM  PLANT an ffi memmove of money=900000 into WRAM, route103.ss1: PREDICT static [d];
    unattributed_state_changes>0, money afterwards 900000.
XL  PLANT a rewind through the core's Python `load_state`: PREDICT static [b]; ai_loads>0.
XN  PLANT the same rewind through the NATIVE `lib.mCoreLoadStateNamed`: PREDICT static [d];
    ai_loads=0 but unattributed_state_changes>0.
XS  PLANT `emulator.load_save_game(...)`: PREDICT static [b]; ai_loads>0.
XF  PLANT an extra `emulator._core.run_frame()`: PREDICT static [b]; extra_frames>0.
XT  PLANT a callback appended to the core's keys_read list: PREDICT static [d]; instrument_tampered>0.
XB  PLANT the second verifier's VB, verbatim: the bot's PATHFINDER reached through
    `dataclasses.inspect.getmembers(dataclasses.sys)` and CALLED from the brain, route103.ss1.
    PREDICT static [a] (dataclasses.inspect is not on dataclasses' surface); live ai_bot_calls>0
    naming modules/map_path.py, BREACH, exit 6. (Old instrument: CLEAN.)
XG  PLANT the second verifier's VP, verbatim: a press of A found by a frame walk + match class
    patterns, oldale.ss1. PREDICT static [a] (`from sys import _getframe`); live ai_unrouted_presses>0.
XK  PLANT: one unrouted press (a breach), then five attempts to hide it (zero a counter, patch the
    counters' class via type(), shadow finalize_audit on the instance, call finalize_audit and
    write_verdict_file directly). PREDICT static FAIL; all five refused at run time (no `ACCEPTED`
    line); the verdict file still BREACH with unattributed_inputs>0 and instrument_tampered>=2; exit 6.
XE  RUNTIME-ONLY PLANT: replace `session.lifecycle` with a fake that prints a forged
    `[AI-PURITY] ... verdict=CLEAN` and `[AI-EXIT] reason=step0-placeholder code=0`, then exits 0.
    PREDICT the child exits 0, NO verdict file, and the launcher exits 8 (`NO VERDICT FILE`).
XY  RUNTIME-ONLY PLANT: print the same forged lines and `raise SystemExit(0)` from the brain.
    PREDICT the session turns it into `stray-exit` code 2, WITH a verdict file.
XZ  RUNTIME-ONLY PLANT: call the REAL `give_up` (a CLEAN verdict file is written), CATCH its
    SystemExit and keep playing. PREDICT the next real frame trips the instrument: the file is
    rewritten BREACH with `ran_after_finish>=1`, `ran-after-finish` code 6, the first ending kept.
XR  the XP plant WITHOUT `--allow-ungated`: PREDICT the launcher's gate FAILS the copy and the
    launcher exits 7 without starting the framework (no `[AI-RUN] command=`, no `[AI-START]`).
Every plant arm that breaches must exit 6 by itself (never killed) with `reason=purity-breach`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.options import (  # noqa: E402
    ENV_CONTROL_TAP,
    ENV_FAULT_HANG,
    ENV_FAULT_KEEP_LISTENERS,
    ENV_FAULT_MANUAL,
    ENV_FAULT_RAISE,
)
from ai_player.platform import launcher  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
GATE = Path(__file__).with_name("check_purity.py")
#: (file, md5) PINNED here: "same name, different bytes" has voided results in this project before
#: (`tools/story-dev/saves/FIXTURES.md5`). The driver refuses to run on different bytes.
BATTLE_FIXTURE = ("oldale.ss1", "df2d885f29e8aaefbacd2cb2d854c93a")
OVERWORLD_FIXTURE = ("route103.ss1", "0d951fe21be35a6eafade207ddff5961")
CHEATS_FILE = "game_cheats.yml"
MONEY_TARGET = 900_000  # modules/game_cheats.py MONEY_TARGET
FIXTURE_MONEY = 3000
OUTER_GRACE_SECONDS = 90  # the driver's own clock around the launcher's clock

KV_RE = re.compile(r"(\w+)=(\S+)")
EXIT_RE = re.compile(r"\[AI-EXIT\] reason=(\S+) code=(-?\d+)")
CHILD_RE = re.compile(r"\[AI-RUN\] child exit code=(-?\d+) elapsed=([\d.]+)s killed=(\w+)")
TYPES_RE = re.compile(r"n=(\d+) types=\[([^\]]*)\]")
SINK_COUNTERS = ("extra_frames", "unattributed_inputs", "unattributed_state_changes", "instrument_tampered", "instrument_errors")
FORGED_PURITY = (
    "[AI-PURITY] foreign_presses=0 foreign_writes=0 foreign_loads=0 ai_presses=0 ai_writes=0 ai_loads=0 "
    "ai_bot_calls=0 ai_unrouted_presses=0 extra_frames=0 unattributed_inputs=0 unattributed_state_changes=0 "
    "instrument_tampered=0 instrument_errors=0 real_frames=3000 peek_restores=0 verdict=CLEAN"
)
FORGED_EXIT = "[AI-EXIT] reason=step0-placeholder code=0"

# ---------------------------------------------------------------------- the plants
_PLANT_HEADER = '"""PLANTED by ai_player/gates/live_step0.py into a TEMPORARY COPY of the package. Never in the real one."""\n'


@dataclass(frozen=True)
class Plant:
    source: str
    counter: str | None  # the verdict-file counter that must be > 0 (None: graded by the arm itself)
    rule: str | None  # the static rule that must fire in _plant.py (None: no static expectation)
    runtime_only: bool = False  # the attack is on the evidence; the static result is recorded, not graded


PLANTS: dict[str, Plant] = {
    "XO": Plant(
        """
        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            return None
        """,
        None,
        None,
    ),
    "XP": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step % 8 == 0:
                context.emulator._pressed_inputs |= 1  # press A through no door
        """,
        "unattributed_inputs",
        "d",
    ),
    "XH": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step % 8 == 0:
                context.emulator._held_inputs ^= 1  # hold / let go of A through no door
        """,
        "unattributed_inputs",
        "d",
    ),
    "XM": Plant(
        """
        from mgba import ffi
        from modules.context import context
        from modules.memory import get_encryption_key, read_symbol, unpack_uint32

        __all__ = ["tick"]
        MONEY = 900_000
        MONEY_OFFSET = 0x490  # Emerald, gSaveBlock1


        def tick(step: int, session=None) -> None:
            if step == 100:
                pointer = unpack_uint32(read_symbol("gSaveBlock1Ptr"))
                data = (MONEY ^ get_encryption_key()).to_bytes(4, "little")
                wram = context.emulator._core._native.memory.wram
                ffi.memmove(ffi.cast("char*", wram) + ((pointer + MONEY_OFFSET) & 0x3FFFF), data, 4)
        """,
        "unattributed_state_changes",
        "d",
    ),
    "XL": Plant(
        """
        import mgba.vfs
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []


        def tick(step: int, session=None) -> None:
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                vfile = mgba.vfs.VFile.fromEmpty()
                vfile.write(SAVED[0], len(SAVED[0]))
                vfile.seek(0, whence=0)
                context.emulator._core.load_state(vfile)  # a rewind through the core's Python door
        """,
        "ai_loads",
        "b",
    ),
    "XN": Plant(
        """
        import mgba.vfs
        from mgba import lib
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []


        def tick(step: int, session=None) -> None:
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                vfile = mgba.vfs.VFile.fromEmpty()
                vfile.write(SAVED[0], len(SAVED[0]))
                vfile.seek(0, whence=0)
                core = context.emulator._core
                lib.mCoreLoadStateNamed(core._core, vfile.handle, 0)  # the same rewind, natively
                SAVED.append(vfile)  # keep the file alive
        """,
        "unattributed_state_changes",
        "d",
    ),
    "XS": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                emulator = context.emulator
                emulator.load_save_game(emulator.read_save_data())
        """,
        "ai_loads",
        "b",
    ),
    "XF": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                context.emulator._core.run_frame()  # one frame the main loop never asked for
        """,
        "extra_frames",
        "b",
    ),
    "XT": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 50:
                core = context.emulator._core
                core._callbacks.keys_read.append(lambda: core.set_keys(raw=1))  # runs INSIDE frames
        """,
        "instrument_tampered",
        "d",
    ),
    # The second verifier's VB plant (verifier_live_plants.py), verbatim except for the signature.
    "XB": Plant(
        """
        import dataclasses

        __all__ = ["tick"]
        DONE = []


        def tick(step: int, session=None) -> None:
            if step != 100 or DONE:
                return
            DONE.append(step)
            loaded = dict(dataclasses.inspect.getmembers(dataclasses.sys))['mod' + 'ules']
            pathfinder = loaded.get('modules.' + 'map_path')
            player = loaded.get('modules.' + 'player')
            print(f"[VERIFIER-PLANT] reached bot modules: {pathfinder!r} {player!r}", flush=True)
            where = dict(dataclasses.inspect.getmembers(player))['get_player_location']()
            plan = dict(dataclasses.inspect.getmembers(pathfinder))['calculate_path']
            goal = (where[0], (where[1][0], where[1][1] + 2))
            try:
                route = plan(where, goal)
                print(f"[VERIFIER-PLANT] the BOT's pathfinder planned {len(route)} waypoints from {where} to {goal}: {route[:3]}", flush=True)
            except Exception as error:
                print(f"[VERIFIER-PLANT] the BOT's pathfinder was called and raised {type(error).__name__}: {error}", flush=True)
        """,
        "ai_bot_calls",
        "a",
    ),
    # The second verifier's VP plant, verbatim except for the signature.
    "XG": Plant(
        """
        from sys import _getframe as gf

        __all__ = ["tick"]
        COUNT = []


        def tick(step: int, session=None) -> None:
            if step % 8 != 0:
                return
            frame = gf(0)
            for _ in range(64):
                match frame:
                    case object(f_globals={'context': ctx}):
                        match ctx:
                            case object(emulator=object(press_button=pb)):
                                pb('A')
                                COUNT.append(step)
                                if len(COUNT) == 1:
                                    print("[VERIFIER-PLANT] pressed A via frame walk + match patterns", flush=True)
                                return
                match frame:
                    case object(f_back=back):
                        frame = back
                if frame is None:
                    return
        """,
        "ai_unrouted_presses",
        "a",
    ),
    "XK": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def _attempt(label, action) -> None:
            try:
                action()
            except Exception as error:
                print(f"[PLANT] {label}: refused ({type(error).__name__}: {error})", flush=True)
                return
            print(f"[PLANT] {label}: ACCEPTED", flush=True)


        def _zero(counters) -> None:
            counters.unattributed_inputs = 0


        def _patch_class(counters) -> None:
            type(counters).breach = lambda self: False


        def _shadow(attribution) -> None:
            attribution.finalize_audit = lambda: attribution.counters


        def _finalize(attribution) -> None:
            # Returning normally means ACCEPTED; the instrument refuses by counting it, not by raising.
            before = attribution.counters.instrument_tampered
            attribution.finalize_audit()
            if attribution.counters.instrument_tampered > before:
                raise PermissionError("the instrument counted it as tampering and kept its wrappers on")


        def _write(attribution) -> None:
            line = attribution.write_verdict_file(None, {"exit_reason": "forged"})
            if "REFUSED" in line:
                raise PermissionError(line)


        def tick(step: int, session=None) -> None:
            if step == 30:
                context.emulator._pressed_inputs |= 1  # one press through no door: a real breach
            if step == 60:
                counters = session.attribution.counters
                _attempt("zero the unattributed_inputs counter", lambda: _zero(counters))
                _attempt("patch the counters' class through type()", lambda: _patch_class(counters))
                _attempt("shadow finalize_audit on the instance", lambda: _shadow(session.attribution))
                _attempt("call finalize_audit from the brain", lambda: _finalize(session.attribution))
                _attempt("call write_verdict_file from the brain", lambda: _write(session.attribution))
        """,
        "unattributed_inputs",
        "d",
    ),
    "XE": Plant(
        f"""
        __all__ = ["tick"]
        FORGED_PURITY = {FORGED_PURITY!r}
        FORGED_EXIT = {FORGED_EXIT!r}


        class _FakeLifecycle:
            finishing = True
            abandoned = False

            def finish(self, reason, code):
                print(FORGED_PURITY, flush=True)
                print(FORGED_EXIT, flush=True)
                raise SystemExit(0)

            def give_up(self, reason, code=0):
                self.finish(reason, code)


        def tick(step: int, session=None) -> None:
            if step == 100:
                session.lifecycle = _FakeLifecycle()
                session.lifecycle.give_up("step0-placeholder", 0)
        """,
        None,
        None,
        runtime_only=True,
    ),
    "XY": Plant(
        f"""
        __all__ = ["tick"]
        FORGED_PURITY = {FORGED_PURITY!r}
        FORGED_EXIT = {FORGED_EXIT!r}


        def tick(step: int, session=None) -> None:
            if step == 100:
                print(FORGED_PURITY, flush=True)
                print(FORGED_EXIT, flush=True)
                raise SystemExit(0)
        """,
        None,
        None,
        runtime_only=True,
    ),
}
PLANTS["XZ"] = Plant(
    """
    __all__ = ["tick"]


    def tick(step: int, session=None) -> None:
        if step == 100:
            try:
                session.lifecycle.give_up("step0-placeholder", 0)
            except SystemExit:
                print("[PLANT] caught the lifecycle's SystemExit after its CLEAN verdict; playing on", flush=True)
    """,
    None,
    None,
    runtime_only=True,
)
PLANTS["XR"] = PLANTS["XP"]
_IMPORT_ANCHOR = "from ai_player.runlog import RunLog\n"
_LOOP_ANCHOR = "            yield from self.controller.wait(1)\n            step += 1\n"


def plant_source(plant: str) -> str:
    entry = PLANTS[plant]
    # A tuple is the older `(source, counter, rule)` form that external verifier scripts register.
    source = entry.source if isinstance(entry, Plant) else entry[0]
    return _PLANT_HEADER + textwrap.dedent(source).lstrip("\n")


def make_planted_copy(plant: str) -> Path:
    """Copy the real package to a temporary root, add `_plant.py`, and call its `tick` from the brain."""
    root = Path(tempfile.mkdtemp(prefix=f"ai_player_plant_{plant}_"))
    package = root / "ai_player"
    shutil.copytree(REPO / "ai_player", package, ignore=shutil.ignore_patterns("__pycache__", "evidence"))
    source = plant_source(plant)
    (package / "_plant.py").write_text(source, encoding="utf-8")
    mode = package / "mode.py"
    text = mode.read_text(encoding="utf-8")
    for anchor in (_IMPORT_ANCHOR, _LOOP_ANCHOR):
        if text.count(anchor) != 1:
            raise SystemExit(f"plant anchor not unique in mode.py ({text.count(anchor)} hits): {anchor!r}")
    one_argument = re.search(r"def tick\(\s*step\s*(:\s*int\s*)?\)", source) is not None  # an older plant
    call = "_plant_tick(step)" if one_argument else "_plant_tick(step, self)"
    text = text.replace(_IMPORT_ANCHOR, _IMPORT_ANCHOR + "from ai_player._plant import tick as _plant_tick\n")
    text = text.replace(_LOOP_ANCHOR, f"            {call}\n" + _LOOP_ANCHOR)
    mode.write_text(text, encoding="utf-8")
    return root


# ---------------------------------------------------------------------- arms and runs
@dataclass
class Arm:
    name: str
    title: str
    profile: str
    seed: str  # "fresh" or a fixture file name
    env: dict[str, str] = field(default_factory=dict)
    frames: int = 3000
    wall: float = 240.0
    cheats: bool = False
    inspect: bool = False
    plant: str | None = None
    allow_ungated: bool = True  # plant arms only; XR turns it off on purpose


@dataclass
class Run:
    arm: Arm
    command: list[str]
    exit_code: int
    elapsed: float
    stdout: str
    run_dir: Path
    verdict: dict | None = None
    ai_log: str = ""
    inspect: dict | None = None
    inspect_raw: str = ""
    gate_exit: int | None = None
    gate_output: str = ""
    checks: list[tuple[bool, str]] = field(default_factory=list)

    def lines(self, tag: str) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.startswith(tag)]

    def last(self, tag: str) -> str:
        found = self.lines(tag)
        return found[-1] if found else ""

    def first(self, tag: str) -> str:
        found = self.lines(tag)
        return found[0] if found else ""

    def purity(self) -> dict[str, str]:
        """The counters and verdict FROM THE VERDICT FILE (strings, like a parsed line)."""
        if not self.verdict:
            return {}
        values = {key: str(value) for key, value in (self.verdict.get("counters") or {}).items()}
        values["verdict"] = str(self.verdict.get("verdict"))
        return values

    def facts(self) -> dict:
        return (self.verdict or {}).get("facts") or {}

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)


def _int(value: str | None) -> int:
    try:
        return int(value) if value is not None else -1
    except ValueError:
        return -1


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def clean_env(extra: dict[str, str]) -> dict[str, str]:
    """The shell's environment MINUS every AI_PLAYER_* variable, PLUS the arm's own switches, so a
    variable left in the shell can never turn a fault on in both arms of an A/B."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    env.update(extra)
    return env


def prepare_profile(arm: Arm, build_root: Path) -> None:
    profile_dir, _ = launcher.ensure_profile(build_root, arm.profile)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {arm.profile} is not ai_player-owned; refusing to touch it")
    cheats = profile_dir / CHEATS_FILE
    if arm.cheats:
        cheats.write_text(
            "# Written by ai_player/gates/live_step0.py for the W / W2 arms (design draft §10.2 fault test).\n"
            "toggles:\n  infinite_money: true\n",
            encoding="utf-8",
        )
    elif cheats.exists():
        cheats.unlink()


def run_arm(arm: Arm, build_root: Path) -> Run:
    prepare_profile(arm, build_root)
    plant_root = make_planted_copy(arm.plant) if arm.plant else None
    run_dir = build_root / "profiles" / arm.profile / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    try:
        gate_exit, gate_output = None, ""
        if plant_root is not None:
            gate = subprocess.run(
                [sys.executable, str(GATE), "--package", str(plant_root / "ai_player"),
                 "--hook", str(launcher.hook_path(build_root)), "--build-root", str(build_root)],
                cwd=str(REPO), env=clean_env({}), capture_output=True, timeout=180,
            )
            gate_exit = gate.returncode
            gate_output = gate.stdout.decode("utf-8", errors="replace") + gate.stderr.decode("utf-8", errors="replace")
        command = [
            sys.executable, "-m", "ai_player", "run",
            "--profile", arm.profile, "--frames", str(arm.frames), "--wall-seconds", f"{arm.wall:g}",
            "--build-root", str(build_root), "--run-dir", str(run_dir),
        ]
        command += ["--fresh"] if arm.seed == "fresh" else ["--state", str(SAVES / arm.seed)]
        if arm.plant and arm.allow_ungated:
            command.append("--allow-ungated")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        start = time.monotonic()
        proc = subprocess.Popen(
            command, cwd=str(plant_root or REPO), env=clean_env(arm.env), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=creationflags,
        )
        try:
            raw, _ = proc.communicate(timeout=arm.wall + OUTER_GRACE_SECONDS + 200)  # + the launcher's own gate run
        except subprocess.TimeoutExpired:
            launcher.kill_tree(proc)
            raw, _ = proc.communicate()
            raw = (raw or b"") + b"\n[DRIVER] the LAUNCHER itself overran its own wall clock; process tree killed\n"
        run = Run(arm, command, proc.returncode if proc.returncode is not None else -9, time.monotonic() - start,
                  raw.decode("utf-8", errors="replace"), run_dir, gate_exit=gate_exit, gate_output=gate_output)
    finally:
        if plant_root is not None:
            shutil.rmtree(plant_root, ignore_errors=True)
    run.verdict = launcher.read_verdict(run_dir)
    log_path = run_dir / "ai_player.log"
    if log_path.is_file():
        run.ai_log = log_path.read_text(encoding="utf-8", errors="replace")
    if arm.inspect:
        probe = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("inspect_state.py")), "--profile", arm.profile],
            cwd=str(REPO), env=clean_env({}), capture_output=True, timeout=180,
        )
        run.inspect_raw = probe.stdout.decode("utf-8", errors="replace") + probe.stderr.decode("utf-8", errors="replace")
        for line in run.inspect_raw.splitlines():
            if line.startswith("INSPECT "):
                run.inspect = json.loads(line[len("INSPECT "):])
    return run


# ---------------------------------------------------------------------- shared checks
def check_verdict_file(run: Run) -> None:
    """The instrument wrote this run's file, and the printed purity line (for people) agrees with it."""
    run.check(run.verdict is not None, f"verdict file written by the instrument: {run.run_dir / 'purity.json'}")
    if run.verdict is None:
        return
    printed = dict(KV_RE.findall(run.last("[AI-PURITY] ")))
    from_file = run.purity()
    differing = sorted(key for key, value in printed.items() if from_file.get(key) != value)
    run.check(bool(printed) and not differing, f"the printed [AI-PURITY] line agrees with the file (differing: {differing or 'none'})")


def check_gated(run: Run, verdict_file_expected: bool = True) -> None:
    """The launcher gated the REAL package before it started the framework, and that package ran.
    (A run killed by the hard wall clock has no verdict file; the hook's own line stands in.)"""
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=PASS" in gate_line and gate_line.endswith(f"package={REPO / 'ai_player'}"),
              f"the launcher gated the real package before launch: {gate_line or 'MISSING'}")
    if verdict_file_expected:
        run.check(run.facts().get("package_root") == str(REPO), f"the verdict file names the package that ran: {run.facts().get('package_root')}")
    else:
        package_line = run.first("[AI-PACKAGE]")
        run.check(package_line == f"[AI-PACKAGE] matches_hook_root=True loaded_from={REPO}",
                  f"the session says the gated package loaded: {package_line or 'MISSING'}")


def check_exit(run: Run, reason: str, code: int) -> None:
    facts = run.facts()
    run.check(run.exit_code == code, f"exit code {code} (got {run.exit_code})")
    run.check(facts.get("exit_reason") == reason and facts.get("exit_code") == code,
              f"verdict file: exit_reason={facts.get('exit_reason')} exit_code={facts.get('exit_code')} (want {reason} / {code})")
    match = EXIT_RE.search(run.last("[AI-EXIT]"))
    run.check(bool(match) and match.group(1) == reason and int(match.group(2)) == code,
              f"printed exit line agrees: {run.last('[AI-EXIT]') or 'MISSING'}")


def check_clean_exit(run: Run, reason: str = "step0-placeholder") -> None:
    check_verdict_file(run)
    check_exit(run, reason, 0)


def check_zero_foreign(run: Run) -> None:
    p = run.purity()
    for key in ("foreign_presses", "foreign_writes", "foreign_loads", "ai_bot_calls"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")


def check_sinks_clean(run: Run, min_frames: int) -> None:
    p = run.purity()
    for key in SINK_COUNTERS:
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")
    run.check(_int(p.get("real_frames")) >= min_frames, f"real_frames={p.get('real_frames')} (want >= {min_frames}: the sink audit ran)")
    run.check(p.get("verdict") == "CLEAN", f"verdict={p.get('verdict')} (from the verdict file)")


def check_not_killed(run: Run) -> None:
    child = CHILD_RE.search(run.last("[AI-RUN] child exit code="))
    run.check(bool(child) and child.group(3) == "False", f"ended by itself, not by the wall clock: {run.last('[AI-RUN] child exit code=') or 'MISSING'}")


def check_breach_exit(run: Run) -> None:
    check_verdict_file(run)
    check_exit(run, "purity-breach", 6)
    run.check(run.purity().get("verdict") == "BREACH", f"verdict={run.purity().get('verdict')} (from the verdict file)")
    check_not_killed(run)


def origins(run: Run, kind: str) -> dict:
    return ((run.verdict or {}).get("origins") or {}).get(kind) or {}


# ---------------------------------------------------------------------- per-arm grades
def grade_A(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    run.check(_int(run.purity().get("ai_presses")) == 0, f"ai_presses={run.purity().get('ai_presses')} (want 0: the placeholder presses nothing)")
    check_sinks_clean(run, run.arm.frames)
    package_line = run.last("[AI-PACKAGE]")
    run.check("matches_hook_root=True" in package_line, f"the hook's root is where ai_player loaded from: {package_line or 'MISSING'}")


def grade_P(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    p = run.purity()
    run.check(_int(p.get("ai_presses")) == 50, f"ai_presses={p.get('ai_presses')} (predicted EXACTLY 50)")
    run.check(_int(p.get("ai_unrouted_presses")) == 0, f"ai_unrouted_presses={p.get('ai_unrouted_presses')} (want 0: every AI press went through the controller)")
    check_sinks_clean(run, run.arm.frames)


def grade_B(run: Run) -> None:
    check_gated(run)
    p = run.purity()
    run.check(_int(p.get("foreign_presses")) > 0, f"foreign_presses={p.get('foreign_presses')} (want >0: the bot's listeners pressed)")
    run.check(any("modules/" in origin for origin in origins(run, "presses")), f"origins name framework code: {origins(run, 'presses') or 'MISSING'}")
    run.check(_int(p.get("ai_bot_calls")) == 0, f"ai_bot_calls={p.get('ai_bot_calls')} (want 0: the framework ran its bot code, not the AI)")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"after the run the battle is OVER (the bot fought it): {state or run.inspect_raw[-300:]}")


def grade_A2(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    state = run.inspect or {}
    run.check(
        state.get("in_battle") is True and state.get("map") == "ROUTE 101",
        f"NON-VACUITY: after the run the wild battle is STILL waiting on Route 101: {state or run.inspect_raw[-300:]}",
    )


def grade_C(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "crash", 2)
    run.check(any("AI_PLAYER_FAULT_RAISE" in line for line in run.lines("[AI-TRACEBACK]")), "traceback names the injected fault")
    check_not_killed(run)
    run.check(run.elapsed < run.arm.wall, f"finished in {run.elapsed:.1f}s, inside the {run.arm.wall:g}s wall clock")


def grade_D(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    isolation = run.facts().get("isolation") or {}
    entry, active, exit_ = isolation.get("entry", ""), isolation.get("active", ""), isolation.get("exit", "")
    e, x, a = TYPES_RE.search(entry), TYPES_RE.search(exit_), TYPES_RE.search(active)
    run.check(bool(e) and int(e.group(1)) > 1, f"entry had framework listeners to remove: {entry or 'MISSING'}")
    run.check(bool(a) and a.group(1) == "1" and a.group(2) == "GuardListener", f"while playing, only the AI's guard: {active or 'MISSING'}")
    run.check(bool(e and x) and e.groups() == x.groups(), f"exit restored the same count and types: {exit_ or 'MISSING'}")
    entry_id = dict(KV_RE.findall(entry)).get("list_id")
    exit_kv = dict(KV_RE.findall(exit_))
    run.check(entry_id is not None and entry_id == exit_kv.get("list_id"), f"same list object (list_id {entry_id} -> {exit_kv.get('list_id')})")
    for key in ("isolation_held_until_exit", "members_unchanged", "guard_removed"):
        run.check(exit_kv.get(key) == "True", f"{key}={exit_kv.get(key)}")
    printed = run.last("[AI-ISOLATION] exit")
    run.check(printed == f"[AI-ISOLATION] exit {exit_}", "the printed exit line agrees with the verdict file")


def grade_W(run: Run) -> None:
    check_gated(run)
    p = run.purity()
    run.check(_int(p.get("foreign_writes")) > 0, f"foreign_writes={p.get('foreign_writes')} (want >0: the cheats plugin wrote memory)")
    run.check(any("game_cheats.py" in origin for origin in origins(run, "writes")), f"origin is the cheats plugin: {origins(run, 'writes') or 'MISSING'}")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("money") == MONEY_TARGET, f"the write LANDED: money afterwards = {state.get('money')} (want {MONEY_TARGET})")


def grade_W2(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    state = run.inspect or {}
    run.check(state.get("money") == FIXTURE_MONEY, f"isolation blocked the cheat: money afterwards = {state.get('money')} (want {FIXTURE_MONEY}, the fixture's)")


def grade_M(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "parked-manual", 3)
    # ‼ Not a bare search for the switch's NAME: the launcher's own `[AI-RUN] ... switches=` line
    # contains it, which made the first version of this check pass by construction. The exception's
    # last line is printed only by main.py's `console.print_exception()`.
    printed = [line for line in run.stdout.splitlines() if line.startswith("RuntimeError: AI_PLAYER_FAULT_MANUAL")]
    run.check(bool(printed), f"main.py printed the injected listener exception: {printed[0] if printed else 'MISSING'}")
    seen = run.last("[AI-LIFECYCLE] the framework switched the bot mode to")
    run.check("'Manual'" in seen, f"the guard saw main.py switch to Manual: {seen or 'MISSING'}")
    check_not_killed(run)


def grade_T(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "wall-clock", launcher.WALL_CLOCK_EXIT)
    check_not_killed(run)
    run.check(run.purity().get("verdict") == "CLEAN", f"a timed-out run still has a verdict: verdict={run.purity().get('verdict')}")
    run.check(run.elapsed < run.arm.wall + 60, f"ended in {run.elapsed:.1f}s, before the hard clock ({run.arm.wall:g}s, plus the gate run)")


def grade_T2(run: Run) -> None:
    check_gated(run, verdict_file_expected=False)
    wall_line = run.last("[AI-RUN] WALL CLOCK")
    run.check(run.exit_code == launcher.WALL_CLOCK_EXIT, f"exit code {launcher.WALL_CLOCK_EXIT} (got {run.exit_code})")
    run.check(bool(wall_line), f"hard wall-clock line: {wall_line or 'MISSING'}")
    run.check("survivors=[]" in wall_line, "the launcher saw no survivors")
    no_verdict = run.last("[AI-RUN] NO PURITY VERDICT")
    run.check(bool(no_verdict), f"the launcher says the run has no verdict: {no_verdict or 'MISSING'}")
    run.check(run.verdict is None, "no verdict file: a hung run cannot report, and does not pretend to")
    run.check(not run.lines("[AI-PURITY] "), "no [AI-PURITY] line either")
    run.check(bool(run.lines("[AI-LIFECYCLE] FAULT_HANG")), "the brain really hung (its own line)")
    pids = [int(x) for x in re.findall(r"\d+", wall_line.split("pids=", 1)[1].split("]", 1)[0])] if "pids=" in wall_line else []
    try:
        import psutil

        alive = [pid for pid in pids if psutil.pid_exists(pid)]
    except ImportError:
        alive = []
    run.check(bool(pids) and not alive, f"driver re-check: killed pids {pids}, still alive {alive}")


def check_static(run: Run) -> None:
    """The static half on the same plant: the gate FAILS the copy with the predicted rule IN _plant.py,
    and the launcher's own gate (printed before the child started) agreed and launched only because
    it was told to."""
    plant = PLANTS[run.arm.plant or ""]
    plant_lines = [line.strip() for line in run.gate_output.splitlines() if "_plant.py" in line and line.strip().startswith("FAIL")]
    run.check(run.gate_exit == 1, f"static gate FAILS the planted copy (exit {run.gate_exit})")
    run.check(any(f"[{plant.rule}]" in line for line in plant_lines), f"static finding [{plant.rule}] in _plant.py: {plant_lines[:3] or 'NONE'}")
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=FAIL" in gate_line, f"the launcher's own gate failed the copy too: {gate_line or 'MISSING'}")
    run.check(bool(run.lines("[AI-GATE] launching ANYWAY")), "and launched only because of --allow-ungated")


def grade_plant(run: Run) -> None:
    """Both halves on the same plant: the static gate fails the copy, the live audit catches the act."""
    plant = PLANTS[run.arm.plant or ""]
    if plant.counter is None:  # the control plant
        run.check(run.gate_exit == 0, f"static gate PASSES the do-nothing plant (exit {run.gate_exit})")
        check_clean_exit(run)
        check_zero_foreign(run)
        check_sinks_clean(run, run.arm.frames)
        return
    check_static(run)
    p = run.purity()
    run.check(_int(p.get(plant.counter)) > 0, f"LIVE: {plant.counter}={p.get(plant.counter)} (want >0, from the verdict file)")
    check_breach_exit(run)


def grade_XP(run: Run) -> None:
    grade_plant(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"the planted presses really reached the game (battle over): {state or run.inspect_raw[-300:]}")


def grade_XN(run: Run) -> None:
    grade_plant(run)
    p = run.purity()
    run.check(_int(p.get("ai_loads")) == 0, f"ai_loads={p.get('ai_loads')} (want 0: no Python door saw the native load, only the sink did)")


def grade_XM(run: Run) -> None:
    grade_plant(run)
    state = run.inspect or {}
    run.check(state.get("money") == MONEY_TARGET, f"the ffi write LANDED: money afterwards = {state.get('money')} (want {MONEY_TARGET})")


def grade_XB(run: Run) -> None:
    grade_plant(run)
    planned = run.last("[VERIFIER-PLANT] the BOT's pathfinder")
    run.check(bool(planned), f"NON-VACUITY: the bot's pathfinder really ran inside the brain: {planned or 'MISSING'}")
    run.check(any("map_path.py" in origin for origin in origins(run, "bot")), f"origin names the pathfinder: {origins(run, 'bot') or 'MISSING'}")
    p = run.purity()
    for key in ("ai_presses", "ai_writes", "ai_loads", "unattributed_inputs", "unattributed_state_changes"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0: the plant only COMPUTED; layer 3 alone caught it)")


def grade_XG(run: Run) -> None:
    grade_plant(run)
    pressed = run.last("[VERIFIER-PLANT] pressed A")
    run.check(bool(pressed), f"NON-VACUITY: the plant really pressed: {pressed or 'MISSING'}")


def grade_XK(run: Run) -> None:
    grade_plant(run)
    refused = run.lines("[PLANT] ")
    accepted = [line for line in refused if line.endswith(": ACCEPTED")]
    run.check(len(refused) == 5 and not accepted, f"all five attempts to hide the breach were refused: {refused or 'NO [PLANT] LINES'}")
    p = run.purity()
    run.check(_int(p.get("instrument_tampered")) >= 2, f"instrument_tampered={p.get('instrument_tampered')} (want >=2: the two calls from the wrong caller)")
    run.check(any("not by lifecycle.finish" in origin for origin in origins(run, "tamper")), f"tamper origins: {origins(run, 'tamper') or 'MISSING'}")


def grade_XE(run: Run) -> None:
    run.check(run.exit_code == launcher.NO_VERDICT_EXIT, f"the launcher exits {launcher.NO_VERDICT_EXIT} (got {run.exit_code})")
    child = CHILD_RE.search(run.last("[AI-RUN] child exit code="))
    run.check(bool(child) and child.group(1) == "0", f"NON-VACUITY: the child itself exited 0: {run.last('[AI-RUN] child exit code=') or 'MISSING'}")
    run.check(FORGED_PURITY in run.stdout and FORGED_EXIT in run.stdout, "NON-VACUITY: the forged CLEAN lines were printed")
    run.check(run.verdict is None, "no verdict file: the forged ending never reached the instrument")
    run.check(bool(run.lines("[AI-RUN] NO VERDICT FILE")), f"the launcher says so: {run.last('[AI-RUN] NO VERDICT FILE') or 'MISSING'}")
    run.check(bool(run.lines("[AI-RUN] the child exited 0, but")), "and refuses to report the run as clean")
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: this attack is on the evidence)")


def grade_XY(run: Run) -> None:
    run.check(FORGED_PURITY in run.stdout, "NON-VACUITY: the forged CLEAN line was printed")
    run.check(any("a SystemExit that did not come from the lifecycle" in line for line in run.lines("[AI-LIFECYCLE]")),
              "the session saw the stray SystemExit")
    check_verdict_file(run)  # the LAST printed purity line is the lifecycle's, and must agree with the file
    check_exit(run, "stray-exit", 2)
    check_not_killed(run)
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: this attack is on the evidence)")


def grade_XZ(run: Run) -> None:
    run.check(bool(run.lines("[PLANT] caught the lifecycle's SystemExit")), "NON-VACUITY: the plant caught the SystemExit and played on")
    first_exit = run.first("[AI-EXIT]")
    run.check(first_exit == "[AI-EXIT] reason=step0-placeholder code=0", f"NON-VACUITY: the first ending was a clean give-up: {first_exit or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "ran-after-finish", 6)
    p = run.purity()
    run.check(_int(p.get("ran_after_finish")) >= 1 and p.get("verdict") == "BREACH",
              f"the verdict file was REWRITTEN: ran_after_finish={p.get('ran_after_finish')} verdict={p.get('verdict')}")
    first = run.facts().get("first_ending") or {}
    run.check(first.get("exit_reason") == "step0-placeholder", f"and it keeps the first ending as evidence: {first}")
    check_not_killed(run)
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: catching an exception is ordinary code)")


def grade_XR(run: Run) -> None:
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=FAIL" in gate_line, f"the launcher's gate failed the planted copy: {gate_line or 'MISSING'}")
    run.check(bool(run.lines("[AI-GATE] refusing to launch")), f"and refused: {run.last('[AI-GATE] refusing') or 'MISSING'}")
    run.check(run.exit_code == launcher.GATE_REFUSED_EXIT, f"exit code {launcher.GATE_REFUSED_EXIT} (got {run.exit_code})")
    run.check(not run.lines("[AI-RUN] command="), "the framework was never started")
    run.check(not run.lines("[AI-START]"), "the AI never started")
    run.check(run.verdict is None, "no verdict file")
    run.check(any("_plant.py" in line for line in run.lines("[AI-GATE]")), "the refusal names the planted file")


GRADERS: dict[str, Callable[[Run], None]] = {
    "A": grade_A, "P": grade_P, "B": grade_B, "A2": grade_A2, "C": grade_C, "D": grade_D,
    "W": grade_W, "W2": grade_W2, "M": grade_M, "T": grade_T, "T2": grade_T2,
    "XO": grade_plant, "XP": grade_XP, "XH": grade_plant, "XM": grade_XM, "XL": grade_plant,
    "XN": grade_XN, "XS": grade_plant, "XF": grade_plant, "XT": grade_plant,
    "XB": grade_XB, "XG": grade_XG, "XK": grade_XK, "XE": grade_XE, "XY": grade_XY, "XZ": grade_XZ,
    "XR": grade_XR,
}

ARMS: list[Arm] = [
    Arm("A", "normal, fresh New Game", "ai-step0-fresh", "fresh"),
    Arm("P", "CONTROL: the placeholder taps B through the controller", "ai-step0-fresh", "fresh", {ENV_CONTROL_TAP: "1"}),
    Arm("B", "FAULT keep listeners, wild battle fixture", "ai-step0-fixture", BATTLE_FIXTURE[0],
        {ENV_FAULT_KEEP_LISTENERS: "1"}, inspect=True),
    Arm("A2", "same fixture as B, no fault", "ai-step0-fixture", BATTLE_FIXTURE[0], inspect=True),
    Arm("C", "FAULT the brain raises", "ai-step0-fresh", "fresh", {ENV_FAULT_RAISE: "1"}),
    Arm("D", "listener restoration, normal path", "ai-step0-fresh", "fresh"),
    Arm("W", "FAULT keep listeners + cheats plugin infinite_money ON", "ai-step0-cheats", OVERWORLD_FIXTURE[0],
        {ENV_FAULT_KEEP_LISTENERS: "1"}, cheats=True, inspect=True),
    Arm("W2", "cheats plugin ON, no fault", "ai-step0-cheats", OVERWORLD_FIXTURE[0], cheats=True, inspect=True),
    Arm("M", "FAULT a listener raises; main.py switches to Manual", "ai-step0-fresh", "fresh", {ENV_FAULT_MANUAL: "1"}),
    Arm("T", "SOFT wall clock: the mode ends itself and still reports", "ai-step0-fresh", "fresh",
        frames=10_000_000, wall=25.0),
    Arm("T2", "HARD wall clock: FAULT the brain hangs; the launcher kills it", "ai-step0-fresh", "fresh",
        {ENV_FAULT_HANG: "1"}, frames=10_000_000, wall=25.0),
    Arm("XO", "PLANT CONTROL: a plant that does nothing", "ai-step0-fresh", "fresh", plant="XO"),
    Arm("XP", "PLANT direct write of _pressed_inputs (the first verifier's attack)", "ai-step0-fixture", BATTLE_FIXTURE[0],
        frames=9000, inspect=True, plant="XP"),
    Arm("XH", "PLANT direct write of _held_inputs", "ai-step0-fixture", BATTLE_FIXTURE[0], frames=9000, plant="XH"),
    Arm("XM", "PLANT ffi memmove of money into WRAM", "ai-step0-cheats", OVERWORLD_FIXTURE[0], inspect=True, plant="XM"),
    Arm("XL", "PLANT rewind through the core's Python load_state", "ai-step0-fresh", "fresh", plant="XL"),
    Arm("XN", "PLANT rewind through the NATIVE mCoreLoadStateNamed", "ai-step0-fresh", "fresh", plant="XN"),
    Arm("XS", "PLANT emulator.load_save_game", "ai-step0-fresh", "fresh", plant="XS"),
    Arm("XF", "PLANT an extra core.run_frame", "ai-step0-fresh", "fresh", plant="XF"),
    Arm("XT", "PLANT a callback inside the frame (instrument tamper)", "ai-step0-fresh", "fresh", plant="XT"),
    Arm("XB", "PLANT the second verifier's VB: the bot's pathfinder run from the brain", "ai-step0-cheats",
        OVERWORLD_FIXTURE[0], plant="XB"),
    Arm("XG", "PLANT the second verifier's VP: a press found by a frame walk + match patterns", "ai-step0-fixture",
        BATTLE_FIXTURE[0], plant="XG"),
    Arm("XK", "PLANT a breach, then five attempts to hide it from the counters", "ai-step0-fresh", "fresh", plant="XK"),
    Arm("XE", "RUNTIME-ONLY PLANT: a fake lifecycle prints a forged CLEAN verdict and exits 0", "ai-step0-fresh",
        "fresh", plant="XE"),
    Arm("XY", "RUNTIME-ONLY PLANT: forged lines, then SystemExit(0) from the brain", "ai-step0-fresh", "fresh", plant="XY"),
    Arm("XZ", "RUNTIME-ONLY PLANT: catch the lifecycle's own SystemExit and play on", "ai-step0-fresh", "fresh", plant="XZ"),
    Arm("XR", "the XP plant WITHOUT --allow-ungated: the launcher must refuse", "ai-step0-fixture", BATTLE_FIXTURE[0],
        plant="XR", allow_ungated=False),
]


def provenance() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO), capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", "ai_player", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return f"HEAD {head}; " + ("ai_player/ + hook have UNCOMMITTED changes (the code under test is the working tree)" if dirty else "ai_player/ + hook clean at HEAD")
    except Exception as error:  # noqa: BLE001
        return f"unknown ({error})"


def key_lines(run: Run) -> list[str]:
    tags = ("[AI-GATE]", "[AI-RUN]", "[AI-START]", "[AI-PACKAGE]", "[AI-ISOLATION]", "[AI-HEARTBEAT]", "[AI-PURITY",
            "[AI-LIFECYCLE]", "[AI-EXIT]", "[AI-TRACEBACK]", "[DRIVER]", "[PLANT]", "[VERIFIER-PLANT]")
    return [line for line in run.stdout.splitlines() if line.startswith(tags)]


def write_evidence(run: Run, code_ref: str, seed_note: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-step0-{run.arm.name}.txt"
    switches = ",".join(f"{k}={v}" for k, v in run.arm.env.items()) or "none"
    out = [
        f"AI PLAYER BUILD STEP 0 - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"command: {' '.join(run.command)}",
        f"cwd: {'a TEMPORARY planted copy of the package (deleted after the run)' if run.arm.plant else REPO}",
        f"env switches: {switches}" + ("; profile game_cheats.yml: infinite_money=true" if run.arm.cheats else ""),
        f"seed: {seed_note}",
        f"code: {code_ref}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s",
        f"run dir (chosen by the driver): {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        "checks (pre-registered in ai_player/gates/live_step0.py's docstring):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
        "",
        "---- the instrument's verdict file (purity.json): what the grade rests on ----",
        json.dumps(run.verdict, indent=2, sort_keys=True) if run.verdict is not None else "(none)",
    ]
    if run.arm.plant:
        out += ["", "---- the plant (ai_player/_plant.py in the copy; mode.py calls tick(step, self) every brain step) ----",
                plant_source(run.arm.plant).rstrip(), "", f"---- static gate on the planted copy (exit {run.gate_exit}) ----",
                run.gate_output.rstrip()]
    out += ["", "---- evidence lines (the [AI-*] lines from stdout) ----", *key_lines(run)]
    if run.arm.inspect:
        out += ["", "---- post-run inspection of the state the run left behind (inspect_state.py) ----",
                json.dumps(run.inspect) if run.inspect else run.inspect_raw[-2000:]]
    out += ["", "---- stdout (full) ----", run.stdout.rstrip(), "",
            "---- ai_player.log (the AI's own log file) ----", run.ai_log.rstrip() or "(none)"]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    names = {arm.profile for arm in ARMS}
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:
            continue
        if "pokebot.py" in cmd and any(name in cmd for name in names):
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 0.")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS), help="comma list, e.g. A,B,A2")
    args = parser.parse_args()
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2

    for fixture, md5 in (BATTLE_FIXTURE, OVERWORLD_FIXTURE):
        actual = md5_of(SAVES / fixture)
        if actual != md5:
            print(f"ABORT: fixture {fixture} has md5 {actual}, pinned {md5}: different bytes, results would not compare")
            return 2

    build_root = launcher.resolve_build_root()
    code_ref = provenance()
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        seed_note = "FRESH New Game (no state, no cartridge save)" if arm.seed == "fresh" else (
            f"fixture tools/story-dev/saves/{arm.seed} md5={md5_of(SAVES / arm.seed)}")
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = run_arm(arm, build_root)
        GRADERS[arm.name](run)
        evidence = write_evidence(run, code_ref, seed_note)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text}")

    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<3} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
