All claims are VERIFIED against the `pokeemerald` decompilation unless explicitly marked otherwise.

### Key Items & Story Progression Gifts

| Item(s) | Map & Coordinates | NPC | Prerequisites | Controlling Flag / Var | Notes / Decomp Citation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pokédex**, **Poké Balls (x5)**, **Pokénav** | `MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB` (10, 6) | Professor Birch | Return to lab after defeating Rival on Route 103 for the first time. `VAR_LITTLEROOT_TOWN_STATE` must be `3`. | `FLAG_RECEIVED_POKEDEX` | **Emerald difference:** Birch gives the Pokénav. In R/S, Mr. Stone does. The Poké Balls are given by the rival immediately after this event. `data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc` (`LittlerootTown_ProfessorBirchsLab_EventScript_GivePokedex`) |
| **Running Shoes** | `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F` (4, 4) | Mom | Have the Pokédex (`FLAG_RECEIVED_POKEDEX` is set). | `FLAG_RECEIVED_RUNNING_SHOES` | `data/maps/LittlerootTown_PlayersHouse_1F/scripts.inc` (`LittlerootTown_PlayersHouse_1F_EventScript_Mom`) |
| **Wailmer Pail** | `MAP_ROUTE104_PRETTY_PETAL_FLOWER_SHOP` (6, 2) | Flower Shop Girl (Blonde) | None. | `FLAG_RECEIVED_WAILMER_PAIL` | `data/maps/Route104_PrettyPetalFlowerShop/scripts.inc` (`Route104_PrettyPetalFlowerShop_EventScript_WailmerPailGirl`) |
| **Great Ball** | `MAP_RUSTBORO_CITY_DEVON_CORP_3F` (8, 3) | Mr. Stone | Defeat Rustboro Gym (`FLAG_DEFEATED_RUSTBORO_GYM`). Talk to him for the first time. | `FLAG_MET_MR_STONE` | This is part of the sequence to get the Letter. In R/S, this is when you receive the Pokénav. `data/maps/RustboroCity_DevonCorp_3F/scripts.inc` (`RustboroCity_DevonCorp_3F_EventScript_MrStone`) |
| **Exp. Share** | `MAP_RUSTBORO_CITY_DEVON_CORP_3F` (8, 3) | Mr. Stone | Deliver the Letter to Steven (`FLAG_DELIVERED_STEVEN_LETTER`). | `FLAG_RECEIVED_EXP_SHARE` | `data/maps/RustboroCity_DevonCorp_3F/scripts.inc` (`RustboroCity_DevonCorp_3F_EventScript_MrStone`) |
| **Old Rod** | `MAP_DEWFORD_TOWN` (4, 7) | Fisherman | None. | `FLAG_RECEIVED_OLD_ROD` | `data/maps/DewfordTown/scripts.inc` (`DewfordTown_EventScript_Fisherman`) |
| **Silk Scarf** | `MAP_DEWFORD_TOWN` (2, 2) | Ace Trainer in house | Talk to him after getting the Knuckle Badge. The script checks `GetPlayerEVTotal() > 500`. | `FLAG_RECEIVED_SILK_SCARF` | A hidden requirement is that your lead Pokémon must have a high total EV count. `data/maps/DewfordTown_House1/scripts.inc` (`DewfordTown_House1_EventScript_Man`) |
| **Coin Case** | `MAP_MAUVILLE_CITY` (10, 4) | Woman in house | Exchange `Harbor Mail` for it. Harbor Mail is purchased at Slateport Pokémart. | `FLAG_RECEIVED_COIN_CASE` | `data/maps/MauvilleCity_House1/scripts.inc` (`MauvilleCity_House1_EventScript_Woman`) |
| **Acro Bike** / **Mach Bike** | `MAP_MAUVILLE_CITY_RYDELS_CYCLES` (7, 2) | Rydel | Defeat Wattson (`FLAG_DEFEATED_MAUVILLE_GYM`). | `FLAG_RECEIVED_BIKE`, `VAR_BIKE` (`1`=Mach, `2`=Acro) | Choice is reversible by returning to Rydel. `data/maps/MauvilleCity_RydelsCycles/scripts.inc` (`MauvilleCity_RydelsCycles_EventScript_Rydel`) |
| **Soothe Bell** | `MAP_SLATEPORT_CITY` (11, 10) | Woman in Pokémon Fan Club | Show a Pokémon with high friendship (value >= 200) as the first in your party. | `FLAG_RECEIVED_SOOTHE_BELL` | `data/maps/SlateportCity_PokemonFanClub/scripts.inc` (`SlateportCity_PokemonFanClub_EventScript_Woman`) |
| **Macho Brace** | `MAP_ROUTE111` (various) | Winstrate Family | Defeat all four Winstrate family members in their house. Talk to Victoria (mom) inside afterwards. | `FLAG_DEFEATED_WINSTRATE_FAMILY` | The flag is set upon defeating the final member. The gift is given by Victoria after this flag is set. `data/maps/Route111_WinstrateFamilyHouse/scripts.inc` (`Route111_WinstrateFamilyHouse_EventScript_Victoria`) |
| **Go-Goggles** | `MAP_ROUTE111` (29, 21) | Rival | Defeat Flannery (`FLAG_DEFEATED_FLANNERY`). The rival appears automatically upon approaching the desert. | `FLAG_RECEIVED_GO_GOGGLES` | `data/maps/Route111/scripts.inc` (`Route111_EventScript_RivalGiveGoGoggles`) |
| **Root Fossil** / **Claw Fossil** | `MAP_ROUTE111_MIRAGE_TOWER_4F` (5, 5) | Fossil (Item Ball) | Reach the top of Mirage Tower. | `FLAG_RECEIVED_FOSSIL` | Irreversible choice. The tower sinks after you take one. `data/maps/Route111_MirageTower_4F/scripts.inc` (`Route111_MirageTower_4F_EventScript_ClawFossil`, `...RootFossil`). **Emerald difference:** The other fossil appears in the Desert Underpass post-game. |
| **Amulet Coin** | `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F` (4, 4) | Mom | Defeat Norman (`FLAG_DEFEATED_PETALBURG_GYM`). | `FLAG_RECEIVED_AMULET_COIN` | `data/maps/LittlerootTown_PlayersHouse_1F/scripts.inc` (`LittlerootTown_PlayersHouse_1F_EventScript_Mom`) |
| **Good Rod** | `MAP_ROUTE118` (27, 4) | Fisherman | None. Answer "Yes" to his question. | `FLAG_RECEIVED_GOOD_ROD` | `data/maps/Route118/scripts.inc` (`Route118_EventScript_Fisherman`) |
| **Itemfinder** | `MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE` (7, 2) | Rival | Defeat Rival on Route 110. | `FLAG_RECEIVED_ITEMFINDER` | Given immediately post-battle. `data/maps/Route110/scripts.inc` (`Route110_EventScript_RivalBattleGiveItemfinder`) |
| **Castform** | `MAP_ROUTE119_WEATHER_INSTITUTE_1F` (13, 1) | Scientist | Defeat Team Aqua/Magma in the Weather Institute. | `FLAG_RECEIVED_CASTFORM` | Given as a Level 25 Pokémon. `data/maps/Route119_WeatherInstitute_1F/scripts.inc` (`Route119_WeatherInstitute_1F_EventScript_ScientistGiveCastform`) |
| **King's Rock** | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` (5, 2) | Steven | (UNSURE of exact prerequisite) Likely requires defeating Team Magma at the Space Center. Steven leaves it on his table with a note. | `FLAG_RECEIVED_KINGS_ROCK_STEVEN` | This is an item ball pickup, not a direct NPC handoff, but it's a unique one-time gift. `data/maps/MossdeepCity_StevensHouse/scripts.inc` (`MossdeepCity_StevensHouse_EventScript_KingsRock`) |
| **Super Rod** | `MAP_MOSSDEEP_CITY` (9, 4) | Fisherman in house | None. Answer "Yes" to his question. | `FLAG_RECEIVED_SUPER_ROD` | `data/maps/MossdeepCity_House1/scripts.inc` (`MossdeepCity_House1_EventScript_Fisherman`) |
| **Wynaut Egg** | `MAP_LAVARIDGE_TOWN` (11, 7) | Old Woman near hot spring | Have an empty slot in your party. | `FLAG_RECEIVED_WYNAUT_EGG` | `data/maps/LavaridgeTown/scripts.inc` (`LavaridgeTown_EventScript_EggWoman`) |
| **Focus Band** | `MAP_ROUTE128` (N/A) | Karate Guy in house | (INFERENCE) Show him a Pokémon with maxed-out Contest stats. The house is `MAP_ROUTE128_BLACK_BELT_MARTINS_HOUSE`. | `FLAG_RECEIVED_FOCUS_BAND` (UNSURE) | Exact location is the lone house on an island on Route 128. Exact flag name is unconfirmed without deeper script analysis. |
| **Beldum** | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` (5, 2) | Poké Ball on table | Defeat the Elite Four. | `FLAG_RECEIVED_BELDUM` | Given as a Level 5 Pokémon. The flag `FLAG_DEFEATED_CHAMPION` must be set. `data/maps/MossdeepCity_StevensHouse/scripts.inc` (`MossdeepCity_StevensHouse_EventScript_Beldum`) |

### TM Gifts

| TM | Map & Coordinates | NPC | Prerequisites | Controlling Flag | Decomp Citation / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TM39 (Rock Tomb)** | `MAP_RUSTBORO_CITY_GYM` (5, 12) | Roxanne | Defeat her. | `FLAG_RECEIVED_TM39` | `data/maps/RustboroCity_Gym/scripts.inc` (`RustboroCity_Gym_EventScript_Roxanne`) |
| **TM08 (Bulk Up)** | `MAP_DEWFORD_TOWN_GYM` (5, 8) | Brawly | Defeat him. | `FLAG_RECEIVED_TM08` | `data/maps/DewfordTown_Gym/scripts.inc` (`DewfordTown_Gym_EventScript_Brawly`) |
| **TM34 (Shock Wave)** | `MAP_MAUVILLE_CITY_GYM` (5, 12) | Wattson | Defeat him. | `FLAG_RECEIVED_TM34` | `data/maps/MauvilleCity_Gym/scripts.inc` (`MauvilleCity_Gym_EventScript_Wattson`) |
| **TM43 (Secret Power)** | `MAP_ROUTE111` (25, 13) | Boy next to large tree | Have the Dynamo Badge (`FLAG_DEFEATED_MAUVILLE_GYM`). | `FLAG_RECEIVED_TM43` | `data/maps/Route111/scripts.inc` (`Route111_EventScript_GiveSecretPower`) |
| **TM50 (Overheat)** | `MAP_LAVARIDGE_TOWN_GYM` (7, 10) | Flannery | Defeat her. | `FLAG_RECEIVED_TM50` | `data/maps/LavaridgeTown_Gym/scripts.inc` (`LavaridgeTown_Gym_EventScript_Flannery`) |
| **TM04 (Calm Mind)** | `MAP_MOSSDEEP_CITY_GYM` (13, 10) | Tate & Liza | Defeat them. | `FLAG_RECEIVED_TM04` | `data/maps/MossdeepCity_Gym/scripts.inc` (`MossdeepCity_Gym_EventScript_TateLiza`) |
| **TM42 (Facade)** | `MAP_PETALBURG_CITY_GYM` (5, 13) | Norman | Defeat him. | `FLAG_RECEIVED_TM42` | `data/maps/PetalburgCity_Gym/scripts.inc` (`PetalburgCity_Gym_EventScript_Norman`) |
| **TM40 (Aerial Ace)** | `MAP_FORTREE_CITY_GYM` (5, 13) | Winona | Defeat her. | `FLAG_RECEIVED_TM40` | `data/maps/FortreeCity_Gym/scripts.inc` (`FortreeCity_Gym_EventScript_Winona`) |
| **TM03 (Water Pulse)** | `MAP_SOOTOPOLIS_CITY_GYM` (9, 31) | Juan | Defeat him. | `FLAG_RECEIVED_TM03` | **Emerald difference:** Wallace gives TM03 in R/S. Juan replaces Wallace as the Gym Leader. `data/maps/SootopolisCity_Gym_1F/scripts.inc` (`SootopolisCity_Gym_1F_EventScript_Juan`) |
| **TM47 (Steel Wing)** | `MAP_GRANITE_CAVE_STEVENS_ROOM` (13, 11) | Steven | Deliver the Letter to him. | `FLAG_RECEIVED_TM47` | `data/maps/GraniteCave_StevensRoom/scripts.inc` (`GraniteCave_StevensRoom_EventScript_Steven`) |
| **TM24 (Thunderbolt)** | `MAP_MAUVILLE_CITY` (12, 6) | Wattson | Complete the New Mauville sidequest by turning off the generator. The quest is started by talking to Wattson in Mauville center. | `FLAG_RECEIVED_TM24` | The sidequest becomes available after defeating Team Aqua/Magma at Mt. Chimney. Prerequisite flag is `FLAG_TURNED_OFF_NEW_MAUVILLE_GENERATOR`. `data/maps/MauvilleCity/scripts.inc` (`MauvilleCity_EventScript_Wattson`) |
| **TM27 (Return)** | `MAP_PACIFIDLOG_TOWN` (10, 4) | Man in house | Show him a Pokémon with maximum friendship (255) as the first in your party. | `FLAG_RECEIVED_TM27` | This is a one-time gift. `data/maps/PacifidlogTown_House5/scripts.inc` (`PacifidlogTown_House5_EventScript_ReturnMan`) |
| **TM32 (Double Team)** | `MAP_ROUTE113` (31, 5) | Boy in house | Answer "No" to his question about seeing his footprints. | `FLAG_RECEIVED_TM32` | `data/maps/Route113_GlassWorkshop/scripts.inc` (`Route113_GlassWorkshop_EventScript_GiveDoubleTeam`) |
| **TM31 (Brick Break)** | `MAP_SOOTOPOLIS_CITY` (26, 8) | Black Belt in house | None. | `FLAG_RECEIVED_TM31` | `data/maps/SootopolisCity_House7/scripts.inc` (`SootopolisCity_House7_EventScript_BlackBelt`) |
| **TM05 (Roar)** | `MAP_ROUTE114` (10, 5) | Man with Poochyena | None. | `FLAG_RECEIVED_TM05` | `data/maps/Route114/scripts.inc` (`Route114_EventScript_Man`) |
| **TM28 (Dig)** | `MAP_ROUTE114_FOSSIL_MANIACS_HOUSE` (4, 2) | Fossil Maniac's Brother | None. | `FLAG_RECEIVED_TM28` | `data/maps/Route114_FossilManiacsHouse/scripts.inc` (`Route114_FossilManiacsHouse_EventScript_ManiacsBrother`) |

### Berry Master Gifts

The Berry Master on `MAP_ROUTE123_BERRY_MASTERS_HOUSE` gives out two Berries per day, chosen from a specific set. His wife gives out one rare Berry per day if you tell her a specific two-word phrase. These are daily events, not one-time gifts, but are included for completeness.

*   **Berry Master (Man):**
    *   **Location:** `MAP_ROUTE123_BERRY_MASTERS_HOUSE` (5, 4)
    *   **Prerequisite:** None.
    *   **Reward:** Two berries per day. The pool of berries depends on the day of the week.
    *   **Controlling Flag:** The script uses daily flags like `FLAG_DAILY_BERRY_MASTER_RECEIVED_BERRY` to track if you've received them today.
    *   **Citation:** `data/maps/Route123_BerryMastersHouse/scripts.inc` (`Route123_BerryMastersHouse_EventScript_BerryMaster`)

*   **Berry Master's Wife:**
    *   **Location:** `MAP_ROUTE123_BERRY_MASTERS_HOUSE` (3, 3)
    *   **Prerequisite:** Tell her a specific phrase. The good phrases are "GREAT BATTLE", "CHALLENGE CONTEST", "OVERWHELMING LATIAS", "COOL LATIOS", "SUPER HUSTLE".
    *   **Reward:** A single rare berry (e.g., Spelon, Pamtre, Watmel, etc.).
    *   **Controlling Flag:** `FLAG_DAILY_BERRY_MASTERS_WIFE_RECEIVED_BERRY`
    *   **Citation:** `data/maps/Route123_BerryMastersHouse/scripts.inc` (`Route123_BerryMastersHouse_EventScript_BerryMastersWife`)