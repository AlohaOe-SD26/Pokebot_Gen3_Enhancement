# Architecture — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Describes how it is built TODAY.

## Tech stack
- **Python 3.11–3.13 (64-bit)** — vendored bot targets 3.12; `black` formatting.
- **libmgba-py 0.2.0-2** (CFFI bindings to mGBA) — the emulator core,
  auto-downloaded into `pokebot-gen3/mgba/` on first run.
- Key libraries: Tkinter (GUI), aiohttp (HTTP API/SSE), SQLite via stdlib
  (stats), confz/pydantic (YAML config schemas), Pillow, numpy, PyYAML.
- Deps are declared in `pokebot-gen3/requirements.py` (a Python list, not
  requirements.txt) and self-installed at first launch.

## Folder / module map
```
Pokebot_Gen3_Enhancement/
├── CLAUDE.md                      # Project Kit standing directives
├── Pokemon_Emerald_AI_Notes.md    # Cross-project transfer notes (Emerald AI project)
├── PROJECT KNOWLEDGE/
│   ├── 00–08 kit docs             # vision, architecture, punch list, handoff, …
│   ├── REFERENCE-INSTALLER-PATTERN.md  # Nick's installer-as-codebase spec
│   └── CODEBASE/                  # ★ deep developer docs of the bot
│       ├── 00-CODEBASE-OVERVIEW.md         # start here
│       ├── 01-core-runtime-and-emulator.md
│       ├── 02-game-state-and-memory.md
│       ├── 03-bot-modes-and-battle.md
│       ├── 04-interfaces-gui-web-streaming.md
│       └── 05-stats-config-data-tests.md
└── pokebot-gen3/                  # ★ vendored upstream (git subtree, commit 5dd898f8)
    ├── pokebot.py                 # entry point + self-bootstrap
    ├── requirements.py, updater.py, pokebot.spec
    ├── modules/                   # all bot code (~59 core modules)
    │   ├── modes/                 # 23 bot automations + BotMode contract
    │   ├── battle_strategies/     # battle decision engine
    │   ├── gui/                   # Tkinter frontend + debug tabs, headless frontend
    │   ├── web/                   # aiohttp API + SSE + stream overlay assets
    │   ├── config/                # confz YAML schemas
    │   ├── data/                  # species/moves/types JSONs, pret symbol tables
    │   └── built_in_plugins/
    ├── plugins/                   # user plugin drop-in dir (our custom automations go here)
    ├── tests/                     # real-emulator E2E tests (need ROM dumps)
    └── wiki/                      # upstream user docs
```

## How the pieces talk
Single-threaded frame-locked loop (`modules/main.py:36`): snapshot state →
run frame listeners → advance the top generator on
`context.controller_stack` (bot modes/battle handlers are generators; each
`yield` = one frame with given button state) → `run_single_frame()`. The
game is paused while Python decides. The `context` singleton
(`modules/context.py`) wires emulator, profile, config, mode, frontend.
Observers (GUI, HTTP API, Discord) consume frame-stamped state-cache
snapshots; the web thread never reads emulator memory directly.
Full walkthrough: `PROJECT KNOWLEDGE/CODEBASE/00-CODEBASE-OVERVIEW.md`.

## Key modules
See the per-layer docs in `PROJECT KNOWLEDGE/CODEBASE/` — they are the
authoritative module reference (intent + mechanics + file:line refs).

## External dependencies & services
- **ROMs**: user-supplied in `pokebot-gen3/roms/`, SHA-1 whitelisted,
  never committed.
- **Profiles** (`pokebot-gen3/profiles/<name>/`): save, savestates,
  per-profile config, `stats.db` — never committed.
- GitHub (upstream releases for the stock auto-updater; disabled for git
  checkouts like ours), Discord webhooks (optional), OBS websocket
  (optional).
- Upstream remote: `upstream-pokebot` → 40Cakes/pokebot-gen3. Pull
  updates: `git subtree pull --prefix pokebot-gen3 upstream-pokebot main --squash`.

## How to run / build / test
```powershell
cd pokebot-gen3
python pokebot.py                      # first run: self-installs deps + libmgba, profile GUI
python pokebot.py <profile> -m Spin    # straight into a mode
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
```
