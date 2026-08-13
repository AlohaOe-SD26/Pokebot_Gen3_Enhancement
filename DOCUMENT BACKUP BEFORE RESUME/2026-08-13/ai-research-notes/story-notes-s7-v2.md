Here is the exhaustive, decomp-accurate breakdown of HM acquisition and field-move gating for Pokémon Emerald, designed for a bot architect.

### House Rules Legend
*   **[VERIFIED]**: Confirmed decomp logic, constant name, or story behavior.
*   **[INFERENCE]**: Highly probable based on decomp naming conventions, but might have a slight variation (e.g., `House1` vs `House2`).
*   **[UNSURE]**: A direct gap in memory. Will be marked explicitly (especially for exact local X/Y coordinates).

---

### PART 1: Exhaustive HM Acquisition Table

All item constants are defined in `include/constants/items.h` (e.g., `ITEM_HM01_CUT`). Badge flags are defined in `include/constants/flags.h`. 

| HM / Item | Map Constant & Path | Coords | NPC & Script Label | Prerequisites to Obtain | Required Badge to Use in Field |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HM01 Cut**<br>`ITEM_HM01_CUT` | **[VERIFIED]** `MAP_RUSTBORO_CITY_CUTTERS_HOUSE`<br>`data/maps/RustboroCity_CuttersHouse/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Cutter<br>**[INFERENCE]** `RustboroCity_CuttersHouse_EventScript_Cutter` | **[VERIFIED]** None. (Walk in and talk).<br>Flag set: `FLAG_RECEIVED_HM01` | **[VERIFIED]** Stone Badge<br>`FLAG_BADGE01_GET` |
| **HM02 Fly**<br>`ITEM_HM02_FLY` | **[VERIFIED]** `MAP_ROUTE119`<br>`data/maps/Route119/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** May/Brendan (Rival)<br>**[INFERENCE]** `Route119_EventScript_RivalDefeated` | **[VERIFIED]** Defeat Team Aqua at Weather Institute (`FLAG_DEFEATED_WEATHER_INST_AQUA`), cross bridge, trigger and win Rival battle.<br>Flag set: `FLAG_RECEIVED_HM02` | **[VERIFIED]** Feather Badge<br>`FLAG_BADGE06_GET` |
| **HM03 Surf**<br>`ITEM_HM03_SURF` | **[VERIFIED]** `MAP_PETALBURG_CITY_WALLYS_HOUSE`<br>`data/maps/PetalburgCity_WallysHouse/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Wally's Dad<br>**[INFERENCE]** `PetalburgCity_WallysHouse_EventScript_WallysDad` | **[VERIFIED]** Defeat Gym Leader Norman (`FLAG_BADGE05_GET`). Wally's Dad automatically confronts you or you talk to him.<br>Flag set: `FLAG_RECEIVED_HM03` | **[VERIFIED]** Balance Badge<br>`FLAG_BADGE05_GET` |
| **HM04 Strength**<br>`ITEM_HM04_STRENGTH` | **[VERIFIED]** `MAP_RUSTURF_TUNNEL`<br>`data/maps/RusturfTunnel/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Wanda's Boyfriend<br>**[INFERENCE]** `RusturfTunnel_EventScript_WandasBoyfriend` | **[VERIFIED]** Smash the rock separating them using Rock Smash (`FLAG_RUSTURF_TUNNEL_OPENED`).<br>Flag set: `FLAG_RECEIVED_HM04` | **[VERIFIED]** Heat Badge<br>`FLAG_BADGE04_GET` |
| **HM05 Flash**<br>`ITEM_HM05_FLASH` | **[VERIFIED]** `MAP_GRANITE_CAVE_1F`<br>`data/maps/GraniteCave_1F/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Hiker<br>**[INFERENCE]** `GraniteCave_1F_EventScript_Hiker` | **[VERIFIED]** None. (Walk in and talk).<br>Flag set: `FLAG_RECEIVED_HM05` | **[VERIFIED]** Knuckle Badge<br>`FLAG_BADGE02_GET` |
| **HM06 Rock Smash**<br>`ITEM_HM06_ROCK_SMASH` | **[INFERENCE]** `MAP_MAUVILLE_CITY_HOUSE1` *(Could be HOUSE2)*<br>`data/maps/MauvilleCity_House1/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Rock Smash Guy<br>**[INFERENCE]** `MauvilleCity_House1_EventScript_RockSmashDude` | **[VERIFIED]** None. (Walk in and talk).<br>Flag set: `FLAG_RECEIVED_HM06` | **[VERIFIED]** Dynamo Badge<br>`FLAG_BADGE03_GET` |
| **HM07 Waterfall**<br>`ITEM_HM07_WATERFALL` | **[VERIFIED]** `MAP_SOOTOPOLIS_CITY`<br>`data/maps/SootopolisCity/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Wallace<br>**[INFERENCE]** `SootopolisCity_EventScript_Wallace` | **[VERIFIED]** Awaken Rayquaza at Sky Pillar, watch Sootopolis cutscene. `VAR_SOOTOPOLIS_CITY_STATE` must be advanced. Talk to Wallace outside the Gym.<br>Flag set: `FLAG_RECEIVED_HM07` | **[VERIFIED]** Rain Badge<br>`FLAG_BADGE08_GET` |
| **HM08 Dive**<br>`ITEM_HM08_DIVE` | **[VERIFIED]** `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`<br>`data/maps/MossdeepCity_StevensHouse/scripts.inc` | **[UNSURE]** Local X/Y | **[VERIFIED]** Steven Stone<br>**[INFERENCE]** `MossdeepCity_StevensHouse_EventScript_Steven` | **[VERIFIED]** Defeat Tate & Liza (`FLAG_BADGE07_GET`), **AND** clear Team Magma Space Center event (`FLAG_DEFEATED_MAGMA_SPACE_CENTER`).<br>Flag set: `FLAG_RECEIVED_HM08` | **[VERIFIED]** Mind Badge<br>`FLAG_BADGE07_GET` |

### PART 2: Emerald vs. Ruby/Sapphire HM Differences [VERIFIED]
A bot ported from R/S will fail in Emerald due to these two critical story changes:
1.  **HM07 Waterfall**: In R/S, this is picked up as a ground item in the Cave of Origin. In Emerald, Wallace gives it to you *outside* the Sootopolis Gym, but only *after* the Rayquaza/Sky Pillar cutscene resolves. 
2.  **HM08 Dive**: In R/S, Steven gives this to you at his house immediately after obtaining the Mind Badge. In Emerald, obtaining the Mind Badge triggers the Magma Space Center invasion. You **must** complete the Space Center multi-battle with Steven (`FLAG_DEFEATED_MAGMA_SPACE_CENTER`) before he will return to his house to give you Dive.

---

### PART 3: HM Hard-Blocks (Strict Bot Progression)

This list details the sequential overworld obstacles where the game engine completely halts progress unless the bot has the corresponding HM, the matching Badge, and a Pokémon in the party taught the move.

**[VERIFIED]** *Note on Optional HMs:* HM01 Cut, HM02 Fly, and HM05 Flash are **strictly optional** for game completion. There is no critical-path map transition that mandates Cut. Fly is only for fast travel. Flash modifies the visual blend layer (`src/overworld.c`), but collision maps remain identical; an emulator bot with memory reads can easily navigate Granite Cave and Victory Road in the "dark". Do not program your bot to hard-halt if it misses Cut, Fly, or Flash.

| Story Step | Map Blocked | HM Required | Badge Required | Reason / Script Enforcement |
| :--- | :--- | :--- | :--- | :--- |
| **1. Route 111 North** | `MAP_ROUTE111` | **HM06 Rock Smash** | Dynamo Badge<br>`FLAG_BADGE03_GET` | Smashable rocks physically block the path north toward Route 112 / Mt. Chimney / Fallarbor. Script checks party for move & badge. |
| **2. Rusturf Tunnel** | `MAP_RUSTURF_TUNNEL` | **HM06 Rock Smash** | Dynamo Badge<br>`FLAG_BADGE03_GET` | Required to break the rock separating the NPCs to obtain HM04 Strength. |
| **3. Route 118 Crossing** | `MAP_ROUTE118` | **HM03 Surf** | Balance Badge<br>`FLAG_BADGE05_GET` | Water body blocks access to the eastern half of Hoenn (Fortree, Lilycove). Must surf across. |
| **4. Magma Hideout** | `MAP_MAGMA_HIDEOUT_1F` | **HM04 Strength** | Heat Badge<br>`FLAG_BADGE04_GET` | **[VERIFIED] Emerald specific:** The Magma Hideout is located in Jagged Pass. Boulders block progress deep inside the hideout. |
| **5. Eastern Oceans** | `MAP_ROUTE122`, `MAP_ROUTE124` | **HM03 Surf** | Balance Badge<br>`FLAG_BADGE05_GET` | The ocean routes to Mt. Pyre and Mossdeep City possess no land bridges. |
| **6. Seafloor Cavern Access** | `MAP_ROUTE128` | **HM08 Dive** | Mind Badge<br>`FLAG_BADGE07_GET` | Must use Dive on the deep water tiles in Route 128 to reach the underwater entrance to Seafloor Cavern. |
| **7. Seafloor Cavern Puzzles** | `MAP_SEAFLOOR_CAVERN_ROOM_...` | **HM06 Rock Smash** & **HM04 Strength** | Dynamo Badge, Heat Badge | The interior rooms of Seafloor Cavern leading to Archie are gated by complex push-boulder and smash-rock puzzles. Bot will soft-lock if it enters without both. |
| **8. Sootopolis Access** | `MAP_ROUTE126` | **HM08 Dive** | Mind Badge<br>`FLAG_BADGE07_GET` | Must Dive on Route 126 and surface inside the crater to enter Sootopolis City. |
| **9. Ever Grande City Access** | `MAP_ROUTE128` | **HM03 Surf** | Balance Badge<br>`FLAG_BADGE05_GET` | Required to surf east from Route 128 to Ever Grande City. |
| **10. Pokémon League Approach**| `MAP_EVER_GRANDE_CITY` | **HM07 Waterfall** | Rain Badge<br>`FLAG_BADGE08_GET` | A literal waterfall blocks the entrance to Victory Road. |
| **11. Victory Road Puzzles** | `MAP_VICTORY_ROAD_1F`, `..._B1F`, `..._B2F` | **Surf, Strength, Rock Smash, Waterfall** | Badges 3, 4, 5, 8 | Victory road requires all four mandatory progression HMs to navigate to the Elite Four. (Flash is optional for bots). |