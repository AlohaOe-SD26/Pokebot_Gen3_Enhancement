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

**Mode name:** `Story`. Plays Emerald's story unattended from a brand-new game,
or resumes an existing save from wherever it actually is.

### How far it gets

**A cold start from the title screen reaches Badge 6 — Winona's Feather Badge —
which is the end of built content.** The reference run covered **38 maps in
~2.48M frames with 0 derails**. On earning BADGE06 the mode prints
"end of built content", hands back to manual, and stops.

Built and played end to end: the intro (New Game → Birch → name/gender → out of
the truck), the starter, Petalburg & Wally, Petalburg Woods & Cut, **Gym 1
Roxanne**, the Devon errand & Peeko, Mr. Briney's boat, Granite Cave & Steven's
letter, **Gym 2 Brawly**, Slateport & the Oceanic Museum, Mauville & the Bike,
**Gym 3 Wattson**, the Route 111 desert & Mt. Chimney, **Gym 4 Flannery**,
**Gym 5 Norman**, Surf, Routes 118/119 & the Weather Institute, Fly, the Devon
Scope & the Fortree Kecleon, the Fortree rotating-gate puzzle (solved live), and
**Gym 6 Winona**.

**Next unbuilt:** Mt. Pyre, then the Magma hideout (Route 121 → Mt. Pyre exterior
→ Magma Emblem → Jagged Pass → Maxie). Everything after that — Aqua hideout,
Mossdeep, Sootopolis, Victory Road, the Elite Four — is not built.

### How to run it

1. Put an Emerald ROM in `roms/` and start the bot (`python pokebot.py`, or the
   installer's launcher).
2. Edit `story.yml` in the profile folder **before** starting a new game — it is
   auto-created with `character_name: NICK`, `gender: boy` (name ≤ 7 letters;
   gender `boy` or `girl`).
3. Pick `Story` from the mode dropdown. From the title screen it starts a new
   game; from the overworld it reads your flags/badges/items, prints which
   chapter you are on, and picks up from there — every segment is flag-gated, so
   resuming mid-game skips what is already done rather than replaying it.

### The other three Story modes

| mode | what it adds |
|---|---|
| `Story (DEBUG)` | exactly `Story`, plus the opt-in debug log (path is printed on start). |
| `Story (DEBUG - RESET)` | debug log, then a **hard emulator reset to the title screen** and an explicitly-selected **NEW GAME** — needed because a plain A-mash would pick CONTINUE whenever a save exists. One click for fresh-run testing. Your save file is not erased. |
| `Story (ENDLESS RESET)` | **chained `Story (DEBUG - RESET)` runs, in-process** — reset → new game → play → reset → … back to back in the same emulator. This is the overnight batch runner. |

`Story (ENDLESS RESET)` defaults to 10 runs; set the count from the GUI's
**"Endless Debug-Reset Runs…"** menu item (0 = run forever). It is built for
unattended use: a `BotModeError` in run 3 is swallowed so runs 4..N still happen,
each run has a hard 3.5M-frame cap, the mode is re-asserted after every run (a
derail can call `set_manual_mode()`), and the batch's emulation speed / video
settings are restored each run so only run 1 is unthrottled.

### Notes / limits

- The mode is **built in verifiable chunks and bounded everywhere** — it is
  designed never to hang silently, so an un-handled situation stops with a named
  `BotModeError` and drops to Manual rather than looping.
- Known open issues that can end a run early are tracked in
  `PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md` (notably the move-learn recovery gap and
  whiteout attrition).
- Design & rationale: `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md`; the chapter
  table lives in `modules/story/chapters.py`.
