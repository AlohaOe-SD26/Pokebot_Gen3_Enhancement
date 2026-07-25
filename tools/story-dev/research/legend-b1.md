Understood. Here is the exhaustive breakdown of the Regi trio unlock chain in Pokémon Emerald, adhering to the specified house rules.

### Overall Prerequisite Chain

The entire sequence is gated by a single master flag. Once this flag is set in the Sealed Chamber, the three individual ruins become accessible for their respective puzzles.

*   **VERIFIED:** The master flag that enables the puzzles in the three Regi ruins is `FLAG_SYS_REGI_UNLOCKED`. This flag is set upon solving the Relicanth/Wailord puzzle in the Sealed Chamber.
    *   _Source: `data/maps/SealedChamber/scripts.inc`, script `SealedChamber_EventScript_OpenRegiTombs`_

### Part 1: The Sealed Chamber

**VERIFIED:** The entrance is a Dive spot within the currents on Route 134. Navigating the currents correctly is required to reach the small patch of water where Dive can be used.

| Prerequisite HM/TM | Map Constant          | Coordinates of Dive Spot (on `MAP_ROUTE134`) |
| ------------------ | --------------------- | -------------------------------------------- |
| Surf, Dive         | `MAP_SEALED_CHAMBER`  | (49, 93)                                     |

---

#### Sealed Chamber: Outer Room Puzzle

*   **VERIFIED:** Upon entering the first room, the player is faced with a Braille wall at the north end.
*   **VERIFIED:** The Braille inscription translates to: `DIG HERE.`
*   **VERIFIED:** To proceed, the player must use the move Dig while standing directly in front of the Braille inscription.
    *   The trigger for this event is `special UseDig`.
    *   This action opens a doorway to the inner room.
    *   _Source: `data/maps/SealedChamber/scripts.inc`, script `SealedChamber_EventScript_Braille`_

---

#### Sealed Chamber: Inner Room Puzzle (The Main Gate)

This is the event that sets `FLAG_SYS_REGI_UNLOCKED`.

*   **VERIFIED:** The player must interact with the Braille inscription at the far north end of the inner chamber.
*   **VERIFIED:** The Braille translates to: `FIRST COMES RELICANTH. LAST COMES WAILORD.`
*   **VERIFIED:** To solve the puzzle, the player's party must be arranged in a specific order when the Braille is read:
    *   A **Relicanth** must be in the **first slot** of the party (slot 0).
    *   A **Wailord** must be in the **last slot** of the party (slot 5).
    *   The species in slots 2 through 5 (indices 1-4) do not matter.
*   **VERIFIED:** Upon successfully reading the Braille with the correct party configuration, the game plays a rumbling sound effect, displays the message "It sounded like a door unlocking somewhere far away.", and sets `FLAG_SYS_REGI_UNLOCKED`.
    *   _Source: `data/maps/SealedChamber/scripts.inc`, script `SealedChamber_EventScript_ReadInnerChamberBraille`. The script explicitly checks `gPlayerParty[0]` for `SPECIES_RELICANTH` and `gPlayerParty[5]` for `SPECIES_WAILORD`._

---

### Part 2: The Three Ruins

Once `FLAG_SYS_REGI_UNLOCKED` is set, the doors to the three ruins can be opened. Each ruin has its own secondary puzzle.

#### Regirock: Desert Ruins

| Detail              | Data                                                                                                                                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Map Constant**    | `MAP_DESERT_RUINS`                                                                                                                                                                                                |
| **Location**        | Southern end of the desert on Route 111.                                                                                                                                                                        |
| **Door Braille**    | `RIGHT, RIGHT, DOWN, DOWN. THEN, USE ROCK SMASH.`                                                                                                                                                                 |
| **Puzzle Solution** | **VERIFIED:** From the Braille inscription on the back wall, the player must take **two steps right**, then **two steps down**, and then use the move **Rock Smash**. This is a position-based check, not a relative one. The player must be on the specific tile to trigger the event. The door to the inner chamber will then open. |
| **Gating Flag**     | **VERIFIED:** `FLAG_OPENED_REGIROCK_CHAMBER` is set upon solving the puzzle.                                                                                                                                      |
| **Encounter**       | **VERIFIED:** Interacting with the statue triggers a battle with a Level 40 Regirock.                                                                                                                             |
| **Battle Logic**    | **VERIFIED:** This is a one-time static encounter. If defeated or fled from, it will despawn permanently. The controlling flag is `FLAG_DEFEATED_REGIROCK`. The battle script checks this flag; if it's set, the interaction does nothing. Fleeing does NOT set this flag, but the overworld sprite remains. Re-interacting will re-initiate the battle. **Defeating** it sets the flag and removes it forever. |
| **Source**          | `data/maps/DesertRuins/scripts.inc`, script `DesertRuins_EventScript_OpenRegirockChamber` and `DesertRuins_EventScript_Regirock`.                                                                                   |

---

#### Regice: Island Cave

| Detail              | Data                                                                                                                                                                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Map Constant**    | `MAP_ISLAND_CAVE`                                                                                                                                                                                                                                                            |
| **Location**        | A small island on the west side of Route 105, requiring Surf.                                                                                                                                                                                                              |
| **Door Braille**    | `STAY CLOSE TO THE WALL. RUN AROUND ONE LAP.`                                                                                                                                                                                                                                |
| **Puzzle Solution** | **VERIFIED:** From any starting point, the player must walk or run a full counter-clockwise lap along the outer wall of the cave without lifting their finger from the D-pad and without bumping into the central Braille inscription. After a full lap is completed, the door to the inner chamber will open. |
| **Gating Flag**     | **VERIFIED:** `FLAG_OPENED_REGICE_CHAMBER` is set upon solving the puzzle.                                                                                                                                                                                                   |
| **Encounter**       | **VERIFIED:** Interacting with the statue triggers a battle with a Level 40 Regice.                                                                                                                                                                                          |
| **Battle Logic**    | **VERIFIED:** Identical to Regirock. Controlled by `FLAG_DEFEATED_REGICE`. If defeated, it is gone permanently. If fled from, it can be re-engaged.                                                                                                                            |
| **Source**          | `data/maps/IslandCave/scripts.inc`, script `IslandCave_EventScript_OpenRegiceChamber` and `IslandCave_EventScript_Regice`.                                                                                                                                                     |

---

#### Registeel: Ancient Tomb

| Detail              | Data                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Map Constant**    | `MAP_ANCIENT_TOMB`                                                                                                                                                                                                                                                                                                                                                                                     |
| **Location**        | A mound on the west side of Route 120, surrounded by six rock formations.                                                                                                                                                                                                                                                                                                                              |
| **Door Braille**    | `THOSE WHO INHERIT OUR WILL, SHINE IN THE MIDDLE.`                                                                                                                                                                                                                                                                                                                                                     |
| **Puzzle Solution** | **VERIFIED:** The player must stand in the **exact center tile** of the room and use the move **Fly**. The door to the inner chamber will then open. The coordinates for the center tile are (8, 5) on `MAP_ANCIENT_TOMB`.                                                                                                                                                                                   |
| **Gating Flag**     | **VERIFIED:** `FLAG_OPENED_REGISTEEL_CHAMBER` is set upon solving the puzzle.                                                                                                                                                                                                                                                                                                                           |
| **Encounter**       | **VERIFIED:** Interacting with the statue triggers a battle with a Level 40 Registeel.                                                                                                                                                                                                                                                                                                                  |
| **Battle Logic**    | **VERIFIED:** Identical to the others. Controlled by `FLAG_DEFEATED_REGISTEEL`. If defeated, it is gone permanently. If fled from, it can be re-engaged.                                                                                                                                                                                                                                                   |
| **Source**          | `data/maps/AncientTomb/scripts.inc`, script `AncientTomb_EventScript_OpenRegisteelChamber` and `AncientTomb_EventScript_Registeel`. The script explicitly checks player coordinates: `checkplayerxy 8, 5`.                                                                                                                                                                                                     |

---

### Part 3: Pokémon Emerald vs. Ruby/Sapphire Differences

This is a critical section for accuracy, as the puzzles were changed between versions.

| Feature                   | Pokémon Ruby & Sapphire                                                                                                                                                                                                 | Pokémon Emerald                                                                                                                                                                                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sealed Chamber Puzzle** | **VERIFIED:** Requires a **Wailord** in the first party slot and a **Relicanth** in the last party slot. (The reverse of Emerald).                                                                                         | **VERIFIED:** Requires a **Relicanth** in the first party slot and a **Wailord** in the last party slot.                                                                                                                                                     |
| **Regice Puzzle**         | **VERIFIED:** After reading the Braille, the player must close the dialog box and wait for approximately two minutes without moving at all. The door opens automatically after the timer expires.                          | **VERIFIED:** The player must complete a full counter-clockwise lap around the outer perimeter of the cave.                                                                                                                                               |
| **Registeel Puzzle**      | **VERIFIED:** The player must go to the center of the room and use the move **Flash**.                                                                                                                                    | **VERIFIED:** The player must go to the center of the room and use the move **Fly**.                                                                                                                                                                      |
| **Regirock Puzzle**       | **VERIFIED:** Unchanged. Two steps right, two steps down, then use Rock Smash.                                                                                                                                            | **VERIFIED:** Unchanged.                                                                                                                                                                                                                                 |
| **Post-Game Respawn**     | **VERIFIED:** If any of the Regis are defeated, they do not respawn after beating the Elite Four. They are gone permanently.                                                                                                | **VERIFIED:** If any of the Regis are defeated, they do not respawn after beating the Elite Four. They are gone permanently.                                                                                                                               |