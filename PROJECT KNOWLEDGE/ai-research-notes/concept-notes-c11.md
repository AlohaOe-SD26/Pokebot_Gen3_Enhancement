## A. MECHANICS THE ROM ENFORCES

### Move Data & Execution
| Mechanic | Source / Implementation | Status |
| :--- | :--- | :--- |
| **Move Stats** | Array `gBattleMoves` (`src/data/battle_moves.h`). Uses `struct BattleMove` (`include/pokemon.h`). Fields: `effect`, `power`, `type`, `accuracy`, `pp`, `secondaryEffectChance`, `target`, `priority`, `flags`. | **VERIFIED** |
| **STAB** | `src/battle_script_commands.c` (`Cmd_calcmaxdamage`). If `gBattleMoves[move].type` == `gBaseStats[species].type1` or `type2`, damage is multiplied by 1.5. | **VERIFIED** |
| **Physical/Special Split** | Tied to Move Type, NOT the Move itself (Gen 1-3 mechanic). `include/constants/pokemon_types.h`. Types 0x00-0x08 (Normal to Steel) are Physical. Types 0x0A-0x11 (Fire to Dark) are Special. | **VERIFIED** |
| **Accuracy** | Ranges 1-100. 0 denotes "never misses" (e.g., Swift). | **VERIFIED** |

### Move Learning Methods
| Method | Mechanic / Constraint | Status |
| :--- | :--- | :--- |
| **Level-Up** | Defined in `src/data/pokemon/level_up_learnsets.h`. Stored as an array of 16-bit values per species: `(level << 9) \| moveId`. Max 4 moves known at once. Overwriting triggers a prompt if slots are full. | **VERIFIED** |
| **TMs (Single-Use)** | Items `ITEM_TM01` to `ITEM_TM50`. Consumed on use. `gBaseStats[species].tmHmLearnset1` and `tmHmLearnset2` (32-bit bitfields) determine compatibility. | **VERIFIED** |
| **HMs (Reusable)** | Items `ITEM_HM01` to `ITEM_HM08`. NOT consumed. Same bitfield compatibility check as TMs. Cannot be forgotten normally. | **VERIFIED** |
| **Story Tutors** | One-time NPC interactions. Emerald adds tutors missing from RS (e.g., Rollout in Mauville, Substitute in Lilycove). Controlled by save flags (e.g., `FLAG_TUTOR_ROLLOUT`). | **VERIFIED** |
| **Move Deleter** | Lilycove City (`data/maps/LilycoveCity_MoveDeletersHouse/scripts.inc`). The *only* way to forget an HM move (`IsMoveHm(move) == TRUE`). | **VERIFIED** |
| **Move Relearner** | Fallarbor Town. Costs 1 `ITEM_HEART_SCALE` per move. Reads the target's `LevelUpLearnset` array up to its *current level*. Egg moves are NOT strictly part of this list unless added by a specific event. | **VERIFIED** |

### Emerald Distinctions
*   **Emerald vs RS:** Emerald adds Move Tutors throughout Hoenn (RS had almost none). Emerald moves the Move Deleter/Relearner logic to centralized UI scripts.
*   **Emerald vs FRLG:** FRLG tracks hatched Egg moves and special event moves in a separate buffer so the Relearner can teach them. Emerald's Relearner strictly checks `gLevelUpLearnsets` (unless trading a FRLG mon over, but a bot won't do that). **VERIFIED**

---

## B. WHAT THE BOT CAN OBSERVE

All critical decision data can be read directly from memory.

| Entity | Location in Memory / Struct Field | Observability |
| :--- | :--- | :--- |
| **Party Moves Known** | `gPlayerParty` array (`struct Pokemon`). Read via `GetMonData(mon, MON_DATA_MOVE1)` through `MON_DATA_MOVE4`. | Read direct |
| **Current PP** | `gPlayerParty` array. Read via `MON_DATA_PP1` through `MON_DATA_PP4`. | Read direct |
| **Move Stats** | Read from `gBattleMoves[move_id]`. Extract `power` (base damage), `accuracy`, `type` (for STAB/Physical/Special calc), `pp`. | Read ROM struct |
| **TM Inventory** | `gSaveBlock1Ptr->bagPocket_TMHM`. Iterating this array reveals which TMs the bot possesses. | Read direct |
| **TM Compatibility** | `gBaseStats[species].tmHmLearnset1` & `tmHmLearnset2`. Match TM item ID to specific bit using `CanSpeciesLearnTMHM()` logic (`src/pokemon_summary_screen.c`). | Read ROM struct |
| **Heart Scale Count** | `gSaveBlock1Ptr->bagPocket_Items`. Search for `ITEM_HEART_SCALE` and read quantity. | Read direct |
| **Tutor Flags** | `gSaveBlock1Ptr->flags`. Specific flags (e.g., `FLAG_TUTOR_SWAGGER` = 0x0C2) indicate if a tutor has been exhausted. | Read direct |

---

## C. OPTION SPACE

How a bot should score and manage its team's moveset over a full story run.

### Option 1: Static Route / Hardcoded Learnsets (The Speedrunner)
Pre-calculate every move a Pokémon should learn at exactly what level, and exactly who gets which TM.
*   **Cost:** Zero runtime computation. Massive setup cost for the developer. Brittle if RNG causes different encounters/levels.
*   **Failure Mode:** If the designated Pokémon faints and misses XP, it won't be high enough level to learn the required move before a boss.
*   **Detection:** Bot compares current `gPlayerParty` moves to the hardcoded step in the state machine; halts if mismatch occurs.

### Option 2: The "Sweeper Heuristic" (Sustained Damage Math)
The bot autonomously scores potential new moves (Level-up or TMs) against known moves using a formula: `Score = (Power * STAB_Multiplier * (Accuracy/100)) * Total_PP`.
*   **Cost:** Low computation. Bot dynamically accepts/rejects level-up moves and aggressively applies TMs to the highest scorer.
*   **Failure Mode:** Rejects high-power/low-PP moves (like Fire Blast or Overheat) because the total damage yield is lower than Flamethrower, potentially missing OHKO thresholds on bosses. Ignores status moves entirely.
*   **Detection:** Bot gets stuck in a battle loop against a boss because its DPS isn't high enough to break through healing (e.g., Wallace's Milotic).

### Option 3: Role-Based Slotting
Bot enforces a moveset structure on its primary combatants: Slot 1: Primary STAB, Slot 2: Coverage/Secondary STAB, Slot 3: HM / Utility, Slot 4: Setup (e.g., Bulk Up).
*   **Cost:** Moderate computation. Bot must read `gBattleMoves` types and effects. Status moves are scored by `effect` (e.g., `EFFECT_ATTACK_UP_2`).
*   **Failure Mode:** Bot might overwrite a perfectly good coverage move with an HM because the coverage move was in "Slot 3".
*   **Detection:** Bot attempts an invalid TM application, or struggles in type-disadvantaged fights because it dropped coverage for a Setup move it doesn't know how to use well.

### Recommended Early-Game Priority Moves (Bot Targets)
*   **Bulk Up (TM08):** Brawly gym reward. High priority for physical attackers (Combusken, Mudkip).
*   **Secret Power (TM43):** Route 111 NPC. 70 BP, 100 Acc, Physical. Excellent neutral sweeping move.
*   **Return (TM27):** Fallarbor/Pacifidlog. Bot must check `MON_DATA_FRIENDSHIP` to score this accurately. (Power = Friendship / 2.5). Max 102 BP.

---

## D. TRAPS

The most dangerous mechanical states for an autonomous player.

| Trap / Danger | Description | Consequence |
| :--- | :--- | :--- |
| **Single-Use TMs** | TMs 1-50 are single-use. If the bot blindly applies TM26 (Earthquake) to a Geodude it plans to box, the most powerful Ground move in the game is permanently lost. | Irreversible loss of offensive capability. |
| **HM Overwrite Lock** | HMs (Surf, Strength, etc.) *cannot be overwritten* by Level-Up moves or TMs. If the bot applies 4 HMs to its starter, it is locked into that moveset until reaching Lilycove City (Badge 6). | Severe combat degradation; potential softlock if boss cannot be beaten with HM stats. |
| **The "Stranding" Softlock** | The Move Deleter `src/party_menu.c` actively checks if deleting Surf/Dive will strand the player. `IsMonValidForMoveDeleter` will return `FALSE` if it's the last Pokémon with Surf and the player is on an island. If the bot tries to brute-force this, it will loop in the UI. | Infinite UI loop / wedge. |
| **Heart Scale Exhaustion** | Heart Scales are finite as map items. Once exhausted, they can only be farmed from wild Luvdisc (Requires Super Rod, 50% encounter, 50% hold rate, requires Thief/Covet). | Bot permanently loses the ability to Relearn moves if farming isn't coded. |
| **Hidden Power Trap** | TM10 (Hidden Power) reads as 0 BP / Normal Type in `gBattleMoves`. The true power/type is derived from IVs. A bot reading raw structs will score it as useless (0) or use it expecting Normal STAB. | Suboptimal move selection. Bot must parse `MON_DATA_HP_IV` through `SPDEF_IV` to calculate it. |
| **Evolution Move Missing** | Certain moves are only learned at the exact level of evolution (e.g., Breloom learns Mach Punch at Level 23). If the bot cancels evolution (B button loop bug) or faints and skips the level, the move is missed and requires a Heart Scale. | Resource drain; delayed power spike. |
| **Status Move PP Stall** | If the bot evaluates moves purely on BP and drops all PP, it will spam Struggle. If it keeps status moves (Growl) but uses them randomly, it will waste turns against bosses, taking free damage. | Battle failure. Bots must have specific heuristics to *not* use status moves on low-threat targets. |