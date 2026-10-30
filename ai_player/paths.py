"""WHERE THE AI'S USER DATA LIVES (R1 + R2, build spec 2026-10-29 D8; backlog DP1): one `AppPaths` per game.

WHY ONE RESOLVER: `memory.jsonl` (the AI's memory of a game, `game_memory.py`) is the first file the AI keeps across
processes, so where it lives is fixed now, in ONE place, before any second file copies a path. The memory of a game lives
BESIDE THE CARTRIDGE SAVE IT DESCRIBES (one playthrough = one save = one memory; round-3 deployment D4): a continue reads
the cart and the memory together, and they must never come from two places.

    dev default             <build_root>/profiles/<NAME>/ai_player/          (beside the profile's current_save.sav)
    AI_PLAYER_HOME set      <AI_PLAYER_HOME>/games/<NAME>/

Each game folder holds `memory.jsonl` (the AI's, written by the play brain through `runlog.RecordFile`),
`launches.jsonl` (the LAUNCHER's own record of how each child ended, D20) and `retired/` (a memory archived by `--fresh` or
`--state`, D10: renamed there, never deleted or rewritten).

LAUNCHER SIDE (`gates/check_purity.py` LAUNCHER_FILES): the launcher resolves the path and hands the child its memory file
through `AI_PLAYER_MEMORY` (`options.py`); the play loop never resolves a path itself. Nothing here writes a file: the
launcher creates and archives. `gates/check_paths.py` refuses machine paths (a drive, the repo's folder names) in string
constants anywhere else in the package, so no second resolver can grow in the AI's code.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from ai_player.game_memory import MEMORY_FILE_NAME

__all__ = [
    "ENV_HOME",
    "GAME_DIR_NAME",
    "LAUNCHES_FILE_NAME",
    "RETIRED_DIR_NAME",
    "AppPaths",
    "PathsError",
]

#: The user's data root for a deployed AI (unset in development: the dev default beside the profile is used).
ENV_HOME = "AI_PLAYER_HOME"
#: The AI's folder inside a framework profile (the dev default).
GAME_DIR_NAME = "ai_player"
LAUNCHES_FILE_NAME = "launches.jsonl"
RETIRED_DIR_NAME = "retired"
#: A game's name is a profile name: the launcher's own rule (`host/launcher.py` _PROFILE_NAME_RE), so a name can never walk
#: out of its folder ("..", a separator, a drive).
_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class PathsError(ValueError):
    """A game name or a root that cannot hold a game's data."""


@dataclass(frozen=True)
class AppPaths:
    """The files of ONE game (`name`, the profile's name) in `game_dir`."""

    name: str
    game_dir: Path

    @classmethod
    def for_profile(cls, name: str, build_root: Path, home: str | None = None) -> "AppPaths":
        """The game folder of profile `name`: under `home` (default: the `AI_PLAYER_HOME` environment variable) when it
        is set, else the dev default beside the profile's cartridge save under `build_root`."""
        if not _NAME.match(name) or name in (".", ".."):
            raise PathsError(f"a game's name is a profile name (letters, digits, '_', '-', '.'), not {name!r}")
        root = home if home is not None else os.environ.get(ENV_HOME)
        if root:
            return cls(name, Path(root) / "games" / name)
        return cls(name, Path(build_root) / "profiles" / name / GAME_DIR_NAME)

    # (build stage 4) the properties are named for their FILES (`memory_jsonl`, not `memory`): the call-site census matches
    # a property's reads by NAME, and `.memory` is read everywhere (the goal manager's memory)
    @property
    def memory_jsonl(self) -> Path:
        """`memory.jsonl`: the AI's memory of this game (`game_memory.py`)."""
        return self.game_dir / MEMORY_FILE_NAME

    @property
    def launches_jsonl(self) -> Path:
        """`launches.jsonl`: the launcher's record of how each child ended (D20)."""
        return self.game_dir / LAUNCHES_FILE_NAME

    @property
    def retired_dir(self) -> Path:
        """`retired/`: where `--fresh` and `--state` move an existing memory (D10)."""
        return self.game_dir / RETIRED_DIR_NAME

    def retired_path(self, file_name: str, when: float | None = None) -> Path:
        """Where `file_name` (`memory.jsonl` or `launches.jsonl`) is archived at `when` (seconds since the epoch, local
        time; default now): `retired/<stem>-<YYYYmmdd-HHMMSS>.jsonl`. A name already taken gets `-2`, `-3`, ... (two
        archives in one second never overwrite each other)."""
        stem = Path(file_name).stem
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time() if when is None else when))
        folder = self.retired_dir
        candidate = folder / f"{stem}-{stamp}.jsonl"
        n = 2
        while candidate.exists():
            if n > 1000:
                raise PathsError(f"more than 1000 archives of {file_name} in one second under {folder}")
            candidate = folder / f"{stem}-{stamp}-{n}.jsonl"
            n += 1
        return candidate
