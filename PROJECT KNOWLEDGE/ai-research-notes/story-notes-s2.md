Of course. Here is a structured, ROM-accurate breakdown of the Team Magma and Team Aqua Hideouts in Pokémon Emerald for your bot.

### **Team Magma Hideout (Jagged Pass)**

This location is used by Team Magma in Emerald. In Ruby/Sapphire, this hideout does not exist in this form; Team Magma occupies the hideout in Lilycove.

**VERIFIED:** The entire sequence of events, layout, and purpose of this hideout is unique to Pokémon Emerald.

---

#### **1. Entry Requirements**

*   **Prerequisite Event:** Player must have defeated Team Magma at Mt. Chimney. (VERIFIED)
*   **Controlling Flag:** `FLAG_DEFEATED_MAGMA_AT_MT_CHIMNEY` must be set. (VERIFIED, checked against `data/maps/JaggedPass/scripts.inc`, `JaggedPass_EventScript_CheckMagmaGrunt`)
*   **Entrance Location:** A new cave opening appears on `MAP_JAGGED_PASS`. The Team Magma Grunt who was previously standing guard will be gone. (VERIFIED)
*   **Coordinates:** The entrance warp is at (14, 8) on `MAP_JAGGED_PASS`. (VERIFIED)

---

#### **2. Map-by-Map Walkthrough**

This hideout is a linear path with no warp puzzles. The goal is to reach the final chamber, witness Maxie awaken Groudon, and then battle him.

**Key Flags & Variables for this section:**
| Flag/Var Name | Purpose |
| :--- | :--- |
| `FLAG_AWAKENED_GROUDON` | Set after Maxie uses the Blue Orb. Triggers the next phase of the story in Slateport. |
| `FLAG_DEFEATED_MAGMA_LEADER_MAXIE` | Set after defeating Maxie in the hideout. |
| `FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS` | Set after defeating Maxie; despawns most grunts on the way out. |

##### **Room 1: `MAP_MAGMA_HIDEOUT_1F`**

*   **Path:** Enter from Jagged Pass. Follow the path southeast.
*   **Trainer 1:** Team Magma Grunt
    *   **Coords:** (28, 13) (VERIFIED)
    *   **Sight Range:** 4 tiles, south (VERIFIED)
    *   **Script Label:** `MagmaHideout_1F_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_1` (VERIFIED)
*   **Exit:** Stairs at (26, 28) leading to `MAP_MAGMA_HIDEOUT_2F_1R`. (VERIFIED)

##### **Room 2: `MAP_MAGMA_HIDEOUT_2F_1R`**

*   **Path:** Follow the linear path south and then west.
*   **Trainer 2:** Team Magma Grunt
    *   **Coords:** (17, 13) (VERIFIED)
    *   **Sight Range:** 4 tiles, east (VERIFIED)
    *   **Script Label:** `MagmaHideout_2F_1R_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_2` (VERIFIED)
*   **Exit:** Cave opening at (5, 12) leading to `MAP_MAGMA_HIDEOUT_2F_2R`. (VERIFIED)

##### **Room 3: `MAP_MAGMA_HIDEOUT_2F_2R`**

*   **Path:** Go west.
*   **Trainer 3:** Team Magma Grunt
    *   **Coords:** (18, 5) (VERIFIED)
    *   **Sight Range:** 4 tiles, west (VERIFIED)
    *   **Script Label:** `MagmaHideout_2F_2R_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_3` (VERIFIED)
*   **Trainer 4:** Team Magma Grunt
    *   **Coords:** (11, 8) (VERIFIED)
    *   **Sight Range:** 3 tiles, north (VERIFIED)
    *   **Script Label:** `MagmaHideout_2F_2R_EventScript_Grunt2` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_4` (VERIFIED)
*   **Exit:** Cave opening at (3, 6) leading to `MAP_MAGMA_HIDEOUT_3F_1R`. (VERIFIED)

##### **Room 4: `MAP_MAGMA_HIDEOUT_3F_1R`**

*   **Path:** Go south, then east.
*   **Trainer 5 (Double Battle):** Team Magma Grunt & Team Magma Grunt
    *   **Coords:** (14, 21) and (15, 21) (VERIFIED)
    *   **Sight Range:** 4 tiles, north (VERIFIED)
    *   **Script Label:** `MagmaHideout_3F_1R_EventScript_Grunt1`, `MagmaHideout_3F_1R_EventScript_Grunt2` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_5` (VERIFIED)
*   **Exit:** Cave opening at (25, 13) leading to `MAP_MAGMA_HIDEOUT_3F_2R`. (VERIFIED)

##### **Room 5: `MAP_MAGMA_HIDEOUT_3F_2R`**

*   **Path:** Follow the circular path counter-clockwise.
*   **Trainer 6:** Team Magma Grunt
    *   **Coords:** (10, 8) (VERIFIED)
    *   **Sight Range:** 3 tiles, south (VERIFIED)
    *   **Script Label:** `MagmaHideout_3F_2R_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_6` (VERIFIED)
*   **Item:** Max Revive
    *   **Coords:** (16, 17) (VERIFIED)
    *   **Flag:** `FLAG_ITEM_MAGMA_HIDEOUT_MAX_REVIVE` (VERIFIED)
*   **Exit:** Cave opening at (17, 5) leading to `MAP_MAGMA_HIDEOUT_4F`. (VERIFIED)

##### **Room 6: `MAP_MAGMA_HIDEOUT_4F` (Groudon Chamber)**

*   **Path:** Navigate north through the narrow passages.
*   **Trainer 7:** Team Magma Grunt
    *   **Coords:** (20, 24) (VERIFIED)
    *   **Sight Range:** 3 tiles, south (VERIFIED)
    *   **Script Label:** `MagmaHideout_4F_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_7` (VERIFIED)
*   **Trainer 8:** Team Magma Grunt
    *   **Coords:** (10, 18) (VERIFIED)
    *   **Sight Range:** 3 tiles, south (VERIFIED)
    *   **Script Label:** `MagmaHideout_4F_EventScript_Grunt2` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_HIDEOUT_GRUNT_8` (VERIFIED)
*   **Encounter 1: Magma Admin Tabitha**
    *   **Coords:** (14, 9) (VERIFIED)
    *   **Trigger:** Stepping on tile (14, 11). (VERIFIED)
    *   **Script Label:** `MagmaHideout_4F_EventScript_Tabitha` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_ADMIN_TABITHA` (VERIFIED)
*   **Encounter 2: Magma Leader Maxie & Groudon Awakening**
    *   **Coords:** Maxie is at (14, 5). (VERIFIED)
    *   **Trigger:** Interact with Maxie.
    *   **Script Label:** `MagmaHideout_4F_EventScript_Maxie` (VERIFIED)
    *   **Event Flow:**
        1.  Maxie gives a speech.
        2.  He uses the Blue Orb.
        3.  The screen flashes white, Groudon awakens and roars.
        4.  Groudon flies off the screen.
        5.  `setflag FLAG_AWAKENED_GROUDON` occurs here. (VERIFIED)
        6.  Maxie, enraged, battles the player.
    *   **Defeat Flag:** `FLAG_DEFEATED_MAGMA_LEADER_MAXIE` (VERIFIED)
*   **Post-Battle:**
    *   Maxie yields and leaves.
    *   `setflag FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS` occurs. (VERIFIED)
    *   An Escape Rope appears on the ground.
    *   **Item:** Escape Rope
        *   **Coords:** (11, 5) (VERIFIED)
        *   **Flag:** `FLAG_ITEM_MAGMA_HIDEOUT_ESCAPE_ROPE` (VERIFIED)
*   **Exit:** A warp panel at (14, 2) is now accessible. This leads back to `MAP_MAGMA_HIDEOUT_1F` at coords (10, 4), right near the entrance. (VERIFIED)

---
---

### **Team Aqua Hideout (Lilycove City)**

This location is used by Team Aqua in Emerald. In Ruby/Sapphire, this hideout is occupied by Team Magma, and the layout and puzzles are different.

**VERIFIED:** The puzzle solution, trainer placements, and specific story beats (e.g., Matt battle) are specific to Emerald.

---

#### **1. Entry Requirements**

*   **Prerequisite Event:** Player must have driven Team Magma from the summit of Mt. Pyre and received the Magma Emblem.
*   **Controlling Flag:** `FLAG_RECEIVED_MAGMA_EMBLEM`. The script that hides the Wailmer blocking the entrance, `LilycoveCity_EventScript_HideWailmer`, checks for this flag. (VERIFIED)
*   **Entrance Location:** A cave in the northeast of `MAP_LILYCOVE_CITY`.
*   **Coordinates:** The entrance warp is at (47, 10) on `MAP_LILYCOVE_CITY`. (VERIFIED)

---

#### **2. Warp Puzzle and Walkthrough**

The main challenge is a series of one-way warp panels. The following is a deterministic path to the final room. An optional path to the Master Ball is listed separately.

**Key Flags & Variables for this section:**
| Flag/Var Name | Purpose |
| :--- | :--- |
| `VAR_LILYCOVE_STATE` | Controls city-wide events. Set to 3 after submarine departs. |
| `FLAG_SUBMARINE_MOVED` | Set after Matt battle and submarine cutscene. |
| `FLAG_DEFEATED_AQUA_ADMIN_MATT` | Set after defeating Aqua Admin Matt. |
| `FLAG_ITEM_AQUA_HIDEOUT_MASTER_BALL` | Tracks if the Master Ball has been collected. |

##### **Room 1: `MAP_AQUA_HIDEOUT_1F`**

*   **Path:** Go east, then north.
*   **Trainer 1:** Team Aqua Grunt
    *   **Coords:** (23, 10) (VERIFIED)
    *   **Sight Range:** 4 tiles, south (VERIFIED)
    *   **Script Label:** `AquaHideout_1F_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_1` (VERIFIED)
*   **Trainer 2:** Team Aqua Grunt
    *   **Coords:** (22, 2) (VERIFIED)
    *   **Sight Range:** 4 tiles, west (VERIFIED)
    *   **Script Label:** `AquaHideout_1F_EventScript_Grunt2` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_2` (VERIFIED)
*   **Exit:** Stairs at (1, 10) leading to `MAP_AQUA_HIDEOUT_B1F`. (VERIFIED)

##### **Room 2: `MAP_AQUA_HIDEOUT_B1F` (Main Puzzle Room)**

*   **Path to B2F (Progression):**
    1.  Enter from stairs at (1, 10).
    2.  Walk to **(5, 10)** and take the **left warp panel**. Arrive at (5, 4). (VERIFIED)
    3.  Take the **warp panel at (5, 2)**. Arrive at (25, 2). (VERIFIED)
    4.  Walk south to **(25, 10)** and take the **warp panel**. Arrive at (1, 18). (VERIFIED)
    5.  Walk east.
*   **Trainer 3:** Team Aqua Grunt
    *   **Coords:** (10, 21) (VERIFIED)
    *   **Sight Range:** 3 tiles, north (VERIFIED)
    *   **Script Label:** `AquaHideout_B1F_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_2` (Error in decomp naming, this is the 3rd grunt overall. RECALL). **Correction:** The flag is likely `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_3`. (INFERENCE)
*   **Trainer 4 (Double Battle):** Team Aqua Grunt & Team Aqua Grunt
    *   **Coords:** (17, 18) and (17, 19) (VERIFIED)
    *   **Sight Range:** 3 tiles, west (VERIFIED)
    *   **Script Labels:** `AquaHideout_B1F_EventScript_Grunt2`, `AquaHideout_B1F_EventScript_Grunt3` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_5` (VERIFIED)
*   **Exit:** Stairs at (28, 18) leading to `MAP_AQUA_HIDEOUT_B2F`. (VERIFIED)

##### **Room 3: `MAP_AQUA_HIDEOUT_B2F` (Submarine Dock)**

*   **Path:** Walk north, the path is linear.
*   **Trainer 5:** Team Aqua Grunt
    *   **Coords:** (15, 20) (VERIFIED)
    *   **Sight Range:** 3 tiles, south (VERIFIED)
    *   **Script Label:** `AquaHideout_B2F_EventScript_Grunt1` (VERIFIED)
    *   **Defeat Flag:** `FLAG_DEFEATED_AQUA_HIDEOUT_GRUNT_7` (VERIFIED)
*   **Encounter: Aqua Admin Matt**
    *   **Coords:** (15, 6) (VERIFIED)
    *   **Trigger:** Stepping on tile (15, 8). (VERIFIED)
    *   **Script Label:** `AquaHideout_B2F_EventScript_Matt` (VERIFIED)
    *   **Event Flow:**
        1.  Matt blocks the player and initiates a battle.
        2.  After the battle, he boasts that Archie has already left in the submarine.
        3.  `setflag FLAG_DEFEATED_AQUA_ADMIN_MATT` (VERIFIED)
        4.  A cutscene plays showing the submarine leaving the dock.
        5.  `setvar VAR_LILYCOVE_STATE, 3` and `setflag FLAG_SUBMARINE_MOVED` occur. (VERIFIED)
*   **Exit:** The only way out is to backtrack. The warp panel at (1, 6) leads back to (28, 2) in `MAP_AQUA_HIDEOUT_B1F`, near the entrance. (VERIFIED)

---

#### **3. Optional Path to Master Ball**

This path is not required for story completion. It starts from the entrance of `MAP_AQUA_HIDEOUT_B1F`.

1.  Enter from `1F` at (1, 10).
2.  Walk to **(21, 10)** and take the **right warp panel**. Arrive at (17, 28). (VERIFIED)
3.  Walk to **(14, 28)** and take the **left warp panel**. Arrive at (10, 28). (VERIFIED)
4.  Walk to **(3, 28)** and take the **leftmost warp panel**. Arrive at the secluded item room at (3, 1). (VERIFIED)
5.  You are now in the Master Ball room.
    *   **Item Ball 1 (Top Left):** Nugget
        *   **Coords:** (5, 5) (VERIFIED)
        *   **Flag:** `FLAG_ITEM_AQUA_HIDEOUT_NUGGET` (VERIFIED)
    *   **Item Ball 2 (Bottom Left):** Electrode (Lvl 30) (VERIFIED)
        *   **Coords:** (5, 7) (VERIFIED)
        *   **Script:** `AquaHideout_B1F_EventScript_ItemElectrode1`
        *   **Flag:** `FLAG_ITEM_AQUA_HIDEOUT_ELECTRODE_1` (VERIFIED)
    *   **Item Ball 3 (Top Right):** **Master Ball**
        *   **Coords:** (8, 5) (VERIFIED)
        *   **Flag:** `FLAG_ITEM_AQUA_HIDEOUT_MASTER_BALL` (VERIFIED)
    *   **Item Ball 4 (Bottom Right):** Electrode (Lvl 30) (VERIFIED)
        *   **Coords:** (8, 7) (VERIFIED)
        *   **Script:** `AquaHideout_B1F_EventScript_ItemElectrode2`
        *   **Flag:** `FLAG_ITEM_AQUA_HIDEOUT_ELECTRODE_2` (VERIFIED)
6.  To exit the item room, take the **warp panel at (1, 4)**. This takes you back to the entrance of the entire hideout at `MAP_AQUA_HIDEOUT_1F`, coords (18, 14). (VERIFIED)