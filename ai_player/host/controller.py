"""The AI's controller: the ONLY place the AI presses buttons or lets emulator frames pass.

WHY ONE DOOR (RULING 36: "the AI presses the BUTTONS itself"): if every press the AI makes goes
through this file, then `attribution.py` can tell an AI press from a press by anyone else simply by
asking "is this file on the call stack?". A press that comes from AI code but NOT through here is
counted as `ai_unrouted_presses` and breaks purity. That is how "the AI pressed it" stays a
measurement instead of a belief.

It implements the brain's abstract `Controls` interface (`ai_player/mode.py`): the brain never sees
this class, only `wait`, `tap` and `hold`, so a standalone build can hand it a different controller.

Every action is a generator with a hard frame budget: the main loop advances one frame per `yield`
(`modules/main.py`), and an unbounded wait is how a mode hangs.

‼ Pressing a button on every frame is HOLDING it. Gen-3 `waitbuttonpress` needs a new-press edge, so
`tap()` presses for one frame and then leaves one frame released (the story-drive protocol, trap 3).
"""

from __future__ import annotations

from collections.abc import Generator

from modules.context import context

from ai_player.host.attribution import seal_module

#: The controller's public surface. `context` is deliberately NOT on it: the purity gate refuses any
#: `__all__` entry that is an imported name, so the controller cannot hand the framework to anyone.
__all__ = ["BUTTONS", "MAX_ACTION_FRAMES", "Controller", "ControllerError"]

#: The GBA's buttons, by the names the emulator layer accepts.
BUTTONS = frozenset({"A", "B", "Select", "Start", "Right", "Left", "Up", "Down", "R", "L"})

#: No single controller action may last longer than this. A longer wait is a design error in the
#: caller, so it raises instead of silently blocking the run.
MAX_ACTION_FRAMES = 60 * 60 * 10  # ten minutes of game time


#: USER RULING 52 in code (build spec 2026-10-29 D12 (b)): START and SELECT are never held together with any other button.
#: Every reset or erase combination needs one of them with others: the soft reset A+B+START+SELECT (`src/main.c:135-137`),
#: the title's clear-save, clock and berry combinations (B+SELECT and more, `src/title_screen.c:39-41`). B held with a
#: direction (running) stays allowed. Nothing in the AI holds two buttons today (`hands/pad.py`: every press is one hold).
_ALONE = frozenset({"Start", "Select"})


class ControllerError(ValueError):
    pass


def _check_button(button: str) -> None:
    if button not in BUTTONS:
        raise ControllerError(f"unknown button {button!r}; expected one of {sorted(BUTTONS)}")


def _check_frames(frames: int) -> None:
    if not isinstance(frames, int) or frames < 0 or frames > MAX_ACTION_FRAMES:
        raise ControllerError(f"frame count {frames!r} outside 0..{MAX_ACTION_FRAMES}")


class Controller:
    """Buttons and time, for the AI only. Counts what it did so the logs can show it."""

    def __init__(self) -> None:
        self.frames_advanced = 0
        self.presses = 0
        #: (R1, D12 (b)) the buttons this controller holds down right now (a `hold` under way)
        self.held: set[str] = set()

    def _check_together(self, button: str) -> None:
        """(R1, D12 (b)) Refuse a press that would put START or SELECT down together with any other button."""
        down = self.held | {button}
        if len(down) > 1 and down & _ALONE:
            raise ControllerError(f"refused: {sorted(down)} together; START and SELECT are never held with another "
                                  f"button (a reset or erase combination: USER RULING 52)")

    def wait(self, frames: int) -> Generator[None, None, None]:
        """Let `frames` frames pass without touching any button."""
        _check_frames(frames)
        for _ in range(frames):
            self.frames_advanced += 1
            yield

    def tap(self, button: str) -> Generator[None, None, None]:
        """Press `button` for one frame, then leave it released for one frame (2 frames in all)."""
        _check_button(button)
        self._check_together(button)
        context.emulator.press_button(button)
        self.presses += 1
        yield from self.wait(2)

    def hold(self, button: str, frames: int) -> Generator[None, None, None]:
        """Hold `button` down for `frames` frames, and always release it, even if interrupted."""
        _check_button(button)
        _check_frames(frames)
        self._check_together(button)
        context.emulator.hold_button(button)
        self.held.add(button)
        self.presses += 1
        try:
            yield from self.wait(frames)
        finally:
            self.held.discard(button)
            context.emulator.release_button(button)


seal_module(__name__)
