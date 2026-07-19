"""
Registers the macro recorder's frame listener (sandbox A2). The recorder
itself lives in modules/macros.py and is armed/stopped from the GUI's
MACROS card; this plugin just makes sure it gets one input sample per frame.
"""

from typing import TYPE_CHECKING, Iterable

from modules.macros import MacroRecorderListener
from modules.plugin_interface import BotPlugin

if TYPE_CHECKING:
    from modules.modes import BotListener


class MacroPlugin(BotPlugin):
    def get_additional_bot_listeners(self) -> Iterable["BotListener"]:
        return [MacroRecorderListener()]
