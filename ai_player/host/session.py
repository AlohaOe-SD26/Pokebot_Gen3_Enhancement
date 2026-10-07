"""One AI run inside the framework: what the hook in `sandbox-pokebot/plugins/custom_modes/` delegates to.

The brain (`ai_player/mode.py`) is framework-free; THIS file is where the run meets the framework
(the adversarial review's finding 10 moved it here from `mode.py`). It:

  * refuses to start where a run could not end cleanly: in the framework's DEBUG mode (`main.py`
    parks a failing mode in `debug_stepping_mode` there instead of ending it) and with the framework's
    HTTP SERVER on (its `work_queue` callbacks run framework code on the main thread between the AI's
    frames). Both are exit 9 with a verdict file, never a silent start (findings 5 and 6);
  * installs Ctrl+C / Ctrl+Break handlers that only set a flag, which the guard turns into
    `reason=interrupted` with a verdict on the next frame (finding 7: a KeyboardInterrupt raised
    outside the AI's generator used to end the process with no verdict at all), and starts the
    INTERRUPT WATCH, a daemon thread that ends the run itself (`reason=interrupted-unresponsive`, code
    130, with a verdict) when no frame reaches the guard within `INTERRUPT_GRACE_SECONDS` of the
    signal. WHY: a verifier hung the brain (`AI_PLAYER_FAULT_HANG`) and pressed Ctrl+Break; the flag
    was set, but the guard never ran again, so the process could not be stopped from its console at
    all (step 0, with no handler, had at least died at once). A second Ctrl+C restoring the default
    action was considered and rejected: it would end the run with NO verdict, which is finding 7
    again. The watch cannot help when the main thread is blocked inside ONE C call (a Python signal
    handler only runs between bytecodes): there only an outside kill ends the run. ROUND 3: the watch
    says what it MEASURED (frames that ran and frames that reached the guard since the signal), never
    "stuck" by assumption; and a main thread that wakes up while the watch is finishing cannot run a
    frame any more (the instrument's frame fence, `attribution.py`), so a late wake-up is neither an
    unaudited frame nor a false `ran-after-finish` BREACH;
  * installs the instrument (`attribution.py`), applies listener isolation (`isolation.py`) and asks
    the instrument to check the AI's guard listener before every real frame (finding 1);
  * runs the GUARD once per frame from the AI's own listener: parked in Manual, discarded, starved
    past the frame budget, out of wall-clock time or interrupted all end the PROCESS (`lifecycle.py`);
  * drives the brain one frame per `yield`, re-asserting isolation between frames.

WHEN THINGS HAPPEN, and why that order:
  `start_session()` runs from the hook's CONSTRUCTOR. `modules/main.py` builds the mode instance,
  then calls every listener, then steps the mode, all in the same frame. Isolating in the
  constructor means no framework listener ever runs while the AI is in charge, not even once:
  on a fixture saved mid-battle, one listener pass would already have pushed the bot's battle
  handler on top of the AI.

WHICH PACKAGE RUNS: the hook passes the folder it appended to `sys.path`; the session checks that
this very file was loaded from there and logs `[AI-PACKAGE]` (the path also goes into the verdict
file). The launcher gates exactly that folder before it starts the framework, so "the gate passed"
and "this code ran" are tied together by evidence, not assumed.

`Session` is `Guarded` (`attribution.py`): its attributes (the lifecycle it ends the run through, the
frame budget, the interrupt flag) can be written only by this file; any other writer is refused and
counted as `instrument_tampered`.
"""

from __future__ import annotations

import signal
import threading
import time
from collections.abc import Generator
from pathlib import Path

from modules.context import context

from ai_player import MODE_NAME
from ai_player.host.attribution import Attribution, Guarded, seal_module
from ai_player.host.controller import Controller
from ai_player.host.isolation import GuardListener, ListenerIsolation
from ai_player.host.lifecycle import (
    EXIT_BRAIN_RETURNED,
    EXIT_CRASH,
    EXIT_FRAME_BUDGET,
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_PARKED,
    EXIT_PURITY_BREACH,
    EXIT_REFUSED,
    EXIT_WALL_CLOCK,
    Lifecycle,
)
from ai_player.mode import Brain, BrainSettings
from ai_player.options import VERDICT_FILE_NAME, RunOptions
from ai_player.runlog import RunLog

#: The folder that CONTAINS this `ai_player/` package: what the hook must have put on `sys.path`.
LOADED_FROM = Path(__file__).resolve().parents[2]

__all__ = ["Session", "start_session"]

#: How many frames past `--frames` the guard allows before it ends a starved run itself.
FRAME_BUDGET_GRACE = 600
#: How often the guard prints the running counters, in frames.
HEARTBEAT_EVERY_FRAMES = 1000
#: FAULT `AI_PLAYER_FAULT_MANUAL`: the planted listener raises on this frame.
FAULT_MANUAL_AT_FRAME = 30
#: After Ctrl+C / Ctrl+Break, how long the guard has to end the run before the interrupt watch does.
#: The guard runs every frame (thousands a second unthrottled, 60 throttled), so 10 s means stuck.
INTERRUPT_GRACE_SECONDS = 10.0
#: How often the interrupt watch looks at the flag.
INTERRUPT_POLL_SECONDS = 0.25
#: The interrupt watch's own bound: it stops watching after this long (a week).
INTERRUPT_WATCH_MAX_SECONDS = 7 * 24 * 60 * 60

#: The session of this process. A list changed in place, because the module is sealed.
_ACTIVE: list = []


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


class Session(Guarded):
    """One AI run inside one framework process."""

    __slots__ = (
        "options", "expected_root", "log", "controller", "brain", "attribution", "guard", "isolation",
        "lifecycle", "frames_seen", "frame_cap", "interrupted", "watch",
    )

    def __init__(self, options: RunOptions, expected_root: str | None) -> None:
        self.options = options
        self.expected_root = expected_root
        self.log = RunLog(options.run_dir)
        self.controller = Controller()
        self.brain = Brain(
            BrainSettings(
                frames=options.frames,
                fault_raise=options.fault_raise,
                fault_hang=options.fault_hang,
                control_tap=options.control_tap,
            ),
            self.log.line,
        )
        self.attribution = Attribution()
        self.guard = GuardListener(self._on_frame)
        extra = [_FaultRaisingListener()] if options.fault_manual else []
        self.isolation = ListenerIsolation(
            self.guard,
            keep_foreign=options.fault_keep_listeners,
            rebind=not options.fault_no_rebind,
            skip_restore=options.fault_skip_restore,
            extra=extra,
            on_tamper=self.attribution.note_tamper,
        )
        verdict_path = options.run_dir / VERDICT_FILE_NAME if options.run_dir is not None else None
        self.lifecycle = Lifecycle(self.log, self.attribution, self.isolation, verdict_path, LOADED_FROM)
        self.frames_seen = 0
        self.frame_cap = options.frames + FRAME_BUDGET_GRACE
        self.interrupted: int | None = None
        self.watch: threading.Thread | None = None

    # ------------------------------------------------------------------ start
    def start(self) -> None:
        http_on = bool(context.config.http.http_server.enable)
        debug = bool(context.debug)
        self.log.line(
            f"[AI-START] mode={MODE_NAME!r} {self.options.describe()} "
            f"http_server={'on' if http_on else 'off'} debug={debug}"
        )
        matches = self.expected_root is None or Path(self.expected_root).resolve() == LOADED_FROM
        self.log.line(f"[AI-PACKAGE] matches_hook_root={matches} loaded_from={LOADED_FROM}")
        if not matches:
            raise RuntimeError(
                f"the hook put {self.expected_root} on sys.path, but ai_player was loaded from "
                f"{LOADED_FROM}: the code running is not the code that was gated"
            )
        if debug:
            self.log.line(
                "[AI-START] REFUSED: the framework runs in debug mode, where main.py parks a failing mode "
                "in debug_stepping_mode instead of ending it; an AI run must always end"
            )
            self.lifecycle.finish("refused-debug-mode", EXIT_REFUSED)
        if http_on:
            self.log.line(
                "[AI-START] REFUSED: the framework's HTTP server is on; its work_queue callbacks run framework "
                "code on the main thread between the AI's frames (the launcher writes http.yml OFF for its profiles)"
            )
            self.lifecycle.finish("refused-http-server", EXIT_REFUSED)
        if self._install_interrupt_handlers():
            self.watch = threading.Thread(target=self._watch_interrupts, name="ai-player-interrupt-watch", daemon=True)
            self.watch.start()
        self.attribution.install()
        entry, active = self.isolation.apply()
        self.attribution.watch_guard(self.guard, self._isolation_lost)
        self.log.line(f"[AI-ISOLATION] entry {entry}")
        self.log.line(f"[AI-ISOLATION] active {active} keep_foreign={self.options.fault_keep_listeners}")

    def _install_interrupt_handlers(self) -> bool:
        """Ctrl+C (SIGINT) and, on Windows, Ctrl+Break (SIGBREAK) only set a flag; the guard ends the
        run with a verdict on the next frame. Not possible outside the main thread (a GUI runs the
        main loop in a worker thread), which is logged. Returns whether any handler is installed."""
        numbers = [signal.SIGINT]
        try:
            numbers.append(signal.SIGBREAK)
        except AttributeError:
            pass  # not Windows: there is no Ctrl+Break
        installed = []
        for number in numbers:
            try:
                signal.signal(number, self._on_signal)
                installed.append(number.name)
            except (ValueError, OSError) as error:
                self.log.line(f"[AI-START] no handler for {number.name}: {error}")
        self.log.line(
            f"[AI-START] interrupt handlers: {','.join(installed) or 'none'} (they end the run with a verdict; "
            f"if no frame comes within {INTERRUPT_GRACE_SECONDS:g}s, the interrupt watch does)"
        )
        return bool(installed)

    def _on_signal(self, number, frame) -> None:
        # Only a flag: no lock, no thread start, no I/O (a handler runs between ANY two bytecodes of
        # the main thread, including inside code holding a lock it would need).
        if self.interrupted is None:
            self.interrupted = int(number)

    def _watch_interrupts(self) -> None:
        """The interrupt watch (a daemon thread). Waits for the flag; then gives the guard
        `INTERRUPT_GRACE_SECONDS` to end the run on the main thread; if it has not, the main thread is
        stuck (the brain hangs, or something under it does), so this thread ends the run itself, with
        a verdict. Every wait here is bounded."""
        for _ in range(int(INTERRUPT_WATCH_MAX_SECONDS / INTERRUPT_POLL_SECONDS)):
            if self.interrupted is not None:
                break
            time.sleep(INTERRUPT_POLL_SECONDS)
        else:
            return
        guard_frames_at_flag = self.frames_seen
        real_frames_at_flag = self.attribution.counters.real_frames
        for _ in range(int(INTERRUPT_GRACE_SECONDS / INTERRUPT_POLL_SECONDS)):
            if self.lifecycle.finishing:
                return
            time.sleep(INTERRUPT_POLL_SECONDS)
        if self.lifecycle.finishing:
            return
        progress = self._progress_since(guard_frames_at_flag, real_frames_at_flag)
        self.log.line(
            f"[AI-LIFECYCLE] interrupted by signal {self.interrupted}, {progress}; the interrupt watch ends the run "
            f"from its own thread, with a verdict (the instrument holds back any frame the main thread starts meanwhile)"
        )
        self.lifecycle.finish("interrupted-unresponsive", EXIT_INTERRUPTED)

    def _progress_since(self, guard_frames: int, real_frames: int) -> str:
        """What the main thread did during the grace period, MEASURED, not assumed. WHY: step 0.1's line
        said "the main thread is stuck" unconditionally, and a verifier's mutant (a guard that ignored
        the flag) printed it while 16,822 frames had run. Two independent counts: frames that reached
        the guard (this session's), and real frames the main loop ran (the instrument's)."""
        guard_now = self.frames_seen
        real_now = self.attribution.counters.real_frames
        ran, reached = real_now - real_frames, guard_now - guard_frames
        if ran == 0 and reached == 0:
            return (
                f"but no frame reached the guard within {INTERRUPT_GRACE_SECONDS:g}s: no frame ran at all since the watch "
                f"saw the signal (the main thread is stuck, or blocked in one long call; the guard saw {guard_now} frames in all)"
            )
        return (
            f"and the main thread is NOT stuck: {ran} frames ran and {reached} reached the guard since the watch saw the "
            f"signal, but the guard did not end the run within {INTERRUPT_GRACE_SECONDS:g}s"
        )

    def _isolation_lost(self) -> None:
        """Called by the instrument when a real frame is about to run without the AI's guard listener."""
        self.log.line(
            "[AI-LIFECYCLE] the instrument found a real frame about to run without the AI's guard listener: "
            "the framework rebuilt its listeners behind the AI's back; ending the run before that frame"
        )
        self.lifecycle.finish("isolation-lost", EXIT_PURITY_BREACH)

    # ------------------------------------------------------------------ the guard (every frame)
    def _on_frame(self) -> None:
        """Runs once per frame from the AI's own listener, even while the AI's generator is starved."""
        self.frames_seen += 1
        if self.interrupted is not None:
            self.log.line(f"[AI-LIFECYCLE] interrupted by signal {self.interrupted} (Ctrl+C / Ctrl+Break); ending the run with a verdict")
            self.lifecycle.finish("interrupted", EXIT_INTERRUPTED)
        if self.lifecycle.abandoned:
            self.lifecycle.finish("abandoned", EXIT_PARKED)
        current_mode = context.bot_mode
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
            reason = yield from self._steps(self.brain.play(self.controller, None))
            if reason is None:
                self.lifecycle.finish("brain-returned", EXIT_BRAIN_RETURNED)
            self.lifecycle.give_up(str(reason), EXIT_OK)
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

    def _steps(self, steps: Generator[None, None, str]) -> Generator[None, None, str | None]:
        """Drive the brain one frame at a time, re-asserting isolation between frames. Returns the
        brain's give-up reason (None when it returned without one). The live driver's PLANT arms hook
        in here, once per step, with `self` (so a plant runs inside the AI's play loop)."""
        step = 0
        try:
            while True:
                try:
                    next(steps)
                except StopIteration as done:
                    return done.value
                note = self.isolation.enforce()
                if note:
                    self.log.line(note)
                yield
                step += 1
        finally:
            steps.close()


def start_session(expected_root: str | None = None) -> Session:
    """Called from the hook's constructor with the folder it put on `sys.path`. Installs attribution
    and isolation, or exits trying."""
    if _ACTIVE:
        # `main.py` builds a fresh mode instance whenever the controller stack runs empty. The AI
        # never lets that happen on purpose, so a second instance means it was restarted: end it.
        _ACTIVE[-1].log.line("[AI-LIFECYCLE] the framework tried to start the AI mode a second time")
        _ACTIVE[-1].lifecycle.finish("mode-restarted", EXIT_PARKED)
    options = RunOptions.from_env()
    session = Session(options, expected_root)
    _ACTIVE.append(session)
    try:
        session.start()
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001
        session.lifecycle.crash(error, "session start")
    return session


seal_module(__name__)
