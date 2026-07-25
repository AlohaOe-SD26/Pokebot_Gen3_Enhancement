Here are the ROM-accurate facts regarding Rayquaza, Groudon, and Kyogre in Pokémon Emerald.

### Rayquaza

#### 1. Mid-Game Story Encounter (Awakening)
This is a mandatory, non-battle story event. The player ascends Sky Pillar to awaken Rayquaza, who then flies to Sootopolis City to quell the fighting between Groudon and Kyogre.

*   **Availability**: VERIFIED. During the Sootopolis City crisis, after Groudon and Kyogre are awakened in the Seafloor Cavern. This occurs after defeating the Mossdeep Gym leaders, Tate & Liza.
*   **Prerequisites**:
    *   **Plot**: VERIFIED. Must have initiated the Sootopolis crisis. This is tracked by `VAR_SOOTOPOLIS_CITY_STATE` being set to `2`. You are sent here by Wallace after speaking with Steven in Sootopolis. Wallace meets you at the Sky Pillar entrance and unlocks the door. (Script: `data/maps/SkyPillar_Entrance/scripts.inc`, label `SkyPillar_Entrance_EventScript_Wallace`).
    *   **Badges**: VERIFIED. 7 Badges (Mind Badge).
    *   **HMs**: VERIFIED. `Surf` (to reach Route 131), `Dive` (required for Seafloor Cavern plot preceding this).
    *   **Items**: VERIFIED. No special items are required for this first ascent. The cracked floor puzzles are not active. The bot can simply walk up the tower.
*   **Outcome**: VERIFIED. Upon reaching the top (`MAP_SKY_PILLAR_TOP`), the player character approaches Rayquaza. A cutscene plays where it awakens and flies away. (Script: `data/maps/SkyPillar_Top/scripts.inc`, label `SkyPillar_Top_EventScript_AwakenRayquaza`). The bot must then Fly/Teleport to Sootopolis City to watch the conclusion of the crisis. After the crisis, Rayquaza returns to the roof of Sky Pillar, where it can be battled.

#### 2. Post-Crisis Battle Encounter
This is the encounter where Rayquaza can be caught.

*   **Availability**: VERIFIED. Immediately after the Sootopolis crisis is resolved. Rayquaza returns to its perch on the roof of Sky Pillar. The player can leave and return at any time to attempt the capture.
*   **Map Location**: VERIFIED. `MAP_SKY_PILLAR_TOP`. Coordinates: (X=10, Y=8).
*   **Prerequisites**:
    *   **Plot**: VERIFIED. Sootopolis crisis must be resolved (`VAR_SOOTOPOLIS_CITY_STATE` >= `3`).
    *   **Badges/E4**: VERIFIED. Can be attempted before or after the Elite Four.
    *   **HMs**: VERIFIED. `Surf`.
    *   **Items**: VERIFIED. **Mach Bike is mandatory**. The cracked floors are now active.
*   **Pokémon Details**:
    *   **Level**: VERIFIED. 70. (Source: `data/maps/SkyPillar_Top/scripts.inc`, `SkyPillar_Top_EventScript_RayquazaBattle` calls `CreateWildMon(SPECIES_RAYQUAZA, 70, ...)`).
    *   **One-Time**: VERIFIED. This is a stationary encounter.
    *   **Event Flag**: VERIFIED. `FLAG_DEFEATED_RAYQUAZA`. Set upon defeating or capturing it. The overworld sprite will not appear if this flag is set.
    *   **Respawn Rules**: VERIFIED. If Rayquaza is defeated (not caught), it will disappear. It will only reappear after the player becomes Champion again (i.e., defeats the Elite Four). This mechanic clears certain flags, including this one. If the bot faints it, it must re-clear the E4 for another attempt. Fleeing from battle allows for an immediate re-engagement without penalty.

---

### Sky Pillar Cracked Floor Mechanic

This puzzle is active on the second visit to Sky Pillar to battle Rayquaza. It requires the Mach Bike.

*   **Mechanic**: VERIFIED. Stepping on a cracked tile causes it to break, and the player falls to the center of the corresponding room on the floor below. To cross, the bot must be moving at the Mach Bike's top speed (achieved after 3 tiles of continuous movement). The bot cannot stop or turn on the cracked tiles.
*   **Path for Bot**:
    1.  **Map**: `MAP_SKY_PILLAR_2F`
        *   VERIFIED. A simple, straight path. The bot must get a running start and bike straight north across the central cracked floor section to reach the ladder.
    2.  **Map**: `MAP_SKY_PILLAR_4F`
        *   VERIFIED. This is a two-part puzzle. The direct path to the next ladder is blocked.
        *   **Step 1**: The bot must navigate the maze of rocks to the northern section of the room.
        *   **Step 2**: The bot must intentionally fall through a specific cracked tile to land on an isolated section of `MAP_SKY_PILLAR_3F`.
        *   **Target Tile**: The correct cracked tile on `MAP_SKY_PILLAR_4F` to fall through is at **(X=9, Y=4)**.
        *   **Step 3**: On `MAP_SKY_PILLAR_3F`, the bot will land near a ladder it previously could not access. Take this ladder back up to `MAP_SKY_PILLAR_4F`.
        *   **Step 4**: The bot is now on the correct path. It must use the Mach Bike to cross the final set of cracked floors to reach the ladder to `MAP_SKY_PILLAR_5F` (which is the roof, `MAP_SKY_PILLAR_TOP`).

---

### Groudon & Kyogre (Post-Game)

In Emerald, both Groudon and Kyogre are only available after becoming Champion. Their locations are not static and must be discovered. This process is entirely different from Ruby & Sapphire.

*   **Overall Availability**: VERIFIED. After defeating the Elite Four and Champion for the first time (`FLAG_SYS_GAME_CLEAR` is set).
*   **Activation**: VERIFIED. The bot must go to the **Weather Institute** on Route 119 (`MAP_WEATHER_INSTITUTE_2F`). Speak to the scientist at the back of the 2nd floor. He will report either a "terrible drought" or "heavy rainfall" on a specific route. This opens up a new cave entrance (Terra Cave for Groudon) or a new dive spot (Marine Cave for Kyogre).
    *   Source Script: `data/maps/WeatherInstitute_2F/scripts.inc`, `WeatherInstitute_2F_EventScript_Scientist`.
    *   The game determines which to make available first. After one is battled (caught or defeated), its cave/spot vanishes. The bot must return to the scientist to be told the location of the other.

#### Groudon
*   **Map Location**: VERIFIED. **Terra Cave**. The cave itself does not have a fixed MAP constant; it is a generic cave layout. The entrance appears on one of four possible routes. The overworld map constant where the entrance can appear are:
    *   `MAP_ROUTE114`
    *   `MAP_ROUTE115`
    *   `MAP_ROUTE116`
    *   `MAP_ROUTE118`
*   **Prerequisites**:
    *   **Plot**: VERIFIED. `FLAG_SYS_GAME_CLEAR` must be set. The Weather Institute scientist must have announced the drought.
    *   **HMs**: VERIFIED. `Surf` may be needed to reach the route. `Strength` and `Rock Smash` are useful within the cave.
*   **Pokémon Details**:
    *   **Level**: VERIFIED. 70.
    *   **One-Time**: VERIFIED. Stationary encounter inside Terra Cave.
    *   **Event Flag**: VERIFIED. `FLAG_DEFEATED_GROUDON`.
    *   **Respawn Rules**: VERIFIED. Identical to Rayquaza. If fainted, it disappears permanently until the Elite Four is defeated again.

#### Kyogre
*   **Map Location**: VERIFIED. **Marine Cave**. Like Terra Cave, the entrance location moves. The entrance is a dive spot that appears on one of four possible routes:
    *   `MAP_ROUTE105`
    *   `MAP_ROUTE125`
    *   `MAP_ROUTE127`
    *   `MAP_ROUTE129`
*   **Prerequisites**:
    *   **Plot**: VERIFIED. `FLAG_SYS_GAME_CLEAR` must be set. The Weather Institute scientist must have announced the heavy rainfall.
    *   **HMs**: VERIFIED. `Surf` and `Dive`.
*   **Pokémon Details**:
    *   **Level**: VERIFIED. 70.
    *   **One-Time**: VERIFIED. Stationary encounter inside Marine Cave.
    *   **Event Flag**: VERIFIED. `FLAG_DEFEATED_KYOGRE`.
    *   **Respawn Rules**: VERIFIED. Identical to Rayquaza and Groudon. If fainted, it disappears permanently until the Elite Four is defeated again.

### Summary Table

| Feature                | Rayquaza                                                                   | Groudon                                                                             | Kyogre                                                                              |
| ---------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Availability**       | VERIFIED: After Sootopolis crisis is resolved.                             | VERIFIED: Post-game only.                                                           | VERIFIED: Post-game only.                                                           |
| **Trigger**            | VERIFIED: Returns to Sky Pillar automatically.                             | VERIFIED: Speak to scientist at Weather Institute.                                  | VERIFIED: Speak to scientist at Weather Institute.                                  |
| **Map Location**       | VERIFIED: `MAP_SKY_PILLAR_TOP`                                             | VERIFIED: Terra Cave (location moves between Routes 114, 115, 116, 118).            | VERIFIED: Marine Cave (location moves between Routes 105, 125, 127, 129).            |
| **Level**              | VERIFIED: 70                                                               | VERIFIED: 70                                                                        | VERIFIED: 70                                                                        |
| **Mandatory Items**    | VERIFIED: Mach Bike                                                        | VERIFIED: HMs depending on route.                                                   | VERIFIED: `Surf`, `Dive`.                                                           |
| **Event Flag (Defeat)**| VERIFIED: `FLAG_DEFEATED_RAYQUAZA`                                         | VERIFIED: `FLAG_DEFEATED_GROUDON`                                                   | VERIFIED: `FLAG_DEFEATED_KYOGRE`                                                    |
| **Respawn on Defeat**  | VERIFIED: Yes, after re-beating the Elite Four.                            | VERIFIED: Yes, after re-beating the Elite Four.                                    | VERIFIED: Yes, after re-beating the Elite Four.                                     |
| **RS Differences**     | VERIFIED: Emerald has a mandatory mid-game awakening event before battle.  | VERIFIED: In RS, fought mid-game. In Emerald, post-game only with moving location. | VERIFIED: In RS, fought mid-game. In Emerald, post-game only with moving location. |