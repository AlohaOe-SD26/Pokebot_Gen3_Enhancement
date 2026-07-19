"""
Registers the XInput gamepad listener (sandbox, punch-list #10) so an
Xbox-style controller — e.g. the ROG Ally X's built-in pad — plays the game
in Manual mode. The actual polling/mapping lives in modules/gamepad.py;
this plugin just puts its frame listener into the bot's listener list.
"""

from typing import TYPE_CHECKING, Iterable

from modules.gamepad import listener
from modules.plugin_interface import BotPlugin

if TYPE_CHECKING:
    from modules.modes import BotListener


class GamepadPlugin(BotPlugin):
    def get_additional_bot_listeners(self) -> Iterable["BotListener"]:
        return [listener]
