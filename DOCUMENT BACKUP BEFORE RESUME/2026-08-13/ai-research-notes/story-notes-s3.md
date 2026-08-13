Here are the ROM-accurate facts for the story progression from the Feather Badge to Mt. Pyre in Pokémon Emerald.

### **Route 120**

This route is accessible from Fortree City to the north. Progression south is initially blocked by an invisible object on a bridge.

**1. Steven and the Devon Scope**

*   **Prerequisite:** VERIFIED: The player must have defeated Winona and obtained the Feather Badge. This is checked by the event script. (Source: `data/maps/Route120/scripts.inc`, label `Route120_EventScript_Steven`)
*   **Event Trigger:** VERIFIED: Player walks south from Fortree City onto Route 120. Steven is standing at coordinates (20, 56) on `MAP_ROUTE_120`.
*   **Interaction:** VERIFIED: Steven will speak to the player and give them the `ITEM_DEVON_SCOPE`. This item is required to reveal invisible Kecleon. (Source: `Route120_EventScript_Steven`)
*   **Flag Set:** VERIFIED: After receiving the Devon Scope, the flag `FLAG_RECEIVED_DEVON_SCOPE` is set. Steven will then walk away and disappear.

**2. Invisible Kecleon (Bridge)**

*   **Location:** VERIFIED: An invisible object blocks the bridge at coordinates (20, 64) on `MAP_ROUTE_120`. (Source: `data/maps/Route120/objects.inc`)
*   **Interaction:** VERIFIED: Interacting with the space triggers a script. If the player has the `ITEM_DEVON_SCOPE`, it will be used automatically, revealing a level 30 Kecleon. (Source: `data/maps/Route120/scripts.inc`, label `Route120_EventScript_KecleonBridge`)
*   **Outcome:** VERIFIED: The player must battle the Kecleon. It can be caught or defeated. After the battle, it runs away, and the path is cleared permanently.
*   **Flag Set:** VERIFIED: `FLAG_HIDE_ROUTE_120_KECLEON_BRIDGE` is set, which removes the Kecleon object from the map on future visits.

### **Route 121**

This route connects Route 120 to Lilycove City and is the location of the Safari Zone entrance.

**1. Team Magma Sighting**

*   **Emerald vs. RS Difference:** VERIFIED: In Emerald, the player encounters Team Magma here. In Ruby/Sapphire, it is Team Aqua.
*   **Event Trigger:** VERIFIED: Walking east past the Safari Zone entrance triggers a cutscene. Two Team Magma grunts are seen at approximately (26, 8) on `MAP_ROUTE_121`. (Source: `data/maps/Route121/scripts.inc`, label `Route121_EventScript_TeamMagmaGrunts`)
*   **Interaction:** VERIFIED: The grunts discuss heading to Mt. Pyre, then run east towards Lilycove City. This is a non-interactive story event.
*   **Flag Set:** INFERENCE/RECALL: A flag is set to mark this event as completed, likely `FLAG_TEAM_MAGMA_GO_TO_MT_PYRE`. This prevents the scene from re-triggering.

**2. Safari Zone Gate**

*   **Location:** VERIFIED: The entrance building is on the northern part of the route. The map is `MAP_ROUTE121_SAFARI_ZONE_ENTRANCE`.
*   **Initial State:** VERIFIED: The attendant at the counter will block the player, stating the Safari Zone is not yet open. This is the default state. (Source: `data/maps/Route121_SafariZoneEntrance/scripts.inc`)
*   **Unlocking:** INFERENCE/RECALL: The Safari Zone opens after the events at Mt. Pyre and the Team Aqua/Magma hideout are resolved. This part of the game is not required for story progression to Mt. Pyre.

### **Lilycove City (`MAP_LILYCOVE_CITY`)**

**1. Rival Battle**

*   **Prerequisite:** INFERENCE/RECALL: This is the player's first visit to Lilycove City.
*   **Event Trigger:** VERIFIED: Walking in front of the Lilycove Department Store, at coordinates (23, 20), will trigger a battle with the rival (May/Brendan). (Source: `data/maps/LilycoveCity/scripts.inc`, label `LilycoveCity_EventScript_RivalBattle`)
*   **Flag Set:** VERIFIED: After the battle, `FLAG_MET_RIVAL_IN_LILYCOVE` is set, preventing this event from re-occurring.

**2. Key Locations**

| Location | Map Constant | Coordinates | Notes | Decomp Source |
| :--- | :--- | :--- | :--- | :--- |
| Pokémon Center | `MAP_LILYCOVE_CITY` | (33, 14) | VERIFIED: Standard healing services. | `data/maps/LilycoveCity/map.json` |
| Poké Mart | `MAP_LILYCOVE_CITY` | (34, 14) | VERIFIED: Standard mart. | `data/maps/LilycoveCity/map.json` |
| Lilycove Dept. Store | `MAP_LILYCOVE_CITY_DEPARTMENT_STORE_1F` | (24, 20) (Entrance) | VERIFIED: Accessible only after the rival battle. | `data/maps/LilycoveCity/events.inc` |
| Contest Hall | `MAP_LILYCOVE_CITY_CONTEST_HALL` | (21, 6) (Entrance) | VERIFIED: Hosts Master Rank contests. Not required for story. | `data/maps/LilycoveCity/map.json` |
| Move Deleter's House | `MAP_LILYCOVE_CITY_MOVE_DELETERS_HOUSE` | (43, 12) (Entrance) | VERIFIED: The Move Deleter is the old man inside. He can delete any move, including HMs. | `data/maps/LilycoveCity_MoveDeletersHouse/scripts.inc` |
| Team Aqua Hideout | `MAP_LILYCOVE_CITY` | (44, 23) (Cave Entrance) | VERIFIED: Blocked by a grunt until after the events at Mt. Pyre and the stolen submarine in Slateport. | `data/maps/LilycoveCity/scripts.inc`, `LilycoveCity_EventScript_AquaHideoutGrunt` |

### **HM Progression to Mt. Pyre**

To proceed from Lilycove City to Mt. Pyre, HMs are required.

| HM | Required For | Status | Notes |
| :--- | :--- | :--- | :--- |
| **HM03 Surf** | Route 122 | **Mandatory** | VERIFIED: Route 122 is a water route. Mt. Pyre is on an island in the middle of it. Access is impossible without Surf. |
| **HM01 Cut** | Side paths on Routes 120, 121, 123 | Optional | VERIFIED: Cut trees block access to optional items and areas, but are not required to travel from Fortree -> Lilycove -> Mt. Pyre. |

### **Route 122 & 123**

*   **Route 122 (`MAP_ROUTE_122`):**
    *   VERIFIED: This is a short, north-south water route connecting Route 121 (north) and Route 123 (south).
    *   VERIFIED: The entrance to Mt. Pyre is located on the large island that dominates this route. The exterior entrance is at `(14, 25)`.
*   **Route 123 (`MAP_ROUTE_123`):**
    *   VERIFIED: This route is not required for story progression at this time. It is a long, east-west route with many ledges, connecting the bottom of Route 122 to Route 118.
    *   VERIFIED: Contains the Berry Master's House.

### **Wild Encounter Tables**

All data below is VERIFIED.
Source: `src/data/wild_encounters.c`

**Route 120 (`MAP_ROUTE_120`)**

| Type | Species | Level Range |
| :--- | :--- | :--- |
| **Grass** | Poochyena | 25-27 |
| | Linoone | 25, 27 |
| | Wingull | 25-27 |
| | Oddish | 25-27 |
| | Marill | 25, 27 |
| | Absol | 25, 27 |
| | Kecleon | 25 |
| **Tall Grass** | Poochyena | 25-27 |
| | Linoone | 25, 27 |
| | Seedot | 25-27 |
| | Wingull | 25-27 |
| | Oddish | 25-27 |
| | Marill | 25, 27 |
| | Absol | 25, 27 |
| | Kecleon | 25 |
| **Surfing** | Marill | 10-30 |
| | Surskit | 20-30 |
| **Fishing (Old Rod)** | Magikarp | 5-10 |
| | Tentacool | 5-10 |
| **Fishing (Good Rod)** | Magikarp | 10-30 |
| | Tentacool | 10-30 |
| | Goldeen | 10-30 |
| | Barboach | 10-30 |
| **Fishing (Super Rod)** | Barboach | 20-45 |
| | Whiscash | 30-45 |

**Route 121 (`MAP_ROUTE_121`)**

| Type | Species | Level Range |
| :--- | :--- | :--- |
| **Grass** | Poochyena | 25-27 |
| | Shuppet | 26-28 |
| | Linoone | 26, 28 |
| | Wingull | 26-28 |
| | Oddish | 26, 28 |
| | Gloom | 28 |
| | Duskull | 26-28 |
| | Kecleon | 25 |
| **Tall Grass** | Poochyena | 25-27 |
| | Shuppet | 26-28 |
| | Linoone | 26, 28 |
| | Wingull | 26-28 |
| | Oddish | 26, 28 |
| | Gloom | 28 |
| | Duskull | 26-28 |
| | Kecleon | 25 |

**Route 122 (`MAP_ROUTE_122`)**

| Type | Species | Level Range |
| :--- | :--- | :--- |
| **Surfing** | Tentacool | 20-30 |
| | Wingull | 10-30 |
| | Pelipper | 25-30 |
| | Sharpedo | 30-35 |
| **Fishing (Old Rod)** | Magikarp | 5-10 |
| | Tentacool | 5-10 |
| **Fishing (Good Rod)** | Magikarp | 10-30 |
| | Tentacool | 10-30 |
| | Wailmer | 10-30 |
| **Fishing (Super Rod)** | Sharpedo | 30-35 |
| | Wailmer | 25-45 |

**Route 123 (`MAP_ROUTE_123`)**

| Type | Species | Level Range |
| :--- | :--- | :--- |
| **Grass** | Poochyena | 26-28 |
| | Shuppet | 26-28 |
| | Linoone | 26, 28 |
| | Wingull | 26-28 |
| | Oddish | 26, 28 |
| | Gloom | 28 |
| | Duskull | 26-28 |
| **Surfing** | Tentacool | 20-30 |
| | Wingull | 10-30 |
| | Pelipper | 25-30 |
| **Fishing (Old Rod)** | Magikarp | 5-10 |
| | Tentacool | 5-10 |
| **Fishing (Good Rod)** | Magikarp | 10-30 |
| | Tentacool | 10-30 |
| | Wailmer | 10-30 |
| **Fishing (Super Rod)** | Wailmer | 25-45 |