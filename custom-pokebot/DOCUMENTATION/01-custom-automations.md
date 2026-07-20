# Custom Automations — how they work and how to add one

> Part of the `custom-pokebot/` fork docs. Upstream mechanics referenced
> here are documented in `../../40cakes repo/DOCUMENTATION/` (docs 01 §plugin
> system and 03 §mode contract).

## What we built

Two pieces turn the fork into a drop-in platform for custom bots:

1. **`plugins/custom_modes_loader.py`** — a stock-API `BotPlugin` whose
   `get_additional_bot_modes()` scans **`plugins/custom_modes/`** and
   registers every `BotMode` subclass defined in any non-underscore `.py`
   file there. The stock plugin loader (`modules/plugins.py:21`) only looks
   at top-level files in `plugins/` — and requires each to contain a
   `BotPlugin` subclass — so a subfolder is the clean place for mode files.
2. **`plugins/custom_modes/`** — the drop-in folder. One file per
   automation. Nothing upstream is modified (keeps `git subtree` merges
   clean), and modes appear in the GUI dropdown + HTTP API automatically.

## How to write a new automation

Copy `plugins/custom_modes/patrol.py` and adapt. The contract (full detail
in upstream doc 03):

- `name()` — unique label shown in the mode dropdown.
- `is_selectable()` — cheap sanity check only (e.g. "map has encounters");
  detailed preconditions belong in `run()` as `BotModeError` raises, which
  show a friendly message and drop the bot to Manual.
- `run()` — a generator; **every `yield` advances the emulator one frame**.
  Build on the upstream toolbox (`modules/modes/util`): `navigate_to`,
  `follow_path`, `ensure_facing_direction`, `wait_for_player_avatar_to_be_controllable`,
  soft resets, PC/mart/Pokécenter interaction, etc.
- Battles: when one starts, the default battle handler takes over (shiny
  pipeline, catch filters, stats all apply). Override `on_battle_started()`
  to return a `BattleAction` or a custom `BattleStrategy`; return
  `BattleAction.CustomAction` to keep frame control inside `run()`.
  ⚠ Upstream's `run()` docstring mentions `disable_default_battle_handler()`
  — that method does not exist (KI-3); `CustomAction` is the real mechanism.
- Optional hooks: `on_battle_ended`, `on_whiteout`, `on_egg_hatched`, etc.

Per-profile configuration: read a YAML file from `context.profile.path`
(see `PatrolMode._load_waypoints()` for the validation pattern — fail with
actionable `BotModeError` messages, never tracebacks).

## Mode catalog (custom)

### Patrol (Custom) — `plugins/custom_modes/patrol.py`
- **Purpose:** shiny-hunt while walking a user-defined waypoint loop on the
  current map — covers ground the single-tile Spin mode can't (grass
  strips, cave corridors, route sections).
- **Config:** `patrol.yml` in the profile folder — a `waypoints:` list of
  `[x, y]` map-local coordinates (≥2), all on the map the player starts on,
  visited in order and looped. Pathfinding handles corners and re-routes
  after battles; `avoid_encounters=False` so grass is walked through, not
  around.
- **Battle handling:** default pipeline; after each non-loss it re-asserts
  Poké Balls + box space (same guards as Spin).
- **Verification status:** syntax-compiled; loader discovery + config
  validation covered by a structural smoke test (see below). **Live
  verification pending** — needs Python 3.11+, the bot's deps, a ROM and a
  profile (first live run: start on a grassy map, create `patrol.yml` with
  2-3 nearby waypoints, select "Patrol (Custom)").

## Verification harness

`smoke test` (session scratchpad; recreate as needed): stubs the bot's
modules with same-named fakes, imports the real plugin files, asserts
PatrolMode is discovered by the loader, and exercises `_load_waypoints()`
failure/success paths. This catches import-name drift and discovery bugs
without needing deps or a ROM. A real end-to-end test should follow the
upstream pattern (`tests/utility.py`) once ROMs are available on a machine.

## Story Mode (#24) — story auto-player

**Mode name:** `Story`. Plays Emerald's story from a fresh save, or reports
progress on an existing one. Built in verifiable chunks; current status:

- **Chapter 0 — New Game intro (working):** from a fresh, save-less boot,
  select `Story` at the title/main menu. It drives: title screen → New Game →
  Professor Birch's welcome speech → gender selection → name entry → and stops
  with the player controllable **inside the moving truck** (the clean end of
  the intro). It then hands back to manual.
- **Progress detection (working):** if you launch `Story` while a save is
  already loaded in the overworld, it reads your flags/badges/items and reports
  which of the 30 story chapters you're on (e.g. "ch5 — Devon errand, 1 badge")
  instead of starting a new game.

**Your character name & gender** come from `story.yml` in the profile folder
(auto-created with `character_name: NICK`, `gender: boy`). Edit it before
starting a new game (name ≤ 7 letters; gender `boy` or `girl`).

**Notes / limits:**
- The intro assumes a save-less boot (it selects "New Game"). Continuing an
  existing save straight from the title screen is not wired yet.
- Chapters 1–24 (stepping off the truck onward) are still being built.
- Design & rationale: `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md`.
