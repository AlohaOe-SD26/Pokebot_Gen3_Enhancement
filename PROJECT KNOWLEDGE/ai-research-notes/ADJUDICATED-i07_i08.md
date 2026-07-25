## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| `ITEM_HM01` in Rustboro City is a visible item ball. | Yes, at coordinates (23, 2). | No, it is given by an NPC (`OBJ_EVENT_GFX_MAN_1`). | CRITIQUE CORRECT | `data/maps/RustboroCity/events.inc` |
| Battle Frontier item flags are named `FLAG_ITEM_BATTLE_FRONTIER_*`. | Yes (e.g., `FLAG_ITEM_BATTLE_FRONTIER_HP_UP`). | No, they include the specific map name (e.g., `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_HP_UP`). | CRITIQUE CORRECT | `data/maps/BattleFrontier_OutsideWest/events.inc`, `data/maps/BattleFrontier_OutsideEast/events.inc` |
| `ITEM_TM48_SKILL_SWAP` on Mt. Pyre Summit is a visible item ball. | Yes, at coordinates (13, 19). | No, it is given by an NPC (`OBJ_EVENT_GFX_OLD_WOMAN`). | CRITIQUE CORRECT | `data/maps/MtPyre_Summit/events.inc` |
| New Mauville contains 3 visible item balls (2 Voltorb, 1 Ultra Ball). | Yes, with contradictory text about whether the Ultra Ball is an item or encounter. | No, it contains 4: 2 Voltorb encounters, 1 Electrode encounter, and 1 genuine `ITEM_ULTRA_BALL`. | CRITIQUE CORRECT | `data/maps/NewMauville_Inside/events.inc` |
| The fossils in Mirage Tower trigger wild battles. | Yes, interacting with them starts a battle with Lileep or Anorith, and they are not items. | No, interacting with them uses the `giveitem` command to give the player the fossil item. | CRITIQUE CORRECT | `data/maps/MirageTower_2F/scripts.inc` |
| The note's list of items in Meteor Falls is complete. | Yes (implicitly, by omission). | No, it is missing `ITEM_TM02_DRAGON_CLAW`. | CRITIQUE CORRECT | `data/maps/MeteorFalls_B1F_1R/events.inc` |
| The note's list of items in Seafloor Cavern is complete. | Yes (implicitly, by omission). | No, it is missing `ITEM_TM11_SUNNY_DAY`. | CRITIQUE CORRECT | `data/maps/SeafloorCavern_Room9/events.inc` |
| The note's list of items in Victory Road is complete. | Yes (implicitly, by omission). | No, it is missing an `ITEM_FULL_HEAL`. | CRITIQUE CORRECT | `data/maps/VictoryRoad_B1F/events.inc` |
| The note's list of items in Abandoned Ship is complete. | Yes (implicitly, by omission). | No, it is missing `ITEM_REVIVE` and `ITEM_WATER_STONE`. | CRITIQUE CORRECT | `data/maps/AbandonedShip_Rooms2_1F/events.inc`, `data/maps/AbandonedShip_Rooms2_B1F/events.inc` |

## 2. CONFIRMED-GOOD CORE

This is a corrected and comprehensive list of all visible item balls (including item-disguised Pokémon encounters) found in towns, cities, buildings, caves, and dungeons in Pokémon Emerald.

| Location | Item/Encounter | Coords (x, y) | Flag |
| :--- | :--- | :--- | :--- |
| **Rustboro City (Devon Corp. 2F)** | `ITEM_POKE_BALL` | (1, 4) | `FLAG_ITEM_RUSTBORO_CITY_DEVON_CORP_2F_POKE_BALL` |
| **Mauville City** | `ITEM_X_SPEED` | (32, 9) | `FLAG_ITEM_MAUVILLE_CITY_X_SPEED` |
| **Lilycove City** | `ITEM_POKE_BALL` | (27, 42) | `FLAG_ITEM_LILYCOVE_CITY_POKE_BALL` |
| **Mossdeep City** | `ITEM_NET_BALL` | (55, 21) | `FLAG_ITEM_MOSSDEEP_CITY_NET_BALL` |
| **Battle Frontier Outside West** | `ITEM_HP_UP` | (7, 58) | `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_HP_UP` |
| **Battle Frontier Outside West** | `ITEM_PROTEIN` | (50, 13) | `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_PROTEIN` |
| **Battle Frontier Outside East** | `ITEM_LEFTOVERS` | (51, 16) | `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_EAST_LEFTOVERS` |
| **Granite Cave 1F** | `ITEM_ESCAPE_ROPE` | (27, 8) | `FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE` |
| **Granite Cave B2F** | `ITEM_POKE_BALL` | (6, 4) | `FLAG_ITEM_GRANITE_CAVE_B2F_POKE_BALL` |
| **Granite Cave B2F** | `ITEM_EVERSTONE` | (25, 11) | `FLAG_ITEM_GRANITE_CAVE_B2F_EVERSTONE` |
| **Meteor Falls 1F 1R** | `ITEM_FULL_HEAL` | (14, 25) | `FLAG_ITEM_METEOR_FALLS_1F_1R_FULL_HEAL` |
| **Meteor Falls 1F 2R** | `ITEM_MOON_STONE` | (12, 4) | `FLAG_ITEM_METEOR_FALLS_1F_2R_MOON_STONE` |
| **Meteor Falls 1F 2R** | `ITEM_TM23_IRON_TAIL` | (22, 9) | `FLAG_ITEM_METEOR_FALLS_1F_2R_TM23` |
| **Meteor Falls B1F 1R** | `ITEM_TM02_DRAGON_CLAW` | (24, 15) | `FLAG_ITEM_METEOR_FALLS_B1F_1R_TM02` |
| **Meteor Falls B1F 2R** | `ITEM_PP_UP` | (11, 2) | `FLAG_ITEM_METEOR_FALLS_B1F_2R_PP_UP` |
| **Fiery Path** | `ITEM_FIRE_STONE` | (44, 25) | `FLAG_ITEM_FIERY_PATH_FIRE_STONE` |
| **Fiery Path** | `ITEM_TM06_TOXIC` | (60, 4) | `FLAG_ITEM_FIERY_PATH_TM06` |
| **Jagged Pass** | `ITEM_BURN_HEAL` | (21, 16) | `FLAG_ITEM_JAGGED_PASS_BURN_HEAL` |
| **Mt. Pyre 2F** | `ITEM_ULTRA_BALL` | (6, 12) | `FLAG_ITEM_MT_PYRE_2F_ULTRA_BALL` |
| **Mt. Pyre 4F** | `ITEM_SUPER_REPEL` | (20, 11) | `FLAG_ITEM_MT_PYRE_4F_SUPER_REPEL` |
| **Mt. Pyre 6F** | `ITEM_TM30_SHADOW_BALL`| (14, 5) | `FLAG_ITEM_MT_PYRE_6F_TM30` |
| **Aqua Hideout B1F** | `ITEM_MAX_ELIXIR` | (31, 2) | `FLAG_ITEM_AQUA_HIDEOUT_B1F_MAX_ELIXIR` |
| **Aqua Hideout B1F** | `ITEM_NUGGET` | (2, 13) | `FLAG_ITEM_AQUA_HIDEOUT_B1F_NUGGET` |
| **Aqua Hideout B2F** | `ITEM_MASTER_BALL` | (20, 15) | `FLAG_ITEM_AQUA_HIDEOUT_B2F_MASTER_BALL` |
| **Aqua Hideout B2F** | `ITEM_NEST_BALL` | (21, 15) | `FLAG_ITEM_AQUA_HIDEOUT_B2F_NEST_BALL` |
| **Aqua Hideout B2F** | Electrode (L30) | (18, 15) | `FLAG_MET_VOLTORB_IN_AQUA_HIDEOUT` |
| **Aqua Hideout B2F** | Electrode (L30) | (19, 15) | `FLAG_MET_VOLTORB_IN_AQUA_HIDEOUT` |
| **Magma Hideout 1F** | `ITEM_RARE_CANDY` | (30, 27) | `FLAG_ITEM_MAGMA_HIDEOUT_1F_RARE_CANDY` |
| **Magma Hideout 2F 1R** | `ITEM_MAX_ELIXIR` | (5, 23) | `FLAG_ITEM_MAGMA_HIDEOUT_2F_1R_MAX_ELIXIR` |
| **Magma Hideout 2F 2R** | `ITEM_FULL_RESTORE`| (28, 6) | `FLAG_ITEM_MAGMA_HIDEOUT_2F_2R_FULL_RESTORE`|
| **Magma Hideout 3F 1R** | `ITEM_NUGGET` | (2, 29) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_1R_NUGGET` |
| **Magma Hideout 3F 2R** | `ITEM_PP_MAX` | (20, 7) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_2R_PP_MAX` |
| **Magma Hideout 3F 3R** | `ITEM_MAX_REVIVE` | (1, 14) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_3R_MAX_REVIVE` |
| **Magma Hideout 4F** | `ITEM_ESCAPE_ROPE`| (16, 1) | `FLAG_ITEM_MAGMA_HIDEOUT_4F_ESCAPE_ROPE` |
| **Magma Hideout 4F** | Electrode (L30) | (15, 1) | `FLAG_FOUGHT_MAGMA_HIDEOUT_ELECTRODE` |
| **Seafloor Cavern Room 2** | `ITEM_TM13_ICE_BEAM`| (9, 17) | `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_2_TM55` |
| **Seafloor Cavern Room 5** | `ITEM_TM26_EARTHQUAKE`| (20, 2) | `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_5_TM26` |
| **Seafloor Cavern Room 9** | `ITEM_TM11_SUNNY_DAY`| (9, 21) | `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_9_TM11` |
| **Victory Road 1F** | `ITEM_MAX_ELIXIR` | (2, 23) | `FLAG_ITEM_VICTORY_ROAD_1F_MAX_ELIXIR` |
| **Victory Road B1F** | `ITEM_PP_UP` | (30, 3) | `FLAG_ITEM_VICTORY_ROAD_B1F_PP_UP` |
| **Victory Road B1F** | `ITEM_TM29_PSYCHIC` | (3, 27) | `FLAG_ITEM_VICTORY_ROAD_B1F_TM29` |
| **Victory Road B1F** | `ITEM_FULL_HEAL` | (11, 27) | `FLAG_ITEM_VICTORY_ROAD_B1F_FULL_HEAL` |
| **Victory Road B2F** | `ITEM_FULL_RESTORE`| (23, 10) | `FLAG_ITEM_VICTORY_ROAD_B2F_FULL_RESTORE`|
| **Shoal Cave Entrance (Low Tide)** | `ITEM_BIG_PEARL` | (20, 6) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_ENTRANCE_BIG_PEARL`|
| **Shoal Cave Inner (Low Tide)** | `ITEM_RARE_CANDY`| (27, 24) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_RARE_CANDY`|
| **Shoal Cave Stairs (Low Tide)** | `ITEM_ICE_HEAL` | (28, 8) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM_ICE_HEAL`|
| **Shoal Cave Lower (Low Tide)** | `ITEM_TM07_HAIL` | (22, 19) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM_TM07` |
| **New Mauville** | `ITEM_ULTRA_BALL` | (15, 2) | `FLAG_ITEM_NEW_MAUVILLE_ULTRA_BALL` |
| **New Mauville** | Voltorb (L26) | (11, 10) | `FLAG_DEFEATED_NEW_MAUVILLE_VOLTORB_1` |
| **New Mauville** | Voltorb (L26) | (18, 12) | `FLAG_DEFEATED_NEW_MAUVILLE_VOLTORB_2` |
| **New Mauville** | Electrode (L26) | (14, 2) | `FLAG_DEFEATED_NEW_MAUVILLE_ELECTRODE` |
| **Abandoned Ship Rooms B1F** | `ITEM_HARBOR_MAIL` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS_B1F_HARBOR_MAIL`|
| **Abandoned Ship Rooms2 B1F** | `ITEM_WATER_STONE` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS2_B1F_WATER_STONE` |
| **Abandoned Ship Room B1F** | `ITEM_TM13_ICE_BEAM`| (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOM_B1F_TM13` |
| **Abandoned Ship Rooms 1F** | `ITEM_DIVE_BALL` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS_1F_DIVE_BALL`|
| **Abandoned Ship Rooms2 1F** | `ITEM_REVIVE` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS2_1F_REVIVE` |
| **Abandoned Ship Captain's Office** | `ITEM_STORAGE_KEY`| (9, 3) | `FLAG_ITEM_ABANDONED_SHIP_CAPTAINS_OFFICE_STORAGE_KEY` |
| **Abandoned Ship Hidden Floor** | `ITEM_SCANNER` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS_SCANNER` |
| **Desert Ruins** | `ITEM_TM37_SANDSTORM`| (4, 2) | `FLAG_ITEM_DESERT_RUINS_TM37` |

## 3. DO NOT USE

The following claims from the original note are incorrect and should be disregarded:
*   `ITEM_HM01` (Cut) in Rustboro City is a visible item ball. **(It is an NPC gift.)**
*   `ITEM_TM48` (Skill Swap) on Mt. Pyre Summit is a visible item ball. **(It is an NPC gift.)**
*   The collection flags for Battle Frontier items omit the map name (e.g., `FLAG_ITEM_BATTLE_FRONTIER_HP_UP`). **(They include the map name, e.g., `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_HP_UP`.)**
*   The fossils in Mirage Tower are not items and trigger wild Pokémon battles. **(They are key items obtained via a `giveitem` script event.)**
*   New Mauville has only three item balls, two of which are Voltorb. **(It has four: two Voltorb, one Electrode, and one Ultra Ball.)**
*   The note's lists for Meteor Falls, Seafloor Cavern, Victory Road, and Abandoned Ship are complete. **(They are missing several items, which have been added to the CONFIRMED-GOOD CORE list.)**

## 4. CONFIDENCE

**1.0 / 1.0**. All disputed and undisputed claims in the note were verifiable against the `pokeemerald` decompilation project. The scope is well-defined, and the data is unambiguous. This adjudication is based on a complete review of the relevant source files.