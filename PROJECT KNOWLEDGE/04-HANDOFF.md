# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-17

## Current state
This project documents and enhances 40Cakes/pokebot-gen3 (Python
shiny-hunting bot driving Gen-3 Pokémon games via libmgba). Layout
(user directive — details in CLAUDE.md "Project rules"):
- `40cakes repo/pokebot-gen3/` — PRISTINE upstream mirror (git subtree,
  remote `upstream-pokebot`, currently upstream commit `5dd898f8`).
  Checked against upstream DAILY; sync record: `40cakes repo/UPDATE-LOG.md`.
- `40cakes repo/DOCUMENTATION/` — complete verified developer docs of the
  ORIGINAL program (00-overview + five layer docs, ~2,400 lines,
  file:line refs); superseded versions go to `_history/`.
- `custom-pokebot/` — OUR fork (exact copy of `5dd898f8`, no divergences
  yet; every future divergence logged in `DIVERGENCE-LOG.md`, custom-only
  docs in its `DOCUMENTATION/`).
- `Pokemon_Emerald_AI_Notes.md` (root) — transfer notes for the sibling
  Pokémon Emerald AI project.
No code enhancements built yet.

## What was just done (last session)
- Vendored upstream (#1), completed the deep documentation pass (#2),
  then restructured to the two-folder fork layout with the daily
  upstream-sync ritual (CLAUDE.md directive + UPDATE-LOG.md).

## In progress (and how far along)
- Nothing mid-flight.

## If stopped mid-task
- Nothing pending — last stop was clean.

## Next steps (in order)
1. DAILY (every new calendar day, session start): upstream update check —
   ritual in CLAUDE.md "Daily upstream update check" / UPDATE-LOG.md header.
2. #3 Custom automations: read `40cakes repo/DOCUMENTATION/03-bot-modes-
   and-battle.md` (mode contract + walkthrough) and `01-core-runtime-and-
   emulator.md` (plugin system); design the first custom bot mode with the
   user; build it in `custom-pokebot/plugins/`.
3. #4 Installer script: design against
   `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md` + bootstrap facts in
   `40cakes repo/DOCUMENTATION/05-stats-config-data-tests.md`; get user
   sign-off on the provisional decision in 06-DECISIONS-LOG.
4. #5 Custom interface: start from the endpoint reference + gap list in
   `40cakes repo/DOCUMENTATION/04-interfaces-gui-web-streaming.md`.

## How to run / build / test
```powershell
cd custom-pokebot                      # our fork ("40cakes repo/pokebot-gen3" = pristine upstream)
python pokebot.py                      # first run self-installs deps + libmgba
python pokebot.py <profile> -m Spin
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
```

## Gotchas / unpushed work
- NEVER edit files under `40cakes repo/pokebot-gen3/` — it's the pristine
  mirror; all enhancement work happens in `custom-pokebot/`.
- ROMs/profiles/saves are user-supplied and must never be committed
  (each copy's .gitignore already excludes them).
- Upstream pull (only during the daily ritual, mirror only):
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`
- Upstream's `pokebot.spec` (PyInstaller) is stale/broken — documented in
  docs 05; don't assume packaged builds work.
- The bot's auto-updater self-disables for git checkouts (good for us).
