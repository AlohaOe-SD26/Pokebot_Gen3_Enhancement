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

## 8. Update (2026-07-18): global navigation now exists in our fork

The warp limitation in §4 is SOLVED in the enhanced fork
(sandbox-pokebot, pending promotion): `modules/warp_graph.py` extracts the
full world graph from map headers via the emulator (518 maps / 1268
directed warp edges for Emerald, 0.02 s, disk-cached per ROM — works at
the title screen, no save needed), and
`modules/modes/util/global_navigation.py::navigate_to_anywhere()` walks
any-map-to-any-map through doors/stairs/cave entrances (BFS over
connection-regions, per-leg warp traversal with verification). For the AI
project this means true world-scale macro-actions; Dive routes and
save-data dynamic warps remain excluded.

## 9. Update (2026-07-21): the Story bot as a reference playthrough + reusable techniques

Our fork now has a **Story-mode bot** (`sandbox-pokebot/plugins/custom_modes/story_mode.py`
+ `modules/story/early_game.py`) that plays a fresh save, *faithfully and unattended*, toward
the Elite Four — currently through Rustboro (Gym 1, PokéNav, rival) and into the Dewford arc.
For the AI project it is a **deterministic reference trajectory**: a scripted agent that makes
the same legitimate moves a player would, so you can (a) compare a learned agent against it,
(b) bootstrap/imitation-learn from it, and (c) reuse its per-area maps + the techniques below.

**Techniques we developed (all directly reusable by the AI project):**
- **Static ROM map recon (no navigation, no save):** `get_map_data((group, num), (0,0))` →
  any map's `.warps` (with resolved destinations), `.objects` (NPC/item `script_symbol`),
  `.connections` (the walk-between-maps graph), `.map_size`. We build per-area "Atlases" from
  this — accurate world structure for free. (See `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md`.)
- **Authoritative scripted-event logic = the pokeemerald decompilation** (fetch
  `raw.githubusercontent.com/pret/pokeemerald/master/data/maps/<Map>/scripts.inc` + `src/*.c`).
  This gives the EXACT flag/var/multichoice a scene needs — e.g. we found the Match-Call
  tutorial flow (`ScriptMenu_CreateStartMenuForPokenavTutorial`, POKéNAV = case 3), the rival
  gate (`VAR_RUSTBORO_CITY_STATE`), Briney's sail (Dewford = multichoice index 0), Steven's
  Letter (`FLAG_DELIVERED_STEVEN_LETTER` → TM47 Steel Wing). An RL/LLM agent can consult the
  same source to *understand* the game rather than brute-forcing it.
- **Renderer matters for app UIs:** the PokéNav (and similar full-screen apps) only advance
  with the **BG/OBJ renderer enabled** (`context.emulator.get_video_enabled()`); their looped
  tasks stall headless. If your env runs `--no-video`, either enable rendering for those
  interactions or drive the state directly. We also **read on-screen menus via screenshots**
  (`get_screenshot()`), which is how we scripted the PokéNav menu path.
- **Battle-behaviour rules the reference bot enforces** (worth encoding as constraints/priors):
  un-fleeable battles (trainer/gym/E4) must **fight through** to win-or-whiteout — never flee
  (raises) and never stall; a **switch target must be benched, non-fainted, non-active** (in a
  DOUBLE battle exclude the on-field partner); prep a boss with a **type-aware lead** (never
  lead a mon weak to the ace) + a **level floor** + a **safe heal** + a bounded **attempt-cap**.
- **Faithfulness discipline:** prefer natural play; a state-write (setting a var/flag to
  vanilla's exact end-state) is a documented last-resort fallback, renderer-gated
  (faithful-when-possible, deterministic-always). Useful if the AI project wants a "legit moves
  only" mode vs a "teleport/skip allowed" mode.
- **Full method** (harness, debugging, mapping, bug patterns) is in
  `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md` — a good read for anyone building on this env.

## 2026-07-22 — Ch6 (Briney sail) learnings for the AI project
- **Patrolling NPCs are a real interaction hazard.** Indoor NPCs with "Walk Sequence"
  movement types are almost never at their map-JSON spawn tile — they lap fixed routes
  (Mr. Briney + Peeko both circle the cottage table, same ring, Peeko ahead). Facts an
  agent needs: (a) a face-tap toward an EMPTY tile *steps* if already facing that way;
  (b) walk-sequence NPCs never re-route — stand on their next route tile and the whole
  room can deadlock (us included); (c) a tail-chase never catches a same-speed walker on
  a loop. The working policy (mirrors human play): watch one lap, stand BESIDE the route
  on a tile nobody visits, press A as the target walks past. Implemented as
  `_talk_to_wandering_npc` in the reference bot.
- **The stock pathfinder over-blocks around walkers** (each object's current AND previous
  tile), so "no path" inside small rooms is often false — an env for an AI agent should
  either expose raw passability or accept manual step actions indoors.
- **First Briney sail is a YES/NO, not the destination multichoice** (that appears from
  the second sail on). Confirming warps the player onto the boat and plays a ~75s scripted
  sail; arrival signal = current map becomes DEWFORD_TOWN (dock (12,3)).
- **Route 104 is one map ID but physically split by a river**; the only Rustboro→beach
  path is back through Petalburg Woods (warp pairs in design §Ch6). Good example of why
  "same map = reachable" is a false prior for navigation policies.

## 2026-07-22 — Ch7 (Granite Cave + Brawly) learnings for the AI project
- **Cave topology is a warp GRAPH, not a floor plan.** Every Granite Cave floor is split
  into disconnected walk-sections; reaching Steven takes a five-warp chain that dips a
  floor BELOW the target (1F→B1F→B2F→B1F→1F). An agent/env should model within-floor
  reachability between warps (computable statically with the pathfinder) rather than
  assume same-floor = reachable — and note reachability is DIRECTIONAL (one-way ledges:
  leaving Steven's area you can ledge-jump straight to the exit, but not back up).
- **Choosing "any reachable next warp" loops.** With one-way ledges, a greedy first-match
  policy rides the wrong ladder forever; ordering candidate hops by progress-along-route
  (furthest-along reachable) converges. Relevant to any learned/planned navigation policy.
- **Snapshot hygiene:** a save state captured mid-dialogue restores as permanently
  input-locked-for-navigation (only A/B advance). For RL checkpointing, only snapshot at
  stable-controllable overworld frames.
- **Party-composition beats levels at Brawly:** a natural L16-18 team wins via type choice
  alone (Bug/Poison Dustox resists Fighting and carries Confusion/Gust for 2×) — no
  grinding possible anyway (no land encounters around Dewford pre-Surf).

## 2026-07-22 — Ch8a (Slateport sail) learnings for the AI project
- **Object events are camera-loaded.** On town-sized maps an NPC's live object does not
  exist in RAM until the player is near it — an env exposing "visible objects" reflects
  the engine truth, but agents must not infer absence from it; walk toward the spawn
  first. (Bit us at the Dewford dock.)
- **Menu defaults matter.** Gen-3 `multichoicedefault` menus start the cursor on an
  arbitrary index (Briney's dock menu defaults to CANCEL); answers must be relative
  cursor moves, not absolute "press Down i times from the top".
- **Route 109 is a dense trainer gauntlet** (a dozen sight-lines) but the pathfinder's
  route dodges most of them; only ~2 battles fired on the validated crossing.
