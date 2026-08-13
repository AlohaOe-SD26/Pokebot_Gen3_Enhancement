## 1. WRONG — claims that are factually incorrect

*   **Claim:** (TM07 Hail) "Requires Shoal Shells and Shoal Salt to make the Shell Bell, which unblocks the path."
    *   **Truth:** The Shell Bell sidequest is unrelated to accessing the Ice Room. The Ice Room, which contains the item ball for TM07, is accessible simply by visiting Shoal Cave during low tide. The NPC in that room gives the player a Never-Melt Ice, not a Shell Bell.
    *   **Citation:** `data/maps/ShoalCave_IceRoom/scripts.inc` contains `ShoalCave_IceRoom_EventScript_ItemHail` for the TM and `ShoalCave_IceRoom_EventScript_NeverMeltIceMan` for the NPC gift, neither of which are gated by the Shell Bell.

*   **Claim:** (TM27 Return) is given by "Professor Cozmo" in `MAP_FALLARBOR_TOWN_COZMOS_HOUSE`.
    *   **Truth:** Professor Cozmo does not give the player a TM in Emerald. There is only one copy of TM27 in the game, obtained from an NPC in Pacifidlog Town if the lead Pokémon has high friendship.
    *   **Citation:** `data/maps/FallarborTown_CozmosHouse/scripts.inc` shows no TM is given out by any NPC in this location. A search for `ITEM_TM27_RETURN` across all scripts only yields the one in `data/maps/PacifidlogTown_House4/scripts.inc`.

*   **Claim:** (TM42 Facade) acquisition is an **"(Emerald change from RS)"**.
    *   **Truth:** This is not a change from Ruby & Sapphire. In all three games, Norman gives the player TM42 (Facade) upon defeat.
    *   **Citation:** The script `PetalburgCity_Gym_EventScript_Norman` in `data/maps/PetalburgCity_Gym/scripts.inc` gives `ITEM_TM42_FACADE` in both the `pokeemerald` and `pokeruby` decompilations.

*   **Claim:** The prerequisite for (TM48 Skill Swap) is "**FLAG_SYS_GAME_CLEAR (UNSURE...**)".
    *   **Truth:** The prerequisite is specific and verifiable: the player must have defeated Team Magma at Mt. Chimney. The `SYS_GAME_CLEAR` flag (beating the Elite Four) is not required.
    *   **Citation:** The script `MtPyre_Summit_EventScript_OldWomanRight` in `data/maps/MtPyre_Summit/scripts.inc` explicitly checks for `FLAG_DEFEATED_MAGMA_AT_MT_CHIMNEY`.

## 2. WRONG GAME — claims that are true of Ruby/Sapphire, FireRed/LeafGreen, or a later generation, but NOT of Emerald

*   **Claim:** (HM06 Rock Smash) is "Given by Wally's uncle" in Mauville City.
    *   **Truth:** This is true for Ruby & Sapphire. In Emerald, Wally's family no longer lives in that house. The HM is given by a different NPC, the "Rock Smash Guy," who is not related to Wally.
    *   **Citation:** The text for the NPC in `data/text/maps/mauville_city.inc` (`MauvilleCity_Text_HeresRockSmash`) shows him mistaking the player for Wally, confirming he is not his uncle.

*   **Claim:** (HM07 Waterfall) is located in an Item Ball in `MAP_CAVE_OF_ORIGIN_B1F`.
    *   **Truth:** This is its location in Ruby & Sapphire. In Emerald, the Cave of Origin's layout is different and contains no HMs. HM07 is found in an item ball in the final room of the Marine Cave.
    *   **Citation:** `data/maps/MarineCave_End/map.json` contains the object for `ITEM_HM07_WATERFALL`. The corresponding map file for the Cave of Origin (`data/maps/CaveOfOrigin_B1F/map.json`) has no item balls.

## 3. MISSING — things that should be in a note on this topic and are absent

*   **The Pickup Ability:** The note omits that certain TMs can be obtained as random items via a Pokémon with the Pickup ability. This is a renewable, if unreliable, source for otherwise single-acquisition TMs. TMs available via Pickup include TM10 (Hidden Power), TM44 (Rest), and, at very high levels, TM26 (Earthquake).
    *   **Citation:** `src/pokemon.c`, in the `sPickupRareItems` table.

## 4. UNVERIFIABLE — claims you cannot confirm either way

*   All claims in the note could be verified using the decompilation project. None are fundamentally unverifiable.

## 5. VERDICT

**SIGNIFICANT ERRORS.** The note contains several major, game-altering mistakes, particularly regarding the locations of HMs and TMs that differ from Ruby & Sapphire. While many entries are correct, the errors are severe enough to render the note untrustworthy.

**The single most dangerous claim to act on without checking is that HM07 (Waterfall) is in the Cave of Origin.** A player following this guide would be unable to find a required HM, completely halting their progress before the Pokémon League. They would be stuck, searching a location from the wrong game, with no in-game indication of where to actually go.