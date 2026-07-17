# Pokémon Emerald AI — Transfer Notes from pokebot-gen3

> Purpose: everything discovered in the pokebot-gen3 codebase (vendored in
> this repo at `40cakes repo/pokebot-gen3/`) that is useful to the separate
> **Pokémon Emerald AI** project — an AI that plays Pokémon Emerald. Written
> to be consumed standalone: paths below are relative to
> `40cakes repo/pokebot-gen3/` in the
> https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement repo (upstream:
> https://github.com/40Cakes/pokebot-gen3).
>
> Deep-dive docs behind every claim: `40cakes repo/DOCUMENTATION/00–05` in
> this repo (all statements verified against source at upstream commit
> `5dd898f8`, 2026-07-17).

## TL;DR — why this codebase matters to the AI project

pokebot-gen3 already solves the entire "environment" half of an
Emerald-playing AI: a deterministic, frame-steppable emulator harness with
symbolic (non-pixel) observations of the full game state, frame-perfect
input injection, instant savestate checkpointing, an accurate Gen-3 battle
math engine, and intent-level navigation primitives. An AI agent could be
built as a **plugin bot mode** on top of it and inherit all of this for
free, or these techniques can be lifted individually.

---

## 1. The emulator harness (a perfect synchronous RL-style env)

- The emulator only advances when Python calls
  `run_single_frame()` — set inputs → step → read state, completely
  race-free. The game is paused while the agent thinks
  (`modules/main.py:36`, `modules/libmgba.py:95`).
- **Headless + unthrottled**: `--headless --no-video -s 0` disables video
  layers and the audio throttle and runs at max CPU speed.
  `modules/gui/headless.py` (`PokebotHeadless`) shows the ~10-line embed
  sequence: profile → `set_rom` → `LibmgbaEmulator` → loop.
- **Inputs are a bitfield** (`modules/libmgba.py:27`): A=0x1, B=0x2,
  Select=0x4, Start=0x8, Right=0x10, Left=0x20, Up=0x40, Down=0x80,
  R=0x100, L=0x200, via `set_inputs()`. A re-press needs a release frame
  between presses; `press_button` handles that edge automatically.
- **Savestates are in-memory bytes** (`get_save_state`/`load_save_state`)
  → instant episode resets and checkpointing. The `peek_frame()` context
  manager literally implements "simulate N frames ahead, observe, roll
  back". Same state + same inputs = deterministic trajectory.
- **Deterministic RNG on demand**: the test harness forces outcomes by
  writing `gRngValue` (`set_next_rng_seed`, `tests/utility.py:385-394`;
  the frame-step loop is `_run_test`, `:271-324`) — that file is
  effectively a ready-made gym environment: headless libmgba, save-state
  injection, deterministic RNG, frame-step loop with task/script
  introspection.
- Pixel observations are also available if wanted: 240×160 PIL image via
  `get_current_screen_image()`.

## 2. Symbolic observation — read RAM by NAME, not address

- The pret decompilation **symbol tables** map names → RAM addresses per
  ROM revision: `modules/data/symbols/pokeemerald.sym`, plus
  `event_flags/emerald.txt` and `event_vars/emerald.txt`. Access layer:
  `read_symbol` (`modules/memory.py:43`), save-block reads with per-game
  offsets and the XOR "encryption" key (`modules/memory.py:119,176` —
  Emerald key at SaveBlock2+0xAC, event flags at SB1+0x1270, vars at
  +0x139C).
- **Screen/state detection without pixels**: `get_game_state()`
  (`modules/memory.py:253`) resolves `gMain.callback2` to a symbol name →
  enum (overworld, battle, menu, …). Finer granularity comes from the
  game's own task scheduler: `gTasks` parsing in `modules/tasks.py`, and
  script-stack introspection.
- **Frame-precise action gating** (know exactly when inputs register):
  `player_avatar_is_controllable()` (`modules/player.py:263`),
  `is_waiting_for_input()` (`modules/tasks.py:199`), battle menu detection
  `get_battle_menu()` (`modules/menu_parsers.py:293`).
- **Pokémon struct decoding**: 100-byte party / 80-byte box structure with
  PID%24 substructure permutation (`modules/pokemon.py:24`), PID^OTID XOR
  decryption (`:898`), checksum validation (`:959`), and PID-derived
  nature/gender/shininess/hidden-power (`:1240-1307`). Party via
  `get_party()`; **the full enemy team is readable** via
  `get_opponent_party()` (`modules/pokemon_party.py:155`) — perfect vs.
  fogged information is a design choice for the AI.
- All repeated reads go through a frame-stamped **state cache**
  (`modules/state_cache.py:301`): `age_in_frames == 0` → reuse, else
  re-read — this is what makes a full per-frame observation cheap.

## 3. Battle: observation space + an exact Gen-3 math engine

- `get_battle_state()` (`modules/battle_state.py:808`) is a near-complete
  battle observation: both actives' live/modified stats, stat stages,
  legal moves (`can_use_move` `:547` handles PP/Disable/Encore), ~35
  volatile statuses, side timers/screens, weather, turn count, outcome.
- `BattleStrategyUtil` (`modules/battle_strategies/_util.py`) reimplements
  the **exact Gen-3 damage formula, escape odds, and catch shake
  probability** — usable directly as a battle-AI evaluation function or as
  ground truth for training.
- A custom battle brain reduces to one method:
  `decide_turn(battle_state) -> (TurnAction, extra)` — menu execution, faints, move
  learning, evolutions are all handled by `handle_battle()`
  (`modules/battle_handler.py`).
- Outcomes are knowable before they render (useful for planning/reward
  shaping): shininess/nature are pure PID functions
  (`modules/pokemon.py:1257,1240`), daycare pre-rolls offspring PID
  (`modules/daycare.py:122`), true per-map encounter distributions via
  `get_effective_encounter_rates_for_current_map()`
  (`modules/map.py:2219`).

## 4. Navigation: act at waypoint granularity, not D-pad granularity

- `calculate_path()` (`modules/map_path.py:620`) runs A* over stitched
  multi-map coordinate spaces with real frame costs: surf transitions,
  waterfalls, currents, ice, ledges, live-NPC avoidance, event-trigger
  avoidance. Emits waypoints with attached actions (Surf/Waterfall/bike).
- Higher-level primitives already exist as generator helpers (doc 03):
  `navigate_to(map, coords)` (crosses directly-connected maps; a warp/door
  can be the *destination* but is not routed through, and surf entry/exit
  must be handled separately), `talk_to_npc`,
  `heal_in_pokemon_center`, `buy_in_shop`, `interact_with_pc`, `fly_to`,
  `use_field_move` — a ready-made **tool library for a planner/LLM agent**.
- Map decoding (`modules/map.py`, 2299 lines): ~200 tile behaviours,
  collision/elevation, connections, warps, NPC object events, wild
  encounter tables. Known gap: pathfinding can't route *through* warps
  (per-map-network only) — a warp meta-graph is the top enhancement
  opportunity if the AI needs global navigation.

## 5. Ready-made Gen-3 knowledge base (no ROM extraction needed)

- `modules/data/species.json`, `moves.json`, `types.json` (full type
  effectiveness matrix), `natures.json`, `abilities.json`, `items.json` —
  complete, directly loadable Gen-3 data for a battle AI.
- `modules/data/symbols/*.sym` + event flag/var name maps = the full
  name→address memory map of Emerald (also Ruby/Sapphire/FRLG).
- `GameStat` counters (`modules/game_stats.py:7`) — the game's own
  built-in counters (steps, battles, …) are ready-made reward signals.

## 6. Integration paths (cheapest first)

1. **In-process plugin bot mode** (recommended): one file in `plugins/`
   subclassing `BotPlugin`, whose `get_additional_bot_modes` returns a
   custom `BotMode`; its `run()` generator IS the agent's policy loop
   (each `yield` = one frame). Inherits GUI, stats, HTTP server, Discord.
   Goal injection seams: `on_battle_started` (return a `BattleStrategy`),
   `on_judge_encounter` plugin hook, `customcatchfilters.py`.
2. **Out-of-process via HTTP** (enable `http.yml`): observation is
   complete — PNG frame stream (`/stream_video`), decoded state (`/party`,
   `/opponent` incl. IVs, `/map` tile passability, `/game_state`, event
   flags), SSE push on 18 topics, Swagger at `/docs`. Control is partial:
   POST `/input` only sets **held** buttons, only in Manual mode, not
   frame-accurate; no profile-select/savestate/reset endpoints; no auth.
   Fine for an observing AI; precise play needs the in-process route or
   small API additions (documented in doc 04).
3. **Lift techniques standalone**: `tests/utility.py` (headless env +
   deterministic RNG), the symbol/memory layer, and the data JSONs are
   individually extractable with light dependencies.

## 7. Scenario construction for training/eval

- `modules/debug_utilities.py` is a scenario factory: fabricate fully
  valid encrypted Pokémon, rewrite party/bag/Pokédex, and import/export
  event flags/vars; the debug GUI menu (`modules/gui/debug_menu.py:54-57`)
  additionally exports PNG savestates with embedded battery saves —
  ideal for constructing reproducible eval situations (specific teams,
  specific map states) without playing to them.
- Profiles are self-contained folders (save + savestates + config +
  stats.db) — cheap to snapshot/copy per experiment. The stats DB stores
  the complete 100-byte Pokémon blob per encounter row, so it doubles as
  a replay/dataset format; the `base_data` key/value table is a sanctioned
  store for custom persisted state.

---

*Maintained as part of Pokebot_Gen3_Enhancement. Update this file whenever
new AI-relevant findings surface (it is referenced by the Emerald AI
project).*
