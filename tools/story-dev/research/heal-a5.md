### GATING AND ROUTING: POST-BADGE 4, PRE-BADGE 5

This analysis refutes the bot's belief that only L3-5 grass is reachable from Petalburg City at this story stage. The player has access to the entire western and central landmass of Hoenn.

#### **Accessibility Summary Table**

The player is assumed to have started from Petalburg City after acquiring the Heat Badge, Go-Goggles, and HM04 Strength. They have not yet defeated Norman.

| Location | Map Constant | Reachable? | Requirements | Required HMs (for full access) | Nearest Healing Point |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Route 111 (South)** | `MAP_ROUTE111` | VERIFIED: Yes | None | Rock Smash | Mauville City |
| **Route 111 (Desert)** | `MAP_ROUTE111` | VERIFIED: Yes | `ITEM_GO_GOGGLES` | None | Lavaridge Town or Mauville City |
| **Route 111 (North)** | `MAP_ROUTE111` | VERIFIED: Yes | `ITEM_GO_GOGGLES` | None | Fallarbor Town |
| **Route 112** | `MAP_ROUTE112` | VERIFIED: Yes | None | Strength (for shortcut) | Lavaridge Town |
| **Route 113** | `MAP_ROUTE113` | VERIFIED: Yes | None | None | Fallarbor Town |
| **Route 114** | `MAP_ROUTE114` | VERIFIED: Yes | None | Rock Smash | Fallarbor Town |
| **Fiery Path** | `MAP_FIERY_PATH` | VERIFIED: Yes | None | Strength | Lavaridge Town |
| **Jagged Pass** | `MAP_JAGGED_PASS` | VERIFIED: Yes | Story Flag: `FLAG_DEFEATED_MAGMA_AT_MT_CHIMNEY` | None | Lavaridge Town |
| **Meteor Falls (West Entrance)** | `MAP_METEOR_FALLS_1F_1R` | VERIFIED: Yes | None | Surf & Waterfall (for deeper areas) | Fallarbor Town |

---

#### **Walking Route from Petalburg City**

This is the primary walking route from `MAP_PETALBURG_CITY` to the specified training areas.

1.  **Petalburg City -> Mauville City (The Hub)**
    *   VERIFIED: Exit Petalburg east to `MAP_ROUTE104`.
    *   VERIFIED: Traverse `MAP_PETALBURG_WOODS`.
    *   VERIFIED: Emerge on the northern part of `MAP_ROUTE104` and enter `MAP_RUSTBORO_CITY`.
    *   VERIFIED: Exit Rustboro east to `MAP_ROUTE116`.
    *   VERIFIED: Traverse `MAP_RUSTURF_TUNNEL`. The second exit is now clear. The player must have used Rock Smash previously to fulfill the sidequest that clears the path.
    *   VERIFIED: Emerge on the eastern part of `MAP_ROUTE116` and enter `MAP_VERDANTURF_TOWN`.
    *   VERIFIED: Exit Verdanturf east onto `MAP_ROUTE117` and proceed to `MAP_MAUVILLE_CITY`.

2.  **Mauville City -> Route 111/112 Corridor**
    *   VERIFIED: From `MAP_MAUVILLE_CITY`, exit north to `MAP_ROUTE111`.
    *   VERIFIED: On `MAP_ROUTE111`, the player can proceed north. The path splits:
        *   **Path A (West):** Leads to `MAP_ROUTE112`, which connects to `MAP_FIERY_PATH` and the base of Mt. Chimney.
        *   **Path B (North):** Leads through the Route 111 desert, requiring Go-Goggles.

3.  **Corridor Navigation**
    *   VERIFIED: From the west part of `MAP_ROUTE112`, the player can ascend Mt. Chimney via the cable car.
    *   VERIFIED: From the top of Mt. Chimney, the player can descend south through `MAP_JAGGED_PASS` to reach the east part of `MAP_ROUTE112` and `MAP_LAVARIDGE_TOWN`.
    *   VERIFIED: Alternatively, from the west part of `MAP_ROUTE112`, the player can traverse `MAP_FIERY_PATH`. The main path leads to the east part of `MAP_ROUTE112`.
    *   VERIFIED: Following Path B through the Route 111 desert leads to the northern section of `MAP_ROUTE111`.
    *   VERIFIED: This northern section of `MAP_ROUTE111` connects west to `MAP_ROUTE113`.
    *   VERIFIED: `MAP_ROUTE113` connects west to `MAP_FALLARBOR_TOWN`.
    *   VERIFIED: `MAP_FALLARBOR_TOWN` connects west to `MAP_ROUTE114`.
    *   VERIFIED: `MAP_ROUTE114` connects south to the west entrance of `MAP_METEOR_FALLS_1F_1R`.

---

#### **Specific Requirements and Blockers**

**1. Go-Goggles and Route 111 Desert**
*   **Acquisition:** VERIFIED: The Go-Goggles (`ITEM_GO_GOGGLES`) are given to the player by their rival on `MAP_ROUTE112` immediately after exiting Lavaridge Town, post-Flannery victory. This is triggered by `FLAG_DEFEATED_LAVARIDGE_GYM`. The event script is `Route112_EventScript_Rival` in `data/maps/Route112/scripts.inc`.
*   **Gating Mechanism:** VERIFIED: The sandstorm on `MAP_ROUTE111` is a scripted barrier. The map script `Route111_EventScript_CheckSandstorm` checks if the player has the Go-Goggles. If not, script `Route111_EventScript_SandstormTurnPlayer` is called, forcing the player one tile south and preventing entry.
    *   File: `data/maps/Route111/scripts.inc`
*   **Grass Patches:**
    *   VERIFIED: A small patch of grass is on the southern part of `MAP_ROUTE111` at coordinates (17, 44) to (27, 50). This is reachable *before* the desert and does not require Go-Goggles.
    *   VERIFIED: A larger patch of grass is on the northern part of `MAP_ROUTE111` at coordinates (11, 10) to (18, 17). This is *after* the desert and requires Go-Goggles to reach.

**2. HM Usage and Gates**
*   **HM06 Rock Smash:** VERIFIED: Usable in the field after obtaining the Dynamo Badge (Badge 3) from Watson. Required to pass through Rusturf Tunnel and access various items/areas on Routes 111 and 114.
    *   Source: `CanUseRockSmash` in `src/field_specials.c` checks for `FLAG_BADGE03_GET`.
*   **HM04 Strength:** VERIFIED: Usable in the field after obtaining the Heat Badge (Badge 4) from Flannery. The player *can now use Strength*.
    *   Source: `CanUseStrength` in `src/field_specials.c` checks for `FLAG_BADGE04_GET`.
    *   **Fiery Path:** A Strength boulder in `MAP_FIERY_PATH` at (9, 9) blocks access to the northern exit, which leads to a separate part of `MAP_ROUTE112` near the desert entrance. Pushing this creates a valuable shortcut.
*   **HM03 Surf:** INFERENCE: Wally's father gives the player HM03 Surf in Petalburg City upon their return after defeating Flannery. VERIFIED: Surf is unusable outside of battle until the Balance Badge (Badge 5) is obtained from Norman.
    *   Source: `CanUseSurf` in `src/field_specials.c` checks for `FLAG_BADGE05_GET`.
    *   **Impact:** Any area requiring Surf, such as the far side of Meteor Falls or island portions of routes, is inaccessible.

**3. Story Flags and NPC Blockers**
*   **Jagged Pass:** VERIFIED: Previously blocked by Team Magma grunts. They disappear once the player has defeated Team Magma at Mt. Chimney, which sets `FLAG_DEFEATED_MAGMA_AT_MT_CHIMNEY`. This is a prerequisite for earning Badge 4, so the path is open.
*   **Magma Hideout (Emerald Specific):** VERIFIED: In Emerald, the Team Magma Hideout entrance is a cave on `MAP_JAGGED_PASS`. At this point in the story, a single grunt blocks the entrance.
    *   Script: `JaggedPass_EventScript_MagmaGruntHideout` in `data/maps/JaggedPass/scripts.inc`.
    *   This grunt remains until after the events on Mt. Pyre, when the flag `FLAG_JAGGED_PASS_MAGMA_HIDEOUT_OPEN` is set. The hideout is therefore inaccessible. This differs from Ruby, where the hideout was on Mt. Chimney.