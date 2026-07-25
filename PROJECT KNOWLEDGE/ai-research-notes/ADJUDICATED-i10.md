## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| **Prerequisite for TM07 (Hail)** | Requires making the Shell Bell, which "unblocks the path" to the Ice Room. | The Shell Bell sidequest is entirely unrelated to accessing the Ice Room. | CRITIQUE CORRECT | The script for the TM item ball, `ShoalCave_IceRoom_EventScript_ItemHail`, contains no flag checks. `data/maps/ShoalCave_IceRoom/scripts.inc` |
| **Second source for TM27 (Return)** | A copy is given by Professor Cozmo in Fallarbor Town. | Cozmo does not give this TM in Emerald (only in R/S). The only copy is from Pacifidlog Town. | CRITIQUE CORRECT | A project-wide search for `ITEM_TM27_RETURN` only yields the script in `data/maps/PacifidlogTown_House4/scripts.inc`. |
| **Acquisition of TM42 (Facade)** | Given by Norman, which is an "(Emerald change from RS)". | This is not a change; Norman gives TM42 in Ruby & Sapphire as well. | CRITIQUE CORRECT | `data/maps/PetalburgCity_Gym/scripts.inc`, `PetalburgCity_Gym_EventScript_Norman`. This behavior is consistent with the `pokeruby` decompilation. |
| **Prerequisite for TM48 (Skill Swap)** | `FLAG_SYS_GAME_CLEAR` (beating the Elite Four), but is "(UNSURE)". | The prerequisite is defeating Team Magma at Mt. Chimney. | CRITIQUE CORRECT | `data/maps/MtPyre_Summit/scripts.inc`, `MtPyre_Summit_EventScript_OldWomanRight` checks for `FLAG_DEFEATED_MAGMA_AT_MT_CHIMNEY`. |
| **Giver of HM06 (Rock Smash)** | Given by "Wally's uncle" in Mauville City. | This is true for R/S. In Emerald, it's given by a different NPC, the "Rock Smash Guy". | CRITIQUE CORRECT | `data/maps/MauvilleCity/scripts.inc`, `MauvilleCity_EventScript_RockSmashGuy`. The NPC's text confirms he is not Wally's uncle. |
| **Location of HM07 (Waterfall)** | An item ball in the Cave of Origin (`MAP_CAVE_OF_ORIGIN_B1F`). | This is the R/S location. In Emerald, it is in an item ball in the final room of the Marine Cave. | CRITIQUE CORRECT | `data/maps/MarineCave_End/map.json` contains the item ball object for `ITEM_HM07_WATERFALL`. |
| **Omission of the Pickup Ability** | The note does not mention the Pickup ability as a source for TMs. | The Pickup ability is a renewable source for certain TMs, including TM10, TM26, and TM44. | CRITIQUE CORRECT | `src/pokemon.c`, in the `sPickupCommonItems` and `sPickupRareItems` tables. |

## 2. CONFIRMED-GOOD CORE

*   **General**: TMs are single-use, HMs are infinite-use. No TMs are permanently missable in the game.
*   **TMs purchasable at Lilycove Dept. Store (₽):** TM14 Blizzard (5500), TM15 Hyper Beam (7500), TM16 Light Screen (3000), TM17 Protect (3000), TM20 Safeguard (3000), TM25 Thunder (5500), TM33 Reflect (3000), TM38 Fire Blast (5500).
*   **TMs from Mauville Game Corner (Coins):** TM13 Ice Beam (4000), TM24 Thunderbolt (4000), TM29 Psychic (3500), TM32 Double Team (1500), TM35 Flamethrower (4000).
*   **TMs from Gym Leaders:** TM03 Water Pulse (Juan), TM04 Calm Mind (Tate & Liza), TM08 Bulk Up (Brawly), TM34 Shock Wave (Wattson), TM39 Rock Tomb (Roxanne), TM40 Aerial Ace (Winona), TM42 Facade (Norman), TM50 Overheat (Flannery).
*   **TM01 Focus Punch:** Prize for Trick House puzzle #5.
*   **TM02 Dragon Claw:** Item Ball in Meteor Falls (Bagon's room). Requires Surf, Waterfall.
*   **TM05 Roar:** Gift from an NPC with a Poochyena on Route 114.
*   **TM06 Toxic:** Item Ball in Fiery Path. Requires Strength.
*   **TM07 Hail:** Item Ball in Shoal Cave's Ice Room. Accessible at low tide; requires Surf.
*   **TM09 Bullet Seed:** Gift from an NPC on Route 104.
*   **TM10 Hidden Power:** Gift from an old woman in Fortree City; also purchasable in Slateport Market. Also obtainable via the Pickup ability.
*   **TM11 Sunny Day:** Item Ball in Scorched Slab. Requires Surf.
*   **TM12 Taunt:** Prize for Trick House puzzle #3.
*   **TM13 Ice Beam:** Besides the Game Corner, an Item Ball is in a locked room in the Abandoned Ship. Requires Storage Key.
*   **TM18 Rain Dance:** Item Ball in the underwater section of the Abandoned Ship. Requires Dive.
*   **TM19 Giga Drain:** Gift from an NPC on Route 123 if you have a Grass-type Pokémon.
*   **TM21 Frustration:** Gift from an NPC in Pacifidlog Town if your lead Pokémon has low friendship.
*   **TM22 Solar Beam:** Item Ball in the Safari Zone. Requires Surf.
*   **TM23 Iron Tail:** Item Ball in Meteor Falls. Requires Surf, Waterfall.
*   **TM24 Thunderbolt:** Besides the Game Corner, a copy is given by Wattson after the New Mauville sidequest.
*   **TM26 Earthquake:** Item Ball in the Seafloor Cavern. Also obtainable via the Pickup ability at high levels (91-100).
*   **TM27 Return:** Gift from an NPC in Pacifidlog Town if your lead Pokémon has high friendship.
*   **TM28 Dig:** Gift from the Fossil Maniac's brother on Route 114.
*   **TM29 Psychic:** Besides the Game Corner, a hidden item in Victory Road.
*   **TM30 Shadow Ball:** Item Ball on Mt. Pyre.
*   **TM31 Brick Break:** Gift from an NPC in Sootopolis City.
*   **TM32 Double Team:** Besides the Game Corner, a hidden item on Route 113.
*   **TM36 Sludge Bomb:** Gift from an NPC in Dewford Town Hall after defeating Norman.
*   **TM37 Sandstorm:** Item Ball in the Route 111 desert.
*   **TM41 Torment:** Gift from an NPC in the Slateport City Battle Tent.
*   **TM43 Secret Power:** Gift from an NPC on Route 111; also purchasable in Slateport Market.
*   **TM44 Rest:** Gift from an NPC in a Lilycove City house. Also obtainable via the Pickup ability.
*   **TM45 Attract:** Gift from an NPC in the Verdanturf Town Battle Tent.
*   **TM46 Thief:** Gift from a Grunt in the Oceanic Museum.
*   **TM47 Steel Wing:** Gift from Steven in Granite Cave.
*   **TM48 Skill Swap:** Gift from an old woman at Mt. Pyre's summit after defeating Team Magma at Mt. Chimney.
*   **TM49 Snatch:** Item Ball on the S.S. Tidal.
*   **HM01 Cut:** Gift from the Cutter in Rustboro City.
*   **HM02 Fly:** Gift from your Rival on Route 119 after defeating Winona.
*   **HM03 Surf:** Gift from Wally's father in Petalburg City after defeating Norman.
*   **HM04 Strength:** Gift in Rusturf Tunnel after using Rock Smash to unite the couple.
*   **HM05 Flash:** Gift from a Hiker inside Granite Cave's entrance.
*   **HM06 Rock Smash:** Gift from the "Rock Smash Guy" in a Mauville City house.
*   **HM07 Waterfall:** Item Ball in the final room of the Marine Cave.
*   **HM08 Dive:** Gift from Steven in his Mossdeep City house after the Space Center event.

## 3. DO NOT USE

*   The claim that accessing TM07 (Hail) requires completing the Shell Bell sidequest.
*   The claim that TM27 (Return) can be obtained from Professor Cozmo.
*   The claim that Norman giving TM42 (Facade) is a change from Ruby & Sapphire.
*   The claim that TM48 (Skill Swap) requires beating the Elite Four.
*   The claim that HM06 (Rock Smash) is given by Wally's uncle.
*   The claim that HM07 (Waterfall) is found in the Cave of Origin.

## 4. CONFIDENCE

**100%**. All claims were verifiable against the `pokeemerald` decompilation project. The critique was accurate and its corrections align with the game's code and data. The corrected information in the "CONFIRMED-GOOD CORE" is reliable.