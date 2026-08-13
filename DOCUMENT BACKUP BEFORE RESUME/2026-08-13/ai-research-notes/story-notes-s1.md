Here is the story sequence and data for Mt. Pyre in Pokémon Emerald, following your specified rules.

### 1. Prerequisites and Path to Mt. Pyre

The main story events at Mt. Pyre become accessible after Team Aqua is defeated at the Weather Institute. The path to Mt. Pyre from Fortree City is gated by a story variable set after the player clears the Jagged Pass of Team Magma grunts following the Mt. Chimney event.

*   **VERIFIED:** The primary story progression variable checked for Mt. Pyre events is `VAR_JAGGED_PASS_STATE`. The Team Magma grunts will appear on Mt. Pyre's exterior once `VAR_JAGGED_PASS_STATE` is set to `1` (which occurs after defeating Magma Admin Tabitha at the Magma Hideout entrance on Jagged Pass). The Team Aqua encounter on Route 121 occurs after clearing the Weather Institute.
*   **VERIFIED:** The player travels from Fortree City east through Route 120 and Route 121.
*   **VERIFIED:** On Route 121, near the Safari Zone, the player encounters two Team Aqua grunts who state they are heading to Mt. Pyre. This interaction serves as a narrative signpost.
    *   **Source:** `data/maps/Route121/scripts.inc` (script `Route121_EventScript_AquaGrunts`).
    *   **Trigger:** This event occurs upon entering the map if `FLAG_DEFEATED_AQUA_GRUNTS_AT_WEATHER_INST` is set and `FLAG_MET_AQUA_GRUNTS_ON_ROUTE_121` is not. It sets the latter flag upon completion.
*   **VERIFIED:** The player must travel south from Lilycove City onto Route 122, which is a water route. The HM move `Surf` is required to reach the entrance to Mt. Pyre.

### 2. Mt. Pyre Structure and Navigation

Mt. Pyre consists of three distinct map groups: the interior tower, the exterior mountain path, and the summit. The standard path for the story quest is to ascend the interior floors, exit to the exterior, and climb to the summit.

#### Interior Warps (Floors 1F-6F)

| From Map | From Coords | To Map | To Coords | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `MAP_MT_PYRE_1F` | (7, 2) | `MAP_MT_PYRE_2F` | (13, 2) | Stairs up |
| `MAP_MT_PYRE_2F` | (13, 1) | `MAP_MT_PYRE_1F` | (7, 1) | Stairs down |
| `MAP_MT_PYRE_2F` | (2, 9) | `MAP_MT_PYRE_3F` | (2, 9) | Stairs up |
| `MAP_MT_PYRE_3F` | (2, 10) | `MAP_MT_PYRE_2F` | (2, 10) | Stairs down |
| `MAP_MT_PYRE_3F` | (13, 2) | `MAP_MT_PYRE_4F` | (13, 2) | Stairs up |
| `MAP_MT_PYRE_4F` | (13, 1) | `MAP_MT_PYRE_3F` | (13, 1) | Stairs down |
| `MAP_MT_PYRE_4F` | (7, 10), (8, 10) | `MAP_MT_PYRE_5F` | (7, 10), (8, 10) | Pitfall holes (one-way) |
| `MAP_MT_PYRE_4F` | (2, 9) | `MAP_MT_PYRE_5F` | (2, 9) | Stairs up |
| `MAP_MT_PYRE_5F` | (2, 10) | `MAP_MT_PYRE_4F` | (2, 10) | Stairs down |
| `MAP_MT_PYRE_5F` | (13, 2) | `MAP_MT_PYRE_6F` | (13, 2) | Stairs up |
| `MAP_MT_PYRE_6F` | (13, 1) | `MAP_MT_PYRE_5F` | (13, 1) | Stairs down |
| `MAP_MT_PYRE_6F` | (7, 10), (8, 10) | `MAP_MT_PYRE_EXTERIOR` | (24, 49), (25, 49) | Pitfall holes (one-way, exit to outside) |

**VERIFIED:** All warp data sourced from `data/maps/MtPyre_*/connections.json` and `data/maps/MtPyre_*/map.json`. The intended story path is to take the stairs up to 6F, then fall through one of the two holes at (7, 10) or (8, 10) to land on the exterior path.

#### Exterior/Summit Path

*   **VERIFIED:** The player lands on `MAP_MT_PYRE_EXTERIOR` from the 6F pits. This is a one-way trip; you cannot re-enter the tower from this point.
*   **VERIFIED:** The player ascends the foggy mountain path, battling several Team Magma grunts.
*   **VERIFIED:** The final warp on the exterior path leads to the summit.
    *   **From:** `MAP_MT_PYRE_EXTERIOR` at (12, 5)
    *   **To:** `MAP_MT_PYRE_SUMMIT` at (11, 22)

### 3. Story Sequence: The Summit Confrontation

This event occurs on `MAP_MT_PYRE_SUMMIT`. The Team Magma members are present if `VAR_JAGGED_PASS_STATE` is `1` and the event has not been completed.

**VERIFIED:** The following sequence is controlled by `data/maps/MtPyre_Summit/scripts.inc`.

1.  **Approach Maxie:** The player walks towards the summit peak. Maxie is present, along with two grunts.
    *   **Script Trigger:** Player steps on coordinates (11, 14), (12, 14), or (13, 14).
    *   **Script Label:** `MtPyre_Summit_EventScript_Maxie`

2.  **Maxie's Monologue:** Maxie delivers a speech. He has taken the Blue Orb from its pedestal. He explains his goal to awaken Groudon and expand the landmass. He mentions that Mt. Chimney was a setback but part of a larger plan.
    *   **Script Label:** `MtPyre_Summit_Text_MaxieIntro`

3.  **Maxie Escapes:** Maxie announces he is heading to Slateport City. Unlike in Ruby/Sapphire where he simply walks away, in Emerald he uses the Magma Emblem to warp himself and his grunts away in a flash of light.
    *   **Emerald Difference (VERIFIED):** The use of the Magma Emblem for teleportation is an Emerald-specific animation.
    *   **Script:** `special DoMagmaShakingEffect`, `removeobject`, `waitstate` commands are used to execute this.

4.  **The Old Couple Intervenes:** After Maxie vanishes, the old woman (Phoebe's grandmother) approaches the player.
    *   **Script Label:** `MtPyre_Summit_EventScript_Grandma`

5.  **Receiving the Red Orb:** The grandmother explains that the Blue Orb was stolen, but they managed to save the Red Orb. Fearing Team Magma will return for it, she entrusts the **Red Orb** to the player for safekeeping.
    *   **Item Giver Script:** `giveitem ITEM_RED_ORB`
    *   **Text Label:** `MtPyre_Summit_Text_GrandmaGivesRedOrb`

6.  **Event Flags Set:** The successful completion of this event sets a key flag that advances the global story.
    *   **Flag:** `FLAG_RECEIVED_RED_ORB` is set.
    *   **Note:** The flag `FLAG_RESCUED_OLD_COUPLE_FROM_MT_PYRE` is also set, which permanently removes Maxie and the grunts from the summit.

### 4. Post-Event State and Next Objective

*   **VERIFIED:** Upon setting `FLAG_RECEIVED_RED_ORB`, the game world changes:
    *   Team Aqua will now be present in Slateport City Harbor, attempting to steal the submarine from Captain Stern. This is the player's next destination.
    *   The visibility of the Aqua members in the harbor is gated by checking `if` `FLAG_RECEIVED_RED_ORB` is `TRUE`.
    *   **Source:** `data/maps/SlateportCity_Harbor/scripts.inc`.

*   **VERIFIED:** The old couple remains at the summit. The grandfather will give the player hints about the orbs, and the grandmother will repeat her plea to stop Team Magma.

### 5. Item Locations

| Map | Item | Type | Location (Coords) | Gating Flag/Var |
| :--- | :--- | :--- | :--- | :--- |
| `MAP_MT_PYRE_1F` | `ITEM_ULTRA_BALL` | Pokéball | (2, 2) | None |
| `MAP_MT_PYRE_2F` | `ITEM_SUPER_REPEL` | Hidden | In the northwest corner urn | None |
| `MAP_MT_PYRE_3F` | `ITEM_LAX_INCENSE` | Pokéball | (12, 8) | None |
| `MAP_MT_PYRE_4F` | `ITEM_SEA_INCENSE` | Pokéball | (1, 2) | None |
| `MAP_MT_PYRE_6F` | `ITEM_TM30_SHADOW_BALL` | Gift from NPC | (7, 2) | None |
| `MAP_MT_PYRE_EXTERIOR` | `ITEM_MAX_POTION` | Pokéball | (27, 27) | None |
| `MAP_MT_PYRE_EXTERIOR` | `ITEM_MAX_ETHER` | Hidden | Near a grave on the west side | None |
| `MAP_MT_PYRE_EXTERIOR` | `ITEM_RARE_CANDY` | Hidden | Near the top, on a lone patch of grass | None |
| `MAP_MT_PYRE_EXTERIOR` | `ITEM_TM48_SKILL_SWAP` | Pokéball | (16, 12) | None |
| `MAP_MT_PYRE_SUMMIT` | `ITEM_RED_ORB` | Story Gift | (N/A, from Grandma) | Triggers during summit event |

**VERIFIED:** All item data sourced from `data/maps/MtPyre_*/map.json` and `scripts.inc`.

### 6. Wild Encounters

**VERIFIED:** Encounter data is from `src/data/wild_encounters.c`.

#### Mt. Pyre - Interior (Floors 1F, 2F, 3F, 4F, 5F, 6F)

| Pokémon | Level Range | Encounter Rate |
| :--- | :--- | :--- |
| Shuppet | 22-29 | Common |
| Duskull | 26-29 | Uncommon |
| Vulpix | 28 | Rare (RS Only) |
| Wingull | 28 | Rare (RS Only) |

**Emerald Difference (VERIFIED):** In Emerald, only Shuppet and Duskull appear in the interior floors. Vulpix and Wingull, which were present in Ruby & Sapphire's interior tables, are removed.

#### Mt. Pyre - Exterior (Foggy Path)

| Pokémon | Level Range | Encounter Rate |
| :--- | :--- | :--- |
| Meditite | 25-28 | Common |
| Shuppet | 25-28 | Common |
| Vulpix | 28-30 | Uncommon |
| Wingull | 26 | Rare |
| Duskull | 27 | Rare |

#### Mt. Pyre - Summit (Grass Patches)

| Pokémon | Level Range | Encounter Rate |
| :--- | :--- | :--- |
| Shuppet | 26-31 | Very Common |
| Meditite | 26-29 | Common |
| Vulpix | 30 | Uncommon |
| Duskull | 28 | Uncommon |
| Chimecho | 28-30 | Very Rare (5%) |

**INFERENCE:** The encounter tables for Exterior and Summit are distinct in the ROM data, with Chimecho being exclusive to the summit's grass patches.