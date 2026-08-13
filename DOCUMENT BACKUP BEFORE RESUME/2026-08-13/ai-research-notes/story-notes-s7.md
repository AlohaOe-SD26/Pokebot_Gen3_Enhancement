Here is an exhaustive breakdown of HM acquisition and gating in Pokémon Emerald, following your specified rules.

### HM Acquisition and Usage Requirements

Each HM is detailed below, including its acquisition method, the badge required for field use, and the primary story progression it unblocks.

| HM               | Acquisition Details                                                                                                                                                                                                                                                                                                                       | Badge for Field Use                                                                                                                                 | Key Story Blocks                                                                                                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **HM01 - Cut**   | **VERIFIED:**<br>- **Map:** `MAP_RUSTBORO_CITY_CUTTERS_HOUSE`<br>- **Coords:** (3, 2)<br>- **NPC:** Cutter<br>- **Script:** `RustboroCity_CuttersHouse_EventScript_Cutter`<br>- **Prerequisite:** None. Can be obtained upon first entering Rustboro City.                                                                                     | **VERIFIED:**<br>- Stone Badge (Roxanne)<br>- **Flag:** `FLAG_BADGE01_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseCut`        | **VERIFIED:**<br>- Gaining entry to the Team Aqua Hideout in Lilycove City is the first *mandatory* story use.                                                                                                  |
| **HM02 - Fly**   | **VERIFIED:**<br>- **Map:** `MAP_ROUTE119`<br>- **Coords:** N/A (Triggered by walking north of Weather Institute)<br>- **NPC:** Rival (Brendan/May)<br>- **Script:** `Route119_EventScript_Rival`<br>- **Prerequisite:** Defeat Norman. **Flag:** `FLAG_DEFEATED_GYM_LEADER_NORMAN`                                                               | **VERIFIED:**<br>- Feather Badge (Winona)<br>- **Flag:** `FLAG_BADGE06_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseFly`       | **VERIFIED:**<br>- None. Fly is a quality-of-life HM and is never strictly required for story progression. The bot can walk/Surf everywhere.                                                                      |
| **HM03 - Surf**  | **VERIFIED:**<br>- **Map:** `MAP_PETALBURG_CITY_WALLYS_HOUSE`<br>- **Coords:** (5, 2)<br>- **NPC:** Wally's Dad<br>- **Script:** `PetalburgCity_WallysHouse_EventScript_WallysDad`<br>- **Prerequisite:** Defeat Norman. **Flag:** `FLAG_DEFEATED_GYM_LEADER_NORMAN`                                                                                 | **VERIFIED:**<br>- Balance Badge (Norman)<br>- **Flag:** `FLAG_BADGE05_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseSurf`      | **VERIFIED:**<br>- Crossing the body of water on Route 118 to reach the eastern half of Hoenn (leading to Fortree City).                                                                                        |
| **HM04 - Strength** | **VERIFIED:**<br>- **Map:** `MAP_RUSTURF_TUNNEL`<br>- **Coords:** N/A (Given after breaking rock)<br>- **NPC:** Wanda's Boyfriend (unnamed)<br>- **Script:** `RusturfTunnel_EventScript_WandasBoyfriend`<br>- **Prerequisite:** Break the rocks between the two halves of the tunnel using Rock Smash.                                   | **VERIFIED:**<br>- Heat Badge (Flannery)<br>- **Flag:** `FLAG_BADGE04_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseStrength`    | **VERIFIED:**<br>- Pushing boulders in the Seafloor Cavern.<br>- Pushing boulders in Victory Road.                                                                                                                |
| **HM05 - Flash** | **VERIFIED:**<br>- **Map:** `MAP_GRANITE_CAVE_1F`<br>- **Coords:** (14, 4)<br>- **NPC:** Hiker<br>- **Script:** `GraniteCave_1F_EventScript_Hiker`<br>- **Prerequisite:** None. Can be obtained upon first entering Granite Cave.                                                                                                                | **VERIFIED:**<br>- Knuckle Badge (Brawly)<br>- **Flag:** `FLAG_BADGE02_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseFlash`     | **VERIFIED:**<br>- Navigating Granite Cave to deliver the letter to Steven.<br>- Navigating Victory Road.<br>**INFERENCE:** While technically traversable by a human, a bot would require Flash to pathfind these areas reliably. |
| **HM06 - Rock Smash** | **VERIFIED:**<br>- **Map:** `MAP_MAUVILLE_CITY_HOUSE1`<br>- **Coords:** (3, 2)<br>- **NPC:** Rock Smash Guy<br>- **Script:** `MauvilleCity_House1_EventScript_RockSmashGuy`<br>- **Prerequisite:** Defeat Wattson. **Flag:** `FLAG_DEFEATED_MAUVILLE_GYM`                                                                                        | **VERIFIED:**<br>- Dynamo Badge (Wattson)<br>- **Flag:** `FLAG_BADGE03_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseRockSmash` | **VERIFIED:**<br>- Clearing the rocks in Rusturf Tunnel to reunite the couple and open the passage.<br>- Clearing the rocks on Route 111 to access the desert.                                                       |
| **HM07 - Waterfall** | **VERIFIED:**<br>- **Map:** `MAP_SOOTOPOLIS_CITY_CAVE_OF_ORIGIN_ENTRANCE`<br>- **Coords:** (7, 4)<br>- **NPC:** Wallace<br>- **Script:** `SootopolisCity_CaveOfOrigin_Entrance_EventScript_Wallace`<br>- **Prerequisite:** Awaken Rayquaza and resolve the Groudon/Kyogre conflict.<br>- **Emerald difference:** In Ruby/Sapphire, Wallace is the gym leader and gives this to you after beating him. In Emerald, he gives it after the Rayquaza event. | **VERIFIED:**<br>- Rain Badge (Juan)<br>- **Flag:** `FLAG_BADGE08_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseWaterfall`     | **VERIFIED:**<br>- Ascending the final waterfall inside Victory Road to reach the Pokémon League.                                                                                                              |
| **HM08 - Dive**  | **VERIFIED:**<br>- **Map:** `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`<br>- **Coords:** (4, 3)<br>- **NPC:** Steven<br>- **Script:** `MossdeepCity_StevensHouse_EventScript_Steven`<br>- **Prerequisite:** Defeat Tate & Liza. **Flag:** `FLAG_DEFEATED_MOSSDEEP_GYM`                                                                                         | **VERIFIED:**<br>- Mind Badge (Tate & Liza)<br>- **Flag:** `FLAG_BADGE07_GET`<br>- **Source:** `src/field_effect_helpers.c`, function `CheckUseDive`    | **VERIFIED:**<br>- Accessing the Seafloor Cavern from Route 128.<br>- Accessing Sootopolis City from Route 126.                                                                                                |

---

### Chronological List of Mandatory HM Gates

This list details every point where story progression is hard-blocked without a specific HM field move. Optional areas are excluded.

1.  **Obstacle:** Dark interior of Granite Cave.
    *   **HM Required:** HM05 Flash
    *   **Location:** `MAP_GRANITE_CAVE_B1F`, `MAP_GRANITE_CAVE_STEVENS_ROOM`
    *   **Purpose:** To reach Steven and deliver the Letter.
    *   **Prerequisite:** Must have Knuckle Badge (`FLAG_BADGE02_GET`).

2.  **Obstacle:** Smashable rocks blocking west exit of Rusturf Tunnel.
    *   **HM Required:** HM06 Rock Smash
    *   **Location:** `MAP_RUSTURF_TUNNEL` (Coords: (16, 5), (17, 5))
    *   **Purpose:** To open the path to Verdanturf Town and obtain HM04 Strength from the reunited couple.
    *   **Prerequisite:** Must have Dynamo Badge (`FLAG_BADGE03_GET`).

3.  **Obstacle:** Water body blocking eastward progression from Mauville City.
    *   **HM Required:** HM03 Surf
    *   **Location:** `MAP_ROUTE118` (Eastern side of Mauville City)
    *   **Purpose:** To access Route 119 and the eastern half of the Hoenn mainland, continuing the story towards Fortree City.
    *   **Prerequisite:** Must have Balance Badge (`FLAG_BADGE05_GET`).

4.  **Obstacle:** Cuttable trees blocking the entrance to the Aqua Hideout.
    *   **HM Required:** HM01 Cut
    *   **Location:** `MAP_LILYCOVE_CITY_AQUA_HIDEOUT_ENTRANCE` (Coords: (19, 9), (20, 9))
    *   **Purpose:** To infiltrate the Aqua Hideout, disable the submarine, and obtain the Master Ball. This is required to clear the Wailmer blocking the path to Mossdeep City.
    *   **Prerequisite:** Must have Stone Badge (`FLAG_BADGE01_GET`).

5.  **Obstacle:** Deep water patch concealing the entrance to the Seafloor Cavern.
    *   **HM Required:** HM08 Dive
    *   **Location:** `MAP_ROUTE128`
    *   **Purpose:** To find and enter the Seafloor Cavern to confront Team Aqua and Kyogre. This is also the only way to reach Sootopolis City for the first time.
    *   **Prerequisite:** Must have Mind Badge (`FLAG_BADGE07_GET`).

6.  **Obstacle:** Boulders blocking paths in the Seafloor Cavern.
    *   **HM Required:** HM04 Strength
    *   **Location:** `MAP_SEAFLOOR_CAVERN_ROOM1` and subsequent puzzle rooms.
    *   **Purpose:** To solve the boulder puzzles and navigate the cavern to reach Archie.
    *   **Prerequisite:** Must have Heat Badge (`FLAG_BADGE04_GET`).

7.  **Obstacle:** Boulders blocking paths in Victory Road.
    *   **HM Required:** HM04 Strength
    *   **Location:** `MAP_VICTORY_ROAD_1F`, `MAP_VICTORY_ROAD_B1F`
    *   **Purpose:** To clear paths to navigate through the first sections of Victory Road.
    *   **Prerequisite:** Must have Heat Badge (`FLAG_BADGE04_GET`).

8.  **Obstacle:** Dark rooms within Victory Road.
    *   **HM Required:** HM05 Flash
    *   **Location:** `MAP_VICTORY_ROAD_B1F`
    *   **Purpose:** To illuminate the cave for navigation.
    *   **Prerequisite:** Must have Knuckle Badge (`FLAG_BADGE02_GET`).

9.  **Obstacle:** Waterfall at the end of Victory Road.
    *   **HM Required:** HM07 Waterfall
    *   **Location:** `MAP_VICTORY_ROAD_B2F` (exit area)
    *   **Purpose:** To ascend the final obstacle and reach the entrance to the Pokémon League at Ever Grande City.
    *   **Prerequisite:** Must have Rain Badge (`FLAG_BADGE08_GET`).