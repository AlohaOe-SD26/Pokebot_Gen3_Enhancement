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
clones this repository ONCE (updates are incremental — only the diff is
ever downloaded), detects and repairs any modified/corrupted/deleted
tracked file via git (never touching your profiles or saves), handles the
game ROM (verifies the repo's copy against the bot's known-good list, or
copies in a `.gba` placed next to the script), and pre-installs only the
dependencies that are actually missing. Every run writes a full trace to
`install.log`, ends with a per-step ✓/⚠/✗ summary, and is safe to re-run
anytime — that IS the update and repair mechanism.

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

## Running the `#24-maintain` A/B batch (no console knowledge needed)

**Double-click `Run-Maintain-AB-Batch.bat` in this folder.** It works on any PC and
from any folder — it locates itself, so the repo can live anywhere.

It runs the experiment as two batches back to back and handles the part that is
easy to get wrong:

| arm | environment |
|---|---|
| 1 — ON | `POKEBOT_MAINTAIN=1` |
| 2 — OFF | `POKEBOT_MAINTAIN` removed entirely (the shipped default) |

⛔ **That variable is the whole reason this script exists.** In a normal command
window, setting it keeps it set for the rest of that window's life. If arm 2
inherits it, both arms are really arm 1, the results look identical, and that
reads as *"the feature does nothing"* — a false refutation, which is worse than no
data. The script clears it explicitly rather than trusting it was never set, and
this was **verified**: with a stale `POKEBOT_MAINTAIN` deliberately left in the
environment beforehand, arm 1 saw `1` and arm 2 saw empty.

It also forces `--build sandbox` (the custom build carries no telemetry, so a
batch against it cannot answer the question), gives both arms the same lanes and
minutes so no difference can be blamed on one arm getting more time, and writes
`ARM-ON.txt` / `ARM-OFF.txt` into each result folder so the pairing cannot be lost.

Defaults are **8 lanes, 180 minutes per arm** (~6 hours total). For a shorter run:

    Run-Maintain-AB-Batch.bat 4 60

At the end it prints the two result folder names — send those to Claude.
