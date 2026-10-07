"""Adapters between the AI player and the game framework it currently runs inside.

WHY A SEPARATE SUBPACKAGE: everything framework-specific lives here, so that when the AI becomes a
standalone program (RULING 37 Q1) only these files change. The brain (`ai_player/mode.py` today, and
the world model, navigator and so on later) talks to the game only through these adapters, and only
through the names each adapter lists in its `__all__` (the purity gate refuses anything else).

  controller.py   the ONLY place the AI presses buttons or lets frames pass
  isolation.py    removes the framework listeners the AI does not own, and restores them on exit
  attribution.py  the instrument: counts every press, write, load, frame and bot-code call by who
                  issued it, audits what reached the emulator (latched keys, memory between frames),
                  and writes the run's verdict file
  lifecycle.py    the single exit door: a give-up, a crash or a timeout ends the PROCESS, never parks it
  launcher.py     the CLI side (launcher process only): gates the package, prepares a profile, runs
                  `pokebot.py` under a soft and a hard wall clock, and grades the verdict file

`ai_player/gates/check_purity.py` holds the per-file doors into the framework, and pins each
adapter's exported names (rule g): a new adapter or export here is a reviewed gate change.
"""
