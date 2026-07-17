# 02 — Game State & Memory Decoding Layer

All paths are relative to the repo root `pokebot-gen3/`, and all line references are
`modules/<file>.py:<line>`. This document covers the layer of the bot that turns raw
emulated GBA memory into meaningful Python objects.

## What this layer is FOR

The bot plays Gen-3 Pokémon games (Ruby/Sapphire/Emerald/FireRed/LeafGreen) *legitimately*:
it never writes game memory to force outcomes. Instead, it **reads** the emulator's RAM/ROM
every frame to know exactly what the game world looks like — party, opponent, map, tiles,
menus, battle state, RNG-derived values like shininess — and then acts purely through
simulated button presses. This layer is the "eyes" of the bot; the button-pressing layers
(bot modes, battle strategies) are its "hands".

The reason this is possible without guesswork is the **pret decompilation projects**
(https://github.com/pret). The community decompiled the retail ROMs back into C, and the
build of that C code produces *symbol tables* — text files mapping every global variable and
function in the game to its exact memory address and size, e.g.:

```
020244ec g 00000258 gPlayerParty
```

means "the C global `gPlayerParty` lives at EWRAM address 0x020244EC and is 600 bytes"
(6 Pokémon × 100 bytes). The bot ships these `.sym` files for every supported ROM revision
and language (`modules/data/symbols/`). Instead of hardcoding addresses, every reader in this
layer calls `read_symbol("gPlayerParty", offset, size)` (`modules/memory.py:43`) and the
symbol name is resolved to the right address *for the currently loaded ROM*. This is what
makes the same Python code work across R/S/E/FR/LG and multiple revisions: the names are
stable even though the addresses differ.

Two supporting concepts recur everywhere:

- **Save blocks** (`get_save_block`, `modules/memory.py:119`): the game keeps almost all
  persistent player data (position, money, bag, Pokédex, event flags/vars, daycare, roamer)
  in two big structs, SaveBlock1 and SaveBlock2. On R/S these are at fixed symbols; on
  Emerald and FR/LG only a *pointer* to them is at a fixed symbol (anti-cheat shuffling), so
  the helper dereferences `gSaveBlock1Ptr`/`gSaveBlock2Ptr` first. Most per-game differences
  in this layer are just different *offsets into the save blocks*.
- **XOR "encryption"** (`modules/memory.py:176-217`): Emerald and FR/LG XOR certain values
  (money, coins, bag quantities, game stats) with a per-save 32-bit key stored in SaveBlock2.
  `decrypt16`/`decrypt32` undo this. R/S has no key (key = 0, XOR is a no-op).

`modules/memory.py` and `modules/game.py` (symbol loading, character-set decoding via
`decode_string`, event-flag/var name tables) are documented in detail by the emulator-core
document; here they are only referenced.

---

## modules/pokemon.py — the Pokémon data model (1583 lines)

This is the heart of the layer: it decodes the famous **100-byte Pokémon structure** and
loads all static species/move/item metadata.

### Static data (loaded once from JSON at import time)

Species, moves, natures, abilities and types are *not* read from the ROM; they are shipped
as JSON in `modules/data/` and loaded at module import into lookup tables:

- `Type` (`pokemon.py:291`) — elemental type with an effectiveness matrix
  (`get_effectiveness_against`, :304) and the Gen-3 physical/special split *by type*
  (:307-317 — types with index < 9 are physical).
- `Move` (`pokemon.py:328`) — the "move species": power, accuracy, PP, priority, effect,
  target, contact/sound/protect flags, associated TM/HM item.
- `LearnedMove` (`pokemon.py:385`) — a move slot on an individual Pokémon (current PP,
  PP-Ups).
- `StatsValues` (`pokemon.py:409`) — 6-stat container used for base stats, IVs, EVs and
  computed stats. `StatsValues.calculate` (:437) re-implements the exact Gen-3 stat formula
  (incl. the Shedinja 1-HP special case) — needed because *boxed* Pokémon don't store their
  stats and they must be recomputed from base stats + IVs + EVs + nature + level.
- `Nature` (`pokemon.py:505`) — stat modifiers plus Pokéblock flavour preferences.
- `LevelUpType` (`pokemon.py:585`) — the six EXP curves, formulas copied from the decomp
  (`get_experience_needed_for_level` :593, inverse `get_level_from_total_experience` :629,
  again needed for boxed Pokémon which don't store level).
- `Species` (`pokemon.py:713`) — dex numbers, types, abilities, base stats, gender ratio,
  egg groups/cycles, catch rate, EV yield, full learnset (`SpeciesMoveLearnset` :667),
  evolutions.
- Lookup helpers: `get_species_by_index` (:1487 — note Unown forms are mapped from synthetic
  IDs 20100-20199 back to species 201), `get_species_by_name` (:1480),
  `get_move_by_index/name` (:1409-1414), `get_nature_by_index` (:1436),
  `get_type_by_name/index` (:1386-1391), `get_ability_by_name/index` (:1455-1460).

### The 100-byte Pokémon structure

`class Pokemon` (`pokemon.py:871`) wraps a single `bytes` blob: 100 bytes for a party
Pokémon, 80 bytes for a boxed one (the last 20 bytes — status, level, current stats — only
exist in the party version and are recomputed for boxed ones). *Everything* else is a
computed property, so serialising a Pokémon = storing `pokemon.data`.

Layout (matches Bulbapedia's "Pokémon data substructures (Generation III)"):

- **Bytes 0-31, unencrypted header**: personality value (PID, u32 at 0), original trainer
  ID + secret ID (u32 at 4), nickname (10 bytes at 8, proprietary character encoding decoded
  via `decode_string`), language (18), flags (19 — bit 1 "has species" is used by `is_empty`
  :971, bit 2 "is egg"), OT name (20-26), markings (27), **checksum** (u16 at 28).
- **Bytes 32-79, encrypted region**: four 12-byte substructures — Growth (species, held
  item, EXP, PP-Ups, friendship), Attacks (4 move IDs + 4 PP), EVs & Contest stats,
  Miscellaneous (Pokérus, met location/level/game/ball, IVs, egg + ability bits).
  - **Encryption**: each 32-bit word is XORed with `PID ^ OT-ID`.
  - **Substructure order**: the four substructures appear in one of 24 permutations selected
    by `PID % 24` — the lookup table is `POKEMON_DATA_SUBSTRUCTS_ORDER` (`pokemon.py:24`).
  - `_decrypted_data` (`pokemon.py:898`) does both steps with a vectorised numpy XOR and
    returns the blob with substructures re-ordered to the canonical (0,1,2,3) order so all
    other properties can use fixed offsets. It is a `cached_property` — decryption happens
    at most once per object.
  - **Checksum**: sum of the 24 decrypted u16 words, truncated to 16 bits
    (`calculate_checksum` :959). `is_valid` (:967) compares this against the stored checksum
    — this is how the bot detects torn reads (memory changing mid-read) and garbage data.
- **Bytes 80-99, party-only**: status condition bitfield (80; `StatusCondition.from_bitfield`
  :830 — 3 sleep-counter bits, then poison/burn/freeze/paralysis/bad-poison), level (84),
  current HP (u16 at 86), the six current stats (u16 each at 88-99).

### Values derived from the personality value

The PID is the master RNG artifact of Gen 3; many attributes are pure functions of it:

- `nature` = `get_nature_by_index(PID % 25)` (:1240)
- `gender` — compares `PID & 0xFF` against the species gender-ratio threshold (:1244)
- **Shininess**: `shiny_value = trainerId ^ secretId ^ PID_high16 ^ PID_low16` (:1257);
  shiny iff `< 8` (:1262). The bot also tracks "anti-shiny" (value 65528-65535, :1266) as a
  fun curiosity.
- `hidden_power_type`/`hidden_power_damage` (:1270/:1284) — from the low bits of each IV.
- `unown_letter` (:1297) — from interleaved PID bit pairs; `wurmple_evolution` (:1307).

Other notable decoders: `original_trainer` (:988, incl. gender bit from the origins word),
`is_egg` (:1026 — checks *both* the header flag and the IV-word egg bit), `moves`/`move`
(:1056-1069, PP-Up bits packed 2-per-move in one byte), `evs` (:1084), `ivs` (:1095 —
5 bits each packed in one u32), `ability` (:1122 — bit 31 of the IV word picks slot 0/1),
`poke_ball` and `game_of_origin` (:1130/:1136 from the origins word), `level_met` (:1155),
`location_met` (:1159 via the 200+-entry `LOCATION_MAP` table at :70), `pokerus_status`
(:1118), `to_pk3` (:924 — export to the standard .pk3 file format).

### Module-level helpers

- `parse_pokemon(data)` (`pokemon.py:1342`) — returns a `Pokemon` only if non-empty *and*
  checksum-valid; this is the standard "is this really a Pokémon?" gate.
- `get_opponent()` (:1500) — first Pokémon of `gEnemyParty` (delegates to pokemon_party).
- `opponent_changed()` (:1521) — ultra-cheap change detector: reads only the first 4 bytes
  (PID) of `gEnemyParty` and compares with the previous call. Used by the encounter loop to
  notice new trainer battles without decoding 600 bytes every frame.

**Consumers:** virtually everything — encounter judging (`modules/encounter.py`), battle
strategies, the web API, stats/logging, the GUI, daycare/breeding modes.

---

## modules/pokemon_party.py — player & enemy parties (190 lines)

- `PartyPokemon` (`:9`) — `Pokemon` + its party slot index.
- `Party` (`:15`) — list wrapper with conveniences: `contains_eggs`, `non_fainted_pokemon`,
  `first_non_fainted` (:69), `has_pokemon_with_move` (:76), `first_pokemon_with_ability`
  (:89), etc.
- `get_party()` (`:110`) — reads `gPlayerPartyCount` (1 byte) then 100 bytes per slot from
  `gPlayerParty`. **Torn-read handling** (:133-145): if a slot fails the checksum (the game
  was mid-write), it uses `context.emulator.peek_frame()` to advance emulation one frame,
  re-read, and restore the savestate — up to 5 retries — so frame-accuracy is preserved.
  Result goes into the state cache.
- `get_opponent_party()` (`:155`) — same for `gEnemyParty` (wild encounters occupy only
  slot 0; trainer battles fill up to 6).
- `get_current_repel_level()` (`:181`) — level of the first non-fainted party member if the
  event var `REPEL_STEP_COUNT` > 0, else 0. Feeds the effective-encounter maths in map.py.

---

## modules/pokemon_storage.py — the PC boxes (152 lines)

`get_pokemon_storage()` (`:140`) reads the whole `gPokemonStorage` struct (on Emerald/FRLG
via the `gPokemonStoragePtr` pointer, on R/S directly). `PokemonStorage` (`:61`) decodes:
active box index (byte 0), then 14 boxes × 30 slots × **80-byte** (boxed-format) Pokémon
starting at offset 0x4, box names at 0x8344 (9 bytes each, game text encoding), wallpaper
IDs at 0x83C2. `PokemonStorageBox.first_empty_slot_index` (`:44`) supports the auto-release
/deposit navigation modes. Consumed by `pokemon_storage_navigaton.py` and stats.

---

## modules/player.py — trainer profile & overworld avatar (322 lines)

Two distinct objects:

- `Player` (`:169`) — *persistent* profile from the save blocks: name/gender/TID/SID from
  SaveBlock2 (:188-201), money and coins XOR-decrypted from SaveBlock1 (:204-209),
  registered Select-button item (:212). Fetched by `get_player()` (:231; SaveBlock1 offset
  0x490 RSE / 0x290 FRLG).
- `PlayerAvatar` (`:66`) — *live* overworld state, combining the `gPlayerAvatar` struct with
  the player's entry in `gObjectEvents` (fetched by `get_player_avatar()` :248):
  - `map_group_and_number` + `local_coordinates` (:93/:124) — where the player is;
  - `flags` (`AvatarFlags` IntFlag :25 — OnFoot/MachBike/AcroBike/Surfing/Underwater/
    Controllable/ForcedMove/Running), `is_on_bike` (:132), `is_in_water` (:136);
  - `running_state` / `tile_transition_state` / `acro_bike_state` enums (:36-56) — critical
    for frame-precise movement: `TileTransitionState` tells you whether the avatar is
    mid-step between tiles;
  - `facing_direction` (:152) and `map_location_in_front` (:111) — the tile being faced
    (used for interaction targets like berry trees, NPCs, doors).

Free functions used constantly by navigation code:

- `player_avatar_is_controllable()` (`:263`) — true only in the OVERWORLD game state with no
  held/forced movement, not frozen, and not in the RSE door-exit edge case (checks the
  `Task_ExitDoor` task).
- `player_avatar_is_standing_still()` (`:287`).
- `get_player_location()` (`:291`) — returns `(MapRSE|MapFRLG enum, (x, y))`, with a
  one-frame peek-ahead retry for the rare corrupt-during-map-change case (:304-315).
- `player_is_at(map, coords)` (`:320`).

---

## modules/items.py — items, bag, PC item storage, Pokéblocks (592 lines)

- `Item` (`:190`) + enums: `ItemPocket` (:29 — with per-game pocket capacities in
  `capacity` :49), `ItemBattleUse` (:72), `ItemFieldUse` (:92), `ItemHoldEffect` (:109 —
  every Gen-3 held-item effect as an enum). Loaded from `data/items.json` (:511).
- `ItemBag` (`:311`) — decodes the in-memory bag: each slot is 4 bytes (item ID u16 +
  quantity u16), quantities XOR-encrypted on E/FRLG (`_get_pocket` :342 uses `decrypt16`).
  Pockets are laid out sequentially (items → key items → balls → TMs/HMs → berries).
  Helpers: `has_space_for` (:377, models the 99 vs 999 stack-size rules),
  `quantity_of` (:427), `number_of_repels` (:442). Fetched by `get_item_bag()` (:541;
  SaveBlock1 offset 0x310 FRLG / 0x560 RSE).
- `ItemStorage` (`:460`) — the PC's item storage (no encryption), `get_item_storage()`
  (:560).
- `Pokeblock` (`:263`) and `get_pokeblocks()` (:577) — RSE-only Pokéblock case contents.

---

## modules/pokedex.py — seen/owned bitfields (94 lines)

`get_pokedex()` (`:73`) reads the dex struct from SaveBlock2 offset 0x18 plus the **two
redundant "seen" backup arrays** in SaveBlock1 (game-version-specific offsets, :77-85 — the
game stores the seen flags three times as an anti-corruption measure and only trusts
agreeing copies; `seen_species` :32 replicates that check). `owned_species` (:44) uses the
owned bitfield at struct offset 0x10. One bit per national-dex species (412 bits).

---

## modules/daycare.py — breeding state (141 lines)

`get_daycare_data()` (`:101`) reads the daycare struct from SaveBlock1 (offset 0x2F9C RS /
0x3030 E / 0x2F80 FRLG): the two deposited Pokémon (80-byte boxed format via
`parse_pokemon`), steps each has accrued (= EXP gained), the **offspring personality value**
(pre-rolled by the game before the egg is even generated — Emerald: u32, others: u16 at
:122-127), and the egg step counter. `DaycareCompatibility.calculate_for` (`:16`) reproduces
the game's breeding-compatibility rules (egg groups, Ditto, genders, same-species/same-OT
matrix). Consumed by the Daycare (egg hatching) bot mode.

---

## modules/roamer.py — Latios/Latias/legendary-bird roamer (180 lines)

The roamer (Latias/Latios in RSE, the legendary beasts in FRLG) is stored in SaveBlock1
(offset 0x30D0 FRLG / 0x31DC E / 0x3144 RS; `get_roamer` :148), *not* as a normal Pokémon
struct: `Roamer` (`:21`) decodes IVs (u32 at 0), PID (u32 at 4), species (u16 at 8), HP,
level, status. It replicates the infamous **FR/LG roamer IV bug** (:44-46: only the low
8 IV bits survive). Shininess needs the trainer IDs passed in because the struct has no OT
(:101). `get_roamer_location_history()` (`:170`, symbol `sLocationHistory`) gives the last
3 maps the roamer visited — used by the roamer-hunt mode to intercept it.

---

## modules/tcg_card.py — souvenir card renderer (318 lines)

Not a state *reader* per se: `generate_tcg_card(pokemon_data)` (`:60`) uses PIL to render a
collectible-card PNG for a caught Pokémon (sprite, IVs, nature, ability, OT, moves, shiny
badge, location) into the profile's `screenshots/cards/` directory. It consumes the decoded
`Pokemon` plus `get_player()`/`get_player_avatar()` for flavour text. Good example of how
downstream code composes this layer's readers.

---

## modules/map.py — maps, tiles, NPCs, wild encounters (2299 lines)

The biggest file in the slice. Four concern areas:

### 1. Map metadata: `MapLocation` (`:738`)

A `MapLocation` is "(map header, map group, map number, local (x,y))" and lazily follows ROM
pointers to answer questions about the map *and* about that one tile:

- Map layout pointer chain: `_map_layout` (`:745`, cached per ROM per map in
  `_map_layout_cache` :735) → `map_size` (:849), border and metatile pointers.
- `_metatile_attributes` (`:757`) is the key tile decoder: it reads the map-grid word for
  the coordinates (10 bits metatile ID, 2 bits **collision**, 4 bits **elevation**), falls
  back to the border tiles for out-of-bounds, then looks the metatile up in the primary or
  secondary tileset's attributes array (layout differs FRLG vs RSE, :783-790) to get the
  **tile behaviour** byte.
- `tile_type` (`:861`) maps that behaviour byte to a human-readable name via the giant
  `_get_tile_type_name` switch (`:36-424`) covering all ~200 Gen-3 metatile behaviours
  (tall grass, water types, waterfalls, ledges/"Jump" tiles, forced-movement/"Walk"/"Slide"
  tiles, currents, ice, warps of every flavour, furniture...). Several codes differ between
  RSE and FRLG and the function handles both.
- Semantic predicates built on this: `has_encounters` (:873 — FRLG encodes it in the
  attribute word, RSE in the `sTileBitAttributes` ROM table read at :813), `is_surfable`
  (:880), `is_cycling_possible` / `is_escaping_possible` / `is_running_possible`
  (:898-947, from map-header flag bytes), `is_dark_cave` (:956), `map_type` (:854),
  `weather` (:858), `map_name` (:830 — follows `gRegionMapEntries`/`sMapNames` into ROM
  text).

### 2. Map events (from the map header's event list, `_event_list` :817)

- `MapConnection` (`:476`) — seamless edge connections to neighbouring maps (direction,
  offset, destination map).
- `MapWarp` (`:526`) — doors/stairs/holes: position, destination map + warp id, with the
  two special cases handled in `destination_location` (:551): *dynamic warps*
  (group/number 127/127 → destination read from SaveBlock1 offset 0x14) and warp id 0xFF
  (destination = same coordinates).
- `MapCoordEvent` (`:585`) — scripts triggered by *stepping on* a tile (plus weather
  triggers); exposes the trigger var/value so pathfinding can predict whether the script
  would actually fire.
- `MapBgEvent` (`:643`) — scripts triggered by *interacting*: signs, **hidden items**
  (item + the event flag that marks it collected, :700-707), secret bases.
- `ObjectEventTemplate` (`:1588`) — the ROM-defined NPC list per map: movement type/range,
  trainer type and sight `trainer_range` (:1635), `is_trainer_defeated` (:1638 — reads the
  trainer-flag from the script), berry tree id, visibility flag, plus FRLG "clone" objects.

### 3. Live entities: `ObjectEvent` (`:1107`)

Decodes one 0x24-byte entry of the live `gObjectEvents` array (up to 16 loaded entities,
player is index 0): 28 boolean state flags (:1382 — `heldMovementActive`,
`heldMovementFinished`, `frozen`, `invisible`...), `current_coords`/`previous_coords`
(:1470/:1475 — stored +7 offset, corrected here), `facing_direction` (:1478),
`movement_type` and current `movement_action` (from the two big name tables at :1108 and
:1192), elevation, and the link back to its template (:1565). Accessors:
`get_map_objects()` (`:1799`) and `get_player_map_object()` (`:1811`).

### 4. Access + wild encounter tables

- `get_map_data(map, coords)` (`:1756`) — the main entry point; on first use it walks
  `gMapGroups` in ROM once and caches every map header per ROM id (`_map_header_cache`
  :1753).
- `get_map_data_for_current_position()` (`:1742`), `get_map_all_tiles()` (`:1816`).
- `get_wild_encounters_for_map()` (`:1885`) — parses the ROM's `gWildMonHeaders` once into
  `WildEncounterList` (`:1849`): land (12 slots), surf/rock-smash (5), and the three fishing
  rods, each slot with species, level range and the game's fixed per-slot probabilities
  (:1893-1896).
- `get_effective_encounter_rates_for_current_map()` (`:2219`) — computes what you will
  *actually* encounter after Repel truncation (`_calculate_repel_rate_and_species_map`
  :2068) and Emerald lead-ability effects (Keen Eye/Intimidate, Pressure/Hustle,
  Static/Magnet Pull — `_get_ability_repel_rate_and_species_map` :2108, with the derivation
  of the combined formula documented in comments at :2162-2194). Cached in the state cache.
- `calculate_targeted_coords()` (`:2288`) — coordinate one step in a facing direction.

**Consumers:** every navigation-capable bot mode, map_path.py, the web map viewer/debug GUI,
encounter statistics.

---

## modules/map_data.py — the map name-space (1591 lines, mostly data)

Pure data tables giving every map a Python name:

- `MapGroupFRLG` (`:13`) / `MapFRLG` (`:75`) and `MapGroupRSE` (`:739`) / `MapRSE` (`:792`):
  enums whose values are `(map_group, map_number)` tuples — e.g.
  `MapRSE.ROUTE101 = (0, 16)`-style. These are the identifiers used across the whole
  codebase ("player is at `MapRSE.PETALBURG_CITY`").
- Enum niceties: tuple-like access (`__getitem__`/`__iter__` :1399-1414), `exists_on_rs`
  (`:1423` — filters Emerald-only maps when running R/S), `pretty_name` (`:1428` —
  regex-based conversion of `EVER_GRANDE_CITY_POKEMON_LEAGUE` into display text).
- `PokemonCenter` (`:1524`) — map + door coordinates of every Pokémon Center, used by
  auto-heal navigation.
- `get_map_enum()` (`:1557`) picks the right enum family for the running ROM;
  `is_safari_map()` (`:1567`).

---

## modules/map_path.py — pathfinding (949 lines)

This is the module that lets the bot *walk somewhere by itself*, and the foundation for any
custom overworld automation.

### Preprocessing: `PathMap` / `PathTile`

- `_get_all_maps_metadata()` (`:398`) runs once per ROM: it loads every map and **stitches
  connected overworld maps into shared global coordinate spaces**. Maps reachable from each
  other via edge connections get the same `level` id and an `(x, y)` offset; a BFS over
  connections (:442-481) assigns offsets so that "global coordinates" are comparable across
  map boundaries. (Indoor maps each end up in their own level; warps intentionally do *not*
  merge levels.) A known quirk — R/S Battle Pyramid maps claiming to connect to the Safari
  Zone — is patched out at :418-422.
- `PathMap.tiles` (`:86`) lazily converts a whole map into `PathTile`s (`:53`), baking the
  tile-behaviour semantics of map.py into pathfinding facts:
  - `accessible_from_direction[4]` — from ledges ("Jump South" = can only enter moving
    south), "Impassable X" tiles, "Walk/Slide" tiles (:118-132);
  - `warps_to` (destination map/coords, plus required extra input for Arrow Warps,
    :288-306);
  - `waterfall_to` / `muddy_slope_to` — precomputed landing tile at the top/bottom
    (:133-186);
  - `forced_movement_to` — full simulation of ocean **currents** (across map connections!)
    and **ice sliding** per entry direction, recording where you end up and how many tiles
    you slide (:197-278);
  - `needs_acro_bike` / `needs_bunny_hop` for rails and bumpy slopes (:187-196);
  - `on_enter_event_triggers` (trigger var → value from coord events),
    `dynamic_collision_flag`/`dynamic_object_id` for NPCs/objects (:331-340),
  - `has_encounters`, `cannot_run` (:324-328).
  - `_is_optional_blocker` (`:357`) — hardcoded list of tiles that appear/disappear with
    event flags (Shoal Cave items) which the ROM data can't express.

### The A* search: `calculate_path()` (`:620`)

`calculate_path(source, destination, avoid_encounters=True, avoid_scripted_events=True,
no_surfing=False, has_acro_bike=False, has_mach_bike=False)` returns a list of `Waypoint`s
(`:602` — direction, map, coordinates, is_warp, and optional `WaypointAction` (`:589`):
Surf/Waterfall/Dive/AcroBikeMount/BunnyHop/MachBikeSlope...). Notable mechanics:

- Capability checks read *game state*, not config: `can_surf()`/`can_dive()`/
  `can_waterfall()` (:684-704) check the badge event flag **and** that a party member knows
  the HM move.
- Live obstacle avoidance: current + previous coordinates of all loaded `gObjectEvents` are
  marked blocked (:706-722), so wandering NPCs are routed around.
- Accessibility (`is_tile_accessible` :729) folds in direction rules, elevation rules
  (elevation 1 = water, 3 = land, 0/15 = wildcard/bridge; surfing transitions allowed only
  with `can_surf()`), acro-bike requirements, and dynamic collision flags.
- Cost model (:861-927): steps cost 1; entering a warp tile that isn't the destination
  costs 1,000,000 (never path *through* doors); starting to surf +16 (the animation takes
  ~267 frames); waterfall cost from real frame counts (:887); encounter-capable tiles
  +1000 when `avoid_encounters`; tiles that would fire an active scripted event +10000
  (:924-927 — it checks the current event *var values* to see if the trigger is live);
  +0.1 for turning (prefer straight lines, :921).
- A special-case hack bridges the 2-tile global-coordinate gap between Route 104 and
  Rustboro (:833-849).
- Failure raises `PathFindingError` (`:511`) with readable map names.

Consumers: `modules/map_path`-based navigation helpers in `modules/modes/_helpers`
(`navigate_to()` etc. — outside this slice), safari, daycare, mart, PC modes.

---

## modules/region_map.py — the fly/town map screen (137 lines)

- `get_map_cursor()` (`:7`) — the cursor position on the open region map (different symbol
  and struct offset per game: `sMapCursor` FRLG / `sRegionMap`+0x54 E / `gRegionMap`+0x54
  RS); `None` when the map isn't open.
- `get_map_region()` (`:26`) — FRLG Sevii-island region page.
- `FlyDestinationRSE` (`:38`) / `FlyDestinationFRLG` (`:82`) — cursor coordinates for every
  fly target plus `get_flag_name()` returning the "visited" event flag that gates whether
  fly is unlocked there. Used by the fly-navigation helper to steer the cursor.

---

## modules/battle_state.py — everything visible mid-battle (973 lines)

Decodes the live battle engine state. Central symbol: `gBattleMons`, an array of up to four
0x58-byte battler structs (player, opponent, player-partner, opponent-partner).

- `get_battle_state()` (`:808`) reads 11 symbols in one go: `gBattleTypeFlags`,
  `gSideTimers`, `gBattlerPartyIndexes`, `gBattlePartyCurrentOrder`, `gBattlersCount`,
  `gBattleMons`, `gStatuses3`, `gDisableStructs`, `gAbsentBattlerFlags`,
  `gBattleResults`+0x13 (turn counter), `gBattleWeather` — and caches the resulting
  `BattleState` in the state cache.
- `BattleState` (`:222`):
  - `type` → `BattleType` flag enum (`:42` — Trainer, Double, Safari, Roamer, Legendary,
    Groudon/Kyogre/Rayquaza, Battle-Frontier modes...), plus `is_double_battle`,
    `is_trainer_battle`, `is_safari_zone_encounter` (:284-297);
  - `battling_pokemon` (:266) — list of `BattlePokemon`;
  - `own_side` / `opponent` (:300/:304) → `BattleStateSide`;
  - `current_turn` (:307), `weather` (`Weather` enum, :311);
  - `map_battle_party_index()` (:332) — maps real party indices to the in-battle party
    order (they diverge after switches; needed to scroll the party menu correctly).
- `BattleStateSide` (`:363`) — per-side view: `active_battlers`/`left_battler`/
  `right_battler` (absent-battler bit handling :380-415), screens and field timers
  (`reflect_timer`, `lightscreen_timer`, `mist_timer`, `safeguard_timer`,
  `follow_me_timer`, `spikes_amount` :438-459), `is_fainted` (:462).
- `BattlePokemon` (`:472`) — one in-battle battler (note: distinct from the party's
  `Pokemon`; Transform, stat stages, and mid-battle changes live here):
  species, **live battle stats** (:496), IVs (:507), moves with current PP (:519),
  `can_use_move` (:547 — accounts for Disable and Encore), ability (:566), current
  types (:577 — can change via e.g. Transform), **stat stages** `stats_modifiers`
  (:587, -6..+6) and `modified_stats()` (:590 — applies the exact stage multiplier table),
  HP (:623-634), level, held item, PID, `status_permanent` (:705) and `status_temporary`
  (:709 — ~35 volatile statuses decoded from `status2` + `gStatuses3` bitfields via
  `TemporaryStatus.from_bitfield` :117), plus the whole per-battler *disable struct*:
  disabled/encored move and remaining turns, Substitute HP, Stockpile/Fury Cutter counters,
  Perish Song / Taunt / Rollout / Charge / recharge timers, Truant "loafing" flag
  (:717-802).
- Battle-flow probes: `battle_is_active()` (:830 — checks that `gMain.callback1` is
  `BattleMainCB1`), `get_main_battle_callback()` (:835), and
  `get_current_battle_script_instruction()` (:839) — resolving the battle-script pointer to
  a symbol name is how the menuing code knows exactly which dialog/animation the battle
  engine is in.
- `BattleOutcome` (`:847`) / `get_last_battle_outcome()` (:862) — Won/Lost/RanAway/Caught...
- `EncounterType` (`:870`) + `get_encounter_type()` (`:906`) — classifies the current
  encounter (trainer/roamer/static/land/surf/rock-smash/fishing-by-rod/hatched/gift) using
  battle-type flags, the *script stack* (e.g. `EventScript_BattleKecleon`), the last fishing
  attempt, and the avatar's surf flag.

**Consumers:** `battle_handler.py`/`battle_strategies/` (choosing moves and switches),
`encounter.py` (logging), safari and catching logic.

---

## modules/state_cache.py — frame-scoped caching (301 lines)

Reading and decoding memory is not free (600 bytes + decryption + checksum per party read,
and Python is slow), and many parts of the bot ask for the same data many times per frame.
The pattern:

- `StateCacheItem[T]` (`:21`) stores a value plus the emulator **frame number** when it was
  last verified. `age_in_frames` (`:44`) = current frame − last checked frame (with a
  guard that reports a huge age after emulator resets, :47-56). `checked()` (:60) marks a
  value as re-verified *without* replacing the object.
- `StateCache` (`:64`) holds one item per expensive read: party, opponent, player,
  player_avatar, pokedex, pokemon_storage, effective_wild_encounters, item_bag,
  item_storage, tasks, script contexts, game_state, battle_state, fishing attempt, last
  encounter/shiny log. Global singleton `state_cache` at `:301`.
- **Usage contract** (seen in every getter, e.g. `get_party()` `pokemon_party.py:115`):
  ```python
  if state_cache.party.age_in_frames == 0:
      return state_cache.party.value   # already read this frame — free
  ...read + decode memory...
  state_cache.party = party            # setter compares with previous value
  ```
  The setters (e.g. :107-112) keep the *old object identity* if the new read is equal and
  just call `checked()` — so `is`-comparisons and cached sub-objects stay valid across
  frames while unchanged.
- `reset()` (:84) is called after emulator resets/loads so stale data is never trusted.

There is no push-invalidation: the invariant is simply "data read this frame is truth;
anything older must be re-read", which is correct because game state only mutates when the
emulator advances a frame.

---

## modules/game_stats.py — the game's own counters (75 lines)

`GameStat` (`:7`) enumerates the ~52 counters the game tracks (STEPS, TOTAL_BATTLES,
WILD_BATTLES, POKEMON_CAPTURES, HATCHED_EGGS, USED_POKECENTER...).
`get_game_stat()` (`:62`) reads them from SaveBlock1 (offset 0x1540 RS / 0x159C E /
0x1200 FRLG, 4 bytes each) and XOR-decrypts with `decrypt32`. A cheap, authoritative
source of lifetime counters (the bot's own stats DB tracks per-session data separately).

---

## modules/clock.py — in-game time (65 lines)

- `get_clock_time()` (`:21`) — the RTC-based clock (`gLocalTime`: days u16, hours, minutes,
  seconds) that drives time-based events (berries, Shoal Cave, lottery). Advances in *real*
  time regardless of emulation speed. FRLG has no RTC → zeros.
- `get_play_time()` (`:53`) — the trainer-card play-time counter from SaveBlock2 offset
  0x0E; advances per emulated frame.

---

## modules/tasks.py — the game's coroutine system (215 lines)

The game engine runs "tasks" (`gTasks`, 16 slots × 40 bytes: function pointer, is_active,
priority, 16 bytes of data) and up to two script-interpreter contexts. Since the bot cannot
ask the game "what are you doing?", **resolving these function pointers back to pret symbol
names is the primary way of inferring game mode**:

- `Task` (`:15`) — `symbol` (:30) resolves the function pointer to a name;
  `data_value(n)` (:42) reads the task's u16 parameters.
- `TaskList` (`:46`) / `get_tasks()` (:164, state-cached) — dict keyed by lowercased symbol
  name; `task_is_active("Task_ExitDoor")` (`:177`) is used everywhere (menus, doors,
  evolution scenes, battles).
- `ScriptContext` (`:84`) — the event-script VM state: `is_active`, mode
  (Bytecode/Native), and crucially the **script call stack resolved to symbol names**
  (`stack` :151). `get_global_script_context()` (:181) powers checks like "are we in the
  egg-hatch script" (`battle_state.py:908`) or "is a scripted encounter running".
- `is_waiting_for_input()` (`:199`) — combines script state and text-printer state to know
  when dialogue awaits an A/B press.

---

## modules/menu_parsers.py — menu cursor decoding (366 lines)

Readers for the game's menu structs, so menuing code can *verify* cursor state rather than
blindly pressing buttons:

- Cursor-option enums per game (`CursorOptionFRLG` :12, `CursorOptionEmerald` :45,
  `CursorOptionRS` :81 — the same actions have different indices per game!) and
  `get_cursor_options()` (:360).
- `get_party_menu_cursor_pos()` (`:134` — `gPartyMenu`, with hardcoded RAM addresses for
  R/S where symbols don't cover it), `parse_menu()` (:170, `sMenu` min/max/cursor),
  `parse_party_menu()` (:191), `parse_start_menu()` (:261).
- Battle menus: `get_battle_menu()` (`:293`) figures out ACTION vs MOVE selection by
  resolving `gBattlerControllerFuncs` symbols (`get_battle_controller` :316);
  `get_battle_cursor()` (:210).
- Prompt detection by *comparing displayed text* against known strings:
  `name_requested()` (:330 — nickname prompt), `switch_requested()` (:346 — "use next
  Pokémon?").
- Move learning: `get_learning_mon()` (:214), `get_learning_move()` (:236),
  `get_learning_move_cursor_pos()` (:243).

---

## modules/game_sprites.py, sprites.py, text_printer.py, fonts/ (brief)

- `game_sprites.py` — `GameSprite` (`:4`) decodes one entry of the in-game `gSprites` OAM
  array (64 × 0x44 bytes): on-screen pixel coordinates, flags (in_use/invisible/
  animation_ended...), per-sprite data words. `get_game_sprite_by_id()` (:63). Used for
  pixel-level detection in a few minigame-ish modes (e.g. fishing/feeder animations).
- `sprites.py` — *file-system* sprite assets, not memory: paths to normal/shiny/anti-shiny
  PNGs for GUI/Discord/TCG-card use (`get_sprite` :120 picks based on `pokemon.is_shiny`).
- `text_printer.py` — decodes the game's text-printer struct (`sTextPrinters` on E/FRLG,
  window structs on R/S) into a `TextPrinter` state machine
  (PrintingCharacter/Scrolling/WaitForButton, :8-58) so dialogue advancement can be timed
  precisely. `get_text_printer()` (:92).
- `fonts/` — just `pokemon-rs.ttf`, the pixel font used by the TCG-card renderer
  (`tcg_card.py:39`); no code.

---

### Enhancement opportunities

- **Expose a single "world snapshot" API.** Today, consumers call a dozen getters
  (`get_party`, `get_player_avatar`, `get_battle_state`, ...). A composed, JSON-serialisable
  snapshot object (party + location + tile info + battle + tasks) would be trivial to build
  on top of the state cache and would be ideal for plugins, the web API, or an external AI
  agent. Most `to_dict()` plumbing already exists (`Pokemon.to_dict` `pokemon.py:1338`,
  `MapLocation.dict_for_map` `map.py:1056`, `PlayerAvatar.to_dict` `player.py:155`).
- **Pathfinding across warps/fly.** `calculate_path` (`map_path.py:620`) explicitly cannot
  route through doors or use Fly ("levels" are only merged by edge connections,
  `map_path.py:398`). A higher-level graph — nodes = map levels, edges = warps
  (`MapWarp.destination_location` `map.py:551`) and fly destinations
  (`region_map.py:38`) — would enable true "go anywhere" navigation. All the data is
  already decoded; only the meta-graph and multi-leg executor are missing.
- **Trainer line-of-sight modelling.** `ObjectEventTemplate.trainer_range` (`map.py:1635`)
  plus `facing_direction` of live objects gives everything needed to compute which tiles
  trigger trainer battles; pathfinding currently ignores this (it only avoids the tiles
  NPCs stand on). Adding "avoid trainer vision cones" would make undefeated-trainer areas
  safely navigable.
- **`get_opponent_party()` dead code**: the `if pokemon is None` branch at
  `pokemon_party.py:168-172` can never trigger (the constructor never returns None) — it
  neither validates checksums nor filters empty slots, unlike `get_party()`. Wild-encounter
  callers only use slot 0 so it works in practice, but validating via
  `is_empty`/`is_valid` would make trainer-party reads more robust.
- **`daycare.py` and `roamer.py` are uncached** — both hit the save block on every call;
  adding them to `StateCache` would follow the established pattern for free.
- **Menu parsing still contains raw addresses** for R/S (`menu_parsers.py:158-162`);
  migrating those to symbols (they exist in pret's pokeruby) would remove the last
  hardcoded addresses in the slice.
- The tile-behaviour switch (`map.py:36`) and the movement-type/action tables
  (`map.py:1108,1192`) are transcriptions of pret constants; a generated mapping from the
  decomp headers would guard against transcription drift.

### For the Pokémon Emerald AI project

This layer is exactly the observation space an AI playing Emerald needs, already decoded and
version-aware. The AI never needs to touch raw memory — it should consume these readers:

1. **Agent observation, overworld**: `get_player_avatar()` (`player.py:248`) for
   position/facing/surf/bike state; `get_player_location()` (`player.py:291`) for
   `(MapRSE, (x, y))`; `get_map_data(...)`/`MapLocation` (`map.py:1756`/`map.py:738`) for
   per-tile collision, elevation, encounters, warps, connections;
   `get_map_objects()` (`map.py:1799`) for live NPCs; `MapLocation.objects/warps/
   coord_events/bg_events` (`map.py:989/977/1016/1031`) for interactables including hidden
   items (`map.py:700`) and undefeated trainers (`map.py:1638`).
2. **Agent observation, battle**: `get_battle_state()` (`battle_state.py:808`) is a
   near-complete battle observation: both actives' live stats, stat stages
   (`modified_stats()` `battle_state.py:590`), moves + PP + Disable/Encore legality
   (`can_use_move` `battle_state.py:547`), volatile statuses (`battle_state.py:709`),
   screens/spikes timers, weather, turn number. Pair with `get_opponent_party()`
   (`pokemon_party.py:155`) for full enemy-team knowledge (the game keeps the whole enemy
   party in RAM — the AI can be given perfect or fogged information, your choice) and
   `get_battle_menu()`/`get_battle_controller()` (`menu_parsers.py:293/316`) to know when
   an action is actually being requested.
3. **Agent observation, resources**: `get_party()` (`pokemon_party.py:110`),
   `get_item_bag()` (`items.py:541`), `get_player()` money (`player.py:204`),
   `get_pokedex()` (`pokedex.py:73`), `get_pokemon_storage()` (`pokemon_storage.py:140`),
   `get_game_stat()` (`game_stats.py:62`) — the latter is a ready-made source of reward
   signals (battles won, captures, hatched eggs, steps).
4. **Action gating / mode detection**: `get_game_state()` (`memory.py:253`) tells the AI
   which "screen" it is on (OVERWORLD/BATTLE/PARTY_MENU/...);
   `player_avatar_is_controllable()` (`player.py:263`), `is_waiting_for_input()`
   (`tasks.py:199`), `task_is_active()` (`tasks.py:177`) and the script stack
   (`tasks.py:151`) tell it *when* inputs will register. These are the difference between an
   agent that mashes buttons and one that acts frame-precisely.
5. **Macro-actions for free**: `calculate_path()` (`map_path.py:620`) turns "go to tile X"
   into an executable waypoint list handling ledges, surf, waterfalls, currents, ice and
   NPC avoidance — an AI can operate on "navigate-to" macro-actions instead of raw D-pad
   presses, dramatically shrinking its action space. `get_effective_encounter_rates_for_current_map()`
   (`map.py:2219`) gives it the true encounter distribution for planning hunts.
6. **Determinism/RNG awareness**: shininess and natures are pure functions of PID
   (`pokemon.py:1257/1240`); the daycare pre-rolls the offspring PID
   (`daycare.py:122-127`); the roamer struct exposes its IVs/PID before battle
   (`roamer.py:21`). An AI (or tool-assisted planner) can therefore *know outcomes before
   they are visible on screen* — decide per experiment whether that is allowed.
7. **Caching discipline**: any AI loop should read through `state_cache`
   (`state_cache.py:301`) exactly like existing getters do — reads are frame-consistent and
   deduplicated, keeping a per-frame full observation cheap.
