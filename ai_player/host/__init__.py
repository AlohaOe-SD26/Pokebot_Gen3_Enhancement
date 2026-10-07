"""The host: everything that ties the AI player to the game framework it currently runs inside.

WHY A SEPARATE SUBPACKAGE: the brain (`ai_player/mode.py`, and the world model, navigator and so on
later) is framework-free; it sees the game only through abstract interfaces. Everything that knows
about the framework lives here, so that when the AI becomes a standalone program (RULING 37 Q1) only
these files change. It is called `host`, not `platform`, because a subpackage named `platform` would
shadow the standard library's `platform` module for anything that put `ai_player/` on `sys.path`
(the adversarial review's finding 10).

  session.py      the run: start-up refusals, the guard callback (park, budget, wall clock, Ctrl+C),
                  listener wiring, and driving the brain one frame at a time
  controller.py   the ONLY place the AI presses buttons or lets frames pass (the brain's `Controls`)
  isolation.py    removes the framework listeners the AI does not own, owns the framework's
                  listener-rebuild door while the AI runs, and restores both on exit
  attribution.py  the instrument: counts every press, write, load, clock change, frame and bot-code
                  call by who issued it, audits what reached the emulator and that isolation held,
                  and writes the run's verdict file
  lifecycle.py    the single exit door: every ending ends the PROCESS with a verdict, never parks it
  launcher.py     the CLI side (launcher process only): gates the package, prepares a profile, runs
                  `pokebot.py` under a soft and a hard wall clock, and grades the verdict file

`ai_player/gates/check_purity.py` holds the per-file doors into the framework, and pins each host
module's exported names (rule g): a new host module or export here is a reviewed gate change. This
package file is deliberately NOT sealed (`attribution.seal_module`): the import system sets each
submodule on it as an attribute.
"""
