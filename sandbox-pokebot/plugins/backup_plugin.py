"""
Sandbox addition (A1): automatic backup triggers.

- Every logged SHINY encounter -> immediate backup (reason "shiny"),
  if `auto_on_shiny` is enabled in backup.yml.
- A frame listener fires a timed backup once `interval_hours` of WALL time
  has passed since the newest local backup (0 disables). Checks are
  throttled to once per 3600 frames AND at most once per minute of wall
  time (so fast-forwarded emulation does not check more often), keeping
  the per-frame cost at a counter increment.

Both triggers are wrapped so that a failing backup can never take the
frame loop down (an uncaught listener exception would kick the bot into
Manual mode and stop the hunt).

Manual backups + restore live in the dashboard GUI ("BACKUPS" card).
Configuration: backup.yml (bot root, or per-profile override).
"""

import logging
import time
from typing import TYPE_CHECKING, Iterable

from modules.plugin_interface import BotPlugin

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo
    from modules.modes import BotListener, BotMode, FrameInfo


class _IntervalBackupListener:
    """BotListener (duck-typed): timed auto-backups while the bot runs."""

    CHECK_EVERY_FRAMES = 3600  # 1 minute of emulated time at 1x speed
    MIN_SECONDS_BETWEEN_CHECKS = 60.0  # wall-time floor for fast-forwarded emulation

    def __init__(self):
        self._frame_counter = 0
        self._last_check_at = 0.0

    def handle_frame(self, bot_mode: "BotMode", frame: "FrameInfo") -> None:
        self._frame_counter += 1
        if self._frame_counter < self.CHECK_EVERY_FRAMES:
            return
        self._frame_counter = 0

        now = time.monotonic()
        if now - self._last_check_at < self.MIN_SECONDS_BETWEEN_CHECKS:
            return
        self._last_check_at = now

        try:
            from modules import backup_manager
            from modules.context import context

            if context.profile is None:
                return
            config = backup_manager.load_config(context.profile.path)
            try:
                interval_hours = float(config.get("interval_hours") or 0)
            except (TypeError, ValueError):
                interval_hours = 0.0
            if not config.get("enabled", True) or interval_hours <= 0:
                return
            elapsed = backup_manager.seconds_since_last_backup(context.profile.path.name)
            if elapsed is None or elapsed >= interval_hours * 3600:
                backup_manager.create_backup(context.profile.path, reason="auto")
        except Exception:
            # A failed backup must never interfere with the frame loop.
            logging.getLogger("backup").exception("timed auto-backup failed")


class BackupPlugin(BotPlugin):
    def get_additional_bot_listeners(self) -> Iterable["BotListener"]:
        return [_IntervalBackupListener()]

    def on_logging_encounter(self, encounter: "EncounterInfo") -> None:
        try:
            if not encounter.pokemon.is_shiny:
                return
            from modules import backup_manager
            from modules.context import context

            if context.profile is None:
                return
            if backup_manager.load_config(context.profile.path).get("auto_on_shiny", True):
                backup_manager.create_backup(context.profile.path, reason="shiny")
        except Exception:
            # A failed backup must never interfere with encounter handling.
            logging.getLogger("backup").exception("shiny auto-backup failed")
