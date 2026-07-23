# Gemini 3.1 Pro consult — Ch12 (Lavaridge → Norman → Surf) deep-map research, 2026-07-23

> LEADS. Verified parts folded into 12-STORYMODE-DESIGN §Ch12; see the ✓/⚠ tags there.

Here is the precise sequence, routing, and flag/variable logic required for your Emerald bot to navigate from Lavaridge Town to Petalburg City, clear the Gym, defeat Norman, and obtain HM03 Surf. 

### 1. GO-GOGGLES (Map: `MAP_LAVARIDGE_TOWN`)
*   **Who/Where:** The Rival (May/Brendan), waiting just outside the Lavaridge Gym warp. 
*   **Trigger:** A step trigger (`coord_event`) located directly outside the Gym entrance. Once the bot beats Flannery and steps outside, the Rival automatically approaches.
*   **Script:** `LavaridgeTown_EventScript_May` or `LavaridgeTown_EventScript_Brendan` (depending on player gender). It sets `FLAG_RECEIVED_GO_GOGGLES`.
*   **Are they required?** **NO.** The Go-Goggles are *only* required to enter the Route 111 Desert (for the Mirage Tower / Fossils), which is entirely optional for story progression. The bot can skip the desert completely. The woman giving an item in Lavaridge is the Wynaut Egg lady, and Cozmo's wife in Fallarbor gives TM27 Return. 

### 2. OVERLAND ROUTE: Lavaridge → Petalburg (No Fly/Surf)
The fastest, faithful overland route leverages the Rusturf Tunnel, which your bot can fully traverse since it has the Dynamo Badge and HM06 Rock Smash. 

**Exact Map Sequence:**
1.  **Lavaridge Town** → East exit to **Route 112**.
2.  **Route 112** → Hop down the **one-way ledges** to the base of the Cable Car station, then walk South to **Route 111**.
3.  **Route 111** → South to **Mauville City**.
4.  **Mauville City** → West exit to **Route 117**.
5.  **Route 117** → West to **Verdanturf Town**.
6.  **Verdanturf Town** → Enter **Rusturf Tunnel**.
7.  **Rusturf Tunnel** → Walk West. *(Note: If the bot did not smash the rocks here earlier during the Wattson routing, it must use Rock Smash now. If previously smashed, they remain cleared.)* Exit West to **Route 116**.
8.  **Route 116** → West to **Rustboro City**.
9.  **Rustboro City** → South exit to **Route 104**.
10. **Route 104** → Enter **Petalburg Woods** (North entrance).
11. **Petalburg Woods** → Walk South through the tall grass (no HM Cut required going North-to-South). Exit South to **Route 104**.
12. **Route 104** → South/East to **Petalburg City**.

### 3. PETALBURG GYM ENTRY (Map: `MAP_PETALBURG_CITY_GYM`)
*   **Entry Sequence:** There is no cutscene upon walking into the Gym at this stage. The bot simply walks in.
*   **The Gate:** The physical sliding doors at the back of the entrance room are coded as interactive objects. Their `EventScript` checks for `FLAG_BADGE04_GET` (the Heat Badge). Because the bot has this flag, interacting with the left or right door will cause it to slide open and warp the player to the first tier of rooms. 

### 4. PETALBURG GYM ROOM PUZZLE (`VAR_PETALBURG_GYM_STATE`)
The gym is a single large map (`MAP_PETALBURG_CITY_GYM`) connected by internal warps. `VAR_PETALBURG_GYM_STATE` increments as you defeat trainers, allowing doors to slide open. 

**The Rule:** Defeating the trainer in a room unlocks the doors at the back of *that specific room*. You must clear 3 rooms to reach Norman. 
**The Path:** The bot does not need to dynamically evaluate rooms. You can hardcode a **"Left Door Only"** route, which is fully valid and standard for speedruns:
1.  **Entrance Room:** Take the **LEFT** door. → Warps to **Speed Room**.
2.  **Speed Room:** Defeat Randall (Swellow Lv26). Take the **LEFT** door. → Warps to **Confusion Room**.
3.  **Confusion Room:** Defeat Parker (Spinda Lv26). Take the **LEFT** door. *(Note: Both doors in this room warp to the Strength Room, but sticking to Left simplifies bot logic).* → Warps to **Strength Room**.
4.  **Strength Room:** Defeat Jody (Zangoose Lv26). Take the **LEFT** door. → Warps to **Gym Leader Room** (Norman).

### 5. NORMAN BATTLE & AFTERMATH (HM03 SURF)
**The Battle:**
*   **Norman's Emerald Team:** Spinda (Lv27), Vigoroth (Lv27), Linoone (Lv29), Slaking (Lv31). 
*   **Flags Set:** Beating him triggers `PetalburgCity_Gym_EventScript_NormanDefeated`, which sets `FLAG_DEFEATED_PETALBURG_GYM` and `FLAG_BADGE05_GET`, gives TM42 (Facade), and updates `VAR_PETALBURG_GYM_STATE` to `6`.

**The HM03 Surf Sequence:**
*   **Trigger:** After the battle ends, the bot must take a **step downwards** to attempt to leave Norman's room. 
*   Because `VAR_PETALBURG_GYM_STATE` is now `6`, a `coord_event` step trigger fires.
*   **Sequence:** Wally's Dad automatically walks into the room, initiates dialogue, and the script forcefully warps the player to `MAP_PETALBURG_CITY_WALLYS_HOUSE`.
*   **Inside the House:** An auto-run script triggers immediately upon loading the map. Wally's Dad talks to the player, hands over HM03 Surf, and sets `FLAG_RECEIVED_HM_SURF`. The bot is now free to leave the house.

### 6. AUTOMATION GOTCHAS & WARNINGS
*   **Slaking’s Truant:** Norman's ace, Slaking, has the ability *Truant* (loafs around every other turn). Slaking's stats are legendary-tier, but the bot's combat logic can abuse Truant by using Protect, Dig, Fly (if obtained later), or taking free turns to heal. If the bot just spams attacks, Slaking's Retaliate/Facade will likely wipe it.
*   **One-Way Ledges (Route 112):** The bot *must* approach Route 111 by jumping down the ledges east of Lavaridge. Attempting to pathfind "up" Jagged Pass or "up" the ledges will result in the bot getting stuck.
*   **Step Trigger Dependency:** Remind the bot to move *downward* after defeating Norman. If the bot uses an Escape Rope or Teleport immediately after the battle menu closes, it will bypass Wally's Dad's step trigger, breaking the story sequence and soft-locking HM03.
*   **Rusturf Tunnel:** Ensure your pathfinding node array recognizes that the middle of Rusturf Tunnel is passable. If the bot's navmesh relies on the initial map state, it might think the tunnel is still blocked by rocks.
*   **Double Battles:** Route 117 has several tightly packed trainers that can trigger forced double battles if the bot steps into their overlapping line of sight. Ensure the bot's battle logic can handle 2v2 targeting.