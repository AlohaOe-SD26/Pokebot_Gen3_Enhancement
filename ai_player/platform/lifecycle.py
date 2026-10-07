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
                   code 124, BEFORE the launcher's hard kill, so the verdict still gets written.

`SystemExit` passes through every `except` in `main.py`, so the process really ends. On the way out
`finish` (and ONLY `finish`: the instrument refuses any other caller) finalizes the audit, restores the
framework's listeners and has the instrument write `<run_dir>/purity.json`, the file the launcher
grades the run from. The printed `[AI-PURITY]` line is for people; any code can print a line.

Exit codes (the launcher adds 7 and 8, see `platform/launcher.py`):
  0    the brain gave up normally and purity is CLEAN
  2    crash (any exception in the AI's code), or a stray SystemExit
  3    parked or abandoned by the framework (Manual mode, generator discarded, mode restarted)
  4    frame budget exceeded (the AI's steps were starved, for example by a foreign handler)
  5    the brain returned without giving up (a programming error)
  6    the brain gave up normally BUT purity was breached, or never measured (UNVERIFIED)
  124  the wall clock ran out (soft: this module, with a verdict; hard: the launcher, without one)
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import NoReturn

from modules.context import context

from ai_player.platform.attribution import Attribution, Sealed
from ai_player.platform.isolation import ListenerIsolation
from ai_player.runlog import RunLog

__all__ = [
    "EXIT_BRAIN_RETURNED",
    "EXIT_CRASH",
    "EXIT_FRAME_BUDGET",
    "EXIT_OK",
    "EXIT_PARKED",
    "EXIT_PURITY_BREACH",
    "EXIT_WALL_CLOCK",
    "Lifecycle",
    "current_bot_mode",
]

EXIT_OK = 0
EXIT_CRASH = 2
EXIT_PARKED = 3
EXIT_FRAME_BUDGET = 4
EXIT_BRAIN_RETURNED = 5
EXIT_PURITY_BREACH = 6
EXIT_WALL_CLOCK = 124  # the same code the launcher uses for its hard kill: "ran out of wall time"


def current_bot_mode() -> str:
    """The framework's selected bot mode. Anything but the AI's own name means it has been parked."""
    return context.bot_mode


class Lifecycle(metaclass=Sealed):
    """Sealed and slotted for the same reason as the instrument: `finish` decides what the verdict
    file says about the ending, so no other code may replace it or the state it reads."""

    __slots__ = ("_log", "_attribution", "_isolation", "_verdict_path", "_package_root", "_finishing", "_abandoned")

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
        self._finishing = False
        self._abandoned = False

    @property
    def finishing(self) -> bool:
        return self._finishing

    @property
    def abandoned(self) -> bool:
        return self._abandoned

    def finish(self, reason: str, code: int) -> NoReturn:
        """End the process: finalize the audit, restore the listeners, write the verdict file, exit."""
        if self._finishing:
            # Something failed while we were already on the way out: do not loop, just leave.
            raise SystemExit(code)
        self._finishing = True

        counters = self._attribution.finalize_audit()  # last instrument check; the counts freeze here
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
