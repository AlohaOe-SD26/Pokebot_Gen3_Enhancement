"""The AI player's single exit door: every ending is a verdict file, log lines, and the PROCESS exiting.

WHY (design draft §10.3): the framework treats a mode's ending in two ways that are both wrong for
the AI. When `run()` returns, `modules/main.py` starts a FRESH mode instance with no limit; when it
raises, `main.py` prints the error and switches the bot to Manual, where the process then sits doing
nothing until a human notices (`main.py` 138-166). For a program meant to run unattended, and later
as an art piece, both are silent failures. So:

* giving up      = `[AI-EXIT] reason=<why> code=<n>` and `sys.exit(n)`;
* any exception  = the traceback, `[AI-EXIT] reason=crash code=2`, and `sys.exit(2)`;
* a stray exit   = a `SystemExit` that did not come from here (the brain called `sys.exit`) is turned
                   into `reason=stray-exit code=2` by the session, so it still leaves a verdict;
* being parked   = the guard listener sees the framework switch away from the AI mode (or discard
                   its generator) and exits with `reason=parked-manual` / `abandoned`, code 3;
* out of time    = the guard sees the launcher's soft deadline and exits with `reason=wall-clock`,
                   code 124, BEFORE the launcher's hard kill, so the verdict still gets written;
* isolation lost = the instrument sees a real frame about to run without the AI's guard listener
                   (the framework rebuilt its listeners behind the AI's back) and the session exits
                   with `reason=isolation-lost`, code 6, before that frame runs;
* interrupted    = Ctrl+C / Ctrl+Break: the session's signal handler only sets a flag, and the
                   guard exits with `reason=interrupted`, code 130, on the next frame; if no frame
                   comes (the brain, or anything else on the main thread, is stuck), the session's
                   interrupt watch ends the run from its own thread after a grace period, with
                   `reason=interrupted-unresponsive`, code 130, and a verdict all the same;
* refused        = the session will not start in debug mode or with the HTTP server on (code 9).

`finish` can therefore be called from two threads (the main thread's guard and the interrupt watch).
It is SINGLE-ENTRY: the first caller holds a lock it never gives back (the process ends), a second
thread waits (bounded) for that one to end the process, and a second call on the SAME thread (a
failure while already finishing) just leaves. And while one thread finishes, no other thread runs a
frame: `finalize_audit`, the first thing `finish` does, closes the instrument's FRAME FENCE (round 3:
a main thread that woke up late used to run a frame unaudited, or after the verdict as a false
`ran-after-finish` BREACH).

WHY THE LIFECYCLE IS `Guarded` (a verifier's probe after step 0.1): its slots were writable from any
code at run time, uncounted (`lifecycle._verdict_path = None` silently suppressed the verdict file,
`lifecycle._attribution = ...` handed `finish` another instrument). Now only this file can write
them; any other writer is refused and counted as `instrument_tampered`.

`SystemExit` passes through every `except` in `main.py`, so the process really ends (and if a
non-daemon framework thread would hold the interpreter open at shutdown, the instrument's exit
watchdog ends it with `os._exit` 20 s later: the HTTP server's thread is one, so a run refused for
it would otherwise never exit; live arms H2 and M5w measure both halves). On the way out
`finish` (and ONLY `finish`: the instrument refuses any other caller) finalizes the audit, restores the
framework's listeners and has the instrument write `<run_dir>/purity.json`, the file the launcher
grades the run from. The printed `[AI-PURITY]` line is for people; any code can print a line.

Exit codes (the launcher adds 7 and 8, see `host/launcher.py`):
  0    the brain gave up normally and purity is CLEAN
  2    crash (any exception in the AI's code), or a stray SystemExit
  3    parked or abandoned by the framework (Manual mode, generator discarded, mode restarted)
  4    frame budget exceeded (the AI's steps were starved, for example by a foreign handler)
  5    the brain returned without giving up (a programming error)
  6    purity breached (or never measured: UNVERIFIED), including isolation lost and ran-after-finish
  9    refused to start: the framework is in debug mode, or its HTTP server is on
  124  the wall clock ran out (soft: this module, with a verdict; hard: the launcher, without one)
  130  interrupted (Ctrl+C / Ctrl+Break), with a verdict (`interrupted`, or `interrupted-unresponsive`
       when the main thread never reached the guard again)
"""

from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path
from typing import NoReturn

from ai_player.host.attribution import Attribution, Guarded, seal_module
from ai_player.host.isolation import ListenerIsolation
from ai_player.runlog import RunLog

__all__ = [
    "EXIT_BRAIN_RETURNED",
    "EXIT_CRASH",
    "EXIT_FRAME_BUDGET",
    "EXIT_INTERRUPTED",
    "EXIT_OK",
    "EXIT_PARKED",
    "EXIT_PURITY_BREACH",
    "EXIT_REFUSED",
    "EXIT_WALL_CLOCK",
    "Lifecycle",
]

EXIT_OK = 0
EXIT_CRASH = 2
EXIT_PARKED = 3
EXIT_FRAME_BUDGET = 4
EXIT_BRAIN_RETURNED = 5
EXIT_PURITY_BREACH = 6
EXIT_REFUSED = 9
EXIT_WALL_CLOCK = 124  # the same code the launcher uses for its hard kill: "ran out of wall time"
EXIT_INTERRUPTED = 130  # the conventional code of a process ended by Ctrl+C
#: How long a SECOND thread that calls `finish` waits for the first one to end the process.
FINISH_WAIT_SECONDS = 60.0


class Lifecycle(Guarded):
    """Guarded, sealed and slotted for the same reason as the instrument: `finish` decides what the
    verdict file says about the ending, so no other code may replace it or the state it reads (a write
    from outside this file is refused and counted; `object.__setattr__` is the known residual, refused
    by the static gate)."""

    __slots__ = (
        "_log", "_attribution", "_isolation", "_verdict_path", "_package_root", "_finishing", "_abandoned",
        "_door", "_finisher", "_loop_thread",
    )

    def __init__(
        self,
        log: RunLog,
        attribution: Attribution,
        isolation: ListenerIsolation,
        verdict_path: Path | None,
        package_root: Path,
    ) -> None:
        self._log = log
        self._attribution = attribution
        self._isolation = isolation
        self._verdict_path = verdict_path
        self._package_root = package_root
        # The session is built on the framework's frame loop, the main thread: `finish` compares against it.
        self._loop_thread = threading.get_ident()
        self._finishing = False
        self._abandoned = False
        self._door = threading.Lock()  # taken once, by the first finish, and never given back
        self._finisher: int | None = None  # the thread that took it

    @property
    def finishing(self) -> bool:
        return self._finishing

    @property
    def abandoned(self) -> bool:
        return self._abandoned

    def finish(self, reason: str, code: int) -> NoReturn:
        """End the process: finalize the audit, restore the listeners, write the verdict file, exit."""
        if not self._door.acquire(blocking=False):
            if self._finisher == threading.get_ident():
                # Something failed while this thread was already on the way out: do not loop, just leave.
                raise SystemExit(code)
            # Another thread is writing the verdict and will end the process; wait for it (bounded).
            self._door.acquire(timeout=FINISH_WAIT_SECONDS)
            raise SystemExit(code)
        self._finisher = threading.get_ident()
        self._finishing = True

        counters = self._attribution.finalize_audit()  # last instrument check; the counts freeze here
        if threading.get_ident() != self._loop_thread:
            # The frame loop may still be running: handing the framework its listeners back now would let them
            # act with every door already off. The process ends right after the verdict, so nothing is lost.
            isolation_line = ("[AI-ISOLATION] finish off the frame-loop thread: listeners NOT restored (the process "
                              "ends after the verdict; the framework never runs again)")
        else:
            try:
                isolation_line = self._isolation.restore()
            except Exception as error:
                isolation_line = f"[AI-ISOLATION] exit restore FAILED: {type(error).__name__}: {error}"
                self._attribution.note_error("restoring the listeners", error)

        verdict = counters.verdict()
        if code == EXIT_OK and verdict != "CLEAN":
            self._log.line(f"[AI-LIFECYCLE] the brain's own reason was '{reason}', but the purity verdict is {verdict}")
            reason = "purity-breach" if verdict == "BREACH" else "purity-unverified"
            code = EXIT_PURITY_BREACH
        file_line = self._attribution.write_verdict_file(
            self._verdict_path,
            {
                "exit_reason": reason,
                "exit_code": code,
                "isolation": self._isolation.report(),
                "package_root": str(self._package_root),
            },
        )
        self._log.line(counters.purity_line())
        self._log.line(counters.origins_line())
        self._log.line(isolation_line)
        self._log.line(file_line)
        self._log.line(f"[AI-EXIT] reason={reason} code={code}")
        # A non-daemon framework thread (the HTTP server's) would hold the interpreter open at
        # shutdown for ever: the instrument's daemon timer ends the process if it is still alive.
        self._attribution.arm_exit_watchdog(code)
        sys.exit(code)

    def give_up(self, reason: str, code: int = EXIT_OK) -> NoReturn:
        """The brain's way to stop: a written reason and a bounded, clean exit."""
        self.finish(reason, code)

    def crash(self, error: BaseException, where: str) -> NoReturn:
        self._log.line(f"[AI-LIFECYCLE] exception in {where}: {type(error).__name__}: {error}")
        for chunk in traceback.format_exception(error):
            for line in chunk.rstrip("\n").splitlines():
                self._log.line(f"[AI-TRACEBACK] {line}")
        self.finish("crash", EXIT_CRASH)

    def note_abandoned(self) -> None:
        """The framework closed the AI's generator. The guard listener ends the process next frame;
        it cannot be done here, because an exception raised while a generator is being closed by the
        garbage collector is printed and ignored, not propagated."""
        self._abandoned = True
        self._log.line("[AI-LIFECYCLE] the framework discarded the AI's generator; exiting on the next frame")


seal_module(__name__)
