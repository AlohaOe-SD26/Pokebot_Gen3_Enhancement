# Core Runtime & Emulator Layer

> Scope: `pokebot.py`, `updater.py`, `requirements.py`, `pokebot.spec`, and
> `modules/{main,context,libmgba,memory,game,tasks,runtime,version,profiles,roms,save_data,save_import,files,plugins,plugin_interface,exceptions,exceptions_hook,console,keyboard}.py`,
> `modules/built_in_plugins/`, `plugins/`.
> Repo root: `pokebot-gen3/` (all paths below are relative to it unless absolute).

## What this layer is FOR

This layer is the "engine room" of PokéBot Gen3. Everything else in the codebase — bot
modes (shiny-hunting automations), the Tk GUI, the web/HTTP API, stats logging — sits
on top of the abstractions defined here:

- **It owns the emulator.** `LibmgbaEmulator` wraps the `libmgba-py` CFFI bindings to
  mGBA and gives Python full, synchronous control over an emulated GBA: run exactly one
  frame, read/write raw memory, press buttons, save/load emulator states, toggle
  video/audio, throttle or unthrottle speed.
- **It owns the clock.** The bot is *not* event-driven; it is a single-threaded,
  frame-locked loop. Every frame of GBA emulation happens because `main_loop()` in
  `modules/main.py` explicitly asked for it. Bot logic runs *between* frames, so the
  game is effectively paused while Python thinks. This is what makes memory reads
  race-free and deterministic.
- **It translates raw RAM into meaning.** `modules/game.py` loads the pret
  decompilation symbol tables (`gPlayerParty`, `gMain`, …), and `modules/memory.py` /
  `modules/tasks.py` use them to answer questions like "what screen is the game on?",
  "which in-game coroutines (Tasks) are running?", "is a dialogue waiting for input?".
- **It owns identity and persistence.** `modules/roms.py` fingerprints ROM files,
  `modules/profiles.py` defines the per-save-game directory layout, `modules/save_data.py`
  parses the actual Gen-3 save structure, and `modules/save_import.py` migrates external
  mGBA saves/states into a bot profile.
- **It provides the extension seams.** `modules/plugins.py` + `plugin_interface.py`
  define the officially supported way to add custom behaviour (including whole new bot
  modes) without touching bot code that would be overwritten by updates.
- **It bootstraps itself.** `requirements.py` self-installs pip dependencies and
  downloads the libmgba-py binary, and `updater.py` self-updates from GitHub releases —
  i.e. the bot is its own installer.

---

## The main frame loop (the single most important thing to understand)

### Flow of one frame

`main_loop()` (`modules/main.py:36`) runs forever on the main thread (it is invoked by
the GUI/headless wrapper after a profile is selected). Each iteration:

1. **Drain the work queue** (`modules/main.py:74`). `work_queue` (`modules/main.py:19`)
   is a `queue.Queue[callable]` that other threads (chiefly the HTTP server) use to run
   code on the main thread at a frame boundary — the only safe time to touch the
   emulator.
2. **Snapshot game state** into a `FrameInfo` (`modules/main.py:90`, class at
   `modules/modes/_interface.py:219`): current mGBA frame counter, decoded
   `GameState` enum, the list of active in-game Tasks, the game's script-engine stack,
   and the names of the Python generators on the controller stack. `FrameInfo` links to
   `previous_frame` so modes/listeners can ask `game_state_changed_to(...)`.
3. **Detect emulator resets** (`modules/main.py:100`): if the frame counter went
   *backwards*, the ROM was reset, so the `state_cache` is flushed and bot listeners
   are re-created.
4. **Ensure a bot mode is running** (`modules/main.py:104-110`). In `"Manual"` mode a
   no-op `ManualBotMode` (`modules/main.py:27`) is used and held buttons are released.
   Otherwise, if the controller stack is empty, the current mode class is looked up by
   name, instantiated, and its `run()` generator is pushed onto
   `context.controller_stack`.
5. **Run listeners, then advance the top generator** (`modules/main.py:112-118`):
   every `BotListener.handle_frame(bot_mode, frame_info)` is called (on a *copy* of the
   listener list, so listeners may add/remove listeners safely), then
   `next(context.controller_stack[-1])` resumes the topmost generator until its next
   `yield`.
6. **Error policy** (`modules/main.py:119-137`): `StopIteration`/`GeneratorExit` pops
   the stack (a sub-generator or the mode finished); `BotModeError` sets
   `context.message` (shown in the GUI status) and drops to Manual mode (buttons
   released); any other exception prints a traceback
   and drops to Manual (or debug stepping mode with `--debug`). `TimeoutError` kills
   the process (nothing in-tree currently raises it; the test harness's
   `with_frame_timeout` raises `AssertionError` instead).
7. **Emulate the frame** (`modules/main.py:139-140`): the pressed-input bitfield is
   recorded into `inputs_each_frame` (a 128-entry deque the HTTP server streams), then
   `context.emulator.run_single_frame()` actually advances mGBA by one frame.

### The generator ("controller stack") pattern

Bot modes are **generator functions**. `BotMode.run()`
(`modules/modes/_interface.py:52`) yields once per frame; between yields the game does
not move. A typical mode fragment is:

```python
context.emulator.press_button("A")
yield                      # <- one frame of emulation happens here
while task_is_active("Task_DuckBGMForPokemonCry"):
    yield                  # wait, frame by frame
```

`context.controller_stack` is a *stack* of generators because listeners and plugins can
temporarily seize control: e.g. the `BattleListener` pushes a battle-handling generator
on top of the mode's generator when a battle starts, and plugin hooks that return
generators are pushed the same way. Only the **top** generator is advanced each frame
(`modules/main.py:118`); when it finishes (`StopIteration`), it is popped and the one
below resumes next frame. Setting the mode to Manual clears the whole stack
(`modules/main.py:115-116`).

### Input injection

Inputs are latched, not typed:

- `press_button(button)` (`modules/libmgba.py:471`) sets a bit in `_pressed_inputs` for
  the *next* frame only. The XOR against `_prev_pressed_inputs` at line 476 means a
  button "pressed" two frames in a row is automatically released for one frame in
  between — the GBA needs to see an edge, not a level, for a new press to register.
- `hold_button` / `release_button` (`modules/libmgba.py:478,492`) manage a separate
  `_held_inputs` bitfield that persists across frames (used for walking/running).
- `run_single_frame()` (`modules/libmgba.py:577`) combines them:
  `set_inputs(self._pressed_inputs | self._held_inputs)` → `core.run_frame()` → clears
  `_pressed_inputs`.
- The bitfield layout is `input_map` (`modules/libmgba.py:27`): A=0x1, B=0x2,
  Select=0x4, Start=0x8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200 —
  the GBA's native KEYINPUT ordering.
- On mode errors/manual switches, `reset_held_buttons()` (`modules/libmgba.py:499`)
  clears held state so the character doesn't keep walking.

### The global `context` object

`context = BotContext()` (`modules/context.py:188`) is a module-level singleton that
every part of the codebase imports (`from modules.context import context`). It is the
dependency-injection hub and the *only* global mutable state:

- `context.emulator` — the `LibmgbaEmulator` instance (set by GUI/headless `run()`).
- `context.gui` — `PokebotGui` or `PokebotHeadless` (set in `pokebot.py:161`).
- `context.profile`, `context.rom` (property proxying `profile.rom`,
  `modules/context.py:180`), `context.config`, `context.stats`, `context.debug`.
- `context.bot_mode` (str property, `modules/context.py:109`) — *setting this string is
  how mode switches happen*; the main loop notices the change on the next frame.
  `set_manual_mode()` (`modules/context.py:128`) additionally releases buttons, resets
  speed to 1x, re-enables video, and fires a desktop notification.
- `context.controller_stack`, `context.bot_listeners`, `context.bot_mode_instance` —
  the frame loop's working state.
- Convenience properties `emulation_speed`, `audio`, `video`, `message` that proxy to
  the emulator and notify the GUI via `_update_gui()` (`modules/context.py:183`).

`BotContext.__init__` also calls `_initialise_config()` (`modules/context.py:17`) which
copies any missing template YAML from `modules/config/templates/` into `profiles/` —
that is why user config lives *outside* the code tree and survives updates.

### Speed control and throttling (why audio matters)

`run_single_frame()` throttles by **blocking on the audio device**
(`modules/libmgba.py:606-629`): it writes one frame's worth of samples to a
`sounddevice.RawOutputStream`, which returns only when the device consumed them.
Non-1x speeds are achieved by changing the GBA's *sample rate* (`set_speed_factor`,
`modules/libmgba.py:354`): half the samples per frame → audio plays them in half a
frame's time → 2x speed. If audio init fails, it falls back to `time.sleep()`-based
pacing. Unthrottled mode (`emulation_speed = 0`) skips all of this and runs as fast as
the CPU allows — combined with `set_video_enabled(False)`
(`modules/libmgba.py:296`, which swaps in dummy no-op renderer flags on all BG/OBJ
layers), this is the bot's "turbo" configuration.

---

## Per-file documentation

### `pokebot.py` — entry point

- Parses CLI args into `StartupSettings` (`pokebot.py:38`): positional profile name,
  `-m/--bot-mode`, `-s/--emulation-speed` (0 = unthrottled), `-hl/--headless`,
  `-nv/--no-video`, `-na/--no-audio`, `-nt/--no-theme`, `-gl/--use-opengl`,
  `-t/--always-on-top`, `-d/--debug`, hidden `-c/--config`.
- Bootstrap order in `__main__` (`pokebot.py:114-163`) — important for anyone building
  an installer or alternative launcher:
  1. If not a PyInstaller bundle → `check_requirements()` (may pip-install and download
     libmgba on first run).
  2. Import the rest of the app (imports are deferred until after the requirements
     check, since the dependencies may not exist yet).
  3. `register_exception_hook()`; `load_plugins()` (user plugins load *before* arg
     parsing because they may register bot modes that must appear in `--bot-mode`
     choices).
  4. On Windows, `win32api.SetConsoleCtrlHandler` (`pokebot.py:141`) catches
     console-close so the emulator state still gets saved.
  5. If not bundled **and** not a git checkout → `run_updater()` (`pokebot.py:146`).
  6. Construct `PokebotHeadless` or `PokebotGui`, assign to `context.gui`, and call
     `gui.run(startup_settings)` — the GUI (or headless wrapper) is what creates the
     emulator and finally calls `main_loop`.
- `on_exit` atexit handler (`pokebot.py:22`): on Windows, when launched via `py.exe`
  double-click or as a bundled exe, waits for Enter before the console closes so crash
  output stays readable.

### `modules/main.py` — the frame loop

Documented in detail above. Additional notes:
- `work_queue` (`modules/main.py:19`) and `inputs_each_frame` (`modules/main.py:24`)
  are module-level and imported by the HTTP server and by built-in plugins (e.g. the
  GIF plugin re-disables video via the work queue after a background thread finishes).
- Unsupported-ROM warning (`modules/main.py:41`) triggers when the loaded ROM's name
  starts with `"Unsupported "` (see `roms.py` hash whitelist below).
- Built-in plugins are loaded *here*, not at startup (`modules/main.py:55`), because
  they depend on the merged global+profile config which only exists after profile
  selection. User plugins, in contrast, load in `pokebot.py` before anything else.
- `StatsDatabase` and the optional HTTP server are also started here
  (`modules/main.py:58-66`).

### `modules/context.py` — global state hub

Documented above. Design decision worth knowing: `reload_config()`
(`modules/context.py:62`) builds a whole new `Config`, loads it non-strictly from the
profile dir, swaps it in, and calls `plugin_config_reloaded()`; on failure it keeps the
old config, so a malformed YAML edit at runtime can't kill a hunt.

### `modules/libmgba.py` — the emulator wrapper

Key API surface of `LibmgbaEmulator` (`modules/libmgba.py:95`):

| Concern | Members |
|---|---|
| Lifecycle | `__init__` (loads ROM + `current_save.sav` + `current_state.ss1`; registers `shutdown` atexit and a savedata-updated callback), `reset()` (:198), `shutdown()` (:231) |
| Frame control | `run_single_frame()` (:577), `get_frame_count()` (:258), `peek_frame(n)` contextmanager (:558) — run ahead n frames, inspect, then restore state; `get_task_look_ahead()` (:634) |
| Memory | `read_bytes(addr, len)` (:399), `write_bytes(addr, data)` (:432) — direct `ffi.memmove` against mGBA's native wram/iwram/rom arrays. Reads allowed from EWRAM (0x02...), IWRAM (0x03...), ROM (0x08+); writes only to EWRAM/IWRAM. |
| Inputs | `get_inputs`/`set_inputs` (raw bitfield, :459/:465), `press_button` (:471), `hold_button` (:478), `is_button_held` (:485), `release_button` (:492), `reset_held_buttons`/`restore_held_buttons` (:499/:508) |
| States & saves | `get_save_state()`/`load_save_state()` (:360/:367) — mGBA savestates as bytes; `create_save_state(suffix)` (:201) writes a **PNG screenshot with the savestate zlib-embedded in a custom `gbAs` chunk** to `profiles/<name>/states/<timestamp>.ss1` and refreshes `current_state.ss1`; `read_save_data()` (:389) clones SRAM/flash contents; `load_save_game()` (:377); `backup_current_save_game()` (:243) copies the .sav to `saves/<timestamp>.sav` every time the *in-game* save function runs |
| Video/audio | `set_video_enabled` (:296, disables all render layers for speed), `get_current_screen_image()` (:511, PIL image of the live frame buffer), `get_screenshot()` (:514 — if video is off, temporarily enables it, emulates 1 frame, snapshots, then restores the savestate: screenshot is 1 frame "late" but emulation is unaffected), `take_screenshot()` (:536 → `screenshots/`), throttle/speed setters (:326-358) |
| Perf | `PerformanceTracker` (:49) — FPS history and "fraction of time spent in bot vs emulator" metric (:276) |

Gotchas:
- `mgba.log.silence()` (:117) is required or libmgba spams stdout.
- The savestate-on-shutdown design means the bot *always resumes exactly where it
  stopped* — `current_state.ss1` is authoritative, `current_save.sav` is only what the
  in-game save last wrote.
- `SAMPLE_RATE_MULTIPLIER` (:25) compensates for the GBA's true 59.7275 fps so 1x
  speed sounds right.

### `modules/memory.py` — symbol-based memory access & game state

- `read_symbol(name, offset, size)` (`modules/memory.py:43`) / `write_symbol` (:73):
  resolve a pret symbol name to (address, length) via `modules/game.py` and do the raw
  read/write. This is the *standard* way all higher layers touch memory.
- `get_save_block(num, offset, size)` (:119) / `write_to_save_block` (:152): access
  SaveBlock1/2 — the game's "global player state" structs. On R/S the blocks are at
  fixed symbols; on Emerald/FRLG only a *pointer* (`gSaveBlock1Ptr`) is fixed, so the
  code dereferences it each call. Returns zeroes when no game is loaded.
- `get_encryption_key()` (:176), `decrypt16/32` (:192/:206): Emerald/FRLG XOR-obfuscate
  certain values (money, items); R/S key is 0.
- `GameState` enum (:220) + `get_game_state()` (:253): decodes the game's current
  top-level screen by reading `gMain.callback2` (a function pointer), resolving it to a
  symbol name (`get_game_state_symbol`, :245), and pattern-matching known callback
  names (OVERWORLD, BATTLE, TITLE_SCREEN, …). Cached per frame in `state_cache`.
- Event flags/vars API (:336-419): named or numbered story flags and variables read
  from/written to SaveBlock1 at per-game offsets (R/S 0x1220/0x1340, Emerald
  0x1270/0x139C, FRLG 0x0EE0/0x1000).
- `game_has_started()` (:325): true once a save is loaded or a new game began.

### `modules/game.py` — symbol tables, event flag maps, text codec

- `set_rom(rom)` (`modules/game.py:171`) is called once when emulation starts (from the
  GUI/headless `run()`): picks the right `.sym` file per game code/revision/language
  from `modules/data/symbols/` (+ `patches/`, + per-language YAML address patches),
  and the right event-flag/var list (`rs.txt`/`emerald.txt`/`frlg.txt`).
- `_symbols` maps UPPERCASED name → (address, size); `_reverse_symbols` maps address →
  name. `get_symbol` (:224), `get_symbol_name` (:232), `get_symbol_name_before` (:245 —
  walks backwards up to 1024 bytes to attribute an arbitrary address to the containing
  function; used for callback/task identification).
- `decode_string` / `encode_string` (:284/:362): the proprietary Gen-3 character
  encoding (0xFF terminator, 0xFE newline, 0xFD variable placeholders, 0xFC formatting
  codes), with international and Japanese tables.
- Everything here is *pure lookup* — no emulator dependency — which is why
  `memory.py` imports it and not vice versa.

### `modules/tasks.py` — the game's coroutine system

Gen-3 games schedule work as "Tasks" (up to 16 entries in `gTasks`, 40 bytes each:
function pointer, active flag, priority, 16 two-byte data slots) and run scripted
events via a bytecode "script context".

- `Task` (:15) / `TaskList` (:46): parsed view of `gTasks`; keyed by resolved function
  symbol name (lowercased). `get_tasks()` (:164) is frame-cached; `task_is_active(name)`
  (:177) is the workhorse predicate bot modes use to wait for in-game operations.
- `ScriptContext` (:84): parses `sGlobalScriptContext` / `sScriptContext1` — mode
  (bytecode/native), stack of script pointers resolved to script symbol names.
  `get_global_script_context()` (:181). The script stack is included in every
  `FrameInfo`, letting modes react to specific event scripts.
- `is_waiting_for_input()` (:199): detects "press A/B to continue" dialogue states via
  the native-function pointer or the text-printer structs (per-game logic).

### `modules/runtime.py` & `modules/version.py` — paths and version

- `is_bundled_app()` (`runtime.py:5`): PyInstaller detection via `sys.frozen`.
- `get_base_path()` (:19): folder of `pokebot.py`/`pokebot.exe` — the anchor for
  `profiles/`, `roms/`, `plugins/`, `mgba/`, `.last-update-check`,
  `.last-requirements-check`.
- `get_data_path()` (:30): `modules/data` (symbol tables etc.; differs from base path
  inside a bundle).
- `version.py`: `pokebot_name = "PokéBot Gen3"`, `pokebot_version = "dev"` by default;
  reads `.git/HEAD` manually (no git binary needed) to produce `dev-<sha>` or a tag
  name (:16-45). GitHub Actions replaces the file with the tagged version at release
  time — this is what the updater compares against.

### `modules/profiles.py` — profile system (on-disk layout)

A **profile** = one save game. Layout under `<base>/profiles/<name>/`:

| Path | Written by | Purpose |
|---|---|---|
| `metadata.yml` | `create_profile` (`profiles.py:94`) | Which ROM (file name, game code, revision, language) this save belongs to |
| `current_save.sav` | libmgba | The battery save (SRAM/flash) |
| `current_state.ss1` | `LibmgbaEmulator.shutdown()` | Savestate; loaded on startup to resume exactly |
| `states/` | `create_save_state` | Timestamped savestate backups (PNG+`gbAs`) |
| `saves/` | `backup_current_save_game` | Timestamped .sav backups on every in-game save |
| `screenshots/`, `screenshots/gifs/`, `screenshots/cards/`, `screenshots/obs/` | screenshot/GIF/TCG/OBS features | Media |
| `pokemon/` | `files.save_pk3` | PKHeX-compatible .pk3 exports |
| `*.yml` (battle.yml, logging.yml, …) | user (optional) | Profile-level config overrides |

Profile-independent config lives directly in `profiles/*.yml` (copied from
`modules/config/templates/` on first run by `_initialise_config`,
`modules/context.py:17`); a profile's own YAML overrides it when
`context.config.load(profile.path)` runs at emulator start.

- `load_profile` (:56): validates `metadata.yml`, derives `last_played` from
  `current_state.ss1` mtime, finds the ROM by file name in `roms/` or by
  (game_code, revision, language) match; **exits the process** if the ROM is missing.
- Names starting with `_` are reserved/ignored (:42,:96).

### `modules/roms.py` — ROM detection

- `ROMS_DIRECTORY = <base>/roms` (:9). `list_available_roms()` (:181) scans every file,
  `load_rom_data()` (:279) sniffs magic bytes (0x96 at 0xB2 → GBA; Nintendo logo at
  0x104 → GB/GBC) and parses header fields (title @0xA0, game code @0xAC → language
  letter is the 4th char, revision @0xBC).
- **Whitelist by SHA-1**: `GBA_ROMS` (:19) enumerates every known-good dump of the 5
  Gen-3 games in 6 languages. Non-matching hashes are rejected (`InvalidROMError`)
  unless listed in the user-created escape hatch `profiles/extra_allowed_roms.txt`
  (:221 — hash, file name, or `*` per line), in which case the game is loaded but
  branded "Unsupported ..." (triggering the warning in `main.py`).
- `ROM` dataclass (:100) carries convenience predicates used *everywhere* for per-game
  branching: `is_rs`, `is_emerald`, `is_frlg`, `is_rse`, `is_gen3`, plus
  `id` = `game_code+language+revision` (e.g. `BPEE0`).
- Results are cached per path in `rom_cache` (SHA-1 of a 16 MB ROM is slow).

### `modules/save_data.py` — parsing the battery save

- `get_save_data()` (:142) pulls SRAM via `emulator.read_save_data()` and parses the
  Gen-3 flash layout: two 57 KB blocks (offset 0x0000 and 0xE000) of 14 rotating 4 KB
  sectors, each with section id, checksum, signature `0x08012025` and save counter.
  It validates checksums and returns the block with the higher save index — i.e. the
  most recent completed save.
- `SaveData` (:20) reassembles SaveBlock1 from sections 1-4 and exposes offline
  equivalents of live-memory readers: `get_player`, `get_party`, `get_pokemon_storage`
  (sections 5+), `get_item_bag`, `get_event_flag/var`, map coordinates. Used for
  save-integrity checks and the import flow without needing the game running.

### `modules/save_import.py` — importing external saves

`migrate_save_state(file, profile_name, rom)` (:15) creates a new profile from:
- an mGBA **savestate file** (magic `07 00 00 01`) — extended data blocks scanned for
  type=2 (embedded save data) (`get_state_data_from_mgba_state_file`, :80);
- an mGBA **PNG savestate** (`gbAs` state chunk + `gbAx` extension chunks, zlib) (:109);
- a **raw .sav** (signature at 0xFF8).

For savestates it identifies the matching ROM automatically via the CRC32 mGBA embeds
at state offset 8 (:63), scanning `roms/`. Writes `current_state.ss1` and/or
`current_save.sav` into the fresh profile. This is the backend of the GUI's import flow
(`modules/gui/create_profile_screen.py`). Note: `pokebot.spec` still builds an
`import.exe` from a root-level `import.py`, but that file does not exist in this
checkout, so only the GUI flow is functional here.

### `modules/files.py` — small file helpers

- `write_file` (:27): atomic write via temp file + `os.replace` (crash-safe stats/
  config writes). Note the `finally: return True` quirk — it *always* returns True if
  the temp file cleanup runs, even after an exception (a latent bug worth knowing).
- `save_pk3` (:81): exports a Pokémon to PKHeX `.pk3` under `profiles/<p>/pokemon/`,
  named `<dex> [★] - <species> - <nature> [<iv sum>] - <PID>.pk3`.
- `get/save_rng_state_history` (:108): dedupe list for soft-reset frame RNG, in
  `soft_reset_frames.json`.

### `modules/plugins.py` + `modules/plugin_interface.py` — plugin system

See dedicated section below.

### `modules/exceptions.py` / `modules/exceptions_hook.py`

- `PrettyException` (:6) subclasses carry a rich-formatted `message_template`,
  `recommendation`, and `exit_code`. `register_exception_hook()`
  (`exceptions_hook.py:30`) installs a `sys.excepthook` that pretty-prints these
  without a traceback for end users (full traceback in `--debug`). Non-pretty
  exceptions pass through untouched.

### `modules/console.py` (skim)

`console = rich.Console(theme=...)` (:223) — the global console with Pokémon-type
colours; `print_stats()` renders the big encounter panel (IV/SV tables) after each
logged encounter. Import it instead of `print`.

### `modules/keyboard.py` (skim)

Models the in-game naming-screen keyboard (pages/rows/columns loaded from
`modules/data/keyboard.json`, keyed per language) and provides a generator
(`handle_naming_screen`) that navigates the cursor and types a nickname — used when a
plugin's `on_should_nickname_pokemon` returns a name.

### `updater.py`, `requirements.py`, `pokebot.spec` — install/update flow

Current flow, relevant to building a custom installer:

1. **First run (source distribution):** `pokebot.py` → `check_requirements()`
   (`requirements.py:216`). A SHA-1 hash of (module list + Python version + libmgba
   version) is compared against `<base>/.last-requirements-check`; mismatch or absence
   triggers `update_requirements()` (:62), which:
   - enforces Python 3.11-3.13, 64-bit (hard exit otherwise; interactive override for
     *newer* Python);
   - pip-installs the pinned `required_modules` list (:14) one by one (`--user` unless
     in a virtualenv; asks for confirmation unless in a venv or called with
     `ask_for_confirmation=False`);
   - downloads and unzips the prebuilt **libmgba-py** binding from
     `github.com/hanzi/libmgba-py` releases into `<base>/mgba/` — platform-specific
     asset (win64 / ubuntu-lunar / macos-arm64 / macos-x86_64), version pinned by
     `libmgba_tag = "0.2.0-2"` (:10);
   - writes the hash file so this never re-runs until requirements or Python change.
2. **Auto-update:** `run_updater()` (`updater.py:92`) runs at startup only when *not*
   bundled and *not* a git checkout (`pokebot.py:146`), at most once per 24 h
   (`.last-update-check` timestamp). It queries the GitHub API for
   `40cakes/pokebot-gen3/releases/latest`, compares `tag_name` to `pokebot_version`,
   and on user confirmation downloads the first release asset (a zip) and **extracts it
   over the base directory in place**, then exits for a restart. No rollback, no
   partial-file protection — a custom installer could improve on this substantially.
3. **Bundled build:** `pokebot.spec` builds `pokebot.exe` + `import.exe` via
   PyInstaller (it first runs `update_requirements(ask_for_confirmation=False)` so all
   deps exist in the build env). Caveat: the spec references a root-level `import.py`
   that is absent from this checkout, so the `import.exe` part of the build would fail
   as-is. Data files bundled: `sprites/`, `modules/data/`.
   The dist folder is post-processed to include LICENSE, Readme, a `profiles/` dir with
   the template `*.yml`/`*.py`, and an empty `roms/` dir. In a bundle, requirements
   checking and the updater are both disabled (`is_bundled_app()` gates).

---

## The plugin system in detail

### Loading

- **User plugins** live in `<base>/plugins/*.py` (the directory ships empty with a
  `.gitkeep`). `load_plugins()` (`modules/plugins.py:21`) — called first thing in
  `pokebot.py:129` — imports every `.py` file as `plugins.<name>`, finds all classes
  subclassing `BotPlugin`, instantiates each with no arguments, and appends to the
  global `plugins` list. A plugin file with no `BotPlugin` subclass is a hard error.
- **Built-in plugins** (`modules/built_in_plugins/`) load later, in
  `main_loop()` via `load_built_in_plugins()` (`modules/plugins.py:44`), and only if
  config demands them: `GenerateEncounterMediaPlugin` (shiny GIFs / TCG cards; inserted
  at index 0 because it must run *first* to set `encounter.gif_path`/`tcg_card_path`
  for other plugins), `OBSPlugin` (obs.yml), `DiscordPlugin` (discord.yml).

### Hook points (`modules/plugin_interface.py`, class `BotPlugin`)

| Hook (line) | When it fires | Return value |
|---|---|---|
| `get_additional_bot_modes` (:13) | At mode-list build time (`modules/modes/__init__.py:68`) | Iterable of `BotMode` *classes* — this is how you add whole custom automations that appear in the GUI dropdown and `--bot-mode` |
| `get_additional_bot_listeners` (:27) | Whenever listeners are (re)built (`modules/modes/__init__.py:109`) — at profile load and after emulator reset | Iterable of `BotListener` *instances* (per-frame `handle_frame`) |
| `on_profile_loaded(profile)` (:46) | After profile selection, emulator running (`modules/main.py:56`) | — |
| `on_config_reload()` (:55) | User-triggered config reload (`modules/context.py:73`) | — |
| `on_battle_started(encounter)` (:62) | Battle screen entered (encounter is None for trainer battles) | may return a **Generator** |
| `on_wild_encounter_visible(encounter)` (:76) | "Wild X appeared!" fully on screen | may return a Generator |
| `on_battle_ended(outcome)` (:89) | Battle outcome known (still on battle screen) | may return a Generator |
| `on_logging_encounter(encounter)` (:102) | Every logged encounter (battles, eggs, gifts) | — |
| `on_pokemon_evolved(pokemon)` (:112) | After an evolution completes | may return a Generator |
| `on_egg_starting_to_hatch` / `on_egg_hatched` (:124/:136) | Hatching cutscene | Generator; `on_egg_hatched` may (also) return `True` to prevent auto-switch to Manual |
| `on_picked_up_items(items)` (:152) | After Pickup/Thief item collection | may return a Generator |
| `on_whiteout()` (:168) | After white-out dialogue, at Pokémon Center | may return a Generator |
| `on_judge_encounter(pokemon)` (:182) | During encounter evaluation | `False` = not interesting; a string = "keep, and here's why" (custom catch criteria) |
| `on_should_nickname_pokemon(encounter)` (:196) | Nickname prompt | nickname string (≤10 chars) or None |

**The generator-return convention is the key extension mechanism**: any hook documented
as "may return a Generator" gets that generator spliced into the frame loop via the
dispatcher functions in `modules/plugins.py` (:98-180) — the current bot mode is
suspended, your generator's `yield`s each advance one frame (you can press buttons,
wait for tasks, etc.), and when it finishes the mode resumes. Dispatchers iterate all
plugins in order; for `on_judge_encounter`/`on_should_nickname_pokemon` the first
non-False/non-empty result wins.

### Writing a custom plugin (recipe)

```python
# plugins/my_plugin.py
from typing import Generator, Iterable
from modules.context import context
from modules.plugin_interface import BotPlugin
from modules.modes import BotMode

class MyMode(BotMode):
    @staticmethod
    def name() -> str:
        return "My Custom Mode"

    def run(self) -> Generator:
        while True:
            context.emulator.press_button("A")
            yield              # advance exactly one frame

class MyPlugin(BotPlugin):
    def get_additional_bot_modes(self) -> Iterable[type[BotMode]]:
        yield MyMode           # class, not instance

    def on_battle_started(self, encounter):
        context.message = "Battle!"   # shows in GUI status
        # return a generator here to take over the frame loop
```

Useful helpers inside modes/plugins: `modules/modes/util/` (e.g. `wait_for_n_frames`,
navigation helpers), `modules/tasks.task_is_active`, `modules/memory.read_symbol`,
`context.bot_listeners.append(...)` for temporary listeners. Plugins survive bot
updates because `plugins/` is user territory (mirrored into bundles by the release
zip, preserved by the in-place updater since release zips don't include user files).

---

## Enhancement opportunities

- **Updater robustness** (`updater.py:92-114`): extraction happens directly over the
  live install with no backup, no hash verification of the downloaded zip, no restart
  automation, and `.last-update-check` gating is best-effort. A custom installer could
  do staged extract-to-temp + atomic swap + config/profile preservation guarantees.
- **`write_file` always returns True** (`modules/files.py:57`): the `return True` in
  the `finally` block swallows the `return False` from the exception path. Fix is
  one line; affects rng-history persistence error reporting.
- **Input API asymmetry** (`modules/libmgba.py:471`): `press_button`'s `inputs=`
  parameter is accepted but ignored (only `hold_button`/`release_button` honour it).
  Either implement or remove.
- **Headless mode still requires a TTY-friendly environment** and has no clean stop
  API — `main_loop` is an infinite `while True` with `sys.exit` on error. A supervised/
  embeddable runner (start/stop/pause, exception callbacks) would make the bot usable
  as a library.
- **`peek_frame` + `get_task_look_ahead`** (`modules/libmgba.py:558,634`) are powerful
  (savestate-rollback lookahead) but under-used; they enable "simulate n frames into
  the future, inspect RNG/task state, roll back" strategies — ideal for frame-perfect
  RNG manipulation features.
- **Work queue has no error handling** (`modules/main.py:74-77`): the drain runs
  *outside* the per-frame `try`, so an exception in a queued callback escapes to
  `main_loop`'s outer handler, which prints the traceback and kills the whole process
  (`sys.exit(1)`). Wrapping callbacks would isolate HTTP-triggered work.
- **Per-frame overhead**: `get_tasks()` re-reads and re-parses all 640 bytes of
  `gTasks` every frame plus a symbol lookup per task; the state cache helps within a
  frame but not across frames. A dirty-check on raw bytes before re-parsing would cut
  bot-side frame cost (`PerformanceTracker.time_spent_in_bot_fraction_history` exists
  precisely to measure this).
- **Plugin API lacks a generic per-frame hook with veto/priority semantics** — today
  you either add a `BotListener` (unordered, no priority) or a bot mode. A prioritized
  event bus would formalize what the "insert GIF plugin at index 0" hack works around
  (`modules/plugins.py:47-51`).
- **ROM whitelist UX**: `extra_allowed_roms.txt` (`modules/roms.py:221`) is
  undocumented in-app; ROM-hack support could be first-class (per-hack symbol tables
  are already half-supported via `modules/data/symbols/patches/`).

## For the Pokémon Emerald AI project

- **Frame-locked control loop is exactly what an AI agent needs**: the emulator only
  advances when `run_single_frame()` (`modules/libmgba.py:577`) is called, so an agent
  gets a fully synchronous observe→act→step API with zero race conditions. Pattern:
  set inputs → `run_single_frame()` → read memory/screen → repeat. No sleeping, no
  polling.
- **Inputs**: bitfield in `input_map` (`modules/libmgba.py:27`; A=0x1 … L=0x200).
  Use `set_inputs(bitfield)` for raw control or `press_button`/`hold_button` for
  edge/level semantics. Remember: the GBA registers a *new* press only after seeing a
  release frame — the XOR trick at `libmgba.py:476` handles this automatically.
- **Reading game state without pixels**: the pret symbol tables
  (`modules/data/symbols/pokeemerald.sym`, loaded by `modules/game.py:set_rom`) give
  named access to every RAM struct. Emerald specifics: SaveBlock1/2 are reached via
  the pointers `gSaveBlock1Ptr`/`gSaveBlock2Ptr` (`modules/memory.py:146`); event flags
  at SaveBlock1+0x1270, vars at +0x139C; 16/32-bit values XOR-encrypted with the key
  at SaveBlock2+0xAC (`modules/memory.py:185`). High-level screen detection =
  resolve `gMain.callback2` to a symbol name (`get_game_state`, `modules/memory.py:253`);
  fine-grained in-game activity = the `gTasks` task list and script context
  (`modules/tasks.py`). This whole stack is directly reusable as an AI's state encoder.
- **Headless & fast**: `--headless` + `-nv` + `-s 0` runs GUI-free, video-disabled
  (dummy renderer, `libmgba.py:296`), unthrottled — hundreds of fps for training.
  `PokebotHeadless` (`modules/gui/headless.py`) shows the minimal embed sequence:
  load profile → `context.config.load` → `set_rom(rom)` → construct
  `LibmgbaEmulator(profile, on_frame)` → call the loop. Screenshots still work while
  video is off via the savestate round-trip in `get_screenshot()` (`libmgba.py:514`)
  — that's the hook for pixel observations (240x160 PIL image via
  `get_current_screen_image()` when video is on).
- **Savestates as env resets**: `get_save_state()`/`load_save_state()` (bytes in
  memory, `libmgba.py:360-375`) give instant checkpoint/restore — ideal for episode
  resets, tree search, or the `peek_frame()` context manager (`libmgba.py:558`) which
  literally implements "simulate ahead, observe, roll back".
- **Determinism**: same savestate + same input sequence ⇒ identical trajectory (RNG
  is in RAM). The bot's soft-reset RNG history (`modules/files.py:108`) exists because
  of this.
- **Reusable infra**: ROM verification by SHA-1 (`modules/roms.py`), save parsing
  offline (`modules/save_data.py`), mGBA savestate/PNG import (`modules/save_import.py`),
  pk3 export (`modules/files.py:81`), and the plugin hook set — an AI driver could be
  written as a `BotPlugin` providing a single custom `BotMode` whose `run()` generator
  wraps the agent's policy loop, gaining the GUI, stats, and Discord layers for free.
