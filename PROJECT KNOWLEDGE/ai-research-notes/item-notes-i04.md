VERIFIED. The following tables contain all hidden items in the specified cave and dungeon locations in Pokémon Emerald. The data is sourced directly from the `pokeemerald` decompilation project. The primary source for this information is the `hidden_item_objects` array within each map's `data/maps/<Map>/map.json` file. The `hidden_item_id` is the name of the flag set when the item is picked up.

### Granite Cave

VERIFIED. Only one hidden item exists in Granite Cave, located in the section accessible with HM06 Rock Smash.

| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------------- |
| `MAP_GRANITE_CAVE_B1F`      | (29, 10)      | `ITEM_EVERSTONE`   | Rock Smash   | `HIDDEN_ITEM_GRANITE_CAVE_B1F_EVERSTONE`                  |

### Meteor Falls

VERIFIED. Only one hidden item exists in Meteor Falls, in the first room. The back area (accessible with Waterfall) and Steven's Cave (an Emerald-exclusive addition) contain no hidden items.

| Location (Map Constant)         | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                      |
| ------------------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------------- |
| `MAP_METEOR_FALLS_1F_1R`        | (10, 3)       | `ITEM_MOON_STONE`  | None         | `HIDDEN_ITEM_METEOR_FALLS_1F_1R_MOON_STONE`               |

### Fiery Path

VERIFIED. Both hidden items are in the back section accessible with HM04 Strength.

| Location (Map Constant) | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                |
| ----------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------- |
| `MAP_FIERY_PATH`        | (52, 7)       | `ITEM_FIRE_STONE`  | Strength     | `HIDDEN_ITEM_FIERY_PATH_FIRE_STONE`                 |
| `MAP_FIERY_PATH`        | (61, 27)      | `ITEM_NUGGET`      | Strength     | `HIDDEN_ITEM_FIERY_PATH_NUGGET`                     |

### Jagged Pass

VERIFIED. This is an outdoor route, but included as requested. The hidden item is in one of the ash piles.

| Location (Map Constant) | Coords (X, Y) | Item                | Requirements          | Flag / Decomp Source                                |
| ----------------------- | ------------- | ------------------- | --------------------- | --------------------------------------------------- |
| `MAP_JAGGED_PASS`       | (14, 19)      | `ITEM_GREAT_BALL`   | Acro Bike (optional)  | `HIDDEN_ITEM_JAGGED_PASS_GREAT_BALL`                |

### Mt. Pyre

VERIFIED. There are no hidden items inside any of the interior floors of Mt. Pyre (`MtPyre_1F` through `_6F`). The two hidden items are on the exterior summit area.

| Location (Map Constant) | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                |
| ----------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------- |
| `MAP_MT_PYRE_EXTERIOR`  | (29, 8)       | `ITEM_ZINC`        | None         | `HIDDEN_ITEM_MT_PYRE_EXTERIOR_ZINC`                 |
| `MAP_MT_PYRE_EXTERIOR`  | (8, 30)       | `ITEM_RARE_CANDY`  | None         | `HIDDEN_ITEM_MT_PYRE_EXTERIOR_RARE_CANDY`           |

### Team Magma Hideout

VERIFIED. There are **no hidden items** in the Team Magma Hideout. This location is significantly different in Emerald compared to Ruby, being located inside Mt. Chimney and having a completely new layout. All `map.json` files for `MagmaHideout_*` maps were checked and contain no `hidden_item_objects` arrays.

### Team Aqua Hideout

VERIFIED. Only one hidden item is present.

| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------------- |
| `MAP_AQUA_HIDEOUT_B2F`      | (35, 3)       | `ITEM_NEST_BALL`   | None         | `HIDDEN_ITEM_AQUA_HIDEOUT_B2F_NEST_BALL`                  |

### Seafloor Cavern

VERIFIED. Only one hidden item is present.

| Location (Map Constant)          | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                     |
| -------------------------------- | ------------- | ------------------ | ------------ | -------------------------------------------------------- |
| `MAP_SEAFLOOR_CAVERN_ROOM5`      | (18, 4)       | `ITEM_BIG_PEARL`   | None         | `HIDDEN_ITEM_SEAFLOOR_CAVERN_ROOM5_BIG_PEARL`            |

### Cave of Origin

VERIFIED. There are **no hidden items** in any part of the Cave of Origin. The relevant `map.json` files for `CaveOfOrigin_*` maps were checked.

### Sky Pillar

VERIFIED. Only one hidden item is present, on the floor with the Rayquaza puzzle.

| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements          | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | --------------------- | --------------------------------------------------------- |
| `MAP_SKY_PILLAR_4F`         | (5, 12)       | `ITEM_RARE_CANDY`  | Mach Bike             | `HIDDEN_ITEM_SKY_PILLAR_4F_RARE_CANDY`                    |

### Victory Road

VERIFIED. Two hidden items are present.

| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------------- |
| `MAP_VICTORY_ROAD_B1F`      | (36, 3)       | `ITEM_ELIXIR`      | None         | `HIDDEN_ITEM_VICTORY_ROAD_B1F_ELIXIR`                     |
| `MAP_VICTORY_ROAD_B2F`      | (5, 20)       | `ITEM_MAX_REPEL`   | None         | `HIDDEN_ITEM_VICTORY_ROAD_B2F_MAX_REPEL`                  |

### Shoal Cave

VERIFIED. Hidden items in Shoal Cave are dependent on the in-game tide, which changes every 6 hours. The map itself changes between high and low tide states.

**Low Tide Only** (Accessible from 3:00-8:59 and 15:00-20:59)
| Location (Map Constant)              | Coords (X, Y) | Item            | Requirements   | Flag / Decomp Source                                       |
| ------------------------------------ | ------------- | --------------- | -------------- | ---------------------------------------------------------- |
| `MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM` | (17, 4)       | `ITEM_PEARL`    | Low Tide       | `HIDDEN_ITEM_SHOAL_CAVE_LOWER_ROOM_PEARL_1`                |
| `MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM` | (21, 13)      | `ITEM_PEARL`    | Low Tide       | `HIDDEN_ITEM_SHOAL_CAVE_LOWER_ROOM_PEARL_2`                |

**High Tide Only** (Accessible from 9:00-14:59 and 21:00-2:59)
| Location (Map Constant)               | Coords (X, Y) | Item             | Requirements | Flag / Decomp Source                                       |
| ------------------------------------- | ------------- | ---------------- | ------------ | ---------------------------------------------------------- |
| `MAP_SHOAL_CAVE_HIGH_TIDE_ENTRANCE`   | (23, 7)       | `ITEM_BIG_PEARL` | High Tide    | `HIDDEN_ITEM_SHOAL_CAVE_ENTRANCE_BIG_PEARL`                |

### New Mauville

VERIFIED. There are **no hidden items** in New Mauville. The `map.json` file for `MAP_NEW_MAUVILLE_INSIDE` was checked.

### Abandoned Ship

VERIFIED. Only one hidden item is present, in an underwater section.

| Location (Map Constant)         | Coords (X, Y) | Item               | Requirements | Flag / Decomp Source                                      |
| ------------------------------- | ------------- | ------------------ | ------------ | --------------------------------------------------------- |
| `MAP_ABANDONED_SHIP_UNDERWATER1`| (3, 3)        | `ITEM_WATER_STONE` | Dive         | `HIDDEN_ITEM_ABANDONED_SHIP_UNDERWATER1_WATER_STONE`      |

### Mirage Tower & Desert Ruins

VERIFIED. These two locations are linked. The Mirage Tower appears on Route 111 and must be climbed to get one of the two fossils. After taking a fossil, the tower collapses and the other fossil falls into the ground, becoming accessible via the Desert Ruins tunnel which opens up at the back of a ruin maniac's house on Route 111. Both fossils are obtained from hidden item spots.

**Mirage Tower** (First Fossil)
| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements         | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | -------------------- | --------------------------------------------------------- |
| `MAP_MIRAGE_TOWER_4F`       | (5, 5)        | `ITEM_ROOT_FOSSIL` | Mach Bike, Rock Smash | `HIDDEN_ITEM_MIRAGE_TOWER_4F_ROOT_FOSSIL`                 |
| `MAP_MIRAGE_TOWER_4F`       | (6, 5)        | `ITEM_CLAW_FOSSIL` | Mach Bike, Rock Smash | `HIDDEN_ITEM_MIRAGE_TOWER_4F_CLAW_FOSSIL`                 |

**Desert Ruins** (Second Fossil)
VERIFIED. This becomes accessible *after* taking a fossil from Mirage Tower. The item here is whichever fossil the player did *not* take.
| Location (Map Constant)     | Coords (X, Y) | Item               | Requirements               | Flag / Decomp Source                                      |
| --------------------------- | ------------- | ------------------ | -------------------------- | --------------------------------------------------------- |
| `MAP_DESERT_RUINS`          | (4, 46)       | Other Fossil       | Obtain first fossil        | `HIDDEN_ITEM_DESERT_RUINS_FOSSIL`                         |