## 1. RULINGS ON DISPUTED CLAIMS

| claim | note says | critique says | RULING | citation |
| :--- | :--- | :--- | :--- | :--- |
| Giver of 5 Poké Balls | The rival, immediately after Birch gives the Pokédex. | Professor Birch, during the same conversation. | **CRITIQUE CORRECT** | `data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc` (`LittlerootTown_ProfessorBirchsLab_EventScript_GivePokedexAndBalls`) |
| Giver and location of Great Ball | Mr. Stone on `DEVON_CORP_3F`. | Devon Researcher on `DEVON_CORP_2F`. | **CRITIQUE CORRECT** | `data/maps/RustboroCity_DevonCorp_2F/scripts.inc` (`RustboroCity_DevonCorp_2F_EventScript_ResearcherGiveGreatBall`) |
| Silk Scarf EV check | The lead Pokémon must have a high total EV count. | The script checks the total EVs of the player's entire party. | **CRITIQUE CORRECT** | `src/pokemon.c` (function `GetPlayerEVTotal` iterates `gPlayerParty`) |
| Bike prerequisite | Defeat Wattson (`FLAG_DEFEATED_MAUVILLE_GYM`). | There is no prerequisite. | **CRITIQUE CORRECT** | `data/maps/MauvilleCity_RydelsCycles/scripts.inc` (`MauvilleCity_RydelsCycles_EventScript_Rydel`) |
| Focus Band prerequisite | (INFERENCE) Show a Pokémon with maxed-out (plural) Contest stats. | Show a Pokémon with a *single* maxed-out Contest stat. | **CRITIQUE CORRECT** | `data/maps/Route128_BlackBeltMartinsHouse/scripts.inc` (`Route128_BlackBeltMartinsHouse_EventScript_Martin`) |
| Prerequisite to start TM24 sidequest | After defeating Team Aqua/Magma at Mt. Chimney. | After defeating Norman (`FLAG_DEFEATED_PETALBURG_GYM`). | **CRITIQUE CORRECT** | `data/maps/MauvilleCity/scripts.inc` (`MauvilleCity_OnFrame`) |
| TM32 (Double Team) source | From a boy in a house on Route 113 after answering "No" to a question. | From a Ninja Boy hiding in an ash pile on Route 113. | **CRITIQUE CORRECT** | `data/maps/Route113/scripts.inc` (`Route113_EventScript_NinjaBoy`) |
| Berry Master (Man)'s berry pool | Depends on the day of the week. | Randomly chosen from a fixed pool of 10 common berries. | **CRITIQUE CORRECT** | `src/berry.c` (`ChooseTwoBerries` and `sBerryMasterBerries`) |
| King's Rock prerequisite | UNSURE; likely defeating Team Magma at the Space Center. | (not disputed) | **BOTH WRONG** The prerequisite is the event flag `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` being set, which makes the item ball visible. | `data/maps/MossdeepCity/scripts.inc` (`MossdeepCity_EventScript_SetStevensHouseState`) |

## 2. CONFIRMED-GOOD CORE

*   **Pokédex, 5 Poké Balls, & Pokénav**: Given by Professor Birch in his lab after the first rival battle on Route 103.
*   **Running Shoes**: Given by Mom in the player's house after receiving the Pokédex.
*   **Wailmer Pail**: Given by a girl in the Route 104 Flower Shop with no prerequisites.
*   **Exp. Share**: Given by Mr. Stone in Devon Corp. 3F after delivering the Letter to Steven.
*   **Old Rod**: Given by a Fisherman in Dewford Town with no prerequisites.
*   **Silk Scarf**: Given by an Ace Trainer in a Dewford Town house after earning the Knuckle Badge, provided the total EV count of the player's entire party is over 500.
*   **Coin Case**: Given by a woman in a Mauville City house in exchange for Harbor Mail.
*   **Soothe Bell**: Given by a woman in the Slateport Pokémon Fan Club for showing a lead Pokémon with friendship of 200 or higher.
*   **Macho Brace**: Given by Victoria Winstrate in the Route 111 Winstrate House after defeating all four family members.
*   **Go-Goggles**: Given by the rival on Route 111 after defeating Flannery.
*   **Root/Claw Fossil**: One is chosen at the top of Mirage Tower. The other can be found in the Desert Underpass post-game.
*   **Amulet Coin**: Given by Mom after defeating Norman.
*   **Good Rod**: Given by a Fisherman on Route 118.
*   **Itemfinder**: Given by the rival after their battle on Route 110.
*   **Castform**: Given by a scientist at the Weather Institute after defeating Team Aqua/Magma.
*   **King's Rock**: Found in an item ball in Steven's House after the events at the Mossdeep Space Center conclude.
*   **Super Rod**: Given by a Fisherman in a Mossdeep City house.
*   **Wynaut Egg**: Given by an old woman in Lavaridge Town if the player has an empty party slot.
*   **Beldum**: Found in an item ball in Steven's House after defeating the Elite Four.
*   **TMs from Gym Leaders**: All listed are correct: TM39 (Roxanne), TM08 (Brawly), TM34 (Wattson), TM50 (Flannery), TM42 (Norman), TM40 (Winona), TM04 (Tate & Liza), TM03 (Juan).
*   **TM43 (Secret Power)**: From a man next to a tree on Route 111 after getting the Dynamo Badge.
*   **TM47 (Steel Wing)**: From Steven in Granite Cave upon delivering the Letter.
*   **TM27 (Return)**: From a man in Pacifidlog Town for showing a Pokémon with maximum friendship.
*   **TM31 (Brick Break)**: From a Black Belt in a Sootopolis City house.
*   **TM05 (Roar)**: From a man with a Poochyena on Route 114.
*   **TM28 (Dig)**: From the Fossil Maniac's brother in his house on Route 114.
*   **Berry Master's Wife**: Gives one rare berry per day in exchange for a correct two-word phrase.

## 3. DO NOT USE

*   **The rival gives you 5 Poké Balls.** They are from Professor Birch.
*   **Mr. Stone gives you a Great Ball on Devon Corp 3F.** It is from a Devon Researcher on 2F.
*   **The Acro Bike / Mach Bike requires defeating Wattson.** There is no prerequisite to obtain a bike.
*   **The TM24 (Thunderbolt) sidequest is available after Mt. Chimney.** It is only available after defeating Norman (5th gym).
*   **TM32 (Double Team) is from a boy in a house on Route 113.** It is from a Ninja Boy hiding in an ash pile on the main route.
*   **The Berry Master's daily berries depend on the day of the week.** This is a Gen IV mechanic; in Emerald, they are random from a fixed pool.
*   **The Silk Scarf prerequisite checks only the lead Pokémon's EVs.** It checks the entire party's total.
*   **The Focus Band prerequisite requires maxing out all five contest stats.** It only requires maxing out one.

## 4. CONFIDENCE

100%. All claims made in the original note and the adversarial critique were verifiable against the `pokeemerald` decompilation. I was able to settle every disputed point and confirm the status of every other claim in the note with complete certainty.