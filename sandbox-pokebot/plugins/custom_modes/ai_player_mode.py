"""
AI Player (hook) — registers the "AI Player" bot mode and hands EVERYTHING to the `ai_player` package.

WHY THIS FILE HAS NO GAME LOGIC (USER RULINGS 35 and 37): the AI plays the game with its own code,
which lives in `ai_player/` at the repo root, outside the framework, so that it can later become a
standalone program. The framework itself is not edited; this is the one new file inside it, and it
only (1) registers the mode the way every `plugins/custom_modes/*.py` file does, (2) APPENDS the
folder that contains `ai_player/` to `sys.path` and delegates, and (3) records, independently of the
AI's own code, the framework's listener list before the AI starts and what the framework holds when
the process exits.

THE PATH IS APPENDED, NEVER PUT FIRST (step 0.1, the adversarial review's finding 4). Step 0 moved the
repo root to the FRONT of `sys.path`, ahead of the standard library, so any file at the repo root
named like a library module (`statistics.py`, `colorsys.py`) would have been what the framework's
own `import` statements loaded. Appended, the standard library always wins. If some other `ai_player`
is found earlier on the path, the session's `[AI-PACKAGE]` check sees that the code that loaded is
not the code that was gated and the run crashes with that reason. The gate allows the hook
`sys.path.append` and nothing else on `sys.path`.

The folder comes from `AI_PLAYER_PACKAGE_ROOT` (set by `py -3.12 -m ai_player run`, which runs the
purity gate on exactly that folder before it starts the framework), else from this file's own
location (`<repo>/sandbox-pokebot/plugins/custom_modes/` -> `<repo>`). Nothing is imported from
`ai_player` until the mode is actually started, so every other mode's startup is unaffected.

THE `[AI-HOOK]` LINES (finding 9): the AI's isolation reports that it restored "the same list object",
but it compares the list it saved with itself. So this file takes its OWN record of
`context.bot_listeners` before `start_session` runs, and at process exit (`atexit`, which runs on every
ending that is not `os._exit`) prints whether the framework now holds that very list with the very
same members. That is an observation by code the AI's isolation does not control.

The session starts in the CONSTRUCTOR on purpose: `modules/main.py` constructs the mode, then runs
the listeners, then steps the mode, in one frame. See `ai_player/host/session.py` for why that matters.
"""

import atexit
import os
import sys
from pathlib import Path
from typing import Generator

from modules.context import context
from modules.modes._interface import BotMode


def _append_repo_root_to_path() -> str:
    root = os.environ.get("AI_PLAYER_PACKAGE_ROOT") or str(Path(__file__).resolve().parents[3])
    sys.path.append(root)
    return root


def _describe(listeners: list) -> str:
    names = ",".join(type(listener).__name__ for listener in listeners)
    return f"n={len(listeners)} types=[{names}]"


def _report_listeners_at_exit(before: list, members: list) -> None:
    now = context.bot_listeners
    same_object = now is before
    unchanged = len(now) == len(members) and all(a is b for a, b in zip(now, members))
    print(
        f"[AI-HOOK] listeners at process exit: same_list_object={same_object} members_unchanged={unchanged} "
        f"{_describe(now)}",
        flush=True,
    )


class AiPlayerMode(BotMode):
    @staticmethod
    def name() -> str:
        return "AI Player"  # must equal `ai_player.MODE_NAME`

    @staticmethod
    def is_selectable_from_title_screen() -> bool:
        # The AI starts from a real New Game (RULING 37 Q4), i.e. at the title screen.
        return True

    def __init__(self) -> None:
        before = context.bot_listeners
        members = list(before)
        print(f"[AI-HOOK] listeners before the AI starts: {_describe(members)}", flush=True)
        atexit.register(_report_listeners_at_exit, before, members)
        root = _append_repo_root_to_path()
        from ai_player.host.session import start_session

        self._session = start_session(root)
        super().__init__()

    def run(self) -> Generator:
        yield from self._session.run()
