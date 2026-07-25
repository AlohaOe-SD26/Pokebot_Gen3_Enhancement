## A. MECHANICS THE ROM ENFORCES

**1. Surf & Movement Mechanics**
| Mechanic | Implementation / Rule | Status |
| :--- | :--- | :--- |
| **HM Requirement** | Requires `FLAG_BADGE05_GET` (Norman) and a party Pokémon with `MOVE_SURF`. Checked via `IsPlayerSurfingNorth` etc. in `src/field_player_avatar.c`. | **VERIFIED** |
| **Water Metatiles** | Tiles with `METATILE_ATTRIBUTE_BEHAVIOR` equal to `MB_SURF_EAST`, `MB_OCEAN_WATER`, `MB_LAKE_WATER`, `MB_POND_WATER` permit surfing. | **VERIFIED** |
| **Encounters** | Checked in `src/wild_encounter.c` (`WaterWildEncounter`). Only triggers on tiles where `MapGridGetMetatileBehaviorAt` matches `MB_SURF` or equivalent, using the `waterMons` encounter table. | **VERIFIED** |
| **Speed/Step** | Surfing changes player movement speed and ignores standard terrain movement penalties (e.g., sand). | **VERIFIED** |

**2. Dive Mechanics**
| Mechanic | Implementation / Rule | Status |
| :--- | :--- | :--- |
| **HM Requirement** | Requires `FLAG_BADGE07_GET` (Liza & Tate) and `MOVE_DIVE`. | **VERIFIED** |
| **Diving Down** | Can only be used on surface metatiles with behavior `MB_DIVE_WARP` (deep water). Triggers `FieldEffectStart(FLDEFF_USE_DIVE)`. | **VERIFIED** |
| **Surfacing** | Can only be used on underwater metatiles with behavior `MB_SURFACE`. The ROM checks the surface map to ensure the corresponding tile above is `MB_DIVE_WARP` before allowing surfacing. | **VERIFIED** |
| **Map Connections** | Surface and underwater maps are strictly paired (e.g., `MAP_ROUTE_124` ↔ `MAP_UNDERWATER_ROUTE_124`). The coordinate system is identical (1:1 X/Y mapping). Handled in `src/overworld.c` (`GetDiveWarpMap`). | **VERIFIED** |

**3. Currents & Forced Movement (Routes 132-134)**
| Mechanic | Implementation / Rule | Status |
| :--- | :--- | :--- |
| **Tile Behaviors** | `MB_CURRENT_R`, `MB_CURRENT_L`, `MB_CURRENT_U`, `MB_CURRENT_D` define the forced movement vectors. | **VERIFIED** |
| **Execution** | Handled in `src/field_control_avatar.c` (`GetForcedMovementByMetatileBehavior`). When stepping onto one of these tiles, player control is locked, and the sprite automatically slides in the tile's designated direction until hitting a non-current tile (calm water or shallows). | **VERIFIED** |
| **Encounters in Currents** | Encounters CAN occur during forced movement. If an encounter triggers, the movement pauses, the battle resolves, and the forced movement instantly resumes. | **VERIFIED** |

**4. Waterfall**
| Mechanic | Implementation / Rule | Status |
| :--- | :--- | :--- |
| **HM Requirement** | Requires `FLAG_BADGE08_GET` (Juan) and `MOVE_WATERFALL`. | **VERIFIED** |
| **Execution** | Requires interacting while facing a tile with `MB_WATERFALL`. Triggers `FLDEFF_USE_WATERFALL`, forcing the player "Up" continuously until hitting a tile without `MB_WATERFALL`. | **VERIFIED** |

**5. Fishing Minigame (Emerald Specific)**
| Mechanic | Implementation / Rule | Status |
| :--- | :--- | :--- |
| **State Machine** | Handled in `src/fishing.c`. States: `FISHING_START`, `FISHING_NIBBLE`, `FISHING_BITE`, `FISHING_GOT_AWAY`, etc. | **VERIFIED** |
| **Timing Window** | When a bite occurs (`sFishingState == FISHING_SHOW_BITE`), a timer `sFishingBiteTimer` ticks down. The player must press `A_BUTTON` before it hits 0. Pressing `A` *before* this state causes failure ("Pulled the rod away too early!"). | **VERIFIED** |
| **Consecutive Bites** | **EMERALD DIFFERENCE:** Unlike RS/FRLG, Emerald requires chaining consecutive successful timed `A` presses. Old Rod = 1 press. Good Rod = up to 2. Super Rod = up to 4. RNG dictates the required number per encounter. | **VERIFIED** |
| **Abilities** | **EMERALD DIFFERENCE:** If the lead Pokémon has `ABILITY_SUCTION_CUPS` or `ABILITY_STICKY_HOLD`, the initial RNG check to hook a fish is far more likely to succeed. | **VERIFIED** |

**6. Map & Encounter Typology**
| Type | Routes | Properties | Status |
| :--- | :--- | :--- | :--- |
| **Hybrid (Water/Land)** | 103, 104, 105, 106, 109, 115, 118, 119, 120, 121, 122, 123. | Contains both `landMons` (grass) and `waterMons` tables. Can be traversed partially without Surf. | **VERIFIED** |
| **Pelagic (Water Only)** | 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134. | Nearly zero land encounters (except Mirage Island on 130). Rely exclusively on `waterMons` and `fishingMons`. | **VERIFIED** |
| **Dive Routes** | 124, 126, 127, 128. | The only routes with deep water (`MB_DIVE_WARP`). | **VERIFIED** |

## B. WHAT THE BOT CAN OBSERVE

| Element | Observable State / Memory Location | Access Method |
| :--- | :--- | :--- |
| **Current Layer (Surface/Dive)** | `gSaveBlock1Ptr->location.mapGroup` and `mapNum`. | Memory Read. If `mapGroup` is 24 (Underwater), the bot is dived. |
| **Surfing/Diving State** | `gPlayerAvatar.flags` | Memory Read. Check bitmasks `PLAYER_AVATAR_FLAG_SURFING` (0x08) and `PLAYER_AVATAR_FLAG_UNDERWATER` (0x20). |
| **Water / Current Metatiles** | `gMapHeader.mapLayout->map` (combined with `gMapHeader.mapLayout->width`). | Memory Read. Translate (X,Y) to index, bitshift to get metatile ID, look up behavior in `gMapHeader.mapLayout->primary` / `secondary` block. |
| **Fishing State** | `sFishingState` inside `src/fishing.c` (BSS section). | Memory Read. Look for `FISHING_SHOW_BITE` to send the `A_BUTTON` input. |
| **Forced Movement** | `gPlayerAvatar.state` and `gPlayerAvatar.transitionFlags`. | Memory Read. Player state will indicate forced movement, locking D-Pad inputs. |

## C. OPTION SPACE

### Strategy 1: The Clairvoyant Graph (Pre-calculated Directed NavMesh)
The bot reads the entire `gMapHeader.mapLayout` upon entering a map. It treats standard water as bi-directional edges and currents (`MB_CURRENT_*`) as strictly uni-directional forced edges. It runs A* or Dijkstra's algorithm to the map warp.
*   **Cost:** High computational overhead in the bot's pathfinding logic. Requires decoding the map layout format into a graph dynamically.
*   **Failure Mode:** If the bot doesn't account for NPC sightlines or wild encounter interruptions, an encounter on a current tile can desync the bot's presumed location if its internal state tracker doesn't halt.
*   **Detection:** Bot verifies `gSaveBlock1Ptr->pos.x` and `y` against its expected step path. If they diverge, trigger a recalculation.

### Strategy 2: Blind Vector Projection (Reactive Raycasting)
The bot only reads a 3x3 or 5x5 grid of metatiles around `gSaveBlock1Ptr->pos`. It moves toward the objective, treating currents as obstacles unless they point directly toward the goal.
*   **Cost:** Extremely low memory cost. Easy to code.
*   **Failure Mode:** Fails catastrophically on Routes 132-134. Because currents form complex loops and dead-ends, a reactive bot will almost certainly be swept to Pacifidlog Town or Slateport repeatedly, completely unable to navigate to the Sealed Chamber.
*   **Detection:** The bot reads `gSaveBlock1Ptr->location` and sees it has transitioned to Pacifidlog instead of its intended Route.

### Strategy 3: Macro Playback with Spliced Error Correction (Hardcoded Routes)
Because Route 132-134 currents are static, the bot uses a hardcoded sequence of inputs (e.g., "Down, Left, Left, Down...") mapped to specific coordinates, ignoring dynamic pathfinding.
*   **Cost:** Bot is rigidly tied to EMERALD's specific map layout (which differs slightly from RS).
*   **Failure Mode:** Wild encounters interrupt the D-Pad timing. If a frame-perfect input was expected immediately after exiting a current, the wild battle delay ruins it.
*   **Detection:** Before executing the next hardcoded step, verify `gSaveBlock1Ptr->pos.x/y`. If the coordinate does not match the macro's anchor point, backtrack or loop.

## D. TRAPS

**1. The Pacifidlog Stranding (Softlock)**
*   **Mechanic:** Pacifidlog Town is surrounded by water. It has a Pokémon Center (PC).
*   **Trap:** If the bot deposits all Pokémon knowing Surf/Fly in the PC, and releases/trades them away, and does not have a fishing rod, OR has a fishing rod but exactly 0 Pokéballs, it cannot leave the town.
*   **Why a Bot Fails:** Bots optimizing PC space might aggressively dump HM slaves.
*   **Mitigation:** The ROM prevents releasing the *last* Pokémon in your party/PC that knows an HM move like Surf. However, EMERALD's protection can be bypassed if the bot saves, resets, or uses specific day-care edge cases (UNSURE on day-care bypass, VERIFIED on release protection). To be completely safe, explicitly ban depositing the primary Surf user.

**2. Route 132-134 Infinite Sweeps (Resource Exhaustion/Wedge)**
*   **Mechanic:** Moving westward from Pacifidlog forces the player through one-way currents.
*   **Trap:** There are multiple current paths. Only one specific path leads to the dive spot for the Sealed Chamber (required to unlock the Regis). Missing the precise tile entry forces the player to ride currents all the way to Route 134, requiring a Fly back to Pacifidlog to try again.
*   **Why a Bot Fails:** A bot without exact pathing will continually miss the 1-tile wide correct current entry, loop to the end, Fly back, and repeat infinitely.

**3. Fishing Infinite Loop (Wedge)**
*   **Mechanic:** The fishing mini-game requires precise `A` button timing.
*   **Trap:** If the bot initiates fishing but misses the frame window (e.g., polling memory too slowly or failing to chain the 4 required presses for the Super Rod), it will reel in nothing. If its logic is "Fish until I catch X", it will sit by the water pressing the rod infinitely.
*   **Mitigation:** The bot MUST monitor `sFishingState == FISHING_SHOW_BITE` and write the `A_BUTTON` input to the emulator strictly within `sFishingBiteTimer` ticks.

**4. Repel Desync on Deep Water (Time Exhaustion)**
*   **Mechanic:** Encounter rates on water are checked almost every step. `MB_SURF` triggers `WaterWildEncounter`, `MB_DIVE_WARP` triggers `WaterWildEncounter`, underwater triggers `UnderwaterWildEncounter`.
*   **Trap:** Navigating long water routes (e.g., Mossdeep to Sootopolis) without Repels takes immense time due to Tentacool/Wingull spam. If a bot uses a Repel but relies on a rigid step-counter for navigation, the prompt "Repel's effect wore off. Use another?" halts movement and expects an A/B input.
*   **Why a Bot Fails:** If the bot sends movement inputs while the Repel dialog is active, it wedges on the text box. The bot must monitor `gSpecialVar_Result` or the active script context to clear the dialogue. (Note: Emerald does *not* auto-prompt to use another Repel; that is a Gen 5+ feature. **RECALL**. In Emerald, it simply says "Repel's effect wore off", forcing an `A` press, and the bot must manually open the bag to use another).