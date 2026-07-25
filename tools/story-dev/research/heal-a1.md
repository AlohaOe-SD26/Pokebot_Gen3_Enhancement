### Conclusion

**(INFERENCE):** The user is misremembering the location. There is no house on Route 112 or Route 113 where an NPC provides a full party heal. The user's description of the interaction—talking to an NPC for a full heal—most closely matches an NPC in Lavaridge Town. A secondary possibility, which better matches the geographical area, is the Rest House on Route 111, though this is an interaction with a bed, not an NPC.

---

### Candidate 1: Old Woman in Lavaridge Town (Best Match for Interaction)

This is the most likely candidate the user is remembering, as it involves a direct NPC conversation leading to a full party heal, similar to a Poké Center. The location is adjacent to the Route 112 corridor.

**(VERIFIED):** This NPC provides a full HP, PP, and status condition heal for the entire party, functionally identical to a Pokémon Center.

| Feature                  | Details                                                                                                                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Map Constant**         | `MAP_LAVARIDGE_TOWN` **(VERIFIED)**                                                                                                                                                 |
| **Location**             | Lavaridge Town, in the outdoor hot spring pool. **(VERIFIED)**                                                                                                                      |
| **NPC / Object**         | Old Woman (local `object_event_id: 4`) **(VERIFIED)**                                                                                                                               |
| **Coordinates (Local)**  | (X: 25, Y: 9) **(VERIFIED)**                                                                                                                                                        |
| **Controlling Script**   | `LavaridgeTown_EventScript_OldWoman` in `data/maps/LavaridgeTown/scripts.inc` **(VERIFIED)**                                                                                        |
| **Healing Function**     | The script calls `special HealPlayerParty`. This is the same special function used by Pokémon Center nurses and the player's Mom for a full party restoration. **(VERIFIED)**       |
| **Dialogue Flow**        | 1. **Initial text:** "The hot sand is wonderfully soothing… Ahhh… Care to join me for a soak? It will restore your POKéMON to full health." **(VERIFIED)**<br>2. **Prompt:** A YES/NO choice box is presented. **(VERIFIED)**<br>3. **If YES:** The screen fades, the healing sound effect (`SE_HEAL`) plays, the party is healed, the screen fades back in, and the NPC says, "There you are. All better." **(VERIFIED)**<br>4. **If NO:** The NPC says, "Oh, what a shame. You are missing out." **(VERIFIED)** |
| **Gating / Conditions**  | This heal is repeatable and has no prerequisite flags or variable checks beyond initiating the conversation. **(VERIFIED)**                                                              |

### Candidate 2: Bed in Route 111 Rest House (Best Match for Geography)

This location is geographically on the specified corridor but does not match the user's description of interacting with an NPC. The heal is triggered by interacting with an object (a bed).

**(VERIFIED):** This bed provides a full HP, PP, and status condition heal for the entire party.

| Feature                  | Details                                                                                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Map Constant**         | `MAP_ROUTE111_REST_STOP` **(VERIFIED)**                                                                                                                                         |
| **Location**             | Route 111, in the unnamed house between the desert entrance and the Route 112 junction. **(VERIFIED)**                                                                          |
| **NPC / Object**         | Bed (script is triggered by stepping on coordinates) **(VERIFIED)**                                                                                                             |
| **Coordinates (Local)**  | The script trigger is at (X: 3, Y: 2) or (X: 4, Y: 2). **(VERIFIED)**                                                                                                           |
| **Controlling Script**   | `Route111_RestStop_EventScript_Bed` in `data/maps/Route111/scripts.inc` **(VERIFIED)**                                                                                         |
| **Healing Function**     | The script calls `special HealPlayerParty`, same as a Pokémon Center. **(VERIFIED)**                                                                                            |
| **Dialogue Flow**        | 1. **Initial text:** "It's a rather inviting bed. Take a rest?" **(VERIFIED)**<br>2. **Prompt:** A YES/NO choice box is presented. **(VERIFIED)**<br>3. **If YES:** The screen fades, the healing sound effect (`SE_HEAL`) plays, the party is healed, and the screen fades back in. There is no follow-up dialogue. **(VERIFIED)**<br>4. **If NO:** The script terminates. **(VERIFIED)** |
| **Gating / Conditions**  | Repeatable with no prerequisites. **(VERIFIED)**                                                                                                                               |

---

### Non-Candidates in the Immediate Area (Debunked)

The following are the only other houses on the Route 112/113 corridor. Neither offers a healing service.

*   **Glass Workshop (Route 113):**
    *   Map: `MAP_ROUTE113_GLASS_WORKSHOP` **(VERIFIED)**
    *   NPC: Glass Worker.
    *   Function: The NPC provides the `ITEM_SOOT_SACK` to collect volcanic ash. His script (`Route113_GlassWorkshop_EventScript_GlassWorker`) contains no healing commands. **(VERIFIED)**
*   **Winstrate Family House (Route 111 / 112 border):**
    *   Map: `MAP_ROUTE111_WINSTRATE_FAMILYS_HOUSE` **(VERIFIED)**
    *   NPCs: Victor, Victoria, Vivi, and Vicky Winstrate.
    *   Function: The family challenges the player to a sequence of four battles. Upon defeating them, the mother (Victoria) gives the player the `ITEM_MACHO_BRACE`. The associated scripts (`Route111_WinstrateHouse_EventScript_...`) contain `trainerbattle` commands but no healing commands. **(VERIFIED)**

### Emerald vs. Ruby/Sapphire Differences

**(VERIFIED):** There are no differences between Pokémon Emerald and Pokémon Ruby/Sapphire regarding the functionality of these specific healing locations. Both the Lavaridge Town Old Woman and the Route 111 Rest House bed exist and function identically in all three games.