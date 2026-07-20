"""
Watchdog plugin (fork enhancement, punch-list #22) — wires modules/watchdog
into the bot: a per-frame listener runs the health checks + recovery, and
the encounter hook feeds the stall timer. See modules/watchdog.py for the
detection signals, recovery ladder, and safety guarantees. Config:
watchdog.yml (global + per-profile). Disabled config = fully inert.
"""

from typing import TYPE_CHECKING, Iterable

from modules.plugin_interface import BotPlugin
from modules.modes import BotListener
from modules.watchdog import watchdog

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo
    from modules.modes import BotMode, FrameInfo
    from modules.profiles import Profile


class _WatchdogListener(BotListener):
    def handle_frame(self, bot_mode: "BotMode", frame: "FrameInfo") -> None:
        watchdog.tick()


class WatchdogPlugin(BotPlugin):
    def on_profile_loaded(self, profile: "Profile") -> None:
        # The frame-freeze monitor is a background thread; start it once the
        # profile (and soon the emulator) exists.
        watchdog.start_background_monitor()

    def get_additional_bot_listeners(self) -> Iterable["BotListener"]:
        return [_WatchdogListener()]

    def on_logging_encounter(self, encounter: "EncounterInfo") -> None:
        watchdog.note_encounter()
