"""
Registers the game-cheat frame listener (SANDBOX feature). The cheats
themselves live in modules/game_cheats.py and are toggled/triggered from the
GUI's CHEATS card; this listener drives the PERSISTENT toggles:

  * throttled overworld upkeep (infinite money, auto-heal party)
  * wild-encounter overrides at battle start (force species / guaranteed shiny)

Battle-start detection mirrors the stock ForceShinyEncounterListener
(modules/gui/debug_menu.py): the `Task_BattleStart` task fires once as a battle
begins, so the override runs exactly once per encounter.
"""

from typing import TYPE_CHECKING, Iterable

from modules.game_cheats import cheat_manager
from modules.plugin_interface import BotPlugin
from modules.modes import BotListener

if TYPE_CHECKING:
    from modules.modes import BotMode, FrameInfo
    from modules.profiles import Profile

# Overworld toggles don't need per-frame precision; every ~15 rendered frames
# is plenty and keeps the cost negligible.
_TOGGLE_INTERVAL_FRAMES = 15


class GameCheatsListener(BotListener):
    def __init__(self) -> None:
        self._frames = 0
        self._battle_start_handled = False

    def handle_frame(self, bot_mode: "BotMode", frame: "FrameInfo") -> None:
        # Wild-encounter overrides — edge-triggered on Task_BattleStart.
        if frame.task_is_active("Task_BattleStart"):
            if not self._battle_start_handled:
                self._battle_start_handled = True
                cheat_manager.on_wild_battle_start()
        else:
            self._battle_start_handled = False

        # Persistent overworld toggles — throttled.
        self._frames += 1
        if self._frames >= _TOGGLE_INTERVAL_FRAMES:
            self._frames = 0
            cheat_manager.apply_persistent_toggles()


class GameCheatsPlugin(BotPlugin):
    def on_profile_loaded(self, profile: "Profile") -> None:
        cheat_manager.load_config()

    def get_additional_bot_listeners(self) -> Iterable["BotListener"]:
        return [GameCheatsListener()]
