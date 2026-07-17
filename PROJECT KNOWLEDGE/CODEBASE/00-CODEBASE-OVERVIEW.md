# PokéBot Gen3 — Codebase Overview (start here)

> Entry point for the developer documentation of the vendored
> `pokebot-gen3/` codebase (upstream: https://github.com/40Cakes/pokebot-gen3,
> vendored at upstream commit `5dd898f8`, 2026-07-17). Each layer below has
> its own deep-dive doc in this folder with intent, mechanics, and
> `file:line` references.

## What the program IS

PokéBot Gen3 is a Python shiny-hunting bot that runs Pokémon
Ruby/Sapphire/Emerald/FireRed/LeafGreen inside an embedded mGBA emulator
(via the `libmgba-py` CFFI bindings). It is not a screen-scraper and not a
memory-cheater: it **reads** the emulated game's RAM through the pret
decompilation symbol tables to know the exact world state, and it **acts**
only by pressing GBA buttons, deliberately playing "as a human could."
Its purpose (per upstream) is to turn Gen-3 games into an idle game —
millions of automated encounters hunting shinies — with a GUI, stats
database, Discord notifications, and an HTTP API for stream overlays.

## The one mental model to keep

**Everything happens in a single-threaded, frame-locked loop.**

```
main_loop()  (modules/main.py:36)
  ┌─▶ snapshot state (FrameInfo: game state, active tasks, script stack)
  │   run frame listeners (battle started? egg hatched? whiteout?)
  │   advance the TOP GENERATOR on context.controller_stack by one step
  │     (bot modes and battle handlers are Python generators —
  │      every `yield` means "press these buttons, then advance 1 frame")
  └── emulator.run_single_frame()   (game is PAUSED while Python thinks)
```

The game only moves when the bot lets it. That makes every read race-free
and every input frame-perfect. The global singleton `context`
(`modules/context.py`) wires everything together: emulator, profile,
config, current mode, GUI/headless frontend, stats.

## Layer map (and where each is documented)

| Layer | Doc | What it owns |
|---|---|---|
| Core runtime & emulator | [01-core-runtime-and-emulator.md](01-core-runtime-and-emulator.md) | Entry point, frame loop, `context`, libmgba wrapper, symbols/memory access, profiles, ROM verification, save import, plugin system, self-bootstrap/updater |
| Game-state decoding | [02-game-state-and-memory.md](02-game-state-and-memory.md) | Pokémon struct decryption, party/box/player/map/items readers, tile behaviours & collision, A* pathfinding, mid-battle state, state cache |
| Bot modes & battle engine | [03-bot-modes-and-battle.md](03-bot-modes-and-battle.md) | The `BotMode` contract, all 23 built-in automations, frame listeners, battle strategies, Gen-3 damage/catch math, encounter pipeline |
| Interfaces | [04-interfaces-gui-web-streaming.md](04-interfaces-gui-web-streaming.md) | Tkinter GUI + debug tabs, headless frontend, aiohttp HTTP API + SSE + video stream, Discord webhooks, OBS, debug utilities |
| Stats, config, data, tests, distribution | [05-stats-config-data-tests.md](05-stats-config-data-tests.md) | SQLite stats DB, YAML config schemas, shipped game-data JSONs & symbol tables, E2E test harness, requirements bootstrap + auto-updater + PyInstaller |

## How the pieces talk (10,000-ft data flow)

1. **Boot** — `pokebot.py` parses args, self-installs deps
   (`requirements.py`), picks/creates a **profile** (a folder holding the
   save, savestates, per-profile config, stats DB), verifies the ROM by
   SHA-1, constructs `LibmgbaEmulator`, and hands off to `main_loop()`
   under either the Tkinter GUI or headless frontend.
2. **Every frame** — the loop builds a `FrameInfo` snapshot; listeners
   watch for game events (battle start, evolution, whiteout); the active
   `BotMode` generator advances one step and sets button state.
3. **Encounters** — when a wild/starter/gift Pokémon appears, the
   encounter pipeline decodes it, judges it (shiny? matches custom
   filter?), logs it to SQLite, fires Discord/OBS/plugin notifications,
   and picks a battle action (fight/run/catch) via the battle-strategy
   system.
4. **Observers** — the GUI, HTTP API (JSON state + SSE events + video
   stream), and Discord all read from the same state-cache snapshots; the
   web thread never touches emulator memory directly.

## How to run / test (upstream flow, works in our vendored copy)

```powershell
cd pokebot-gen3
python pokebot.py                # first run self-installs deps + libmgba, opens profile GUI
python pokebot.py <profile> -m Spin   # run a profile straight into a mode
python pokebot.py --headless --no-video   # headless
python -m unittest discover tests      # E2E tests — need specific ROM dumps in roms/
```

Requires 64-bit Python 3.11–3.13 on Windows/Linux/macOS. ROMs are NOT
included and never committed.

## The extension points that matter for OUR enhancements

- **Custom automations** → subclass `BotMode` and register it from a
  plugin (`plugins/*.py`, `get_additional_bot_modes`) — zero upstream
  edits. See doc 03 §mode contract + walkthrough.
- **Custom battle logic** → return a `BattleStrategy` from
  `on_battle_started`, or implement `decide_turn(battle_state)`.
- **Custom interface** → the aiohttp API (doc 04) already provides full
  observation; control gaps (profile select, savestates, frame-accurate
  input, auth) are enumerated in doc 04's enhancement section.
- **Installer** → current bootstrap/updater mechanics documented in docs
  01 & 05; punch-list #4 will design ours against
  `../REFERENCE-INSTALLER-PATTERN.md`.
- **Per-encounter value judgments** → `customcatchfilters.py` per-profile
  hook + `plugin_judge_encounter`.

## Cross-project: Pokémon Emerald AI

Everything transferable to the sibling Emerald-AI project is compiled in
[`Pokemon_Emerald_AI_Notes.md`](../../Pokemon_Emerald_AI_Notes.md) at the
repo root — memory maps, input injection, savestate mechanics, battle
observation space, pathfinding primitives, and the ready-made Gen-3 data
files.
