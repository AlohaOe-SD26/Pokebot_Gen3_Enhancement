"""
AI Player (hook) — registers the "AI Player" bot mode and hands EVERYTHING to the `ai_player` package.

WHY THIS FILE HAS NO LOGIC (USER RULINGS 35 and 37): the AI plays the game with its own code, which
lives in `ai_player/` at the repo root, outside the framework, so that it can later become a
standalone program. The framework itself is not edited; this is the one new file inside it, and it
only (1) registers the mode the way every `plugins/custom_modes/*.py` file does, and (2) puts the
folder that contains `ai_player/` FIRST on `sys.path` and delegates.

The folder comes from `AI_PLAYER_PACKAGE_ROOT` (set by `py -3.12 -m ai_player run`, which runs the
purity gate on exactly that folder before it starts the framework), else from this file's own
location (`<repo>/sandbox-pokebot/plugins/custom_modes/` -> `<repo>`). It is moved to the FRONT of
`sys.path` even if it is already listed further back, so no other `ai_player` can be found first, and
it is handed to `start_session`, which checks the package really loaded from there and logs it
(`[AI-PACKAGE]`). Nothing is imported from `ai_player` until the mode is actually started, so every
other mode's startup is unaffected by this file.

The session starts in the CONSTRUCTOR on purpose: `modules/main.py` constructs the mode, then runs
the listeners, then steps the mode, in one frame. See `ai_player/mode.py` for why that matters.
"""

import os
import sys
from pathlib import Path
from typing import Generator

from modules.modes._interface import BotMode


def _put_ai_player_first_on_path() -> str:
    root = os.environ.get("AI_PLAYER_PACKAGE_ROOT") or str(Path(__file__).resolve().parents[3])
    sys.path[:] = [root] + [entry for entry in sys.path if entry != root]
    return root


class AiPlayerMode(BotMode):
    @staticmethod
    def name() -> str:
        return "AI Player"  # must equal `ai_player.MODE_NAME`

    @staticmethod
    def is_selectable_from_title_screen() -> bool:
        # The AI starts from a real New Game (RULING 37 Q4), i.e. at the title screen.
        return True

    def __init__(self) -> None:
        root = _put_ai_player_first_on_path()
        from ai_player.mode import start_session

        self._session = start_session(root)
        super().__init__()

    def run(self) -> Generator:
        yield from self._session.run()
