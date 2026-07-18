# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-18

## What this project is
Documents and enhances 40Cakes/pokebot-gen3 (Python shiny-hunting bot
driving Gen-3 Pokémon games via libmgba). Layout (user directive — details
in CLAUDE.md "Project rules"):
- `40cakes repo/pokebot-gen3/` — PRISTINE upstream mirror (git subtree,
  remote `upstream-pokebot`, upstream commit `5dd898f8`). Checked against
  upstream DAILY; sync record: `40cakes repo/UPDATE-LOG.md`.
- `40cakes repo/DOCUMENTATION/` — complete, adversarially verified dev docs
  of the ORIGINAL program (superseded versions go to `_history/`).
- `custom-pokebot/` — OUR fork; every divergence logged in
  `DIVERGENCE-LOG.md`, custom docs in its `DOCUMENTATION/`.
- `Pokemon_Emerald_AI_Notes.md` (root) — transfer notes for the sibling
  Pokémon Emerald AI project.

## Current state
- **#5 custom interface — the program's OWN WINDOW is now the dashboard**
  (user direction 2026-07-18): `custom-pokebot/modules/gui/dashboard_gui.py`
  (`PokebotDashboardGui`, default GUI; `--classic-gui` = upstream window,
  also home of OpenGL/frame-stepping). Resizable letterboxed video + tool
  column (mode/speed/AV, KPI tiles, party HP bars, status, event log);
  handheld mode for ROG Ally X (F11/H/double-click → fullscreen; canvas
  Pokéball opens overlay drawer; Hide/H/Esc closes; per-profile
  persistence in `dashboard_ui.json`). Stock menu bar kept; `-d` debug
  tabs open in a separate Toplevel. VERIFIED on a real run with the
  Emerald ROM (test-dashboard profile, title screen): desktop, handheld,
  drawer, Esc-out, and `--classic-gui` regression all screenshot-confirmed.
  Not yet verified: party/KPI panels with a progressed save; debug
  Toplevel tabs; the user's on-device Ally test. Browser dashboard
  (`modules/web/static/custom-ui/`) remains as opt-in remote viewing
  (auto-open plugin defaults OFF).
- **#4 installer — DONE**: `install.py` (git-driven one-script
  install/update/heal, fully tested). Deps + libmgba installed on this
  machine; the user's Emerald ROM is in `custom-pokebot/roms/` (tracked by
  user ruling — see gotchas), so the bot runs for real here.
- **#3 custom automations — WIP**: framework + "Patrol (Custom)" built,
  real-import verified; awaiting the user's in-game play-test.
- requirements.py (fork) now installs only missing modules; cffi pin
  loosened to `>=1.17.1` (upstream conflict); http.yml template defaults
  enabled (127.0.0.1).

## What was just done (this session, 2026-07-18)
- Daily upstream check (unchanged at `5dd898f8`); pulled the user's ROM
  upload; user ruling logged to keep it tracked.
- Smart dependency bootstrap + dashboard discoverability fixes.
- Built the native dashboard GUI (fork agent; ~860 lines) and verified it
  on a live run; browser auto-open defaulted off per user preference.

## In progress (and how far along)
- #5: native GUI built + machine-verified; awaiting user's real-play test
  (esp. on the Ally) and a progressed save to exercise party/KPI panels.

## If stopped mid-task
- Nothing pending — last stop was clean.

## Next steps (in order)
1. DAILY (every new calendar day, session start): upstream update check —
   ritual in CLAUDE.md "Daily upstream update check" / UPDATE-LOG.md header.
2. User tests the native GUI (`cd custom-pokebot; python pokebot.py` →
   dashboard window; F11 for handheld on the Ally) with a real save, and
   play-tests Patrol (#3): grassy map + `patrol.yml` (2-3 waypoints) in the
   profile folder + select "Patrol (Custom)". Fix whatever they report.
3. After user sign-off: mark #3 done and #5's native-GUI milestone done;
   then #5 v2 backlog (trend charts, shiny log browser, API additions) and
   #6 icebox.

## How to run / build / test
```powershell
cd custom-pokebot                      # our fork ("40cakes repo/pokebot-gen3" = pristine upstream)
python pokebot.py                      # dashboard GUI (native); profile GUI on first run
python pokebot.py <profile> --classic-gui   # upstream's original window
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
python ..\install.py                   # from repo root: update + heal + deps
```

## Gotchas / unpushed work
- The user's Emerald ROM is TRACKED in the (private) repo by explicit user
  ruling (2026-07-18, see 06-DECISIONS-LOG) — do not remove it and do not
  re-raise; but never commit any additional ROMs/saves/profiles.
- NEVER edit files under `40cakes repo/pokebot-gen3/` — pristine mirror;
  all enhancement work happens in `custom-pokebot/`.
- New files under `custom-pokebot/plugins/` need .gitignore negations and
  a `git ls-files` check (ML-2).
- Upstream pull (daily ritual, mirror only):
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`
- Upstream's `pokebot.spec` (PyInstaller) is stale/broken (KI-1); the
  bot's auto-updater self-disables for git checkouts (good for us).
- A gitignored `test-dashboard` profile exists locally for GUI testing.
