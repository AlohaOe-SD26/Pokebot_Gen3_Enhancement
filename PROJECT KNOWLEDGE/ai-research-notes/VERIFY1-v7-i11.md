## 1. WRONG — claims that are factually incorrect

*   **Quote:** "Vulpix | `ITEM_RAWST_BERRY` | `ITEM_RAWST_BERRY` | Redundant entry. Effectively a 50% chance for `RAWST_BERRY`."
    *   **What is actually true:** The 50% chance is correct, but the note's underlying logic is wrong. The general formula given implies a `5% + (95% * 50%) = 52.5%` chance. The note fails to mention that the game has a specific check for when `item1 == item2`, which forces a single 50% roll instead of two separate rolls. The reasoning is flawed, even if the one-off conclusion is correct.
    *   **Citation:** `src/wild_encounter.c`, in `CreateWildMon`:
        ```c
        if (gBaseStats[species].item1 == gBaseStats[species].item2)
        {
            chance = 50;
            // ... (single roll)
        }
        else
        {
            // ... (two separate rolls)
        }
        ```

*   **Quote:** "Sandshrew | `ITEM_ORAN_BERRY` | `ITEM_QUICK_CLAW`"
    *   **What is actually true:** Sandshrew's common held item (`item1`) is `ITEM_NONE`. It only has a 5% chance to hold a `ITEM_QUICK_CLAW`.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_SANDSHREW] =
        {
            .item1 = ITEM_NONE,
            .item2 = ITEM_QUICK_CLAW,
        },
        ```

*   **Quote:** "Meowth | `ITEM_ORAN_BERRY` | `ITEM_QUICK_CLAW`"
    *   **What is actually true:** Meowth's common held item (`item1`) is `ITEM_NONE`. It only has a 5% chance to hold a `ITEM_QUICK_CLAW`.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_MEOWTH] =
        {
            .item1 = ITEM_NONE,
            .item2 = ITEM_QUICK_CLAW,
        },
        ```

*   **Quote:** "Chansey | `ITEM_NONE` | `ITEM_LUCKY_EGG`"
    *   **What is actually true:** Chansey's common held item (`item1`) is `ITEM_LUCKY_PUNCH`.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_CHANSEY] =
        {
            .item1 = ITEM_LUCKY_PUNCH,
            .item2 = ITEM_LUCKY_EGG,
        },
        ```

*   **Quote:** "Corsola | `ITEM_RED_SHARD` | `ITEM_BLUE_SHARD`"
    *   **What is actually true:** Corsola's rare held item (`item2`) is `ITEM_NONE`. It only has a 50% chance to hold a `ITEM_RED_SHARD`.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_CORSOLA] =
        {
            .item1 = ITEM_RED_SHARD,
            .item2 = ITEM_NONE,
        },
        ```

*   **Quote:** "Relicanth | `ITEM_GREEN_SHARD` | `ITEM_DEEP_SEA_SCALE`"
    *   **What is actually true:** Relicanth's rare held item (`item2`) is `ITEM_DEEP_SEA_TOOTH`, not `ITEM_DEEP_SEA_SCALE`. These are different, mutually exclusive evolution items for Clamperl.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_RELICANTH] =
        {
            .item1 = ITEM_GREEN_SHARD,
            .item2 = ITEM_DEEP_SEA_TOOTH,
        },
        ```

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald

*   **Quote:** "Electrike | `ITEM_NONE` | `ITEM_MAGNET`"
    *   **What is actually true:** In Pokémon Emerald, wild Electrike do not hold any items. In Diamond/Pearl/Platinum, they have a chance to hold a Magnet when encountered via the Poké Radar.
    *   **Citation:** `src/data/pokemon/base_stats.h`:
        ```c
        [SPECIES_ELECTRIKE] =
        {
            .item1 = ITEM_NONE,
            .item2 = ITEM_NONE,
        },
        ```

*   **Quote:** "Absol | `ITEM_NONE` | `ITEM_LIFE_ORB` | **[UNSURE]** Decomp shows `ITEM_LIFE_ORB`..."
    *   **What is actually true:** This is entirely false for Emerald. Wild Absol hold no items. `ITEM_LIFE_ORB` is a Generation IV item and does not exist in Pokémon Emerald's data. The note's claim that the "Decomp shows `ITEM_LIFE_ORB`" is incorrect.
    *   **Citation:** `src/data/pokemon/base_stats.h` shows no items for Absol. The item constant `ITEM_LIFE_ORB` does not exist in `include/constants/items.h`.

## 3. MISSING — things that should be in a note on this topic and are absent

The note claims to provide a "Full List," but it is missing several Pokémon that can be found holding items in the wild in Emerald.

*   **Missing:** Cubone and Marowak can both rarely hold `ITEM_THICK_CLUB`.
    *   **Citation:** `src/data/pokemon/base_stats.h`
*   **Missing:** Koffing and Weezing can both rarely hold `ITEM_SMOKE_BALL`.
    *   **Citation:** `src/data/pokemon/base_stats.h`
*   **Missing:** Spinda can commonly hold `ITEM_CHESTO_BERRY`.
    *   **Citation:** `src/data/pokemon/base_stats.h`
*   **Missing:** Trapinch can rarely hold `ITEM_SOFT_SAND`.
    *   **Citation:** `src/data/pokemon/base_stats.h`
*   **Missing:** Cacnea can rarely hold `ITEM_POISON_BARB`.
    *   **Citation:** `src/data/pokemon/base_stats.h`
*   **Missing:** Clamperl can commonly hold `ITEM_BLUE_SHARD` and rarely hold `ITEM_BIG_PEARL`.
    *   **Citation:** `src/data/pokemon/base_stats.h`

## 4. UNVERIFIABLE — claims you cannot confirm either way

There are no unverifiable claims in this note. All claims can be proven correct or incorrect by cross-referencing the pokeemerald decompilation. The note's single `[UNSURE]` tag on Absol is verifiably false, as documented in section 2.

## 5. VERDICT

**SIGNIFICANT ERRORS**. While the description of the core mechanic is mostly accurate, the list of Pokémon and their held items—the bulk of the note—is riddled with factual errors, data from other games, and major omissions. It cannot be trusted as a reference.

**The single most dangerous claim to act on without checking is:** "Relicanth | `ITEM_GREEN_SHARD` | `ITEM_DEEP_SEA_SCALE`".

**Why:** A player or bot developer would use this information to farm for a `DEEP_SEA_SCALE`, which is an evolution item required to obtain Gorebyss. Relicanth does **not** hold this item; it holds the `DEEP_SEA_TOOTH` (for Huntail). This would lead to wasted time farming the wrong Pokémon for an item it can never provide. The actual source for a wild `DEEP_SEA_SCALE` is Clamperl, a Pokémon completely absent from the note's list.