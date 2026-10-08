"""The AI player's own logs: every line goes to stdout AND to `<run_dir>/ai_player.log`; one-line
records (the ACTION LOG) go to `<run_dir>/actions.jsonl`.

WHY ITS OWN LOG: the framework prints through `rich`, which wraps long lines when stdout is a file
and has physically split machine-read lines before (`tools/story-dev/x4_headless.py`, "TWO TRAPS").
The `[AI-*]` lines are read by gates and drivers, so they are written with plain `print` and also to a
file nobody else writes to. Every line is flushed at once, so a killed process still leaves its lines.

WHY THE ACTION LOG IS WRITTEN HERE (build step 1): this file is one of the two the purity gate lets
write files (rule f; the other is the instrument). `ai_player/memory_log.py` BUILDS the records (frame,
observation digest, decision, action, reason, observation) and hands each finished line to a
`RecordFile`; it never opens a file itself, so the gate's list of file writers did not have to grow.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["ACTION_LOG_FILE_NAME", "LOG_FILE_NAME", "RecordFile", "RunLog"]

LOG_FILE_NAME = "ai_player.log"
#: The ACTION LOG (JSON lines, one per record), next to the run's log.
ACTION_LOG_FILE_NAME = "actions.jsonl"


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


class RecordFile:
    """An append-only file of one-line records in the run directory. No run directory, no file: the
    records are then dropped (a GUI start has no run directory; the run itself is unaffected). Each
    append opens, writes and closes, so a killed process leaves every record it finished."""

    def __init__(self, run_dir: Path | None, name: str = ACTION_LOG_FILE_NAME) -> None:
        self._path: Path | None = None
        if run_dir is not None:
            run_dir.mkdir(parents=True, exist_ok=True)
            self._path = run_dir / name
        self._written = 0

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def written(self) -> int:
        """How many records reached the file."""
        return self._written

    def append(self, record: str) -> None:
        if self._path is None:
            return
        if "\n" in record:
            raise ValueError("a record is ONE line: a newline inside it would split it in two")
        try:
            with open(self._path, "a", encoding="utf-8", errors="replace") as handle:
                handle.write(record + "\n")
            self._written += 1
        except OSError as error:
            try:
                print(f"[AI-LOG] could not append to {self._path}: {error}", file=sys.stderr, flush=True)
            except Exception:
                pass
