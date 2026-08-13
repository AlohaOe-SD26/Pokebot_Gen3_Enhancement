## A. MECHANICS THE ROM ENFORCES

**1. Early Roster Availability (Route 101 to Granite Cave - Pre-Badge 2)**
Encounter data is defined in `src/data/wild_encounters.json`.

| Species | Primary Type | Secondary | Location | Encounter Rate | Viability / Dead-End |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lotad** | Water | Grass | Route 102 | 20% (Lv 3-4) | **High:** Unique typing, evolves via Water Stone. (RS Diff: Ruby has Seedot). |
| **Ralts** | Psychic | None | Route 102 | 4% (Lv 4) | **Med:** High power, but 4% find rate costs bot time. |
| **Taillow** | Normal | Flying | Route 104 | 20% (Lv 4-5) | **High:** Fast, high attack. Outclasses Pidgey (FRLG). |
| **Shroomish** | Grass | None | Petalburg Woods | 15% (Lv 5-6) | **High:** Evolves to Breloom (Grass/Fighting) at Lv 23. |
| **Slakoth** | Normal | None | Petalburg Woods | 5% (Lv 5-6) | **Dead-End (Bot):** `ABILITY_TRUANT` skips every other turn. Bots struggle to evaluate this properly. |
| **Nincada** | Bug | Ground | Route 116 | 20% (Lv 6-8) | **High/Special:** Yields Ninjask + Shedinja at Lv 20. |
| **Makuhita** | Fighting | None | Granite Cave 1F | 50% (Lv 6-10)| **High:** Bulky fighting type, highly common. |
| **Geodude** | Rock | Ground | Granite Cave B1F | 10% (Lv 6-7) | **Med:** Good for early gyms, falls off late without trade evo. |
| **Abra** | Psychic | None | Granite Cave B1F | 10% (Lv 7-8) | **Dead-End (Bot):** Knows only Teleport. Fails to trade-evolve. |
| **Sableye** | Dark | Ghost | Granite Cave B2F | 10% (Lv 9-10)| **Med:** No weaknesses in Gen 3, but low base stats. |

**2. Obedience Caps (VERIFIED)**
*   **The Rule:** Badge-based obedience caps (e.g., "Pokémon up to L30 will obey") **ONLY apply to Pokémon with a mismatched Original Trainer (OT) ID or Secret ID**.
*   **Self-Caught:** Any Pokémon the bot catches itself will obey 100% of the time, even if it is Level 100 with zero badges.
*   **Code:** `IsMonDisobedient` in `src/battle_main.c`. It checks `GetMonData(mon, MON_DATA_OT_ID)` against `gSaveBlock2Ptr->playerTrainerId`.

**3. Storage & Party Limits (VERIFIED)**
*   **Party:** Maximum 6. Managed in `gPlayerParty` (array of `struct Pokemon`, 100 bytes each). Size tracked by `gPlayerPartyCount`.
*   **PC Storage:** 14 Boxes × 30 slots = 420 maximum. Managed via `gPokemonStoragePtr` (array of `struct BoxPokemon`, 80 bytes each).
*   **Catch Routing:** When catching a Pokémon with a full party, it is auto-sent to the lowest-indexed empty slot in the currently active PC box, then subsequent boxes.

**4. Experience (EXP) Mechanics (VERIFIED)**
*   **Formula:** `(BaseExpYield * EnemyLevel) / 7`. Lookups are in `gBaseStats[species].expYield` (`src/data/pokemon/base_stats.h`).
*   **Splitting:** EXP is divided evenly among all non-fainted party members that participated in the battle (`numBattlers`).
*   **Exp. Share (`ITEM_EXP_SHARE`):** Intercepts 50% of the total EXP *before* battler distribution. The 50% is divided evenly among all Exp. Share holders. The remaining 50% is divided among `numBattlers`.

## B. WHAT THE BOT CAN OBSERVE

| State / Data | Memory Location / Function | Bot Observability |
| :--- | :--- | :--- |
| **Party Contents** | `gPlayerParty[0` to `5]` | **Direct Read:** Parse `struct Pokemon` using `GetMonData`. |
| **Party Size** | `gPlayerPartyCount` (1 byte) | **Direct Read:** 1 to 6. |
| **Active PC Box** | `gSaveBlock1Ptr->pcItems` or `gPokemonStoragePtr->currentBox` | **Direct Read:** Tracks where new catches go. |
| **Box Fullness** | `gPokemonStoragePtr->boxes[i].mons[j]` | **Direct Read:** Check `GetBoxMonData(..., MON_DATA_SANITY_HAS_SPECIES)` to count empty slots. |
| **Wild Encounters** | `gEnemyParty[0]` | **Direct Read:** Instantly known upon battle start. Can read `MON_DATA_SPECIES` to decide whether to throw ball or flee/kill. |
| **EXP to Next Level** | `gPlayerParty[i]` | **Direct Read:** Read `MON_DATA_EXP`. Calculate threshold using `gExperienceTables[growthRate][level + 1]`. |

## C. OPTION SPACE

### Strategy 1: The "Elite Two" (Overleveling)
Rely on Starter + 1 coverage mon (e.g., Mudkip + Taillow), completely ignoring a diverse bench.
*   **Mechanical Cost:** Low. Bot spends no time catching, heals fewer targets, routes are faster. EXP formula heavily rewards concentrating EXP (Lv 30 Mudkip sweeps faster than 6 Lv 15s).
*   **Failure Mode:** Hard counter types (e.g., Grovyle vs Flannery) causing infinite white-out loops.
*   **Detection:** Bot observes `gPlayerPartyCount <= 2` and a localized white-out counter exceeding threshold on a specific Gym Leader.

### Strategy 2: Modular Swapping (Catch & Bench)
Catch 10+ viable species early. Before a gym, query `gBaseStats[species].type1/2` vs Gym type, pull from PC, and grind wild encounters.
*   **Mechanical Cost:** Extremely high. Requires complex PC navigation scripts, dynamic target-level calculation, and thousands of wild battles.
*   **Failure Mode:** EXP starvation. Attempting to keep 6 diverse Pokémon at the level curve via wild battles in Gen 3 is mathematically miserable (EXP yields from wild mons are low).
*   **Detection:** Bot observes `gPlayerParty[i].level` is statically >5 levels below `gEnemyParty[x].level` during trainer battles, but wild grinding takes >2 hours per level.

### Strategy 3: Passive Daycare Benching
Catch diverse mons, dump two into Route 117 Daycare (`gSaveBlock1Ptr->daycare`), and farm steps on the Mach Bike.
*   **Mechanical Cost:** 1 EXP per step. Costs ¥100 + (¥100 × levels gained) to retrieve.
*   **Failure Mode:** Run out of money, trapping mons in Daycare. Movesets are automatically overwritten (new learned moves push old moves up and delete slot 1).
*   **Detection:** Bot reads `gSaveBlock1Ptr->money` and sees it is `< 100`, making retrieval impossible.

## D. TRAPS (Exhaustive)

**1. The Shedinja Softlock (VERIFIED)**
*   **Mechanic:** Nincada evolves into Ninjask at Lv 20. If `gPlayerPartyCount < 6` AND the bag contains a standard `ITEM_POKE_BALL`, Shedinja is added to the party.
*   **Trap:** If the bot tries to generate Shedinja but exclusively bought Great Balls, the Shedinja spawn silently fails. The chance to get it from that Nincada is permanently lost.

**2. Evolution Cancellation via Input Mashing (VERIFIED)**
*   **Mechanic:** During `CB2_Evolution`, pressing the `B_BUTTON` sets the evolution state to cancel.
*   **Trap:** A bot holding B to skip text or run will continuously cancel its own evolutions forever, capping its stats.
*   **Fix:** Bot must observe `gMain.callback2 == CB2_Evolution` and forcibly release the B button.

**3. Move Overwrite Blindness (VERIFIED)**
*   **Mechanic:** Daycare auto-learns moves. Wild grinding auto-prompts to learn moves.
*   **Trap:** If the bot doesn't understand the power/accuracy of moves, it might overwrite a 90 BP STAB move with a non-damaging move (e.g., Overwriting Surf with Tail Whip). A bot with 4 non-damaging moves will struggle-spam to death.
*   **Fix:** Must hardcode a move-priority tier list or read `gBattleMoves[move].power`.

**4. The PC Box 420 Overflow (VERIFIED)**
*   **Mechanic:** If all 14 boxes are full, throwing a Poké Ball fails with a message: "The PC BOX is full."
*   **Trap:** If the bot has an unconstrained "throw ball at new species" logic, or gets stuck in a loop catching duplicate wild mons, it will fill the 420 slots. It is then permanently locked out of catching Rayquaza or story-mandated captures unless it can navigate the PC Release menu (which is incredibly high-risk for an automated bot).

**5. Slaking / Truant Loop (VERIFIED)**
*   **Mechanic:** `ABILITY_TRUANT` forces the `turn skipped` flag every alternating turn.
*   **Trap:** If the bot attempts to heal Slakoth on its "active" turn, then attacks on its "loafing" turn, it will permanently deal 0 damage and eventually wipe. Bot must read `gBattleMons[battler].ability` and track turn parity.

**6. HM Slave Erasure (RECALL / HIGH CONFIDENCE)**
*   **Mechanic:** HMs (Surf, Dive, Strength) cannot be overwritten via leveling up or standard TMs; they require the Move Deleter in Lilycove.
*   **Trap:** If the bot puts an HM slave in the Daycare, the Daycare **CAN** overwrite HMs because the Daycare bypasses the HM-lock check. If the bot loses Surf while on an island, and has no other Surfers or means to catch one, it is permanently softlocked.