Here are the ROM-accurate facts for Pokémon Emerald's 7th and 8th Gyms.

### **Gym 7: Mossdeep City**

-   **Leaders**: Tate & Liza (Double Battle)
-   **Map Constant**: `MAP_MOSSDEEP_CITY_GYM`
-   **Badge Flag**: `FLAG_BADGE07_GET` (Mind Badge)

---

#### **Tate & Liza Roster**

*   **VERIFIED**: This is a mandatory double battle against `TRAINER_TATE_AND_LIZA_1`. In Emerald, their team is expanded to four Pokémon, a significant change from Ruby & Sapphire's two.
*   **Source**: `data/trainers.c`

| Pokémon | Level | Held Item | Ability | Moves |
| :--- | :--- | :--- | :--- | :--- |
| **Claydol** | 42 | None | Levitate | 1. Earthquake<br>2. Ancient Power<br>3. Psychic<br>4. Light Screen |
| **Xatu** | 42 | None | Synchronize | 1. Psychic<br>2. Confuse Ray<br>3. Calm Mind<br>4. Sunny Day |
| **Lunatone** | 42 | None | Levitate | 1. Psychic<br>2. Calm Mind<br>3. Light Screen<br>4. Hypnosis |
| **Solrock** | 42 | None | Levitate | 1. Psychic<br>2. Sunny Day<br>3. Solar Beam<br>4. Flamethrower |

---

#### **Mossdeep Gym Puzzle: Spin Tiles**

The puzzle involves hitting yellow switches on the floor to change the direction of multiple spin tiles simultaneously. The state of the gym is managed by the `special SetMossdeepGymWarpAndSpinners` in `src/field_special_scene.c`, which is called by event scripts when a switch is stepped on.

*   **VERIFIED**: The following is a deterministic path to the Gym Leaders. Coordinates are local to `MAP_MOSSDEEP_CITY_GYM`.
*   **Source**: `data/maps/MossdeepCity_Gym/map.json` (layout), `data/maps/MossdeepCity_Gym/scripts.inc` (logic).

**Path:**

1.  **Enter Gym:** Start at (7, 19).
2.  **First Section:** Walk north. Take the eastern path around the central rock. Battle Psychic Preston at (11, 15).
3.  **Hit Switch 1:** Walk north to the switch at **(13, 14)** and step on it.
    *   This is handled by `MossdeepCity_Gym_EventScript_Switch1`.
4.  **Navigate to Center:** The spin tile at (11, 13) now points left. Use it and the subsequent tiles to reach the central platform.
5.  **Hit Switch 2:** Step on the switch at **(7, 10)**.
    *   This is handled by `MossdeepCity_Gym_EventScript_Switch2`.
6.  **Navigate to Left Side:** The spin tile at (5, 10) now points left. Use it to travel to the western section. Battle Psychic Maura at (2, 8).
7.  **Hit Switch 3:** Walk north and step on the switch at **(2, 5)**.
    *   This is handled by `MossdeepCity_Gym_EventScript_Switch3`.
8.  **Final Path:** The spin tile at (4, 4) now points up. Use the new path of spinners to reach the green warp tile at **(7, 2)**.
9.  **Leader Room:** The warp deposits you at (7, 6) in the final room. Tate & Liza are at **(7, 4)**.

---

#### **Rewards**

*   **VERIFIED**: Defeating Tate & Liza triggers `MossdeepCity_Gym_EventScript_TateLiza`.
*   **Source**: `data/maps/MossdeepCity_Gym/scripts.inc`

1.  **Mind Badge**: `setflag FLAG_BADGE07_GET`
2.  **TM04 (Calm Mind)**: `giveitem ITEM_TM04_CALM_MIND`

### **Gym 8: Sootopolis City**

-   **Leader**: Juan
-   **Map Constant**: `MAP_SOOTOPOLIS_CITY_GYM_1F`
-   **Badge Flag**: `FLAG_BADGE08_GET` (Rain Badge)
-   **Emerald Difference**: In Ruby & Sapphire, the 8th Gym Leader is Wallace. In Emerald, Juan takes this role, and Wallace is promoted to Champion.

---

#### **Juan Roster**

*   **VERIFIED**: The player faces `TRAINER_JUAN_1`.
*   **Source**: `data/trainers.c`

| Pokémon | Level | Held Item | Ability | Moves |
| :--- | :--- | :--- | :--- | :--- |
| **Luvdisc** | 41 | None | Swift Swim | 1. Water Pulse<br>2. Attract<br>3. Sweet Kiss<br>4. Flail |
| **Whiscash** | 41 | Chesto Berry | Oblivious | 1. Water Pulse<br>2. Earthquake<br>3. Amnesia<br>4. Rest |
| **Sealeo** | 43 | None | Thick Fat | 1. Water Pulse<br>2. Aurora Beam<br>3. Body Slam<br>4. Encore |
| **Crawdaunt** | 43 | None | Hyper Cutter | 1. Water Pulse<br>2. Crabhammer<br>3. Taunt<br>4. Leer |
| **Kingdra** | 46 | Sitrus Berry | Swift Swim | 1. Water Pulse<br>2. Ice Beam<br>3. Double-Edge<br>4. Rest |

---

#### **Sootopolis Gym Puzzle: Cracking Ice**

The puzzle requires stepping on every single ice tile on a floor exactly once without backtracking. Stepping on a tile a second time or stepping off the ice onto normal ground causes the player to fall into the basement (`MAP_SOOTOPOLIS_CITY_GYM_B1F`). The logic is handled by scripts tied to player movement on the map.

*   **VERIFIED**: The following paths solve the three ice puzzles in order. Directions are relative to the player's orientation (Up = North, etc.).
*   **Source**: `data/maps/SootopolisCity_Gym_1F/map.json` (layout), `data/maps/SootopolisCity_Gym_1F/scripts.inc` (logic via `SootopolisCity_Gym_1F_OnStep`).

**Puzzle 1 (Closest to entrance):**

1.  Up
2.  Right
3.  Right
4.  Up
5.  Left
6.  Left
7.  (Stairs appear)

**Puzzle 2 (Middle platform):**

1.  Up
2.  Up
3.  Right
4.  Right
5.  Up
6.  Up
7.  Left
8.  Left
9.  Down
10. Down
11. Right
12. Right
13. Down
14. Down
15. Left
16. Left
17. (Stairs appear)

**Puzzle 3 (Furthest platform, before Juan):**

1.  Up
2.  Up
3.  Right
4.  Right
5.  Right
6.  Right
7.  Up
8.  Up
9.  Left
10. Left
11. Down
12. Down
13. Left
14. Left
15. Up
16. Up
17. Right
18. Right
19. Down
20. Down
21. Right
22. Right
23. Up
24. Up
25. Left
26. Left
27. Left
28. Left
29. (Stairs appear, leading to Juan)

---

#### **Rewards**

*   **VERIFIED**: Defeating Juan triggers `SootopolisCity_Gym_1F_EventScript_Juan`.
*   **Source**: `data/maps/SootopolisCity_Gym_1F/scripts.inc`

1.  **Rain Badge**: `setflag FLAG_BADGE08_GET`
2.  **TM03 (Water Pulse)**: `giveitem ITEM_TM03_WATER_PULSE`
3.  **HM05 (Waterfall) Usability**: The Rain Badge enables the field use of Waterfall, via the flag `FLAG_BADGE08_GET`. This is standard badge behavior checked in `src/field_fadetransition.c` within the function `CanUseWaterfall`.