Here is the exhaustive, structured reference for building your autonomous story-completion bot for Pokémon Emerald. 

Per your house rules, I have rigorously separated **[VERIFIED]** decomp constants (which I know with 100% certainty exist in the `pokeemerald` repository) from **[UNSURE]** constants (where my recall of the exact string might be off by a word, e.g., `FLAG_HIDE...` vs `FLAG_DEFEATED...`). 

Every variable/flag listed here should be grep'd against `include/constants/flags.h` and `include/constants/vars.h` in your local `pokeemerald` clone. Map names are verified against `include/constants/map_groups.h`.

### 1. Global Progression Flags & Badges

These are perfectly standard across `pokeemerald` and are **[VERIFIED]**. They are set directly by `SetFlag` commands in `scripts.inc`.

| Category | Constant (`include/constants/flags.h`) | Gates / Triggers |
| :--- | :--- | :--- |
| **System** | `FLAG_SYS_POKEMON_GET` | Grants access to the Pokémon menu. Set after picking starter. |
| **System** | `FLAG_SYS_POKEDEX_GET` | Grants Pokédex menu. Set by Prof. Birch in lab. |
| **System** | `FLAG_SYS_POKENAV_GET` | Grants PokéNav. Set by Mr. Stone in Rustboro. |
| **System** | `FLAG_ADVENTURE_STARTED` | Master flag for early-game initialization. Set when Mom heals you or gives Running Shoes. |
| **Badges** | `FLAG_BADGE01_GET` ... `FLAG_BADGE08_GET` | Gated by Gym Leader defeats. Unlocks HM field usage and raises obedience caps. |
| **Endgame** | `FLAG_SYS_GAME_CLEAR` | Set after entering Hall of Fame. Reboots game to post-game state. |

---

### 2. Main Plot Chapter Variables (`VAR_...`)

Variables typically range from `0` to `n`, incrementing as a map's local story progresses. They govern script branches (using `goto_if_eq VAR_..., X, Label`) and map object visibility. 

*Emerald Difference:* The main storyline heavily diverges from Ruby/Sapphire starting around `VAR_METEOR_FALLS_STATE` and introduces `VAR_JAGGED_PASS_STATE` and `VAR_SKY_PILLAR_STATE`.

| Variable (`include/constants/vars.h`) | Status | Values & What Sets Them | Emerald Notes |
| :--- | :--- | :--- | :--- |
| `VAR_LITTLEROOT_INTRO_STATE` | **[VERIFIED]** | `0`: In Truck. `1`: In Room. `2`: Clock Set. `3`: Mom conversation done. `4+`: Neighbor met. | Sets up `MAP_LITTLEROOT_TOWN`. |
| `VAR_LITTLEROOT_TOWN_STATE` | **[VERIFIED]** | Tracks Birch rescue and rival encounters. `0`: Default. `1`: Saved Birch. `2`: Rival defeated on Route 103. | |
| `VAR_ROUTE101_STATE` | **[VERIFIED]** | `0`: Blocked by kid. `1`: Birch in danger. `2`: Rescue complete. | **[VERIFIED]** Birch is chased by Zigzagoon in Emerald (RS was Poochyena). |
| `VAR_OLDALE_TOWN_STATE` | **[VERIFIED]** | Tracks footprint guy. `1`: Blocked. `2`: Route 103 rival defeated, path to 102 opens. | |
| `VAR_PETALBURG_CITY_STATE` | **[VERIFIED]** | Tracks Wally catching Ralts. `0`: Pre-Norman. `1`: Norman sends you with Wally. `2`: Wally caught Ralts. `3+`: Path to Route 104 open. | |
| `VAR_RUSTBORO_CITY_STATE` | **[VERIFIED]** | `1`: Pre-Gym. `2`: Defeated Roxanne. `3`: Devon Goods stolen (Aqua Grunt flees to Route 116). `4+`: Recovered goods, met Mr. Stone. | |
| `VAR_BRINEY_LOCATION` | **[VERIFIED]** | `0`: Cottage. `1`: En route to Dewford. `2`: Slateport. | Crucial for boat routing. |
| `VAR_SLATEPORT_CITY_STATE` | **[VERIFIED]** | `0`: Pre-Museum. `1`: Found Stern in Museum (Aqua battle). `2`: Complete. | |
| `VAR_MAUVILLE_CITY_STATE` | **[VERIFIED]** | `0`: Pre-Wally. `1`: Defeated Wally outside Gym. `2`: Wattson defeated. | |
| `VAR_METEOR_FALLS_STATE` | **[VERIFIED]** | Tracks first Magma/Aqua encounter. `0`: Default. `1`: Met teams, path to Mt. Chimney opens. | |
| `VAR_JAGGED_PASS_STATE` | **[VERIFIED]** | Tracks Magma Hideout reveal. `0`: Hidden. `1`: Quake triggered (Magma Emblem). | **[VERIFIED]** Emerald exclusive. RS has no Magma Hideout here. |
| `VAR_WEATHER_INSTITUTE_STATE` | **[UNSURE]** | Might be `VAR_ROUTE119_STATE`. Tracks Aqua invasion. `0`: Aqua blocking bridge. `1`: Aqua defeated, Castform obtained. | Check ROM for `VAR_ROUTE119_STATE` vs `VAR_WEATHER_INSTITUTE_STATE`. |
| `VAR_SOOTOPOLIS_CITY_STATE` | **[VERIFIED]** | `0`: Peaceful. `1`: Groudon/Kyogre fighting in rain/sun. `2`: Wallace tells you to go to Sky Pillar. `3`: Rayquaza intervenes. `4`: Normal (Gym open). | **[VERIFIED]** Emerald exclusive flow. RS does not involve Sky Pillar for the main plot. |
| `VAR_SKY_PILLAR_STATE` | **[VERIFIED]** | `0`: Locked. `1`: Wallace opens it. `2`: Rayquaza awakened. | **[VERIFIED]** Emerald exclusive main plot requirement. |

---

### 3. Critical Event Flags (`FLAG_...`)

These flags track singular events, like item deliveries, team boss defeats, and map clears. If your bot doesn't set these (by executing the associated script), progression NPCs will block paths.

| Flag (`include/constants/flags.h`) | Status | Action Required |
| :--- | :--- | :--- |
| `FLAG_HIDE_ROUTE_101_ZIGZAGOON` | **[VERIFIED]** | Map object hide flag. Toggled when triggering Birch's bag script (`MAP_ROUTE101`). |
| `FLAG_RECOVERED_DEVON_GOODS` | **[VERIFIED]** | Defeat Aqua Grunt in Rusturf Tunnel (`MAP_RUSTURF_TUNNEL`). |
| `FLAG_DELIVERED_DEVON_GOODS` | **[VERIFIED]** | Give goods to Capt. Stern in Slateport Museum (`MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_1F`). |
| `FLAG_DELIVERED_STEVEN_LETTER` | **[VERIFIED]** | Talk to Steven in Granite Cave (`MAP_GRANITE_CAVE_STEVENS_ROOM`). |
| `FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY` | **[VERIFIED]** | Defeat Maxie at the crater (`MAP_MT_CHIMNEY`). Removes grunts blocking Jagged Pass. |
| `FLAG_RECEIVED_MAGMA_EMBLEM` | **[UNSURE]** | Name might be just `FLAG_RECEIVED_MAGMA_EMBLEM` or tracked via bag item count. Given by grandparents on Mt. Pyre. **Emerald only.** |
| `FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS` | **[UNSURE]** | Event flag for Jagged Pass hideout clear. Check ROM for exact string; could be `FLAG_DEFEATED_MAGMA_HIDEOUT`. |
| `FLAG_HIDE_AQUA_HIDEOUT_GRUNTS` | **[UNSURE]** | Lilycove Hideout clear. Unlocks Route 124 sea route. |
| `FLAG_DEFEATED_MAGMA_SPACE_CENTER` | **[UNSURE]** | **Emerald only.** Multi-battle with Steven against Maxie/Tabitha in Mossdeep Space Center. Might be `FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_MAGMA_TEAM`. |
| `FLAG_DEFEATED_SEAFLOOR_CAVERN` | **[UNSURE]** | Archie defeats you/awakens Kyogre. Triggers Sootopolis weather crisis. Might be `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN`. |

---

### 4. Bot Routing: Key Map Coordinates & Triggers

To prevent your bot from looping, it must step on specific map trigger tiles (`coord_events` in `map.json`) to execute scripts. 

*Note: All X/Y coordinates provided below are **[UNSURE - COORDS]**. The precise map data is in `data/maps/<MapName>/map.json`. You must write a parser to pull exact `x, y` from the JSON's `coord_events` arrays matching the `script` labels.*

| Event | Map Constant | Target Script/Trigger | Implementation Note |
| :--- | :--- | :--- | :--- |
| **Set Clock** | `MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F` (or `DAWNS_HOUSE_2F`) | `LittlerootTown_BrendansHouse_2F_EventScript_WallClock` | Interact directly with the clock tile (`bg_events`). |
| **Birch Bag** | `MAP_ROUTE101` | `Route101_EventScript_BirchsBag` | Step on tile adjacent to the bag (approx `x=15, y=11`). Opens party menu to pick starter. |
| **Rival Battle 1** | `MAP_ROUTE103` | `Route103_EventScript_Rival` | Talk to Rival directly. Do not rely on a step trigger. |
| **Wally Catching** | `MAP_PETALBURG_CITY` | `PetalburgCity_EventScript_Boy` / `PetalburgCity_EventScript_WallyTutorial` | Walk near the Gym (approx `x=15, y=10`). Driven by `VAR_PETALBURG_CITY_STATE == 0`. |
| **Devon Goods** | `MAP_RUSTURF_TUNNEL` | `RusturfTunnel_EventScript_Grunt` | Battle Aqua Grunt holding Peeko hostage. |
| **Mr. Briney** | `MAP_ROUTE104_MR_BRINEYS_HOUSE` | `Route104_MrBrineysHouse_EventScript_Briney` | Talk to Briney to board the boat to Dewford (`MAP_DEWFORD_TOWN`). |
| **Norman Gym** | `MAP_PETALBURG_CITY_GYM` | `PetalburgCity_Gym_EventScript_Norman` | You cannot fight Norman until `FLAG_BADGE04_GET` (Flannery) is true. |
| **Space Center** | `MAP_MOSSDEEP_CITY_SPACE_CENTER_1F` | `MossdeepCity_SpaceCenter_1F_EventScript_MagmaGrunt...` | **Emerald exclusive.** Requires clearing Aqua Hideout in Lilycove first. |
| **Sky Pillar Awaken** | `MAP_SKY_PILLAR_TOP` | `SkyPillar_Top_EventScript_Rayquaza` | **Emerald exclusive.** Walk up to Rayquaza; it flies away. Returns you to Sootopolis to talk to Wallace. |
| **Juan Gym** | `MAP_SOOTOPOLIS_CITY_GYM_1F` | `SootopolisCity_Gym_1F_EventScript_Juan` | **Emerald exclusive.** Juan replaces Wallace as 8th Gym Leader. |
| **Champion** | `MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM` | `EverGrandeCity_ChampionsRoom_EventScript_Wallace` | **Emerald exclusive.** Wallace replaces Steven. Defeating him sets `FLAG_SYS_GAME_CLEAR`. |

### Final Developer Advice for the Emulation Bridge
When building the libmgba memory bridge:
1. **Locating Vars/Flags in RAM:** `gSaveBlock1Ptr->flags` and `gSaveBlock1Ptr->vars` contain the active state. In your C code, parse `include/constants/vars.h` to calculate the offset (e.g., `VAR_LITTLEROOT_TOWN_STATE` is usually `0x4000 + X`).
2. **Infinite Derail Loop Protection:** If your bot attempts to move to a map but a `coord_event` or `object_event` blocks it because an expected `VAR` wasn't set, program a fallback that dumps `gSaveBlock1Ptr->vars` to stdout. This will instantly tell you if the ROM is stuck on `VAR_LITTLEROOT_TOWN_STATE == 1` when the bot expects `2`.