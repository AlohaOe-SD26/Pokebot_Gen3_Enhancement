"""The AI player: a program that plays Pokemon Emerald ITSELF (USER RULINGS 35-37).

WHY THIS PACKAGE IS SHAPED THE WAY IT IS
----------------------------------------
* The AI plays the game with its OWN code: navigation, battles, menus and decisions. The story bot
  is only its teacher (RULING 35), so nothing from the bot's brain may run inside the AI's play loop.
* It is built from day one to become a single standalone program that loads the ROM itself
  (RULING 37 Q1). So it reaches the game framework ONLY through thin adapters in
  `ai_player/platform/` (and, later, an eyes facade), it hard-codes no path to the bot, and the one
  file inside the framework (`sandbox-pokebot/plugins/custom_modes/ai_player_mode.py`) is a hook
  with no logic in it.
* Purity is enforced by gates, not prose (CLAUDE.md session discipline rule 6):
  `ai_player/gates/check_purity.py` (static) and the `[AI-PURITY]` counters (live).

See `ai_player/README.md` for how to run it and the purity contract.

‼ Never put the `ai_player/` folder ITSELF on `sys.path`: its `platform` subpackage would then
shadow the standard library's `platform` module. The repo root (the folder that CONTAINS
`ai_player/`) is what goes on the path.
"""

#: The bot-mode name the hook registers and the launcher selects with `-m`. The hook file repeats
#: this literal (it must answer `name()` before `ai_player` is importable); if the two ever differ,
#: `pokebot.py` rejects the `-m` choice and the run fails loudly at startup instead of silently.
MODE_NAME = "AI Player"

__all__ = ["MODE_NAME"]
