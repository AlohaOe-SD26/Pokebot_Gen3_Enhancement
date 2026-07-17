# 04 — User-Facing Interfaces: GUI, Web/HTTP API, Streaming, Discord, Console

> Codebase: `pokebot-gen3/` (all paths below are relative to that folder unless absolute)
> Files covered: `modules/gui/*`, `modules/web/*`, `modules/discord.py`,
> `modules/built_in_plugins/discord_integration.py`, `modules/built_in_plugins/obs.py`,
> `modules/console.py`, `modules/keyboard.py`, `modules/debug.py`, `modules/debug_utilities.py`

## What this layer is FOR

The bot's *core* is a frame-synchronous loop (`modules/main.py:main_loop`) that drives libmgba
one frame at a time and lets the active bot mode inject inputs. Everything documented here is an
**observer/controller layered on top of that core** — the core runs identically whether you watch
it through Tkinter, a browser, a Discord channel, or not at all:

- **GUI (Tkinter)** — the default frontend. Draws the emulator's video output into a window, adds
  speed/mode/video/audio controls, profile creation/selection screens, and (in `--debug` mode) a
  large panel of live memory-inspection tabs plus save-editing tools.
- **Headless / GLFW frontends** — drop-in replacements for the GUI object
  (`modules/gui/headless.py`, `modules/gui/glfw.py`) that implement the same duck-typed interface
  (`run()`, `on_settings_updated()`, `is_headless`). `pokebot.py:149-160` picks one:
  `--headless` → `PokebotHeadless`, otherwise `PokebotGui` (with optional `use_opengl`).
  (Startup/CLI is documented fully elsewhere; the key point is the frontend is swappable.)
- **Web/HTTP API** — an aiohttp server in a separate thread exposing bot state as JSON, an SSE
  event stream, PNG video streaming, WebRTC audio/video, and a *limited* set of control endpoints.
  This is the substrate the stream overlay and any custom UI is built on.
- **Discord** — webhook notifications for shinies/milestones (a built-in plugin) plus Rich
  Presence.
- **Console** — `rich`-based pretty terminal output (encounter tables, IV colouring).

The crucial architectural device connecting the web thread to the emulator is the **work queue**
(`modules/main.py:19`): the HTTP thread never reads emulator memory directly (it could get
mid-frame garbage); instead it enqueues callbacks that the main loop executes between frames
(`modules/main.py:74-77`), usually to refresh an entry in `modules/state_cache.py`. The HTTP
handlers then serve the cached value (`modules/web/http.py:49-93`, `_update_via_work_queue`).

---

## 1. The Tkinter GUI

### 1.1 Window/screen structure (`modules/gui/__init__.py`)

`PokebotGui` owns a single root window (a `ThemedTk` — "equilux" theme if the OS is in dark mode,
"clam" otherwise; `__init__.py:31-36`) and swaps three "screen" objects in and out of it:

1. **`CreateProfileScreen`** (`create_profile_screen.py`) — shown on first launch (or via
   "+ New profile"). Presents a name entry (validated live against `^[-_a-zA-Z0-9 ]+$` and
   existing profile dirs, lines 94-132), a ROM combobox from `list_available_roms()`, and two
   actions: **Start New Game** (`create_profile`) or **Load Existing Save** — a `plyer`
   file chooser accepting `.sav`/`.ss0-9` files fed into `migrate_save_state()` (lines 164-197),
   which imports saves from other emulators. If no ROMs exist in `roms/`, a "missing ROMs" error
   screen with a retry button appears instead (lines 226-245). Includes a clickable Professor
   Birch sprite labelled "Very important." (line 75).
2. **`SelectProfileScreen`** (`select_profile_screen.py`) — a sortable `Treeview` of profiles
   (name / game / last-played), double-click to launch, Ctrl+F incremental filter (lines 109-141).
3. **`EmulatorScreen`** (`emulator_screen.py`) — the running-bot view (below).

`_run_profile()` (`__init__.py:132-151`) is the pivot: it sets `context.profile`, loads the
profile's config, constructs `LibmgbaEmulator(profile, self._emulator_screen.update)` — note the
GUI's `update` method is handed to the emulator as its **per-frame video callback** — and then
calls `self._main_loop()`, i.e. the bot core runs *inside* Tk's thread; `window.mainloop()` is
only used before a profile is chosen (`run()`, line 81).

### 1.2 How video reaches Tkinter (`modules/gui/emulator_screen.py`)

There is no game loop inside Tk. The emulator calls `EmulatorScreen.update()` after frames; that
method throttles to ~60 renders/sec (`update()`, lines 111-117), fetches the current 240×160 frame
via `context.emulator.get_current_screen_image()` (a PIL image), nearest-neighbour scales it by
the integer zoom factor, wraps it in `PIL.ImageTk.PhotoImage`, and draws it on a `Canvas`
(`_update_image()`, lines 227-236). Each render also pumps Tk manually with
`window.update_idletasks(); window.update()` (`_update_window()`, lines 238-243) — the GUI is
essentially "ticked" by the emulator, not by Tk's event loop. An optional experimental **OpenGL
path** (`glfw.py`, guarded import at lines 7-13) renders the raw frame buffer into a separate
GLFW window on a daemon thread instead.

When video is disabled (for speed), a placeholder image is drawn instead
(`_generate_placeholder_image()`, line 221) and rendering cost drops to nearly zero.

**Stepping mode** (lines 165-219, toggled by a hotkey): pauses the bot loop inside `update()` and
adds ⮜/⮞ buttons + Space / Ctrl+Space bindings to single-step frames forward and *backward* — it
keeps a 128-entry `deque` of full save states (line 21) and rewinds by reloading them. Invaluable
for debugging bot modes frame-by-frame.

### 1.3 Controls panel (`modules/gui/emulator_controls.py`)

`EmulatorControls` builds the strip below the canvas (only when zoom > 1; `scale` setter at
`emulator_screen.py:136-163` removes it at 1×):

- **Menu bar** (lines 47-89): Emulator (Load/New save state, Take Screenshot, Reset), Profile
  (Open Profile Folder, Reset Shiny Phase Stats — with a confirmation dialog, lines 322-339),
  Help (wiki + Discord links), and Debug (only in debug mode).
- **Bot Mode dropdown** (lines 144-200): lists Manual plus every registered mode from
  `get_bot_modes()`; each mode's `is_selectable()` is checked against the current game state and
  non-selectable ones are greyed out (lines 172-190). Selecting writes `context.bot_mode`.
- **Speed controls** (lines 202-248): 1× / menu (2-32×) / ∞ (unthrottled = speed 0).
- **Video / Audio toggle buttons** (lines 250-267), purple-highlighted when active.
- **Message area** (lines 269-274): displays `context.message` — the bot's one-line status string
  that modes set to communicate with the user.
- **Stats footer** (lines 310-320): FPS, speed multiple, encounters/hour, and (debug) bot-load %.

**Save-state loading** (`load_state_window.py`): a `Toplevel` grid of state thumbnails — state
files are PNGs with the actual savestate hidden in custom chunks, so the PNG itself *is* the
preview (lines 82-91). Loading a state forces Manual mode (line 32-33).

**Modal helpers** (`multi_select_window.py`): `ask_for_choice`, `ask_for_choice_scroll`, and
`ask_for_confirmation` — sprite-button dialogs used by bot modes to ask questions. Each has a
headless fallback that prompts on the console via `rich.prompt` when `context.gui.is_headless`
(lines 20-27, 106-108) — this is how the same bot modes work in both GUI and headless mode.
`ev_selection_window.py` is the same pattern for choosing EV-training targets.

**Desktop notifications** (`desktop_notification.py`): `notifypy` toast notifications, gated by
`config.logging.desktop_notifications`.

### 1.4 Keyboard input (`modules/gui/__init__.py:153-222`)

The root window binds all key press/release events. Mapping comes from the profile's key config
(`_apply_key_config`, lines 61-69): GBA buttons (only honoured in **Manual** mode — they call
`context.emulator.hold_button/release_button`) and emulator hotkeys (always honoured): reset,
save/load state, stepping mode, zoom in/out, **toggle_manual** (switch bot mode ⇄ Manual),
reload_config, toggle video/audio, speed presets 1×-32×/unthrottled, screenshot, exit
(lines 168-210). `context.gui.inputs_enabled` is set to False by debug-tab search fields so
typing there doesn't press GBA buttons (`debug_tabs.py:950-954`).

Note: `modules/keyboard.py` is **not** GUI input handling — it models the *in-game naming-screen
keyboard* (layouts per language from `data/keyboard.json`) and provides
`type_in_naming_screen(name)`, a generator that navigates the on-screen keyboard cursor to type a
nickname/player name (lines 146-222). It is bot-automation code, filed here only by name.

### 1.5 Debug mode tabs (`modules/gui/debug_tabs.py`, enabled by `--debug`)

In debug mode `EmulatorScreen._initialise_controls()` (`emulator_screen.py:55-66`) instantiates
`DebugEmulatorControls`, which adds a 550px-wide `ttk.Notebook` beside the canvas
(`emulator_controls.py:353-402`); only the *visible* tab updates each rendered frame
(`on_frame_render`, line 383-386). All tabs render into `FancyTreeview`
(`debug_tabs.py:77-235`), a generic key/value tree that reflects arbitrary nested Python
data (dicts, lists, objects with properties) and offers right-click actions (Copy Value + per-tab
extras). The tabs:

| Tab | Shows (source) |
|---|---|
| **Tasks** | The game's internal task list, main callbacks 1/2, global/immediate script contexts with symbol-resolved function pointers and stacks, battle callbacks in battle (`TasksTab`, lines 296-403). |
| **Battle** | `gBattleResults` decoded (faint/switch counters, catches, last moves, shiny flag) + current battle-script instruction symbol (lines 406-456). |
| **Player** | Player identity, money, avatar flags/position, game stats, full Pokédex seen/owned lists, entire party, item bag, item storage, Pokéblocks, all PC boxes (lines 671-816). |
| **Map** | A colour-coded minimap (collision red, encounters green, surf blue, jump cyan — `MapViewer`, lines 238-293) plus everything about the current map: tiles, warps, connections, loaded objects, object templates, coord/bg events, raw and *effective* encounter tables. **Clicking a tile on the game video selects it** and shows that tile's data with a dashed marker; selecting an object outlines it live (lines 1182-1601). |
| **Misc** | Daycare state (compatibility, offspring PV), roamer + location history, Feebas tiles, text printer, fade state, play time, RTC (lines 819-921). |
| **Symbols** | A live memory watch: any ROM symbol (from the game's symbol table `_symbols`) can be added via a searchable picker and displayed as hex/dec/bin/string (lines 459-668). |
| **Flags** | All event flags, searchable, with right-click **Toggle Flag** (writes memory; lines 924-974). |
| **Vars** | All event vars from save block 1, searchable, double-click to **set a value** (lines 977-1113). |
| **Emulator** | Held/pressed inputs, frame counters, RNG seed (`gRngValue`), encounter timing, controller stack, RTC override state, and `debug.action_stack` / `debug.debug_values` (lines 1116-1179). |

### 1.6 Debug menu — save manipulation (`modules/gui/debug_menu.py`)

A menu-bar cascade (debug mode only) offering active cheats/tools:

- **Edit Party / Edit Item Bag / Edit Pokédex** — full Toplevel editors
  (`debug_edit_party.py` — per-slot notebook editing species/level/moves/IVs/EVs/status;
  `debug_edit_item_bag.py`; `debug_edit_pokedex.py` — per-species seen/owned checkboxes with
  "Complete Hoenn"/"Complete All"/"Clear All" buttons).
- **Give Test Party / Test Item Pack / Lead with Ability** — one-click cheats (see §5).
- **Toggleable frame listeners** (lines 152-229, implemented as `BotListener`s injected into
  `context.bot_listeners`): Infinite Repel, Infinite Safari Zone, **Force Shiny Encounter**
  (rewrites the enemy party with a shiny clone at battle start, lines 172-212), Force PokéNav
  call.
- **RTC manipulation** — advance/rewind the emulated real-time clock by ±1h/±1day (lines 119-122).
- **Export/Import events and vars** to an INI-like text file; **Create state with save game**
  (a PNG savestate that also embeds the battery save, lines 43-61, used for the test suite).

---

## 2. Web / HTTP API (`modules/web/http.py`, `modules/web/http_stream.py`)

### 2.1 Lifecycle

Started from the core loop, *not* the GUI: `modules/main.py:60-66` — if
`config.http.http_server.enable` (default **off**, `modules/config/schemas_v1.py:237-242`,
default `127.0.0.1:8888`, configured in `profiles/<name>/http.yml` or global `profiles/http.yml`)
then `start_http_server()` (`http.py:965-977`) spins up an aiohttp `AppRunner` in its own thread
with its own asyncio loop. Because it starts inside `main_loop`, **the API only exists after a
profile is loaded** — profile selection cannot be done over HTTP.

An OpenAPI 3.0.3 spec is generated at runtime from the route docstrings via `apispec`
(lines 905-941): `GET /api.json` returns it, `GET /docs` redirects to a bundled Swagger-UI page
(`/static/api-doc.html`).

### 2.2 Endpoint reference

All responses are JSON unless noted. "(cached)" = served via the state cache + work queue.

| Path | Method | Payload | Purpose / returns |
|---|---|---|---|
| `/player` | GET | – | Player name, TID/SID, money etc. (cached) — `http.py:104` |
| `/player_avatar` | GET | – | On-map avatar: map group/number, x/y, facing, flags (cached) — `:129` |
| `/items` | GET | – | `{bag, storage}` — all items + quantities (cached, 1 s max age) — `:149` |
| `/party` | GET | – | Full detail of party Pokémon (cached) — `:177` |
| `/pokedex` | GET | – | Seen/caught lists (cached, 1 s) — `:195` |
| `/pokemon_storage` | GET | `?format=size-only` | All PC boxes, or just counts — `:215` |
| `/daycare` | GET | – | Daycare Pokémon, steps, compatibility — `:251` |
| `/opponent` | GET | – | Current battle opponent, or `null` outside battle — `:266` |
| `/map` | GET | – | Current map metadata + player position + **every tile's** data — `:291` |
| `/map_encounters` | GET | – | Regular + *effective* encounter rates (repel/lead-ability adjusted) — `:323` |
| `/map/{group}/{number}` | GET | – | Same map dump for an arbitrary map; 404 if invalid — `:344` |
| `/game_state` | GET | – | Coarse state name (`OVERWORLD`, `BATTLE`, `TITLE_SCREEN`, …) — `:389` |
| `/custom_state` | GET | – | Free-form dict writable by plugins (module-level `custom_state`, line 46) — `:408` |
| `/event_flags` | GET | `?flag=NAME` | All (or one) event flags — `:425` |
| `/encounter_log` | GET | – | Last 10 encounters, full detail — `:457` |
| `/shiny_log` | GET | – | All shiny phases — `:473` |
| `/encounter_rate` | GET | – | `{encounter_rate}` per hour — `:489` |
| `/stats` | GET | – | Global + phase totals per species — `:505` |
| `/fps` | GET | – | FPS history, last 60 s — `:521` |
| `/bot_modes` | GET | – | Names of all installed bot modes — `:540` |
| `/emulator` | GET | – | Speed, video/audio flags, bot mode, `context.message`, frame count, FPS, bot-load fraction, profile name, game/ROM info — `:555` |
| `/emulator` | **POST** | `{"emulation_speed": 0-32, "bot_mode": str, "video_enabled": bool, "audio_enabled": bool}` (any subset) | **Change emulator settings / switch bot mode.** Validates values (speed ∈ {0,1,2,3,4,8,16,32}; mode must be installed); returns updated GET body — `:592-660` |
| `/input` | GET | – | Currently pressed buttons as strings — `:662` |
| `/input` | **POST** | JSON array, e.g. `["B","Right"]`; `[]` releases all | **Set held buttons** — replaces all held inputs via the work queue. *Silently ignored unless bot mode is Manual* (`update_inputs`, lines 713-719). Returns 204 — `:677` |
| `/stream_events` | GET (SSE) | `?topic=X&topic=Y` (≥1 required) | Server-sent events stream, see §2.3 — `:723` |
| `/stream_video` | GET | `?fps=1-60` (default 30) | `multipart/x-mixed-replace` PNG frame stream of the emulator screen — `:860-903` |
| `/rtc` | POST | WebRTC SDP offer | WebRTC peer connection streaming **video + audio** (only if `aiortc` installed, else 503) — `:759-858` |
| `/api.json` | GET | – | Generated OpenAPI spec — `:936` |
| `/docs` | GET | – | Redirect to Swagger UI — `:943` |
| `/` | GET | – | Redirect to `/static/index.html` demo dashboard — `:953` |
| `/stream-overlay` | GET | – | Redirect to `/static/stream-overlay/index.html` — `:947` |
| `/static/*` | GET | – | Static assets (below) — `:957` |

### 2.3 The event stream (SSE) mechanism (`modules/web/http_stream.py`)

`GET /stream_events?topic=...` uses classic Server-Sent Events (`text/event-stream`; the
`EventSource` browser API). Topics are the `DataSubscription` flags (lines 26-48):
`Player, PlayerAvatar, Party, Pokedex, Opponent, WildEncounter, FishingAttempt, GameState, Map,
MapTile, MapEncounters, PokenavCall, BotMode, Message, EmulatorSettings, Inputs,
PerformanceData, CustomEvent`.

How it works: the first subscriber starts a watcher thread (`add_subscriber`, lines 126-157)
which polls at ~60 Hz (`run_watcher`, lines 175-408). For each topic with ≥1 subscriber it
checks whether the corresponding state-cache entry's frame number advanced (pushing a refresh
callback onto the main-thread work queue if the cache is stale) and emits an event only **on
change** — e.g. `MapChange` (full map dump) vs `MapTileChange` (just coordinates) (lines
309-333), `Opponent` becomes `null` when battle ends (line 283). A `Ping` event fires every
second (line 216); `PerformanceData` (fps/frame count/bot load/encounter rate) is also
per-second (lines 218-228). Slow clients whose 10-message queue overflows are disconnected
(lines 422-429). Plugins can push arbitrary strings to subscribers via
`send_custom_http_stream_event()` (lines 160-172). Client-facing documentation lives in
`modules/web/docs/event_stream.md`.

### 2.4 Static assets (`modules/web/static/`)

- `index.html` + `js/`/`css/` — a **demo dashboard** (self-described "example page… not meant to
  be used as a productive interface") that exercises the whole API: WebRTC video/audio, bot mode
  and speed `<select>`s, party/encounter panels.
- `api-doc.html` — Swagger UI.
- `map.html`, `world_map.html` — map viewers.
- `stream-overlay/` — a full OBS-ready browser-source overlay (config in `config.dist.js`,
  connection/state/layout JS, checklist/PSS/gym content components) driven entirely by the SSE
  stream + JSON endpoints.
- `sprites/` — the bot's whole sprite library served over HTTP: subfolders `pokemon/`,
  `pokemon-animated/`, `items/`, `badges/`, `types/`, `status/`, `pokeblocks/`, `tcg/`,
  `stream-overlay/`, `other/` (summary — thousands of files).
- TypeScript definition files (`pokemon.d.ts`, `routes.d.ts`, `stats.d.ts`,
  `stream_events.d.ts`, `stream-overlay/stream-overlay-config.d.ts`) documenting the JSON shapes
  — very useful for building a typed custom client.

### 2.5 Can a total custom interface be built on this API alone?

**Observation: yes, comprehensively.** Video (3 transports: PNG multipart, WebRTC, SSE-driven
polling), audio (WebRTC), and essentially all game state (party, boxes, items, map+tiles, flags,
stats, logs) are exposed, with push updates via SSE.

**Control: only partially.** What you CAN do remotely: switch bot mode (POST `/emulator` —
notably *without* the GUI's `is_selectable()` safety check, it only validates the name), set
emulation speed, toggle video/audio, and hold/release GBA buttons (POST `/input`, Manual mode
only). What you CANNOT do over HTTP today:

- **No profile selection/creation** — server starts after profile load (`main.py:60`).
- **No save-state operations** — no create/load state, no emulator reset, no screenshot-to-disk.
- **No single-frame screenshot endpoint** — a client must open `/stream_video` and take one frame
  (or use WebRTC). There is no `GET /screenshot`.
- **No timed button *press*** — `/input` only sets held buttons; a "press A for one frame"
  round-trip over HTTP is racy at 60 fps. (The GUI/core use `press_button` which is
  frame-accurate; the API doesn't expose it.)
- **No config/settings editing** (catch filters, battle strategy, cheats), **no stats reset**,
  **no shutdown/restart**, **no debug utilities** (flag/var *writing* is GUI-only; `/event_flags`
  is read-only), **no mode-specific parameters** (e.g. which starter to soft-reset for — those
  come from profile YAML or GUI dialogs like `ask_for_choice`, which in a headless+HTTP setup
  fall back to *console* prompts, invisible to an HTTP client).
- **No authentication whatsoever** — binding beyond 127.0.0.1 exposes full control to the LAN.

So a custom *dashboard/observer* interface needs nothing else; a custom *controller* interface is
viable for "pick a mode and watch" workflows, but full parity with the GUI requires adding
endpoints (see Enhancement opportunities).

---

## 3. Discord notifications (`modules/discord.py` + `modules/built_in_plugins/discord_integration.py`)

Configured by `discord.yml` (`schemas_v1.py:89-137`): a `global_webhook_url`, per-event
`DiscordWebhook` sections (each with `enable`, own `webhook_url`, `interval`, and
`ping_mode: user|role` + `ping_id` for @-mentions), a global `delay`, and `rich_presence`.

`modules/discord.py` is the transport: `discord_send(DiscordMessage)` enqueues onto an asyncio
queue consumed by a dedicated thread (`discord_message_thread`, lines 210-217). `_process_message`
(lines 54-132) builds a `discord-webhook` embed — title, description, fields, thumbnail/image
(attached as files; it *waits up to 5 s* for images like the encounter GIF or TCG card to be
generated by other threads, lines 62-76), footer defaulting to bot ID + game + version, timestamp
— and retries sending 3 times. `discord_rich_presence_loop` (lines 135-196) updates Discord Rich
Presence every 15 s: location, encounter totals + shinies, encounters/h, fps, with a game-specific
large image (Rayquaza for Emerald, line 144-145).

The *events* live in the plugin `discord_integration.py` (`DiscordPlugin.on_logging_encounter`,
lines 125-307), fired from the encounter-logging pipeline:

| Event | Trigger | Embed contents |
|---|---|---|
| Shiny encounter | `EncounterValue.Shiny` | Gold embed: nature/species/level/map, SV, IV table (ASCII box art, lines 26-40), held item, species + phase totals, phase records (IV/SV highs-lows, streak), shiny sprite thumbnail, encounter GIF |
| Blocked shiny | shiny on block list | Grey short version |
| Species milestone | every N total encounters of that species | Sprite + count |
| Shiny milestone | every N shinies of species | |
| Total-encounter milestone | every N overall | Random Poké Ball thumbnail |
| Phase summary | at `first_interval`, then every `consequent_interval` non-shiny encounters | Phase stats fields |
| Anti-shiny | `is_anti_shiny` (SV ≥ 65528) | Black embed |
| Custom catch-filter match | `EncounterValue.CustomFilterMatch` | Filter name + full stats |
| TCG card | if TCG-card generation enabled | Generated card image |

The **OBS plugin** (`built_in_plugins/obs.py`) is the streaming sibling: connects to
obs-websocket, can trigger the replay buffer hotkey and take OBS screenshots of the scene on
shiny encounters, optionally posting those screenshots to their own Discord webhook.

---

## 4. Console (`modules/console.py`)

A themed `rich.Console` singleton (line 223) with Pokémon-type colours as theme styles
(lines 13-36). `print_stats()` (lines 105-220) renders the per-encounter report: a panel titled
with the type-coloured species name, containing a general-info table (PID, level, gender, item,
nature, ability, hidden power, SV, Wurmple evolution), an IV table with per-value colour grading
(31 = yellow, 0 = purple, arrows for nature modifiers), moves/EV yield, and a phase-statistics
table across all encountered species. This is the primary "UI" in `--headless` mode.

---

## 5. Debug tooling (`modules/debug.py`, `modules/debug_utilities.py`)

`modules/debug.py` — tiny but central: `DebugUtil` holds `enabled`, an `action_stack`, and
`debug_values`. Its `@debug.track` decorator wraps bot-mode generator functions so that while
they run, their qualified name + args appear on `action_stack` (displayed live in the Emulator
debug tab and usable anywhere). This is how you see *what the bot is currently doing* at any
nesting depth.

`modules/debug_utilities.py` — the save/memory manipulation library backing the Debug menu:

- `export_flags_and_vars` / `import_flags_and_vars` (lines 51-109) — INI-style dump/restore of
  every event flag and var.
- `debug_create_pokemon` (lines 112-391) — builds a fully valid, encrypted 100-byte Pokémon data
  block from criteria (species/level/shiny/nature/IVs/EVs/moves…), brute-forcing a personality
  value that satisfies gender+nature+shininess (lines 326-356) and computing the checksum and
  substructure encryption exactly like the game. Custom mons are marked by Safari-Zone-met +
  Premier Ball so they are recognisable (lines 246-265).
- `debug_write_party` / `debug_write_item_bag` / `debug_write_pokedex` — direct writes to
  `gPlayerParty`, save-block item pockets (with quantity encryption via `decrypt16`), and Pokédex
  seen/owned bitfields including national-dex unlock (lines 394-455, 687-734).
- `debug_give_test_party` / `debug_give_test_item_pack` / `debug_give_max_coins_and_money` /
  `debug_give_fainted_first_slot_pokemon_with_special_ability` — canned cheats: a shiny 31-IV
  Mewtwo + False-Swipe/Spore Lotad catching lead + HM slaves; every ball/TM/berry/key item; a
  fainted level-1 lead with an encounter-affecting ability (Illuminate, Synchronize, etc.,
  lines 619-669) to bias wild encounters without affecting battles.

There is no free-form *memory search* tool; the closest is the Symbols debug tab (watch any
symbol, §1.5) plus raw `read_symbol`/`get_save_block` used throughout. Note `_symbols` /
`get_symbol_name_before` give full symbol-table lookup for arbitrary addresses.

---

### Enhancement opportunities

1. **Control-plane gaps for a total custom interface** (the project's stated goal): add HTTP
   endpoints for (a) frame-accurate `press_button` (accept a button list + hold-frames, executed
   via the work queue), (b) `GET /screenshot` returning one PNG, (c) save-state list/create/load,
   (d) emulator reset, (e) profile list/select (requires starting the server before profile load —
   currently structurally impossible, `main.py:60`), (f) write access to event flags/vars and the
   debug utilities, (g) config read/write, (h) stats reset. Most are thin wrappers over functions
   that already exist and are invoked by the GUI.
2. **Interactive prompts break headless/remote control**: bot modes call `ask_for_choice`, which
   in headless mode blocks on *console* input (`multi_select_window.py:20-27`) — invisible over
   HTTP. A "pending question" endpoint/SSE topic + answer POST would make every mode remotely
   drivable.
3. **No auth/CORS story** on the HTTP server — fine on localhost, needs at least a token if the
   custom UI runs on another device.
4. **POST `/input` is release-then-hold only and Manual-only**; it also bypasses nothing when
   ignored (silent 204) — a client can't tell its input was dropped. Return an error when not in
   Manual mode.
5. **POST `/emulator` bot_mode skips `is_selectable()`** — remote mode switches can put the bot
   into an immediately-erroring mode; mirroring the GUI's selectability check (and exposing it
   via `GET /bot_modes`) would help.
6. The Tk architecture (emulator ticks the GUI, blocking `while` loops with `update()` in modal
   windows, `os._exit(0)` on close, `__init__.py:87-104`) is functional but brittle; a custom
   interface should be built against the HTTP layer rather than extending Tkinter.

### For the Pokémon Emerald AI project

- **The HTTP API is a nearly ready-made AI observation/actuation harness**: an external agent can
  poll `/game_state`, `/map` (full tile passability/encounter data), `/player_avatar`, `/party`,
  `/opponent`, subscribe to `/stream_events` for push updates, watch the screen via
  `/stream_video` (PNG frames — directly consumable by a vision model), and act via
  POST `/input` (button holds, Manual mode) — i.e. observe + control loops need **no emulator
  integration work at all**, just `http.yml` enable.
- **Structured state beats pixels here**: the API exposes decoded RAM (exact tile collision maps,
  encounter tables, battle opponent stats/IVs, event flags), so an AI can play from *symbolic*
  state with vision as an optional extra — a large advantage over screenshot-only agents.
- **Latency/robustness caveats for an AI controller**: `/input` sets *held* buttons only, is
  ignored outside Manual mode, and HTTP round-trips are not frame-accurate; for precise play
  either add the press-with-duration endpoint (Enhancement #1a) or run the AI in-process as a
  custom bot mode / `BotListener`, which gets frame-synchronous `handle_frame` callbacks and
  `context.emulator.press_button`.
- **`custom_state` + `send_custom_http_stream_event` are the sanctioned plugin→client channels**
  (`http.py:46`, `http_stream.py:160`) — an in-process AI plugin could publish its own
  reasoning/telemetry to a custom dashboard without touching core code.
- **The debug layer is a scenario factory**: `debug_create_pokemon`, party/item/Pokédex writers,
  flag/var import-export, and PNG savestates with embedded saves (`debug_menu.py:43-61`) allow
  constructing arbitrary reproducible game situations for training/evaluating the AI.
