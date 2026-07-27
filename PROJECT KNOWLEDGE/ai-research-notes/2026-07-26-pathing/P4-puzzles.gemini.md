To build a bot that successfully navigates Pokémon Emerald, you must clearly separate **organic/randomised travel** from **deterministic puzzle-solving**. If the bot randomises movement in a puzzle area, it will likely softlock, fall through the floor, or trap itself in an infinite loop.

Here is the comprehensive breakdown of movement puzzles in Pokémon Emerald and how your bot should handle them.

---

### 1, 2 & 3: Movement Puzzles, Mechanics, and Punishments
*Note: "Required" means necessary to beat the game. "Optional" means for items/sidequests.*

#### A. The "Punishing" Puzzles (Wrong move = Drop, Reset, or Map Reload)
If the bot makes a wrong move here, it faces a severe penalty. **These strictly require deterministic movement.**

*   **Sootopolis Gym (Required):**
    *   *Mechanic:* Cracking ice tiles. You must step on every single ice tile exactly once to unlock the stairs to the next floor.
    *   *Punishment:* Stepping on a tile twice breaks it. You fall into a basement full of trainers and must fight your way out, then restart the puzzle from scratch.
*   **Sky Pillar (Required) & Mirage Tower (Optional):**
    *   *Mechanic:* Cracked floorboards. You must use the Mach Bike at maximum speed (which requires 3 tiles of momentum to build up) and turn precisely on specific tiles without hitting walls or stopping.
    *   *Punishment:* Falling through the floor to the level below. You must climb back up and try again.
*   **Seafloor Cavern & Victory Road (Required) / Fiery Path (Optional):**
    *   *Mechanic:* Strength Boulder puzzles. Boulders must be pushed into holes or out of the way.
    *   *Punishment:* If the bot pushes a boulder against a wall or into a corner randomly, it becomes permanently stuck. The bot **must leave the room and re-enter** to reset the puzzle.
*   **Route 132, 133, 134 Ocean Currents (Optional - to unlock Regis):**
    *   *Mechanic:* Fast-moving water currents. Entering a specific current tile forces the player along a set path.
    *   *Punishment:* Hitting the wrong current sweeps you to the wrong island or spits you out in Pacifidlog Town. You must use Fly to return to Route 131 and start the entire route over.

#### B. The "Time-Wasting" Puzzles (Wrong move = Wasted time, backtracking)
Randomised movement here won't softlock the room, but the bot might spend hours trapped in a loop.

*   **Mossdeep Gym (Required - *Emerald Specific*):**
    *   *Mechanic:* Coloured spin-tiles and switches. Stepping on a yellow tile spins the player automatically along a path. Switches change the direction the tiles send you.
    *   *Punishment:* Being spun back to the start of the room.
*   **Fortree Gym (Required):**
    *   *Mechanic:* Rotating turnstiles. Pushing them alters the path.
    *   *Punishment:* Getting stuck on the wrong side; the bot will have to walk in circles to reset the turnstile state.
*   **Mauville Gym (Required):**
    *   *Mechanic:* Electric fences toggled by stepping on switch tiles.
    *   *Punishment:* Blocking the path forward.
*   **Lavaridge Gym & Aqua/Magma Hideouts (Required):**
    *   *Mechanic:* Teleporter pads / Geysers. Stepping on one sends you to another room.
    *   *Punishment:* Getting stuck in a loop between two teleporters if movement is randomised immediately upon teleporting.
*   **Shoal Cave Ice Room (Optional):**
    *   *Mechanic:* Frictionless ice. Stepping on it slides the player in one direction until they hit a rock or wall.
    *   *Punishment:* Sliding into a corner and having to slide back.
*   **Trick House (Optional):**
    *   *Mechanic:* A mix of turnstiles, sliding floors, and boulders.
    *   *Punishment:* Highly dependent on the room, mostly time waste.

---

### 4. Overworld Obstacles Requiring Exact Approach
Ordinary routes contain obstacles that require precise tile approaches or specific input states.

*   **Ledges:** Can only be crossed moving Down, Left, or Right (depending on orientation). Randomly pushing against the bottom of a ledge does nothing.
*   **Strength Boulders:** Must be approached facing exactly perpendicular to the direction you want to push.
*   **Mach Bike Mud Slopes (e.g., Route 111 Desert, Granite Cave):** The bot *cannot* just approach the slope. It must have the Mach Bike equipped, be lined up precisely, and have at least **3 tiles of uninterrupted movement** before hitting the slope to build enough momentum to climb it.
*   **Acro Bike White Rails (e.g., Route 119, Safari Zone):** The bot must hold the B-button to hop, and press directional inputs precisely to jump between rails. Random movement will cause the player to fall off.
*   **Acro Bike Stepping Stones:** Requires pressing `B + Direction` simultaneously to jump gaps.

---

### 5. Dual-Purpose Maps (Corridor + Puzzle)
Yes, several maps share IDs or contiguous spaces where ordinary travel suddenly becomes a precise puzzle.

*   **Victory Road:** The primary corridor to the Pokémon League, but it contains choke points filled with Strength puzzles. The bot must switch from organic pathing to deterministic boulder-pushing at specific coordinates.
*   **Route 111 (Desert):** You can walk around organically in the sand, but climbing the Mud Slope or navigating the Mirage Tower requires a sudden switch to deterministic Mach Bike logic.
*   **Route 119:** The main path is a long, organic travel corridor (tall grass, trainers), but branching paths require Acro Bike rail hopping to get items.
*   **Safari Zone:** Normal grass movement is mixed directly with Acro and Mach bike puzzle tracks in the same map space.

---

### 6. The Cleanest Rule for Bot Decision-Making
Do not try to make the bot visually "recognise" puzzles. The cleanest, most fail-proof rule relies on **RAM reading: Map ID + Bounding Boxes (Coordinate Zones).**

**The Rule Engine:**
1.  Read current `Map_ID` (e.g., Sootopolis Gym is Map ID `X`).
2.  Read current `Player_X` and `Player_Y`.
3.  Maintain a JSON/Config file of "Deterministic Zones" defined by `[Map_ID, X1, Y1, X2, Y2]`.

**The Logic Loop:**
```text
IF (Current_Map_ID is in Deterministic_Config) AND (Player_X, Player_Y is inside defined bounding box):
    Execute Deterministic_Macro(Macro_ID) // e.g., Execute perfectly timed Mach Bike turns
ELSE:
    Execute Organic_Randomised_Movement()
```

**Why this is the best method:**
*   **Handles Dual-Purpose Maps:** By defining a bounding box (e.g., `X: 10-15, Y: 20-25` inside Victory Road), the bot will travel organically until it steps into the bounding box of a Strength puzzle. It will then switch to deterministic mode, solve the puzzle, step out of the box, and resume organic travel.
*   **Handles Resets Gracefully:** If the bot falls through the floor in Sky Pillar, its coordinates instantly change to the floor below (outside the puzzle bounding box). It will organically find the stairs, walk back up, re-enter the bounding box, and the deterministic macro will trigger from step 1 again.

**Flagging UNCERTAINTIES for your bot development:**
*   *NPC Interference:* In places like Victory Road or Gyms, are there wandering NPCs (trainers you haven't fought) inside your bounding boxes? If an NPC steps in the way of a deterministic Boulder push, your bot's macro will desync. You must ensure deterministic macros include logic to either battle the trainer first or wait for the NPC to move.
*   *Frame Delays on Ice/Spin Tiles:* Mossdeep spin tiles and Sootopolis ice tiles lock player input for specific amounts of frames. Your deterministic macro must wait for the exact memory flag that says "Player regains control" before executing the next directional input, rather than just waiting a set amount of time.