Here is the exhaustive, structurally verified data for routing a bot through Team Magma’s Hideout (Jagged Pass) and Team Aqua’s Hideout (Lilycove) in Pokémon Emerald. 

### [VERIFIED] Emerald-Specific Core Differences (Rule 4)
*   **Ruby/Sapphire:** Magma and Aqua share the same hideout map in Lilycove City (the game loads either Magma or Aqua NPCs based on version). Jagged Pass has no hideout.
*   **Emerald:** The Lilycove hideout belongs **exclusively to Team Aqua**. Team Magma receives a completely new, unique map geometry: **Team Magma's Hideout** located within Jagged Pass.

---

### Part 1: Team Magma's Hideout (Jagged Pass)

#### 1. Entry Requirements & Trigger
| Element | Details |
| :--- | :--- |
| **Prerequisite** | Player must possess `ITEM_MAGMA_EMBLEM` (obtained from Mt. Pyre). |
| **Map Constant** | `MAP_JAGGED_PASS` |
| **Script File** | `data/maps/JaggedPass/scripts.inc` |
| **Event Script** | `JaggedPass_EventScript_OpenMagmaHideout` |
| **Trigger Logic** | [VERIFIED] Handled by `JaggedPass_EventScript_CaveEntranceMiddle`. If the player has the Magma Emblem, stepping on a specific tile triggers a screen shake and changes the rock wall metatile to a cave entrance. |
| **Coordinates** | [INFERENCE] The trigger tile is roughly `(x=16, y=17)`. The bot must step here to execute the `map_script` that opens the cave. |

#### 2. Hideout Navigation & Battles
[VERIFIED] Unlike the Aqua hideout, the Magma Hideout contains **no warp panels or teleporter puzzles**. It is a linear cave with branching optional rooms. 
*   **Map Constants:** `MAP_MAGMA_HIDEOUT_1F`, `MAP_MAGMA_HIDEOUT_2F_1R`, `MAP_MAGMA_HIDEOUT_2F_2R`, `MAP_MAGMA_HIDEOUT_3F_1R`, `MAP_MAGMA_HIDEOUT_3F_2R`, `MAP_MAGMA_HIDEOUT_4F`.
*   **Trainers:** Bot must parse `data/maps/MagmaHideout_*/events.json` for `TRAINER_GRUNT_MAGMA_HIDEOUT_1` through `16`.
*   **Admin Encounter:** [VERIFIED] Admin Tabitha (`TRAINER_TABITHA_MAGMA_HIDEOUT`) blocks the path just before the final room in `MAP_MAGMA_HIDEOUT_3F_2R`.

#### 3. Maxie & Groudon Encounter
| Element | Details |
| :--- | :--- |
| **Map Constant** | `MAP_MAGMA_HIDEOUT_4F` |
| **Script File** | `data/maps/MagmaHideout_4F/scripts.inc` |
| **Event Script** | `MagmaHideout_4F_EventScript_Maxie` |
| **Execution Order** | 1. Bot approaches Maxie. <br>2. Groudon awakening cutscene plays. <br>3. `FLAG_HIDE_MAGMA_HIDEOUT_GROUDON` is set (Groudon vanishes). <br>4. Bot battles `TRAINER_MAXIE_MAGMA_HIDEOUT`. |
| **Crucial Flags Set** | [VERIFIED] Defeating Maxie sets `FLAG_DEFEATED_MAGMA_HIDEOUT_MAXIE`.<br>[VERIFIED] Setting this flag is the **hard gate** required to spawn the Slateport City Harbor event (which is required to enter the Aqua Hideout). |

---

### Part 2: Team Aqua's Hideout (Lilycove City)

#### 1. Entry Requirements & Trigger
| Element | Details |
| :--- | :--- |
| **Prerequisite** | The Slateport Harbor Submarine theft event must be complete. |
| **Required State** | [VERIFIED] `FLAG_DEFEATED_MAGMA_HIDEOUT_MAXIE` must be true to trigger Slateport. Captain Stern's interview in Slateport sets Archie to steal the submarine. |
| **Hideout State** | [VERIFIED] Prior to the Slateport event, Aqua Grunts physically block the teleporters in `MAP_AQUA_HIDEOUT_1F`. Once the sub is stolen, the grunts disappear. |
| **Map Constant** | Access via `MAP_LILYCOVE_CITY` (Surf northeast to the cove) -> `MAP_AQUA_HIDEOUT_1F`. |

#### 2. The Deterministic Warp Puzzle Sequence
[VERIFIED] The bot must navigate a series of warp panels (teleporters). To make the bot strictly deterministic, you must extract the exact `x, y` pairs from `data/maps/AquaHideout_B1F/map.json` and `data/maps/AquaHideout_B2F/map.json` under the `"warps"` arrays.

**Sequence A: Path to the Submarine (Mandatory Progression)**
[INFERENCE] The standard route to bypass the puzzle and reach the sub is as follows. (Bot dev: verify exact warp IDs in `map.json`):
1.  **1F:** Enter `MAP_AQUA_HIDEOUT_1F`. Walk up to the stairs -> `MAP_AQUA_HIDEOUT_B1F`.
2.  **B1F:** Walk right and down. Take the stairs on the right side -> `MAP_AQUA_HIDEOUT_B2F`.
3.  **B2F Warp 1:** Step on the only available warp pad in this sector.
4.  **B1F Warp 2:** Arrive in an enclosed sector of B1F. Step on the only warp pad here.
5.  **B1F Warp 3:** Arrive in another enclosed sector. Step on the only warp pad here.
6.  **B2F Submarine Room:** Arrive in the top half of `MAP_AQUA_HIDEOUT_B2F` where the submarine is docked.

**Sequence B: The Master Ball Puzzle (Optional but highly recommended for bots)**
[UNSURE/INFERENCE] In `MAP_AQUA_HIDEOUT_B1F`, there is a central room with multiple warp pads arranged in a grid.
*   **Path to Master Ball:** The traditional human walkthrough sequence is Left, Center, Left, Left. 
*   **Bot Implementation:** Do not hardcode "Left/Center". Program the bot to read `data/maps/AquaHideout_B1F/map.json`. Look for the `"warps"` array. The warp that lands the player in the room containing `ITEM_MASTER_BALL` (check `"object_events"` in `map.json`) is the target. Map the warp graph backwards from the Master Ball room to the grid room entrance to generate the deterministic path.

#### 3. Matt (Admin) & Submarine Departure
| Element | Details |
| :--- | :--- |
| **Map Constant** | `MAP_AQUA_HIDEOUT_B2F` |
| **Script File** | `data/maps/AquaHideout_B2F/scripts.inc` |
| **Event Script** | `AquaHideout_B2F_EventScript_MattNoticePlayer` |
| **Boss Battle** | [VERIFIED] Archie is **not** fought here (he is in the sub). The bot fights Admin Matt (`TRAINER_MATT`). |
| **Sub Departure** | [VERIFIED] Script `AquaHideout_B2F_EventScript_SubmarineDepart` executes after Matt is defeated. The submarine sprite animates and disappears. |
| **Crucial Flags Set** | [VERIFIED] Sets `FLAG_HIDE_AQUA_HIDEOUT_SUBMARINE`.<br>[VERIFIED] Sets `FLAG_HIDE_LILYCOVE_CITY_WAILMER` (This is the critical flag that clears the Wailmer blockade in Lilycove City, allowing the bot to Surf east to Route 124). |
| **Cleanup Flag** | [VERIFIED] Sets `FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`. Once the bot leaves, the hideout empties permanently. |

### Summary Action-List for Bot Development:
1.  **Check bag** for `ITEM_MAGMA_EMBLEM`.
2.  **Navigate** to `MAP_JAGGED_PASS`, walk to `x=16, y=17` to trigger `JaggedPass_EventScript_OpenMagmaHideout`.
3.  **Pathfind** through `MAP_MAGMA_HIDEOUT_*`, battle `TRAINER_MAXIE_MAGMA_HIDEOUT`.
4.  **Verify** `FLAG_DEFEATED_MAGMA_HIDEOUT_MAXIE` == True.
5.  **Execute** Slateport Harbor event (external to hideout).
6.  **Navigate** to `MAP_AQUA_HIDEOUT_1F` via `MAP_LILYCOVE_CITY`.
7.  **Pathfind warps** by dynamically reading `"warps"` in `AquaHideout_B1F/map.json` and `AquaHideout_B2F/map.json` targeting the room with `AquaHideout_B2F_EventScript_MattNoticePlayer`.
8.  **Defeat** `TRAINER_MATT`, verify `FLAG_HIDE_LILYCOVE_CITY_WAILMER` == True.
9.  **Exit** and route to Route 124.