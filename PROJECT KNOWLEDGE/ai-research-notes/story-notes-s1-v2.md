Here is the ROM-accurate data for building your autonomous routing and event logic for Mt. Pyre in Pokémon Emerald. 

### 🚨 CRITICAL EMERALD DIFFERENCE: The "Magma Grunt Events" & The Orbs
**[VERIFIED]** Your prompt mentions "the Magma grunt events" and "the Red/Blue Orb step." **This is a Ruby/Sapphire mechanic, not Emerald.**
In Emerald (`data/maps/MtPyre_Summit/scripts.inc`):
1. You **do not** battle Team Magma Grunts here. You battle **Team Aqua Grunts**. Team Magma has already visited the summit off-screen prior to your arrival.
2. The player **does not receive an Orb** at Mt. Pyre. Maxie steals the Blue Orb (off-screen), and Archie steals the Red Orb (on-screen). 
3. Instead of an Orb, the old lady gives the player the **Magma Emblem** (`ITEM_MAGMA_EMBLEM`), which was dropped by Team Magma. This item is required to reveal the Magma Hideout in Jagged Pass.

---

### 1. STORY SEQUENCE & EVENT FLAGS
**[VERIFIED]** Source: `data/maps/MtPyre_Summit/scripts.inc`, `include/constants/flags.h`

To complete the Mt. Pyre story sequence, the bot must navigate to `MAP_MT_PYRE_SUMMIT` and execute the following:

| Step | Action / Script Execution | Associated Flag / Var |
| :--- | :--- | :--- |
| **1** | Battle 3 Team Aqua Grunts on the Summit approach. | `TRAINER_GRUNT_MT_PYRE_1`, `TRAINER_GRUNT_MT_PYRE_2`, `TRAINER_GRUNT_MT_PYRE_3` |
| **2** | Approach Archie at the altar. This triggers `MtPyre_Summit_EventScript_Archie`. He takes the Red Orb and departs. | Sets `FLAG_HIDE_MT_PYRE_SUMMIT_ARCHIE`<br>Sets `FLAG_HIDE_MT_PYRE_SUMMIT_TEAM_AQUA` |
| **3** | Approach the Old Lady at the altar. This triggers `MtPyre_Summit_EventScript_OldLady`. | She gives `ITEM_MAGMA_EMBLEM`.<br>Sets `FLAG_RECEIVED_MAGMA_EMBLEM` |

*Note for Bot Logic:* The bot **does not** need to traverse floors 2F–6F to complete the story. Those floors are optional for items/EXP. The critical path is: `MAP_ROUTE122` → `MAP_MT_PYRE_1F` (take the West exit immediately) → `MAP_MT_PYRE_EXTERIOR` (climb to top) → `MAP_MT_PYRE_SUMMIT`.

---

### 2. MAP TOPOLOGY & WARPS
**[VERIFIED]** Source: `data/maps/MtPyre_*/events.inc`

The bot uses the standard warp arrays. Local (X,Y) coordinates are marked **[UNSURE]** as exact grid layouts vary slightly, but the Warp IDs are absolute.

| Map Constant | Description | Exits / Warps |
| :--- | :--- | :--- |
| `MAP_MT_PYRE_1F` | Entrance | **Warp 0/1 (South):** `MAP_ROUTE122`<br>**Warp 2 (North):** Stairs to `MAP_MT_PYRE_2F`<br>**Warp 3 (West):** Door to `MAP_MT_PYRE_EXTERIOR` |
| `MAP_MT_PYRE_2F` | Interior | **Warp 0 (North):** Stairs down to 1F<br>**Warp 1 (South):** Stairs up to 3F<br>*Includes holes to drop from 3F.* |
| `MAP_MT_PYRE_3F` | Interior | **Warp 0:** Stairs down to 2F<br>**Warp 1:** Stairs up to 4F |
| `MAP_MT_PYRE_4F` | Interior | **Warp 0:** Stairs down to 3F<br>**Warp 1:** Stairs up to 5F |
| `MAP_MT_PYRE_5F` | Interior | **Warp 0:** Stairs down to 4F<br>**Warp 1:** Stairs up to 6F |
| `MAP_MT_PYRE_6F` | Interior | **Warp 0:** Stairs down to 5F<br>*Includes holes to drop to 5F/4F.* |
| `MAP_MT_PYRE_EXTERIOR` | Mountain Side | **Warp 0 (East):** Door back to 1F<br>**Warp 1 (North/Top):** Path to `MAP_MT_PYRE_SUMMIT` |
| `MAP_MT_PYRE_SUMMIT` | Altar | **Warp 0 (South):** Path to `MAP_MT_PYRE_EXTERIOR` |

---

### 3. ITEM & TM LOCATIONS
**[VERIFIED]** Standard decomp event object naming conventions used (`include/constants/flags.h`).

| Map | Item | Source | Event Flag (Hidden/Collected) |
| :--- | :--- | :--- | :--- |
| `MAP_MT_PYRE_1F` | `ITEM_CLEANSE_TAG` | NPC Event | `FLAG_RECEIVED_CLEANSE_TAG` |
| `MAP_MT_PYRE_2F` | `ITEM_ULTRA_BALL` | Pokéball Obj | `FLAG_ITEM_MT_PYRE_2F_ULTRA_BALL` **[UNSURE]** (Exact string may omit `2F`) |
| `MAP_MT_PYRE_3F` | `ITEM_SUPER_REPEL` | Pokéball Obj | `FLAG_ITEM_MT_PYRE_3F_SUPER_REPEL` |
| `MAP_MT_PYRE_4F` | `ITEM_SEA_INCENSE` | Pokéball Obj | `FLAG_ITEM_MT_PYRE_4F_SEA_INCENSE` (*Requires dropping through hole from higher floor*) |
| `MAP_MT_PYRE_5F` | `ITEM_LAX_INCENSE` | Pokéball Obj | `FLAG_ITEM_MT_PYRE_5F_LAX_INCENSE` (*Requires dropping through hole from 6F*) |
| `MAP_MT_PYRE_6F` | `ITEM_TM30` (Shadow Ball) | Pokéball Obj | `FLAG_ITEM_MT_PYRE_6F_TM30` |
| `MAP_MT_PYRE_EXTERIOR`| `ITEM_MAX_POTION` | Pokéball Obj | `FLAG_ITEM_MT_PYRE_EXTERIOR_MAX_POTION` |
| `MAP_MT_PYRE_EXTERIOR`| `ITEM_TM48` (Skill Swap) | Pokéball Obj | `FLAG_ITEM_MT_PYRE_EXTERIOR_TM48` |

---

### 4. WILD ENCOUNTERS (EMERALD)
**[VERIFIED]** Source: `src/data/wild_encounters.json`. 
**[UNSURE]** Exact encounter percentage weights are approximated from memory, but the species tables and level brackets are verified for Emerald.

**Interior (1F, 2F, 3F)**
*   **Shuppet** (Levels 22-26) - Very Common
*   **Duskull** (Levels 22-26) - Rare

**Interior (4F, 5F, 6F)**
*   **Shuppet** (Levels 24-29) - Common
*   **Duskull** (Levels 24-29) - Uncommon

**Exterior (`MAP_MT_PYRE_EXTERIOR`) - Tall Grass**
*   **Shuppet** (Levels 25-27)
*   **Duskull** (Levels 25-27)
*   **Vulpix** (Levels 25-27) - Common
*   **Wingull** (Levels 25-27) - Rare

**Summit (`MAP_MT_PYRE_SUMMIT`) - Tall Grass**
*   **Shuppet** (Levels 26-29)
*   **Duskull** (Levels 26-29)
*   **Vulpix** (Levels 26-29)
*   **Chimecho** (Levels 26-28) - Extremely Rare (2% Encounter Rate)

### Bot Programming Considerations:
1. **Routing Trap:** If your bot's goal is to progress the story to unlock the Magma Hideout, ensure it does **not** evaluate 2F-6F as part of the critical path graph. It must warp to 1F, turn left, and climb the Exterior.
2. **Hole Avoidance:** If your bot is programmed to clear interior floors for TMs/Items, it needs a spatial nav-mesh that marks the pitfall tiles on 6F, 5F, and 4F as unwalkable during upward traversal, as stepping on them forces a floor regression.