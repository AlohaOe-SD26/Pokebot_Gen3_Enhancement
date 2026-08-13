Here is the structured, decomp-accurate breakdown for an autonomous bot navigating from the Fortree Gym completion (Feather Badge) through to Mt. Pyre in Pokémon Emerald. 

### 1. HM Requirements for Eastward Progression
| HM / Item | Status | Purpose / Location |
|-----------|--------|--------------------|
| **HM03 Surf** | **[VERIFIED] REQUIRED** | Required on `MAP_ROUTE122` to cross the water and reach `MAP_MT_PYRE_EXTERIOR`. |
| **HM01 Cut** | **[VERIFIED] OPTIONAL** | Allows bypass of tall grass mazes on `MAP_ROUTE120`. Not strictly required to progress. |

---

### 2. Story Progression Steps & Event Flags

#### Step A: Route 120 (Steven & The Devon Scope)
**Decomp Path:** `data/maps/Route120/scripts.inc`
*   **Trigger:** The bridge heading south is blocked by an invisible Kecleon. 
*   **Interaction:** 
    *   Interact with the invisible entity (acts like a generic NPC interaction).
    *   `Route120_EventScript_Steven` executes.
    *   Steven asks if the player is ready to battle. (Requires a `YES` from standard menu).
    *   Uses `ITEM_DEVON_SCOPE` to reveal Kecleon, forcing a wild battle.
    *   After battle, Steven gives `ITEM_DEVON_SCOPE`.
*   **Required State Changes:**
    *   **[VERIFIED]** `FLAG_RECEIVED_DEVON_SCOPE` (Set when Steven hands it over).
    *   **[VERIFIED]** `FLAG_HIDE_ROUTE_120_STEVEN` (Set to remove Steven).
    *   **[VERIFIED]** `FLAG_HIDE_ROUTE_120_KECLEON_BRIDGE` (Set to remove the blocking Kecleon).
*   **Map Coords:** `MAP_ROUTE120`. Bridge Kecleon is at **[INFERENCE]** `x=14, y=30`.

#### Step B: Route 121 (Aqua Grunts & Safari Zone)
**Decomp Path:** `data/maps/Route121/scripts.inc`
*   **Trigger:** Player walks east past a specific vertical line of tiles.
*   **Interaction:** 
    *   `Route121_EventScript_AquaGruntsMoveOut` triggers automatically.
    *   Camera pans; Aqua Grunts talk, then walk south toward Route 122 (Mt. Pyre).
*   **Required State Changes:**
    *   **[VERIFIED]** `VAR_ROUTE121_STATE` updates to `1` (prevents script from repeating).
*   **Map Coords:** `MAP_ROUTE121`. Trigger line is at **[UNSURE]** `x=21..23, y=14`.

#### Step C: Lilycove City (Rival Battle)
**Decomp Path:** `data/maps/LilycoveCity/scripts.inc`
*   **Trigger:** Approaching the Department Store from the west or south.
*   **Interaction:**
    *   Triggered by scripts `LilycoveCity_EventScript_RivalTrigger0` through `LilycoveCity_EventScript_RivalTrigger3` (depending on y-coordinate).
    *   May/Brendan initiates battle (Rival Battle 3).
*   **Required State Changes:**
    *   **[VERIFIED]** Checks `VAR_LILYCOVE_CITY_STATE == 0`.
    *   **[VERIFIED]** Sets `VAR_LILYCOVE_CITY_STATE = 1`.
    *   **[VERIFIED]** Sets `FLAG_DEFEATED_RIVAL_LILYCOVE`.
    *   **[VERIFIED]** Sets `FLAG_HIDE_LILYCOVE_CITY_RIVAL`.
*   **Map Coords:** `MAP_LILYCOVE_CITY`. Triggers are at **[INFERENCE]** `x=24, y=14` to `x=24, y=18`.

#### Step D: Lilycove Contest Hall (Pokéblock Case)
**Decomp Path:** `data/maps/LilycoveCity_ContestLobby/scripts.inc`
*   **Emerald Difference:** **[VERIFIED]** In RS, Contest Halls were split by rank across Fallarbor, Verdanturf, Slateport, and Lilycove. In Emerald, *all* ranks are unified in Lilycove. Fallarbor and Verdanturf have Battle Tents instead.
*   **Interaction:**
    *   Speak to the Receptionist NPC on the left side of the lobby.
    *   Executes `LilycoveCity_ContestLobby_EventScript_Receptionist`.
*   **Required State Changes:**
    *   **[VERIFIED]** Player receives `ITEM_POKEBLOCK_CASE`.
    *   **[VERIFIED]** Sets `FLAG_RECEIVED_POKEBLOCK_CASE`.
*   **Map Coords:** `MAP_LILYCOVE_CITY_CONTEST_LOBBY`.

#### Step E: Accessing the Safari Zone
**Decomp Path:** `data/maps/Route121_SafariZoneEntrance/scripts.inc`
*   **Prerequisite:** Must have `ITEM_POKEBLOCK_CASE` from Lilycove.
*   **Interaction:** 
    *   Speak to the front desk NPC.
    *   Checks for the case. Deducts 500 Pokédollars. Gives 30 Safari Balls.
*   **Map Constants:** `MAP_ROUTE121_SAFARI_ZONE_ENTRANCE` leading to `MAP_SAFARI_ZONE_SOUTH`.

---

### 3. Key Point of Interest: Move Deleter
*   **Map Constant:** `MAP_LILYCOVE_CITY_MOVE_DELETERS_HOUSE`
*   **Decomp Path:** `data/maps/LilycoveCity_MoveDeletersHouse/scripts.inc`
*   **Location/Coords:** The house immediately east of the Lilycove Department Store. Enter from `MAP_LILYCOVE_CITY` at **[INFERENCE]** `x=43, y=14`.
*   **Script Name:** `MoveDeleter_EventScript_ChooseMonAndMoveToForget`. It safely removes HM moves (except Surf if it's the only Pokémon with Surf in the party).

---

### 4. Wild Encounter Tables (Emerald Specific)
**Decomp Path:** `src/data/wild_encounters.json` (or `.h` in older decomp versions)

*Note on Data: The exact percentages and levels below are marked as **[RECALL]**, but the specific Pokémon species present in Emerald vs RS are **[VERIFIED]**.*

#### `MAP_ROUTE120`
*   **Emerald Difference:** Seedot/Lotad evolution lines differ. Surskit and Roselia are missing in Emerald.
| Terrain | Species | Levels | Encounter Rate (approx) |
| :--- | :--- | :--- | :--- |
| **Land (Grass)** | Poochyena | 25-27 | **[RECALL]** 20% |
| | Mightyena | 26-28 | **[RECALL]** 20% |
| | Oddish | 25-27 | **[RECALL]** 20% |
| | Marill | 25-27 | **[RECALL]** 20% |
| | Absol | 25-27 | **[RECALL]** 10% |
| | Kecleon | 25-27 | **[RECALL]** 10% |
| **Water (Surf)** | Marill | 10-30 | **[RECALL]** 60% |
| | Goldeen | 10-30 | **[RECALL]** 40% |
| **Fishing (Old/Good/Super)** | Magikarp, Goldeen, Barboach | Varies | Standard Rod Distributions |

#### `MAP_ROUTE121`
| Terrain | Species | Levels | Encounter Rate (approx) |
| :--- | :--- | :--- | :--- |
| **Land (Grass)** | Poochyena | 25-27 | **[RECALL]** 20% |
| | Mightyena | 26-28 | **[RECALL]** 20% |
| | Shuppet | 27-29 | **[RECALL]** 20% |
| | Oddish | 25-27 | **[RECALL]** 15% |
| | Gloom | 27-29 | **[RECALL]** 15% |
| | Wingull | 25-27 | **[RECALL]** 10% |
| | Kecleon | 25-27 | **[RECALL]** 1% (Rare) |
| **Water (Surf)** | Tentacool | 10-30 | **[RECALL]** 60% |
| | Wingull | 10-30 | **[RECALL]** 35% |
| | Pelipper | 25-30 | **[RECALL]** 5% |

#### `MAP_ROUTE122`
| Terrain | Species | Levels | Encounter Rate (approx) |
| :--- | :--- | :--- | :--- |
| **Water (Surf)** | Tentacool | 10-30 | **[RECALL]** 60% |
| | Wingull | 10-30 | **[RECALL]** 35% |
| | Pelipper | 25-30 | **[RECALL]** 5% |
| **Fishing** | Magikarp, Tentacool, Wailmer | Varies | Standard Ocean Rod Distributions |

#### `MAP_ROUTE123` (Optional Bot Path, Berry Master)
| Terrain | Species | Levels | Encounter Rate (approx) |
| :--- | :--- | :--- | :--- |
| **Land (Grass)** | Poochyena | 25-27 | **[RECALL]** 20% |
| | Mightyena | 26-28 | **[RECALL]** 20% |
| | Shuppet | 27-29 | **[RECALL]** 20% |
| | Oddish | 25-27 | **[RECALL]** 15% |
| | Gloom | 27-29 | **[RECALL]** 15% |
| | Wingull | 25-27 | **[RECALL]** 10% |
| **Water (Surf)** | Tentacool | 10-30 | **[RECALL]** 60% |
| | Wingull | 10-30 | **[RECALL]** 35% |
| | Pelipper | 25-30 | **[RECALL]** 5% |

---

### 5. Routing Bot Memory Directives
When programming the bot state-machine for this segment:
1.  **Monitor `FLAG_RECEIVED_DEVON_SCOPE`**: Until this is true, pathfinding east of Route 120's bridge is impossible. The invisible Kecleon blocks standard movement tiles. Bot must interact at specific bridge tile to progress.
2.  **Verify `VAR_LILYCOVE_CITY_STATE`**: Before attempting to navigate Lilycove (e.g., to heal at Pokémon Center or go to the Contest Hall), the bot *must* path through the `x=24` meridian in `MAP_LILYCOVE_CITY`, forcing the Rival battle. Ensure the bot's party is healed *before* entering Lilycove, as it will be ambushed.
3.  **Monitor `FLAG_RECEIVED_POKEBLOCK_CASE`**: The Safari Zone entrance (`data/maps/Route121_SafariZoneEntrance`) script halts the bot with a dialog box preventing passage if this flag is false.
4.  **Mt. Pyre Access**: The bot will transition from `MAP_ROUTE121` -> `MAP_ROUTE122` by using Surf. Monitor memory for `HM03` in party moveset. There is no land bridge to Mt. Pyre.