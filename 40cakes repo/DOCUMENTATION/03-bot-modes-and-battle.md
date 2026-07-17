# 03 — Bot Modes and the Battle Engine

Scope: `modules/modes/` (mode contract, listeners, asserts, util helpers, all 23 concrete
modes), `modules/battle_strategies/`, the battle engine (`battle_handler.py`,
`battle_action_selection.py`, `battle_menuing.py`, `battle_move_replacing.py`,
`battle_evolution_scene.py`), the encounter pipeline (`encounter.py`), and the supporting
automation modules (`safari_strategy.py`, `fishing.py`, `keyboard.py`, `menuing.py`,
`player_pc_navigaton.py`, `pokemon_storage_navigaton.py`, `pokeblock_feeder.py`,
`berry_trees.py`, `mart.py`). All paths are relative to the repo root
`pokebot-gen3/`.

---

## What this layer is FOR

Everything below `modules/modes/` is the bot's *behavior* layer. A **bot mode** is one
complete automated activity — "spin in the grass until a shiny appears", "soft-reset for a
starter", "hatch daycare eggs forever". The rest of the codebase (memory reading, map
data, emulator core) exists so that this layer can *observe* the game and *press buttons*.

The whole system is built on one control idea: **cooperative generators clocked by the
emulator frame loop**. A mode's `run()` method is a Python generator. Every time it
`yield`s, control returns to the main loop, exactly one GBA frame is emulated, and then
the generator is resumed. Pressing a button is a side effect (`context.emulator.press_button("A")`)
that takes effect on the *next* frame. This means bot logic reads like a
straight-line script ("walk here, talk to this NPC, mash A until the battle starts") while
actually being a frame-perfect state machine. There are no threads, no sleeps, no polling
loops with timers — a "wait" is simply a `while <memory condition>: yield`.

The main loop lives in `modules/main.py:36-142` (`main_loop()`). Per frame it:

1. Builds a `FrameInfo` snapshot (frame count, `GameState`, active game **tasks**, active
   game **scripts**, names of generators on the controller stack) — `main.py:90-97`.
2. Instantiates the selected mode if the controller stack is empty (`main.py:108-110`)
   and pushes `mode.run()` onto `context.controller_stack`.
3. Calls every registered `BotListener.handle_frame()` (battle detection, egg hatching,
   repel expiry, etc. — see below), which may *push additional generators* onto the stack.
4. Advances **only the top generator** on the stack (`next(context.controller_stack[-1])`,
   `main.py:118`). When a generator finishes (`StopIteration`), it is popped.
5. Any `BotModeError` raised inside a generator is caught, shown to the user as a message,
   and the bot drops back to Manual mode (`main.py:121-124`). This is the standard
   "graceful abort" mechanism — modes freely raise `BotModeError` for any precondition
   failure.
6. Runs one emulator frame (`context.emulator.run_single_frame()`).

`context.controller_stack` is therefore a *stack of nested behaviors*: the mode's `run()`
sits at the bottom, and event handlers (battle handling, trainer-approach dialogue,
white-out recovery…) temporarily stack on top of it, suspending the mode until they
finish. This is the single most important architectural pattern in the project.

---

## THE MODE CONTRACT (`modules/modes/_interface.py`)

`BotMode` (`_interface.py:24-211`) is the base class every mode extends. It is
deliberately small; a mode only ever *needs* to implement `name()` and `run()`.

### Identity & availability

- `name() -> str` (static, `:26`) — the label shown in the GUI's mode drop-down. Also the
  string stored in `context.bot_mode`.
- `is_selectable() -> bool` (static, `:33`) — a *rough* sanity check ("is the player on
  the right map / facing water?") that decides whether the mode appears in the drop-down.
  The docstring is explicit about the philosophy: keep this coarse and put the *precise*
  checks in `run()` as `BotModeError`s, so users see a meaningful error message instead of
  a mysteriously missing menu entry.

### Lifecycle

- `__init__()` (`:207`) immediately calls `self.run()` to create the generator
  (`self._iterator`); `__next__` (`:210`) delegates to it, so a `BotMode` instance *is*
  an iterator. The main loop constructs a fresh instance every time the mode starts (or
  restarts after the controller stack empties — which is how "loop forever" modes that
  `return` end up being re-entered).
- `run() -> Generator` (`:52`) — the actual behavior. Called once per frame *when it is
  the top of the controller stack*. Crucially, per its docstring: **when a battle starts,
  the battle handler takes over by default** and `run()` is not advanced until the battle
  is done. A mode can opt out of that by returning `BattleAction.CustomAction` from
  `on_battle_started()`, in which case in-battle frames flow to `run()` too. (Beware: the
  docstring itself names a `self.disable_default_battle_handler()` method as the opt-out —
  that method exists nowhere in the codebase; the stale docstring predates the
  `BattleAction.CustomAction` mechanism.)

### Event hooks (all optional overrides)

These are called by the `BotListener`s in `_listeners.py`, *not* by the game:

- `on_battle_started(encounter: EncounterInfo | None) -> BattleAction | BattleStrategy | None`
  (`:67`) — called when `GameState.BATTLE` is first reached. `encounter` is populated for
  wild battles, `None` for trainer battles. Return value semantics (this is the crux of
  battle integration):
  - `None` → default behavior: `handle_encounter()` decides (shiny → manual/catch, trash →
    run away).
  - `BattleAction.Fight` → fight using `DefaultBattleStrategy`.
  - `BattleAction.RunAway` → flee (wild battles only).
  - `BattleAction.Catch` → catch using `CatchStrategy`.
  - `BattleAction.CustomAction` → *the listener does nothing*; the mode's own `run()`
    keeps receiving frames and must handle the battle itself (used by soft-reset modes
    that only need to *see* the opponent, not fight it).
  - a `BattleStrategy` *instance* → fight using that strategy (how EV-train, level-grind,
    item-steal and lose-on-purpose modes inject custom battle brains).
- `on_battle_ended(outcome: BattleOutcome)` (`:89`) — battle result is known; modes use
  this to re-check Poké Ball supply, decide on healing trips, count catches, etc.
- `on_pokemon_evolving_after_battle(pokemon, party_index) -> bool` (`:99`) — allow/cancel
  an evolution (only consulted by the default strategy).
- `on_pickup_threshold_reached() -> bool` (`:116`) — gate the automatic post-battle Pickup
  item collection.
- `on_spotted_by_trainer()` (`:129`) — a trainer's `!` appeared; the listener will mash B
  through the approach dialogue, this hook is informational.
- `on_pokenav_call()` (`:139`) — Emerald PokeNav ringing (listener declines it).
- `on_repel_effect_ended() -> Generator | None` (`:145`) — after the listener closes the
  "Repel wore off" box; return a generator to e.g. apply another Repel (roamer modes do).
- `on_pokemon_fainted_due_to_poison(pokemon, party_index)` (`:154`) — overworld poison
  faint.
- `on_whiteout() -> bool` (`:164`) — return `True` to claim responsibility for a whiteout,
  otherwise the bot switches to Manual. Modes that *intentionally* lose (Nugget Bridge,
  Kecleon) or use the Pokémon Center loop return `True`.
- `on_safari_zone_timeout() -> bool` (`:178`) — kicked out of the Safari Zone (steps/balls
  exhausted); `True` = mode handles it.
- `on_egg_hatched(encounter, party_index) -> bool | None` (`:193`) — during the hatch
  cutscene, once the hatchling is visible; return `True` to suppress the automatic switch
  to Manual on a shiny hatch.

### Supporting types in the same file

- `BattleAction` enum (`:17`): `Fight | RunAway | Catch | CustomAction`.
- `BotModeError` (`:214`): the "abort politely" exception described above.
- `FrameInfo` (`:218-244`): per-frame snapshot with convenience predicates
  (`game_state_changed_to()`, `task_is_active()`, `script_is_active()`). Listeners key off
  this instead of re-reading memory.
- `BotListener` (`:247`): one-method interface `handle_frame(bot_mode, frame)`; listeners
  are the always-on "reflexes" while modes are deliberate plans.

### Registration & selection (`modules/modes/__init__.py`)

`get_bot_modes()` (`__init__.py:14-71`) holds the hard-coded list of the 23 built-in mode
classes **plus** anything returned by `plugin_get_additional_bot_modes()` — meaning *a
plugin can register new bot modes without touching core code* (see
`modules/plugin_interface.py`). `get_bot_mode_names()` prepends `"Manual"`;
`get_bot_mode_by_name()` resolves the GUI selection back to a class.
`get_bot_listeners(rom)` (`:84-111`) builds the listener set: Battle, Fishing, EggHatch,
TrainerApproach, Repel, Poison, SafariZone, Whiteout listeners always; PokenavListener on
Emerald only; plus plugin listeners.

### Precondition helpers (`modules/modes/_asserts.py`)

A library of `assert_*` functions that raise `BotModeError` with user-friendly text:
`assert_save_game_exists`, `assert_saved_on_map(SavedMapLocation(...))` (which parses the
raw save-file object-event table to check the *saved* player position/facing —
`_asserts.py:37-77`), `assert_registered_item`, `assert_has_pokemon_with_any_move`,
`assert_item_exists_in_bag`, `assert_empty_slot_in_party`,
`assert_boxes_or_party_can_fit_pokemon`, `assert_player_has_poke_balls`,
`assert_party_has_damaging_move`, `assert_pokemon_in_party_slot`. Most take a
`check_in_saved_game=True` flag because soft-reset modes must validate the *saved* state
(what will exist after reset), and they append a helpful "(This is only the case in the
saved game…)" hint when the live game would pass.

### The utility toolbox (`modules/modes/util/`)

Everything a mode's `run()` composes with `yield from`. Highlights (all generators unless
noted):

- **walking.py** — `navigate_to(map, coords)` (pathfinds via `modules/map_path.calculate_path`
  and walks there, `walking.py:314`), `follow_waypoints()` (frame-timeout based, raises
  `TimedOutTryingToReachWaypointError`; handles Surf/Waterfall waypoint actions —
  `walking.py:115-`), `follow_path()`, `walk_one_tile()`, `ensure_facing_direction()`,
  `wait_for_player_avatar_to_be_controllable/standing_still()`.
- **tasks_scripts.py** — the "wait for game engine state" primitives:
  `wait_until_task_is_active`, `wait_for_task_to_start_and_finish`,
  `wait_for_script_to_start_and_finish`, `wait_for_yes_no_question`,
  `wait_for_multiple_choice_question`, `wait_for_no_script_to_run`. These watch the
  game's own task/script schedulers (via `modules/tasks.py`) — the same symbols visible in
  `FrameInfo.active_tasks`. This is how the bot stays in sync with dialogue without OCR.
- **soft_reset.py** — `soft_reset(mash_random_keys=True)` (reboot + randomized intro
  mashing so the RNG seed differs) and `wait_for_unique_rng_value()` (waits until
  `gRngValue` differs from every previously-seen seed — the anti-duplicate backbone of all
  soft-reset hunting).
- **higher_level_actions.py** — `fly_to()`, `fish()` (drives `Task_Fishing` state machine,
  `:129`), `spin()` (rotate in place to trigger encounters without moving, `:154`),
  `heal_in_pokemon_center()`, `change_lead_party_pokemon()`, `save_the_game()`,
  `buy_in_shop()`/`sell_in_shop()` (uses `mart.py` parsers), `talk_to_npc()`,
  `mount/unmount_bicycle()`, `dive()`/`surface_from_dive()`, `put_pokeblock_in_feeder()`,
  `leave_safari_zone()`.
- **items.py** — `register_key_item()`, `use_item_from_bag()`, `apply_repel()` (raises
  `RanOutOfRepels`), `repel_is_active()`, `apply_white_flute_if_available()`,
  `teach_hm_or_tm()`, `apply_rare_candy()`, `scroll_to_item_in_bag()`.
- **event_flags_and_vars.py** — `wait_until_event_flag_is_true/false`,
  `wait_until_event_var_equals/not_equals`.
- **pc_interaction.py** — `interact_with_pc(actions)` with a declarative `PCAction` API
  (deposit/withdraw/release Pokémon or items) driving the storage-system UI.
- **pokecenter_loop.py** — `PokecenterLoopController` (`:23`): the reusable
  "grind loop" brain shared by Level Grind, EV Train (partially) and Item Steal: heal at
  the nearest Pokémon Center, walk back to the encounter tile, spin/fish until the party
  needs healing, repeat; handles whiteouts by walking out of the Center and re-healing.
  Modes delegate `on_battle_started/on_battle_ended/on_whiteout` straight into it.
- **_util_helper.py** — `isolate_inputs` decorator (`:6`): snapshots & clears held
  buttons before a generator and restores them after, so nested handlers don't inherit a
  held B button. Used liberally by listeners.
- **sleep.py** — `wait_for_n_frames(n)`.

### How you'd write a new mode (walkthrough)

The simplest real mode is **Spin** (`modules/modes/spin.py`, 28 lines):

```python
class SpinMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Spin"

    @staticmethod
    def is_selectable() -> bool:
        return get_player_avatar().map_location.has_encounters

    def on_battle_ended(self, outcome: "BattleOutcome") -> None:
        if outcome is not BattleOutcome.Lost:
            assert_player_has_poke_balls()
            assert_boxes_or_party_can_fit_pokemon()

    def run(self) -> Generator:
        assert_player_has_poke_balls()
        assert_boxes_or_party_can_fit_pokemon()
        yield from apply_white_flute_if_available()
        yield from spin()
```

The recipe, generalized:

1. Subclass `BotMode`, implement `name()` and a *coarse* `is_selectable()`.
2. In `run()`, first validate everything precisely with `_asserts` helpers (raise
   `BotModeError` for anything wrong — never crash silently).
3. Express the behavior as `yield from <util helper>` calls plus raw
   `while <condition>: press_button(); yield` loops for anything bespoke.
4. Don't handle battles yourself: when an encounter starts, the `BattleListener`
   suspends your generator, runs the encounter pipeline + battle handler on top of the
   controller stack, and resumes you on the overworld afterwards. Override
   `on_battle_started()` only if you want a non-default action or a custom
   `BattleStrategy`; override `on_battle_ended()` for post-battle bookkeeping.
5. Register the class in `get_bot_modes()` — or ship it as a plugin via
   `plugin_get_additional_bot_modes()`, which is the intended path for custom
   automations.
6. State that must survive across listener callbacks goes in `self._fields` set in
   `__init__` (call `super().__init__()` *after* initializing anything `run()` reads,
   since `super().__init__()` creates the generator — see `FeebasMode.__init__`,
   `feebas.py:136-141`).

---

## Per-mode catalog

All `run()` line references are to the mode file named.

- **Spin** (`spin.py:24`) — all games. Rotates in place on an encounter tile
  (`spin()` util) to farm wild encounters without step-count risk; applies White Flute
  first. The canonical minimal mode.
- **Sweet Scent** (`sweet_scent.py:24`) — all games. One-liner: uses the field move
  Sweet Scent via `use_field_move()` to force an instant encounter; the mode re-runs
  automatically each time the controller stack empties, producing an encounter loop.
- **Fishing** (`fishing.py:29`) — all games. Faces water, ensures a rod is registered to
  Select (asks the user which rod via GUI `ask_for_choice` if several), then loops
  `fish()` forever. `FishingListener` (in `_listeners.py:310`) independently logs
  attempt/bite/landed stats by watching `Task_Fishing`'s data words.
- **Acro Bike Bunny Hop** (`bunny_hop.py:29`) — R/S/E only. Registers the Acro Bike and
  holds/releases B in sync with `AcroBikeState`/`TileTransitionState` to bunny-hop in
  place, which rolls encounter checks per hop without moving. A nice example of raw
  per-frame input logic instead of util helpers.
- **Starters** (`starters.py:222`) — all games, three sub-flows chosen by save location:
  FR/LG lab balls (`run_frlg`, `:28`), R/S/E Hoenn bag on Route 101 (`run_rse_hoenn`,
  `:80`), Emerald Johto starters in Birch's lab (`run_rse_johto`, `:145`). Soft-reset
  loop: `soft_reset()` → `wait_for_unique_rng_value()` → scripted A/B mashing through the
  gift dialogue (task-based waits) → `handle_encounter()` on the received Pokémon. The
  Hoenn variant waits for the starter to be *visible* in the first battle (watching the
  main battle callback, `:131-140`) before judging, to mimic human play; it receives the
  encounter via `on_battle_started` capturing `self._active_encounter` because the starter
  appears in a battle. Uses `BattleAction.CustomAction` so the reset loop keeps control.
- **Static Soft Resets** (`static_soft_resets.py:109`) — all games. Table-driven
  (`_get_targeted_encounter()`, `:34`) soft-reset hunting for stationary legendaries/
  gifts-in-battle (Snorlax, birds, Mewtwo, Regis, Rayquaza, Deoxys, Groudon/Kyogre…);
  selectable only when facing a known tile. After reset it waits for the two
  `Task_DuckBGMForPokemonCry` activations (first cry = pre-battle, second = opponent fully
  visible) then judges the opponent. `on_battle_started` (`:103`) returns
  `CustomAction` for trash so the loop resets, and hands shinies to `handle_encounter`.
- **Static Gift Resets** (`static_gift_resets.py:96`) — all games. Same soft-reset
  skeleton but for out-of-battle gifts (Lapras, Hitmons, fossils, Eevee, Magikarp,
  Castform, Beldum, Wynaut/Togepi eggs). A large per-game/per-gift dialogue matrix of
  task waits; for the two egg gifts it then rides a bike back and forth between two
  waypoints until `on_egg_hatched` fires (`:86`), popping the controller stack itself for
  non-interesting hatches. For non-egg gifts it opens the party summary screen to make the
  sprite visible before `handle_encounter(..., disable_auto_catch=True)`.
- **Static Run Away** (`static_run_away.py:50`) — Emerald + FR/LG. For respawning
  statics (Lugia, Ho-Oh, Regis, Lati@s, Kyogre/Groudon caves, Rayquaza, Mew). A big
  `match` on the current map defines a per-target `path()` generator that leaves the room
  and returns (statics respawn on re-entry), then mashes A to start the battle; the
  default encounter pipeline runs away from non-shinies. No soft resets, so it's fast and
  save-independent.
- **Roamer (Reset)** (`roamer_reset.py:87`) — all games. Creates a *new* roamer via
  soft reset (Latias/Latios TV choice in Emerald at `run_emerald` `:153`; Sapphire/ferry
  sequence in FR/LG at `run_frlg` `:240`; R/S TV at `run_rs` `:308`), then flies to the
  hunting corridor and loops: apply Repel (party level window enforced so *only* the
  roamer can appear), spin-face in grass, force map transitions (the game avoids spawning
  the roamer on the player's last three maps), until `on_battle_started` (`:78`) sees the
  roamer. Shiny → keep; otherwise sets `_should_reset` and the loop soft-resets. Handles
  `RanOutOfRepels` by resetting.
- **Roamer (Re-Encounter)** (`roamer_reencounter.py:72`) — all games. For an *existing*
  roamer: same Repel + map-transition dance between Slateport/Route 110 (or Pallet/Route
  1) but without resets; on encounter it simply switches to Manual for the user to fight
  (roamers flee, so catching is user business). `on_repel_effect_ended` re-applies Repel.
- **Daycare** (`daycare.py:67`) — all games (Route 117 / Four Island). Infinite egg
  production line: warns about incompatible parents (`DaycareCompatibility`), acquires and
  registers the Mach Bike (buying one in Mauville if needed!), then cycles a four-point
  bike path in front of the daycare. Dynamic waypoint generator (`get_path()`, `:217`)
  breaks out when an egg is ready (`PENDING_DAYCARE_EGG` flag → talk to the daycare man,
  `handle_egg_collecting` `:153`) or the party is full of hatched non-keepers → releases
  them at the daycare PC via `interact_with_pc(PCAction.release_pokemon_from_party(...))`
  (`pc_release`, `:184`), judging keepers with `judge_encounter()`. `EggHatchListener`
  does the actual hatching UI work and shiny checks.
- **EV Train** (`ev_train.py:152`) — all games with a Pokémon Center near an encounter
  map. GUI window (`ask_for_ev_targets`) collects per-stat EV goals; validates totals
  (≤510, ≥current). Loop: heal (or exit Center after whiteout), walk to the training
  tile, `spin()`. `on_battle_started` (`:105`) computes whether the opponent's EV yield
  (× Macho Brace ×2, × Pokérus ×2) still *fits* the targets: fight with
  `NoRotateLeadDefaultBattleStrategy` (a one-off subclass that never rotates the lead,
  `:80`) or `RunAway` for useless yields. `on_battle_ended` prints a rich progress table
  and raises `BotModeError` when targets are reached.
- **Level Grind** (`level_grind.py:49`) — all games near a Pokémon Center. Asks whether
  to level the lead only (`LevelUpLeadBattleStrategy`) or level-balance the whole party
  (`LevelBalancingBattleStrategy`, which also rotates the lowest-level member into the
  lead slot before starting). Everything else is delegated to
  `PokecenterLoopController` (heal → walk to grass → spin → fight → repeat).
- **Item Steal** (`item_steal.py:47`) — all games near a Pokémon Center; requires
  Thief/Covet. `PokecenterLoopController` with `battle_strategy = ItemStealingBattleStrategy`;
  `on_battle_started` (`:36`) pre-screens the species and returns `RunAway` if the species
  can't even hold an item. Stolen items are automatically un-equipped after battle by the
  `BattleListener`'s `retrieve_held_items` flow (`_listeners.py:234`).
- **Safari** (`safari.py:102`) — FR/LG + R/S/E Safari Zones. The most orchestrated
  catching mode: GUI target-species picker (from `safari_strategy.py` per-game tables of
  species → map, tile, hunting method), verifies method requirements (Surf badge, rods,
  bikes), optional Repel and Pokéblock-feeder usage, then enters the zone via scripted
  NPC dialogue, follows a curated multi-map `get_navigation_path()`, and spins/fishes on
  the target tile. Money/ball accounting in `on_battle_ended` (`:84`) decides between
  re-entering (pay again) and soft-resetting to refund cash (`_money_spent_limit`).
  Actual in-battle catching uses `CatchStrategy.decide_turn_in_safari_zone` (below).
- **Rock Smash** (`rock_smash.py:139`) — R/S/E. Two hunts: Nosepass in Granite Cave
  (scripted round of the six smashable rocks with optional Repel + level-13 lead trick,
  `granite_cave()` `:323`) and Shuckle in Emerald's Safari Zone (`safari_zone()` `:441`,
  with step-counter awareness to bail before being kicked out). Its
  `on_battle_started` (`:88`) is notable: it detects *duplicate RNG streams* by checking
  each encounter's PV against the stats DB and injects one-frame delays to desynchronize —
  plus a live "Nosepass per Hour" debug metric.
- **Feebas** (`feebas.py:170`) — R/S/E Route 119 while surfing. Systematic search of
  every fishable tile (Feebas lives on 6 random tiles): builds a `FishingSpotList` of all
  accessible water tiles (`:36-97`), fishes each up to 3 times, marks failures, navigates
  to the nearest neighbor of the next untested tile. `on_battle_started` (`:143`) updates
  the search state — a Feebas encounter locks the tile; 20 consecutive non-Feebas bites
  after a find triggers a re-search (tile set re-randomized by date changes etc.).
- **Nugget Bridge** (`nugget_bridge.py:44`) — FR/LG only. Money farm: with a single
  level ≤6 Pokémon, repeatedly loses (`LoseOnPurposeBattleStrategy`) to the Route 24
  Rocket who gives a Nugget *before* the fight; whiteout returns you to the Cerulean
  Center. `on_whiteout` returns `True` so the loop continues; the message line shows
  cumulative nugget value.
- **Kecleon** (`kecleon.py:49`) — Emerald only. Farms the *one* Route 119 Kecleon by
  Selfdestructing against it (`LoseOnPurposeBattleStrategy`), whiting out (heal spot must
  be Fortree), and re-approaching — since the static respawns if you never defeated it.
  Requires Devon Scope, single-member party. Mach Bike waypoint variant included.
- **Sudowoodo** (`sudowoodo.py:37`) — Emerald Battle Frontier. Soft-reset hunt: save in
  front of the tree with Wailmer Pail registered, reset → unique RNG → use pail (Select)
  → mash through cries. `on_battle_started` (`:31`) logs and returns `CustomAction` so the
  reset loop continues for non-shinies.
- **Game Corner** (`game_corner.py:40`) — FR/LG. Soft-resets buying a chosen prize
  Pokémon (Abra/Clefairy/Dratini/Scyther/Pinsir/Porygon; menu navigation differs per
  version) with coins restored on every reset; opens the summary screen and judges via
  `handle_encounter` (gift-type encounter).
- **Berry Blend** (`berry_blend.py:37`) — R/S/E. Not a hunting mode at all: a
  frame-perfect Berry Blender player. Reads the blender's RAM struct (arrow position,
  speed, per-player hit ranges) and presses A exactly when the arrow will be in the hit
  zone next frame (`:105-121`), alternating A/L to exploit the L=A setting. Deliberately
  misses once progress > 950 RPM logic inverts. Great reference for direct-RAM
  minigame automation.
- **Puzzle Solver** (`puzzle_solver.py:107`) — R/S/E + FR/LG. Scripted walkthroughs of
  environmental puzzles: Mirage Tower, Sky Pillar, the three Regi chambers (including the
  Braille interactions, Dig/Fly requirements), Birth Island's Deoxys triangle, Pacifidlog
  currents, Seafloor Cavern, Tanoby Key, plus Route 113 ash collecting for the Glass
  Workshop (1,000 ashes, then hands back to Manual). Each map gets a `path()` generator of
  navigation + `use_rock_smash`/`use_strength`/`dive()` calls; `on_battle_started`
  auto-battles interruptions. Not a loop — it ends back in Manual when solved.

(23 built-in modes + `ManualBotMode` in `main.py:27`, which just `yield`s once and lets
the listener set run for logging purposes.)

---

## Frame listeners (`modules/modes/_listeners.py`) — the bot's reflexes

Listeners run every frame *before* the top generator is advanced, and react to game
events regardless of what the mode is doing:

- **BattleListener** (`_listeners.py:71`) — the bridge between overworld modes and the
  battle engine. Detects battle start via game state ∈ {BATTLE, BATTLE_STARTING,
  BATTLE_ENDING} or `Task_BattleStart` (`:84`). Once `GameState.BATTLE` is confirmed it
  builds an `EncounterInfo` for wild battles (`:95-106`), calls the mode's
  `on_battle_started()`, coerces the answer (trainer battles are always fought; tutorial
  battles are always CustomAction; `None` → `handle_encounter()`), then pushes the
  matching generator onto the controller stack: `fight(strategy)` (`:206`),
  `catch()` (`:261`), or `run_away_from_battle()` (`:280`) — all wrapped in
  `isolate_inputs`. It also delays encounter *logging* until the "Wild X appeared!"
  text is on screen (`:163-195`) so screenshots/GIF plugins capture a visible sprite.
  On battle end it fires `on_battle_ended` + stats logging, then waits for the overworld
  to be fully restored before clearing its in-battle flag (`:148-157`). The `fight` path
  additionally handles post-battle chores: collecting Pickup/stolen items via the party
  menu (`retrieve_held_items`, `:234`) and rotating the lead if the strategy requests it.
  The `catch` path optionally saves the game after a successful catch (leaving the Safari
  Zone first if necessary, `:265-276`).
- **TrainerApproachListener** (`:288`) — sees the trainer-approach script and mashes B
  through the intro dialogue (battle start is then handled by BattleListener), calling
  `on_spotted_by_trainer()` first.
- **FishingListener** (`:310`) — passively decodes `Task_Fishing` to log rod usage and
  bite/escape/encounter outcomes into the stats DB.
- **PokenavListener** (`:345`, Emerald) — declines Match Call calls with B, logs them.
- **EggHatchListener** (`:368`) — watches the egg-hatch script; in bot modes pushes
  `handle_hatching_egg()` which mashes B through the cutscene, optionally typing a
  nickname (plugin hook + `handle_naming_screen`), reads the hatch-scene struct to know
  when the hatchling sprite is visible, then calls `on_egg_hatched()` and routes the new
  Pokémon through `handle_encounter()`/`log_encounter()`.
- **RepelListener** (`:437`) — closes the "Repel wore off" message and then runs the
  mode's `on_repel_effect_ended()` generator if one is returned.
- **PoisonListener** (`:466`) — detects the overworld poison-faint script, reports
  fainted-by-poison Pokémon to the mode, closes the message.
- **WhiteoutListener** (`:498`) — mashes through the entire whiteout sequence (multiple
  script/task phases) until the player stands at the heal spot, then asks the mode via
  `on_whiteout()`; if unhandled → Manual mode.
- **SafariZoneListener** (`:542`) — detects the times-up / out-of-balls scripts, waits
  until the player is back at the entrance, then `on_safari_zone_timeout()`.

The idiom `if self.handler.__qualname__ not in frame.controller_stack` prevents a
listener from stacking its handler twice — the controller stack doubles as a re-entrancy
guard.

---

## The battle engine

### Detection → decision → execution

1. **Detection** is the BattleListener (above).
2. **Decision** is a `BattleStrategy` object.
3. **Execution** is `handle_battle(strategy)` in `modules/battle_handler.py:37` — a
   generator that runs until `battle_is_active()` goes false. Each frame it inspects the
   game's *battle script instruction pointer* and *battle callbacks* (symbols decoded by
   `battle_state.py`) and dispatches:
   - main callback `HandleTurnActionSelectionState` → `handle_battle_action_selection(strategy)`
     (a new turn needs input);
   - `BattleScript_ItemSteal` → record what the opponent stole / we stole
     (`handle_item_stealing`, `:137`);
   - `BattleScript_AskToLearnMove` → `handle_move_replacement_dialogue(strategy)`;
   - `Task_EvolutionScene` active → `handle_evolution_scene(strategy)`;
   - own side fainted → `handle_fainted_pokemon(strategy)` (`:155`) — asks the strategy
     whether to flee (`should_flee_after_faint`) or which party index to send out
     (`choose_new_lead_after_faint`), carefully mapping *overworld* party order to
     *in-battle* party order (`:192-243`);
   - caught-Pokémon nickname prompt → `handle_nickname_caught_pokemon` (`:248`, plugin
     may supply a nickname → `keyboard.handle_naming_screen`);
   - anything else → press B (dismiss text, decline things).
   On completion it diffs party state before/after (HP/status damage, EXP gains,
   evolutions, Pickup items, stolen items, money delta) into a `HandledBattleResult`
   (`:119-128`) that the BattleListener uses for post-battle chores.

### Turn input plumbing (`battle_action_selection.py`, `battle_menuing.py`)

`handle_battle_action_selection(strategy)` (`battle_action_selection.py:21`) loops while
the game is asking for turn input. It figures out *which* battler is being asked (single,
double left = controller 0, double right = controller 2, Safari) by reading per-battler
controller callbacks, then calls the matching strategy method
(`decide_turn` / `decide_turn_in_double_battle` / `decide_turn_in_safari_zone`) and
executes the returned `(TurnAction, argument)` tuple:

- `UseMove*` → `battle_action_use_move` (`:229`): choose FIGHT, scroll the move cursor
  (`scroll_to_move`), handle the Struggle edge case, and drive the double-battle target
  selector (`gMultiUsePlayerCursor`) to hit the intended slot.
- `UseItem` → `battle_action_use_item` (`:162`): open Bag, `scroll_to_item_in_bag`,
  optionally pick a target party member (healing items).
- `RotateLead` → scroll to PkMn action, party menu scroll, confirm (`:87-108`), with
  overworld→battle index mapping.
- `RunAway` / Safari actions (ThrowBall / GoNear / Pokeblock / Bait / Rock) → the
  corresponding menu slot; `battle_action_use_pokeblock` (`:183`) even scrolls the
  Pokéblock case by reading its scroll struct.
- `SwitchToManual` → `context.set_manual_mode()`.

`battle_menuing.py` is the tiny cursor library: `scroll_to_battle_action` and
`scroll_to_move` read `gActionSelectionCursor` / `gMoveSelectionCursor` and press
directional buttons until the cursor index matches (3rd byte used for the right-side
Pokémon in doubles).

### The `BattleStrategy` interface (`modules/battle_strategies/_interface.py`)

Ten decision points (`_interface.py:8-101`): `party_can_battle()`,
`pokemon_can_battle(pokemon)`, `which_move_should_be_replaced(pokemon, new_move)`
(return 0–3 to replace, 4 to refuse), `should_allow_evolution(pokemon, index)`,
`should_flee_after_faint(battle_state)`, `choose_new_lead_after_battle()` (post-battle
rotation), `choose_new_lead_after_faint(battle_state)`, `decide_turn(battle_state)`,
`decide_turn_in_double_battle(battle_state, battler_index)`,
`decide_turn_in_safari_zone(battle_state)`. Turn decisions are expressed with the
`TurnAction` / `SafariTurnAction` enum factories (`use_move(i)`, `use_item(item)`,
`rotate_lead(i)`, `run_away()`, `switch_to_manual()`, `throw_ball()`, `pokeblock(i)`, …).

### Concrete strategies

- **DefaultBattleStrategy** (`default.py:12`) — the standard "win efficiently" brain.
  `decide_turn` picks `get_strongest_move_against()` (see util below); if HP is under the
  configured `battle.hp_threshold` percentage or no damaging move is usable, it follows
  the `lead_cannot_battle_action` config: flee (best escape method), rotate (best
  switch-in), or abort to manual (`_handle_lead_cannot_battle`, `:220`). Move learning
  (`which_move_should_be_replaced`, `:25`) honors config (`stop`/`cancel`/banned moves),
  never replaces HMs, computes effective power (base × attacking stat × STAB) and prefers
  dropping redundant-type moves to preserve coverage. Evolution defers to the mode hook
  plus the `stop_evolution` config. Fainting: flee per config or when the party is done;
  new lead after faint = highest-HP non-egg (`:118`). Post-battle it rotates the lead
  back/onward via `BattleStrategyUtil.select_rotation_target()` if the pre-battle lead
  can no longer fight.
- **CatchStrategy** (`catch.py:23`) — used for `BattleAction.Catch`. Each turn: pick the
  best ball (`_get_best_poke_ball`, `:212` — per-ball multipliers: Ultra 2×, Great/Safari
  1.5×, Net 3× vs Water/Bug, Dive 3.5× underwater, Nest scaled below level 40, Repeat 3×
  if already owned, Timer up to 4× by turn count; **Master Ball is deliberately never
  chosen**). If the target is healthy *and* the computed one-turn catch probability
  (`calculate_catch_success_chance`, Gen-3 exact shake formula in `_util.py:271-294`) is
  <50%, it first uses the best sleep/paralysis move available (`:186-210`, weighting
  sleep 2× > paralysis 1.5×, respecting Insomnia/Vital Spirit/Limber and Taunt).
  Safari turns: R/S/E feeds Pokéblocks per `RSESafariStrategy` state machine; FR/LG
  replays curated bait/rock/ball sequences from
  `modules/data/frlg_safari_catch_strategies/*.yml`, keyed by species group, remaining
  balls and bait state (`safari_strategy.py:512-600`).
- **RunAwayStrategy** (`run_away.py:10`) — flee via
  `BattleStrategyUtil.get_best_escape_method()`; if escape is currently impossible, attack
  with the strongest move (to end the battle the hard way), else keep trying Run.
- **LevelBalancingBattleStrategy** (`level_balancing.py:17`) — keeps the *lowest-level*
  party member as lead so it soaks EXP; if the lead is weak, temporarily switches in the
  strongest member so the weakling still gets shared EXP; after battle always rotates the
  lowest-level member back to slot 0.
- **LevelUpLeadBattleStrategy** (`level_up.py:8`) — "train only the lead": never rotates
  after battle, requires healthy+damaging-capable Pokémon
  (`_can_battle`), fleeing/rotating per config when the lead can't fight.
- **ItemStealingBattleStrategy** (`item_stealing.py:10`) — uses Thief/Covet on opponents
  whose species can hold items (tracking victims by personality value to avoid stealing
  twice); respects Sticky Hold, Substitute, and Ghost-type immunity to Covet; rotates the
  strongest remaining "thief" in as needed, then escapes when there is nothing to steal.
- **LoseOnPurposeBattleStrategy** (`lose_on_purpose.py`) — inverse move scoring
  (`_get_weakest_move_against`): prefers Splash (score −1), heavily penalizes
  healing/multi-hit/Roar/OHKO moves and moves with a semi-invulnerable turn (it *wants*
  to be hit, so Fly/Dig scores are doubled to select against them), and actively
  **prefers** Explosion/Selfdestruct when it is down to the last non-fainted Pokémon —
  a guaranteed loss is exactly the goal, so that case scores −2, below even Splash
  (plus a general ×0.85 bonus for self-fainting moves); after a faint it simply sends
  out the next body — the goal is a controlled whiteout (Nugget Bridge, Kecleon).
- **BattleStrategyUtil** (`_util.py:40`) — the shared math engine: exact Gen-3 escape
  odds (`get_escape_chance`, `:44`, including Smoke Ball / Run Away ability / trap
  abilities and the escape-attempts counter read from game RAM), escape method selection
  (Poké Doll / Fluffy Tail / Teleport / Roar fallbacks, `:97`), `can_switch()` (trap
  checks), and a substantial reimplementation of the Gen-3 damage formula
  (`calculate_move_damage_range`, `:165` — stat stages, badge boosts, held item boosts,
  abilities, Reflect/Light Screen, weather, spread-move halving, fixed-damage moves,
  85–100% roll range), `get_strongest_move_against()` (`:244`), rotation target selection
  weighted by HP and status (`select_rotation_target`, `:556`).

### Move learning & evolution scenes

- `battle_move_replacing.py` — `get_learn_move_state()` (`:25`) reconstructs which stage
  of the "wants to learn a move" dialogue is active from tasks + battle-script offsets
  (this differs *inside battle*, *after battle*, and *during evolution*, and per
  game/revision). `handle_move_replacement_dialogue(strategy)` (`:76`) then asks
  `strategy.which_move_should_be_replaced()`, and either scrolls the summary-screen move
  cursor to the victim move and confirms, or backs out through the "stop learning?"
  dialogue. The party-index bookkeeping (`:92-106`) again maps battle order to party
  order per game.
- `battle_evolution_scene.py` — `handle_evolution_scene(strategy)` (`:17`) watches
  `Task_EvolutionScene`; once the scene has progressed far enough to know *which* Pokémon
  is evolving it asks `strategy.should_allow_evolution()` and thereafter holds either B
  (cancel) or A (allow), delegating to the move-replacement handler if the evolved form
  wants a new move.

---

## The encounter pipeline (`modules/encounter.py`)

The judging/logging/alerting funnel every wild Pokémon, gift, and hatched egg passes
through:

1. **`EncounterInfo.create(pokemon, type)`** (`:45`) snapshots the Pokémon, timestamp,
   encounter type (grass/surf/fishing/gift/hatched/…, from `battle_state.get_encounter_type`),
   map + coordinates, current bot mode, and immediately runs the custom catch filters.
2. **`judge_encounter(pokemon) -> EncounterValue`** (`:124`) classifies:
   `RepeatEncounter` (same PV as last encounter — or, for the very first encounter after
   launch, any PV already in the stats DB, to survive save-state reloads, `:92-107`),
   `Shiny` / `ShinyOnBlockList` (block list is re-read from `catch_block.yml` live so
   users can edit it mid-run), `CustomFilterMatch`, `Roamer` / `RoamerOnBlockList`
   (PV+species matches the active roamer), else `Trash`. Only `Shiny` and
   `CustomFilterMatch` count as `is_of_interest`.
3. **Custom catch filters** (`run_custom_catch_filters`, `:72`) — user-supplied
   `profiles/<profile>/customcatchfilters.py` (falling back to the global
   `profiles/customcatchfilters.py`) exposes `custom_catch_filters(pokemon) -> str|bool`;
   plugins can also judge via `plugin_judge_encounter`. This is the user's programmable
   "keep it" hook (perfect IVs, specific natures, Unown letters…).
4. **`handle_encounter(...) -> BattleAction`** (`:217`) — the policy step: prints/notifies
   per value (rich console line, desktop notification with the species sprite, optional
   `.pk3` dump via `save_pk3`, optional emulator save state for shinies), then chooses the
   battle action: of-interest + `battle.auto_catch` config → `Catch` (unless
   `disable_auto_catch`); of-interest otherwise → switch to Manual + `CustomAction`;
   species in `battle.avoided_pokemon` → `RunAway`; `enable_auto_battle` flag (grind
   modes) → `Fight`; default → `RunAway`.
5. **`log_encounter(info)`** (`:163`) — writes to the SQLite stats DB
   (`context.stats.log_encounter`), triggers phase-reset on shinies, fires the
   `plugin_logging_encounter` hook (Discord notifications etc. live in plugins), and
   composes the status message shown under the emulator video (nature/ability/IV
   sum/shiny value "fun facts"). During battles, logging is deferred by the
   BattleListener until the opponent is visible; outside battles (gifts) it happens
   immediately from `handle_encounter`.

Battle outcome is later attached by `_listeners.py:146` (`log_end_of_battle`).

---

## Supporting automation modules (outside `modes/`)

- **`safari_strategy.py`** — data + logic for Safari hunting: per-game target tables
  (`SafariPokemon`, `SafariPokemonRSE` enums with species/map/tile/method), entrance
  configs, `get_navigation_path()` curated routes, FRLG bait/rock YAML lookup
  (`FRLGSafariStrategy`), RSE Pokéblock preference logic (`RSESafariStrategy`,
  `get_baiting_state`, lowest-"feel" block selection), `get_safari_balls_left()`
  (reads `gNumSafariBalls`).
- **`fishing.py`** — the *data model* for fishing stats (`FishingRod`, `FishingResult`,
  `FishingAttempt`) plus `get_feebas_tiles()`; the acting code is `modes/util`'s `fish()`
  and the FishingListener.
- **`keyboard.py`** — full naming-screen driver: decodes the on-screen keyboard layout,
  page, and cursor sprite from RAM (`get_naming_screen_data`, `:110`), then
  `type_in_naming_screen()` (`:146`) navigates key-by-key with wrap-aware shortest-path
  cursor movement, and `handle_naming_screen()` (`:226`) wraps the whole dialogue. Used
  for nicknaming caught/hatched Pokémon via plugin hook.
- **`menuing.py`** — overworld menu navigation library: `StartMenuNavigator("POKEMON")`,
  `PokemonPartyMenuNavigator(index, "summary"|"switch"|"take_item"|…)`,
  `BattlePartyMenuNavigator`, `PartyMenuExit`, `RotatePokemon` — all `BaseMenuNavigator`
  subclasses implementing a named-step state machine (`current_step` + generator per
  step), wrapped by `MenuWrapper.step()`. Also `use_field_move()` (Surf/Sweet Scent…
  via party menu), pickup-item helpers (`get_items_available_for_pickup`,
  `take_held_items_from_multiple_party_pokemon`, `should_check_for_pickup` — the
  `battle.pickup_check_frequency` batching logic), and cursor scrollers
  (`scroll_to_item_in_bag`, `scroll_to_party_menu_index`).
- **`player_pc_navigaton.py`** — `WithdrawItemNavigator` / `DepositItemNavigator` for the
  player's item PC.
- **`pokemon_storage_navigaton.py`** — `PCMainMenuNavigator`, `BoxNavigator` and
  `StorageCursor` for the Pokémon storage system UI (box/slot cursor math via
  `pc_slot_from_number`).
- **`pokeblock_feeder.py`** — reads active Pokéblock feeder state (which feeder tiles
  currently contain a block and what flavor) so CatchStrategy can match the fed flavor.
- **`berry_trees.py`** — decodes all berry tree slots (stage, berry, watering) for the
  berry-farming plugin/util (`modes/util/berry_tree_interaction.py` plants/waters/
  harvests).
- **`mart.py`** — parses the Poké Mart buy menu (item list pointer + cursor positions)
  for `buy_in_shop`/`sell_in_shop`.

---

### Enhancement opportunities

- **Custom modes are first-class**: the cleanest extension point is a plugin exposing
  `plugin_get_additional_bot_modes()` — a new `BotMode` subclass gets the full toolbox
  (navigation, soft resets, menuing, battle strategies) with zero core edits. Any
  new automation (berry farming loops, contest grinding, trainer re-match farming,
  gym re-runs) should start life as a mode + optionally a custom `BattleStrategy`.
- **`PokecenterLoopController` is the template for sustainable grind loops** — new
  farm-style modes should reuse it rather than re-implement heal/return/spin logic.
- **The battle strategy layer is pluggable per battle**: `on_battle_started` may return a
  strategy *instance*, so per-encounter tactics (e.g. "False Swipe + status then catch",
  which currently doesn't exist as a strategy) can be added without touching the engine.
  A "SmartCatch" strategy that weakens targets with False Swipe before throwing balls is
  an obvious gap — `CatchStrategy` today only does status + best ball.
- **Damage model is close but incomplete** (`_util.py` todos: Bide/Counter/Endeavor,
  Helping Hand, Flash Fire boost, sport moves). Improving it directly improves every
  fighting mode.
- **`decide_turn_in_safari_zone` on `DefaultBattleStrategy` just bails to manual** — RSE
  safari auto-catch outside SafariMode (see the TODO at `rock_smash.py:174`) is a known
  gap.
- **Known fragility**: modes lean on game-version-specific task/script symbol names
  (three-way `is_rs/is_emerald/is_frlg` branches everywhere). Any new mode must be tested
  per game; the util wrappers hide most but not all of this.

### For the Pokémon Emerald AI project

- **The generator/frame-yield control pattern is the chassis to reuse.** An AI agent
  playing Emerald can be implemented as *just another `BotMode`*: `run()` becomes the
  policy loop (observe → decide → `yield from` an action helper), and the existing
  listeners already handle the involuntary events (battles starting, whiteouts, eggs,
  repel) that would otherwise crash a naive agent. `BattleAction.CustomAction` +
  `context.controller_stack` give the AI frame-level control whenever it wants it.
- **Battle competence is already solved to a strong baseline.** `BattleStrategy` is a
  clean decision interface (typed actions, no button knowledge needed), `handle_battle()`
  does all menu execution, and `BattleStrategyUtil` provides a faithful Gen-3 damage
  formula, escape odds, and catch probability. An AI battle policy only needs to
  implement `decide_turn(battle_state) -> TurnAction` — everything below that line is
  plumbing that already works. Conversely, an LLM/planner can *replace* just this one
  method while keeping default faint/learn/evolve handling.
- **Navigation is a solved primitive**: `navigate_to(map, coords)` pathfinds across map
  connections and warps, handles Surf/Waterfall transitions, and raises a typed timeout
  error for recovery. Combined with `talk_to_npc`, `interact_with_pc`, `buy_in_shop`,
  `fly_to`, `heal_in_pokemon_center`, and `use_field_move`, an agent can act at the level
  of *intents*, not button presses. This is precisely the "tool library" an AI planner
  wants.
- **Game-state observability comes from tasks/scripts, not pixels.** `FrameInfo`'s
  `active_tasks`/`script_stack` (from the game's own schedulers) plus the typed readers
  (`get_party()`, `get_battle_state()`, `get_player_avatar()`, event flags/vars) mean an
  agent can condition on exact symbolic state — dialogue open? battle turn awaited?
  script running? — the same signals every wait-helper in `modes/util` uses.
- **The encounter pipeline is where "goals" plug in**: `customcatchfilters.py` and
  `handle_encounter`'s config-driven policy show how per-user objectives are injected
  today; an AI project should route its own "is this Pokémon worth catching / is this
  battle worth fighting" value function through the same `judge_encounter`/
  `on_battle_started` seams rather than inventing a parallel path.
