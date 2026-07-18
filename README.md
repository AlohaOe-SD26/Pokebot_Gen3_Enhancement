# Pokebot_Gen3_Enhancement

An enhanced, deeply documented fork of
[40Cakes/pokebot-gen3](https://github.com/40Cakes/pokebot-gen3) — a Python
shiny-hunting bot for Gen-3 Pokémon games (Ruby/Sapphire/Emerald/
FireRed/LeafGreen) that drives an embedded mGBA emulator.

## Install / update / repair — one script

```
python install.py              # install (fresh machine), update, and heal
python install.py --check-only # report state, change nothing
python install.py --yes        # unattended (auto-confirm, never launches)
```

`install.py` runs on any Python 3.8+ and takes care of everything else:
finds (or offers to install) the 64-bit Python 3.11–3.13 the bot needs,
clones/updates this repository, detects and repairs modified or corrupted
bot files via git (never touching your profiles, saves, or ROMs), and
pre-installs the bot's dependencies. Re-run it anytime.

ROMs are not included — put your own `.gba` dumps in `custom-pokebot/roms/`.

## Repository layout

| Folder | What it is |
|---|---|
| `custom-pokebot/` | **Our enhanced fork** — the bot you run. Custom automations live in `plugins/custom_modes/`; every difference vs upstream is logged in `DIVERGENCE-LOG.md`. |
| `40cakes repo/` | Pristine upstream mirror + complete developer documentation of the original (`DOCUMENTATION/`), synced with upstream on a daily-check ritual (`UPDATE-LOG.md`). |
| `PROJECT KNOWLEDGE/` | Project management docs (vision, architecture, punch list, handoff, logs). |
| `Pokemon_Emerald_AI_Notes.md` | Findings transferable to the sibling Pokémon Emerald AI project. |

## Running the bot

```
cd custom-pokebot
python pokebot.py              # dashboard window (default); deps self-install on first run
python pokebot.py --classic-gui   # upstream's original window
```

**The bot's window IS a dashboard** (our native GUI, default since
2026-07-18): resizable emulator video plus a tool column with bot-mode and
speed controls, encounter stat tiles, party HP bars, and an event log.
**Handheld mode** (built for the ROG Ally X): `F11` or double-click the
video for fullscreen; the semi-transparent Pokéball button (or `H`) slides
the tools in as an overlay drawer; "Hide"/`Esc` collapses it.

**Web dashboard** (optional remote viewing): with the HTTP server enabled
(`http.yml`), open http://127.0.0.1:8888/static/custom-ui/index.html for
the same layout in a browser.

See `40cakes repo/DOCUMENTATION/00-CODEBASE-OVERVIEW.md` for how the whole
program works, and `custom-pokebot/DOCUMENTATION/` for our enhancements.
