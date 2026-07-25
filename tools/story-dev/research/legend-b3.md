Here are the ROM-accurate facts about roaming Pokémon in Pokémon Emerald.

### 1. Roamer Selection Mechanic

The roaming Pokémon in Emerald is either Latias or Latios. The choice is presented to the player after they become the Champion.

*   **VERIFIED:** The selection event occurs in the player's bedroom after defeating the Champion and viewing the credits.
*   **Location:** `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_2F`, specifically by interacting with the television. (VERIFIED)
*   **Trigger:** The event is controlled by `VAR_LITTLEROOT_TOWN_STATE`. After the Hall of Fame, this variable is set to a value that enables the TV event. The script is `LittlerootTown_PlayersHouse_2F_EventScript_Mom` in `data/maps/LittlerootTown_PlayersHouse_2F/scripts.inc`. (VERIFIED)
*   **The Question:** Mom asks the player what color the Pokémon on TV was.
    *   Choosing **"RED"** sets **Latias** as the roamer.
    *   Choosing **"BLUE"** sets **Latios** as the roamer.
*   **Script Logic:** The script uses a `multichoice` box. Based on the result (0 for RED, 1 for BLUE), it calls either `LittlerootTown_PlayersHouse_2F_EventScript_SetLatias` or `LittlerootTown_PlayersHouse_2F_EventScript_SetLatios`. These scripts call the functions `SetLatias()` and `SetLatios()` respectively, defined in `src/roamer.c`. (VERIFIED)
*   **Emerald vs. RS:** This TV choice mechanic is **exclusive to Emerald**. In Ruby and Sapphire, the roamer was automatically set based on the game version (Latias in Sapphire, Latios in Ruby) without player input. (VERIFIED)

### 2. Roamer Data Storage

The roamer's identity, status, and location are stored in a dedicated `struct Roamer` within the save block. For a bot with memory access, this is the canonical source of truth.

*   **Location in Memory:** `gSaveBlock1Ptr->roamer` (VERIFIED, defined in `include/global.h`, instance in `src/save.c`).
*   **Key Data Fields:**

| Field | Type | Description | Decomp Source |
| :--- | :--- | :--- | :--- |
| `species` | `u16` | The species of the roamer (`SPECIES_LATIAS` or `SPECIES_LATIOS`). | VERIFIED |
| `level` | `u8` | The roamer's level. Initially set to 40. | VERIFIED (`ROAMER_LEVEL` in `src/roamer.c`) |
| `status` | `u32` | The roamer's status condition (e.g., `STATUS1_SLEEP`). Persists between encounters. | VERIFIED |
| `hp` | `u16` | The roamer's current HP. Persists between encounters. | VERIFIED |
| `location` | `u32` | A packed value of the map group and map number where the roamer is currently located. | VERIFIED |
| `ivs` | `u32` | The roamer's IVs, packed into a single 32-bit integer. | VERIFIED |
| `personality` | `u32` | The roamer's personality value (PID). | VERIFIED |
| `active` | `bool8` | A flag indicating if the roamer is currently active and moving around Hoenn. | VERIFIED |

*   **Enabling Flag:** The choice event sets `FLAG_SYS_ROAMER_INFO_ENABLED` to true, which enables the roamer functionality. The roamer struct's `active` field is also set to `TRUE`. (VERIFIED, `src/roamer.c`, `InitRoamer()`)

### 3. Roaming Behavior

The roamer's movement is deterministic but appears random to the player.

*   **Movement Trigger:** The roamer's location is updated whenever the player transitions between maps (e.g., entering a route from a city). The function `RoamerMove()` in `src/roamer.c` is responsible for this. (VERIFIED)
*   **Location Storage:** The roamer's location is stored in `gSaveBlock1Ptr->roamer.location`. This value can be read directly to know exactly where the roamer is at all times. (VERIFIED)
*   **Valid Locations:** The roamer can only move to a predefined set of outdoor routes and waterways. This list is defined in `const u8 sRoamerLocations[][5]` in `src/roamer.c`. (VERIFIED)
*   **Possible Routes:**
    *   Route 110 through Route 134. (VERIFIED, from `sRoamerLocations` array)
*   **Tracking In-Game:** The Pokédex's "Area" function will show the roamer's current location once it has been seen. A bot can bypass this entirely by reading the `location` field from memory. (VERIFIED)
*   **Encounter Logic:** When the game generates a wild encounter on a map where the roamer is present (`gSaveBlock1Ptr->roamer.location` matches player's location), there is a chance for the encounter to be the roamer instead of a regular wild Pokémon. This is handled by `TryGenerateRoamerEncounter()` in `src/wild_encounter.c`. (VERIFIED)

### 4. The Encounter and Fleeing

Encounters with the roamer are unique. Its state is saved after each battle.

*   **Flee-on-Sight:** The roamer will attempt to flee on the first turn of battle.
    *   **Mechanic:** This is not a standard "flee". The game uses a specific battle script command that checks if the opponent is a roamer. If it is and it is not prevented from fleeing, it will escape before the player can act, unless the player's Pokémon is faster and uses a trapping move. The function `IsRoamerTheFirstToAttack` in `src/battle_script_commands.c` returns `B_RUN_SUCCESS` to trigger the flee message. (VERIFIED)
*   **Preventing Escape:**
    *   **Moves:** `Mean Look` and `Block` prevent the roamer from fleeing as long as the user remains in battle. (VERIFIED)
    *   **Abilities:** The abilities `Arena Trap` (Trapinch, Dugtrio) and `Shadow Tag` (Wobbuffet, Wynaut) prevent the roamer from fleeing. Note that in Gen 3, this works even on a Flying-type like Lati@s. (VERIFIED)
*   **Fast Ball:** The Fast Ball **does not work** on Latias or Latios in Generation 3. Its effect is hardcoded to only apply to Magnemite, Grimer, and Tangela. This is a common point of confusion from later generations. (VERIFIED, see `BallMultipliers` in `src/battle_util.c` and the logic for `ITEM_FAST_BALL`). Your bot should not attempt this strategy.
*   **State Persistence:** Any damage dealt and non-volatile status conditions (Poison, Paralyze, Sleep, Burn, Freeze) inflicted on the roamer are saved to `gSaveBlock1Ptr->roamer.hp` and `gSaveBlock1Ptr->roamer.status` after the battle ends. The next encounter will resume with this state. (VERIFIED)

### 5. The Eon Ticket and the Other Lati@s

The Eon Ticket provides access to the Lati@s that was *not* chosen as the roamer.

*   **VERIFIED:** The Eon Ticket is an event item, typically obtained via Mystery Gift or by mixing records with a player who has one. Placing it in the Bag enables an event.
*   **Activation:** With the Eon Ticket, taking the S.S. Tidal from Lilycove City will grant a new option to travel to **Southern Island**.
*   **Event Location:** `MAP_SOUTHERN_ISLAND_EXTERIOR`. Interacting with the egg in the center of the island will trigger the battle.
*   **The Pokémon:** The game checks which Lati@s is the roamer and spawns the other one for this static encounter.
    *   Script: `SouthernIsland_Exterior_EventScript_Lati` in `data/maps/SouthernIsland_Exterior/scripts.inc`.
    *   Logic: `if (var(VAR_RESULT) == SPECIES_LATIAS)`... spawns Latios, and vice versa. `var(VAR_RESULT)` is loaded with the roamer species via the `getroamerspecies` special. (VERIFIED)
*   **Encounter Details:**
    *   Level: 50 (VERIFIED)
    *   Behavior: This is a standard static legendary encounter. It will not flee. (VERIFIED)
    *   Held Item: This Lati@s will be holding a **Soul Dew**. (VERIFIED, `item(ITEM_SOUL_DEW)`)

### 6. Other Roaming Pokémon

*   **VERIFIED:** Latias and Latios are the **only** roaming Pokémon in Pokémon Emerald. There are no others.