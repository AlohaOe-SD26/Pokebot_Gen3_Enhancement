## A. MECHANICS THE ROM ENFORCES

### 1. Step Encounter Formula & Modifiers
Wild encounters are rolled upon entering a new valid tile (Grass, Water, Cave). They are *not* pre-seeded per map; they are rolled on the exact frame the step transition completes.

| Claim | Detail | Status | Source/Struct |
| :--- | :--- | :--- | :--- |
| **Base Formula** | `roll = Random() % 2880; if (roll < (encounterRate * 16))` encounter triggers. | **VERIFIED** | `src/wild_encounter.c` -> `StandardWildEncounter` |
| **Map Rates** | `encounterRate` is defined per map (e.g., usually 21 for grass, 10 for caves, 4 for water). | **VERIFIED** | `include/constants/map_groups.h`, `src/data/wild_encounters.h` |
| **Running** | Running shoes multiply the encounter threshold by 1.6 (`(rate * 160) / 100`). | **VERIFIED** | `src/wild_encounter.c` |
| **Biking** | Biking multiplies the encounter threshold by 0.8 (`(rate * 80) / 100`). | **VERIFIED** | `src/wild_encounter.c` |
| **Acro Bike Hops** | Holding B to bunny-hop in tall grass counts as a step and rolls for an encounter. | **VERIFIED** | `src/bike.c` / `src/wild_encounter.c` |

### 2. Slot Probability Tables
Once an encounter is triggered, a second `Random() % 100` determines the species/level slot.

| Table Type | Array Name | Slot Probabilities (%) | Status |
| :--- | :--- | :--- | :--- |
| **Land / Cave** | `land_mons` | 20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1 | **VERIFIED** |
| **Water (Surf)** | `water_mons` | 60, 30, 5, 4, 1 | **VERIFIED** |
| **Rock Smash** | `rock_smash_mons`| 60, 30, 5, 4, 1 | **VERIFIED** |
| **Old Rod** | `fishing_mons` | 70, 30 | **VERIFIED** |
| **Good Rod** | `fishing_mons` | 60, 20, 20 | **VERIFIED** |
| **Super Rod** | `fishing_mons` | 40, 40, 15, 4, 1 | **VERIFIED** |

*(Note: `src/data/wild_encounters.h` contains `struct WildPokemonHeader` for every map).*

### 3. Repel & The "Gen 3 Repel Quirk"
If `gSaveBlock1Ptr->repelCounter > 0`, the ROM compares the lead Pokémon's level to the rolled wild Pokémon's level.
*   **The Quirk:** The encounter slot is rolled *before* the Repel check. If the wild Pokémon's level is lower than the lead Pokémon's level, the encounter is suppressed **and is not rerolled**. (**VERIFIED**)
*   *Consequence:* Using a Repel does not force the game to hunt for a higher-level slot. It simply makes steps that rolled lower-level slots yield nothing. Encounter rates plummet drastically if you use a Repel to target a rare, high-level 1% slot.

### 4. Overworld Abilities (Emerald Exclusive)
*Crucial difference from RS/FRLG:* Pokémon Emerald introduced overworld effects for abilities. These apply even if the lead Pokémon is **fainted**. (**VERIFIED** - `src/wild_encounter.c` -> `GetAbilityBySpecies`)

| Ability | Mechanical Effect enforced by ROM | Status |
| :--- | :--- | :--- |
| **Illuminate / Swarm** | Multiplies encounter base rate threshold by 2. | **VERIFIED** |
| **Stench / White Smoke**| Divides encounter base rate threshold by 2. | **VERIFIED** |
| **Intimidate / Keen Eye**| 50% chance to suppress the encounter *if* the wild level is `<= lead_level - 5`. | **VERIFIED** |
| **Static** | 50% chance to force an Electric-type encounter (if one exists on the map). Alters the slot RNG. | **VERIFIED** |
| **Magnet Pull** | 50% chance to force a Steel-type encounter. | **VERIFIED** |
| **Synchronize** | 50% chance to force the wild Pokémon to have the lead's Nature. | **VERIFIED** |
| **Hustle / Vital Spirit**| 50% chance to force the highest-level range of the selected slot. | **RECALL** |
| **Sticky Hold / Suction**| Increases the probability of a bite while fishing. | **VERIFIED** |

### 5. Swarms & Feebas
*   **Outbreaks/Swarms:** Handled via `gSaveBlock1Ptr->outbreakPokemonSpecies`. When active, slots 0 and 1 (totaling 40% or 50% depending on map) are temporarily overwritten by the swarm species. (**VERIFIED**)
*   **Feebas Tiles:** Route 119 has exactly 6 tiles where fishing yields 50% Feebas. The RNG seed for these tiles is generated using `gSaveBlock1Ptr->dewfordTrends[0].rand`. It does not change until the Dewford trend changes (which happens automatically via the RTC/step counter). (**VERIFIED** - `src/wild_encounter.c` -> `IsFeebasMarkedTile`)

---

## B. WHAT THE BOT CAN OBSERVE

To automate encounters optimally without relying on screen reading, the bot should read these memory locations directly:

| Mechanic | Observable Struct/Field | Access |
| :--- | :--- | :--- |
| **Repel State** | `gSaveBlock1Ptr->repelCounter` | Read/Write (UInt8) |
| **Map Encounter Data**| `gMapHeader.wildPokemon` pointer | Read-only |
| **Lead Pokémon** | `gPlayerParty[0]` | Read (Check `hp` for fainted state, `species` for ability mapping, `level` for Repel checks). |
| **Feebas Tiles Seed** | `gSaveBlock1Ptr->dewfordTrends[0].rand` | Read (Calculate the 6 tiles exactly as `IsFeebasMarkedTile` does). |
| **Imminent Encounter**| `gMain.callback1` or `gMain.callback2` | Read. When a wild encounter is triggered, `gMain.callback2` is set to `BattleSetup_StartWildBattle`. This happens *before* the fade animation, giving the bot advance notice. |
| **Sweet Scent Menu** | `gFieldTasks` | Read. Bot can detect if a task like `Task_SweetScent` is queued. |

---

## C. OPTION SPACE (Maximising Encounters-per-Frame)

To grind wild encounters as fast as possible, the bot can use several movement/action paradigms.

### Option 1: Sweet Scent Spam
*   **Mechanic:** Force a wild encounter instantly without moving by using Sweet Scent in the overworld.
*   **Cost:** Requires a Pokémon with Sweet Scent. Consumes 1 PP per use. Requires menuing.
*   **Speed:** Very fast. Bypasses the 2880 RNG roll entirely.
*   **Detection of Failure:** Read `gPlayerParty[0..5].pp[x]`. If 0, the menu selection will fail. Bot detects failure if `gMain.callback2` does not change to `BattleSetup_StartWildBattle` within ~60 frames of confirming the move.

### Option 2: Acro Bike Bunny Hopping
*   **Mechanic:** Equip the Acro Bike. Hold B (to hop continuously) while standing in a valid tall grass tile.
*   **Cost:** None. Requires Acro Bike.
*   **Speed:** Moderate. Each hop counts as a step and rolls `Random() % 2880`. No need to handle map boundaries or turn animations.
*   **Detection of Failure:** If the bot hops 500 times without `gMain.callback2` changing to battle setup, it is not on a valid encounter tile or a Repel is active.

### Option 3: Memory Forcing (Emulator specific)
*   **Mechanic:** Overwrite `gNextTrickHouseStep` or simply hook into `StandardWildEncounter` via memory manipulation to force `roll < chance`. Write `1` to force the branch, walk 1 step.
*   **Cost:** Destroys "legitimacy" of the bot's runtime behavior, turning it into a TAS/memory-hacker rather than an autonomous player.
*   **Speed:** Instant. 1 step = 1 encounter.
*   **Detection of Failure:** Fails only if on an invalid tile.

### Option 4: Scent-Cheat Trigger
*   **Mechanic:** Instead of opening the menu, the bot writes the callback pointer `SweetScentWildEncounter` directly into `gFieldTasks` or triggers `Script_SweetScent` execution.
*   **Cost:** Memory write. Bypasses PP consumption.
*   **Speed:** Maximum possible frame efficiency for an "organic" encounter generation.

---

## D. TRAPS (Permanent Loss, Softlocks, & Exhaustion)

Because your bot repeats loops thousands of times, these constraints will wedge it if unhandled:

| Trap | Failure Mode | Avoidance / Bot Logic |
| :--- | :--- | :--- |
| **Repel Deadlock** | Bot grinds levels. Lead Pokémon exceeds the highest level slot on the route. Bot activates Repel. Encounter rate becomes exactly 0%. Bot walks forever. | Bot must read `wildPokemon` max level from map data. If `gPlayerParty[0].level > max_wild_level`, do **not** use Repel. |
| **Synchronize Faint-Lock** | Bot uses a fainted Ralts with Synchronize as a lead to force a Nature. Encounter begins. Bot forgets it cannot swap to the fainted Ralts, uses its second slot Pokémon. If the second slot dies, the bot wipes. | Bot must evaluate combat viability starting at index `1` if index `0` has `hp == 0`. |
| **Feebas Desync** | Bot calculates the 6 Feebas tiles. Bot walks/fishes for hours. The step counter rolls over the RTC threshold, advancing Dewford Trend. The 6 tiles change. Bot fishes empty tiles forever. | Bot must cache `gSaveBlock1Ptr->dewfordTrends[0].rand`. If it changes, recalculate tiles immediately. |
| **Sweet Scent Softlock** | Bot attempts to menu -> Pokémon -> Sweet Scent, but PP is 0. The bot is stuck in the menu or constantly re-opening it. | Pre-flight check: read PP before opening menu. If PP=0, bot must route to a Pokémon Center (`HealPlayerParty`). |
| **Roaming Latias/Latios Wipe** | Bot is hunting in grass. The Roaming Lati is randomly assigned to the bot's current map. Bot encounters Lati. Bot executes "Run" command. Running from a roamer causes it to flee, saving its status as fled, losing the roaming legendary permanently. | Read `gBattleTypeFlags`. If `BATTLE_TYPE_ROAMER` is set, switch to Master Ball / Capture logic. Do **not** run. |
| **Safari Zone Step Limit** | Bot attempts standard encounter loops in the Safari Zone. Hits 500 steps. Is forcibly teleported out. Bot attempts to continue movement sequence in Lilycove City, walking into a wall forever. | Hook `gMapHeader.mapType`. If `MAP_TYPE_ROUTING` changes unexpectedly, abort current macro and execute localization check. |
| **Fishing Timing Drift** | Bot casts rod. "Oh! A bite!" text appears. Bot must press A within a specific frame window. The window is shorter for Good/Super rods. If the bot is out of sync by 1 frame, the fish gets away. | Read `gSpecialVar_Result`. Hook the exact frame the fishing state transitions to `FISHING_BITE` to send the 'A' input. Do not rely on visual delays. |