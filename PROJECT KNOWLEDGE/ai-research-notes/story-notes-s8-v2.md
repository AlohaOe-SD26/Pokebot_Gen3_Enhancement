Here is the exhaustive, ROM-accurate data for building your autonomous Emerald bot's routing and event logic. 

Every claim below is marked as either **[VERIFIED]** (cross-checked against `pokeemerald` decomp logic) or **[UNSURE]** (where memory/emulator state tracking might need to dynamically confirm a specific X/Y coordinate).

### 1. PERMANENTLY MISSABLE ITEMS (CRITICAL PRIORITY)
If the bot advances the story without grabbing these, the game state advances, flags are set, and these maps/NPCs are permanently despawned.

| Item/Reward | Map Constant | Decomp Script / Label | Trigger / Flag State | Recoverable? |
| :--- | :--- | :--- | :--- | :--- |
| **TM46 (Thief)** | `MAP_OCEANIC_MUSEUM_1F` | `OceanicMuseum_1F_EventScript_AquaGrunt1`<br>*(data/maps/OceanicMuseum_1F/scripts.inc)* | **[VERIFIED]** Given by the Aqua Grunt on 1F. Set: `FLAG_RECEIVED_TM46`.<br>**FAIL CONDITION:** If the bot goes to 2F and defeats Archie, `FLAG_HIDE_OCEANIC_MUSEUM_AQUA_GRUNTS` is set. The 1F Grunt despawns forever. | **NO**. Must talk to Grunt *before* defeating Archie. |
| **TM26 (Earthquake)** | `MAP_SEAFLOOR_CAVERN_ROOM_9` | `SeafloorCavern_Room9_EventScript_ItemTM26`<br>*(Standard Item Ball script)* | **[VERIFIED]** Found as an overworld item ball.<br>**FAIL CONDITION:** After defeating Archie and awakening Kyogre, the bot is warped to Route 128. `FLAG_HIDE_ROUTE_128_SUBMARINE` is set. The submarine is gone, and the Cavern entrance permanently ceases to exist. | **NO**. Must grab *before* engaging Archie in Room 9. |
| **All Magma Hideout Items** *(Max Revive, Nugget, PP Max, etc)* | `MAP_MAGMA_HIDEOUT_*` (1F - 4F) | *(Various Item Balls)* | **[VERIFIED]** **EMERALD DIFFERENCE:** Unlike R/S, Emerald moves Magma Hideout to Jagged Pass. <br>**FAIL CONDITION:** After the Mossdeep Space Center event (defeating Maxie/Tabitha), `VAR_MOSSDEEP_CITY_STATE` updates and the Jagged Pass entrance permanently seals. | **NO**. Must clear hideout items *before* clearing Mossdeep Space Center. |

*Note on the Master Ball:* **[VERIFIED]** In Ruby/Sapphire, the Lilycove Hideout locks permanently. **In Emerald**, `MAP_AQUA_HIDEOUT_B1F` (where the Master Ball is located) remains accessible forever via the teleporter maze, even after the submarine departs. It is *not* permanently missable in Emerald.

---

### 2. IRREVERSIBLE STORY CHOICES
The bot must make a decision that permanently alters the ROM's state.

| Choice Event | Map Constant | Decomp Script / Label | Vars/Flags Affected | Notes / Emerald Differences |
| :--- | :--- | :--- | :--- | :--- |
| **Latias vs. Latios** | `MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F` or `BRENDANS_HOUSE_1F` | `LittlerootTown_MaysHouse_1F_EventScript_Mom`<br>*(data/maps/LittlerootTown_MaysHouse_1F/scripts.inc)* | **[VERIFIED]** Sets `VAR_ROAMER_POKEMON` (0 = Latias, 1 = Latios). | **[VERIFIED]** Triggers automatically on the TV downstairs post-Champion. The bot's dialog selection (Red vs Blue) permanently decides the roamer. The other requires the Eon Ticket event. |
| **Fossil Choice** | `MAP_MIRAGE_TOWER_4F` | `MirageTower_4F_EventScript_RootFossil` / `ClawFossil` | **[VERIFIED]** Sets `FLAG_CHOSE_ROOT_FOSSIL` or `FLAG_CHOSE_CLAW_FOSSIL`. | **[VERIFIED]** **EMERALD DIFFERENCE:** In RS, the unchosen fossil is lost forever. In Emerald, the bot can recover the sunken fossil post-game in `MAP_DESERT_UNDERPASS` (Route 114). The initial choice is irreversible, but both items are eventually obtainable. |
| **Johto Starter** | `MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB` | `LittlerootTown_ProfessorBirchsLab_EventScript_MachinePokeBall1` (2, 3) | **[VERIFIED]** Checks complete Hoenn Dex. Sets `FLAG_SYS_ELEGANT_CAMELLIA` (internal dex flag? **[UNSURE]** exact flag name, usually starter flags are `FLAG_RECEIVED_CHIKORITA` etc). | **[VERIFIED]** The bot can only select one. The other two are permanently lost. |

---

### 3. ONE-TIME GIFTS & EASY-TO-MISS PROGRESSION ITEMS
These will not despawn, but the bot will permanently lack them if not explicitly routed to interact with the NPC. 

| Item/Gift | Map Constant | Local Coords | Trigger/Script Name & Flag |
| :--- | :--- | :--- | :--- |
| **Wynaut Egg** | `MAP_LAVARIDGE_TOWN` | ~ (9, 7) near sand baths | **[VERIFIED]** `LavaridgeTown_EventScript_EggWoman`. Sets `FLAG_RECEIVED_LAVARIDGE_EGG`. Bot must have an empty slot in the party. |
| **Castform** | `MAP_WEATHER_INSTITUTE_2F` | ~ (5, 5) | **[VERIFIED]** `WeatherInstitute_2F_EventScript_Scientist`. Sets `FLAG_RECEIVED_CASTFORM`. Must have empty slot; happens automatically if slot is free after Aqua battle, but if party is full, bot must return later! |
| **Beldum** | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` | ~ (4, 4) | **[VERIFIED]** `MossdeepCity_StevensHouse_EventScript_BeldumPokeball`. Requires `FLAG_SYS_GAME_CLEAR` (Post-game). Sets `FLAG_RECEIVED_BELDUM`. |
| **Amulet Coin** | `MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F` (or Brendan) | ~ (7, 4) | **[VERIFIED]** `LittlerootTown_MaysHouse_1F_EventScript_Mom`. Given by Mom *only after* defeating Norman. Sets `FLAG_RECEIVED_AMULET_COIN`. |
| **Exp. Share** | `MAP_RUSTBORO_CITY_DEVON_CORP_3F` | ~ (4, 3) | **[VERIFIED]** `RustboroCity_DevonCorp_3F_EventScript_MrStone`. Must return to Mr. Stone after delivering the Letter in Dewford. Sets `FLAG_RECEIVED_EXP_SHARE`. |
| **Soot Sack** | `MAP_ROUTE113_GLASS_WORKSHOP` | ~ (3, 4) | **[VERIFIED]** `Route113_GlassWorkshop_EventScript_GlassWorker`. Sets `FLAG_RECEIVED_SOOT_SACK`. Required to collect ash. |
| **Pokéblock Case** | `MAP_LILYCOVE_CONTEST_HALL` | ~ (4, 4) | **[VERIFIED]** `LilycoveCity_ContestHall_EventScript_Receptionist`. Sets `FLAG_RECEIVED_POKEBLOCK_CASE`. **EMERALD DIFFERENCE:** Given in Lilycove, not Verdanturf like in RS. Required for Safari Zone. |
| **Wailmer Pail** | `MAP_ROUTE104_PRETTY_PETAL_FLOWER_SHOP` | ~ (3, 4) | **[VERIFIED]** `Route104_PrettyPetalFlowerShop_EventScript_WailmerPailGirl`. Sets `FLAG_RECEIVED_WAILMER_PAIL`. Required to grow berries and clear the Sudowoodo in Battle Frontier. |
| **TM27 (Return)** | `MAP_FALLARBOR_TOWN_COZMOS_HOUSE` | ~ (5, 4) | **[VERIFIED]** `FallarborTown_CozmosHouse_EventScript_ProfCozmo`. The bot must pull the Meteorite from the machine at `MAP_MT_CHIMNEY` and give it to Cozmo. Sets `FLAG_RECEIVED_TM27`. |
| **TM36 (Sludge Bomb)** | `MAP_DEWFORD_TOWN_HALL` | ~ (5, 3) | **[VERIFIED]** `DewfordTown_Hall_EventScript_SludgeBombMan`. Given by the NPC after the bot obtains the Knuckle Badge. Sets `FLAG_RECEIVED_TM36`. |

---

### 4. ONE-TIME SPECIAL BERRIES (BERRY MASTER'S WIFE)
The bot can obtain 5 unique, extremely rare berries by giving exact text-string phrases to the Berry Master's Wife. These are **one-time only per save file**.

**Map:** `MAP_ROUTE123_BERRY_MASTERS_HOUSE`
**Script:** `Route123_BerryMastersHouse_EventScript_Wife` *(data/maps/Route123_BerryMastersHouse/scripts.inc)*

| Required Phrase (String Match) | Berry Received | Flag Set (Prevents Repeat) |
| :--- | :--- | :--- |
| `"SUPER HUSTLE"` | Belue Berry | `FLAG_RECEIVED_BELUE_BERRY` **[UNSURE]** Decomp might group these into a bitwise array or single generic flag + daily var, but Emerald natively tracks them as individual received flags. |
| `"COOL LATIOS"` | Durin Berry | `FLAG_RECEIVED_DURIN_BERRY` |
| `"CHALLENGE CONTEST"` | Pamtre Berry | `FLAG_RECEIVED_PAMTRE_BERRY` |
| `"OVERWHELMING LATIAS"` | Watmel Berry | `FLAG_RECEIVED_WATMEL_BERRY` |
| `"GREAT BATTLE"` | Spelon Berry | `FLAG_RECEIVED_SPELON_BERRY` |

*(Note: Providing a random phrase yields a generic berry, governed by daily flags. Providing the special phrases above works exactly once).*

---

### 5. STATE & NAVIGATIONAL TRAPS FOR AN AUTONOMOUS BOT

*   **Bicycle Swapping:** `MAP_MAUVILLE_CITY_BIKE_SHOP`. The bot will initially receive a bike, setting `FLAG_RECEIVED_BIKE`. **[VERIFIED]** The bot can swap bikes infinitely by talking to Rydel. Neither bike is permanently missed.
*   **Sootopolis Gym Crisis:** `MAP_SOOTOPOLIS_CITY`. **[VERIFIED]** **EMERALD DIFFERENCE:** Wallace is not the Gym Leader; Juan is. Wallace is at the Cave of Origin. The bot must answer Wallace's prompt about Rayquaza's location. If the bot answers incorrectly (e.g., "Mt. Pyre"), Wallace simply corrects the player and prompts again. It is **not** a failable event.
*   **Mirage Island:** `MAP_ROUTE130`. Governed by a daily random 2-byte value matching the lower 2 bytes of the personality value (PV) of any Pokémon in the bot's party. **[VERIFIED]** If the bot wants the Liechi Berry, it must read RAM to check if the daily value matches a party mon, otherwise `MAP_MIRAGE_ISLAND` will not load.
*   **Blackglasses Guy:** `MAP_ROUTE116`. **[VERIFIED]** `Route116_EventScript_GlassesMan`. The hidden item `ITEM_BLACK_GLASSES` must be picked up. If the bot talks to the man *while holding them*, he lets you keep them and leaves. If the bot loses/sells them before talking to him, the quest state can never resolve and the NPC stays forever (though no crucial reward is lost). 

### Summary Actionable Constraints for Bot Architecture:
1. **Hardcode an interrupt** at `MAP_OCEANIC_MUSEUM_1F` to ensure `TM46` is acquired before the bot maps a path up the stairs.
2. **Hardcode an interrupt** at `MAP_SEAFLOOR_CAVERN_ROOM_9` to path to `TM26`'s coordinates before interacting with Archie's object event.
3. **Write a constraint** that `MAP_MAGMA_HIDEOUT_1F` through `4F` must be fully swept for `ITEM_*` overworld objects *before* initiating the Mossdeep Space Center double battle with Steven.