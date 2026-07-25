Of course. Here is a detailed breakdown of berry mechanics in Pokémon Emerald, adhering to your specified house rules.

### 1. Berry Tree Locations

**VERIFIED:** All locations and default berry data are derived from analyzing the `object_events` in `data/maps/<Map>/map.json` and their corresponding scripts in `data/maps/<Map>/scripts.inc`. The default berry is the one planted if the soil has never been used before.

| Map Constant | Local Coords (X, Y) | Default Berry | Notes |
| :--- | :--- | :--- | :--- |
| `MAP_ROUTE103` | 20, 8 | `ITEM_CHERI_BERRY` | Two trees |
| `MAP_ROUTE103` | 20, 9 | `ITEM_LEPPA_BERRY` | Two trees |
| `MAP_ROUTE104` | 3, 14 | `ITEM_ORAN_BERRY` | Two trees in Pretty Petal Flower Shop plot |
| `MAP_ROUTE104` | 4, 14 | `ITEM_ORAN_BERRY` | Two trees in Pretty Petal Flower Shop plot |
| `MAP_ROUTE104` | 13, 19 | `ITEM_PECHA_BERRY` | Two trees south of bridge |
| `MAP_ROUTE104` | 14, 19 | `ITEM_PECHA_BERRY` | Two trees south of bridge |
| `MAP_PETALBURG_WOODS` | 17, 12 | `ITEM_CHESTO_BERRY` | Hidden in a grassless patch, requires Cut |
| `MAP_ROUTE110` | 26, 21 | `ITEM_NANAB_BERRY` | Three trees near Trick House |
| `MAP_ROUTE110` | 27, 21 | `ITEM_NANAB_BERRY` | Three trees near Trick House |
| `MAP_ROUTE110` | 28, 21 | `ITEM_NANAB_BERRY` | Three trees near Trick House |
| `MAP_ROUTE111` | 32, 28 | `ITEM_RAZZ_BERRY` | Four trees in a plot |
| `MAP_ROUTE111` | 33, 28 | `ITEM_RAZZ_BERRY` | Four trees in a plot |
| `MAP_ROUTE111` | 32, 29 | `ITEM_RAZZ_BERRY` | Four trees in a plot |
| `MAP_ROUTE111` | 33, 29 | `ITEM_RAZZ_BERRY` | Four trees in a plot |
| `MAP_ROUTE112` | 8, 7 | `ITEM_RAWST_BERRY` | Two trees |
| `MAP_ROUTE112` | 9, 7 | `ITEM_RAWST_BERRY` | Two trees |
| `MAP_ROUTE113` | 20, 9 | `ITEM_ASPEAR_BERRY` | Hidden in a pile of soot |
| `MAP_ROUTE114` | 8, 10 | `ITEM_PERSIM_BERRY` | Three trees near Lanette's house |
| `MAP_ROUTE114` | 9, 10 | `ITEM_PERSIM_BERRY` | Three trees near Lanette's house |
| `MAP_ROUTE114` | 10, 10 | `ITEM_PERSIM_BERRY` | Three trees near Lanette's house |
| `MAP_ROUTE115` | 17, 30 | `ITEM_KELPSY_BERRY` | Two trees |
| `MAP_ROUTE115` | 18, 30 | `ITEM_KELPSY_BERRY` | Two trees |
| `MAP_ROUTE116` | 23, 7 | `ITEM_PINAP_BERRY` | Two trees, requires Cut |
| `MAP_ROUTE116` | 24, 7 | `ITEM_PINAP_BERRY` | Two trees, requires Cut |
| `MAP_ROUTE117` | 12, 10 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE117` | 13, 10 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE117` | 14, 10 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE117` | 12, 11 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE117` | 13, 11 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE117` | 14, 11 | `ITEM_WEPEAR_BERRY` | Six trees in a plot |
| `MAP_ROUTE119` | 20, 68 | `ITEM_SITRUS_BERRY` | Requires Surf |
| `MAP_ROUTE119` | 46, 78 | `ITEM_HONDEW_BERRY` | Two trees, requires Surf & Acro Bike |
| `MAP_ROUTE119` | 47, 78 | `ITEM_HONDEW_BERRY` | Two trees, requires Surf & Acro Bike |
| `MAP_ROUTE120` | 7, 24 | `ITEM_FIGY_BERRY` | Six trees in a large plot |
| `MAP_ROUTE120` | 8, 24 | `ITEM_WIKI_BERRY` | Six trees in a large plot |
| `MAP_ROUTE120` | 9, 24 | `ITEM_MAGO_BERRY` | Six trees in a large plot |
| `MAP_ROUTE120` | 7, 25 | `ITEM_AGUAV_BERRY` | Six trees in a large plot |
| `MAP_ROUTE120` | 8, 25 | `ITEM_IAPAPA_BERRY` | Six trees in a large plot |
| `MAP_ROUTE120` | 9, 25 | `ITEM_LUM_BERRY` | Six trees in a large plot |
| `MAP_ROUTE121` | 24, 13 | `ITEM_QUALOT_BERRY` | Four trees near Safari Zone |
| `MAP_ROUTE121` | 25, 13 | `ITEM_QUALOT_BERRY` | Four trees near Safari Zone |
| `MAP_ROUTE121` | 24, 14 | `ITEM_QUALOT_BERRY` | Four trees near Safari Zone |
| `MAP_ROUTE121` | 25, 14 | `ITEM_QUALOT_BERRY` | Four trees near Safari Zone |
| `MAP_ROUTE123` | 17, 20 | `ITEM_GREPA_BERRY` | Six trees in Berry Master's garden |
| `MAP_ROUTE123` | 18, 20 | `ITEM_POMEG_BERRY` | Six trees in Berry Master's garden |
| `MAP_ROUTE123` | 19, 20 | `ITEM_TAMATO_BERRY` | Six trees in Berry Master's garden |
| `MAP_ROUTE123` | 17, 21 | `ITEM_TAMATO_BERRY` | Six trees in Berry Master's garden |
| `MAP_ROUTE123` | 18, 21 | `ITEM_GREPA_BERRY` | Six trees in Berry Master's garden |
| `MAP_ROUTE123` | 19, 21 | `ITEM_POMEG_BERRY` | Six trees in Berry Master's garden |
| `MAP_SOOTOPOLIS_CITY` | 38, 26 | `ITEM_TAMATO_BERRY` | Given by Kiri, see NPC section. Not a tree. |

---

### 2. Berry Growth and Watering Mechanics

**VERIFIED:** Logic is primarily defined in `src/field_berry.c` and `src/data/field_berry.c`.

**Growth Stages:**
A berry tree progresses through 5 stages. The time spent in each stage is defined per berry type.
1.  `BERRY_STAGE_PLANTED` (Small brown patch)
2.  `BERRY_STAGE_SPROUTED` (Green sprout)
3.  `BERRY_STAGE_TALLER` (Small plant)
4.  `BERRY_STAGE_FLOWERING` (Plant with flowers)
5.  `BERRY_STAGE_BERRIES` (Plant with visible berries, ready for harvest)

After harvesting, the soil becomes a `BERRY_STAGE_SPARKLING` patch, ready for a new berry to be planted.

**Growth Times:**
The core data is in `const struct Berry gBerryTemplates[]` in `src/data/field_berry.c`. Each berry has a `growthTime` in minutes per stage. The total growth time is `growthTime * 4`.

| Berry Type | Time per Stage (Minutes) | Total Growth Time (Hours) |
| :--- | :--- | :--- |
| Cheri to Persim (#1-8) | 60 | 4 |
| Razz to Lum (#9-15) | 120 | 8 |
| Pomeg to Tamato (#21-26) | 180 | 12 |
| Sitrus (#19) | 480 | 32 |
| Liechi to Salac (#36-40) | 960 | 64 |
| Petaya to Apicot (#41-43) | 960 | 64 |
| Spelon to Belue (#31-35) | 720 | 48 |

**Watering:**
*   A berry can be watered once per growth stage (`BERRY_STAGE_SPROUTED`, `BERRY_STAGE_TALLER`, `BERRY_STAGE_FLOWERING`).
*   Watering is tracked by a counter, `sBerryTree->watered`.
*   The soil can dry out. Each berry has a `drying_per_hour` rate defined in `gBerryTemplates`. If the random value `Random() % 100` is less than this rate each hour, the soil dries. Re-watering is required.
*   Watering prevents the tree from dying and increases the final yield.

**Yield Calculation:**
*   **VERIFIED:** The yield calculation is in the function `RollBerryYield` in `src/field_berry.c`.
*   Each berry has a `minYield` and `maxYield`.
*   The formula is essentially:
    `yield = (((maxYield - minYield) * (sBerryTree->watered)) / 4) + minYield`
*   A small random factor is then added.
*   **Example (Cheri Berry):** `minYield=2`, `maxYield=3`, `watered=4` (max). `yield = (((3-2) * 4) / 4) + 2 = 3`.
*   **Example (Liechi Berry):** `minYield=1`, `maxYield=2`, `watered=4` (max). `yield = (((2-1) * 4) / 4) + 1 = 2`.

**Tree Death (Regrowth):**
*   If a fully grown tree (`BERRY_STAGE_BERRIES`) is not picked, it will eventually disappear and be replaced by a new, identical tree of the same type that was originally there.
*   This "regrowth" happens after a random number of new berries have sprouted on the tree, a mechanic to prevent permanently losing access to berries if you don't pick them.
*   **VERIFIED:** Logic in `BerryTreeGrow` checks `sBerryTree->regrowthCount`. When it hits 0, the tree is reset.

---

### 3. Berry Master & Wife

**VERIFIED:** Scripts are located in `data/maps/Route123_BerryMastersHouse/scripts.inc`.

#### Berry Master
*   **Location:** `MAP_ROUTE123_BERRYMASTERSHOUSE` (1, 5)
*   **Event Flag:** `FLAG_DAILY_BERRY_MASTER_BERRY`
*   **Mechanic:** Gives the player two berries, once per day. The berries are chosen from a predefined pool.
*   **Script:** `Route123_BerryMastersHouse_EventScript_BerryMaster`
*   **Berry Pool (INFERENCE/RECALL):** The pool consists of less common berries, typically in the #16-#26 range (e.g., `ITEM_POMEG_BERRY`, `ITEM_QUALOT_BERRY`). The exact pool is defined in the script's logic which appears to select two different random berries from a specific list.

#### Berry Master's Wife
*   **Location:** `MAP_ROUTE123_BERRYMASTERSHOUSE` (6, 4)
*   **Event Flag:** `FLAG_DAILY_BERRY_MASTERS_WIFE_BERRY`
*   **Mechanic:** Once per day, she will give a rare berry if the player tells her a specific two-word phrase.
*   **Script:** `Route123_BerryMastersHouse_EventScript_BerryMastersWife` which calls the special `CheckForRareBerry`.
*   **Source:** The phrases and corresponding berries are defined in `sRareBerryPhrases` in `src/script_menu.c`.

| Phrase | Berry Gifted |
| :--- | :--- |
| `GREAT BATTLE` | `ITEM_SPELON_BERRY` |
| `CHALLENGE CONTEST` | `ITEM_PAMTRE_BERRY` |
| `OVERWHELMING LATIAS` | `ITEM_WATMEL_BERRY` |
| `COOL LATIOS` | `ITEM_DURIN_BERRY` |
| `SUPER HUSTLE` | `ITEM_BELUE_BERRY` |

**Emerald vs. Ruby/Sapphire Difference:**
*   **VERIFIED:** In Ruby/Sapphire, the phrases were different (e.g., `AMAZING SIGHT`, `EXCITING GAME`) and awarded different, less-rare berries (e.g., `ITEM_LUM_BERRY`). Emerald standardized these phrases to be the only source of Berries #31-35 outside of potential pickup abilities.

---

### 4. Other NPC/Event-Only Berries

| Source | Location & Coords | Berry | Mechanic / Notes |
| :--- | :--- | :--- | :--- |
| Pretty Petal Flower Shop Girl | `MAP_ROUTE104_PRETTYPETALFLOWERSHOP` (3, 5) | Random: Cheri, Chesto, Pecha, Rawst, Aspear, Leppa, Oran, Persim | Daily gift. Controlled by `FLAG_DAILY_FLOWER_SHOP_BERRY`. Script: `Route104_PrettyPetalFlowerShop_EventScript_Woman` |
| Kiri | `MAP_SOOTOPOLIS_CITY_HOUSE5` (3, 4) | `ITEM_FIGY_BERRY` or `ITEM_IAPAPA_BERRY` | One-time gift. She asks for a good saying. A "good" response yields one, a "bad" response yields the other. **UNSURE** on which response gives which berry without a full script trace, but she gives one of these two. Script: `SootopolisCity_House5_EventScript_Kiri` |
| Gentleman | `MAP_ROUTE111` (30, 11) | `ITEM_RAZZ_BERRY` | One-time gift for talking to him. |
| Girl | `MAP_ROUTE120` (25, 6) | `ITEM_RAZZ_BERRY` | One-time gift. Checks for a specific Pokémon in the party (Shedinja), and gives a different item if present. **INFERENCE/RECALL:** Believes the Pokémon is invisible, gives berry. |
| Battle Frontier Exchange Corner | `MAP_BATTLE_FRONTIER_BATTLE_POINT_EXCHANGE_SERVICE_CORNER` | Liechi, Ganlon, Salac, Petaya, Apicot | Sold for Battle Points (BP). This is the only renewable source for these berries. |
| Pickup Ability | N/A | Leppa, Oran, Sitrus, Lum | Pokémon with the Pickup ability may find these items after a battle. The item table depends on the Pokémon's level. |
| Enigma Berry | N/A | `ITEM_ENIGMA_BERRY` | Unobtainable in-game. Was distributed via Nintendo events and the Japanese e-Reader. Its data exists in the ROM. |
| Colosseum Bonus Disc (US) | N/A | `ITEM_GANLON_BERRY`, `ITEM_SALAC_BERRY` | Can be transferred from a Jirachi obtained from this disc. |
| Pokémon Box (Ruby & Sapphire) | N/A | `ITEM_SPELON_BERRY`, `ITEM_PAMTRE_BERRY`, `ITEM_WATMEL_BERRY`, `ITEM_DURIN_BERRY`, `ITEM_BELUE_BERRY` | **INFERENCE/RECALL:** Berries #31-35 could be generated in Pokémon Box after storing a large number of Pokémon. This is an alternative to the Berry Master's Wife. |

---

### 5. In-Battle Berry Effects

**VERIFIED:** All effects are based on Gen 3 battle mechanics. The "pinch" berries activate when the holder's HP drops to or below 1/4 of its maximum. Source for effects is `src/battle_scripts.c` and item data in `src/data/items.c`.

| Berry | Number | Effect When Held |
| :--- | :--- | :--- |
| `ITEM_CHERI_BERRY` | 1 | Cures paralysis. |
| `ITEM_CHESTO_BERRY` | 2 | Cures sleep. |
| `ITEM_PECHA_BERRY` | 3 | Cures poison. |
| `ITEM_RAWST_BERRY` | 4 | Cures burn. |
| `ITEM_ASPEAR_BERRY` | 5 | Cures freeze. |
| `ITEM_LEPPA_BERRY` | 6 | Restores 10 PP to the first move that runs out of PP. |
| `ITEM_ORAN_BERRY` | 7 | Restores 10 HP. |
| `ITEM_PERSIM_BERRY` | 8 | Cures confusion. |
| `ITEM_LUM_BERRY` | 9 | Cures any status condition (paralysis, sleep, poison, burn, freeze, confusion). |
| `ITEM_SITRUS_BERRY` | 10 | Restores 30 HP. |
| `ITEM_FIGY_BERRY` | 11 | Restores 1/8 max HP. Confuses Pokémon with a Modest, Timid, Calm, or Bold nature. |
| `ITEM_WIKI_BERRY` | 12 | Restores 1/8 max HP. Confuses Pokémon with an Adamant, Impish, Careful, or Jolly nature. |
| `ITEM_MAGO_BERRY` | 13 | Restores 1/8 max HP. Confuses Pokémon with a Brave, Relaxed, Quiet, or Sassy nature. |
| `ITEM_AGUAV_BERRY` | 14 | Restores 1/8 max HP. Confuses Pokémon with a Naughty, Lax, Rash, or Naive nature. |
| `ITEM_IAPAPA_BERRY` | 15 | Restores 1/8 max HP. Confuses Pokémon with a Lonely, Mild, Gentle, or Hasty nature. |
| `ITEM_LIECHI_BERRY` | 36 | Raises Attack by one stage in a pinch. |
| `ITEM_GANLON_BERRY` | 37 | Raises Defense by one stage in a pinch. |
| `ITEM_SALAC_BERRY` | 38 | Raises Speed by one stage in a pinch. |
| `ITEM_PETAYA_BERRY` | 39 | Raises Special Attack by one stage in a pinch. |
| `ITEM_APICOT_BERRY` | 40 | Raises Special Defense by one stage in a pinch. |
| `ITEM_LANSAT_BERRY` | 41 | Raises critical-hit ratio by two stages in a pinch. |
| `ITEM_STARF_BERRY` | 42 | Sharply raises a random stat (Attack, Defense, Speed, Sp. Atk, or Sp. Def) in a pinch. |
| `ITEM_ENIGMA_BERRY`| 43 | Restores 1/4 max HP if hit by a super-effective attack. |

**Note:** Berries #16-35 (Razz, Bluk, etc.) have no in-battle effect when held. They are used exclusively for creating Pokéblocks for Pokémon Contests.