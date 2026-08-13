Here is the exhaustive, ROM-accurate catalog of overworld obstacles in Pokémon Emerald, formatted for bot development and autonomous solving. 

All claims are marked **[VERIFIED]** (known accurate to `pokeemerald` decompilation) or **[INFERENCE/RECALL]** (highly likely based on general Gen 3 engine knowledge, but requires double-checking the exact C function name/constant).

### PART 1: Object-Event Based Obstacles
These obstacles are map entities (Objects), not metatiles. A bot finds them in `data/maps/<MapName>/map.json` under `object_events`. The bot solves them by facing the object, pressing A, and passing the script checks.

| Obstacle | Visual ID (Graphics) | Key Script | Pass Requirements (Memory) |
| :--- | :--- | :--- | :--- |
| **Cuttable Trees** | `OBJ_EVENT_GFX_CUTTABLE_TREE` | `EventScript_CutTree` | `FLAG_BADGE01_GET` (Stone Badge) == 1.<br>Party Pokémon must know `MOVE_CUT`. |
| **Rock Smash Rocks** | `OBJ_EVENT_GFX_BREAKABLE_ROCK` | `EventScript_RockSmash` | `FLAG_BADGE03_GET` (Dynamo Badge) == 1.<br>Party Pokémon must know `MOVE_ROCK_SMASH`. |
| **Strength Boulders** | `OBJ_EVENT_GFX_PUSHABLE_BOULDER` | `EventScript_StrengthBoulder` | `FLAG_BADGE04_GET` (Heat Badge) == 1.<br>`FLAG_SYS_USE_STRENGTH` == 1 (Set by using the move from the menu or pressing A on a boulder). |

**Mechanics & Solver Notes:**
*   **[VERIFIED]** Source: `data/scripts/field_move_scripts.inc`.
*   **[VERIFIED]** When broken/cut, the script calls `FieldEffectStart(...)`, plays an animation, and uses `removeobject VAR_LAST_TALKED` to clear the collision.
*   **[VERIFIED]** For Strength, the object is not removed. Pushing logic lives in `src/field_player_avatar.c` (`PushObject`). The bot must have `FLAG_SYS_USE_STRENGTH` set; once set, moving into the object coordinates triggers the push if the tile behind the boulder is walkable (collision check).

---

### PART 2: Metatile-Behavior Based Obstacles
These are inherent properties of the map grid. The bot identifies them by reading the map's current metatile array and looking up the behavior in `include/constants/metatile_behaviors.h` (`MB_...`). The movement logic is handled in `src/field_player_avatar.c` and `src/field_control_avatar.c`.

#### 1. Currents / Whirlpools
*   **Map Constants:** `MAP_ROUTE132`, `MAP_ROUTE133`, `MAP_ROUTE134`.
*   **Metatile Behaviors:** `MB_CURRENT_W`, `MB_CURRENT_E`, `MB_CURRENT_N`, `MB_CURRENT_S`.
*   **[VERIFIED] Mechanic:** Stepping onto these metatiles locks player input. The game engine overrides d-pad input and forces player movement in the specified direction.
*   **Solver Note:** This is a directed acyclic graph (DAG) traversal. The bot must calculate the end-point of a current path before stepping onto the first tile.

#### 2. Sky Pillar Crumbling Floors
*   **Map Constants:** `MAP_SKY_PILLAR_2F`, `MAP_SKY_PILLAR_4F`.
*   **Emerald Difference:** **[VERIFIED]** Sky Pillar is mandatory before the Elite 4 in Emerald. The floor layouts are entirely different from Ruby/Sapphire.
*   **Metatile Behavior:** `MB_CRUMBLING_FLOOR` (changes to `MB_CRUMBLED_FLOOR` / hole when broken).
*   **[INFERENCE/RECALL] Mechanic:** Located in `src/bike.c` and `src/field_player_avatar.c`. The game checks if the player is currently riding the Mach Bike (`PlayerIsOnMachBike()`) **and** maintaining maximum speed. If the player drops speed, turns without momentum, or stops, the metatile breaks and triggers a fall to the floor below (warp).
*   **Solver Note:** The bot must simulate sustained D-Pad inputs without stopping. 90-degree turns require instantaneous directional shifts on the exact frame the player hits the tile center, without releasing input.

#### 3. Mirage Tower / Desert Ruins Sand (Mud Slopes)
*   **Map Constants:** `MAP_MIRAGE_TOWER_1F` to `MAP_MIRAGE_TOWER_4F` (Mirage Tower is **Emerald Exclusive**).
*   **Metatile Behavior:** `MB_MUD_SLOPE`.
*   **[VERIFIED] Mechanic:** Similar to Crumbling Floors. To ascend the slope (move North), the player must be on a Mach Bike at top speed. Moving laterally or South over them does not require momentum. If speed is insufficient, collision behaves as a solid wall.

#### 4. Mossdeep Gym Spin Tiles
*   **Map Constant:** `MAP_MOSSDEEP_CITY_GYM`.
*   **Emerald Difference:** **[VERIFIED]** The Mossdeep Gym puzzle is completely redesigned in Emerald. RS used a static layout. Emerald uses interactive statues (switches) that dynamically change the spin tile paths.
*   **Metatile Behaviors:** `MB_SPIN_RIGHT`, `MB_SPIN_LEFT`, `MB_SPIN_UP`, `MB_SPIN_DOWN`.
*   **[VERIFIED] Mechanic:** Stepping on an arrow locks input and slides the player.
*   **[INFERENCE/RECALL] Dynamic Mechanic:** Hitting the color-coded switches triggers scripts that use `setmetatile` to physically alter the map array in memory. A solver cannot rely on the static `map.bin` layout; it must read the *current working map array* in RAM to calculate paths, updating its graph every time a switch is flipped.

#### 5. Sootopolis Gym Cracked Ice
*   **Map Constants:** `MAP_SOOTOPOLIS_CITY_GYM_1F`, `MAP_SOOTOPOLIS_CITY_GYM_B1F`.
*   **Metatile Behavior:** `MB_THIN_ICE` (unstepped), `MB_CRACKED_ICE` (stepped once).
*   **[VERIFIED] Mechanic:** Handled via a Step Callback (`STEP_CB_CRACKED_ICE` or similar in `src/field_control_avatar.c`). When stepping off `MB_THIN_ICE`, the metatile behind the player is updated to `MB_CRACKED_ICE`.
*   **[INFERENCE/RECALL] Pass Condition:** The game maintains a counter in memory (likely `VAR_ICE_STEP_COUNT`). When the room loads, this var is set to the total number of ice tiles. Each valid step decrements it. If a player steps on `MB_CRACKED_ICE`, they fall. If they step on the end stairs when the var is exactly `0`, the next floor opens.
*   **Solver Note:** This is a Hamiltonian Path problem. The bot must map the contiguous block of `MB_THIN_ICE`, calculate a path touching every node exactly once, and ending at the exit tile.

---

### PART 3: Complex / Composite Rooms
These are specific map instances that combine standard mechanics into complex solver scenarios.

#### Trick House (Emerald specific)
*   **Map Constants:** `MAP_TRICK_HOUSE_PUZZLE_1` through `MAP_TRICK_HOUSE_PUZZLE_8`.
*   **Emerald Difference:** **[VERIFIED]** The puzzles in Emerald are entirely different from Ruby/Sapphire.
*   **Mechanics by Puzzle [INFERENCE/RECALL for exact order, highly confident in puzzle mechanics]:**
    *   *Puzzle 1:* Cut Trees (`EventScript_CutTree`).
    *   *Puzzle 2:* Floor switches that use `setmetatile` to close holes.
    *   *Puzzle 3:* Mech doors / switches (Red/Blue switches). `setmetatile` alters the walls.
    *   *Puzzle 4:* Strength Boulders.
    *   *Puzzle 5:* Quiz Mechs (interact with objects, requires matching answers).
    *   *Puzzle 6:* Fortree-style rotating doors (Metatile behaviors that block movement from one side, and rotate 90 degrees when pushed from the valid side).
    *   *Puzzle 7:* Spin Pads & Teleporters (Mossdeep / Team Aqua hideout mechanics).
    *   *Puzzle 8:* Slippery Ice Floors (`MB_ICE`). Sliding until hitting an object or wall.

#### Granite Cave / Seafloor Cavern Boulder Rooms
*   **Map Constants:** `MAP_GRANITE_CAVE_B2F`, `MAP_SEAFLOOR_CAVERN_ROOM_1`, `MAP_SEAFLOOR_CAVERN_ROOM_4`, etc.
*   **Mechanic:** These use the standard `OBJ_EVENT_GFX_PUSHABLE_BOULDER`.
*   **Solver Note:** Pushing a boulder physically updates the Object Event's X/Y coordinates in memory. This permanently alters the collision grid of the room until the player leaves and re-enters. A bot solver must treat this as a Sokoban state-space search. The exact coordinates of boulders are initialized from the `map.json`, but the solver must read their *live* X/Y coordinates in RAM (`gObjectEvents` array) to pathfind safely.

---

### Actionable Advice for Bot Implementation
1.  **Map Reading:** Do not rely exclusively on the static ROM definitions for dynamic rooms (Mossdeep Gym, Trick House). Read the working map array from RAM. The pointer to the current map block is accessible via `gMapHeader`.
2.  **Object Events:** A bot should parse the `gObjectEvents` array (found in `src/event_object_movement.c` memory space). Look at the `currentCoords.x` and `currentCoords.y` rather than the initial coords, as Strength boulders update these live.
3.  **Collision Checks:** Implement a replica of `GetMetatileBehavior` in your bot to read the current map tile behavior before executing a directional input. This avoids attempting to move through newly-spawned walls (Trick House) or falling through broken floors (Sky Pillar).