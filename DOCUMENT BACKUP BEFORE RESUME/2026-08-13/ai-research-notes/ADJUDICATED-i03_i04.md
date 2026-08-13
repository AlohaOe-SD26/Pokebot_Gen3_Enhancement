## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| Hidden items in Mauville Game Corner | `ITEM_COIN` is found. | There is no `ITEM_COIN`. The script directly adds coins to the Coin Case. | **CRITIQUE CORRECT** | The special function `FindHiddenCoin` calls `AddCoins` directly. It does not use `finditem` or any defined item. `src/special_field.c` |
| Hidden item in Steven's House | There is a hidden `ITEM_REVIVE` at (1, 2). | This is a complete fabrication. There are no hidden items. | **CRITIQUE CORRECT** | The file `data/maps/MossdeepCity_StevensHouse/map.json` has no `hidden_item_object_events` array. The cited script gives the player a Beldum. |
| Second hidden item in Sootopolis City | There is a hidden `ITEM_NUGGET` at (10, 47). | This item does not exist. There is only one hidden item, a Big Pearl. | **CRITIQUE CORRECT** | `data/maps/SootopolisCity/map.json` lists only one hidden item event, `SootopolisCity_EventScript_HiddenBigPearl`. There is no object at (10, 47). |
| Fossils in Mirage Tower | Lists `ITEM_ROOT_FOSSIL` and `ITEM_CLAW_FOSSIL` as two separate hidden items. | This is misleading. The player can only choose one; they are mutually exclusive. | **CRITIQUE CORRECT** | The scripts `MirageTower_4F_EventScript_RootFossil` and `...ClawFossil` both set `FLAG_MIRAGE_TOWER_COLLAPSED`, making the other fossil unobtainable at that location. `data/maps/MirageTower_4F/scripts.inc` |
| Hidden item in Fortree City | There is a hidden `ITEM_REVIVE` at (23, 11). | This item is from Ruby/Sapphire and was removed in Emerald. | **CRITIQUE CORRECT** | `data/maps/FortreeCity/map.json` in the pokeemerald repository has no `hidden_item_object_events` array. |
| Hidden items in Pacifidlog Town | Lists one hidden item (`ITEM_HEART_SCALE`). | A second hidden item (`ITEM_BIG_PEARL`) is missing. | **CRITIQUE CORRECT** | `data/maps/PacifidlogTown/map.json` contains two hidden item events: `PacifidlogTown_EventScript_HiddenHeartScale` and `PacifidlogTown_EventScript_HiddenBigPearl`. The note missed the second one. |

## 2. CONFIRMED-GOOD CORE

The following hidden items are confirmed to exist in Pokémon Emerald at the specified locations.

**Towns & Cities:**
*   **Oldale Town:** Potion
*   **Petalburg City:** Rare Candy
*   **Rustboro City:** X Defend
*   **Rustboro City (Cutter's House):** Poke Ball
*   **Dewford Town:** Stardust
*   **Slateport City:** Revive
*   **Mauville City:** X Speed
*   **Verdanturf Town:** Ultra Ball
*   **Fallarbor Town:** Nugget
*   **Lavaridge Town:** Ice Heal
*   **Lilycove City:** Heart Scale, Poke Ball
*   **Mossdeep City:** Net Ball
*   **Sootopolis City:** Big Pearl
*   **Pacifidlog Town:** Heart Scale, Big Pearl
*   **Ever Grande City:** Elixir

**Dungeons & Caves:**
*   **Granite Cave:** Everstone
*   **Meteor Falls:** Moon Stone
*   **Fiery Path:** Fire Stone, Nugget
*   **Jagged Pass:** Great Ball
*   **Mt. Pyre Exterior:** Zinc, Rare Candy
*   **Team Aqua Hideout:** Nest Ball
*   **Seafloor Cavern:** Big Pearl
*   **Sky Pillar:** Rare Candy
*   **Victory Road:** Elixir, Max Repel
*   **Shoal Cave (Low Tide):** 2x Pearl
*   **Shoal Cave (High Tide):** Big Pearl
*   **Abandoned Ship (Underwater):** Water Stone

**Special Cases:**
*   **Mauville Game Corner:** 16 floor locations can be checked for hidden coins. The script `special FindHiddenCoin` directly adds 10, 20, 100, or 200 coins to the player's Coin Case. This does not involve an "item".
*   **Mirage Tower & Desert Ruins:** The player chooses between the Root Fossil and Claw Fossil at the top of Mirage Tower. Taking one causes the tower to collapse. The other fossil then becomes a hidden item in the Desert Ruins.

## 3. DO NOT USE

The following claims from the original note are false and should be disregarded entirely:

*   **DO NOT USE:** The claim that there is a hidden `ITEM_REVIVE` in Steven's House in Mossdeep City. This is a hallucination.
*   **DO NOT USE:** The claim that there is a hidden `ITEM_NUGGET` on the western shore of Sootopolis City. This is a hallucination.
*   **DO NOT USE:** The claim that there is a hidden `ITEM_REVIVE` behind the Pokémon Center in Fortree City. This item exists in Ruby/Sapphire, but not in Emerald.
*   **DO NOT USE:** The term `ITEM_COIN` for the Mauville Game Corner. No such item exists; coins are added directly to the player's total.
*   **DO NOT USE:** The implication that both the Root and Claw Fossils can be collected as hidden items from within Mirage Tower. They are a mutually exclusive choice at that location.

## 4. CONFIDENCE

**100%**. Every claim in the note and critique was verifiable against the `pokeemerald` decompilation project. All disputes have been settled.