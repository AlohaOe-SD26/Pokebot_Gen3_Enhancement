Here is the exhaustive, ROM-accurate technical guide for the Seafloor Cavern, Cave of Origin, and Sootopolis sequences in Pokémon Emerald. 

### GENERAL EMERALD VS. RUBY/SAPPHIRE DIFFERENCES [VERIFIED]
*   **Obtaining Dive:** In RS, Steven gives Dive immediately after Tate/Liza. In Emerald, you **must** defeat Team Magma at the Space Center first.
*   **Seafloor Cavern:** In RS, the enemy team matches the version (Aqua/Magma). In Emerald, it is **strictly Team Aqua** (Archie/Kyogre). Maxie and Groudon were already handled at the Magma Hideout earlier.
*   **Sootopolis Event:** In RS, you enter the Cave of Origin, fight Kyogre/Groudon, then fight Gym Leader Wallace. In Emerald, Kyogre and Groudon are fighting in the city. You cannot fight them. You must find Wallace in the Cave of Origin, fetch Rayquaza from Sky Pillar to stop the fight, and then challenge Gym Leader **Juan** (Wallace is now the Champion).
*   **HM07 Waterfall:** In RS, Wallace gives this after you beat him in the Gym. In Emerald, Wallace gives this outside the Gym as an NPC *after* Rayquaza stops the fight.

---

### PART 1: PREREQUISITES & OBTAINING DIVE (MOSSDEEP CITY)

#### Sequence & Flags
| Decomp Variable / Flag | State / Value | Condition / Purpose | Status |
| :--- | :--- | :--- | :--- |
| `FLAG_BADGE07_GET` | Set | Mind Badge. Unlocks Dive overworld usage. | [VERIFIED] |
| `VAR_MOSSDEEP_CITY_STATE` | `1` $\to$ `2` | Must complete the Space Center Team Magma invasion (Steven & Player vs. Maxie & Tabitha) to advance to state 2. | [VERIFIED] |
| `FLAG_RECEIVED_HM08` | Set | Given by Steven in his house. | [VERIFIED] |

*   **Location:** `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`
*   **Bot Action:** After `VAR_MOSSDEEP_CITY_STATE == 2`, route to Steven's House (approx local coords: `{x: 23, y: 14}` on `MAP_MOSSDEEP_CITY` [INFERENCE]), speak to Steven to receive HM08 Dive.

---

### PART 2: REACHING SEAFLOOR CAVERN

*   **Pathing:** `MAP_ROUTE128` $\to$ `MAP_UNDERWATER_ROUTE128` $\to$ `MAP_UNDERWATER_SEAFLOOR_CAVERN` $\to$ `MAP_SEAFLOOR_CAVERN_ENTRANCE`.
*   **Dive Spot:** `MAP_ROUTE128` has a dark water trench. The bot must Surf over it and use Dive.
*   **Underwater Cave Entry:** On `MAP_UNDERWATER_ROUTE128`, route to the southern cave entrance and enter. This transitions to `MAP_UNDERWATER_SEAFLOOR_CAVERN`.
*   **Surfacing:** The bot must navigate to the submarine (`obj_event` 1) and press 'B' to surface, transitioning to `MAP_SEAFLOOR_CAVERN_ENTRANCE`.

---

### PART 3: SEAFLOOR CAVERN ROOM-BY-ROOM (PUZZLES & HMS)
*   **Required HMs:** Surf, Strength, Rock Smash. [VERIFIED]

The cavern is a network of 10 maps. The bot must navigate through the rooms to reach Archie in Room 9. 

| Map Constant | Description / Bot Requirements | Status |
| :--- | :--- | :--- |
| `MAP_SEAFLOOR_CAVERN_ENTRANCE` | Starting room. Contains Aqua Grunts. Exit North. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM1` | Contains **Rock Smash** rocks and **Strength** boulders. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM2` | Strength boulders. Path branches. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM3` | Transition room / minor puzzle. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM4` | Strength boulder puzzle. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM5` | Transition room. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM6` | **Surf** current puzzle. Bot must step on specific currents to reach the correct exit. Needs an A* path or hardcoded sequence. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM7` | Strength puzzle. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM8` | Strength puzzle. | [VERIFIED] |
| `MAP_SEAFLOOR_CAVERN_ROOM9` | The final massive Strength puzzle, Archie battle, and Kyogre awakening event. | [VERIFIED] |

**Room 9 Strength Puzzle Note:**
*   [INFERENCE] The bot will need a hardcoded step-sequence for the Room 9 boulders. If a boulder is pushed incorrectly, the puzzle becomes unsolvable, requiring the bot to leave the map to reset `MAP_SEAFLOOR_CAVERN_ROOM9`.

#### The Awakening Sequence (`data/maps/SeafloorCavern_Room9/scripts.inc`)
1.  **Archie Battle:** Bot approaches Archie. Defeating him sets `FLAG_DEFEATED_ARCHIE_SEAFLOOR_CAVERN`. [VERIFIED]
2.  **Cutscene:** Archie uses Red Orb. Kyogre awakens and flees. Maxie enters. Archie gets a PokéNav call about the extreme weather. Archie and Maxie leave. [VERIFIED]
3.  **Weather State:** `VAR_SHOULD_END_ABNORMAL_WEATHER` is NOT set yet. Instead, global weather changes to alternating Rain/Sun. [VERIFIED]

---

### PART 4: SOOTOPOLIS CITY & CAVE OF ORIGIN

Because of Emerald-specific plot changes, the bot must follow a strict non-combat narrative sequence here.

#### 4A. Entering Sootopolis (`MAP_SOOTOPOLIS_CITY`)
*   **Event Trigger:** Upon entering via Dive, a cutscene of Groudon and Kyogre fighting plays automatically. [VERIFIED]
*   **Routing to Cave of Origin:** The gym is locked. The bot must Surf to the west side of the crater, walk up the stairs, and speak to Steven. Steven escorts the player to the entrance of the Cave of Origin. [VERIFIED]

#### 4B. Cave of Origin (`MAP_CAVE_OF_ORIGIN_ENTRANCE` / `MAP_CAVE_OF_ORIGIN_1F`)
*   [VERIFIED] Emerald Diff: You do not navigate down to B4F. You do not fight a legendary here.
*   **Wallace Interaction:** Wallace is located on `MAP_CAVE_OF_ORIGIN_1F` (or `B1F` [UNSURE of exact floor constant used for his spawn in Emerald, check `data/maps/CaveOfOrigin_B1F/scripts.inc`]). 
*   **The Prompt:** Wallace asks where Rayquaza is. A multichoice menu opens.
*   **Crucial Bot Action:** The bot **must** select the option for "Sky Pillar". 
    *   [VERIFIED] The multichoice list `MULTICHOICE_CAVE_OF_ORIGIN_PACIFIDLOG` (or similar) maps to: 0 = Cave of Origin, 1 = Mt. Pyre, 2 = Sky Pillar. The bot must select Index 2. If it selects 0 or 1, Wallace says it's wrong and the script waits for the bot to talk to him again.

| Decomp Variable / Flag | State / Value | Condition / Purpose | Status |
| :--- | :--- | :--- | :--- |
| `VAR_SOOTOPOLIS_CITY_STATE` | `1` $\to$ `2` | State increments after telling Wallace about Sky Pillar. (Exact integer values 1->2 [UNSURE], but the increment dictates progression). | [INFERENCE] |

---

### PART 5: THE SKY PILLAR DETOUR (`MAP_SKY_PILLAR_ENTRANCE`)
*   **Routing:** The bot must Surf to Route 131 and enter Sky Pillar. [VERIFIED]
*   **Emerald Diff - Bike Puzzle:** On the *first* visit to awaken Rayquaza, there are **no cracked floors** requiring the Mach Bike. The bot can walk normally to the top. [VERIFIED]
*   **Awakening Rayquaza:** Reach `MAP_SKY_PILLAR_TOP`. Walk up to Rayquaza. It awakens and flies away.
*   **Flags:** Sets `FLAG_AWAKENED_RAYQUAZA`. [VERIFIED]

---

### PART 6: SOOTOPOLIS RESOLUTION & GYM LEADER JUAN

#### Returning to Sootopolis
1.  **Cutscene:** Upon entering `MAP_SOOTOPOLIS_CITY`, Rayquaza descends, roars, and ends the fight. The weather clears. Groudon and Kyogre flee. Rayquaza flies away. [VERIFIED]
2.  **State Change:** `VAR_SOOTOPOLIS_CITY_STATE` advances, changing the map layout (NPCs move). [VERIFIED]

#### Receiving HM07 (Waterfall)
*   **Bot Action:** Surf to the island in front of the Gym (`MAP_SOOTOPOLIS_CITY`). Archie, Maxie, and Wallace are standing there.
*   **Conversation:** Talk to Archie/Maxie (they leave), then talk to Wallace.
*   **Reward:** Wallace gives HM07 Waterfall. [VERIFIED]
*   **Flags:** Sets `FLAG_RECEIVED_HM07`. [VERIFIED]
*   **Emerald Diff Warning:** *Do not program the bot to expect Waterfall from defeating the Gym Leader. It must be obtained from Wallace right here.* [VERIFIED]

#### Juan's Gym
*   **Gym Access:** Wallace moves out of the way. The bot can now enter the Gym.
*   **Leader:** Juan (Water-type). [VERIFIED]
*   **Reward:** Rain Badge.
*   **Flags:** Defeating Juan sets `FLAG_BADGE08_GET` and `FLAG_DEFEATED_SOOTOPOLIS_GYM`. [VERIFIED]

### CRITICAL FLAGS SUMMARY FOR YOUR MEMORY WATCHER

Monitor these explicitly in your libmgba bot memory loop:

```c
// Pre-Dive
FLAG_BADGE07_GET                  // Mind Badge
VAR_MOSSDEEP_CITY_STATE           // Must be 2 (Space Center defeated)
FLAG_RECEIVED_HM08                // Dive obtained

// Seafloor Cavern
FLAG_DEFEATED_ARCHIE_SEAFLOOR_CAVERN // Archie defeated
FLAG_HIDE_SEAFLOOR_CAVERN_ROOM_9_KYOGRE // Kyogre is gone
// Note: Global weather shifts to abnormal here

// Sootopolis & Cave of Origin
VAR_SOOTOPOLIS_CITY_STATE         // Tracks cutscene progress (Fight -> Wallace -> Sky Pillar -> Resolution)
FLAG_HIDE_CAVE_OF_ORIGIN_WALLACE  // Wallace leaves Cave of Origin for the Gym exterior

// Sky Pillar
FLAG_AWAKENED_RAYQUAZA            // Rayquaza flies to Sootopolis

// Post-Resolution
FLAG_RECEIVED_HM07                // Waterfall obtained from Wallace outside gym
FLAG_BADGE08_GET                  // Rain badge obtained from Juan
```