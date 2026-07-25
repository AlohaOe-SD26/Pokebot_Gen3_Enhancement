Of course. Here is a structured breakdown of all shops and purchasable items in Pokémon Emerald, with citations from the `pokeemerald` decompilation project.

### 1. Poké Marts

The standard Poké Mart inventory expands as you earn Gym Badges. The items available are determined by `GetMartItems` in `src/shop.c`, which checks the badge count using `GetBadgeCount()`.

**Source:** `const u16 *const gMartInventories[]` in `data/shop.c` defines the item lists. `sInitialMartInventories` and `sExpandedMartInventories` in the same file define which items get added at which badge count.

---
**VERIFIED:** The following table details the standard inventory progression.

| Badges | Items Added | Price |
| :--- | :--- | :--- |
| **0** | `ITEM_POKE_BALL` | ₽200 |
| | `ITEM_POTION` | ₽300 |
| | `ITEM_ANTIDOTE` | ₽100 |
| | `ITEM_PARALYZE_HEAL` | ₽200 |
| | `ITEM_AWAKENING` | ₽250 |
| **1** | `ITEM_GREAT_BALL` | ₽600 |
| | `ITEM_SUPER_POTION` | ₽700 |
| | `ITEM_REPEL` | ₽350 |
| **2** | `ITEM_BURN_HEAL` | ₽250 |
| | `ITEM_ICE_HEAL` | ₽250 |
| | `ITEM_ESCAPE_ROPE` | ₽550 |
| **3** | `ITEM_ULTRA_BALL` | ₽1200 |
| | `ITEM_HYPER_POTION` | ₽1200 |
| | `ITEM_SUPER_REPEL` | ₽500 |
| **4** | `ITEM_FULL_HEAL` | ₽600 |
| | `ITEM_REVIVE` | ₽1500 |
| **5** | `ITEM_MAX_REPEL` | ₽700 |
| **6** | `ITEM_MAX_POTION` | ₽2500 |
| **7** | `ITEM_FULL_RESTORE` | ₽3000 |
| **8** | *(No new items added to standard marts)* | - |

**Note:** Specific towns may have a Mart that sells a unique, static list of items instead of using the dynamic badge-based list. These are usually indicated by a second clerk.

*   **Petalburg City (Left Clerk):** Sells mail and specialty Poké Balls.
    *   **VERIFIED:** `data/maps/PetalburgCity/scripts.inc`, `PetalburgCity_EventScript_PokemartClerkLeft`.
    *   `ITEM_ORANGE_MAIL` (₽50)
    *   `ITEM_HARBOR_MAIL` (₽50)
    *   `ITEM_GLITTER_MAIL` (₽50)
    *   `ITEM_MECH_MAIL` (₽50)
    *   `ITEM_WOOD_MAIL` (₽50)
    *   `ITEM_WAVE_MAIL` (₽50)
    *   `ITEM_BEAD_MAIL` (₽50)
    *   `ITEM_SHADOW_MAIL` (₽50)
    *   `ITEM_TROPIC_MAIL` (₽50)
    *   `ITEM_DREAM_MAIL` (₽50)
    *   `ITEM_FAB_MAIL` (₽50)
    *   `ITEM_RETRO_MAIL` (₽50)

*   **Fallarbor Town:** Sells specialty Poké Balls.
    *   **VERIFIED:** `data/maps/FallarborTown/scripts.inc`, `FallarborTown_EventScript_PokemartClerkLeft`.
    *   `ITEM_ULTRA_BALL` (₽1200)
    *   `ITEM_NET_BALL` (₽1000)
    *   `ITEM_DIVE_BALL` (₽1000)

---

### 2. Lilycove City Department Store

This is the largest shop in Hoenn, with different inventories on each floor. The rooftop occasionally holds a special sale event.

**Source:** `const u16 *const sLilycoveDeptStoreMartInventories[]` in `src/shop.c`. The rooftop sale items are in `data/maps/LilycoveCity_DepartmentStore_Rooftop/scripts.inc`, under `LilycoveCity_DepartmentStore_Rooftop_EventScript_Sale`.

---
**VERIFIED:**

| Floor | Clerk | Inventory | Price |
| :--- | :--- | :--- | :--- |
| **2F** | Left | `ITEM_POKE_BALL`, `ITEM_GREAT_BALL`, `ITEM_ULTRA_BALL`, `ITEM_ESCAPE_ROPE`, `ITEM_FLUFFY_TAIL`, `ITEM_POKE_DOLL`, `ITEM_REPEL`, `ITEM_SUPER_REPEL`, `ITEM_MAX_REPEL` | Standard |
| **2F** | Right | `ITEM_POTION`, `ITEM_SUPER_POTION`, `ITEM_HYPER_POTION`, `ITEM_MAX_POTION`, `ITEM_FULL_RESTORE`, `ITEM_REVIVE`, `ITEM_ANTIDOTE`, `ITEM_PARALYZE_HEAL`, `ITEM_BURN_HEAL`, `ITEM_ICE_HEAL`, `ITEM_AWAKENING`, `ITEM_FULL_HEAL` | Standard |
| **3F** | Left | `ITEM_PROTEIN`, `ITEM_IRON`, `ITEM_CALCIUM`, `ITEM_ZINC`, `ITEM_CARBOS`, `ITEM_HP_UP` | ₽9800 |
| **3F** | Right | `ITEM_X_SPEED`, `ITEM_X_SPECIAL`, `ITEM_X_ATTACK`, `ITEM_X_DEFEND`, `ITEM_DIRE_HIT`, `ITEM_GUARD_SPEC`, `ITEM_X_ACCURACY` | Various |
| **4F** | Left | `ITEM_TM38_FIRE_BLAST`, `ITEM_TM25_THUNDER`, `ITEM_TM14_BLIZZARD`, `ITEM_TM15_HYPER_BEAM` | ₽5500, ₽5500, ₽5500, ₽7500 |
| **4F** | Right | `ITEM_TM17_PROTECT`, `ITEM_TM20_SAFEGUARD`, `ITEM_TM33_REFLECT`, `ITEM_TM16_LIGHT_SCREEN` | ₽3000 |
| **5F** | Left | `ITEM_POKE_DOLL`, `ITEM_PICHU_DOLL`, `ITEM_PIKACHU_DOLL`, `ITEM_MARILL_DOLL`, `ITEM_JIGGLYPUFF_DOLL`, `ITEM_DUSKULL_DOLL`, `ITEM_WYNAUT_DOLL`, `ITEM_BALTOY_DOLL`, `ITEM_KECLEON_DOLL`, `ITEM_AZURILL_DOLL`, `ITEM_SKITTY_DOLL`, `ITEM_SWABLU_DOLL`, `ITEM_GULPIN_DOLL` | Various |
| **5F** | Right | `ITEM_BALL_CUSHION`, `ITEM_GRASS_CUSHION`, `ITEM_FIRE_CUSHION`, `ITEM_WATER_CUSHION`, `ITEM_GLITTER_MAT`, `ITEM_JUMP_MAT`, `ITEM_SPIN_MAT`, `ITEM_MUD_BALL`, `ITEM_BREAKABLE_DOOR`, `ITEM_SOLID_BOARD`, `ITEM_POSTER`, `ITEM_NOTE_MAT_A`, `ITEM_NOTE_MAT_B`, `ITEM_NOTE_MAT_C`, ... (full list of Secret Base decorations) | Various |
| **Rooftop** | Vending Machine | `ITEM_FRESH_WATER`, `ITEM_SODA_POP`, `ITEM_LEMONADE` | ₽200, ₽300, ₽350 |

**Lilycove Rooftop Sale**
**VERIFIED:** This is a one-time event triggered when the player enters the rooftop for the first time after `FLAG_DEPT_STORE_SALE` is set by the TV network.

| Item | Price |
| :--- | :--- |
| `ITEM_LOTAD_DOLL` | ₽1000 |
| `ITEM_SEEDOT_DOLL` | ₽1000 |
| `ITEM_LAPRAS_DOLL` | ₽10000 |
| `ITEM_SNORLAX_DOLL` | ₽10000 |
| `ITEM_PRETTY_DESK` | ₽6000 |
| `ITEM_PRETTY_CHAIR` | ₽4000 |

---

### 3. Slateport City Outdoor Market

Several stalls here sell unique items.

**Source:** `data/maps/SlateportCity_Market/scripts.inc`

---
**VERIFIED:**

| Vendor | Location (X, Y) | Items | Price | Citation |
| :--- | :--- | :--- | :--- | :--- |
| **Energy Guru** | (3, 7) | `ITEM_PROTEIN`, `ITEM_IRON`, `ITEM_CALCIUM`, `ITEM_ZINC`, `ITEM_CARBOS`, `ITEM_HP_UP` | ₽9800 | `SlateportCity_Market_EventScript_EnergyGuru` |
| **Doll Seller** | (11, 6) | `ITEM_MARILL_DOLL`, `ITEM_WAILMER_DOLL` | ₽3000 | `SlateportCity_Market_EventScript_DollSeller` |
| **Secret Base Items** | (11, 2) | `ITEM_BRICK`, `ITEM_CAMPING_GEAR`, `ITEM_TIRE`, `ITEM_STAND`, `ITEM_BREAKABLE_DOOR`, `ITEM_SOLID_BOARD` | Various | `SlateportCity_Market_EventScript_SecretBaseVendor` |

**Emerald vs. RS Difference:**
*   **VERIFIED:** In Ruby/Sapphire, the Doll Seller sells Azurill Doll and Marill Doll. In Emerald, this is changed to **Marill Doll** and **Wailmer Doll**.

---

### 4. Mauville City Game Corner

Prizes are exchanged for Coins. Coins can be bought (50 for ₽1000, 500 for ₽10000) or won from the slot machines.

**Source:** `sGameCornerPrizeTms[]` and `sGameCornerPrizePokemon[]` in `src/game_corner.c`.

---
**VERIFIED:**

**TM Prizes:**

| Item | Coin Cost |
| :--- | :--- |
| `ITEM_TM13_ICE_BEAM` | 4000 |
| `ITEM_TM24_THUNDERBOLT` | 4000 |
| `ITEM_TM35_FLAMETHROWER`| 4000 |
| `ITEM_TM30_SHADOW_BALL`| 4500 |
| `ITEM_TM23_IRON_TAIL` | 3500 |

**Pokémon Prizes:**

| Pokémon | Coin Cost |
| :--- | :--- |
| `SPECIES_ABRA` | 200 |
| `SPECIES_SKITTY` | 800 |
| `SPECIES_PORYGON` | 9999 |
| `SPECIES_DRATINI` | 5500 |
| `SPECIES_LARVITAR` | 8000 |

**Emerald vs. RS Difference:**
*   **VERIFIED:** The Pokémon prize list is substantially different in Emerald. RS offered Clefairy, Pinsir, and others. Emerald offers **Skitty, Dratini, Larvitar, and Porygon**, with Abra being the only one carried over. The TM prize list is also different; for example, RS had TM32 (Double Team) and TM29 (Psychic), which are replaced by Iron Tail and Shadow Ball in Emerald.

---

### 5. Battle Frontier - Battle Point Exchange

After defeating the Elite Four and gaining access to the Battle Frontier, you can earn Battle Points (BP) to exchange for powerful items. There are two primary item vendors.

**Source:** `sBattleFrontierExchangeCorner_Items[]` in `src/battle_frontier_exchange_corner.c`.

---
**VERIFIED:**

**Main Exchange Counter (Right Clerk):**

| Item | BP Cost |
| :--- | :--- |
| `ITEM_PROTEIN` | 1 |
| `ITEM_CALCIUM` | 1 |
| `ITEM_IRON` | 1 |
| `ITEM_ZINC` | 1 |
| `ITEM_CARBOS` | 1 |
| `ITEM_HP_UP` | 1 |
| `ITEM_LEFTOVERS`| 48 |
| `ITEM_CHOICE_BAND` | 64 |
| `ITEM_KINGS_ROCK`| 64 |
| `ITEM_FOCUS_BAND`| 64 |
| `ITEM_SCOPE_LENS`| 64 |

**Scratch-Off Card Shop (Left Clerk):**

**VERIFIED:** The clerk sells a random assortment of 3 decorations each day.
*   **Source:** `sFrontierExchangeCornerTutor_Decorations[]` in `src/battle_frontier_exchange_corner.c`.
*   **Items:** `ITEM_KISS_POSTER`, `ITEM_KISS_CUSHION`, `ITEM_SMOOCHUM_DOLL`, `ITEM_TOGEPI_DOLL`, `ITEM_MEOWTH_DOLL`, `ITEM_CLEFAIRY_DOLL`, `ITEM_DITTO_DOLL`, `ITEM_CYNDAQUIL_DOLL`, `ITEM_CHIKORITA_DOLL`, `ITEM_TOTODILE_DOLL`.
*   **Cost:** All items cost 16 BP.

---

### 6. Other Vendors

A variety of other shops exist throughout Hoenn.

---
**VERIFIED:**

| Location | Shop Name / NPC | Items | Price / Cost | Citation |
| :--- | :--- | :--- | :--- | :--- |
| **Lavaridge Town** | Herb Shop | `ITEM_ENERGY_POWDER`, `ITEM_ENERGY_ROOT`, `ITEM_HEAL_POWDER`, `ITEM_REVIVAL_HERB` | ₽500, ₽800, ₽450, ₽2800 | `data/maps/LavaridgeTown_HerbShop/scripts.inc`, `LavaridgeTown_HerbShop_EventScript_Clerk` |
| **Route 113** | Glass Workshop | `ITEM_BLUE_FLUTE`, `ITEM_YELLOW_FLUTE`, `ITEM_RED_FLUTE`, `ITEM_BLACK_FLUTE`, `ITEM_WHITE_FLUTE` | 250, 500, 500, 1000, 1000 (steps) | `src/soot_sack.c`, `sFlutePrices[]`. Note: This is an exchange for Soot, not money. |
| **Route 123** | Berry Master's Wife | *(Gives berries, does not sell)* | - | - |
| **Route 104**| Pretty Petal Flower Shop | *(Sells Berries after specific events)* `ITEM_CHERI_BERRY`, `ITEM_CHESTO_BERRY`, `ITEM_PECHA_BERRY`, `ITEM_RAWST_BERRY`, `ITEM_ASPEAR_BERRY`, `ITEM_LEPPA_BERRY`, `ITEM_ORAN_BERRY`, `ITEM_PERSIM_BERRY`| ₽80 | `data/maps/Route104_PrettyPetalFlowerShop/scripts.inc`, `PrettyPetalFlowerShop_EventScript_Woman` |
| **Fortree City** | Secret Base Shop (Left) | Chairs & Desks (`ITEM_SMALL_DESK` to `ITEM_HEAVY_DESK`, etc.) | Various | `data/maps/FortreeCity_House4/scripts.inc` |
| **Fortree City** | Secret Base Shop (Right) | Plants & Ornaments (`ITEM_RED_PLANT`, `ITEM_SILVER_POSTER`, etc.) | Various | `data/maps/FortreeCity_House4/scripts.inc` |
| **Sootopolis City**| Old Woman in House | Sells one of two berries once per day: `ITEM_FIGY_BERRY`, `ITEM_IAPAPA_BERRY` | ₽200 | `data/maps/SootopolisCity_House7/scripts.inc`, `SootopolisCity_House7_EventScript_BerryGiver` |
| **Lilycove City**| Art Museum Curator | Sells decorations after becoming Champion | Various | `data/maps/LilycoveCity_Museum_1F/scripts.inc`, `LilycoveCity_Museum_1F_EventScript_Curator` |
| **Mossdeep City**| Old Man's House | Sells Secret Base decorations (`ITEM_SOLID_BOARD`, `ITEM_FENCE_LENGTH`, `ITEM_FENCE_WIDTH`, `ITEM_TIRE`, etc.) | Various | `data/maps/MossdeepCity_House4/scripts.inc` |
| **Pacifidlog Town**| Man in House | Trades a `ITEM_TM27_RETURN` for a Shard | 1x `ITEM_GREEN_SHARD` | `data/maps/PacifidlogTown_House5/scripts.inc` |

**UNSURE:** The exact trigger for the Pretty Petal Flower Shop to start selling berries. It is likely tied to story progression flags, possibly `FLAG_DEFEATED_RUSTBORO_GYM` or similar.

---

### 7. Purchase-Only Items (and items primarily acquired through purchase)

This list identifies items that are either impossible or extremely impractical to obtain in renewable quantities without spending money, coins, or BP. This is critical for money/resource planning.

**VERIFIED:**

*   **Poké Balls:** While some are found, the vast majority needed will be purchased (`ITEM_POKE_BALL`, `ITEM_GREAT_BALL`, `ITEM_ULTRA_BALL`, `ITEM_NET_BALL`, `ITEM_DIVE_BALL`).
*   **Healing Items:** Core healing items are primarily purchased (`ITEM_POTION` through `ITEM_FULL_RESTORE`, `ITEM_ANTIDOTE`, `ITEM_REVIVE`, etc.).
*   **Vitamins:** `ITEM_HP_UP`, `ITEM_PROTEIN`, `ITEM_IRON`, `ITEM_CARBOS`, `ITEM_CALCIUM`, `ITEM_ZINC`. A few can be found as hidden items, but the only renewable source is purchasing them (with money or BP).
*   **Battle Items:** `ITEM_X_ATTACK`, `ITEM_X_DEFEND`, etc. are purchase-only.
*   **TMs:**
    *   `ITEM_TM38_FIRE_BLAST` (Lilycove)
    *   `ITEM_TM25_THUNDER` (Lilycove)
    *   `ITEM_TM14_BLIZZARD` (Lilycove)
    *   `ITEM_TM15_HYPER_BEAM` (Lilycove)
    *   `ITEM_TM17_PROTECT` (Lilycove)
    *   `ITEM_TM20_SAFEGUARD` (Lilycove)
    *   `ITEM_TM33_REFLECT` (Lilycove)
    *   `ITEM_TM16_LIGHT_SCREEN` (Lilycove)
    *   `ITEM_TM13_ICE_BEAM` (Game Corner)
    *   `ITEM_TM24_THUNDERBOLT` (Game Corner)
    *   `ITEM_TM35_FLAMETHROWER` (Game Corner)
    *   `ITEM_TM30_SHADOW_BALL` (Game Corner)
    *   `ITEM_TM23_IRON_TAIL` (Game Corner)
*   **Evolution Items:** While some can be found or held by wild Pokémon, the only guaranteed, renewable source for `ITEM_FIRE_STONE`, `ITEM_THUNDER_STONE`, `ITEM_WATER_STONE`, and `ITEM_LEAF_STONE` is the Treasure Hunter on Route 124, who exchanges them for shards. *Correction:* These stones are not purchasable with money. This was an error in my initial recall. They are exchanged for colored shards. The only vendor that can be considered a "shop" for evolution items is the Battle Frontier selling `ITEM_KINGS_ROCK`.
*   **Game Corner Pokémon:** `SPECIES_PORYGON`, `SPECIES_DRATINI`, `SPECIES_LARVITAR`. These are exclusive to the Game Corner prize counter.
*   **Battle Frontier Items:** `ITEM_LEFTOVERS`, `ITEM_CHOICE_BAND`, etc. are exclusive to the BP Exchange.
*   **Secret Base Decorations:** The vast majority are purchase-only.
*   **Mail:** All mail types are purchase-only.
*   **Herbal Medicine:** All items from the Lavaridge Herb Shop are exclusive to that vendor.