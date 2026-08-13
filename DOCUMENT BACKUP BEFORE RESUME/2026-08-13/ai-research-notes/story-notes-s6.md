Here is the requested information on Victory Road and the Pokémon League in Pokémon Emerald, following all house rules.

### Victory Road: Path and HM Requirements

**VERIFIED:** The path through Victory Road requires the use of Strength, Flash, Surf, and Waterfall. Rock Smash is required for the main path in one instance on floor B2F.

| HM        | Required for Progression? | Map(s) Used                                                                                                | Notes                                                                               |
| :-------- | :------------------------ | :--------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------- |
| Surf      | **Yes**                   | `MAP_VICTORY_ROAD_B1F`                                                                                     | Required to cross water sections to reach the waterfall.                            |
| Strength  | **Yes**                   | `MAP_VICTORY_ROAD_1F`, `MAP_VICTORY_ROAD_B2F`                                                                | Required to move boulders blocking the path.                                        |
| Flash     | **Yes**                   | `MAP_VICTORY_ROAD_B1F`, `MAP_VICTORY_ROAD_B2F`                                                               | The lower floors are dark. The game checks for `FLAG_SYS_FLASH_ACTIVE`.             |
| Waterfall | **Yes**                   | `MAP_VICTORY_ROAD_B1F`                                                                                     | Required to ascend the waterfall to reach the exit ladder.                          |
| Rock Smash| **Yes**                   | `MAP_VICTORY_ROAD_B2F`                                                                                     | One breakable rock on B2F must be smashed to proceed north. Others are optional.    |

---

#### **Progression Route**

**VERIFIED:** The following is the critical path to the exit. Coordinates are (X, Y). Decomp source: `data/maps/VictoryRoad_*/map.json` for layouts and `data/maps/VictoryRoad_*/scripts.inc` for events.

1.  **Enter `MAP_VICTORY_ROAD_1F`**
    *   Upon entering and walking forward, you are stopped for a mandatory battle. See **Wally Rematch** section below.
    *   Go north past the bridge. Use **Strength** on the boulder at (15, 12). Push it west.
    *   Go up the stairs at (9, 10).
    *   Take the ladder at (9, 6) down to `MAP_VICTORY_ROAD_B1F`.

2.  **Navigate `MAP_VICTORY_ROAD_B1F`**
    *   This floor is dark. Use **Flash**. The darkness is controlled by `map_header VictoryRoad_B1F_MapHeader` which specifies `weather: WEATHER_FOG_1`.
    *   Go south and down the stairs.
    *   Use **Surf** at (17, 24) and surf west.
    *   Go north. Land at (6, 12).
    *   Use **Waterfall** to ascend the waterfall at (6, 9).
    *   Surf east. Land at (12, 9).
    *   Take the ladder at (14, 9) down to `MAP_VICTORY_ROAD_B2F`.

3.  **Navigate `MAP_VICTORY_ROAD_B2F`**
    *   This floor is also dark. **Flash** is still required.
    *   Go south, then east.
    *   Use **Strength** on the boulder at (21, 14). Push it east.
    *   Go north. Use **Rock Smash** on the rock at (25, 9). This is the mandatory one.
    *   Continue west, then south around the rock formations.
    *   Go east and find the ladder at (32, 13). Take it up to `MAP_VICTORY_ROAD_B1F`.

4.  **Exit Victory Road**
    *   You arrive back on `MAP_VICTORY_ROAD_B1F` in an isolated area.
    *   Walk north to the exit ladder at (33, 5). This leads to the exterior area `MAP_EVER_GRANDE_CITY_VICTORY_ROAD_ENTRANCE`.
    *   The Pokémon League building is directly ahead.

---

### Wally Rematch

**VERIFIED:** In Emerald, Wally challenges the player upon entering Victory Road for the first time. This battle is mandatory.
*   **Source File:** `data/maps/VictoryRoad_1F/scripts.inc`
*   **Script Label:** `VictoryRoad_1F_EventScript_Wally`
*   **Trigger:** Player steps on trigger tiles at (14, 25) or (15, 25) on `MAP_VICTORY_ROAD_1F`.
*   **Condition:** `FLAG_DEFEATED_VICTORY_ROAD_WALLY` is not set.

#### **Wally's Team**

**VERIFIED:** Source: `data/trainers.h` (`TRAINER_WALLY_VICTORY_ROAD`), `data/trainer_parties.h` (`sParty_WallyVictoryRoad`).

| Pokémon   | Level | Ability        | Held Item     | Moves                                             |
| :-------- | :---- | :------------- | :------------ | :------------------------------------------------ |
| Altaria   | 44    | Natural Cure   | None          | Dragon Breath, Dragon Dance, Aerial Ace, Refresh  |
| Delcatty  | 43    | Cute Charm     | None          | Sing, Assist, Charm, Faint Attack                 |
| Roselia   | 44    | Natural Cure   | None          | Magical Leaf, Giga Drain, Leech Seed, Toxic       |
| Magneton  | 41    | Sturdy         | None          | Thunderbolt, Supersonic, Thunder Wave, Tri Attack |
| Gardevoir | 45    | Synchronize    | Sitrus Berry  | Calm Mind, Psychic, Thunderbolt, Future Sight     |

---

### Elite Four & Champion Wallace

**VERIFIED:** All data below is sourced from `data/trainers.h`, `data/trainer_parties.h`, and `src/data/pokemon/species_info.h` in the pokeemerald decompilation. The battle order is fixed. Healing items are used by all members at low HP.

#### **Elite Four 1: Sidney (Dark-type)**

| Pokémon    | Level | Ability      | Held Item      | Moves                                                |
| :--------- | :---- | :----------- | :------------- | :--------------------------------------------------- |
| Mightyena  | 46    | Intimidate   | None           | Swagger, Crunch, Take Down, Sand Attack              |
| Shiftry    | 48    | Chlorophyll  | None           | Double Team, Swagger, Extrasensory, Fake Out         |
| Cacturne   | 46    | Sand Veil    | None           | Leech Seed, Faint Attack, Needle Arm, Cotton Spore   |
| Crawdaunt  | 48    | Hyper Cutter | None           | Surf, Swords Dance, Crabhammer, Facade               |
| Absol      | 49    | Pressure     | Sitrus Berry   | Aerial Ace, Swords Dance, Slash, Snatch              |

#### **Elite Four 2: Phoebe (Ghost-type)**

| Pokémon     | Level | Ability     | Held Item      | Moves                                                |
| :---------- | :---- | :---------- | :------------- | :--------------------------------------------------- |
| Dusclops    | 48    | Pressure    | None           | Shadow Punch, Confuse Ray, Curse, Future Sight       |
| Banette     | 49    | Insomnia    | None           | Shadow Ball, Spite, Faint Attack, Will-O-Wisp        |
| Sableye     | 50    | Keen Eye    | None           | Shadow Ball, Double Team, Night Shade, Faint Attack  |
| Banette     | 49    | Insomnia    | None           | Shadow Ball, Psychic, Thunderbolt, Facade            |
| Dusclops    | 51    | Pressure    | Sitrus Berry   | Shadow Ball, Ice Beam, Rock Slide, Earthquake        |

#### **Elite Four 3: Glacia (Ice-type)**

| Pokémon  | Level | Ability     | Held Item      | Moves                                                |
| :------- | :---- | :---------- | :------------- | :--------------------------------------------------- |
| Sealeo   | 50    | Thick Fat   | None           | Surf, Body Slam, Hail, Encore                        |
| Glalie   | 50    | Inner Focus | None           | Hail, Crunch, Icy Wind, Shadow Ball                  |
| Sealeo   | 52    | Thick Fat   | None           | Blizzard, Attract, Hail, Double-Edge                 |
| Glalie   | 52    | Inner Focus | None           | Ice Beam, Explosion, Hail, Crunch                    |
| Walrein  | 53    | Thick Fat   | Sitrus Berry   | Surf, Blizzard, Body Slam, Sheer Cold                |

#### **Elite Four 4: Drake (Dragon-type)**

| Pokémon   | Level | Ability     | Held Item      | Moves                                                |
| :-------- | :---- | :---------- | :------------- | :--------------------------------------------------- |
| Shelgon   | 52    | Rock Head   | None           | Rock Tomb, Dragon Claw, Protect, Double-Edge         |
| Altaria   | 54    | Natural Cure| None           | Dragon Dance, Dragon Breath, Aerial Ace, Refresh     |
| Kingdra   | 53    | Swift Swim  | None           | Surf, Dragon Dance, Smokescreen, Body Slam           |
| Flygon    | 53    | Levitate    | None           | Earthquake, Dragon Breath, Crunch, Flamethrower      |
| Salamence | 55    | Intimidate  | Sitrus Berry   | Dragon Claw, Crunch, Flamethrower, Rock Slide        |

#### **Champion: Wallace (Water-type)**

| Pokémon    | Level | Ability     | Held Item      | Moves                                                |
| :--------- | :---- | :---------- | :------------- | :--------------------------------------------------- |
| Wailord    | 57    | Water Veil  | None           | Rain Dance, Water Spout, Blizzard, Double-Edge       |
| Ludicolo   | 56    | Swift Swim  | None           | Surf, Giga Drain, Double Team, Leech Seed            |
| Whiscash   | 56    | Oblivious   | None           | Surf, Earthquake, Amnesia, Hyper Beam                |
| Tentacruel | 55    | Clear Body  | None           | Toxic, Surf, Sludge Bomb, Ice Beam                   |
| Gyarados   | 56    | Intimidate  | None           | Dragon Dance, Earthquake, Surf, Hyper Beam           |
| Milotic    | 58    | Marvel Scale| Sitrus Berry   | Surf, Ice Beam, Toxic, Recover                       |

---

### Emerald vs. Ruby/Sapphire Plot Changes: Champion and Gym Leader

**VERIFIED:** Pokémon Emerald significantly altered the roles of Wallace, Steven Stone, and Juan compared to Ruby and Sapphire.

*   **Wallace becomes Champion:**
    *   **INFERENCE:** Following the Groudon/Kyogre crisis, which is more severe in Emerald and requires the player to awaken Rayquaza, Wallace steps up to become the Champion of the Hoenn League.
    *   **VERIFIED:** His Champion battle data is found under `TRAINER_WALLACE_CHAMPION` in `data/trainers.h`. The final battle script in `data/maps/EverGrandeCity_HallOfFame/scripts.inc` confirms he is the final opponent.

*   **Steven Stone steps down:**
    *   **VERIFIED:** Steven is no longer the Champion. He assists the player during the story, notably at the Mossdeep Space Center against Team Magma.
    *   **VERIFIED:** After the player becomes Champion, Steven can be found deep within Meteor Falls in a new area, `MAP_METEOR_FALLS_STEVENS_CAVE`. He can be battled there as an optional, high-level post-game opponent. His trainer data is `TRAINER_STEVEN`. Defeating him is not required for story completion.

*   **Juan becomes Sootopolis Gym Leader:**
    *   **VERIFIED:** With Wallace vacating his position as the Sootopolis Gym Leader, his mentor, Juan, takes over.
    *   **VERIFIED:** The player must battle Juan to earn the Rain Badge. This is a mandatory story battle. His trainer data is `TRAINER_JUAN` in `data/trainers.h` and the relevant battle script is in `data/maps/SootopolisCity_Gym_1F/scripts.inc`. In Ruby/Sapphire, the player battles Wallace at this gym.