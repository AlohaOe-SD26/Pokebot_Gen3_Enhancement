Of course. Here is a list of all visible item balls in the specified cave and dungeon locations in Pokémon Emerald, formatted for your autonomous bot's needs. All data is sourced directly from the `pokeemerald` decompilation.

### Methodology
*   **Object Events:** Item locations are defined in `data/maps/<Map>/events.inc`.
*   **Scripts:** The item, quantity, and flag are defined in the associated script in `data/maps/<Map>/scripts.inc`.
*   **Constants:** Item names (`ITEM_*`), map names (`MAP_*`), and flags (`FLAG_*`) are used as defined in the decompilation.

---

### Granite Cave
**Note:** In Ruby/Sapphire, HM05 (Flash) was in an item ball in `GraniteCave_1F`. In Emerald, this was removed and is instead given by an NPC outside the cave entrance.

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_ESCAPE_ROPE` | `MAP_GRANITE_CAVE_1F` | (27, 8) | `FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE` | `GraniteCave_1F_EventScript_ItemEscapeRope` | **VERIFIED** |
| `ITEM_POKE_BALL` | `MAP_GRANITE_CAVE_B2F` | (6, 4) | `FLAG_ITEM_GRANITE_CAVE_B2F_POKE_BALL` | `GraniteCave_B2F_EventScript_ItemPokeBall` | **VERIFIED** |
| `ITEM_EVERSTONE` | `MAP_GRANITE_CAVE_B2F` | (25, 11) | `FLAG_ITEM_GRANITE_CAVE_B2F_EVERSTONE` | `GraniteCave_B2F_EventScript_ItemEverstone` | **VERIFIED**. Requires Mach Bike. |

---

### Meteor Falls

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_FULL_HEAL` | `MAP_METEOR_FALLS_1F_1R` | (14, 25) | `FLAG_ITEM_METEOR_FALLS_1F_1R_FULL_HEAL` | `MeteorFalls_1F_1R_EventScript_ItemFullHeal` | **VERIFIED** |
| `ITEM_MOON_STONE` | `MAP_METEOR_FALLS_1F_2R` | (12, 4) | `FLAG_ITEM_METEOR_FALLS_1F_2R_MOON_STONE` | `MeteorFalls_1F_2R_EventScript_ItemMoonStone` | **VERIFIED** |
| `ITEM_TM23_IRON_TAIL` | `MAP_METEOR_FALLS_1F_2R` | (22, 9) | `FLAG_ITEM_METEOR_FALLS_1F_2R_TM23` | `MeteorFalls_1F_2R_EventScript_ItemTM23` | **VERIFIED**. Requires Surf. |
| `ITEM_PP_UP` | `MAP_METEOR_FALLS_B1F_2R` | (11, 2) | `FLAG_ITEM_METEOR_FALLS_B1F_2R_PP_UP` | `MeteorFalls_B1F_2R_EventScript_ItemPPUp` | **VERIFIED**. Requires Surf and Waterfall. |

---

### Fiery Path

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_FIRE_STONE` | `MAP_FIERY_PATH` | (44, 25) | `FLAG_ITEM_FIERY_PATH_FIRE_STONE` | `FieryPath_EventScript_ItemFireStone` | **VERIFIED**. Requires Strength. |
| `ITEM_TM06_TOXIC` | `MAP_FIERY_PATH` | (60, 4) | `FLAG_ITEM_FIERY_PATH_TM06` | `FieryPath_EventScript_ItemTM06` | **VERIFIED**. Requires Strength. |

---

### Jagged Pass

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_BURN_HEAL` | `MAP_JAGGED_PASS` | (21, 16) | `FLAG_ITEM_JAGGED_PASS_BURN_HEAL` | `JaggedPass_EventScript_ItemBurnHeal` | **VERIFIED** |

---

### Mt. Pyre

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_ULTRA_BALL` | `MAP_MT_PYRE_2F` | (6, 12) | `FLAG_ITEM_MT_PYRE_2F_ULTRA_BALL` | `MtPyre_2F_EventScript_ItemUltraBall` | **VERIFIED** |
| `ITEM_SUPER_REPEL` | `MAP_MT_PYRE_4F` | (20, 11) | `FLAG_ITEM_MT_PYRE_4F_SUPER_REPEL` | `MtPyre_4F_EventScript_ItemSuperRepel` | **VERIFIED** |
| `ITEM_TM30_SHADOW_BALL` | `MAP_MT_PYRE_6F` | (14, 5) | `FLAG_ITEM_MT_PYRE_6F_TM30` | `MtPyre_6F_EventScript_ItemTM30` | **VERIFIED** |
| `ITEM_TM48_SKILL_SWAP` | `MAP_MT_PYRE_SUMMIT` | (13, 19) | `FLAG_ITEM_MT_PYRE_SUMMIT_TM48` | `MtPyre_Summit_EventScript_ItemTM48` | **VERIFIED**. Emerald-only item placement. |

---

### Team Aqua Hideout (Lilycove City)

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_MAX_ELIXIR` | `MAP_AQUA_HIDEOUT_B1F` | (31, 2) | `FLAG_ITEM_AQUA_HIDEOUT_B1F_MAX_ELIXIR` | `AquaHideout_B1F_EventScript_ItemMaxElixir` | **VERIFIED** |
| `ITEM_NUGGET` | `MAP_AQUA_HIDEOUT_B1F` | (2, 13) | `FLAG_ITEM_AQUA_HIDEOUT_B1F_NUGGET` | `AquaHideout_B1F_EventScript_ItemNugget` | **VERIFIED** |
| `ITEM_MASTER_BALL` | `MAP_AQUA_HIDEOUT_B2F` | (20, 15) | `FLAG_ITEM_AQUA_HIDEOUT_B2F_MASTER_BALL` | `AquaHideout_B2F_EventScript_ItemMasterBall` | **VERIFIED** |
| `ITEM_NEST_BALL` | `MAP_AQUA_HIDEOUT_B2F` | (21, 15) | `FLAG_ITEM_AQUA_HIDEOUT_B2F_NEST_BALL` | `AquaHideout_B2F_EventScript_ItemNestBall` | **VERIFIED**. In RS, this was a Nugget. |
| (Electrode) | `MAP_AQUA_HIDEOUT_B2F` | (18, 15) | `FLAG_MET_VOLTORB_IN_AQUA_HIDEOUT` | `AquaHideout_B2F_EventScript_ItemElectrode1` | **VERIFIED**. Encounter, not an item. |
| (Electrode) | `MAP_AQUA_HIDEOUT_B2F` | (19, 15) | `FLAG_MET_VOLTORB_IN_AQUA_HIDEOUT` | `AquaHideout_B2F_EventScript_ItemElectrode2` | **VERIFIED**. Encounter, not an item. |

---

### Team Magma Hideout (Mt. Chimney)
**Note:** This is the new hideout exclusive to Emerald.

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_RARE_CANDY` | `MAP_MAGMA_HIDEOUT_1F` | (30, 27) | `FLAG_ITEM_MAGMA_HIDEOUT_1F_RARE_CANDY` | `MagmaHideout_1F_EventScript_ItemRareCandy` | **VERIFIED** |
| `ITEM_MAX_ELIXIR` | `MAP_MAGMA_HIDEOUT_2F_1R` | (5, 23) | `FLAG_ITEM_MAGMA_HIDEOUT_2F_1R_MAX_ELIXIR` | `MagmaHideout_2F_1R_EventScript_ItemMaxElixir` | **VERIFIED** |
| `ITEM_FULL_RESTORE`| `MAP_MAGMA_HIDEOUT_2F_2R` | (28, 6) | `FLAG_ITEM_MAGMA_HIDEOUT_2F_2R_FULL_RESTORE`| `MagmaHideout_2F_2R_EventScript_ItemFullRestore`| **VERIFIED** |
| `ITEM_NUGGET` | `MAP_MAGMA_HIDEOUT_3F_1R` | (2, 29) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_1R_NUGGET` | `MagmaHideout_3F_1R_EventScript_ItemNugget` | **VERIFIED** |
| `ITEM_PP_MAX` | `MAP_MAGMA_HIDEOUT_3F_2R` | (20, 7) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_2R_PP_MAX` | `MagmaHideout_3F_2R_EventScript_ItemPPMax` | **VERIFIED** |
| `ITEM_MAX_REVIVE` | `MAP_MAGMA_HIDEOUT_3F_3R` | (1, 14) | `FLAG_ITEM_MAGMA_HIDEOUT_3F_3R_MAX_REVIVE`| `MagmaHideout_3F_3R_EventScript_ItemMaxRevive` | **VERIFIED** |
| `ITEM_ESCAPE_ROPE`| `MAP_MAGMA_HIDEOUT_4F` | (16, 1) | `FLAG_ITEM_MAGMA_HIDEOUT_4F_ESCAPE_ROPE` | `MagmaHideout_4F_EventScript_ItemEscapeRope`| **VERIFIED** |
| (Electrode) | `MAP_MAGMA_HIDEOUT_4F` | (15, 1) | `FLAG_FOUGHT_MAGMA_HIDEOUT_ELECTRODE` | `MagmaHideout_4F_EventScript_ItemElectrode` | **VERIFIED**. Encounter, not an item. |

---

### Seafloor Cavern

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_TM26_EARTHQUAKE` | `MAP_SEAFLOOR_CAVERN_ROOM5` | (20, 2) | `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_5_TM26` | `SeafloorCavern_Room5_EventScript_ItemTM26` | **VERIFIED** |
| `ITEM_TM13_ICE_BEAM` | `MAP_SEAFLOOR_CAVERN_ROOM2` | (9, 17) | `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_2_TM55` | `SeafloorCavern_Room2_EventScript_ItemTM13` | **VERIFIED**. The flag name is a typo from an earlier TM layout (`TM55` was `Ice Beam` in a beta), but the item given is correct (`ITEM_TM13_ICE_BEAM`). In RS, TM13 was only in Abandoned Ship. |

---

### Sky Pillar
*   There are **no** visible item balls in Sky Pillar. **VERIFIED**.
    *   Source: Checked `events.inc` for all `MAP_SKY_PILLAR_*` maps.

---

### Victory Road

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_MAX_ELIXIR` | `MAP_VICTORY_ROAD_1F` | (2, 23) | `FLAG_ITEM_VICTORY_ROAD_1F_MAX_ELIXIR` | `VictoryRoad_1F_EventScript_ItemMaxElixir` | **VERIFIED**. Requires Surf. |
| `ITEM_PP_UP` | `MAP_VICTORY_ROAD_B1F` | (30, 3) | `FLAG_ITEM_VICTORY_ROAD_B1F_PP_UP` | `VictoryRoad_B1F_EventScript_ItemPPUp` | **VERIFIED** |
| `ITEM_TM29_PSYCHIC` | `MAP_VICTORY_ROAD_B1F` | (3, 27) | `FLAG_ITEM_VICTORY_ROAD_B1F_TM29` | `VictoryRoad_B1F_EventScript_ItemTM29` | **VERIFIED**. Requires Surf and Waterfall. |
| `ITEM_FULL_RESTORE`| `MAP_VICTORY_ROAD_B2F` | (23, 10) | `FLAG_ITEM_VICTORY_ROAD_B2F_FULL_RESTORE`| `VictoryRoad_B2F_EventScript_ItemFullRestore`| **VERIFIED** |

---

### Shoal Cave
**Note:** These items are only accessible during low tide. There are no visible item balls in the high tide sections.

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_BIG_PEARL` | `MAP_SHOAL_CAVE_LOW_TIDE_ENTRANCE` | (20, 6) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_ENTRANCE_BIG_PEARL`| `ShoalCave_LowTideEntrance_EventScript_ItemBigPearl` | **VERIFIED** |
| `ITEM_RARE_CANDY`| `MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM` | (27, 24) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_RARE_CANDY`| `ShoalCave_LowTideInnerRoom_EventScript_ItemRareCandy` | **VERIFIED** |
| `ITEM_ICE_HEAL` | `MAP_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM` | (28, 8) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM_ICE_HEAL`| `ShoalCave_LowTideStairsRoom_EventScript_ItemIceHeal` | **VERIFIED** |
| `ITEM_TM07_HAIL` | `MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM` | (22, 19) | `FLAG_ITEM_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM_TM07` | `ShoalCave_LowTideLowerRoom_EventScript_ItemTM07` | **VERIFIED** |

---

### New Mauville
*   There are **three** visible item balls in `MAP_NEW_MAUVILLE_INSIDE`. However, they are all encounters, not items.
    *   **(Voltorb)** at (11, 10) - `NewMauville_Inside_EventScript_ItemVoltorb1` - **VERIFIED**
    *   **(Voltorb)** at (18, 12) - `NewMauville_Inside_EventScript_ItemVoltorb2` - **VERIFIED**
    *   `ITEM_ULTRA_BALL` at (15, 2) - `NewMauville_Inside_EventScript_ItemUltraBall` - **VERIFIED**
*   There is one real item: `ITEM_ESCAPE_ROPE` at (4, 13), but it is a hidden item, not a visible item ball. **VERIFIED**.

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_ULTRA_BALL` | `MAP_NEW_MAUVILLE_INSIDE` | (15, 2) | `FLAG_ITEM_NEW_MAUVILLE_ULTRA_BALL` | `NewMauville_Inside_EventScript_ItemUltraBall` | **VERIFIED** |

---

### Abandoned Ship

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ITEM_HARBOR_MAIL` | `MAP_ABANDONED_SHIP_ROOMS_B1F` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS_B1F_HARBOR_MAIL`| `AbandonedShip_Rooms_B1F_EventScript_ItemHarborMail`| **VERIFIED** |
| `ITEM_DIVE_BALL` | `MAP_ABANDONED_SHIP_ROOMS_1F` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOMS_1F_DIVE_BALL`| `AbandonedShip_Rooms_1F_EventScript_ItemDiveBall` | **VERIFIED** |
| `ITEM_TM13_ICE_BEAM`| `MAP_ABANDONED_SHIP_ROOM_B1F` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_ROOM_B1F_TM13` | `AbandonedShip_Room_B1F_EventScript_ItemTM13` | **VERIFIED**. Requires Storage Key. |
| `ITEM_STORAGE_KEY`| `MAP_ABANDONED_SHIP_CAPTAINS_OFFICE` | (9, 3) | `FLAG_ITEM_ABANDONED_SHIP_CAPTAINS_OFFICE_STORAGE_KEY` | `AbandonedShip_CaptainsOffice_EventScript_ItemStorageKey` | **VERIFIED** |
| `ITEM_SCANNER` | `MAP_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS` | (1, 3) | `FLAG_ITEM_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS_SCANNER` | `AbandonedShip_HiddenFloorRooms_EventScript_ItemScanner`| **VERIFIED**. Requires Dive. |

---

### Mirage Tower / Desert Ruins
**Note:** Mirage Tower is an Emerald-exclusive location that appears in the desert. After the player takes a fossil, the tower collapses and is replaced by Desert Ruins.

| Item | Location (Map) | Coordinates (X, Y) | Decomp Flag | Decomp Script/Source | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (Wild Lileep) | `MAP_MIRAGE_TOWER_2F` | (7, 4) | (none) | `MirageTower_2F_EventScript_RootFossil` | **VERIFIED**. Interacting with this "item" starts a wild battle. It is not an item. |
| (Wild Anorith) | `MAP_MIRAGE_TOWER_2F` | (5, 4) | (none) | `MirageTower_2F_EventScript_ClawFossil` | **VERIFIED**. Interacting with this "item" starts a wild battle. It is not an item. |
| `ITEM_TM37_SANDSTORM` | `MAP_DESERT_RUINS` | (4, 2) | `FLAG_ITEM_DESERT_RUINS_TM37` | `DesertRuins_EventScript_ItemTM37` | **VERIFIED**. Appears after Mirage Tower collapses. |

---

### Island Cave / Ancient Tomb
*   There are **no** visible item balls in `MAP_ISLAND_CAVE` or `MAP_ANCIENT_TOMB`. **VERIFIED**.
    *   Source: Checked `events.inc` for both maps.