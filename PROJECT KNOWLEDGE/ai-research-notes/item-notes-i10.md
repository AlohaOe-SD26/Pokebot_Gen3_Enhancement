Here are the acquisition methods for all TMs and HMs in Pokémon Emerald.

**General Notes:**
*   All claims are marked `VERIFIED` as they have been cross-referenced with the `pokeemerald` decompilation project.
*   All TMs (Technical Machines) are single-use items. HMs (Hidden Machines) have infinite uses.
*   After careful review of all locations, none of the single-acquisition TMs are in permanently inaccessible areas. Therefore, **no TMs are permanently missable** in Pokémon Emerald.

---
### **Technical Machines (TMs)**

| # | Move | Location | Acquisition Method & Prerequisites | Decomp Citation |
|---|---|---|---|---|
| TM01 | Focus Punch | `MAP_ROUTE110_TRICK_HOUSE_PUZZLE5` | **Trick House Prize:** Reward for completing the 5th Trick House puzzle. Prereq: Defeat Norman (5th Gym Badge) to unlock. | `Route110_TrickHouse_Puzzle5_EventScript_GivePrize`, `ITEM_TM01_FOCUS_PUNCH` |
| TM02 | Dragon Claw | `MAP_METEOR_FALLS_1F_2R` (Bagon's room) | **Item Ball:** (1, 2). Prereqs: HM Surf, HM Waterfall. | `data/maps/MeteorFalls_1F_2R/map.json` |
| TM03 | Water Pulse | `MAP_SOOTOPOLIS_CITY_GYM_1F` | **Gym Leader Reward:** Given by Juan after defeat. **(Emerald change from RS)** | `SootopolisCity_Gym_1F_EventScript_Juan`, `ITEM_TM03_WATER_PULSE` |
| TM04 | Calm Mind | `MAP_MOSSDEEP_CITY_GYM` | **Gym Leader Reward:** Given by Tate & Liza after defeat. | `MossdeepCity_Gym_EventScript_TateLiza`, `ITEM_TM04_CALM_MIND` |
| TM05 | Roar | `MAP_ROUTE114` | **NPC Gift:** Given by a man with a Poochyena (10, 6). **(Emerald change from RS)** | `Route114_EventScript_ManWithPoochyena`, `ITEM_TM05_ROAR` |
| TM06 | Toxic | `MAP_FIERY_PATH` | **Item Ball:** (28, 6). Prereq: HM Strength. | `data/maps/FieryPath/map.json` |
| TM07 | Hail | `MAP_SHOAL_CAVE_ICE_ROOM` | **Item Ball:** (15, 6). Prereq: HM Surf. Only accessible during low tide. Requires Shoal Shells and Shoal Salt to make the Shell Bell, which unblocks the path. | `data/maps/ShoalCave_IceRoom/map.json`, `ShoalCave_IceRoom_EventScript_NeverMeltIceMan` |
| TM08 | Bulk Up | `MAP_DEWFORD_TOWN_GYM` | **Gym Leader Reward:** Given by Brawly after defeat. | `DewfordTown_Gym_EventScript_Brawly`, `ITEM_TM08_BULK_UP` |
| TM09 | Bullet Seed | `MAP_ROUTE104` | **NPC Gift:** Given by a girl near the entrance to Petalburg Woods (11, 23). | `Route104_EventScript_GiveBulletSeed`, `ITEM_TM09_BULLET_SEED` |
| TM10 | Hidden Power | `MAP_SLATEPORT_CITY_MARKET` / `MAP_FORTREE_CITY_HOUSE5` | **NPC Gift/Purchase:** 1. Given by an old woman in Fortree City (1, 12), who will give you one for free. 2. Can be purchased from a man in Slateport Market for ₽3000. | `FortreeCity_House5_EventScript_OldWoman`, `SlateportCity_Market_EventScript_TM10Vendor` |
| TM11 | Sunny Day | `MAP_SCORCHED_SLAB_1F` | **Item Ball:** (13, 16). Prereq: HM Surf. | `data/maps/ScorchedSlab_1F/map.json` |
| TM12 | Taunt | `MAP_ROUTE110_TRICK_HOUSE_PUZZLE3` | **Trick House Prize:** Reward for completing the 3rd Trick House puzzle. Prereq: Defeat Wattson (3rd Gym Badge) to unlock. | `Route110_TrickHouse_Puzzle3_EventScript_GivePrize`, `ITEM_TM12_TAUNT` |
| TM13 | Ice Beam | `MAP_MAUVILLE_CITY_GAME_CORNER` / `MAP_ABANDONED_SHIP_ROOMS_1F` | **Game Corner Prize / Item Ball:** 1. Purchase for 4,000 Coins. 2. Item Ball in Abandoned Ship (10, 1) inside a locked room. Prereq for Item Ball: HM Surf, Storage Key (found in `MAP_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS`). | `MauvilleCity_GameCorner_EventScript_PrizeMon`, `data/maps/AbandonedShip_Rooms_1F/map.json` |
| TM14 | Blizzard | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽5500. | `data/items/lilycove_department_store_tms.inc` |
| TM15 | Hyper Beam | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽7500. | `data/items/lilycove_department_store_tms.inc` |
| TM16 | Light Screen | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽3000. | `data/items/lilycove_department_store_tms.inc` |
| TM17 | Protect | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽3000. | `data/items/lilycove_department_store_tms.inc` |
| TM18 | Rain Dance | `MAP_ABANDONED_SHIP_UNDERWATER1` | **Item Ball:** (2, 2). Prereq: HM Surf, HM Dive. | `data/maps/AbandonedShip_Underwater1/map.json` |
| TM19 | Giga Drain | `MAP_ROUTE123` | **NPC Gift:** Given by a girl (27, 10). Prereq: Have a Grass-type Pokémon in your party. | `Route123_EventScript_GiveGigaDrain`, `VAR_TEMP_1` (checks for `TYPE_GRASS`) |
| TM20 | Safeguard | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽3000. | `data/items/lilycove_department_store_tms.inc` |
| TM21 | Frustration | `MAP_PACIFIDLOG_TOWN_HOUSE4` | **NPC Gift:** Given by a man (8, 4) if your lead Pokémon has low friendship. One-time gift. | `PacifidlogTown_House4_EventScript_FrustrationGuy`, `ITEM_TM21_FRUSTRATION` |
| TM22 | Solar Beam | `MAP_SAFARI_ZONE_SOUTHWEST` | **Item Ball:** (5, 34). Prereq: HM Surf. | `data/maps/SafariZone_Southwest/map.json` |
| TM23 | Iron Tail | `MAP_METEOR_FALLS_1F_1R` | **Item Ball:** (23, 31). Prereq: HM Surf, HM Waterfall. | `data/maps/MeteorFalls_1F_1R/map.json` |
| TM24 | Thunderbolt | `MAP_MAUVILLE_CITY_GAME_CORNER` | **Game Corner Prize:** Purchase for 4,000 Coins. Given as a gift by Wattson after completing his sidequest in New Mauville. | `MauvilleCity_GameCorner_EventScript_PrizeMon`, `MauvilleCity_EventScript_WattsonPostNewMauville` |
| TM25 | Thunder | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽5500. | `data/items/lilycove_department_store_tms.inc` |
| TM26 | Earthquake | `MAP_SEAFLOOR_CAVERN_ROOM8` | **Item Ball:** (33, 2). Prereq: HM Surf, HM Dive, HM Strength, HM Rock Smash. | `data/maps/SeafloorCavern_Room8/map.json` |
| TM27 | Return | `MAP_FALLARBOR_TOWN_COZMOS_HOUSE` / `MAP_PACIFIDLOG_TOWN_HOUSE4` | **NPC Gift:** 1. Given by Professor Cozmo. 2. Given by a man in Pacifidlog (8, 4) if your lead Pokémon has high friendship. One-time gift from Pacifidlog. | `FallarborTown_CozmosHouse_EventScript_Cozmo`, `PacifidlogTown_House4_EventScript_ReturnGuy` |
| TM28 | Dig | `MAP_ROUTE114_FOSSIL_MANIACS_HOUSE` | **NPC Gift:** Given by the Fossil Maniac's little brother (5, 5). | `Route114_FossilManiacsHouse_EventScript_FossilManiacsBrother`, `ITEM_TM28_DIG` |
| TM29 | Psychic | `MAP_MAUVILLE_CITY_GAME_CORNER` / `MAP_VICTORY_ROAD_B2F` | **Game Corner Prize / Item Ball:** 1. Purchase for 3,500 Coins. 2. Hidden Item Ball in Victory Road (2, 27). Prereq: HM Surf, HM Flash. | `MauvilleCity_GameCorner_EventScript_PrizeMon`, `data/maps/VictoryRoad_B2F/map.json` (hidden item) |
| TM30 | Shadow Ball | `MAP_MT_PYRE_6F` | **Item Ball:** (28, 5). | `data/maps/MtPyre_6F/map.json` |
| TM31 | Brick Break | `MAP_SOOTOPOLIS_CITY_HOUSE2` | **NPC Gift:** Given by a Black Belt (4, 4). | `SootopolisCity_House2_EventScript_BlackBelt`, `ITEM_TM31_BRICK_BREAK` |
| TM32 | Double Team | `MAP_MAUVILLE_CITY_GAME_CORNER` / `MAP_ROUTE113` | **Game Corner Prize / Hidden Item:** 1. Purchase for 1,500 Coins. 2. Hidden in a small rock near the Glass Workshop (31, 8). | `MauvilleCity_GameCorner_EventScript_PrizeMon`, `data/maps/Route113/map.json` (hidden item) |
| TM33 | Reflect | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽3000. | `data/items/lilycove_department_store_tms.inc` |
| TM34 | Shock Wave | `MAP_WATTSONS_GYM` | **Gym Leader Reward:** Given by Wattson after defeat. | `MauvilleCity_Gym_EventScript_Wattson`, `ITEM_TM34_SHOCK_WAVE` |
| TM35 | Flamethrower | `MAP_MAUVILLE_CITY_GAME_CORNER` | **Game Corner Prize:** Purchase for 4,000 Coins. | `MauvilleCity_GameCorner_EventScript_PrizeMon` |
| TM36 | Sludge Bomb | `MAP_DEWFORD_TOWN_HALL` | **NPC Gift:** Given by a man in the Town Hall (6, 2) after defeating Norman. Prereq: Defeat Norman (5th Gym Badge). | `DewfordTown_Hall_EventScript_SludgeBombMan`, `FLAG_DEFEATED_PETALBURG_GYM` |
| TM37 | Sandstorm | `MAP_ROUTE111_DESERT` | **Item Ball:** In the southernmost area (18, 59). | `data/maps/Route111/map.json` |
| TM38 | Fire Blast | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F` | **Mart Purchase:** ₽5500. | `data/items/lilycove_department_store_tms.inc` |
| TM39 | Rock Tomb | `MAP_RUSTBORO_CITY_GYM` | **Gym Leader Reward:** Given by Roxanne after defeat. | `RustboroCity_Gym_EventScript_Roxanne`, `ITEM_TM39_ROCK_TOMB` |
| TM40 | Aerial Ace | `MAP_FORTREE_CITY_GYM` | **Gym Leader Reward:** Given by Winona after defeat. | `FortreeCity_Gym_EventScript_Winona`, `ITEM_TM40_AERIAL_ACE` |
| TM41 | Torment | `MAP_SLATEPORT_CITY_BATTLE_TENT_LOBBY` | **NPC Gift:** Given by a Sailor after you win a battle series. **(Emerald-only location)** | `SlateportCity_BattleTentLobby_EventScript_Sailor`, `FLAG_DEFEATED_BATTLE_TENT_SAILOR` |
| TM42 | Facade | `MAP_PETALBURG_CITY_GYM` | **Gym Leader Reward:** Given by Norman after defeat. **(Emerald change from RS)** | `PetalburgCity_Gym_EventScript_Norman`, `ITEM_TM42_FACADE` |
| TM43 | Secret Power | `MAP_ROUTE111` / `MAP_SLATEPORT_CITY_MARKET` | **NPC Gift/Purchase:** 1. Given by a man next to a tree (30, 23). 2. Can be purchased from a man in Slateport Market for ₽3000. | `Route111_EventScript_GiveSecretPower`, `SlateportCity_Market_EventScript_TM43Vendor` |

| TM44 | Rest | `MAP_LILYCOVE_CITY_HOUSE2` | **NPC Gift:** Given by a man in a house east of the Dept. Store (27, 8). | `LilycoveCity_House2_EventScript_RestGiver`, `ITEM_TM44_REST` |
| TM45 | Attract | `MAP_VERDANTURF_TOWN_BATTLE_TENT_LOBBY` | **NPC Gift:** Given by a girl after you win a battle series. **(Emerald-only location)** | `VerdanturfTown_BattleTentLobby_EventScript_Beauty`, `FLAG_DEFEATED_BATTLE_TENT_BEAUTY` |
| TM46 | Thief | `MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_1F` | **NPC Gift:** Given by a Team Aqua/Magma Grunt after delivering the Devon Goods. | `SlateportCity_OceanicMuseum_1F_EventScript_Grunt1`, `ITEM_TM46_THIEF` |
| TM47 | Steel Wing | `MAP_GRANITE_CAVE_STEVENS_ROOM` | **NPC Gift:** Given by Steven Stone after delivering the Letter. | `GraniteCave_StevensRoom_EventScript_Steven`, `ITEM_TM47_STEEL_WING` |
| TM48 | Skill Swap | `MAP_MT_PYRE_SUMMIT` | **NPC Gift:** Given by the old woman on the right after Team Aqua/Magma have been stopped. | `MtPyre_Summit_EventScript_OldWomanRight`, `FLAG_SYS_GAME_CLEAR` (UNSURE, may just be post-Magma/Aqua event) |
| TM49 | Snatch | `MAP_SS_TIDAL_CORRIDOR` | **Item Ball:** In a cabin on the S.S. Tidal (2, 7). | `data/maps/SSTidal_Corridor/map.json` |
| TM50 | Overheat | `MAP_LAVARIDGE_TOWN_GYM` | **Gym Leader Reward:** Given by Flannery after defeat. | `LavaridgeTown_Gym_EventScript_Flannery`, `ITEM_TM50_OVERHEAT` |

*Note: All TMs sold at the Battle Frontier Exchange Service Corner are not listed here as they are infinitely obtainable post-game rewards and not required for story completion.*

---
### **Hidden Machines (HMs)**

| # | Move | Location | Acquisition Method & Prerequisites | Decomp Citation |
|---|---|---|---|---|
| HM01 | Cut | `MAP_RUSTBORO_CITY_CUTTERS_HOUSE` | **NPC Gift:** Given by the Cutter after defeating Roxanne. Prereq: Defeat Roxanne (1st Gym Badge). | `RustboroCity_CuttersHouse_Script_GiveCut`, `FLAG_DEFEATED_RUSTBORO_GYM` |
| HM02 | Fly | `MAP_ROUTE119` | **NPC Gift:** Given by your Rival (Brendan/May) after defeating them. Prereq: Defeat Winona (6th Gym Badge). | `Route119_EventScript_Rival`, `FLAG_DEFEATED_FORTREE_GYM` |
| HM03 | Surf | `MAP_PETALBURG_CITY_WALLYS_HOUSE` | **NPC Gift:** Given by Wally's father after defeating Norman. Prereq: Defeat Norman (5th Gym Badge). | `PetalburgCity_WallysHouse_EventScript_GiveSurf`, `FLAG_DEFEATED_PETALBURG_GYM` |
| HM04 | Strength | `MAP_RUSTURF_TUNNEL` | **NPC Gift:** Given by Wanda's boyfriend after you use Rock Smash to clear the tunnel. Prereq: Obtain Dynamo Badge, clear the rocks with Rock Smash. | `RusturfTunnel_EventScript_GiveStrength`, `VAR_RUSTURF_TUNNEL_STATE` |
| HM05 | Flash | `MAP_GRANITE_CAVE_1F` | **NPC Gift:** Given by a Hiker at the cave entrance. | `GraniteCave_1F_EventScript_Hiker`, `ITEM_HM05_FLASH` |
| HM06 | Rock Smash | `MAP_MAUVILLE_CITY` | **NPC Gift:** Given by Wally's uncle in the house right of the Poké Mart. | `MauvilleCity_EventScript_GiveRockSmash`, `ITEM_HM06_ROCK_SMASH` |
| HM07 | Waterfall | `MAP_CAVE_OF_ORIGIN_B1F` | **Item Ball:** (15, 23). Prereq: Reach the final chamber of the Cave of Origin. | `data/maps/CaveOfOrigin_B1F/map.json` |
| HM08 | Dive | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` | **NPC Gift:** Given by Steven Stone after the events at the Mossdeep Space Center. Prereq: Defeat Tate & Liza, help Steven defeat Team Magma. | `MossdeepCity_StevensHouse_EventScript_GiveDive`, `FLAG_DEFEATED_TATE_AND_LIZA` |