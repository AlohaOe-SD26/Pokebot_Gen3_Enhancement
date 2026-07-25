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
├── CLAUDE.md                      # Kit directives + project rules (two-folder layout, daily upstream check)
├── Pokemon_Emerald_AI_Notes.md    # Cross-project transfer notes (Emerald AI project)
├── PROJECT KNOWLEDGE/
│   ├── 00–08 kit docs             # vision, architecture, punch list, handoff, …
│   └── REFERENCE-INSTALLER-PATTERN.md  # Nick's installer-as-codebase spec
├── 40cakes repo/                  # ★ everything about the ORIGINAL program
│   ├── UPDATE-LOG.md              # append-only upstream sync record + daily-check ritual
│   ├── DOCUMENTATION/             # deep developer docs of the original bot
│   │   ├── 00-CODEBASE-OVERVIEW.md         # start here
│   │   ├── 01-core-runtime-and-emulator.md
│   │   ├── 02-game-state-and-memory.md
│   │   ├── 03-bot-modes-and-battle.md
│   │   ├── 04-interfaces-gui-web-streaming.md
│   │   ├── 05-stats-config-data-tests.md
│   │   └── _history/              # versioned snapshots of superseded docs
│   └── pokebot-gen3/              # PRISTINE upstream mirror (git subtree, commit 5dd898f8)
│       ├── pokebot.py             # entry point + self-bootstrap
│       ├── modules/               # all bot code (~59 core modules)
│       │   ├── modes/             # 23 bot automations + BotMode contract
│       │   ├── battle_strategies/ # battle decision engine
│       │   ├── gui/  web/  config/  data/  built_in_plugins/
│       ├── plugins/  tests/  wiki/
└── custom-pokebot/                # ★ OUR enhanced fork (from upstream 5dd898f8)
    ├── DIVERGENCE-LOG.md          # append-only: every intentional diff vs upstream
    ├── DOCUMENTATION/             # docs about the CUSTOM parts only
    ├── modules/gui/dashboard_gui.py   # native dashboard GUI (default window)
    ├── modules/web/static/custom-ui/  # browser dashboard (opt-in remote viewing)
    ├── plugins/custom_modes/      # drop-in custom bot modes (Patrol, …)
    └── (otherwise same program layout as the mirror)
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
Full walkthrough: `40cakes repo/DOCUMENTATION/00-CODEBASE-OVERVIEW.md`.

**‼ The controller stack is FLAT, not nested.** `main_loop` advances only the
TOP generator, so a bot mode and a battle handler pushed by `BattleListener` are
SIBLINGS — an exception raised by battle code propagates to `main_loop` (which
sets Manual), never through the mode's own `try`. A mode therefore cannot catch
or recover from a battle-handler failure by any arrangement of `except`. Faults
that a mode should survive travel by an explicit channel instead:
`modules/battle_fault.py` (sandbox) — the battle handler records the reason and
returns; a mode that declares `handles_battle_faults = True` claims it on its
next frame and re-raises inside its own recoverable scope. Opt-in on purpose;
see 06-DECISIONS-LOG 2026-07-25.

## Key modules
See the per-layer docs in `40cakes repo/DOCUMENTATION/` — the
authoritative module reference (intent + mechanics + file:line refs).
Custom-only behavior is documented in `custom-pokebot/DOCUMENTATION/`.

## External dependencies & services
- **ROMs**: user-supplied in each copy's `roms/`, SHA-1 whitelisted,
  never committed.
- **Profiles** (`<copy>/profiles/<name>/`): save, savestates, per-profile
  config, `stats.db` — never committed.
- GitHub (upstream releases for the stock auto-updater; disabled for git
  checkouts like ours), Discord webhooks (optional), OBS websocket
  (optional).
- Upstream remote: `upstream-pokebot` → 40Cakes/pokebot-gen3. Daily check
  + pull ritual: see `40cakes repo/UPDATE-LOG.md` header. Pull command:
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`.

## How to run / build / test
```powershell
cd custom-pokebot          # our fork; use "40cakes repo/pokebot-gen3" to run pristine upstream
python pokebot.py                      # dashboard GUI (default); first run self-installs deps
python pokebot.py <profile> -m Spin    # straight into a mode
python pokebot.py <profile> --classic-gui   # upstream's original window (OpenGL/stepping)
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
python ..\install.py                   # repo root: one-script install/update/heal
```
