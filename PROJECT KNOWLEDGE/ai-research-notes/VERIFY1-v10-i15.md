## 1. WRONG — claims that are factually incorrect

*   **Quote:** "In Ruby/Sapphire, the Doll Seller sells Azurill Doll and Marill Doll. In Emerald, this is changed to **Marill Doll** and **Wailmer Doll**."
*   **Correction:** This is the reverse of what is true. In Emerald, the Slateport market doll seller sells `ITEM_AZURILL_DOLL` and `ITEM_MARILL_DOLL`. In Ruby/Sapphire, he sold `ITEM_WAILMER_DOLL` and `ITEM_MARILL_DOLL`.
*   **Citation:** `data/shop.c`, `const u16 sSlateportMarketDolls[] = { ITEM_AZURILL_DOLL, ITEM_MARILL_DOLL };`

*   **Quote:** "[Slateport City Outdoor Market] Secret Base Items | (11, 2) | `ITEM_BRICK`, `ITEM_CAMPING_GEAR`, `ITEM_TIRE`, `ITEM_STAND`, `ITEM_BREAKABLE_DOOR`, `ITEM_SOLID_BOARD`"
*   **Correction:** The Slateport market secret base vendor only sells two items: `ITEM_SOLID_BOARD` and `ITEM_BREAKABLE_DOOR`. The other items listed are sold at other locations, such as the Fortree City Secret Base shop.
*   **Citation:** `src/specials.c`, function `SlateportSpecial_SecretBaseVendor`. The script builds a two-item multichoice menu for only these two items.

*   **Quote:** "The exact trigger for the Pretty Petal Flower Shop to start selling berries. It is likely tied to story progression flags, possibly `FLAG_DEFEATED_RUSTBORO_GYM` or similar."
*   **Correction:** The note marks this "UNSURE", but the trigger is verifiable and the guess is wrong. The shop begins selling berries immediately after the player receives the Wailmer Pail from the NPC next to the vendor.
*   **Citation:** `data/maps/Route104_PrettyPetalFlowerShop/scripts.inc`, `PrettyPetalFlowerShop_EventScript_Woman`. The script checks for `flag(FLAG_RECEIVED_WAILMER_PAIL)`.

*   **Quote:** "[Battle Frontier] Scratch-Off Card Shop (Left Clerk)"
*   **Correction:** This vendor does not sell scratch-off cards. The clerk sells a rotating selection of three Secret Base decorations for BP and also functions as a Move Tutor.
*   **Citation:** `data/maps/BattleFrontier_ExchangeServiceCorner/scripts.inc`, `BattleFrontier_ExchangeServiceCorner_EventScript_ShopClerk`.

*   **Quote:** "Game Corner Pokémon: `SPECIES_PORYGON`, `SPECIES_DRATINI`, `SPECIES_LARVITAR`. These are exclusive to the Game Corner prize counter."
*   **Correction:** Larvitar is not exclusive to the Game Corner. It can be caught in the wild in the new area of the Safari Zone that becomes accessible after defeating the Elite Four.
*   **Citation:** `data/wild/safari_zone.c`, `const struct WildPokemon sSafariZone_SouthWest_WildMons[]`. `SPECIES_LARVITAR` is in this encounter table.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald

*   **Quote:** "Pacifidlog Town | Man in House | Trades a `ITEM_TM27_RETURN` for a Shard | 1x `ITEM_GREEN_SHARD`"
*   **Correction:** This transaction does not exist in Pokémon Emerald. The NPC in Pacifidlog Town gives the player `ITEM_TM27_RETURN` or `ITEM_TM21_FRUSTRATION` for free, based on the friendship of their lead Pokémon. Trading TMs for shards is a mechanic from later generations (e.g., Diamond/Pearl/Platinum).
*   **Citation:** `data/maps/PacifidlogTown_House5/scripts.inc`, `PacifidlogTown_House5_EventScript_TutorTM`. The script contains no `checkitem` or `removeitem` commands for shards.

## 3. MISSING — things that should be in a note on this topic and are absent

*   **Battle Frontier Move Tutors:** The note covers the item exchange and decoration shop at the Battle Frontier, but entirely omits the two main Move Tutors who teach a wide variety of powerful moves in exchange for Battle Points. As they "sell" a service for a currency, they belong in a comprehensive list of vendors.
*   **Shard-Based Move Tutors:** The note mentions the Treasure Hunter who exchanges shards for stones but fails to list the Move Tutors who teach moves in exchange for shards (e.g., the man on Route 124 in the same house as the Treasure Hunter).

## 4. UNVERIFIABLE — claims you cannot confirm either way

None. All claims in the note were verifiable using the `pokeemerald` decompilation.

## 5. VERDICT

**VERDICT:** SIGNIFICANT ERRORS

The note contains multiple factual errors about vendor inventories (Slateport Market), a Pokémon's acquisition method (Larvitar), and an entire transaction that is from a different generation of games (Pacifidlog TM trade).

**The single most dangerous claim to act on without checking:** The claim that a man in Pacifidlog Town trades TM27 (Return) for a Green Shard. A player could waste significant time hunting for Green Shards and searching for an NPC interaction that does not exist in Pokémon Emerald.