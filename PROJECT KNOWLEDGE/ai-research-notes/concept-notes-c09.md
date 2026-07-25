## A. MECHANICS THE ROM ENFORCES

### Legendary Catch Data & Constraints
In Emerald, Elite Four rematches **do not** respawn defeated legendaries [**VERIFIED**]. If a legendary is KO’d, it is permanently removed from the save file.

| Legendary | Lv | Base Catch Rate | Type | Flee? | Permanent Loss / Flag Set | Re-attempt on Whiteout / Flee? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rayquaza** | 70 | 3 | Static | No | KO (`FLAG_DEFEATED_RAYQUAZA`) | Yes (leave map and return) |
| **Groudon** | 70 | 5 | Static | No | KO (`FLAG_DEFEATED_GROUDON`) | Yes (leave map and return) |
| **Kyogre** | 70 | 5 | Static | No | KO (`FLAG_DEFEATED_KYOGRE`) | Yes (leave map and return) |
| **Regirock** | 40 | 3 | Static | No | KO (`FLAG_DEFEATED_REGIROCK`) | Yes (leave map and return) |
| **Regice** | 40 | 3 | Static | No | KO (`FLAG_DEFEATED_REGICE`) | Yes (leave map and return) |
| **Registeel**| 40 | 3 | Static | No | KO (`FLAG_DEFEATED_REGISTEEL`) | Yes (leave map and return) |
| **Lati@s** (Roamer) | 40 | 3 | Roamer | **Yes** | KO (`FLAG_DEFEATED_LATIAS_OR_LATIOS`) | Yes (remains on map if player whiteout) |
| **Lati@s** (South Isle) | 50 | 3 | Event | No | KO (`FLAG_DEFEATED_LATIAS_OR_LATIOS`) | Yes (interact with orb again) |
| **Mew** | 30 | 45 | Event | No | KO (`FLAG_DEFEATED_MEW`) | Yes (leave map and return) |
| **Deoxys** | 30 | 3 | Event | No | KO (`FLAG_DEFEATED_DEOXYS`) | Yes (leave map and return) |
| **Ho-Oh** | 70 | 3 | Event | No | KO (`FLAG_DEFEATED_HO_OH`) | Yes (leave map and return) |
| **Lugia** | 70 | 3 | Event | No | KO (`FLAG_DEFEATED_LUGIA`) | Yes (leave map and return) |

*Note: Groudon and Kyogre have a Catch Rate of 5 in Gen 3, not 3.* [**VERIFIED** `src/data/pokemon/species_info.h`]

### Roamer Mechanics (`src/roamer.c`)
*   **Activation**: Triggered by TV broadcast at home (`VAR_ROAMER_POKEMON`: 0 = Latias, 1 = Latios). [**VERIFIED**]
*   **Movement**: The roamer changes routes every time the player transitions between maps. It does *not* move on time/steps alone. [**VERIFIED**]
*   **Fleeing**: Hardcoded to attempt flee on Turn 1 before attacking, unless prevented by `ABILITY_SHADOW_TAG` (Wobbuffet) or trapping moves (Mean Look). *Note: `ABILITY_ARENA_TRAP` fails because Lati@s have Levitate.* [**VERIFIED**]
*   **Damage Retention**: Roamer HP and Status effects are saved to `gSaveBlock1Ptr->roamer`. [**VERIFIED**]
*   **Emerald Difference**: The "Roamer IV Glitch" (where IVs other than HP/Atk are forced to 0), present in RS and FRLG, was **fixed** in Emerald. Lati@s will have normally generated IVs. [**VERIFIED**]

### Catch Rate Formula (`src/pokemon.c`)
The game calculates base probability $a = \frac{3 \times HP_{max} - 2 \times HP_{current}}{3 \times HP_{max}} \times \text{CatchRate} \times \text{BallBonus}$.
If $a \ge 255$, the catch skips to success. Otherwise, $b = 1048560 / \sqrt{\sqrt{16711680 / a}}$.
The RNG (`Random()`) is called 4 times. Each must be $< b$ for a successful catch. Status bonuses (Sleep/Freeze = 2, PSN/BRN/PAR = 1.5) are applied to $a$. [**VERIFIED**]

---

## B. WHAT THE BOT CAN OBSERVE

All variables below can be directly read via memory inspection through `libmgba`.

| State / Data | Memory Struct / Location | How the Bot Reads It |
| :--- | :--- | :--- |
| **Enemy HP, Level, Moves** | `gEnemyParty[0]` | Read the `Pokemon` struct. Specifically, `box.hp`, `box.maxHP`, and `box.moves` to detect dangerous recoil moves. |
| **Enemy IVs/Nature** | `gEnemyParty[0]` | Read `box.personality` (Nature) and bitfields for IVs. Allows bot to instantly reset if stats aren't perfect (RNG manipulation). |
| **Roamer Location/State** | `gSaveBlock1Ptr->roamer` | Exposes `roamer.species`, `roamer.level`, `roamer.hp`, `roamer.status`, and `gRoamerLocationMapSectionId`. |
| **RNG State** | `gRngValue`, `gRng2Value` | 32-bit seeds. The bot can read these to know exactly what the outcome of tossing a ball or an attack will be before taking action. |
| **Legendary Dead?** | `gSaveBlock1Ptr->flags` | Bitmask lookup for `FLAG_DEFEATED_*` (e.g., `FLAG_DEFEATED_RAYQUAZA`). |
| **Catch Success** | `gBattleResults` | `gBattleResults.catchAttempts` increments. The bot can also watch the enemy sprite matrix or `gBattleOutcome` switch to `B_OUTCOME_CAUGHT`. |
| **Inventory count** | `gSaveBlock1Ptr->bagPocket_Pokeballs` | Read `ItemSlot` array to confirm quantity of Ultra/Timer/Master balls before engaging. |

---

## C. OPTION SPACE

### Strategy 1: The False Swipe / Spore Loop
The bot sends out an overleveled Smeargle/Parasect/Breloom, uses False Swipe until `hp == 1`, applies Sleep, and throws Ultra Balls.
*   **Mechanical Cost**: Requires building a specific high-level catcher Pokémon.
*   **Failure Mode**: Legendary uses a self-damaging move (Recoil/Confusion) and KOs itself at 1 HP.
*   **Detection**: Bot reads `gEnemyParty[0].hp == 0` and `gBattleOutcome == B_OUTCOME_WON`. Flag `FLAG_DEFEATED_...` goes high.

### Strategy 2: Tank and Timer Ball
The bot uses an extremely tanky Pokémon with high HP/Def (e.g., Blissey/Shuckle) and spams healing items or `Rest` for 30 turns. Turn 31+, it throws Timer Balls (4x catch rate modifier).
*   **Mechanical Cost**: High resource consumption (Potions/Balls). Battles take a long time in real-time execution.
*   **Failure Mode**: Legendary exhausts all PP and uses `Struggle` (recoil).
*   **Detection**: Bot reads `gEnemyParty[0]` move PP fields. If all 4 moves hit 0 PP, Struggle is imminent.

### Strategy 3: RNG Exploitation (The "TAS" Route)
The bot reads `gRngValue` and waits on the overworld until the frame guarantees both perfect IVs/Nature on generation, and then during battle, waits on menus until the frame guarantees a Pokéball will roll 4 successful shakes at full HP.
*   **Mechanical Cost**: Heavy reverse-engineering of the frame advance logic and menu delays.
*   **Failure Mode**: Frame-perfect desync due to NPC movement or VBlank interrupts advancing the RNG unexpectedly.
*   **Detection**: The read `box.personality` of the spawned legendary doesn't match the target, or the ball fails to catch. The bot detects this instantly and initiates a soft-reset (`libmgba` reset).

---

## D. TRAPS (Exhaustive)

These are the automated failure states that will permanently ruin a save file or wedge the bot in an infinite loop.

1.  **Recoil KO Trap (Kyogre)**
    *   **The Trap**: Kyogre (Lv 70) knows **Double-Edge**. [**VERIFIED**]
    *   **The Consequence**: If the bot False Swipes Kyogre to 1 HP, Kyogre will use Double-Edge, KO itself via recoil, and trigger `FLAG_DEFEATED_KYOGRE`.
    *   **Prevention**: Bot must read `gEnemyParty[0].moves`. If Recoil moves exist, skip False Swipe or use a Ghost-type Pokémon to be immune to Double-Edge.

2.  **Confusion KO Trap (Rayquaza)**
    *   **The Trap**: Rayquaza (Lv 70) knows **Outrage**. [**VERIFIED**]
    *   **The Consequence**: After 2-3 turns of Outrage, Rayquaza becomes Confused. Confusion damage is calculated as a 40BP physical typeless attack. At 1 HP (from False Swipe), it will kill itself.
    *   **Prevention**: Never False Swipe Rayquaza. Use Status + full HP balls, or inflict Sleep before it can Outrage.

3.  **PP Exhaustion / Struggle Trap**
    *   **The Trap**: Legendaries only have ~40 total PP across their moves. High catch rates (3) + bad RNG = 40+ turns of throwing balls.
    *   **The Consequence**: The legendary runs out of PP, uses Struggle, takes 1/4 recoil damage, and KOs itself.
    *   **Prevention**: The bot *must* track enemy PP consumption by reading `gEnemyParty[0].pp`. If total PP $\le 1$, the bot must execute a soft-reset or throw a Master Ball immediately.

4.  **The Roamer Autosave Trap**
    *   **The Trap**: The bot encounters Lati@s, it gets KO'd by a critical hit, and the battle ends. The bot's logic defaults to "save the game after a battle."
    *   **The Consequence**: `FLAG_DEFEATED_LATIAS_OR_LATIOS` is baked into the save file. The roamer is gone forever.
    *   **Prevention**: Wrap the save routine in a check: `if (FLAG_DEFEATED_LATIAS_OR_LATIOS) { do_not_save; throw_error; }`.

5.  **Mew's "Hide and Seek" AI Pathing Wedge**
    *   **The Trap**: On Faraway Island, Mew hides in tall grass. The player must chase it. Mew moves in reaction to the player's inputs.
    *   **The Consequence**: A naive pathfinding bot will get stuck in an infinite loop, continuously trailing one tile behind Mew without ever initiating the encounter. [**RECALL**]
    *   **Prevention**: Requires a specialized cornering algorithm for this specific map (`MAP_FARAWAY_ISLAND_INTERIOR`).

### NEVER ATTEMPT UNSUPERVISED:
*   **Rayquaza / Kyogre**: Due to Outrage and Double-Edge respectively. The mechanical risk of a self-KO is virtually guaranteed if a generic Catch-Bot logic (False Swipe + Spore) is applied.
*   **Lati@s (Roamer)**: The logic required to track the roamer via `gRoamerLocationMapSectionId`, manipulate map transitions to force an encounter, and handle the Turn-1 Flee (requires trapping Pokémon like Wobbuffet, which itself has no safe attacking moves) is too complex for a generalized battle state machine. It requires a bespoke subroutine.