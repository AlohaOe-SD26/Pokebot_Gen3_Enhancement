"""
Sandbox addition (#12): shiny alerts.

When a shiny encounter is logged, this plugin can:
  - show a desktop toast notification (notify-py — already a bot dependency),
  - play a sound (Windows system sound, asynchronous),
  - optionally auto-pause the bot (switch to Manual) so the shiny stays
    on screen for you.

Configuration: `alerts.yml` at the bot root, whole-file-overridden by
`profiles/<name>/alerts.yml` (same layering as backup.yml). Missing or
malformed config falls back to safe defaults key by key.

Every path is wrapped: a failing toast/sound must never disturb encounter
handling or the frame loop. Toasts are sent non-blocking (notify-py spawns
its own worker), and the system beep is asynchronous by nature.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from modules.plugin_interface import BotPlugin
from modules.runtime import get_base_path

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo

CONFIG_FILE_NAME = "alerts.yml"

DEFAULT_CONFIG: dict = {
    "enabled": True,
    "toast": True,        # desktop notification on shiny
    "sound": True,        # audible ding on shiny (Windows)
    "auto_pause": False,  # switch to Manual so the shiny sits on screen
}

_logger = logging.getLogger("alerts")


def load_config(profile_path: "Path | None" = None) -> dict:
    """alerts.yml at bot root, whole-file-overridden per profile."""

    def _read(path: Path) -> "dict | None":
        try:
            if path.is_file():
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
                _logger.warning("config %s is not a mapping; ignored", path)
        except Exception as error:
            _logger.warning("config %s unreadable (%s); using defaults", path, error)
        return None

    raw = None
    if profile_path is not None:
        raw = _read(Path(profile_path) / CONFIG_FILE_NAME)
    if raw is None:
        raw = _read(get_base_path() / CONFIG_FILE_NAME)
    if raw is None:
        raw = {}
    return {**DEFAULT_CONFIG, **raw}


def _send_toast(pokemon_name: str, details: str) -> None:
    from notifypy import Notify

    toast = Notify()
    toast.application_name = "PokéBot"
    toast.title = f"✨ Shiny {pokemon_name}! ✨"
    toast.message = details
    toast.send(block=False)


def _play_sound() -> None:
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONASTERISK)  # asynchronous
    except ImportError:
        pass  # non-Windows: no built-in beep; toast still fires


class ShinyAlertPlugin(BotPlugin):
    def on_logging_encounter(self, encounter: "EncounterInfo") -> None:
        try:
            if not encounter.pokemon.is_shiny:
                return
            from modules.context import context

            profile_path = context.profile.path if context.profile is not None else None
            config = load_config(profile_path)
            if not config.get("enabled", True):
                return

            pokemon = encounter.pokemon
            if config.get("toast", True):
                try:
                    details = f"SV {pokemon.shiny_value} · after this phase's hunting — go catch it!"
                    _send_toast(str(pokemon.species.name), details)
                except Exception:
                    _logger.exception("toast failed")
            if config.get("sound", True):
                try:
                    _play_sound()
                except Exception:
                    _logger.exception("sound failed")
            if config.get("auto_pause", False):
                try:
                    context.set_manual_mode()
                except Exception:
                    _logger.exception("auto-pause failed")
        except Exception:
            # Alerts must never interfere with encounter handling.
            _logger.exception("shiny alert failed")
