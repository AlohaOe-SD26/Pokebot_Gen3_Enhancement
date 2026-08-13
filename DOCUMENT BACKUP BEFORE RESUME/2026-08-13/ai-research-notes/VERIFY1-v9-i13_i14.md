## 1. WRONG — claims that are factually incorrect
*   **Claim:**
    > | Map Constant | Local Coords (X, Y) | Default Berry |
    > | :--- | :--- | :--- |
    > | `MAP_ROUTE123` | 17, 21 | `ITEM_TAMATO_BERRY` |
    > | `MAP_ROUTE123` | 18, 21 | `ITEM_GREPA_BERRY` |
    > | `MAP_ROUTE123` | 19, 21 | `ITEM_POMEG_BERRY` |
    **Actually:** The default berries in the second row of the Berry Master's garden are incorrect. The correct berries are Grepa, Pomeg, and Tamato, respectively.
    *   (17, 21) is `ITEM_GREPA_BERRY`
    *   (18, 21) is `ITEM_POMEG_BERRY`
    *   (19, 21) is `ITEM_TAMATO_BERRY`
    **Citation:** `data/maps/Route123/scripts.inc`, `Route123_EventScript_BerryTree4`, `Route123_EventScript_BerryTree5`, `Route123_EventScript_BerryTree6`.

*   **Claim:**
    > | Map Constant | Local Coords (X, Y) | Default Berry | Notes |
    > | :--- | :--- | :--- | :--- |
    > | `MAP_SOOTOPOLIS_CITY` | 38, 26 | `ITEM_TAMATO_BERRY` | Given by Kiri, see NPC section. Not a tree. |
    **Actually:** This is a standard, plantable berry tree. The default berry is `ITEM_TAMATO_BERRY`. Kiri is an NPC in `MAP_SOOTOPOLIS_CITY_HOUSE5` who gives a one-time berry gift; she is unrelated to this outdoor berry tree.
    **Citation:** `data/maps/SootopolisCity/map.json` object event at (38, 26) points to the script `SootopolisCity_EventScript_BerryTree1` in `data/maps/SootopolisCity/scripts.inc`.

*   **Claim:**
    > | Berry Type | Time per Stage (Minutes) | Total Growth Time (Hours) |
    > | :--- | :--- | :--- |
    > | Razz to Lum (#9-15) | 120 | 8 |
    **Actually:** This range is incorrect. `ITEM_RAZZ_BERRY`, `ITEM_BLUK_BERRY`, `ITEM_NANAB_BERRY`, `ITEM_WEPEAR_BERRY`, and `ITEM_PINAP_BERRY` all have a `growthTime` of 60 minutes per stage, for a total of 4 hours.
    **Citation:** `src/data/field_berry.c`, in `const struct Berry gBerryTemplates[]`.

*   **Claim:**
    > The formula is essentially:
    > `yield = (((maxYield - minYield) * (sBerryTree->watered)) / 4) + minYield`
    **Actually:** This formula is incorrect. The game's code has different logic for trees watered 0 or 1 times, and the main calculation for 2-4 waterings is `yield = (((maxYield - minYield) * (wateredCount - 1)) / 3) + minYield`. The note's formula produces incorrect yields for partially watered trees.
    **Citation:** `src/field_berry.c`, function `RollBerryYield`.

*   **Claim:**
    > If a fully grown tree (`BERRY_STAGE_BERRIES`) is not picked, it will eventually disappear and be replaced by a new, identical tree of the same type that was originally there.
    **Actually:** This is false. If a berry tree (either a default wild one or one planted by the player) is left unpicked for too long, it withers and disappears, leaving empty, tilled soil. It does *not* automatically respawn the original default berry.
    **Citation:** `src/field_berry.c`, function `BerryTreeGrow` calls `ClearBerryTree`, which sets the stage to `BERRY_STAGE_NO_BERRY` but does not reset the flag indicating the default berry has been picked.

*   **Claim:**
    > Gentleman | `MAP_ROUTE111` (30, 11) | `ITEM_RAZZ_BERRY` | One-time gift for talking to him.
    **Actually:** This NPC does not exist. There is no gentleman on Route 111 who gives a berry. A one-time `ITEM_RAZZ_BERRY` is given by a girl in the Lilycove City Contest Lobby.
    **Citation:** `data/maps/Route111/scripts.inc` shows no such NPC. The correct NPC is in `data/maps/LilycoveCity_ContestLobby/scripts.inc`, `LilycoveCity_ContestLobby_EventScript_Girl`.

*   **Claim:**
    > Girl | `MAP_ROUTE120` (25, 6) | `ITEM_RAZZ_BERRY` | One-time gift. Checks for a specific Pokémon in the party (Shedinja)...
    **Actually:** This NPC gives an `ITEM_ASPEAR_BERRY`, not a `ITEM_RAZZ_BERRY`.
    **Citation:** `data/maps/Route120/scripts.inc`, `Route120_EventScript_Girl`. The script contains `giveitem ITEM_ASPEAR_BERRY`.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald
*   **Claim:**
    > Battle Frontier Exchange Corner | ... | Liechi, Ganlon, Salac, Petaya, Apicot | Sold for Battle Points (BP). This is the only renewable source for these berries.
    **Actually:** The Battle Frontier Exchange Corner in Emerald does *not* sell any berries. This is a feature from Generation IV and later games.
    **Citation:** The merchandise list in `src/battle_frontier_shop.c`, `sShopItems[]`, contains only vitamins and held battle items, no berries.

*   **Claim:**
    > Pickup Ability | N/A | Leppa, Oran, Sitrus, Lum | Pokémon with the Pickup ability may find these items after a battle.
    **Actually:** In Pokémon Emerald, the only berry available via the Pickup ability is `ITEM_LEPPA_BERRY` (at levels 31-50). Oran, Sitrus, and Lum berries were added to Pickup tables in later generations.
    **Citation:** `src/ability_battle_effects.c`, `gPickupLevelTables`.

## 3. MISSING — things that should be in a note on this topic and are absent
*   **A second berry tree in Sootopolis City.** In addition to the Tamato Berry tree, there is another tree at coordinates (40, 26) that provides an `ITEM_SITRUS_BERRY`.
    **Citation:** `data/maps/SootopolisCity/scripts.inc`, `SootopolisCity_EventScript_BerryTree2`.
*   **The actual source of Lansat and Starf Berries.** These berries are not sold. They are obtained as one-time gifts from Scott in his house at the Battle Frontier after the player obtains all Silver Symbols (`ITEM_STARF_BERRY`) and all Gold Symbols (`ITEM_LANSAT_BERRY`).
    **Citation:** `data/maps/BattleFrontier_Scott_House/scripts.inc`, `BattleFrontier_ScottHouse_EventScript_Scott`.

## 4. UNVERIFIABLE — claims you cannot confirm either way
*   The claims regarding berry acquisition from the "Colosseum Bonus Disc (US)" and "Pokémon Box (Ruby & Sapphire)" are external to the Pokémon Emerald ROM and its code. While consistent with community knowledge, they cannot be verified by analyzing the decompilation.

## 5. VERDICT
**UNRELIABLE**

The note contains multiple, significant errors concerning core game mechanics (yield calculation, tree death/regrowth) and item acquisition (Battle Frontier, Pickup). While some data tables are correct, the errors in fundamental systems make it untrustworthy.

The single most dangerous claim to act on without checking is **the "Tree Death (Regrowth)" mechanic.** It falsely claims that an unpicked tree will eventually be "replaced by a new, identical tree of the same type that was originally there." A player relying on this might let their own planted, rare berries die, expecting the valuable default wild berry (e.g., the Lum Berry on Route 120) to respawn for free. In reality, their planted berry would be permanently lost, and the soil would simply become empty. This encourages behavior that directly leads to the loss of resources.