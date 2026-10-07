"""The AI player's own log: every line goes to stdout AND to `<run_dir>/ai_player.log`.

WHY ITS OWN LOG: the framework prints through `rich`, which wraps long lines when stdout is a file
and has physically split machine-read lines before (`tools/story-dev/x4_headless.py`, "TWO TRAPS").
The `[AI-*]` lines are read by gates and drivers, so they are written with plain `print` and also to a
file nobody else writes to. Every line is flushed at once, so a killed process still leaves its lines.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["LOG_FILE_NAME", "RunLog"]

LOG_FILE_NAME = "ai_player.log"


class RunLog:
    def __init__(self, run_dir: Path | None) -> None:
        self._path: Path | None = None
        if run_dir is not None:
            run_dir.mkdir(parents=True, exist_ok=True)
            self._path = run_dir / LOG_FILE_NAME

    @property
    def path(self) -> Path | None:
        return self._path

    def line(self, text: str) -> None:
        try:
            print(text, flush=True)
        except Exception:
            # A closed or broken stdout must never stop the AI from exiting cleanly.
            pass
        if self._path is not None:
            try:
                with open(self._path, "a", encoding="utf-8", errors="replace") as handle:
                    handle.write(text + "\n")
            except OSError as error:
                try:
                    print(f"[AI-LOG] could not append to {self._path}: {error}", file=sys.stderr, flush=True)
                except Exception:
                    pass
