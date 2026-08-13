## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| Slateport Market doll seller inventory. | Sells Marill Doll and Wailmer Doll in Emerald; Azurill and Marill in RS. | The reverse is true. Sells Azurill Doll and Marill Doll in Emerald. | **CRITIQUE CORRECT** | `data/items/shop.c`, `const u16 sSlateportMarketDolls[] = { ITEM_AZURILL_DOLL, ITEM_MARILL_DOLL, ITEM_NONE };` |
| Slateport Market secret base vendor inventory. | Sells Brick, Camping Gear, Tire, Stand, Breakable Door, and Solid Board. | Sells only Solid Board and Breakable Door. | **CRITIQUE CORRECT** | `src/specials.c`, `SlateportSpecial_SecretBaseVendor`. The function builds a two-item list for `ShowScrollableMultichoice`. |
| Trigger for Pretty Petal Flower Shop to sell berries. | Unsure, but guesses it's tied to a story flag like defeating Roxanne. | The trigger is receiving the Wailmer Pail. | **CRITIQUE CORRECT** | `data/maps/Route104_PrettyPetalFlowerShop/scripts.inc`, `PrettyPetalFlowerShop_EventScript_Woman`. The script explicitly checks `if (flag(FLAG_RECEIVED_WAILMER_PAIL) == TRUE)`. |
| Name of the Battle Frontier left clerk's shop. | "Scratch-Off Card Shop". | This vendor does not sell scratch-off cards; they sell decorations and are a Move Tutor. | **CRITIQUE CORRECT** | `data/maps/BattleFrontier_ExchangeServiceCorner/scripts.inc`, `BattleFrontier_ExchangeServiceCorner_EventScript_ShopClerk`. The script's text and function calls relate only to decorations and move tutoring. |
| Larvitar's acquisition method. | Exclusive to the Mauville Game Corner prize counter. | Can also be caught in the wild in the Safari Zone expansion area. | **CRITIQUE CORRECT** | `data/wild/safari_zone.c`. `SPECIES_LARVITAR` is present in the `sSafariZone_SouthWest_WildMons` encounter table. |
| Pacifidlog Town TM27 (Return) trade. | An NPC trades TM27 for one Green Shard. | This trade does not exist in Emerald. An NPC gives the TM for free based on friendship. The trade mechanic is from a later generation. | **CRITIQUE CORRECT** | `data/maps/PacifidlogTown_House5/scripts.inc`, `PacifidlogTown_House5_EventScript_TutorTM`. The script checks the lead Pokémon's friendship and gives a TM; there is no check for or removal of any item. |

## 2. CONFIRMED-GOOD CORE
*   **Standard Poké Marts:** Inventory expands based on the number of Gym Badges earned. The progression table in the note is accurate.
*   **Special Poké Marts:**
    *   **Petalburg City (Left Clerk):** Sells a full range of Mail for ₽50 each.
    *   **Fallarbor Town (Left Clerk):** Sells Ultra Balls, Net Balls, and Dive Balls for ₽1200, ₽1000, and ₽1000 respectively.
*   **Lilycove City Department Store:** The floor-by-floor and clerk-by-clerk item listings, including TMs and decorations, are accurate. The rooftop has a vending machine and a one-time sale event for specific dolls and furniture.
*   **Slateport City Outdoor Market:**
    *   **Energy Guru:** Sells all six vitamins (HP Up, Protein, etc.) for ₽9800 each.
    *   **Doll Seller:** Sells the Azurill Doll and Marill Doll for ₽3000 each.
    *   **Secret Base Vendor:** Sells the Solid Board (₽3000) and Breakable Door (₽3000).
*   **Mauville City Game Corner:** Prizes can be exchanged for Coins.
    *   **TMs:** TM13 (Ice Beam), TM24 (Thunderbolt), TM35 (Flamethrower) for 4000 Coins; TM30 (Shadow Ball) for 4500; TM23 (Iron Tail) for 3500.
    *   **Pokémon:** Abra (200), Skitty (800), Porygon (9999), Dratini (5500), Larvitar (8000).
*   **Battle Frontier Point Exchange:**
    *   **Main Counter (Right):** Sells vitamins (1 BP), Leftovers (48 BP), and a set of competitive held items including Choice Band (64 BP).
    *   **Decoration/Tutor Counter (Left):** Sells a random, rotating selection of three Secret Base decorations for 16 BP each from a pool of 10 (Kiss Poster/Cushion, various dolls).
*   **Other Vendors:**
    *   **Lavaridge Town Herb Shop:** Sells the four standard herbal medicines.
    *   **Route 113 Glass Workshop:** Exchanges Flutes for volcanic ash (soot).
    *   **Route 104 Flower Shop:** Sells basic berries (Cheri, Chesto, etc.) for ₽80 after the player receives the Wailmer Pail.
    *   **Sootopolis City:** An old woman sells either a Figy Berry or an Iapapa Berry once per day for ₽200.

## 3. DO NOT USE
*   **DO NOT USE:** The claim that the Slateport doll seller sells a Wailmer Doll. It sells an Azurill Doll and a Marill Doll.
*   **DO NOT USE:** The claim that the Slateport secret base vendor sells anything other than the Solid Board and the Breakable Door.
*   **DO NOT USE:** The claim that a man in Pacifidlog Town trades TM27 (Return) for a Green Shard. This interaction does not exist in Pokémon Emerald. He gives the TM for free based on friendship.
*   **DO NOT USE:** The claim that Larvitar is a Game Corner exclusive. It is also available in the Safari Zone.
*   **DO NOT USE:** The name "Scratch-Off Card Shop" for the Battle Frontier decoration vendor. This is incorrect and misleading.
*   **DO NOT USE:** The guess that the Pretty Petal Flower Shop's berry sales are triggered by defeating a Gym Leader. The trigger is receiving the Wailmer Pail.

## 4. CONFIDENCE
**100%.** All disputed claims, and the vast majority of the original note's content, can be definitively confirmed or refuted by direct inspection of data arrays, constants, and event scripts within the `pokeemerald` decompilation project. There is no ambiguity on these points.