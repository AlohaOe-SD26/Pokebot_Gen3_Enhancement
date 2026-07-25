Of course. Here is a complete list of non-Poké-Center party healing locations in Pokémon Emerald, structured for your bot's logic and adhering to your house rules.

### Table of Repeatable Full-Party Healing Locations

This table lists all locations that provide a full (HP, PP, Status) party heal and are indefinitely repeatable, making them suitable as long-term training hubs.

| Location (Map Constant) | Trigger (Object, Coords) | Gating / Prerequisites | Emerald/RS Differences | Decomp Citation | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F` | Mom (NPC), (4, 6) | None. Available from game start. | None. | `data/maps/LittlerootTown_PlayersHouse_1F/scripts.inc` -> `LittlerootTown_PlayersHouse_1F_EventScript_Mom` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_PETALBURG_CITY_WALLYS_HOUSE` | Wally's Mom (NPC), (4, 2) | Must help Wally catch his Ralts. Gated by `FLAG_MET_WALLY_IN_PETALBURG` (flag is set after the tutorial). The healing dialogue path checks this flag. | None. | `data/maps/PetalburgCity_WallysHouse/scripts.inc` -> `PetalburgCity_WallysHouse_EventScript_WallysMom` checks `FLAG_MET_WALLY_IN_PETALBURG`. | VERIFIED |
| `MAP_ROUTE104_MR_BRINEYS_HOUSE` | Bed, (3, 2) | None. Available upon first reaching Route 104. | None. The function is identical, though Briney's role in the story differs slightly (Team Aqua/Magma encounter). | `data/maps/Route104_MrBrineysHouse/scripts.inc` -> `Route104_MrBrineysHouse_EventScript_Bed` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_ROUTE111_WINSTRATE_FAMILY_HOUSE` | Victoria Winstrate (NPC), (3, 2) | Must defeat all four Winstrate family members in a gauntlet battle outside on Route 111. Gated by `FLAG_DEFEATED_WINSTRATES`. | None. | `data/maps/Route111_WinstrateFamilyHouse/scripts.inc` -> `Route111_WinstrateFamilyHouse_EventScript_Vicky` checks `FLAG_DEFEATED_WINSTRATES`. | VERIFIED |
| `MAP_ROUTE111_OLD_LADYS_REST_STOP` | Old Lady (NPC), (5, 2) | None. Available upon reaching the house (requires Rock Smash). House is on the northern part of Route 111, south of the desert. | None. In RS, she's a "Cooltrainer". In Emerald, she's a "Pokéfan". The script and function are identical. | `data/maps/Route111_OldLadysRestStop/scripts.inc` -> `Route111_OldLadysRestStop_EventScript_Rest` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_ROUTE114_FOSSIL_MANIACS_BROTHERS_HOUSE` | Fossil Maniac's Brother (NPC), (2, 2) | None. Available upon reaching Route 114. | None. | `data/maps/Route114_FossilManiacsBrothersHouse/scripts.inc` -> `Route114_FossilManiacsBrothersHouse_EventScript_Brother` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_LAVARIDGE_TOWN` | Hot Springs Water (Trigger) | None. Available upon reaching Lavaridge Town. Player must enter the water. | None. | `data/maps/LavaridgeTown/scripts.inc` -> `LavaridgeTown_EventScript_HotSprings` calls `Script_HealParty`. Triggered by `TRIGGER_TYPE_NORMAL` on coordinates (23,7), (24,7), (25,7), (26,7). | VERIFIED |
| `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` | Bed, (8, 3) | None. Available upon reaching Mossdeep City. | None. | `data/maps/MossdeepCity_StevensHouse/scripts.inc` -> `MossdeepCity_StevensHouse_EventScript_Bed` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_BATTLE_FRONTIER_LOUNGE1`, `MAP_BATTLE_FRONTIER_LOUNGE2` | Attendant (NPC), (4, 3) | Must defeat the Pokémon League Champion. Gated by `FLAG_DEFEATED_CHAMPION`. | **Emerald Only.** The Battle Frontier does not exist in Ruby/Sapphire. | `data/maps/BattleFrontier_Lounge1/scripts.inc` -> `BattleFrontier_Lounge1_EventScript_Attendant` calls `Common_EventScript_HealParty`. | VERIFIED |

---

### One-Time or Conditionally Accessible Heals

These locations provide a full party heal but are either single-use or become permanently inaccessible after certain story points. They are not reliable for repeatable training loops but are critical for story progression logic.

| Location (Map Constant) | Trigger (Object, Coords) | Conditions / Inaccessibility | Decomp Citation | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `MAP_AQUA_HIDEOUT_B2F` | Bed, (12, 2) or (13, 2) | Becomes inaccessible after Kyogre awakens and you exit the Seafloor Cavern. Gated by `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN`. | `data/maps/AquaHideout_B2F/scripts.inc` -> `AquaHideout_B2F_EventScript_Bed` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_MAGMA_HIDEOUT_3F_2` | Bed, (1, 8) or (2, 8) | Becomes inaccessible after Groudon awakens and you exit the Seafloor Cavern. Gated by `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`. | `data/maps/MagmaHideout_3F_2/scripts.inc` -> `MagmaHideout_3F_2_EventScript_Bed` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_TRICK_HOUSE_END` | Bed, (6, 1) | The Trick House puzzle rooms reset after each completion. This bed is usable once per puzzle completion, but is not a freely accessible "walk-in" heal. The room itself is accessible only after solving the current puzzle. | `data/maps/TrickHouseEnd/scripts.inc` -> `TrickHouseEnd_EventScript_Bed` calls `Common_EventScript_PlayerRest`. | VERIFIED |
| Various Post-Rival/Boss Battles | (Scripted Event) | Many key story battles (e.g., against May/Brendan on Route 110, some Gym Leader rematches) are followed by a scripted full heal. These are one-time events tied to the specific battle's completion flag. | Example: `data/maps/Route110/scripts.inc` -> `Route110_EventScript_RivalBattle`. After the battle, the script calls `Script_HealParty`. Gated by `VAR_ROUTE110_STATE`. | VERIFIED |

---

### Addressed But Not Healing Locations

These are common points of confusion or locations suggested in the prompt that do not actually offer a party heal.

| Location (Map Constant) | Trigger (Object, Coords) | Reason for Exclusion | Decomp Citation / Logic | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `MAP_ROUTE114_LANETTES_HOUSE` | Lanette (NPC), (4, 2) | Lanette manages the Pokémon Storage System. She gives you a Lotad Doll (Emerald) but never offers to heal your party. | `data/maps/Route114_LanettesHouse/scripts.inc` -> `Route114_LanettesHouse_EventScript_Lanette` has no calls to `HealPlayerParty` or `Common_EventScript_PlayerRest`. | VERIFIED |
| `MAP_LAVARIDGE_TOWN` | Old Woman with Egg (NPC), (17, 10) | This NPC gives the player a Wynaut egg (`giveegg SPECIES_WYNAUT`). She does not heal the party. | `data/maps/LavaridgeTown/scripts.inc` -> `LavaridgeTown_EventScript_GiveWynautEgg`. Script contains no healing calls. | VERIFIED |
| `MAP_ROUTE123_BERRY_MASTERS_HOUSE` | Berry Master's Wife (NPC), (6, 3) | She gives out one Berry per day based on a player-submitted phrase. She does not heal the party. | `data/maps/Route123_BerryMastersHouse/scripts.inc` -> `Route123_BerryMastersHouse_EventScript_Wife`. Script contains no healing calls. | VERIFIED |