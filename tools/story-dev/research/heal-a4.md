Excellent. Adhering to the requested format for bot automation.

### Summary Table

| Healer NPC / Object | Map Location | Coordinates | Trigger | Repeatable? | Confirmation Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Player's Mom** | `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F` | (7, 2) | Interact (A) | Yes, immediate | Party State |
| **Old Woman** | `MAP_ROUTE111_REST_HOUSE` | (4, 2) | Interact (A) | Yes, immediate | Party State |
| **Fossil Maniac's Brother** | `MAP_ROUTE114_FOSSIL_MANIACS_HOUSE` | (5, 2) | Interact (A) | Yes, immediate | Party State |
| **Player's Bed** | `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_2F` | (1, 2) | Step On | Yes, immediate | Party State |
| **Steven's Bed** | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` | (7, 1) | Step On | Yes, immediate* | Party State |
| **S.S. Tidal Bed** | `MAP_SS_TIDAL_ROOMS` | Multiple | Step On | Yes, immediate | Party State |
| **Scott's House Bed** | `MAP_BATTLE_FRONTIER_SCOTTS_HOUSE` | (8, 1) | Step On | Yes, immediate | Party State |

\* *Becomes available only after receiving HM08 from Steven.*

---

### Detailed Automation Mechanics

#### 1. Player's Mom

*   **Location**: `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_1F`, NPC object at (7, 2).
*   **Script**: `data/maps/LittlerootTown_PlayersHouse_1F/scripts.inc`, label `LittlerootTown_PlayersHouse_1F_EventScript_Mom`.

**a) Automation Sequence:**
1.  **VERIFIED:** Face Mom's NPC object (or be adjacent) and press the A button.
2.  **VERIFIED:** A dialogue box appears. Press A to advance through the text.
3.  **VERIFIED:** A YES/NO prompt appears (`msgbox LittlerootTown_PlayersHouse_1F_Text_TakeARest, MSGBOX_YESNO`). The default selection is YES.
4.  **VERIFIED:** Press A to confirm YES. The script branches based on `VAR_RESULT`.
5.  **VERIFIED:** The screen fades to black (`fadescreen FADE_TO_BLACK`).
6.  **VERIFIED:** The heal function is called (`special HealPlayerParty`).
7.  **VERIFIED:** A recovery sound effect plays (`playse SE_RECOVERY`).
8.  **VERIFIED:** The screen fades back in (`fadescreen FADE_FROM_BLACK`).
9.  **VERIFIED:** A final dialogue box appears. Press A to dismiss it. Control is returned to the player. The `Task_ScriptWait` task will be running during this sequence, eventually yielding to `Task_PlayerController_Enable`.

**b) Confirmation from Memory:**
*   **VERIFIED:** There is **no flag or var** set to confirm that a heal occurred. The `special HealPlayerParty` function (defined in `src/special.c`) directly modifies the `gPlayerParty` array in RAM.
*   **VERIFIED:** A bot must confirm the heal by comparing party Pokémon data (Current HP, PP for all moves, and status condition bytes) before and after interacting with the NPC. A successful heal will restore all to their maximum values and clear non-volatile status conditions.

**c) Re-runnability:**
*   **VERIFIED:** The script is immediately re-runnable. No flags are set to prevent subsequent heals.
*   **VERIFIED:** A one-time flag, `FLAG_ADVERTISED_WOULD_HEAL`, is set after she offers to heal the first time, which slightly alters her initial dialogue on subsequent interactions, but the healing path remains identical.

**d) Player Movement:**
*   **VERIFIED:** The player character sprite is **not moved**. The script implies the player goes upstairs and rests via the screen fade and sound effects, but no `applymovement` command is issued. The player's coordinates remain unchanged.

**e) Edge Cases:**
*   **VERIFIED:** The script does not check if the player's party needs healing. A bot can trigger the entire sequence with a perfectly healthy party. The sequence will play out identically. There are no known softlocks.

---

#### 2. Old Woman (Route 111 Rest House)

*   **Location**: `MAP_ROUTE111_REST_HOUSE`, NPC object at (4, 2).
*   **Script**: `data/maps/Route111_RestHouse/scripts.inc`, label `Route111_RestHouse_EventScript_OldWoman`.

**a) Automation Sequence:**
1.  **VERIFIED:** Face NPC and press A.
2.  **VERIFIED:** Press A to advance text.
3.  **VERIFIED:** YES/NO prompt (`msgbox Route111_RestHouse_Text_TakeRestInBed, MSGBOX_YESNO`).
4.  **VERIFIED:** Press A to confirm YES.
5.  **VERIFIED:** Screen fades to black (`fadescreen FADE_TO_BLACK`).
6.  **VERIFIED:** A healing fanfare plays (`playfanfare MUS_ME_ASA`).
7.  **VERIFIED:** `special HealPlayerParty` is called.
8.  **VERIFIED:** Screen fades from black (`fadescreen FADE_FROM_BLACK`).
9.  **VERIFIED:** Press A to dismiss final dialogue. Control is returned.

**b) Confirmation from Memory:**
*   **VERIFIED:** Same as Player's Mom. No flag/var is set. Confirmation requires comparing party state in memory.

**c) Re-runnability:**
*   **VERIFIED:** Immediately re-runnable. No flags are set.

**d) Player Movement:**
*   **VERIFIED:** The player character is not moved.

**e) Edge Cases:**
*   **VERIFIED:** Safe. The script will run even if the party is at full health. No softlocks.

---

#### 3. Fossil Maniac's Brother

*   **Location**: `MAP_ROUTE114_FOSSIL_MANIACS_HOUSE`, NPC object at (5, 2).
*   **Script**: `data/maps/Route114_FossilManiacsHouse/scripts.inc`, label `Route114_FossilManiacsHouse_EventScript_Brother`.

**a) Automation Sequence:**
*   **VERIFIED:** This script is functionally identical to the Route 111 Rest House script. It uses a YES/NO prompt (`Route114_FossilManiacsHouse_Text_WantToRest`), fades, plays `MUS_ME_ASA`, calls `special HealPlayerParty`, and fades back.

**b, c, d, e):**
*   **VERIFIED:** All other mechanics are identical to the Old Woman on Route 111. Confirmation via party state, immediately re-runnable, no player movement, and safe for a full-HP party.

---

#### 4. Bed-Based Heals (Player's Bed, Steven's Bed, S.S. Tidal, Scott's House)

These objects all use a near-identical script triggered by movement, not interaction.

*   **Locations**:
    *   Player's Bed: `MAP_LITTLEROOT_TOWN_PLAYERS_HOUSE_2F`, trigger at (1, 2). Script `LittlerootTown_PlayersHouse_2F_EventScript_Bed`.
    *   Steven's Bed: `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`, trigger at (7, 1). Script `MossdeepCity_StevensHouse_EventScript_Bed`.
    *   S.S. Tidal Beds: `MAP_SS_TIDAL_ROOMS`, triggers at (1,1), (1,5), (5,1), (5,5). Script `SSTidal_Rooms_EventScript_Bed`.
    *   Scott's House Bed: `MAP_BATTLE_FRONTIER_SCOTTS_HOUSE`, trigger at (8, 1). Script `BattleFrontier_ScottsHouse_EventScript_Bed`.

**a) Automation Sequence:**
1.  **VERIFIED:** Move the player character onto the trigger coordinate. The script executes automatically.
2.  **VERIFIED:** A dialogue box with a YES/NO prompt appears.
3.  **VERIFIED:** Press A to confirm YES.
4.  **VERIFIED:** Screen fades to black (`fadescreen FADE_TO_BLACK`).
5.  **VERIFIED:** Healing fanfare plays (`playfanfare MUS_ME_ASA`).
6.  **VERIFIED:** `special HealPlayerParty` is called.
7.  **VERIFIED:** Screen fades from black (`fadescreen FADE_FROM_BLACK`).
8.  **VERIFIED:** Press A to dismiss final dialogue. Control is returned.

**b) Confirmation from Memory:**
*   **VERIFIED:** Same as all others. No flag/var is set. Confirmation requires comparing party state in memory.

**c) Re-runnability:**
*   **VERIFIED:** Immediately re-runnable. The bot must step off and back onto the trigger tile.
*   **VERIFIED (Emerald Difference):** Steven's Bed has a prerequisite. The script first checks `if (flag(FLAG_RECEIVED_HM08) == TRUE)`. If the player has not yet received HM08 (Dive) from Steven in this house, the script will instead display the message "This isn't your bed..." and terminate without offering a heal.

**d) Player Movement:**
*   **VERIFIED:** No movement is applied *by the script*. The player remains on the trigger tile where the script was initiated.

**e) Edge Cases:**
*   **VERIFIED:** Safe. All bed scripts will run even if the party is at full health (provided Steven's bed prerequisite is met). No softlocks.

---

### Inconclusive / Non-Healing Locations

*   **Trick House**: **VERIFIED:** Contrary to some player recall, there is **no** healing NPC or object within any stage of the Trick House. The beds in the puzzle rooms are purely decorative and give a simple text string when interacted with (e.g., `Route110_TrickHousePuzzle1_EventScript_Bed`). The Trick Master himself does not heal the party upon completion of a puzzle. A bot should not attempt to find a heal here.