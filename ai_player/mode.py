"""The AI player's BRAIN: what it does, one frame at a time. Framework-free by construction.

WHY THIS FILE KNOWS NOTHING ABOUT THE FRAMEWORK (RULING 37 Q1, and the adversarial review's finding
10 on step 0): the AI is built to become a standalone program that loads the ROM itself. So the brain
sees the game ONLY through the two abstract interfaces below, `Controls` (buttons and time) and
`Eyes` (what it can see), and it ends ONLY by returning its give-up reason. Everything that ties it
to the framework (starting a session, the guard listener, parking, listener isolation, the purity
audit, exit codes) lives in `ai_player/host/`; `ai_player/host/session.py` builds the real
controller and drives `Brain.play` one frame per `yield`. The purity gate enforces the split: this
file may not import `ai_player.host` (rule c), and it has no door into the framework at all (rule a).

BUILD STEP 0 (design draft §6, "purity scaffolding"). The brain is a PLACEHOLDER that presses
nothing, lets `frames` frames pass, and gives up with reason `step0-placeholder`. Later steps replace
`Brain.play` with the real brain (eyes, world model, navigator, battle decider, menus, goals,
personality, coach). The contract stays: it yields once per frame, every press goes through
`controls`, and it ends by RETURNING a reason (a return without one is a programming error, exit 5).

The fault and control switches are read by the host from the environment (`ai_player/options.py`)
and handed in as `BrainSettings`, so the fault arms exercise this very loop. None is set on the happy
path.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Protocol

__all__ = [
    "CONTROL_TAP_EVERY_STEPS",
    "FAULT_HANG_AT_STEP",
    "FAULT_HANG_MAX_SECONDS",
    "FAULT_RAISE_AT_STEP",
    "PLACEHOLDER_REASON",
    "Brain",
    "BrainSettings",
    "Controls",
    "Eyes",
]

#: FAULT `AI_PLAYER_FAULT_RAISE`: the brain raises on this step.
FAULT_RAISE_AT_STEP = 30
#: FAULT `AI_PLAYER_FAULT_HANG`: the brain blocks on this step, for at most this many seconds (a
#: bound, so even a launcher that failed to kill it could not leave it running forever).
FAULT_HANG_AT_STEP = 30
FAULT_HANG_MAX_SECONDS = 300
#: CONTROL `AI_PLAYER_CONTROL_TAP`: the placeholder taps B once every this many steps.
CONTROL_TAP_EVERY_STEPS = 60
#: The step-0 placeholder's give-up reason.
PLACEHOLDER_REASON = "step0-placeholder"


class Controls(Protocol):
    """The brain's hands: buttons and time. Each action is a generator that yields once per frame."""

    def wait(self, frames: int) -> Generator[None, None, None]:
        """Let `frames` frames pass without touching any button."""

    def tap(self, button: str) -> Generator[None, None, None]:
        """Press `button` for one frame, then leave it released for one frame."""

    def hold(self, button: str, frames: int) -> Generator[None, None, None]:
        """Hold `button` for `frames` frames, and always release it."""


class Eyes(Protocol):
    """The brain's view of the game. EMPTY in step 0: the placeholder looks at nothing. Build step 1
    (the eyes facade, memory reads behind an interface) gives it its first methods."""


@dataclass(frozen=True)
class BrainSettings:
    """What the brain is told about this run."""

    frames: int
    fault_raise: bool = False
    fault_hang: bool = False
    control_tap: bool = False


class Brain:
    """STEP 0 PLACEHOLDER. Presses nothing (except under the CONTROL switch); waits; gives up."""

    def __init__(self, settings: BrainSettings, say: Callable[[str], None]) -> None:
        self.settings = settings
        self._say = say

    def play(self, controls: Controls, eyes: Eyes | None) -> Generator[None, None, str]:
        """One `yield` per frame. Returns the give-up reason."""
        settings = self.settings
        step = 0
        while step < settings.frames:
            if settings.fault_raise and step >= FAULT_RAISE_AT_STEP:
                raise RuntimeError("AI_PLAYER_FAULT_RAISE: injected brain fault")
            if settings.fault_hang and step >= FAULT_HANG_AT_STEP:
                self._hang()
            if settings.control_tap and step % CONTROL_TAP_EVERY_STEPS == 0:
                yield from controls.tap("B")
                step += 2
                continue
            yield from controls.wait(1)
            step += 1
        return PLACEHOLDER_REASON

    def _hang(self) -> None:
        """FAULT `AI_PLAYER_FAULT_HANG` only: block the main thread, as a stuck brain would. Nothing in
        this process can end the run now; only the launcher's hard wall clock can. Bounded anyway."""
        self._say(f"[AI-LIFECYCLE] FAULT_HANG: the brain blocks the main thread (at most {FAULT_HANG_MAX_SECONDS}s)")
        for _ in range(FAULT_HANG_MAX_SECONDS):
            time.sleep(1)
        raise RuntimeError("AI_PLAYER_FAULT_HANG: nobody killed the hung brain within its bound")
