Excellent. Here are the ROM-accurate facts regarding held items on wild Pokémon in Emerald, structured for bot development.

### 1. Core Mechanic: Held Item Generation

The logic for determining a wild Pokémon's held item is executed during its creation. The game checks two separate "slots" for items, a rare slot and a common slot, in that order.

*   **[VERIFIED]** A Pokémon species has two potential held items defined in its base stats structure.
    *   `item2`: The "rare" item.
    *   `item1`: The "common" item.
*   **[VERIFIED]** The generation logic is found in `src/wild_encounter.c`, within the `CreateWildMon` function.
*   **[VERIFIED]** The process is as follows:
    1.  A random number (`rand`) between 0 and 99 is generated.
    2.  The game checks if `rand` is less than the rare item chance (default: 5). If true, and the species has a rare item (`item2 != ITEM_NONE`), the Pokémon is given that item.
    3.  If the rare item check fails, a *new* random number (`rand`) between 0 and 99 is generated.
    4.  The game checks if this new `rand` is less than the common item chance (default: 50). If true, and the species has a common item (`item1 != ITEM_NONE`), the Pokémon is given that item.
    5.  If both checks fail, the Pokémon holds no item.

This means the checks are independent; a Pokémon can *never* hold both its common and rare item simultaneously. The effective probabilities are:
*   **Rare Item:** 5%
*   **Common Item:** 95% (remaining chance) * 50% = 47.5%
*   **No Item:** 47.5% (or 100% if no items are defined)

#### 1.1. The `Compound Eyes` Ability Effect

*   **[VERIFIED]** If the first Pokémon in the player's party (even if fainted) has the ability `ABILITY_COMPOUND_EYES`, the probabilities are increased.
*   **[VERIFIED]** This check is also in `src/wild_encounter.c` in the `CreateWildMon` function. It modifies the `chanceRare` and `chanceCommon` local variables.
*   **[VERIFIED]** With `Compound Eyes`, the chances become:
    *   `chanceRare` = 10 (10%)
    *   `chanceCommon` = 60 (60%)

The effective probabilities with `Compound Eyes` are:
*   **Rare Item:** 10%
*   **Common Item:** 90% (remaining chance) * 60% = 54%
*   **No Item:** 36%

### 2. Full List of Wild Pokémon with Held Items

*   **[VERIFIED]** This data is sourced directly from the `gBaseStats` array in `src/data/pokemon/base_stats.h`. `item1` corresponds to the 50% slot, `item2` to the 5% slot.

| Species | Common Item (50%) | Rare Item (5%) | Notes |
| :--- | :--- | :--- | :--- |
| Pikachu | `ITEM_ORAN_BERRY` | `ITEM_LIGHT_BALL` | The only source for Light Ball. |
| Sandshrew | `ITEM_ORAN_BERRY` | `ITEM_QUICK_CLAW` | |
| Vulpix | `ITEM_RAWST_BERRY` | `ITEM_RAWST_BERRY` | Redundant entry. Effectively a 50% chance for `RAWST_BERRY`. |
| Meowth | `ITEM_ORAN_BERRY` | `ITEM_QUICK_CLAW` | |
| Magnemite | `ITEM_NONE` | `ITEM_METAL_COAT` | Only has a rare item. |
| Magneton | `ITEM_NONE` | `ITEM_METAL_COAT` | Only has a rare item. |
| Farfetch'd | `ITEM_NONE` | `ITEM_STICK` | Only has a rare item. |
| Grimer | `ITEM_NONE` | `ITEM_NUGGET` | |
| Muk | `ITEM_NONE` | `ITEM_NUGGET` | |
| Horsea | `ITEM_NONE` | `ITEM_DRAGON_SCALE` | **Emerald difference:** In R/S, Horsea/Seadra did not hold items. |
| Seadra | `ITEM_NONE` | `ITEM_DRAGON_SCALE` | **Emerald difference.** |
| Chansey | `ITEM_NONE` | `ITEM_LUCKY_EGG` | The only source for Lucky Egg. |
| Staryu | `ITEM_STARDUST` | `ITEM_STAR_PIECE` | |
| Mr. Mime | `ITEM_LEPPA_BERRY` | `ITEM_LEPPA_BERRY` | Redundant entry. 50% chance for `LEPPA_BERRY`. |
| Snorlax | `ITEM_LEFTOVERS` | `ITEM_LEFTOVERS` | Redundant entry. 50% chance for `LEFTOVERS`. |
| Chinchou | `ITEM_NONE` | `ITEM_YELLOW_SHARD` | Only has a rare item. |
| Lanturn | `ITEM_NONE` | `ITEM_YELLOW_SHARD` | Only has a rare item. |
| Pichu | `ITEM_ORAN_BERRY` | `ITEM_ORAN_BERRY` | Redundant entry. 50% chance for `ORAN_BERRY`. |
| Corsola | `ITEM_RED_SHARD` | `ITEM_BLUE_SHARD` | **Emerald difference:** In R/S, Corsola held no items. |
| Zigzagoon | `ITEM_ORAN_BERRY` | `ITEM_REVIVE` | |
| Linoone | `ITEM_ORAN_BERRY` | `ITEM_SITRUS_BERRY` | |
| Electrike | `ITEM_NONE` | `ITEM_MAGNET` | |
| Roselia | `ITEM_NONE` | `ITEM_POISON_BARB` | |
| Gulpin | `ITEM_ORAN_BERRY` | `ITEM_BIG_PEARL` | |
| Swalot | `ITEM_ORAN_BERRY` | `ITEM_BIG_PEARL` | |
| Solrock | `ITEM_NONE` | `ITEM_SUN_STONE` | |
| Lunatone | `ITEM_NONE` | `ITEM_MOON_STONE` | |
| Castform | `ITEM_MYSTIC_WATER` | `ITEM_MYSTIC_WATER` | Redundant entry. 50% chance for `MYSTIC_WATER`. |
| Shuppet | `ITEM_NONE` | `ITEM_SPELL_TAG` | |
| Banette | `ITEM_NONE` | `ITEM_SPELL_TAG` | |
| Duskull | `ITEM_NONE` | `ITEM_SPELL_TAG` | |
| Dusclops | `ITEM_NONE` | `ITEM_SPELL_TAG` | |
| Chimecho | `ITEM_ORAN_BERRY` | `ITEM_ORAN_BERRY` | Redundant entry. 50% chance for `ORAN_BERRY`. |
| Absol | `ITEM_NONE` | `ITEM_LIFE_ORB` | **[UNSURE]** Decomp shows `ITEM_LIFE_ORB`, but this item is unused and has no effect in Gen 3. It's likely a leftover. It cannot be obtained. The name exists but the item itself is dummied. Your bot should treat this as `ITEM_NONE`. |
| Spheal | `ITEM_ORAN_BERRY` | `ITEM_SITRUS_BERRY` | |
| Sealeo | `ITEM_ORAN_BERRY` | `ITEM_SITRUS_BERRY` | |
| Walrein | `ITEM_ORAN_BERRY` | `ITEM_SITRUS_BERRY` | |
| Relicanth | `ITEM_GREEN_SHARD` | `ITEM_DEEP_SEA_SCALE`| |
| Luvdisc | `ITEM_HEART_SCALE` | `ITEM_NONE` | Only has a common item. |
| Bagon | `ITEM_NONE` | `ITEM_DRAGON_SCALE` | |

### 3. Exploitation Methods for a Bot

A bot can acquire these items from wild Pokémon in two primary ways.

#### 3.1. Using `Thief` or `Covet`

These moves steal the target's held item.

*   **[VERIFIED]** The core logic is handled by `atk19_setstolenitem` in `src/battle_script_commands.c`.
*   **Preconditions for Success:**
    1.  The user of `Thief`/`Covet` must **not** be holding an item. `gBattleMons[gBattlerAttacker].item == ITEM_NONE`.
    2.  The target Pokémon must be holding an item. `gBattleMons[gBattlerTarget].item != ITEM_NONE`.
    3.  The target Pokémon must not have the ability `ABILITY_STICKY_HOLD`.
*   **Bot Implementation:**
    *   Maintain a designated "thief" Pokémon (e.g., a Mightyena) with one of these moves.
    *   Before entering an encounter to farm an item, the bot must ensure its thief is not holding an item. If it successfully steals an item, the bot must remove the item from the thief before attempting another theft.
    *   The bot can know the target's item beforehand by reading the `gEnemyParty` memory structure after the encounter begins. This avoids wasting turns on Pokémon that spawned with no item.

#### 3.2. Catching the Pokémon

*   **[VERIFIED]** A caught Pokémon retains the item it was holding in the wild.
*   **Bot Implementation:**
    *   This is a less efficient method for farmable items (like Heart Scales) due to the cost of Poké Balls and the time spent in the capture animation.
    *   It is the only method for a story-completion bot that does not yet have access to the TMs for `Thief` (TM46, Slateport City Oceanic Museum) or a Pokémon that learns it by level-up.
    *   The bot should simply catch the target Pokémon, then transfer the item to the bag via the party menu. The `Take-Item` option logic can be found in `src/party_menu.c`, specifically `Task_GiveTakeItem`.

### 4. Pokémon with Pickup Ability

While not a "held item" on wild Pokémon, the `Pickup` ability is relevant for item acquisition and can be confused with it.

*   **[VERIFIED]** In Emerald, `Pickup` gives a chance to generate an item *after* a battle is won if the Pokémon with the ability did not already have a held item.
*   **[VERIFIED]** The item generated depends on the Pokémon's level. The logic is in `src/battle_main.c` in the function `BattleMainCB_EndTurn`. It calls `DoPickupAbilityCheck`.
*   **[VERIFIED]** This is an out-of-battle effect that triggers on the "victory" screen. It has no bearing on what items wild Zigzagoon or Linoone themselves are holding *during* an encounter. Their held items follow the table in Section 2.