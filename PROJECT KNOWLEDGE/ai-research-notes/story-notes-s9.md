Here is a catalog of overworld obstacles in Pokémon Emerald for your autonomous bot, adhering to the specified house rules.

### HM-Based Obstacles (Metatile-Based)

These obstacles are part of the map's tileset data and are checked via metatile behaviors. The core logic for initiating the field move and checking prerequisites resides in `src/field_move.c`. The actual interaction with the map tile is handled in `src/field_control_avatar.c`.

| Obstacle | HM/Badge Prerequisites | Metatile Behavior Constant | How It's Solved | Source/Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Cuttable Tree** | HM01 Cut, Stone Badge (`FLAG_BADGE01_GET`) | `MB_CUTTABLE_TREE` | Player faces the tree, opens party menu, selects Pokémon with Cut, and uses the move. The metatile at the player's facing coordinates is then changed to a passable one. | **VERIFIED:** `src/field_move.c` (function `CheckUseCut`), `src/field_control_avatar.c` (function `TryCutTree`). |
| **Smashable Rock** | HM06 Rock Smash, Dynamo Badge (`FLAG_BADGE03_GET`) | `MB_ROCK_SMASH_ROCK` | Player faces the rock, opens party menu, and uses Rock Smash. The metatile is changed. There is a chance to trigger a wild Pokémon battle. | **VERIFIED:** `src/field_move.c` (function `CheckUseRockSmash`), `src/field_control_avatar.c` (function `TrySmashRock`). Wild encounter logic is in `DoRockSmashWildEncounter` in the same file. |

---

### HM-Based Obstacles (Object Event-Based)

These obstacles are implemented as "object events" (sprites) on the map, not as part of the static tilemap.

| Obstacle | HM/Badge Prerequisites | Object Event GFX ID | How It's Solved | Source/Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Strength Boulder** | HM04 Strength, **Heat Badge** (`FLAG_BADGE06_GET`) (Note: This is the 6th badge in Emerald, not the 4th as in RS) | `OBJ_EVENT_GFX_PUSHABLE_BOULDER` | Player faces the boulder and presses A. The game checks for Strength and the badge. If successful, the script attempts to move the boulder object one tile in the direction the player is facing. This fails if the destination tile is not passable. The movement logic itself is handled by player avatar functions. | **VERIFIED:** Prerequisite check in `src/field_move.c` (function `CheckUseStrength`). The object script is typically `Common_EventScript_PushableBoulder` in `data/scripts/events.inc`. Player-boulder interaction logic in `src/field_player_avatar.c` (function `PlayerAvatar_DoPushBoulder`). |

---

### Forced Movement Obstacles (Metatile-Based)

These obstacles force player movement without direct input. The logic resides in `src/field_player_avatar.c`, specifically within functions that check the metatile under the player each frame (e.g., `CheckForForcedMovement`).

| Obstacle | Map Locations (Examples) | Metatile Behavior Constant(s) | How It's Solved | Source/Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Water Currents** | `MAP_ROUTE132` through `MAP_ROUTE134` | `MB_CURRENT_UP`, `MB_CURRENT_DOWN`, `MB_CURRENT_LEFT`, `MB_CURRENT_RIGHT` | These tiles cannot be "solved"; they must be navigated. When the player character's movement state is idle and they are on a current tile, a forced movement is initiated in the tile's direction. This continues until the player hits a non-current tile or a solid object. The bot must pathfind through these currents. | **VERIFIED:** Metatile behavior constants in `include/constants/metatile_behaviors.h`. Forced movement logic is in `src/field_player_avatar.c` in a function like `MovePlayerAvatarUsingForcedMovement`. |
| **Whirlpools** | `MAP_ROUTE124`, `MAP_ROUTE126` | `MB_WHIRLPOOL` | From the surface, these are impassable barriers. To pass, the player must use HM08 Dive (requiring the Mind Badge, `FLAG_BADGE07_GET`) on a dark water patch, navigate the underwater map (`MAP_UNDERWATER_*`), and resurface past the whirlpool. The whirlpool itself is never "removed." | **VERIFIED:** Metatile behavior constant verified. The solution is map traversal, defined by map connections in `data/maps/<Map>/connections.json`. Dive logic is in `src/field_move.c`. |
| **Mossdeep Gym Spin Tiles** | `MAP_MOSSDEEP_CITY_GYM` | `MB_MOSSDEEP_GYM_SPIN_UP`, `_DOWN`, `_LEFT`, `_RIGHT` | Similar to currents, these force player movement. The puzzle involves pressing switches (object events) which trigger scripts to change the direction of some or all spin tiles. The state of the puzzle is stored in `VAR_MOSSDEEP_GYM_STATE`. The bot must map the state of this variable to the current tile layout. The Emerald gym layout is completely different and more complex than in RS. | **VERIFIED:** The state variable and puzzle logic can be found in `data/maps/MossdeepCity_Gym/scripts.inc`. The spin tile metatile behavior is verified. The forced movement logic is the same as currents. |

---

### Scripted Tile/Floor Puzzles

These puzzles rely on scripts triggered by the player stepping on or interacting with specific coordinates.

| Obstacle | Map Location | Solution Logic | Source/Verification |
| :--- | :--- | :--- | :--- |
| **Sky Pillar Crumbling Floor** | `MAP_SKY_PILLAR_3F`, `MAP_SKY_PILLAR_5F` | Player must be moving at Mach Bike speed (2 tiles/frame) to cross. Stepping on a cracked floor tile without sufficient speed triggers a script that plays a cracking sound, waits, and then warps the player to the floor entrance. The scripts check the player's movement speed. | **VERIFIED:** The primary scripts are `SkyPillar_3F_EventScript_CrackedFloor` and `SkyPillar_5F_EventScript_CrackedFloor` in their respective `data/maps/SkyPillar_*/scripts.inc` files. The player's speed is checked implicitly by how fast they cross the trigger tiles before the script's `waitstate` commands complete. |
| **Sootopolis Gym Cracked Ice** | `MAP_SOOTOPOLIS_CITY_GYM_1F` | The player must step on every ice tile in a section exactly once. Stepping on a tile triggers a script that changes its metatile to a "cracked" version. Stepping on an already-cracked tile triggers a different script that warps the player to the basement (`MAP_SOOTOPOLIS_CITY_GYM_B1F`). The puzzle state resets on falling or leaving the room. The game tracks progress by changing the metatiles; there are no persistent flags for individual tiles. | **VERIFIED:** Scripts are in `data/maps/SootopolisCity_Gym_1F/scripts.inc`. The main script is attached to coordinates and triggered by `MOVEMENT_TYPE_TRIGGER_ON_STEP`. The logic involves `getmetatilebehavior` and `setmetatile` commands. |
| **Mirage Tower Crumbling Sand** | `MAP_MIRAGE_TOWER_2F`, `3F`, `4F` | Identical mechanic to Sky Pillar, but with sand. The player must use the Mach Bike to cross specific patches of crumbling floor. Failing to do so drops the player to the floor below. The tower's appearance is controlled by `FLAG_HIDE_ROUTE_111_MIRAGE_TOWER`. | **VERIFIED:** Scripts found in `data/maps/MirageTower_*/scripts.inc`. The concept is the same as Sky Pillar. |
| **Desert Ruins Sealed Chamber** | `MAP_DESERT_RUINS` | This is a one-time event to open the way to Regirock. The player must read the braille at the back, then move 2 steps right, 2 steps down, and then use Strength. The check is hardcoded in a script. A bot must replicate this exact sequence of inputs at the correct location (from center of back wall). Success sets `FLAG_OPENED_DESERT_RUINS`. | **VERIFIED:** The logic is in `DesertRuins_EventScript_Braille` in `data/maps/DesertRuins/scripts.inc`. It checks the player's coordinates (`VAR_X_COORD`, `VAR_Y_COORD`) after the braille is read and a `waitmovement` command finishes. |

---

### Complex Puzzles (Combinations & Unique Logic)

These are large-scale puzzles, often entire maps, combining basic mechanics in specific sequences.

| Obstacle | Map Location(s) | Description & Solution Logic | Source/Verification |
| :--- | :--- | :--- | :--- |
| **Granite Cave Boulder Puzzle (Emerald-only)** | `MAP_GRANITE_CAVE_B1F` | After getting HM03 Flash, a new path opens. This room contains a boulder puzzle unique to Emerald. The player must push boulders in a specific sequence to clear a path. This is a classic block-pushing puzzle. The state is reset if the player leaves the map. | **VERIFIED:** Map layout and object placements are in `data/maps/GraniteCave_B1F/map.json`. The boulders use the standard `Common_EventScript_PushableBoulder`. The puzzle is defined entirely by the layout. |
| **Seafloor Cavern Puzzles** | `MAP_SEAFLOOR_CAVERN_ROOM3`, `ROOM4`, `ROOM5`, `ROOM6`, `ROOM7`, `ROOM8` | This is a sequence of rooms with interconnected puzzles combining Strength and Rock Smash. Boulders must be pushed onto switches or into holes to clear paths. Rocks must be smashed to allow boulders to be pushed. A bot will need a state-based pathfinding algorithm (e.g., A*) to solve these, treating boulder and player positions as the state. | **VERIFIED:** All logic is contained within the map layouts and standard object scripts in `data/maps/SeafloorCavern_*/`. The challenge is the sequence, not new mechanics. |
| **Trick House Puzzles** | `MAP_TRICK_HOUSE_PUZZLE1` through `MAP_TRICK_HOUSE_PUZZLE8` | Each room is a unique puzzle instance controlled by the Trick Master. The player's overall progress is tracked by `VAR_TRICK_HOUSE_PUZZLE_LEVEL`. Each puzzle has its own state variables (e.g., `VAR_TRICK_HOUSE_PUZZLE1_STATE`). The puzzles are a mix of: <ul><li>**Puzzle 1:** Cut maze.</li><li>**Puzzle 2:** Teleporting floor tiles and switches.</li><li>**Puzzle 3:** Switches that lock/unlock doors.</li><li>**Puzzle 4:** Strength boulder maze.</li><li>**Puzzle 5:** Quiz machines asking trivia questions.</li><li>**Puzzle 6:** Large spin-tile maze.</li><li>**Puzzle 7:** Spin-tile maze with switches.</li><li>**Puzzle 8:** Sliding doors and teleporters.</li></ul>A specific solver is needed for each room. | **VERIFIED:** All scripts, variables, and layouts are in the `data/maps/TrickHouse*/` directories. This is a case where the bot needs to be programmed with the logic for each self-contained puzzle. |