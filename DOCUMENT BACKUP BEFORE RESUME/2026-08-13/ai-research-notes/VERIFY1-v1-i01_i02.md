## 1. WRONG — claims that are factually incorrect
*   **Claim**: On Route 113, the flag for the hidden TM32 is `FLAG_HIDDEN_ITEM_ROUTE_113_TM32_DOUBLE_TEAM`.
    *   **Reality**: The flag constant does not include the item's name. The correct flag is `FLAG_HIDDEN_ITEM_ROUTE_113_TM32`.
    *   **Source**: `data/maps/Route113/scripts.inc` contains the line `hiddenitem ITEM_TM32_DOUBLE_TEAM, 65, 12, FLAG_HIDDEN_ITEM_ROUTE_113_TM32`.

*   **Claim**: "Route 116: There are no hidden items on Route 116."
    *   **Reality**: Route 116 has one hidden item: an `ITEM_SUPER_POTION` at coordinates (37, 10).
    *   **Source**: `data/maps/Route116/scripts.inc` contains `hiddenitem ITEM_SUPER_POTION, 37, 10, FLAG_HIDDEN_ITEM_ROUTE_116_SUPER_POTION`.

*   **Claim**: "Route 117: There are no hidden items on Route 117."
    *   **Reality**: Route 117 has one hidden item: an `ITEM_REPEL` at coordinates (29, 13).
    *   **Source**: `data/maps/Route117/scripts.inc` contains `hiddenitem ITEM_REPEL, 29, 13, FLAG_HIDDEN_ITEM_ROUTE_117_REPEL`.

*   **Claim**: "Route 134: There are no hidden items on Route 134."
    *   **Reality**: Route 134 has two hidden items in its underwater section.
        *   `ITEM_HEART_SCALE` at `(21, 31)`, flag `FLAG_HIDDEN_ITEM_ROUTE_134_HEART_SCALE`.
        *   `ITEM_STAR_PIECE` at `(48, 13)`, flag `FLAG_HIDDEN_ITEM_ROUTE_134_STAR_PIECE`.
    *   **Source**: `data/maps/Route134_Underwater/scripts.inc`.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald
No instances of this error were found. The note correctly identifies the TM37 change on Route 111 as an Emerald-specific detail.

## 3. MISSING — things that should be in a note on this topic and are absent
The note omits the following hidden items:
*   **Route 114**: `ITEM_CARBOS` at `(11, 52)`, `FLAG_HIDDEN_ITEM_ROUTE_114_CARBOS`.
    *   **Source**: `data/maps/Route114/scripts.inc`.
*   **Route 121**: `ITEM_FULL_HEAL` at `(10, 19)`, `FLAG_HIDDEN_ITEM_ROUTE_121_FULL_HEAL`.
    *   **Source**: `data/maps/Route121/scripts.inc`.
*   **Route 123**: `ITEM_REVIVE` at `(6, 23)`, `FLAG_HIDDEN_ITEM_ROUTE_123_REVIVE`.
    *   **Source**: `data/maps/Route123/scripts.inc`.
*   **Route 124 (Underwater)**: Four Shards are missing from the list.
    *   `ITEM_GREEN_SHARD` at `(48, 20)`, `FLAG_HIDDEN_ITEM_ROUTE_124_GREEN_SHARD`.
    *   `ITEM_RED_SHARD` at `(44, 48)`, `FLAG_HIDDEN_ITEM_ROUTE_124_RED_SHARD`.
    *   `ITEM_YELLOW_SHARD` at `(63, 27)`, `FLAG_HIDDEN_ITEM_ROUTE_124_YELLOW_SHARD`.
    *   `ITEM_BLUE_SHARD` at `(61, 57)`, `FLAG_HIDDEN_ITEM_ROUTE_124_BLUE_SHARD`.
    *   **Source**: `data/maps/Route124_Underwater/scripts.inc`.
*   **Route 127**: `ITEM_RARE_CANDY` at `(21, 4)`, `FLAG_HIDDEN_ITEM_ROUTE_127_RARE_CANDY`.
    *   **Source**: `data/maps/Route127/scripts.inc`.
*   **Route 130**: `ITEM_RARE_CANDY` at `(41, 10)`, `FLAG_HIDDEN_ITEM_ROUTE_130_RARE_CANDY`.
    *   **Source**: `data/maps/Route130/scripts.inc`.

## 4. UNVERIFIABLE — claims you cannot confirm either way
All claims in the note are verifiable against the `pokeemerald` decompilation.

## 5. VERDICT
**SIGNIFICANT ERRORS.** The note incorrectly claims multiple routes have no hidden items when they do, and it omits over a dozen hidden items across seven different routes.

**The single most dangerous claim to act on without checking is:** "Route 134: There are no hidden items on Route 134."

**Why:** This is a categorical claim of absence for a large, difficult-to-navigate map (especially the underwater currents), which would cause a user to not bother searching it at all. This guarantees they would miss valuable items, including a `ITEM_STAR_PIECE`. Unlike a single missed item on a route with many others, this claim dismisses an entire map's worth of secrets.