## 1. WRONG — claims that are factually incorrect

> | Location Description | Coordinates (X, Y) | Item |
> | :--- | :--- | :--- |
> | Multiple hidden coins scattered on the floor. (`MAP_MAUVILLE_CITY_GAME_CORNER`) | Various | `ITEM_COIN` |

**What is actually true:** There is no `ITEM_COIN`. The script for finding hidden coins (`special FindHiddenCoin`) directly adds a random quantity of coins (10, 20, 100, or 200) to the player's Coin Case via the `AddCoins` function. It does not use the `finditem` command or any item from the `items.h` list.
**Citation:** `src/special_field.c`, function `FindHiddenCoin`.

> | Location Description | Coordinates (X, Y) | Item | Decomp Citation |
> | :--- | :--- | :--- | :--- |
> | Inside Steven's House, in the bottom-left corner near the strange rocks. (`MAP_MOSSDEEP_CITY_STEVENS_HOUSE`) | (1, 2) | `ITEM_REVIVE` | **VERIFIED:**<br>Map: `data/maps/MossdeepCity_StevensHouse/map.json`<br>Script: `MossdeepCity_StevensHouse_EventScript_HiddenBelieveMail` (Note: script name is a misnomer)<br>Flag: `FLAG_HIDDEN_ITEM_STEVENS_HOUSE_REVIVE` |

**What is actually true:** This entire entry is a fabrication. There are no hidden items in Steven's House.
- The map file contains no `hidden_item_object_events`.
- The flag `FLAG_HIDDEN_ITEM_STEVENS_HOUSE_REVIVE` does not exist.
- The cited script, `MossdeepCity_StevensHouse_EventScript_HiddenBelieveMail`, is not a hidden item script. It is attached to the Poké Ball on Steven's table and gives the player a Beldum after the main story. The note's claim that the script name is a "misnomer" is false; it is simply misidentifying a completely different type of event.
**Citation:** `data/maps/MossdeepCity_StevensHouse/map.json` and `data/maps/MossdeepCity_StevensHouse/scripts.inc`.

> | Location Description | Coordinates (X, Y) | Item |
> | :--- | :--- | :--- |
> | On the far western shore, south of the brothers' house. | (10, 47) | `ITEM_NUGGET` |

**What is actually true:** This item does not exist. There is only one hidden item in Sootopolis City, an `ITEM_BIG_PEARL`. The map file lists no other hidden items, and there is no object or script at coordinates (10, 47) that gives an item.
**Citation:** `data/maps/SootopolisCity/map.json` contains only one entry in `hidden_item_object_events`, for `SootopolisCity_EventScript_HiddenBigPearl`.

> **Mirage Tower** (First Fossil)
> | Location (Map Constant) | Coords (X, Y) | Item |
> | --------------------------- | ------------- | ------------------ |
> | `MAP_MIRAGE_TOWER_4F` | (5, 5) | `ITEM_ROOT_FOSSIL` |
> | `MAP_MIRAGE_TOWER_4F` | (6, 5) | `ITEM_CLAW_FOSSIL` |

**What is actually true:** The table is highly misleading. It presents these as two distinct hidden items that can be collected. In reality, the player can only choose **one** of the two fossils. Upon taking one, the other fossil and the entire Mirage Tower disappear permanently. They are mutually exclusive choices at this location.
**Citation:** `data/maps/MirageTower_4F/scripts.inc`, scripts `MirageTower_4F_EventScript_RootFossil` and `MirageTower_4F_EventScript_ClawFossil` both set `FLAG_MIRAGE_TOWER_COLLAPSED` and `FLAG_HIDE_MIRAGE_TOWER`.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald

> | Location Description | Coordinates (X, Y) | Item |
> | :--- | :--- | :--- |
> | In the tall grass behind the Pokémon Center. | (23, 11) | `ITEM_REVIVE` |

**What is actually true:** This hidden `ITEM_REVIVE` exists in Pokémon Ruby and Sapphire, but it was removed in Pokémon Emerald. There are no hidden items in Fortree City in Emerald.
**Citation:** `data/maps/FortreeCity/map.json` in `pokeemerald` has no `hidden_item_object_events` array. The equivalent file in the `pokeruby` decompilation contains this item.

## 3. MISSING — things that should be in a note on this topic and are absent

*   **Pacifidlog Town:** The note lists the hidden `ITEM_HEART_SCALE` but omits the second hidden item in town.
    *   **Item:** `ITEM_BIG_PEARL`
    *   **Location:** In the southwest corner of town, on an empty patch of water.
    *   **Coordinates:** (1, 7)
    *   **Citation:** `data/maps/PacifidlogTown/map.json`, object with script `PacifidlogTown_EventScript_HiddenBigPearl` and flag `FLAG_HIDDEN_ITEM_PACIFIDLOG_TOWN_BIG_PEARL`.

## 4. UNVERIFIABLE — claims you cannot confirm either way

None. All claims in the note were verifiable using the pokeemerald decompilation.

## 5. VERDICT

**UNRELIABLE.** The note contains multiple fabricated hidden items, at least one of which is presented with a complex, confident, and utterly false justification. It also includes data from other games and is missing at least one real item. It cannot be trusted.

**Most dangerous claim to act on:** The `ITEM_REVIVE` in `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`.

**Why:** This claim is not just wrong, it is a complete hallucination. It invents an item, coordinates, a flag, and a false narrative about a "misnomer" script to seem more credible. A player acting on this information would waste time searching for something that was never there, and the note's false confidence ("VERIFIED", "Note: script name is a misnomer") makes it dangerously convincing. This single entry reveals the generating AI's process to be fundamentally flawed and untrustworthy.