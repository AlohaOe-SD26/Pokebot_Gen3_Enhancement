# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-17

## Current state
Punch-list #4 (installer) is DONE: `install.py` at repo root = one-script
install/update/heal (git-driven; tested on this machine incl. fresh-clone,
corrupt→heal, full dep install into Python 3.12; see 06-DECISIONS-LOG).
Dependencies + libmgba are now installed on THIS machine, so the bot is
ready to launch here as soon as a ROM is added to `custom-pokebot/roms/`.
Root README.md added (install + layout).
Punch-list #3 (custom automations) is CODE-COMPLETE but not live-verified:
`custom-pokebot/plugins/custom_modes_loader.py` auto-registers custom bot
modes from `custom-pokebot/plugins/custom_modes/`; first mode is
"Patrol (Custom)" (waypoint-loop shiny hunt, per-profile `patrol.yml`).
Verified: structural smoke test + REAL-import discovery under Python 3.12
(actual bot modules; PatrolMode registers). Only a live gameplay run
(needs a ROM + profile) remains to close #3. How-to:
`custom-pokebot/DOCUMENTATION/01-custom-automations.md`.

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
  restructured to the two-folder fork layout with the daily upstream-sync
  ritual (CLAUDE.md directive + UPDATE-LOG.md), then ran a full
  adversarial verification of all seven docs (~975 claims, 39 errors
  fixed — docs are now build-on-able; upstream bugs found are KI-1..KI-3).

## In progress (and how far along)
- Nothing mid-flight.

## If stopped mid-task
- Nothing pending — last stop was clean.

## Next steps (in order)
1. DAILY (every new calendar day, session start): upstream update check —
   ritual in CLAUDE.md "Daily upstream update check" / UPDATE-LOG.md header.
2. #3 close-out: live-verify "Patrol (Custom)" — on a machine with the
   user's ROM: `cd custom-pokebot; python pokebot.py` (deps self-install,
   needs Python 3.11-3.13), create a profile, stand on a grassy map, write
   `patrol.yml` (2-3 nearby waypoints) into the profile folder, select the
   mode, confirm it loops and handles an encounter. Then mark #3 done.
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
