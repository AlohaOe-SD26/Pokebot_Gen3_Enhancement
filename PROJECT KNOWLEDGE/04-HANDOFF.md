# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-17

## Current state
This project documents and enhances 40Cakes/pokebot-gen3 (Python
shiny-hunting bot driving Gen-3 Pokémon games via libmgba). The upstream
source is vendored at `pokebot-gen3/` (git subtree, upstream commit
`5dd898f8`, remote `upstream-pokebot`). The full deep-documentation pass is
COMPLETE: `PROJECT KNOWLEDGE/CODEBASE/00-CODEBASE-OVERVIEW.md` is the entry
point to five verified layer docs (~2,400 lines with file:line refs).
Cross-project findings for the sibling Pokémon Emerald AI project live in
`Pokemon_Emerald_AI_Notes.md` (repo root). No code enhancements built yet.

## What was just done (last session)
- Vendored upstream via git subtree (#1) and completed the deep
  documentation pass (#2): CODEBASE docs 00–05, Emerald AI notes, vision/
  architecture/punch-list filled in, installer-pattern reference copied to
  `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md`, decisions logged
  (subtree vendoring; provisional installer-pattern adaptation).

## In progress (and how far along)
- Nothing mid-flight.

## If stopped mid-task
- Nothing pending — last stop was clean.

## Next steps (in order)
1. #3 Custom automations: read `CODEBASE/03-bot-modes-and-battle.md` (mode
   contract + walkthrough) and `01-core-runtime-and-emulator.md` (plugin
   system), then design the first custom bot mode with the user.
2. #4 Installer script: design against
   `REFERENCE-INSTALLER-PATTERN.md` + the current-bootstrap facts in
   `CODEBASE/05-stats-config-data-tests.md`; get user sign-off on the
   provisional decision in 06-DECISIONS-LOG (adapt pattern, not literal
   base64).
3. #5 Custom interface: start from the endpoint reference + gap list in
   `CODEBASE/04-interfaces-gui-web-streaming.md`.

## How to run / build / test
```powershell
cd pokebot-gen3
python pokebot.py                      # first run self-installs deps + libmgba
python pokebot.py <profile> -m Spin
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
```

## Gotchas / unpushed work
- ROMs/profiles/saves are user-supplied and must never be committed
  (upstream .gitignore already excludes them).
- Upstream updates: `git subtree pull --prefix pokebot-gen3 upstream-pokebot main --squash`.
- Upstream's `pokebot.spec` (PyInstaller) is stale/broken — known upstream
  issue, documented in CODEBASE/05; don't assume packaged builds work.
- The bot's auto-updater self-disables for git checkouts (good for us).
