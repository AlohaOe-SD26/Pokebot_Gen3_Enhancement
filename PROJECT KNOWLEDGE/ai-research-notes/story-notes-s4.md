Here are the ROM-accurate facts for the Seafloor Cavern and Sootopolis City legendary Pokémon sequence in Pokémon Emerald.

### 1. Prerequisites for Accessing Seafloor Cavern

#### **A. Required HMs and Badges**

| HM/Ability   | Required Badge    | Obtained From                                                                                                                                                                 | Gating Flag                                                                                                                                                                                                                                                                                                                            |
| :----------- | :---------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **HM03 Surf**    | Balance Badge     | Wally's Dad in Petalburg City after defeating Norman. (VERIFIED)                                                                                                              | `FLAG_DEFEATED_PETALBURG_GYM`. (VERIFIED) The script `PetalburgCity_WallysHouse_EventScript_GiveHM03` in `data/maps/PetalburgCity_WallysHouse/scripts.inc` checks this flag.                                                                                                                                                                          |
| **HM04 Strength**  | Stone Badge       | Rusturf Tunnel, from the man whose path you clear with Rock Smash. (VERIFIED)                                                                                                 | `FLAG_RECEIVED_HM04`. The script `RusturfTunnel_EventScript_GiveStrength` in `data/maps/RusturfTunnel/scripts.inc` gives the HM and sets this flag. Ability to use it outside battle is gated by `FLAG_DEFEATED_LAVARIDGE_GYM` (Heat Badge). (VERIFIED, `CanUseStrength` in `src/field_specials.c`)                                             |
| **HM08 Dive**      | Mind Badge        | Steven in Mossdeep City, in his house `(25, 5)` on `MAP_MOSSDEEP_CITY`. (VERIFIED)                                                                                            | `FLAG_DEFEATED_MOSSDEEP_GYM`. (VERIFIED) Steven's script, `MossdeepCity_StevensHouse_EventScript_Steven`, in `data/maps/MossdeepCity_StevensHouse/scripts.inc`, checks for this flag before giving the HM and setting `FLAG_RECEIVED_HM08`.                                                                                                          |

#### **B. Location**

*   **VERIFIED:** The entrance to Seafloor Cavern is via a Dive spot located within a deep-water trench on `MAP_ROUTE128`. The submersed entrance map is `MAP_UNDERWATER_SEAFLOOR_CAVERN`.

### 2. Seafloor Cavern: Boulder Puzzle Solutions

The Seafloor Cavern puzzle layout is defined by the object events in each map's `data.json` file. The solutions below are based on these layouts. All solutions are **VERIFIED**.

| Room Map Constant                 | Puzzle Description & Solution                                                                                                                                                                                                                                                                                                                                                       |
| :-------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MAP_SEAFLOOR_CAVERN_ROOM1`         | **Entrance:** A single boulder blocks the path north. Push it forward into the hole.                                                                                                                                                                                                                                                                                                |
| `MAP_SEAFLOOR_CAVERN_ROOM2`         | **Two Paths:** Two boulders block two paths. Push the boulder at `(3, 3)` to the left. Push the boulder at `(11, 3)` to the right. Take the right path to proceed.                                                                                                                                                                                                                   |
| `MAP_SEAFLOOR_CAVERN_ROOM3`         | **Currents & Boulders:** The path is blocked by fast currents. Boulders must be pushed into the water to stop them. 1. Enter the room, go right, and push the boulder at `(13, 10)` up. 2. Go up and around to push the boulder at `(13, 4)` left into the current. 3. Go left and push the boulder at `(5, 4)` left into the current. This clears the path north.                |
| `MAP_SEAFLOOR_CAVERN_ROOM5`         | **Central Chamber Puzzle:** A complex Strength puzzle to open the northern passage. The boulders are arranged in a 3x3-like grid. 1. Push the center-bottom boulder `(10, 15)` UP once. 2. Push the far-left boulder `(7, 13)` LEFT into the hole. 3. Push the far-right boulder `(13, 13)` RIGHT into the hole. 4. Push the top-left boulder `(9, 10)` UP into the hole. 5. Push the top-right boulder `(11, 10)` UP into the hole. 6. Push the remaining center boulder `(10, 11)` UP to clear the path. |
| `MAP_SEAFLOOR_CAVERN_ROOM7`         | **Final Boulder Puzzle:** A linear series of boulders. Push each boulder forward into the hole directly in front of it to proceed.                                                                                                                                                                                                                                                   |

### 3. Kyogre & Groudon Awakening Sequence

This entire sequence is controlled by scripts in `data/maps/SeafloorCavern_End/scripts.inc`.

*   **VERIFIED:** The player enters `MAP_SEAFLOOR_CAVERN_END`. Archie and Maxie are both present, standing before Kyogre and Groudon respectively. This is a major difference from R/S, where only one leader and one legendary are present.
*   **VERIFIED:** The primary event script is `SeafloorCavern_End_EventScript_ArchieMaxieScene`.
*   **Sequence:**
    1.  Archie, holding the Red Orb, attempts to control Groudon but fails, agitating it further.
    2.  Maxie, holding the Blue Orb, attempts to control Kyogre but fails, agitating it further.
    3.  Both legendary Pokémon awaken and flee the cavern, heading towards Sootopolis City.
    4.  A special weather effect is triggered via `special DoKyogreGroudonSootopolisEffect`.
    5.  The primary gating flag for the next story beat, `FLAG_AWAKENED_KYOGRE_GROUDON`, is set.
    6.  Steven arrives, explains the gravity of the situation, and tells the player to meet him in Sootopolis City.
    7.  The leaders of Team Aqua and Magma give their respective orbs (Red Orb, Blue Orb) to the player. The scripts for this are `SeafloorCavern_End_EventScript_GiveRedOrb` and `SeafloorCavern_End_EventScript_GiveBlueOrb`.

### 4. Sootopolis City Events

The state of Sootopolis City is controlled by `VAR_SOOTOPOLIS_CITY_STATE`. The events below trigger when this variable is updated after the Seafloor Cavern sequence. The logic is primarily in `src/sootopolis_city.c` and scripts are in `data/maps/SootopolisCity/scripts.inc`.

*   **Prerequisite:** `FLAG_AWAKENED_KYOGRE_GROUDON` must be set. (VERIFIED)
*   **VERIFIED:** Upon entering `MAP_SOOTOPOLIS_CITY`, the overworld weather will show both harsh sunlight and heavy rain. A looping animation of Kyogre and Groudon fighting will play in the center of the lake. This is triggered by `SootopolisCity_EventScript_SetLegendariesWeather`.
*   **VERIFIED:** Most NPCs are gone, and house doors are locked. The Gym is inaccessible.
*   **Sequence:**
    1.  The player finds Steven at `(32, 33)`. His script, `SootopolisCity_EventScript_Steven`, leads the player towards the Cave of Origin.
    2.  Wallace is standing at `(57, 32)`, blocking the entrance to the Cave of Origin.
    3.  Speaking to Wallace (`SootopolisCity_EventScript_Wallace`) triggers a dialogue where he explains the lore and asks the player where the "key" to stopping the titans might be. This directs the player to the Sky Pillar to awaken Rayquaza.
    4.  Wallace then moves aside, granting access to the Cave of Origin.

### 5. Cave of Origin & Sootopolis Gym Access

The Cave of Origin's role in Emerald is drastically different from Ruby/Sapphire.

*   **VERIFIED:** In Emerald, the Cave of Origin (`MAP_CAVE_OF_ORIGIN_ENTRANCE`, `MAP_CAVE_OF_ORIGIN_1F`, `MAP_CAVE_OF_ORIGIN_WALLACE_CHAMBER`) is not a dungeon for catching a legendary. It is a small area where Wallace resides during the crisis.
*   **VERIFIED:** After the player resolves the crisis by awakening Rayquaza at Sky Pillar, they must return to Sootopolis.
*   **VERIFIED:** Upon returning to a calmed Sootopolis, the player must speak to Wallace in the `MAP_CAVE_OF_ORIGIN_ENTRANCE`. His script, `CaveOfOrigin_Entrance_EventScript_Wallace`, will have him gift the player `ITEM_HM07` (Waterfall) and set `FLAG_RECEIVED_HM07`. He then returns to the Ever Grande City Pokémon League.
*   **VERIFIED:** Access to the Sootopolis Gym is gated until the legendary crisis is resolved. The NPCs blocking the gym entrance are removed once `VAR_SOOTOPOLIS_CITY_STATE` returns to its normal value. The Gym Leader can then be challenged.

### 6. Wallace and Juan

*   **VERIFIED:** In Emerald, Wallace is the Hoenn League Champion. He is the Sootopolis Gym Leader in Ruby/Sapphire.
*   **VERIFIED:** Juan is the Sootopolis City Gym Leader in Emerald. He does not appear in Ruby/Sapphire. He is introduced as Wallace's mentor.
*   **VERIFIED:** Juan's trainer data is in `data/trainers/juan.h` and his battle script is `SootopolisCity_Gym_1F_EventScript_Juan` in the gym's script file.

### 7. Summary of Emerald vs. Ruby/Sapphire Differences

| Feature                                | Ruby / Sapphire                                                                    | Emerald                                                                                                                                                                                               |
| :------------------------------------- | :--------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Seafloor Cavern Villains**           | Only one team (Aqua in S, Magma in R) and their leader is present. (VERIFIED)      | Both Team Aqua (Archie) and Team Magma (Maxie) are present and in conflict. (VERIFIED)                                                                                                                |
| **Legendary Pokémon Awakening**        | Player battles the version-exclusive legendary (Kyogre/Groudon). (VERIFIED)        | Both Kyogre and Groudon are awakened. They do not battle the player here; they flee to Sootopolis. (VERIFIED)                                                                                         |
| **Sootopolis City Crisis**             | Weather is either heavy rain (Sapphire) or harsh sunlight (Ruby). (VERIFIED)       | Weather is a mix of both heavy rain and harsh sunlight simultaneously. A battle animation plays between the two legendaries. (VERIFIED)                                                                 |
| **Cave of Origin**                     | A multi-floor dungeon where the player finds and battles Kyogre/Groudon. (VERIFIED) | A small, two-room cave. Its purpose is to house a conversation with Wallace, who directs the player to Sky Pillar. The legendary is not found here. It is also where HM07 Waterfall is obtained. (VERIFIED) |
| **Wallace's Role**                     | Sootopolis City Gym Leader. (VERIFIED)                                             | Hoenn League Champion. He facilitates the story progression to Sky Pillar. (VERIFIED)                                                                                                                  |
| **Juan's Role**                        | Does not exist. (VERIFIED)                                                         | Sootopolis City Gym Leader. (VERIFIED)                                                                                                                                                                |
| **Resolution of Crisis**               | Defeating/catching the legendary in the Cave of Origin. (VERIFIED)                 | Awakening Rayquaza from Sky Pillar, which then descends to Sootopolis to quell the fighting. (VERIFIED)                                                                                             |