## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| Berries in Berry Master's Garden (Route 123, second row) | (17,21)=Tamato, (18,21)=Grepa, (19,21)=Pomeg | (17,21)=Grepa, (18,21)=Pomeg, (19,21)=Tamato | **CRITIQUE CORRECT** | `data/maps/Route123/scripts.inc` |
| Sootopolis City berry spot at (38,26) | A one-time gift from the NPC Kiri; not a tree. | A standard, plantable berry tree with a default Tamato Berry. | **CRITIQUE CORRECT** | `data/maps/SootopolisCity/scripts.inc` |
| Growth time for berries #9-13 (Razz, Bluk, etc.) | 120 minutes per stage (8 hours total) for "Razz to Lum". | 60 minutes per stage (4 hours total) for Razz, Bluk, Nanab, Wepear, Pinap. | **CRITIQUE CORRECT** | `src/data/field_berry.c`, `gBerryTemplates` |
| Berry yield calculation formula | `yield = (((max - min) * watered) / 4) + min` | The formula is `(((max - min) * (watered - 1)) / 3) + min` for 2-4 waterings, with different logic for 0-1. | **CRITIQUE CORRECT** | `src/field_berry.c`, `RollBerryYield` |
| Behavior of unpicked, fully grown berry trees | They are replaced by a new tree of the original default type. | They wither and disappear, leaving empty, tilled soil. | **CRITIQUE CORRECT** | `src/field_berry.c`, `BerryTreeGrow` and `ClearBerryTree` |
| Source of a one-time Razz Berry | A Gentleman on Route 111. | This NPC is nonexistent. The berry comes from a girl in the Lilycove Contest Lobby. | **CRITIQUE CORRECT** | `data/maps/Route111/scripts.inc`, `data/maps/LilycoveCity_ContestLobby/scripts.inc` |
| Berry given by the girl on Route 120 | `ITEM_RAZZ_BERRY` | `ITEM_ASPEAR_BERRY` | **CRITIQUE CORRECT** | `data/maps/Route120/scripts.inc` |
| Berries sold at the Battle Frontier Exchange Corner | Liechi, Ganlon, Salac, Petaya, and Apicot are sold for BP. | No berries are sold at the Battle Frontier Exchange Corner in Emerald. | **CRITIQUE CORRECT** | `src/battle_frontier_shop.c`, `sShopItems` |
| Berries obtainable via the Pickup ability | Leppa, Oran, Sitrus, and Lum berries. | Only `ITEM_LEPPA_BERRY` is obtainable via Pickup. | **CRITIQUE CORRECT** | `src/ability_battle_effects.c`, `gPickupLevelTables` |
| Source of Lansat and Starf Berries | Implied to be available and growable in the wild. | One-time gifts from Scott at the Battle Frontier for obtaining all Silver/Gold symbols. | **CRITIQUE CORRECT** | `data/maps/BattleFrontier_Scott_House/scripts.inc` |

## 2. CONFIRMED-GOOD CORE
*   **Berry Growth Stages:** A planted berry goes through 5 stages: Planted, Sprouted, Taller, Flowering, and Berries (harvestable). After harvesting, the soil becomes a sparkling patch.
*   **Watering:** A berry tree can be watered once per growth stage (Sprouted, Taller, Flowering) for a maximum of 4 watering credits (the initial planting counts as one). Watering increases the final yield.
*   **Yield Calculation:** The base yield is determined by the berry's `minYield`, `maxYield`, and the number of times it was watered. The formula for 2-4 waterings is `yield = (((max - min) * (watered - 1)) / 3) + min`. Yield for 0 waterings is `min`, and for 1 watering is `(min + max) / 2`. A small random factor is added.
*   **NPC Gifts:**
    *   **Berry Master (Route 123):** Gives two berries from a common pool, once per day.
    *   **Berry Master's Wife (Route 123):** Gives a rare berry (#31-35) once per day for a specific phrase:
        *   `GREAT BATTLE`: Spelon Berry
        *   `CHALLENGE CONTEST`: Pamtre Berry
        *   `OVERWHELMING LATIAS`: Watmel Berry
        *   `COOL LATIOS`: Durin Berry
        *   `SUPER HUSTLE`: Belue Berry
    *   **Flower Shop Girl (Route 104):** Gives one random berry (#1-8) daily.
    *   **Kiri (Sootopolis City):** One-time gift of either a Mago or Iapapa Berry.
    *   **Girl (Route 120):** One-time gift of an Aspear Berry.
*   **Special Berries:**
    *   **Lansat & Starf Berries:** One-time gifts from Scott at the Battle Frontier for earning all Gold and all Silver Symbols, respectively. They are not found in the wild.
    *   **Enigma Berry:** Data exists, but the item is unobtainable without an event distribution.
*   **In-Battle Effects:**
    *   Berries #1-5 cure a single status effect. Lum Berry (#9) cures any status condition. Persim Berry (#8) cures confusion.
    *   Oran Berry restores 10 HP. Sitrus Berry restores 30 HP when HP drops to 1/2 or less. Leppa Berry restores 10 PP.
    *   Figy-Iapapa berries (#11-15) restore 1/8 max HP but confuse Pokémon with certain natures.
    *   Liechi-Apicot berries (#36-40), Lansat, and Starf activate "in a pinch" (when HP drops to 1/4 or less) to raise a stat.

## 3. DO NOT USE
*   **DO NOT RELY ON THE "TREE DEATH (REGROWTH)" MECHANIC.** The note's claim that an unpicked tree respawns the original default berry is **FALSE**. An unpicked tree, whether wild or player-planted, will wither and disappear, leaving an empty patch of tilled soil. Any planted berry will be permanently lost, and the default wild berry will *not* return.
*   **The yield calculation formula in the note is incorrect.** It produces wrong results for partially watered trees. Use the formula in the `CONFIRMED-GOOD CORE` section.
*   **Berries are NOT sold at the Battle Frontier Exchange Corner.** This is a feature from later generations.
*   **The Pickup ability can only find Leppa Berries in Emerald.** Oran, Sitrus, and Lum berries are not in Emerald's Pickup item table.
*   **The Gentleman on Route 111 who gives a Razz Berry does not exist.** This NPC was hallucinated. A Razz Berry is given by an NPC in the Lilycove City Contest Lobby.
*   **The tables for berry locations and growth times in the original note contain multiple errors.** The Route 123 garden layout is wrong, a Sootopolis tree is missing, and growth times for berries like Razz are incorrect.
*   **The claims about obtaining berries from the Colosseum Bonus Disc or Pokémon Box are unresolvable** by inspecting the Emerald ROM and should be treated with caution.

## 4. CONFIDENCE
**95% - Very High.** I was able to settle all claims relating to the internal mechanics of the Pokémon Emerald ROM by cross-referencing the decompilation source code and data files. The only claims that remain unresolved are those that depend on interaction with external hardware or software (e.g., Pokémon Box, Colosseum Bonus Disc), as these cannot be verified from the game's code alone. For any developer working with the Emerald engine itself, the rulings and confirmed data here are reliable.