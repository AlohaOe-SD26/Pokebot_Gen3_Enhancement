# 05 — Stats/Persistence, Configuration, Embedded Data, Tests, and Packaging

Covers: `modules/stats.py`, `modules/stats_migrate.py`, the stats-facing parts of
`modules/encounter.py`, `modules/config/`, `modules/data/`, `tests/`, and the
install/update/distribution machinery (`requirements.py`, `updater.py`,
`pokebot.spec`, `.github/workflows/`). All paths are relative to the vendored repo
root `pokebot-gen3/` unless absolute.

## What this layer is FOR

This is the bot's "everything that isn't emulation or navigation" layer:

- **Stats** is the long-term memory of a shiny hunt. Every encounter the bot sees
  is recorded to a per-profile SQLite database so streaks, phase lengths, IV/SV
  records, and shiny logs survive restarts and can be shown in the GUI/HTTP API
  and posted to Discord.
- **Config** is how users customize behavior without touching code: a set of small
  YAML files validated by pydantic schemas, with a global layer (`profiles/*.yml`)
  that individual profiles can override file-by-file.
- **Data** is the bot's baked-in knowledge of Gen-3: species, moves, items,
  natures, types, abilities, plus pret symbol tables that let the bot read
  arbitrary game memory by name instead of hard-coded addresses.
- **Tests** are true end-to-end tests: they boot the real mGBA core against real
  ROMs, load prepared save states, and drive actual bot modes frame-by-frame.
- **Packaging** is a self-bootstrapping story: the entry script installs its own
  pip dependencies and downloads libmgba on first run, checks GitHub for updates
  daily, and can alternatively be frozen into a Windows `pokebot.exe` bundle.

---

## 1. Stats: the per-profile SQLite database

### Where it lives

`StatsDatabase.__init__` (modules/stats.py:592-596) opens
`<profile>/stats.db` — i.e. `profiles/<name>/stats.db` next to the profile's
save game. It is created lazily on first launch of a profile; the connection is
opened with `check_same_thread=False` and guarded by a `threading.Lock` for
writes (`_execute_write`, stats.py:1231). The instance is created in
`main_loop()` (modules/main.py:58: `context.stats = StatsDatabase(context.profile)`)
after the profile is chosen.

### Schema (version 3, `current_schema_version` at stats.py:25)

Schema creation/migration lives in `_update_schema` (stats.py:1308-1442). It is a
cumulative "if from_version <= N" ladder, so any older DB (or an empty one,
version 0) is brought up to date in one pass. A `schema_version` table stores the
version; a DB *newer* than the code raises `StatsDatabaseSchemaTooNew`
(stats.py:605-608), which matters because profiles are shared between machines.

Six tables:

- **`schema_version`** — single row, `version INT`.
- **`encounters`** (stats.py:1390-1407) — one row per logged encounter:
  `encounter_id` (PK, manually incremented — see gotcha below), `species_id`,
  `personality_value`, `shiny_phase_id`, `is_shiny`, `is_roamer`,
  `matching_custom_catch_filters` (text label from the custom filter that
  matched), `encounter_time` (UTC ISO), `map`, `coordinates` ("x:y"),
  `bot_mode`, `type` (EncounterType string), `outcome` (BattleOutcome int,
  updated post-battle), and `data` — a **BLOB of the full 100-byte Gen-3 Pokémon
  data structure**, so the entire Pokémon (IVs, moves, OT, everything) can be
  reconstructed later via `Pokemon(row[13])` (stats.py:141).
  Important: **not every encounter is inserted**. `log_encounter`
  (stats.py:644; the insert check is at 668) only inserts the row if `logging.log_encounters` is true OR the
  encounter is "of interest" (shiny/custom-filter match). Aggregates are always
  updated regardless.
- **`shiny_phases`** (stats.py:1361-1387, + v2/v3 columns) — one row per "phase"
  (the span between two shinies): `start_time`, `end_time`,
  `shiny_encounter_id` (FK to the shiny that ended it), `encounters`,
  `anti_shiny_encounters` (added in v3), highest/lowest IV-sum and shiny-value
  records with their species ids, longest/current same-species streaks, fishing
  attempt counters, `pokenav_calls` (added in v2), and four `snapshot_*` columns
  freezing total/species encounter counts at the moment the shiny appeared.
- **`encounter_summaries`** (stats.py:1340-1358) — one row per species (PK
  `species_id`; Unown letters get synthetic ids `20100 + letter_index`, see
  `SpeciesRecord.species_id_for_database`, stats.py:96-100): lifetime totals
  (`total_encounters`, `shiny_encounters`, `catches`, total high/low IV-sum and
  SV) plus current-phase columns that are zeroed when a phase ends.
- **`pickup_items`** (stats.py:1409-1415) — `item_id`, `item_name`,
  `times_picked_up` for the Pickup-ability farming feature.
- **`base_data`** (recreated in v2 as TEXT key/value, stats.py:1427-1432) — a
  generic key/value store (`set_data`/`get_data`, stats.py:636-642), used by
  plugins/HTTP for arbitrary persisted state.

### Runtime flow (how encounter.py feeds it)

- `modules/encounter.py` builds an `EncounterInfo` and calls
  `context.stats.log_encounter(encounter_info)` (encounter.py:173), which
  creates a phase if none is open, inserts/updates all tables, and bumps the
  in-memory encounter-rate deques (last 100 timestamps and frame counts;
  `POKEBOT_ENCOUNTER_BENCHMARK` env var raises the window to 1000 —
  stats.py:622-634). `encounter_rate` (wall clock) and `encounter_rate_at_1x`
  (frame-derived, using the GBA's 59.7275 fps) are recomputed per encounter
  (stats.py:886-911).
- If the encounter is shiny, `context.stats.reset_shiny_phase(log_entry)`
  (encounter.py:178) stamps end_time/snapshot, zeroes phase columns everywhere,
  and updates the cached shortest/longest phase.
- After the battle, `log_end_of_battle` (stats.py:784) writes the
  `outcome` back onto the last encounter row and increments `catches`.
- Repeat-encounter suppression: `is_repeat_encounter` (encounter.py:92-107)
  compares the PV against `stats.last_encounter`; on the *first* encounter after
  startup it runs a full DB lookup (`has_encounter_with_personality_value`) so
  that reloading a save state from a shiny doesn't double-count it.
- Fishing (`log_fishing_attempt`, stats.py:804), PokéNav calls
  (`log_pokenav_call`, stats.py:813), and Pickup items (`log_pickup_items`,
  stats.py:793) also flow into the phase/pickup tables.
- Read API: `get_global_stats()` returns a `GlobalStats` aggregate,
  `get_encounter_log()` / `get_shiny_log()` / `query_encounters(where, params)`
  serve the GUI and HTTP server. Note `query_encounters` interpolates the
  caller-supplied `where_clause` directly into SQL (parameters are bound, but
  the clause itself is trusted — internal use only).

### Error handling gotchas

`_handle_sqlite_error` (stats.py:1246-1269) hard-exits (`sys.exit(1)`) on
`SQLITE_BUSY` (profile opened twice, or stats.db open in a DB tool) and on
duplicate `encounter_id` primary keys — encounter IDs are allocated in Python
(`_get_next_encounter_id`, stats.py:913), not by AUTOINCREMENT, so two bot
instances on one profile collide.

### Migration from legacy JSON/CSV stats

If the DB is brand-new (schema version 0) and `<profile>/stats/` exists,
`_migrate_old_stats` (stats.py:1271) invokes
`migrate_file_based_stats_to_sqlite` (modules/stats_migrate.py:37). Sources, in
merge order (stats_migrate.py:57-106):

1. `stats/encounters/_old.zip` — per-encounter JSON files from the *Bizhawk*
   era of the bot (species IDs are off by one and get corrected,
   stats_migrate.py:992-994).
2. `stats/encounters/Phase N Encounters.csv` — per-phase CSVs from both the
   Bizhawk and early-mGBA bots. mGBA CSVs have no timestamps, so times are
   guessed from file ctime + 13s per encounter (stats_migrate.py:597-605) and
   later corrected backwards from the shiny's known time. There is a large
   hard-coded table of malformed CSV files from 40 Cakes' own stream profile
   (stats_migrate.py:461-489).
3. `stats/shiny_log.json` — authoritative for shinies and phase snapshots;
   `stats/totals.json` — authoritative for per-species lifetime totals
   (overrides summaries computed from the encounter list,
   stats_migrate.py:256-309).

Each legacy record is rebuilt into a genuine 100-byte encrypted Pokémon data
blob (`_create_pokemon_data`, stats_migrate.py:1045-1148 — it re-implements the
Gen-3 substructure encryption/checksum) so migrated rows are indistinguishable
from native ones. Old files are left in place (not deleted) after migration.

---

## 2. Configuration system

### Mechanics: confz + pydantic schemas

- Every config file is a class in `modules/config/schemas_v1.py` inheriting
  `confz.BaseConfig` (pydantic-based). Each class carries a `filename` ClassVar
  (e.g. `Battle.filename = "battle.yml"`), field defaults, and validation
  (`Literal[...]` enums, `Field(gt=..., lt=...)` ranges).
- `modules/config/__init__.py` defines `Config`, which holds one instance per
  file. `CONFIG_ATTRS` (config/__init__.py:13-22) lists the eight managed
  files: `battle`, `catch_block`, `cheats`, `discord`, `obs`, `keys`,
  `logging`, `http`. Missing files simply keep defaults (`load_config_file`
  returns None when non-strict, config/__init__.py:106-119).
- `Config.reload_file(attr)` re-reads a single file at runtime — used for hot
  reload (default hotkey Ctrl+C via `context.reload_config()`,
  modules/context.py:62) and for re-reading `catch_block.yml` on *every shiny*
  so users can block a species mid-hunt without restarting
  (modules/encounter.py:137, 153).
- `Config.save()` can write the current model back out as YAML (ruamel.yaml).

### Layering: global vs. profile

1. On startup, `BotContext.__init__` runs `_initialise_config()`
   (modules/context.py:17-37): every file in `modules/config/templates/` that
   does not yet exist in `profiles/` is copied there. Templates are the
   documented, commented default YAMLs; `profiles/*.yml` are the user's live
   **global** config (updates never overwrite them).
2. `Config()` then loads from `profiles/` (default `config_dir`,
   config/__init__.py:36).
3. When a profile is selected, `context.config.load(profile.path, strict=False)`
   (modules/gui/__init__.py:135, glfw.py:36, headless.py:22) re-points
   `config_dir` at `profiles/<name>/` and reloads. Because missing files are
   skipped non-strictly, this is a **per-file overlay**: a `discord.yml` inside
   the profile folder replaces the global one entirely (no per-key merging);
   files absent from the profile keep the previously loaded global values.
4. `metadata.yml` (`ProfileMetadata`, schemas_v1.py:245-259) exists only inside
   profile folders and records which ROM (file name, game code, revision,
   language) the profile belongs to.

### Full option reference (defaults from schemas_v1.py)

**battle.yml — `Battle` (schemas_v1.py:12-71)**
- `auto_catch: true` — auto-catch shinies/filter matches.
- `save_after_catching: false` — in-game save after a catch.
- `pickup: true`, `pickup_threshold: 1` (1-6), `pickup_check_frequency: 5` —
  Pickup-ability item farming.
- `hp_threshold: 20` (percent, 0-100) — lead considered unfit below this.
- `lead_cannot_battle_action: flee` / `faint_action: flee` — `stop|flee|rotate`.
- `new_move: stop` — `stop|cancel|learn_best`.
- `stop_evolution: true`; `switch_strategy: first_available`
  (`first_available|lowest_level`).
- `banned_moves` — long default list of moves the auto-battler must not use
  (2-turn moves, inconsistent moves, battle-ending moves).
- `avoided_pokemon: []`, `targeted_pokemon: []` — species filters for
  level-grind-style modes.

**catch_block.yml — `CatchBlock` (schemas_v1.py:74-78)**
- `block_list: ["MissingNo"]` — shinies on this list are logged but not caught.
  Reloaded on every shiny encounter.

**cheats.yml — `Cheats` (schemas_v1.py:81-86)**
- `random_soft_reset_rng: false` — skip legit RNG-burning delays on soft resets.
- `faster_pickup: false` — read Pickup results from memory instead of menuing.

**discord.yml — `Discord` + `DiscordWebhook` (schemas_v1.py:89-137)**
- `rich_presence: false`, `iv_format: formatted|basic`, `delay: 0`,
  `bot_id: "PokéBot Gen3"`, `global_webhook_url: ""`.
- Ten webhook sections, each a `DiscordWebhook` (`enable`, `interval`,
  `first_interval`/`consequent_interval` for phase summaries,
  `ping_mode: user|role|None`, `ping_id`, per-hook `webhook_url` override):
  `shiny_pokemon_encounter`, `blocked_shiny_encounter`,
  `pokemon_encounter_milestones` (default interval 10000),
  `shiny_pokemon_encounter_milestones` (5), `total_encounter_milestones`
  (25000), `phase_summary` (first 8192, then every 5000),
  `anti_shiny_pokemon_encounter`, `custom_filter_pokemon_encounter`, `pickup`
  (10), `tcg_cards`.

**keys.yml — `Keys`/`KeysGBA`/`KeysEmulator` (schemas_v1.py:140-185)**
- GBA pad mapping (A=`x`, B=`z`, L=`a`, R=`s`, Start=Return, Select=BackSpace)
  and emulator hotkeys (speed presets 1x-32x/unthrottled on number keys,
  Tab=manual toggle, Ctrl+R reset, Ctrl+C reload config, Ctrl+S/Ctrl+L save/load
  state, F12 screenshot, etc.).

**logging.yml — `Logging` (schemas_v1.py:188-206)**
- `save_pk3.shiny/custom/roamer: true` — dump .pk3 files of notable mons.
- `create_save_state_for_shiny: true`, `log_encounters: false` (full
  per-encounter DB rows — off by default!), `log_encounters_to_console: true`,
  `desktop_notifications: true`, `shiny_gifs: true`, `tcg_cards: true`
  (generates joke trading-card images via modules/tcg_card.py).

**obs.yml — `OBS`/`OBSWebsocket` (schemas_v1.py:216-234)**
- `discord_delay`, `discord_webhook_url`, `replay_buffer` +
  `replay_buffer_delay`, `screenshot`, `shiny_delay`, and `obs_websocket`
  (`host: 127.0.0.1`, `port: 4455`, `password`) for stream automation.

**http.yml — `HTTP`/`HTTPServer` (schemas_v1.py:209-213, 237-242)**
- `http_server: {enable: false, ip: 127.0.0.1, port: 8888}` — REST/stream API
  (aiohttp) used by stream overlays.

**customcatchfilters.py** (templates/customcatchfilters.py) — not YAML: a user
Python hook. `custom_catch_filters(pokemon) -> str | bool` returns a label to
treat any encounter as catch-worthy (perfect IVs, all-0 IVs, 6 identical IVs
are active by default; more examples commented out). Loaded per-profile if
`profiles/<name>/customcatchfilters.py` exists, else the global
`profiles/customcatchfilters.py` (modules/encounter.py:72-86). Exceptions list
skips one-time encounters (starters/legendaries).

---

## 3. Embedded data catalog (`modules/data/`)

Accessed via `get_data_path()` (modules/runtime.py:30-35), so it ships inside
PyInstaller bundles (`pokebot.spec` includes `modules/data`).

| File / dir | Purpose |
|---|---|
| `species.json` (1.1 MB, 412 entries) | Full Gen-3 species dex: name, national/hoenn dex numbers, types, abilities, RSE/FRLG held items, base stats, gender ratio, egg cycles/groups, base friendship, catch rate, safari flee probability, level-up curve, EV/exp yield, complete learnset (level-up/TM/HM/tutor/egg), localized names (6 languages), evolutions/family. |
| `moves.json` (443 KB, 355 entries) | Every move: effect id, base power, type, accuracy, PP, target, priority, contact/sound/protect/magic-coat/snatch/mirror-move/kings-rock flags, TM/HM number, localized names + descriptions. |
| `items.json` (414 KB, 377 entries) | Items: index, price, type, battle/field use, pocket, hold effect + parameters, TM/HM move id, localized names/descriptions. |
| `abilities.json` (78 entries) | Ability names + localized names/descriptions. |
| `natures.json` (25 entries) | Nature stat modifiers + localized names. |
| `types.json` (18 entries) | Type chart: per-type `effectiveness` map (the full Gen-3 damage multiplier matrix) + localized names. |
| `keyboard.json` | Layout arrays of the in-game naming-screen keyboard per language — used to type nicknames/player names programmatically. |
| `symbols/*.sym` (~26 MB) | pret decompilation symbol tables (address, scope, size, name) for Emerald, R/S (+rev1, +German), FR/LG (+rev1). This is how the bot reads `gPlayerParty` etc. by name. `patches/` overrides missing sizes and holds per-language offset patches; `fetch_symbols.py` re-downloads from pret; format documented in `symbols/Readme.md`. |
| `event_flags/`, `event_vars/` | pret-derived flag/var name→index maps per game (`emerald.txt`, `frlg.txt`, `rs.txt`) + compile scripts. Loaded in modules/game.py:97-105. |
| `frlg_safari_catch_strategies/lookup-*.yml` | Precomputed optimal Safari Zone ball/bait/rock strategy tables for FR/LG. |
| `extract.py` | Maintainer tool: reads localized data out of a set of ROMs (needs all 6 Emerald languages + rev-1 ROMs of the other four games) to regenerate the JSONs. |
| `get_pret_maps.py` | Maintainer tool: generates `modules/map_data.py` from checked-out pokeemerald/pokefirered repos. |

Note: **wild encounter tables are not in `modules/data/`** — they are read from
ROM at runtime (see the map/encounter agent's doc); and "TCG data" is not data
either — `modules/tcg_card.py` generates card images from sprite assets.
Sprites do **not** live at the repo root: `get_sprites_path()`
(modules/runtime.py:38-43) points at `modules/web/static/sprites/`, which holds
all Pokémon/item/TCG sprite images. (`pokebot.spec` still lists a repo-root
`sprites/` as bundled data — a stale reference, see the packaging section.)

---

## 4. Tests (`tests/`)

True end-to-end suite driving the real emulator (docs: tests/README.md).

- **Prerequisites**: three specific ROM dumps in `roms/` — Emerald (English),
  Ruby (English rev 2... actually SHA1 `5b64eacf...`), FireRed (English rev 1);
  SHA1 hashes listed in tests/README.md:9-11. No mocked emulator — tests run
  libmgba headless with video/audio off and throttle disabled
  (tests/utility.py:247-254).
- **Run**: from repo root, `python -m unittest discover -s tests` (or a single
  module/test). Standard `unittest`, no pytest.
- **Infrastructure** (tests/utility.py):
  - `tests/states/{emerald,firered,ruby}/*.ss1` — prepared mGBA save states
    (some include the battery save for soft-reset tests; created via the bot's
    Debug menu "Create state with save game").
  - `@with_save_state("emerald/x.ss1")` or a list (runs the test once per game
    via `subTest`) — `guess_rom_from_save_state` picks the matching ROM, builds
    a throwaway `Profile` pointed at the tests dir, and loads the state
    (utility.py:257-268, 327-350).
  - `@with_frame_timeout(n)` — fails the test after n frames and saves
    `tests/last_frame_timeout.png` as a screenshot for debugging
    (utility.py:353-372).
  - `AutomatedTestBotMode` (utility.py:82) wraps a test generator as a bot mode
    with overridable event callbacks (`on_battle_started`, `on_egg_hatched`...);
    `_run_test` re-implements the frame loop from modules/main.py.
  - `MockStatsDatabase` (utility.py:28) replaces the SQLite stats DB — tests
    assert on `self.stats.logged_encounters`; **the real StatsDatabase itself is
    never exercised by the suite**.
  - RNG control: `set_next_rng_seed` writes `gRngValue` directly and mocks
    `wait_for_unique_rng_value` with an LCG simulator (utility.py:385-398) —
    this is how `test_it_catches_shinies` forces shiny encounters with
    per-game magic seeds (tests/test_mode_spin.py:31-60).
  - Module-level `mock.patch` of `ask_for_choice` (GUI dialogs) and the rich
    console (utility.py:375-382); config comes from the *templates* directory,
    with logging tweaked for tests (utility.py:232-240).
- **Coverage**: mode Spin (encounters + shiny catch), mode Starters, battle
  evolution handling (4 cases), move learning (4 cases), pathfinding (13 cases:
  warps, connected maps, surf, waterfalls, dive, currents, muddy slopes, acro
  bike rails), and `test_map.py` (non-emulator-heavy: encounter-table math with
  repel/Pressure/Intimidate/Magnet Pull/Static level filtering).
- **Gaps**: no tests for the stats DB or JSON migration, config
  loading/validation, Discord/OBS/HTTP integrations, the GUI, the updater/
  requirements bootstrap, or most bot modes (fishing, safari, daycare, roamers,
  soft-reset modes...). CI does **not** run the suite (ROMs can't be shipped);
  the only CI check is Black formatting.

---

## 5. Distribution: bootstrap, auto-update, packaging

### Fresh-machine setup (source distribution — the normal path)

What a fresh Windows machine needs (per wiki/pages/Getting Started.md):
64-bit Python 3.13 on PATH (installer, "Add to PATH" ticked) and the bot folder
(release ZIP or git clone) plus a legally dumped ROM in `roms/`. Then double
click / `py pokebot.py`:

1. `pokebot.py:114-118`: if not a PyInstaller bundle, `check_requirements()`
   (requirements.py:216) runs *before any third-party import*.
2. `check_requirements` compares a SHA1 of (module list + Python version +
   libmgba version) against `.last-requirements-check` in the repo root; if
   missing/stale it runs `update_requirements()` (requirements.py:62):
   - Python version gate: supported `3.11/3.12/3.13` (requirements.py:7-8);
     newer minor versions prompt "risk it anyway?"; older ones hard-exit.
     32-bit Python hard-exits (requirements.py:104).
   - Asks for confirmation, then runs `pip install` **per module** via
     subprocess (requirements.py:129-134) with `--user` unless in a venv.
     The dependency list is a Python list in requirements.py:14-38 (confz,
     numpy, ruamel.yaml, pypresence, obsws-python, discord-webhook, rich, cffi,
     Pillow, sounddevice, plyer, notify-py, apispec, ttkthemes, darkdetect,
     aiohttp, aiortc, ...; pywin32 + psutil on Windows). There is **no
     requirements.txt** — this file is the single source of truth.
   - libmgba: if `./mgba/` doesn't exist, downloads a prebuilt
     `libmgba-py` ZIP from `github.com/hanzi/libmgba-py` releases (tag
     `0.2.0-2`) chosen by OS/arch (win64, ubuntu-lunar for Linux, macOS
     arm64/x86_64) and extracts it into the repo root (requirements.py:136-204).
     Only specific Linux distros are "tested"; others get a warning prompt.
   - Writes the new hash to `.last-requirements-check`.
3. `updater.py` then runs (only when *not* bundled and *not* a git checkout —
   pokebot.py:146-147): at most once per day (`.last-update-check`) it queries
   the GitHub API for the latest release of `40Cakes/pokebot-gen3`
   (updater.py:43), and if the tag differs from `modules/version.py`'s
   `pokebot_version`, prompts to download the release ZIP and **extracts it
   over the current directory** (updater.py:82-89). No backup, no file
   deletion — stale files from removed modules linger. Profile data survives
   because releases contain no `profiles/` content that would overwrite user
   files (and template copies only fill gaps). Git checkouts are expected to
   update via `git pull` instead.
4. Version identity: `modules/version.py` is `dev`/`dev-<sha>` in checkouts
   (it parses `.git/HEAD` manually); the release workflow rewrites it with the
   tag.

### Release pipeline (.github/workflows/)

- `lint.yml` — Black `--line-length 120 --check` on every push/PR. That's the
  entire CI.
- `release-when-tag-pushed.yml` — on any tag push (main repo only): rewrites
  `modules/version.py` with the tag, deletes `.git*` and `pokebot.spec`,
  renames LICENSE, zips the whole tree, and publishes it as a GitHub release
  asset. So a "release" is just the source tree with a pinned version string —
  users still run the Python bootstrap on their machine.

### PyInstaller bundle (`pokebot.spec`)

- Running `pyinstaller pokebot.spec` first calls
  `update_requirements(ask_for_confirmation=False)` (pokebot.spec:9-11) so the
  build env has all deps + libmgba.
- Builds `pokebot.exe` (console app) with `sprites/` and `modules/data/` as
  bundled datas (pokebot.spec:17 — but the repo-root `sprites/` it names no
  longer exists; sprites moved to `modules/web/static/sprites/`), collects into
  `dist/pokebot/`, copies LICENSE/Readme, creates
  empty `profiles/` (with template YMLs + .py files copied from a repo-root
  `profiles/` dir) and `roms/`.
- At runtime, `is_bundled_app()` (modules/runtime.py:5-9) short-circuits both
  the requirements check and pip installs; `get_base_path()` becomes the exe's
  directory.
- **Currently broken/stale**: the spec also builds an `import.exe` from
  `import.py` (pokebot.spec:27-34), but `import.py` does not exist in the repo
  — the spec would fail as-is. Its `('sprites', 'sprites')` data entry points
  at a repo-root `sprites/` directory that also does not exist (sprites are at
  `modules/web/static/sprites/`), and it expects a repo-root `profiles/`
  directory that is not checked in (it's created at first run). No CI job
  builds this bundle; releases are source ZIPs.

---

## 6. Wiki index (`wiki/`)

`wiki/Readme.md` is the table of contents; `wiki/pages/` holds one Markdown page
per topic. Quick map:

- **Setup**: `Getting Started.md` (OS support, Python 3.13, download/venv/run),
  `MacOS Installation.md`, `Supported Games and Languages.md`,
  `Using Unsupported ROMs.md`, `Report an Issue.md`, `Stream FAQ.md`.
- **Config** (mirrors the schema files): `Configuration - Overview.md`
  (profile-vs-global layering, hot reload), `... Battling and Pickup.md`,
  `... Catch Block List.md`, `... Cheats.md`, `... Custom Catch Filters.md`,
  `... Discord.md`, `... HTTP Server.md`, `... Key Mappings.md`, `... OBS.md`,
  `Console, Logging and Image Config.md`.
- **Modes**: one page per bot mode (Spin, Starters, Fishing, Safari, Daycare,
  Static Soft Resets/Run Aways/Gift Resets, Roamer Resets/Re-Encounter, Rock
  Smash, Sweet Scent, Feebas, Kecleon, Sudowoodo, Nugget Bridge, Game Corner,
  Berry Blender, EV Train, Level Grind, Item Steal, Puzzle Solver, Acro Bike
  Bunny Hop, Manual) plus `Pokemon By Bot Mode.md` (which species each mode can
  hunt).
- **Advanced**: `Customisation - Plugins.md` (plugin hook API),
  `Customisation - Statistics Database.md` (querying stats.db),
  `Data Manipulation - Save Modification.md`, `Optimisations - *.md` (battle
  transitions, tips), `Anti-Shiny Sprites.md`.

### Enhancement opportunities

- **One-script installer**: everything the bootstrap needs is already
  programmatic — `requirements.py` exposes `update_requirements()` and the
  libmgba download URL logic; an installer only has to (a) verify/install
  64-bit Python 3.11-3.13, (b) fetch the release ZIP or git clone, (c) run
  `python requirements.py` non-interactively (add a flag or call
  `update_requirements(ask_for_confirmation=False)`), and (d) drop a shortcut
  to `pokebot.py`. Pain points to fix: per-module sequential `pip install`
  (slow — could be one pip call or a generated requirements.txt), interactive
  `input()` prompts sprinkled through requirements.py/updater.py (no
  `--yes`/headless mode), no venv creation by default (`--user` installs
  pollute the global site-packages), and the `.last-requirements-check` hash
  silently skipping re-checks after manual edits.
- **Updater redesign**: current updater extracts a ZIP over the install dir
  with no manifest, rollback, or deletion of removed files, and only works for
  non-git, non-bundled installs. A git-based or manifest-based updater (with
  the profile dir explicitly excluded) would be safer and also serve the
  PyInstaller path, which today has *no* update mechanism at all.
- **pokebot.spec is stale** (references missing `import.py`, a repo-root
  `sprites/` dir that moved to `modules/web/static/sprites/`, and a repo-root
  `profiles/` template dir); fixing it plus adding a CI build job would enable
  a true no-Python Windows distribution — likely the cleanest end state for a
  one-click installer.
- **Stats**: encounter IDs allocated client-side + hard `sys.exit` on lock
  contention make multi-instance use fragile; AUTOINCREMENT + retry/backoff
  would be more robust. `log_encounters` defaults to false, so most users have
  aggregates only — worth surfacing. `query_encounters`' raw where-clause is
  fine internally but shouldn't ever be exposed to HTTP input.
- **Config**: the per-file (not per-key) profile override is subtle and
  undocumented in code; a merge strategy or explicit docs would prevent
  surprises. Schemas are versioned in the filename (`schemas_v1.py`) but there
  is no migration path defined for a v2.
- **Tests**: no coverage of stats/migration/config; the migration code path in
  particular is complex and easy to regress. The suite can't run in CI without
  ROMs — a small set of unit tests (stats DB against a temp file, config
  validation, type-chart lookups) would be CI-safe.

### For the Pokémon Emerald AI project

- **`modules/data/` is a ready-made Gen-3 knowledge base**: `species.json`
  (base stats, catch rates, learnsets, evolutions), `moves.json` (power/
  accuracy/PP/priority/flags), `types.json` (the full effectiveness matrix),
  `natures.json`, `items.json`, `abilities.json`. An Emerald battle AI can load
  these directly — no ROM extraction needed — and they're license-compatible
  since we already vendor the repo.
- **`modules/data/symbols/pokeemerald.sym`** + the patch mechanism give
  name→address→size for every RAM/ROM symbol in Emerald; combined with
  `event_flags/emerald.txt` and `event_vars/emerald.txt` this is the complete
  memory-reading map an AI agent needs to observe game state.
- **The tests' harness pattern is the right template for AI training loops**:
  headless libmgba, save-state injection (`_load_test_state`), direct
  `gRngValue` writes for determinism, and a frame-step loop with full game-state
  introspection (tests/utility.py:271-324) — essentially a gym environment
  already.
- **stats.db is a self-contained episode log**: every encounter stores the full
  100-byte Pokémon blob, timestamps, map, coordinates, and battle outcome — a
  free dataset/replay format an AI project can reuse or extend (and the
  `base_data` key/value table is a sanctioned place for custom persisted state).
- **The custom catch filter + plugin hooks** (`customcatchfilters.py`,
  `plugin_judge_encounter`) are the sanctioned injection points for smarter
  decision logic without forking core code.
