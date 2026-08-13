## 1. WRONG — claims that are factually incorrect

*   **Claim:**
    > `MAP_RUSTBORO_CITY` | `ITEM_HM01` | (23, 2) | `FLAG_ITEM_RUSTBORO_CITY_HM01`

    **Fact:** This is not a visible item ball. `ITEM_HM01` is given to the player by an NPC. The object at coordinates (23, 2) is a person, not an item ball.
    **Citation:** `data/maps/RustboroCity/events.inc` defines the object as `object_event 4, OBJ_EVENT_GFX_MAN_1, 23, 2, ...` which triggers the script `RustboroCity_EventScript_Cutter`. This script uses the `giveitem` command.

*   **Claim:**
    > | Location (Map Constant) | Item (Constant) | ... | Collection Flag |
    > | :--- | :--- | :--- | :--- |
    > | `MAP_BATTLE_FRONTIER_OUTSIDE_WEST` | `ITEM_HP_UP` | ... | `FLAG_ITEM_BATTLE_FRONTIER_HP_UP` |
    > | `MAP_BATTLE_FRONTIER_OUTSIDE_WEST` | `ITEM_PROTEIN` | ... | `FLAG_ITEM_BATTLE_FRONTIER_PROTEIN` |
    > | `MAP_BATTLE_FRONTIER_OUTSIDE_EAST` | `ITEM_LEFTOVERS`| ... | `FLAG_ITEM_BATTLE_FRONTIER_LEFTOVERS` |

    **Fact:** The flag names are incorrect. They are missing the map location specifier. The correct flags are `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_HP_UP`, `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_WEST_PROTEIN`, and `FLAG_ITEM_BATTLE_FRONTIER_OUTSIDE_EAST_LEFTOVERS`.
    **Citation:** `data/maps/BattleFrontier_OutsideWest/events.inc` and `data/maps/BattleFrontier_OutsideEast/events.inc`.

*   **Claim:**
    > `MAP_MT_PYRE_SUMMIT` | `ITEM_TM48_SKILL_SWAP` | (13, 19) | `FLAG_ITEM_MT_PYRE_SUMMIT_TM48`

    **Fact:** This is not a visible item ball. `ITEM_TM48_SKILL_SWAP` is given to the player by an NPC. The object at coordinates (13, 19) is a person, not an item ball.
    **Citation:** `data/maps/MtPyre_Summit/events.inc` defines the object as `object_event 2, OBJ_EVENT_GFX_OLD_WOMAN, 13, 19, ...` which triggers the script `MtPyre_Summit_EventScript_OldWoman`. This script uses the `giveitem` command.

*   **Claim:**
    > There are **three** visible item balls in `MAP_NEW_MAUVILLE_INSIDE`. However, they are all encounters, not items.
    > *   **(Voltorb)** at (11, 10)
    > *   **(Voltorb)** at (18, 12)
    > *   `ITEM_ULTRA_BALL` at (15, 2)

    **Fact:** This section is contradictory and incorrect. There are **four** visible item balls in New Mauville. Two are Voltorb encounters, one is an Electrode encounter, and one is a genuine `ITEM_ULTRA_BALL`. The note miscounts the total and misses the Electrode.
    **Citation:** `data/maps/NewMauville_Inside/events.inc` lists four objects with `OBJ_EVENT_GFX_ITEMBALL`:
    1.  `(11, 10)` -> `NewMauville_Inside_EventScript_ItemVoltorb1`
    2.  `(18, 12)` -> `NewMauville_Inside_EventScript_ItemVoltorb2`
    3.  `(15, 2)` -> `NewMauville_Inside_EventScript_ItemUltraBall`
    4.  `(14, 2)` -> `NewMauville_Inside_EventScript_ItemElectrode`

*   **Claim:**
    > (Wild Lileep) | `MAP_MIRAGE_TOWER_2F` | (7, 4) | (none) | `MirageTower_2F_EventScript_RootFossil` | **VERIFIED**. Interacting with this "item" starts a wild battle. It is not an item.
    > (Wild Anorith) | `MAP_MIRAGE_TOWER_2F` | (5, 4) | (none) | `MirageTower_2F_EventScript_ClawFossil` | **VERIFIED**. Interacting with this "item" starts a wild battle. It is not an item.

    **Fact:** This is completely wrong. Interacting with the fossils does **not** start a wild battle. The player is given the corresponding key item (`ITEM_ROOT_FOSSIL` or `ITEM_CLAW_FOSSIL`), and the tower then collapses.
    **Citation:** `data/maps/MirageTower_2F/scripts.inc` shows that both `MirageTower_2F_EventScript_RootFossil` and `MirageTower_2F_EventScript_ClawFossil` use the `giveitem` command, not `doitembattle` or `wildbattle`.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald

The note is generally good at correctly identifying differences between Ruby/Sapphire and Emerald. No errors of this type were found.

## 3. MISSING — things that should be in a note on this topic and are absent

*   **Meteor Falls:** The note is missing `ITEM_TM02_DRAGON_CLAW`.
    *   **Citation:** Found in `MAP_METEOR_FALLS_B1F_1R` at coordinates (24, 15). The object uses `FLAG_ITEM_METEOR_FALLS_B1F_1R_TM02`. See `data/maps/MeteorFalls_B1F_1R/events.inc`.
*   **Seafloor Cavern:** The note is missing `ITEM_TM11_SUNNY_DAY`.
    *   **Citation:** Found in `MAP_SEAFLOOR_CAVERN_ROOM9` at coordinates (9, 21). The object uses `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_9_TM11`. See `data/maps/SeafloorCavern_Room9/events.inc`.
*   **Victory Road:** The note is missing an `ITEM_FULL_HEAL`.
    *   **Citation:** Found in `MAP_VICTORY_ROAD_B1F` at coordinates (11, 27). The object uses `FLAG_ITEM_VICTORY_ROAD_B1F_FULL_HEAL`. See `data/maps/VictoryRoad_B1F/events.inc`.
*   **Abandoned Ship:** The note is missing an `ITEM_REVIVE`.
    *   **Citation:** Found in `MAP_ABANDONED_SHIP_ROOMS2_1F` at coordinates (1, 3). The object uses `FLAG_ITEM_ABANDONED_SHIP_ROOMS2_1F_REVIVE`. See `data/maps/AbandonedShip_Rooms2_1F/events.inc`.
*   **Abandoned Ship:** The note is missing a `ITEM_WATER_STONE`.
    *   **Citation:** Found in `MAP_ABANDONED_SHIP_ROOMS2_B1F` at coordinates (1, 3). The object uses `FLAG_ITEM_ABANDONED_SHIP_ROOMS2_B1F_WATER_STONE`. See `data/maps/AbandonedShip_Rooms2_B1F/events.inc`.

## 4. UNVERIFIABLE — claims you cannot confirm either way

All claims in the note are verifiable against the pokeemerald decompilation.

## 5. VERDICT

**SIGNIFICANT ERRORS**. The note misidentifies multiple NPC gifts as item balls, incorrectly describes the mechanics of a key one-time event (Mirage Tower), miscounts items in New Mauville, and is missing five items from major dungeons.

The single most dangerous claim to act on is that the **Mirage Tower fossils trigger wild battles and are not items**. This is false. A user acting on this information might ignore the fossils, not realizing it is their only chance to obtain one. This would lock them out of getting a fossil Pokémon and prevent the appearance of `TM37_SANDSTORM` in the Desert Ruins.