"""The AI player's mode logic: what the hook in `sandbox-pokebot/plugins/custom_modes/` delegates to.

BUILD STEP 0 (design draft §6, "purity scaffolding"). The brain is a PLACEHOLDER that presses
nothing, lets `--frames` frames pass, and gives up with reason `step0-placeholder`. What step 0 proves
is everything AROUND the brain, so that every later step is built on a measured boundary:

  * isolation   the framework's listeners are removed on entry and restored on exit (§10.1-2);
  * attribution every press, memory write, state load and frame is counted by origin, and the
                emulator's sinks are audited so an action through no counted door is still caught
                (§2.2, §10.2);
  * lifecycle   a give-up, a crash or running out of time ends the process and never parks it in
                Manual (§10.3).

WHEN THINGS HAPPEN, and why that order:
  `start_session()` runs from the hook's CONSTRUCTOR. `modules/main.py` builds the mode instance,
  then calls every listener, then steps the mode, all in the same frame. Isolating in the
  constructor means no framework listener ever runs while the AI is in charge, not even once:
  on a fixture saved mid-battle, one listener pass would already have pushed the bot's battle
  handler on top of the AI.

WHICH PACKAGE RUNS: the hook passes the folder it put FIRST on `sys.path`; the session checks that
this very file was loaded from there and logs `[AI-PACKAGE]` (the path also goes into the verdict
file). The launcher gates exactly that folder before it starts the framework, so "the gate passed"
and "this code ran" are tied together by evidence, not assumed.

Fault and control switches are read here, from the environment (`ai_player/options.py`), so the
fault arms exercise the production path. None of them is set on the happy path.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from pathlib import Path

from ai_player import MODE_NAME
from ai_player.options import VERDICT_FILE_NAME, RunOptions
from ai_player.platform.attribution import Attribution
from ai_player.platform.controller import Controller
from ai_player.platform.isolation import GuardListener, ListenerIsolation
from ai_player.platform.lifecycle import (
    EXIT_BRAIN_RETURNED,
    EXIT_CRASH,
    EXIT_FRAME_BUDGET,
    EXIT_OK,
    EXIT_PARKED,
    EXIT_WALL_CLOCK,
    Lifecycle,
    current_bot_mode,
)
from ai_player.runlog import RunLog

#: The folder that CONTAINS this `ai_player/` package: what the hook must have put on `sys.path`.
LOADED_FROM = Path(__file__).resolve().parents[1]

__all__ = ["Session", "start_session"]

#: How many frames past `--frames` the guard allows before it ends a starved run itself.
FRAME_BUDGET_GRACE = 600
#: How often the guard prints the running counters, in frames.
HEARTBEAT_EVERY_FRAMES = 1000
#: FAULT `AI_PLAYER_FAULT_RAISE`: the brain raises on this step.
FAULT_RAISE_AT_STEP = 30
#: FAULT `AI_PLAYER_FAULT_MANUAL`: the planted listener raises on this frame.
FAULT_MANUAL_AT_FRAME = 30
#: FAULT `AI_PLAYER_FAULT_HANG`: the brain blocks on this step, for at most this many seconds (a
#: bound, so even a launcher that failed to kill it could not leave it running forever).
FAULT_HANG_AT_STEP = 30
FAULT_HANG_MAX_SECONDS = 300
#: CONTROL `AI_PLAYER_CONTROL_TAP`: the placeholder taps B once every this many steps.
CONTROL_TAP_EVERY_STEPS = 60

_active_session: "Session | None" = None


class _FaultRaisingListener:
    """FAULT `AI_PLAYER_FAULT_MANUAL` only. Raises once inside the framework's listener loop, which is
    exactly what any buggy listener would do; `main.py` then prints the error and switches to Manual.
    Duck-typed (no base class) because the framework only ever calls `handle_frame` on a listener."""

    def __init__(self) -> None:
        self._frames = 0
        self._fired = False

    def handle_frame(self, bot_mode, frame) -> None:
        self._frames += 1
        if not self._fired and self._frames >= FAULT_MANUAL_AT_FRAME:
            self._fired = True
            raise RuntimeError("AI_PLAYER_FAULT_MANUAL: injected listener exception (main.py will switch to Manual)")


class Session:
    """One AI run inside one framework process."""

    def __init__(self, options: RunOptions, expected_root: str | None) -> None:
        self.options = options
        self.expected_root = expected_root
        self.log = RunLog(options.run_dir)
        self.controller = Controller()
        self.attribution = Attribution()
        extra = [_FaultRaisingListener()] if options.fault_manual else []
        self.isolation = ListenerIsolation(
            GuardListener(self._on_frame),
            keep_foreign=options.fault_keep_listeners,
            extra=extra,
            on_tamper=self.attribution.note_tamper,
        )
        verdict_path = options.run_dir / VERDICT_FILE_NAME if options.run_dir is not None else None
        self.lifecycle = Lifecycle(self.log, self.attribution, self.isolation, verdict_path, LOADED_FROM)
        self.frames_seen = 0
        self.frame_cap = options.frames + FRAME_BUDGET_GRACE

    # ------------------------------------------------------------------ start
    def start(self) -> None:
        self.log.line(f"[AI-START] mode={MODE_NAME!r} {self.options.describe()}")
        matches = self.expected_root is None or Path(self.expected_root).resolve() == LOADED_FROM
        self.log.line(f"[AI-PACKAGE] matches_hook_root={matches} loaded_from={LOADED_FROM}")
        if not matches:
            raise RuntimeError(
                f"the hook put {self.expected_root} first on sys.path, but ai_player was loaded from "
                f"{LOADED_FROM}: the code running is not the code that was gated"
            )
        self.attribution.install()
        entry, active = self.isolation.apply()
        self.log.line(f"[AI-ISOLATION] entry {entry}")
        self.log.line(
            f"[AI-ISOLATION] active {active} keep_foreign={self.options.fault_keep_listeners}"
        )

    # ------------------------------------------------------------------ the guard (every frame)
    def _on_frame(self) -> None:
        """Runs once per frame from the AI's own listener, even while the AI's generator is starved."""
        self.frames_seen += 1
        if self.lifecycle.abandoned:
            self.lifecycle.finish("abandoned", EXIT_PARKED)
        current_mode = current_bot_mode()
        if current_mode != MODE_NAME:
            self.log.line(f"[AI-LIFECYCLE] the framework switched the bot mode to {current_mode!r}")
            self.lifecycle.finish("parked-manual", EXIT_PARKED)
        if self.frames_seen > self.frame_cap:
            self.log.line(
                f"[AI-LIFECYCLE] {self.frames_seen} frames passed but the AI advanced only "
                f"{self.controller.frames_advanced}; budget {self.frame_cap}"
            )
            self.lifecycle.finish("frame-budget", EXIT_FRAME_BUDGET)
        if self.options.wall_deadline is not None and time.time() >= self.options.wall_deadline:
            self.log.line(
                f"[AI-LIFECYCLE] the launcher's soft wall-clock deadline passed after {self.frames_seen} frames; "
                f"ending the run while the verdict can still be printed"
            )
            self.lifecycle.finish("wall-clock", EXIT_WALL_CLOCK)
        if self.frames_seen % HEARTBEAT_EVERY_FRAMES == 0:
            c = self.attribution.counters
            self.log.line(
                f"[AI-HEARTBEAT] frames={self.frames_seen} ai_steps={self.controller.frames_advanced} "
                f"foreign_presses={c.foreign_presses} foreign_writes={c.foreign_writes} "
                f"foreign_loads={c.foreign_loads} ai_presses={c.ai_presses} "
                f"unattributed_inputs={c.unattributed_inputs} "
                f"unattributed_state_changes={c.unattributed_state_changes}"
            )

    # ------------------------------------------------------------------ the generator main.py drives
    def run(self) -> Generator[None, None, None]:
        try:
            for _ in self._brain():
                note = self.isolation.enforce()
                if note:
                    self.log.line(note)
                yield
            self.lifecycle.finish("brain-returned", EXIT_BRAIN_RETURNED)
        except SystemExit:
            if not self.lifecycle.finishing:
                # Not the lifecycle's own exit: the brain called sys.exit (or raised SystemExit). Left
                # alone it would end the process with no verdict file; make it a recorded ending.
                self.log.line("[AI-LIFECYCLE] a SystemExit that did not come from the lifecycle")
                self.lifecycle.finish("stray-exit", EXIT_CRASH)
            raise
        except GeneratorExit:
            self.lifecycle.note_abandoned()
            raise
        except BaseException as error:  # noqa: BLE001 - every ending must be an exit, see lifecycle.py
            self.lifecycle.crash(error, "the brain")

    # ------------------------------------------------------------------ the brain (step 0 placeholder)
    def _brain(self) -> Generator[None, None, None]:
        """STEP 0 PLACEHOLDER. Presses nothing; waits `frames` steps; gives up.

        Later steps replace this with the real brain (eyes, world model, navigator, battle decider,
        menus, goals, personality, coach). The contract stays: it yields once per frame, every press
        goes through `self.controller`, and it ends ONLY through `self.lifecycle.give_up`.
        """
        options = self.options
        step = 0
        while step < options.frames:
            if options.fault_raise and step >= FAULT_RAISE_AT_STEP:
                raise RuntimeError("AI_PLAYER_FAULT_RAISE: injected brain fault")
            if options.fault_hang and step >= FAULT_HANG_AT_STEP:
                self._hang()
            if options.control_tap and step % CONTROL_TAP_EVERY_STEPS == 0:
                yield from self.controller.tap("B")
                step += 2
                continue
            yield from self.controller.wait(1)
            step += 1
        self.lifecycle.give_up("step0-placeholder", EXIT_OK)

    def _hang(self) -> None:
        """FAULT `AI_PLAYER_FAULT_HANG` only: block the main thread, as a stuck brain would. Nothing in
        this process can end the run now; only the launcher's hard wall clock can. Bounded anyway."""
        self.log.line(f"[AI-LIFECYCLE] FAULT_HANG: the brain blocks the main thread (at most {FAULT_HANG_MAX_SECONDS}s)")
        for _ in range(FAULT_HANG_MAX_SECONDS):
            time.sleep(1)
        raise RuntimeError("AI_PLAYER_FAULT_HANG: nobody killed the hung brain within its bound")


def start_session(expected_root: str | None = None) -> Session:
    """Called from the hook's constructor with the folder it put first on `sys.path`. Installs
    attribution and isolation, or exits trying."""
    global _active_session
    if _active_session is not None:
        # `main.py` builds a fresh mode instance whenever the controller stack runs empty. The AI
        # never lets that happen on purpose, so a second instance means it was restarted: end it.
        _active_session.log.line("[AI-LIFECYCLE] the framework tried to start the AI mode a second time")
        _active_session.lifecycle.finish("mode-restarted", EXIT_PARKED)
    options = RunOptions.from_env()
    session = Session(options, expected_root)
    _active_session = session
    try:
        session.start()
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001
        session.lifecycle.crash(error, "session start")
    return session
