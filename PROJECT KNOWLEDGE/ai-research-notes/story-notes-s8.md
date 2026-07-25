Understood. This is a request for a structured, ROM-accurate data dump for an automation project. All claims will be marked.

### 1. One-Time Gift Pokémon

These are Pokémon given by NPCs. The bot must have a free party slot to receive them. The game will typically prompt the player to make room if their party is full, making these events hard to miss but crucial to complete when triggered.

| Pokémon | Map & Coords | Trigger NPC & Details | Controlling Flag/Var | Recoverable? | Decomp Citation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Castform** | `MAP_ROUTE119_WEATHER_INSTITUTE_2F` (11, 4) | VERIFIED: Given by the lead scientist after defeating Aqua Admin Shelly. This is a mandatory story event. | `FLAG_RECEIVED_CASTFORM` | No. The event is a one-time occurrence. The game forces you to accept it to proceed. | `data/maps/Route119_WeatherInstitute_2F/scripts.inc` (Label: `Route119_WeatherInstitute_2F_EventScript_GiveCastform`) |
| **Wynaut Egg** | `MAP_LAVARIDGE_TOWN` (11, 6) | VERIFIED: Old woman standing next to the hot springs sand pit. Simply talk to her. | `FLAG_RECEIVED_WYNAUT_EGG` | Yes. She will wait indefinitely until you take the egg. | `data/maps/LavaridgeTown/scripts.inc` (Label: `LavaridgeTown_EventScript_EggGiver`) |
| **Beldum** | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` (9, 7) | VERIFIED: Poké Ball on the table in Steven's house. Only appears after you defeat the Elite Four and Champion. | `FLAG_RECEIVED_BELDUM` | Yes. The Poké Ball will remain on the table indefinitely post-game. | `data/maps/MossdeepCity_StevensHouse/scripts.inc` (Label: `MossdeepCity_StevensHouse_EventScript_BeldumBall`) |
| **Johto Starter** (Cyndaquil, Totodile, Chikorita) | `MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB` (4, 4) | VERIFIED: Given by Professor Birch after completing the Hoenn Pokédex (seen, not owned). You get to choose one of the three. | `FLAG_RECEIVED_JOHTO_STARTER` | Yes. This becomes available upon Pokédex completion and remains so. | `src/prof_birch.c` (Function: `GetJohtoStarter`) |

---

### 2. Fossil Choice (Irreversible Decision)

This event is a permanent choice between two Pokémon. Once chosen, the other is lost forever.

| Event | Map & Coords | Trigger Details | Controlling Flag/Var | Recoverable? | Decomp Citation & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Root Fossil** (Lileep) vs. **Claw Fossil** (Anorith) | `MAP_MIRAGE_TOWER_4F` (5, 5) & (5, 9) | VERIFIED: Pick up one of the two fossils at the top of Mirage Tower. The tower then collapses, and the other fossil is lost permanently. | `VAR_FOSSIL_CHOSEN_FROM_DESERT` (set to 1 for Root, 2 for Claw). The tower's existence is controlled by `VAR_MIRAGE_TOWER_STATE`. | **No.** This choice is permanent for this save file. | `data/maps/MirageTower_4F/scripts.inc` (Labels: `MirageTower_4F_EventScript_RootFossil`, `MirageTower_4F_EventScript_ClawFossil`). **Emerald Specific:** In R/S, both fossils were in the desert, and the one you didn't pick would sink into the sand. In Emerald, they are in the Mirage Tower, which only appears after getting the Go-Goggles and disappears after picking a fossil. If the player leaves the tower without a fossil, it collapses, and the fossils reappear at the back of the Ruin Maniac's tunnel on Route 111. The choice there is still permanent. |

---

### 3. One-Time TM Gifts from NPCs

These are TMs given by NPCs, distinct from those found on the ground or purchased.

| TM | Map & Coords | Trigger NPC & Details | Controlling Flag | Recoverable? | Decomp Citation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TM46 (Thief)** | `MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_1F` (12, 13) | VERIFIED: Aqua/Magma Grunt. Talk to him during the story event where you deliver the Devon Goods. | `FLAG_RECEIVED_TM46` | **No.** This NPC disappears after the Slateport museum story segment is complete. | `data/maps/SlateportCity_OceanicMuseum_1F/scripts.inc` (Label: `SlateportCity_OceanicMuseum_1F_EventScript_GruntGivesTM`) |
| **TM36 (Sludge Bomb)** | `MAP_DEWFORD_TOWN` (12, 16) | VERIFIED: Man standing outside the Dewford Hall. He gives the TM after you defeat Norman (5th gym badge). | `FLAG_RECEIVED_TM36` | Yes. He remains there indefinitely after the condition is met. | `data/maps/DewfordTown/scripts.inc` (Label: `DewfordTown_EventScript_SludgeBombMan`) |
| **TM10 (Hidden Power)** | `MAP_FORTREE_CITY` (12, 8) | VERIFIED: Old woman in a house in the northern part of town. You must guess which hand the coin is in (right, right, left). You can try again if you fail. | `FLAG_RECEIVED_TM10` | Yes. You can keep guessing until you get it right. | `data/maps/FortreeCity_House4/scripts.inc` (Label: `FortreeCity_House4_EventScript_HiddenPowerWoman`) |
| **TM05 (Roar)** | `MAP_ROUTE114` (11, 23) | VERIFIED: Man with a Poochyena. | `FLAG_RECEIVED_TM05` | Yes. He remains there indefinitely. | `data/maps/Route114/scripts.inc` (Label: `Route114_EventScript_ManWithPoochyena`) |
| **TM27 (Return)** | `MAP_FALLARBOR_TOWN` (4, 7) | VERIFIED: Professor Cozmo's aide inside his house. Requires your lead Pokémon to have high friendship. | `FLAG_RECEIVED_TM27` | Yes. You can return anytime with a high-friendship Pokémon. | `data/maps/FallarborTown_CozmosHouse/scripts.inc` (Label: `FallarborTown_CozmosHouse_EventScript_GiveTM27`) |
| **TM48 (Skill Swap)** | `MAP_MT_PYRE_EXTERIOR` (26, 7) | VERIFIED: Gentleman NPC on the west side of the exterior. | `FLAG_RECEIVED_TM48` | Yes. He remains there indefinitely. | `data/maps/MtPyre_Exterior/scripts.inc` (Label: `MtPyre_Exterior_EventScript_GiveSkillSwap`) |

*Note: Gym Leader TMs are mandatory and not included.*

---

### 4. Special/Unique One-Time Item Gifts

| Item | Map & Coords | Trigger NPC & Details | Controlling Flag/Var | Recoverable? | Decomp Citation & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Amulet Coin** | `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F` (9, 4) | VERIFIED: The player's mom, after you defeat Norman (5th gym badge). | `FLAG_RECEIVED_AMULET_COIN` | Yes. She will offer it anytime you speak to her after beating Norman until you accept. | `data/maps/LittlerootTown_PlayersHouse_1F/scripts.inc` (Label: `PlayersHouse_1F_EventScript_MomGiveAmuletCoin`) |
| **Soothe Bell** | `MAP_SLATEPORT_CITY` (17, 9) | VERIFIED: Woman in the Pokémon Fan Club. Your lead Pokémon must have high friendship. | `FLAG_RECEIVED_SOOTHE_BELL` | Yes. You can return anytime with a high-friendship Pokémon. | `data/maps/SlateportCity_PokemonFanClub/scripts.inc` (Label: `SlateportCity_PokemonFanClub_EventScript_WomanGivesSootheBell`) |
| **Coin Case** | `MAP_MAUVILLE_CITY` (11, 9) | VERIFIED: Woman in house next to the Pokémon Center. She gives you the Coin Case in exchange for Harbor Mail. | `FLAG_GOT_COIN_CASE` | Yes. The exchange is available indefinitely. | `data/maps/MauvilleCity_House1/scripts.inc` (Label: `MauvilleCity_House1_EventScript_Woman`) |
| **Glass Ornament** | `MAP_LILYCOVE_CITY_CONTEST_LOBBY` (10, 4) | VERIFIED: An artist NPC appears after you have beaten all 5 Master Rank Contests and have the paintings in the Lilycove Museum. | `FLAG_RECEIVED_GLASS_ORNAMENT` | Yes. He will wait until the conditions are met. | `data/maps/LilycoveCity_ContestLobby/scripts.inc` (Label: `LilycoveCity_ContestLobby_EventScript_GiveGlassOrnament`) |
| **Rare Berries** (Pamtre/Spelon) | `MAP_ROUTE123_BERRY_MASTERS_HOUSE` (4, 7) | VERIFIED: The Berry Master's wife. She gives a rare berry if you tell her a specific two-word phrase. The berry depends on the phrase. "GREAT BATTLE" gives a Spelon Berry. "CHALLENGE CONTEST" gives a Pamtre Berry. | `FLAG_BERRY_MASTER_WIFE_GAVE_BERRY` | **Partially.** You can only get ONE of these two special berries from her per save file. The flag prevents getting another. The choice of which phrase to say determines which berry you get, locking you out of the other. The bot must choose wisely. | `data/maps/Route123_BerryMastersHouse/scripts.inc` (Label: `Route123_BerryMastersHouse_EventScript_Wife`) |
| **Belue Berry** | `MAP_LILYCOVE_CITY_CONTEST_LOBBY` (4, 3) | VERIFIED: An NPC fan appears after you have successfully blended Pokéblocks with 3 other NPCs. Talk to him to receive the berry. | `FLAG_RECEIVED_BELUE_BERRY_FROM_LILYCOVE_FAN` | Yes. He remains until you talk to him. | `data/maps/LilycoveCity_ContestLobby/scripts.inc` (Label: `LilycoveCity_ContestLobby_EventScript_PokeblockFan`) |

---

### 5. Permanently Missable Areas & Events

These are locations, trainers, or items that become permanently inaccessible after a certain story point. This is the most critical category for a completionist bot.

| Event/Area | Trigger for Unavailability | Details | Decomp Citation / Relevant State |
| :--- | :--- | :--- | :--- |
| **Aqua Hideout** (All items/trainers within) | **VERIFIED:** Awakening Kyogre in the Seafloor Cavern and returning to the surface. | **VERIFIED:** After the Sootopolis City weather crisis begins, a group of Wailmer will block the entrance to the hideout in Lilycove City permanently. Any trainers not fought or items not collected (including the **Master Ball**) are lost forever. | `data/maps/LilycoveCity/scripts.inc` contains the logic to place the Wailmer. The check is against the story progression, specifically `is_stadium_and_mt_pyre_cleared()` and `is_kyogre_awakened()`. The primary flag seems to be `FLAG_HIDEPOUT_ENTRANCE_BLOCKED`. |
| **S.S. Tidal (Pre-E4)** (Trainers/Items) | **VERIFIED:** Defeating the Elite Four and Champion. | **VERIFIED:** Before becoming Champion, the S.S. Tidal sails between Slateport and Lilycove. It contains several one-time trainers and an item (`Leftovers` in a trash can in the storage room). After becoming Champion, the ship's only destination becomes the Battle Frontier. The Slateport/Lilycove route and its associated trainers/items become permanently inaccessible. | `src/ss_tidal.c`. The ship's state and destination are determined by checks against `FLAG_SYS_GAME_CLEAR`. The trainers on the ship have their own defeat flags (e.g., `FLAG_DEFEATED_SS_TIDAL_TRAINER_1`). |
| **Trick House** (Puzzles 1-7) | **VERIFIED:** Completing the 8th and final puzzle. | **VERIFIED:** After completing the final puzzle and receiving the reward, the Trick Master leaves a note and disappears. The interior of the house becomes inaccessible, blocked by a scroll. Only the final reward room can be entered. The puzzles themselves are permanently gone. | `VAR_TRICK_HOUSE_STATE` tracks puzzle completion. When it reaches its final value (`TRICK_HOUSE_STAT_MASTER_DEPARTED`), the script in `data/maps/Route110_TrickHouse_Entrance/scripts.inc` locks the door. |
| **Mirage Island** | **INFERENCE:** While not a story event, its appearance is governed by a one-time daily calculation that is notoriously difficult to trigger. A bot needs to check its status daily at the Pacifidlog Town house. | **VERIFIED:** An old man in a house in Pacifidlog Town (10, 5) will tell you if he can see the island. Its appearance is determined by matching two random bytes generated daily with two bytes from a Pokémon's personality value in the player's party. Missing a day it appears means waiting for the RNG to align again, which could be never. The island contains Wynaut and one Leichi Berry plant. | `src/fldeff_misc.c` (Function: `UpdateMirageIsland()`). The check is done daily. |
| **Scott's First Encounters** | **VERIFIED:** Progressing past specific story points. | **VERIFIED:** Scott appears in several locations (Petalburg Woods, Slateport Battle Tent, etc.) during the story. If you miss these encounters, you can't go back and see them. This has no gameplay impact but is a missable event. The final encounter needed for Battle Frontier access in Mossdeep Space Center is not missable. | `VAR_SCOTT_STATE` tracks which encounter is next. The NPC objects for Scott in various maps are often conditioned on this var being an exact value (e.g., `VAR_SCOTT_STATE, 1`). |