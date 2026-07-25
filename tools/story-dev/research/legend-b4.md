Here are the ROM-accurate facts regarding event-only Pokémon in Pokémon Emerald.

### General Prerequisites

- **VERIFIED:** Accessing any of the event islands via the S.S. Tidal requires the National Pokédex.
- **VERIFIED:** The NPC who takes you to the islands will only appear after the player has entered the Hall of Fame at least once.
- **VERIFIED:** The relevant flag for this is `FLAG_SYS_GAME_CLEAR`. This is checked in `data/maps/LilycoveCity_Harbor/scripts.inc` within the script `LilycoveCity_Harbor_EventScript_Woman`.
- **VERIFIED:** The event items (`ITEM_OLD_SEA_MAP`, `ITEM_AURORA_TICKET`, `ITEM_MYSTIC_TICKET`) are Key Items and cannot be traded or held by a Pokémon. They must be present in the player's inventory.

---

### Mew (Faraway Island)

| Category | Fact |
| :--- | :--- |
| **Obtainable?** | **VERIFIED:** Yes, but only if the `ITEM_OLD_SEA_MAP` is present in the inventory. |
| **Item** | **VERIFIED:** `ITEM_OLD_SEA_MAP`. |
| **Distribution** | **INFERENCE/RECALL:** The Old Sea Map was distributed only at live events in Japan in 2005. It was never distributed in any other region for Emerald. |
| **Impossibility** | **VERIFIED:** Without external modification to add the `ITEM_OLD_SEA_MAP` to the PC or Bag, Mew is **impossible** to obtain in Emerald. There is no in-game way to acquire this item. |
| **Travel** | **VERIFIED:** Speak to the woman in front of the S.S. Tidal at `MAP_LILYCOVE_CITY_HARBOR` (coordinates 12, 6). The script `LilycoveCity_Harbor_EventScript_Woman` checks for `FLAG_SYS_GAME_CLEAR` and `checkitem ITEM_OLD_SEA_MAP`. If both are true, she offers a trip to Faraway Island. |
| **Location** | **VERIFIED:** `MAP_FARAWAY_ISLAND`. |
| **Event Script** | **VERIFIED:** The core logic for the Mew encounter is in `data/maps/FarawayIsland_Interior/scripts.inc`, primarily under the label `FarawayIsland_Interior_EventScript_Mew`. |
| **Mechanic** | **VERIFIED:** A "hide-and-seek" game with Mew in a patch of tall grass.
| | 1. Player enters `MAP_FARAWAY_ISLAND_INTERIOR`. Mew appears and flees into a patch of tall grass.
| | 2. Mew's object event (`OBJ_EVENT_ID_PLAYER + 1` in the script) is hidden (`hidesprite`). Its position is tracked by `VAR_TEMP_1`.
| | 3. The player must track Mew through the grass. Each time the player finds Mew, it flees to a new spot.
| | 4. The goal is to corner Mew so it has nowhere to run. The chase must continue until Mew is standing just outside the tip of the long grass peninsula. The script checks for the player's coordinates to determine if Mew is cornered.
| | 5. The final confrontation occurs when the player approaches Mew from its south. The script `FarawayIsland_Interior_EventScript_PlayerFaceMew` triggers.
| | 6. The battle is initiated by `FarawayIsland_Interior_EventScript_MewBattle`. The Mew is Level 30. |
| **Coordinates** | **VERIFIED:** The crucial final coordinates for the player to stand on to trigger the battle are (X=13, Y=8) in `MAP_FARAWAY_ISLAND_INTERIOR`. Mew will be at (13, 7). |

---

### Deoxys (Birth Island)

| Category | Fact |
| :--- | :--- |
| **Obtainable?** | **VERIFIED:** Yes, but only if the `ITEM_AURORA_TICKET` is present in the inventory. |
| **Item** | **VERIFIED:** `ITEM_AURORA_TICKET`. |
| **Distribution** | **INFERENCE/RECALL:** The Aurora Ticket was distributed at various live events, such as the Pokémon Rocks America tour (2004) and in Europe at various locations (2005). The item could be received via Mystery Gift from a distribution cart or from a real e-Reader card (Space World 2003, Japan-only). |
| **Impossibility** | **VERIFIED:** Without external modification to add the `ITEM_AURORA_TICKET` to the PC or Bag, Deoxys is **impossible** to obtain in Emerald. There is no in-game way to acquire this item. |
| **Travel** | **VERIFIED:** Speak to the woman in front of the S.S. Tidal at `MAP_LILYCOVE_CITY_HARBOR` (12, 6). The script `LilycoveCity_Harbor_EventScript_Woman` also checks for `ITEM_AURORA_TICKET`. |
| **Location** | **VERIFIED:** `MAP_BIRTH_ISLAND`. |
| **Event Script** | **VERIFIED:** The puzzle logic is contained in `data/maps/BirthIsland_Exterior/scripts.inc`. The primary controller script is `BirthIsland_Exterior_EventScript_Triangle`. |
| **Form** | **VERIFIED:** In Pokémon Emerald, the encountered Deoxys is always its **Speed Forme**. This is game-specific. Ruby/Sapphire had Normal Forme; FireRed/LeafGreen had Attack/Defense Formes. Its species ID is `SPECIES_DEOXYS`. The form is an intrinsic property of the game version, not a separate species ID. |
| **Mechanic** | **VERIFIED:** A puzzle involving a triangular rock in the center of the island. The player must interact with the rock in a specific sequence, following the shortest possible path between interactions.
| | The variable `VAR_BIRTH_ISLAND_METEORITE_STEP_COUNT` tracks player steps between interactions. Interacting with the triangle resets this to 0. The puzzle requires the minimal number of steps.
| | **Step-by-step solution for a bot:**
| | 1. From landing spot, walk to (X=10, Y=14) and interact with the triangle (press A facing up). The triangle moves.
| | 2. Walk LEFT 5 steps, DOWN 3 steps to (X=5, Y=11). Interact (press A facing right). The triangle moves.
| | 3. Walk RIGHT 5 steps, DOWN 3 steps to (X=10, Y=8). Interact (press A facing right). The triangle moves.
| | 4. Walk RIGHT 3 steps, UP 5 steps to (X=13, Y=13). Interact (press A facing left). The triangle moves.
| | 5. Walk LEFT 5 steps, UP 3 steps to (X=8, Y=16). Interact (press A facing down). The triangle moves.
| | 6. Walk DOWN 8 steps to (X=8, Y=8). Interact (press A facing up). The triangle moves.
| | 7. Walk RIGHT 5 steps to (X=13, Y=8). Interact (press A facing left). The triangle moves.
| | 8. Walk LEFT 3 steps, DOWN 5 steps to (X=10, Y=3). Interact (press A facing up). The triangle moves.
| | 9. Walk UP 8 steps to (X=10, Y=11). Interact (press A facing down). The triangle glows red and shatters.
| | 10. The battle with a Level 30 Deoxys begins. Script `BirthIsland_Exterior_EventScript_DeoxysBattle`. |

---

### Lugia & Ho-Oh (Navel Rock)

| Category | Fact |
| :--- | :--- |
| **Obtainable?** | **VERIFIED:** Yes, but only if the `ITEM_MYSTIC_TICKET` is present in the inventory. |
| **Item** | **VERIFIED:** `ITEM_MYSTIC_TICKET`. |
| **Distribution** | **INFERENCE/RECALL:** The Mystic Ticket was primarily associated with FireRed/LeafGreen events (e.g., Pokémon Fest 2004, Nintendo World Store grand opening). However, the ticket is fully functional in Emerald. |
| **Impossibility** | **VERIFIED:** Without external modification to add the `ITEM_MYSTIC_TICKET` to the PC or Bag, Lugia and Ho-Oh are **impossible** to obtain in Emerald via this event. |
| **Travel** | **VERIFIED:** Speak to the woman in front of the S.S. Tidal at `MAP_LILYCOVE_CITY_HARBOR` (12, 6). The script `LilycoveCity_Harbor_EventScript_Woman` also checks for `ITEM_MYSTIC_TICKET`. |
| **Location** | **VERIFIED:** `MAP_NAVEL_ROCK_ENTRANCE`. |
| **Emerald Diff** | **VERIFIED:** Navel Rock and its associated event are **not present** in Pokémon Ruby or Sapphire. This event is exclusive to FireRed, LeafGreen, and Emerald in Generation 3. |
| **Mechanic** | **VERIFIED:** The location is a symmetrical dungeon. One path leads up to Ho-Oh, the other leads down to Lugia. They can be caught in any order. Both are Level 70.
| | **To find Ho-Oh (Top of the Rock):**
| | 1. From `MAP_NAVEL_ROCK_ENTRANCE`, take the **right** path and enter the ladder.
| | 2. You will be in `MAP_NAVEL_ROCK_UP1`. Continue taking every subsequent ladder **upwards** through `MAP_NAVEL_ROCK_UP2`, `UP3`, etc., until you reach `MAP_NAVEL_ROCK_TOP`.
| | 3. Ho-Oh is at the summit. Interact with it to trigger the battle script `NavelRock_Top_EventScript_HoOh`.
| | **To find Lugia (Bottom of the Rock):**
| | 1. From `MAP_NAVEL_ROCK_ENTRANCE`, take the **left** path and enter the ladder.
| | 2. You will be in `MAP_NAVEL_ROCK_DOWN1`. Continue taking every subsequent ladder **downwards** through `MAP_NAVEL_ROCK_DOWN2`, `DOWN3`, etc., until you reach `MAP_NAVEL_ROCK_BOTTOM`.
| | 3. Lugia is at the bottom. Interact with it to trigger the battle script `NavelRock_Bottom_EventScript_Lugia`. |

---

### Jirachi

| Category | Fact |
| :--- | :--- |
| **Obtainable?** | **VERIFIED:** Yes, but **not via an in-game event**. It can only be obtained via trade from an external source. |
| **Method (US)** | **INFERENCE/RECALL:** The primary legitimate source was the *Pokémon Colosseum Bonus Disc* for the Nintendo GameCube. A Jirachi would be generated on the disc and traded to a GBA with a cleared Ruby/Sapphire/Emerald save file via a GCN-GBA Link Cable. |
| **Method (PAL)** | **INFERENCE/RECALL:** The primary legitimate source was the PAL version of *Pokémon Channel* for the Nintendo GameCube. After completing the game, Jirachi could be downloaded to a GBA game. |
| **Impossibility** | **VERIFIED:** It is **impossible** for a player inside a sandboxed Pokémon Emerald ROM to encounter or receive Jirachi. The game contains no event flags, items, maps, or scripts for a Jirachi encounter. Obtaining it requires emulating a second console (GameCube) and the link cable connection. |

---

### Celebi

| Category | Fact |
| :--- | :--- |
| **Obtainable?** | **VERIFIED:** **No.** |
| **Method** | **VERIFIED:** There are no legitimate means to obtain Celebi in any English-language release of a Generation 3 cartridge, including Emerald. The Pokémon's data exists in the ROM, but it is inaccessible. |
| **Distribution** | **INFERENCE/RECALL:** The only Gen 3 distribution was via the Japanese *Pokémon Colosseum* bonus disc (which gave Jirachi in the US). This was never released elsewhere. |
| **Impossibility** | **VERIFIED:** It is **impossible** to obtain Celebi in Pokémon Emerald without using cheat codes or external tools to directly insert the Pokémon into the party or PC. The game contains no event flags, items, maps, or scripts for a Celebi encounter. It is an unreachable target for a bot playing the game as intended. |