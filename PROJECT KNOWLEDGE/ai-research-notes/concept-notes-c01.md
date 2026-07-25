## A. MECHANICS THE ROM ENFORCES

**PC and Party Capacity**
| Mechanic | Rule / Threshold | Status | Source / Struct |
| :--- | :--- | :--- | :--- |
| **Max Party Size** | 6 slots. Caught Pokémon go here first. | **VERIFIED** | `PARTY_SIZE` in `include/constants/pokemon.h` |
| **Box Count** | 14 boxes in Emerald (and RS/FRLG). | **VERIFIED** | `TOTAL_BOXES_COUNT` |
| **Box Capacity** | 30 slots per box. Max PC capacity = 420. | **VERIFIED** | `IN_BOX_COUNT` |
| **Auto-Deposit Routing** | If Party is full, caught Pokémon goes to `currentBox`. If `currentBox` is full, it wraps to the next sequential box (e.g., 13 -> 0). | **VERIFIED** | `SendMonToPC()` in `src/pokemon.c` |

**Data Formats: Party vs. Box**
| Format | Size | Details | Status | Source |
| :--- | :--- | :--- | :--- | :--- |
| `struct BoxPokemon` | 80 bytes | Contains only core identity, encrypted stat blocks (Growth, Attacks, EVs, Misc), and checksum. No current HP/Status. | **VERIFIED** | `include/pokemon.h` |
| `struct Pokemon` | 100 bytes | The Party format. Contains `struct BoxPokemon` (80b) + `struct PokemonSubstruct` (20b) for volatile battle stats (HP, Level, Status, Mail). | **VERIFIED** | `include/pokemon.h` |

**The Storage Encryption System (Anti-Tampering)**
The ROM compresses and encrypts Pokémon data in the PC to save space and prevent simple memory editing.
*   **Decryption Key:** `personality XOR otId`. (**VERIFIED**)
*   **Permutation:** `personality % 24` determines the order of the 4 data substructures (Growth, Attacks, EVs, Misc) in the 48-byte `secure` array. (**VERIFIED**)
*   **Checksum:** The sum of all unencrypted 16-bit words in the `secure` array must equal the `checksum` field. (**VERIFIED**)
*   **Empty Slot Definition:** A PC slot is considered empty if its decrypted `species` is `SPECIES_NONE` (0). (**VERIFIED** - `GetBoxMonData` handles this).

**Limits and Releasing**
| Action | ROM Enforcement | Status | Source / Logic |
| :--- | :--- | :--- | :--- |
| **All Boxes Full** | If Party=6 and PC=420, throwing a Poké Ball is **prohibited**. The item is not consumed. Text: *"The BOX is full! You can't catch any more!"* | **VERIFIED** | `ItemUseCB_PokeBall` / `battle_util.c` |
| **Release Minimum** | You cannot release a Pokémon if it leaves your Party with 0 conscious Pokémon. | **VERIFIED** | `CanReleaseMon()` in `src/pokemon_storage_system.c` |
| **Egg Releasing** | Eggs and Bad Eggs cannot be released via the PC UI. | **VERIFIED** | `src/pokemon_storage_system.c` |
| **HM Slave Releasing** | Emerald does *not* prevent releasing the last Pokémon that knows a necessary HM (unlike Gen 4+). | **RECALL** | Lack of HM block in `CanReleaseMon()` |

---

## B. WHAT THE BOT CAN OBSERVE

All storage state is directly observable via memory reads, provided the bot implements the ROM's decryption logic.

| State to Observe | Memory Location / Pointer | Implementation Notes |
| :--- | :--- | :--- |
| **Current Party** | `gPlayerParty` | Array of 6 `struct Pokemon` (100 bytes each). Iterate and check `species != SPECIES_NONE` to count active party size. |
| **Active PC Box** | `gPokemonStoragePtr->currentBox` | 1 byte (0-13). Defines where the next catch goes. |
| **Entire PC Contents** | `gPokemonStoragePtr->boxes[14][30]` | 2D array of `struct BoxPokemon`. |
| **Is Box Slot Empty?** | Bot must read `personality` and `otId`, calculate the decryption key, unscramble the 4 blocks based on `personality % 24`, and read `species` from the Growth block. If `0`, it is empty. | Alternatively, checking if the entire 80-byte block is exactly `0x00` is a 99% reliable heuristic for an empty slot without decrypting. |
| **Pre-Catch Safety Check** | Count valid structs in `gPlayerParty`. If 6, iterate `gPokemonStoragePtr->boxes`. If ALL 420 slots have non-zero encrypted data, abort catch attempts. | Cannot rely purely on RAM flags; must iterate the structs. |

---

## C. OPTION SPACE

How the bot manages PC limits and captures.

### Option 1: Proactive PC Clearing (UI Automation)
The bot tracks PC capacity via memory. When capacity exceeds ~90%, it routes to a Pokémon Center, opens the PC, and navigates the UI to release low-value Pokémon.
*   **Cost:** High execution time. Box UI automation is complex (grid navigation, multi-state menus, lag frames in UI transitions).
*   **Failure Mode:** Misaligning menu inputs releases the wrong Pokémon (e.g., the team carry).
*   **Detection:** Post-release memory diff on `gPokemonStoragePtr` shows the intended slot is not empty, or the carry's `personality` vanished.

### Option 2: Run-to-Failure (Menu-Trap Handling)
The bot ignores PC capacity until it tries to throw a ball and fails.
*   **Cost:** Low coding overhead, but wastes battle turns.
*   **Failure Mode:** If the bot doesn't read the *"The BOX is full!"* battle message (or infer it via the ball item quantity not decreasing), it will mash 'A' to throw balls infinitely, softlocking the bot in a battle menu loop.
*   **Detection:** The bot reads `gBattleResults.pokeballThrows` or its inventory count. If it issued a throw command but the ball count did not decrement, the PC is full.

### Option 3: Direct Memory Management (The "God" Hand)
The bot bypasses the PC UI and directly writes zeroes to `gPokemonStoragePtr->boxes[x][y]` to release Pokémon instantly anywhere in the world.
*   **Cost:** Extremely low execution time. Technically cheating.
*   **Failure Mode:** If the bot modifies a Pokémon's stats (e.g., EV training via memory) but fails to recalculate the 16-bit checksum and re-encrypt, the game silently flags it as a **Bad Egg**.
*   **Detection:** The bitfield in `struct BoxPokemon` (bit 0) gets set to `isBadEgg = 1` upon the game's next internal validation pass.

---

## D. TRAPS

Irreversible actions and softlocks specific to storage automation.

| Trap | Severity | Trigger / Description |
| :--- | :--- | :--- |
| **The Full-Box Battle Softlock** | **FATAL** | If the PC is full, tossing a Poké Ball fails, returns the player to the item menu, and *does not consume the turn or the ball*. A bot hardcoded to "throw ball until caught or dead" will loop this menu indefinitely. |
| **Bad Egg Contagion** | **FATAL** | If the bot injects/modifies PC memory without properly hashing the checksum, it creates a Bad Egg. Bad Eggs **cannot be released** via UI. Furthermore, due to a Gen 3 bug, placing a Bad Egg in the PC can occasionally corrupt adjacent slots, permanently destroying box capacity. |
| **HM Stranding** | **FATAL** | Emerald allows releasing HM slaves from the PC. If the bot navigates the UI to release boxed Pokémon and accidentally releases the only Pokémon with Surf/Dive while saved on an island (e.g., Sootopolis, Mossdeep), the bot is permanently softlocked. |
| **Releasing the Active Carry** | **HIGH** | The game only prevents releasing your *last* conscious Pokémon. If the bot has 2 conscious Pokémon, it can release its Lv. 80 Swampert and keep a Lv. 3 Zigzagoon. The bot must verify `personality` matches a blacklist before confirming a UI release. |
| **Box 14 Save De-sync** | **MEDIUM** | In Gen 3, PC Box data is staggered across save sectors. If the bot relies solely on `gPokemonStoragePtr` for state but the emulator resets before a formal save, the bot's internal world-model of what it released/caught will de-sync from the ROM's battery save. Always read from RAM dynamically, do not cache PC state externally. |