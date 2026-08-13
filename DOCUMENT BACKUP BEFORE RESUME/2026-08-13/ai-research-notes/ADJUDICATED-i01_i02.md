## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| Flag name for hidden TM32 on Route 113 | `FLAG_HIDDEN_ITEM_ROUTE_113_TM32_DOUBLE_TEAM` | `FLAG_HIDDEN_ITEM_ROUTE_113_TM32` | CRITIQUE CORRECT | `data/maps/Route113/scripts.inc` |
| Hidden items on Route 116 | There are no hidden items. | There is one hidden item, a Super Potion. | CRITIQUE CORRECT | `data/maps/Route116/scripts.inc` |
| Hidden items on Route 117 | There are no hidden items. | There is one hidden item, a Repel. | CRITIQUE CORRECT | `data/maps/Route117/scripts.inc` |
| Hidden items on Route 134 | There are no hidden items. | There are two hidden items in the underwater section. | CRITIQUE CORRECT | `data/maps/Route134_Underwater/scripts.inc` |
| Completeness of Route 114 item list | Lists one item (Revive). | The list is missing a Carbos. | CRITIQUE CORRECT | `data/maps/Route114/scripts.inc` |
| Completeness of Route 121 item list | Lists two items (HP Up, Nugget). | The list is missing a Full Heal. | CRITIQUE CORRECT | `data/maps/Route121/scripts.inc` |
| Completeness of Route 123 item list | Lists three items (Super Repel, Rare Candy, PP Up). | The list is missing a Revive. | CRITIQUE CORRECT | `data/maps/Route123/scripts.inc` |
| Completeness of Route 124 item list | Lists two underwater items (Pearl, Big Pearl). | The list is missing four underwater Shards (Green, Red, Yellow, Blue). | CRITIQUE CORRECT | `data/maps/Route124_Underwater/scripts.inc` |
| Completeness of Route 127 item list | Lists three underwater items. | The list is missing an overworld item, a Rare Candy. | CRITIQUE CORRECT | `data/maps/Route127/scripts.inc` |
| Completeness of Route 130 item list | Lists one item (Heart Scale). | The list is missing a Rare Candy. | CRITIQUE CORRECT | `data/maps/Route130/scripts.inc` |

## 2. CONFIRMED-GOOD CORE

The following information from the original note is correct and complete.

**Routes with No Hidden Items:**
*   Route 101, 102, 107, 108, 112, 122, 125, 131.

**Routes with Correctly Listed Hidden Items:**
*(Note: Some flag names may be simplified for brevity, e.g., `_HEART_SCALE_1` becomes `_HEART_SCALE`)*

*   **Route 103**: Potion (19,9), Heart Scale (10,10)
*   **Route 104**: Potion (13,19), Super Potion (4,1)
*   **Route 105**: Heart Scale (20,4), Big Pearl (4,25)
*   **Route 106**: Heart Scale (2,8), Stardust (21,14)
*   **Route 109**: Revive (8,14), Heart Scale (10,20), Great Ball (1,13), Heart Scale (0,19), Ether (7,7)
*   **Route 110**: Poké Ball (27,2), Revive (22,28), Great Ball (10,42), Rare Candy (2,17)
*   **Route 111**: Protein (11,14), Stardust (29,9), Rare Candy (9,44)
    *   The Rare Candy at (9,44) correctly replaces TM37 (Sandstorm) from Ruby/Sapphire.
*   **Route 113**: Ether (9,8), Super Repel (26,8), Nugget (45,12), TM32 Double Team (65,12)
*   **Route 115**: Heart Scale (36,44), Iron (10,20)
*   **Route 118**: Heart Scale (59,13)
*   **Route 119**: Calcium (29,91), Full Heal (46,76), Ultra Ball (25,59), Max Ether (16,32), Rare Candy (51,10)
*   **Route 120**: Rare Candy (71,12), Rare Candy (24,46), Revive (20,71)
*   **Route 126 (Underwater)**: Blue Shard (48,8), Big Pearl (65,23), Yellow Shard (27,23), Pearl (10,31), Ultra Ball (30,42), Heart Scale (58,49), Red Shard (14,49), Stardust (20,56), Green Shard (48,59), Heart Scale (36,12)
*   **Route 128**: Heart Scale (12,19), Heart Scale (42,35, Underwater), Pearl (5,50, Underwater)
*   **Route 129 (Underwater)**: Heart Scale (16,17)
*   **Route 132**: Rare Candy (27,24)
*   **Route 133**: Big Pearl (9,23), Star Piece (48,11)
*   **Route 130 (Mirage Island)**: The note correctly identifies a hidden Heart Scale on Mirage Island at (23,11) and accurately describes the island's appearance mechanic.

## 3. DO NOT USE

The following claims from the original note are incorrect and should be disregarded.

*   **Claims of absence:**
    *   **DO NOT USE**: "Route 116: There are no hidden items on Route 116." (It has a Super Potion).
    *   **DO NOT USE**: "Route 117: There are no hidden items on Route 117." (It has a Repel).
    *   **DO NOT USE**: "Route 134: There are no hidden items on Route 134." (It has an underwater Heart Scale and Star Piece).

*   **Incomplete Lists:** The note's lists for the following routes are incomplete. Do not treat them as exhaustive.
    *   **Route 114**: Missing `ITEM_CARBOS` at (11, 52).
    *   **Route 121**: Missing `ITEM_FULL_HEAL` at (10, 19).
    *   **Route 123**: Missing `ITEM_REVIVE` at (6, 23).
    *   **Route 124**: Missing four underwater shards: Green (48,20), Red (44,48), Yellow (63,27), and Blue (61,57).
    *   **Route 127**: Missing an overworld `ITEM_RARE_CANDY` at (21, 4).
    *   **Route 130**: Missing `ITEM_RARE_CANDY` at (41, 10).

*   **Incorrect Data:**
    *   **DO NOT USE**: The flag name `FLAG_HIDDEN_ITEM_ROUTE_113_TM32_DOUBLE_TEAM`. The correct flag is `FLAG_HIDDEN_ITEM_ROUTE_113_TM32`.

## 4. CONFIDENCE

**100%**. All claims regarding the presence, location, and flags of hidden items are definitively verifiable by inspecting the `hiddenitem` macros within the `data/maps/**/scripts.inc` files of the `pokeemerald` decompilation. The evidence is unambiguous, and all disputed claims have been settled.