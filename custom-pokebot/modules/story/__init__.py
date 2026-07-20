"""Story-mode support package.

Chapter 24 (#24) — the story auto-player that plays Emerald from a fresh save
(or continues an existing one) toward the Elite Four and beyond.

This package is being built in verifiable chunks (see
``PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md`` §11). Chunk 1 — implemented here —
is a **read-only progress detector**: it reads a save's event flags/vars and
reports which ordered story Chapter the save is at, plus a human-readable
progress summary. Nothing here writes to the game; it is safe to run against a
real save.
"""

from modules.story.progress import (
    StoryProgress,
    detect_progress,
    detect_from_save_data,
    detect_live,
)

__all__ = [
    "StoryProgress",
    "detect_progress",
    "detect_from_save_data",
    "detect_live",
]
