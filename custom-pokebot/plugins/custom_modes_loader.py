"""
Custom-modes loader plugin (part of the Pokebot_Gen3_Enhancement fork).

The stock plugin loader (modules/plugins.py:21) imports every top-level .py
file in `plugins/` and requires each one to contain a BotPlugin subclass.
This plugin is that subclass — and it turns the `plugins/custom_modes/`
subfolder (which the stock loader ignores, as it only looks at files) into
a drop-in directory for custom bot modes:

    plugins/custom_modes/<anything>.py  →  its BotMode subclasses appear in
                                           the bot-mode dropdown automatically

To add a new automation: copy `custom_modes/patrol.py` as a starting point,
give your class a unique `name()`, and restart the bot. No upstream files
need to be touched. Files starting with `_` are skipped.
"""

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from modules.plugin_interface import BotPlugin

if TYPE_CHECKING:
    from modules.modes import BotMode


class CustomModesPlugin(BotPlugin):
    def get_additional_bot_modes(self) -> Iterable[type["BotMode"]]:
        # Imported here rather than at module level: plugins load very early
        # (modules/main.py), before profile selection; modules.modes pulls in
        # large parts of the bot, so we defer until the mode list is built.
        from modules.modes import BotMode

        modes: list[type[BotMode]] = []
        modes_dir = Path(__file__).resolve().parent / "custom_modes"
        if not modes_dir.exists():
            return modes

        for file in sorted(modes_dir.glob("*.py")):
            if file.name.startswith("_"):
                continue
            module = importlib.import_module(f"plugins.custom_modes.{file.stem}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                # `cls.__module__` check: only register classes DEFINED in the
                # file, not BotMode subclasses it merely imports.
                if issubclass(cls, BotMode) and cls is not BotMode and cls.__module__ == module.__name__:
                    modes.append(cls)
        return modes
