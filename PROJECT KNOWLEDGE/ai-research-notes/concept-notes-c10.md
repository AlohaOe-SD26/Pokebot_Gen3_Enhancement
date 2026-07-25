## A. MECHANICS THE ROM ENFORCES

| Mechanic | Implementation / Location | Verification |
| :--- | :--- | :--- |
| **Whiteout Money Loss** | Calculates payout based on highest level Pokémon in party and a badge-dependent multiplier (unlike Ruby/Sapphire, which strictly halved money). Formula caps at current money. `src/money.c` (`GetWhiteoutMoneyPenalty`). | **VERIFIED** |
| **Whiteout Friendship Drop** | Fainted Pokémon lose 1 friendship point. If the opponent was $\ge$ 30 levels higher, they lose 5 points (for `friendship < 200`) or 10 points (for `friendship < 100`). `src/pokemon.c` (`AdjustFriendship`, `FRIENDSHIP_EVENT_FAINT_...`). | **VERIFIED** |
| **Respawn Location** | The player is warped to `gSaveBlock1Ptr->lastHealLocation`. Set by healing at a Pokémon Center or Mom. `src/overworld.c` (`CB2_WhiteOut`). | **VERIFIED** |
| **Boss Defeat Flags** | Trainer battle scripts check and set a specific `TRAINER_X` flag (`FLAG_DEFEATED_...`). If a whiteout occurs, the script terminates before the `trainerbattle` command can set this flag. `src/battle_setup.c`. | **VERIFIED** |
| **Map Re-entry: NPCs** | `gObjectEvents` structs are rebuilt from `events.inc` defaults upon map load. Any positional changes made during a map visit reset unless a map script (`ON_TRANSITION` or `ON_RESUME`) explicitly moves them based on a `VAR` or `FLAG`. | **VERIFIED** |
| **Map Re-entry: Puzzles** | Gym puzzles (e.g., Sootopolis Ice, Mossdeep arrows) reset completely on map reload. Handled by `ON_TRANSITION` scripts resetting specific `VAR`s. `data/maps/SootopolisCity_Gym_1F/scripts.inc`. | **VERIFIED** |
| **Stationary Legendaries** | Defeating Rayquaza, Groudon, or Kyogre sets their `FLAG_DEFEATED_...`. Fleeing does *not* set the flag, but hides the sprite until the map is reloaded or Elite Four is beaten. `data/maps/SkyPillar_Top/scripts.inc`. | **VERIFIED** |
| **Roamer Persistence** | Latias/Latios retain HP and status conditions across encounters. `gSaveBlock1Ptr->roamer`. If they faint, they are permanently flagged as dead. | **VERIFIED** |

## B. WHAT THE BOT CAN OBSERVE

All bot observation should occur via memory polling (e.g., every frame or on `CB2` hooks).

| Metric | Memory Target / Method | Observable State |
| :--- | :--- | :--- |
| **Money** | `gSaveBlock1Ptr->money` | Read directly (U32). Bot can diff this before/after whiteout to measure exact financial loss. |
| **Level Gap** | `gEnemyParty[0..5].level` vs `gPlayerParty[0..5].level` | Read directly (U8). Enemy stats are generated and placed in memory the moment the battle starts. |
| **Damage & Durability** | `gBattleMons[i].hp` vs `gBattleMons[i].maxHP` | Read directly (U16) every turn. Bot must sample this delta across `CB2_Battle` frames to calculate "Damage Taken Per Turn" or "# of turns to die". |
| **Type Matchups** | `gBattleStruct->typeEffectiveness` | Wait for attack execution, read this U8 field (contains multiplier data like 0x40 for 1x, 0x80 for 2x). Alternatively, simulate `src/pokemon.c` type tables using `gBattleMons` types and `gBattleMoves` data. |
| **Boss Movesets** | `gEnemyParty[i].moves` | Read directly (U16 array). The bot has omniscient access to the boss's moveset the moment battle initializes, allowing preemptive counter-switching. |
| **Failure Cause** | `gBattleResults.battleTurnCounter` | Read directly (U16). Low turn count + high level gap = Stat/Level check failure. High turn count + enemy HP recovered = Out-sustained (need burst damage/heal block). |

## C. OPTION SPACE

How the bot can handle failure loops when blocked by a story boss.

### 1. In-Game Save and Soft Reset
*   **Mechanism**: Bot issues an in-game save (`save` command) before a boss. On whiteout, triggers emulator reset and reads save.
*   **Cost**: Time cost of re-navigating from the save tile to the boss interaction.
*   **Failure Mode**: If the bot saves in a state where the boss is mathematically unbeatable (e.g., trapped in a room with no healing, underleveled), it soft-locks into an infinite retry loop.
*   **Detection**: Track `attempt_count` per boss. If `attempt_count > threshold` and maximum enemy HP depleted across attempts remains similar, the bot is hard-stuck.

### 2. Natural Whiteout and Grinding
*   **Mechanism**: Bot accepts the whiteout, respawns at the Pokémon Center, paths to tall grass, grinds levels until `PartyLevel >= EnemyBossLevel + X`, then returns.
*   **Cost**: Loss of Money and Friendship. High time cost for travel.
*   **Failure Mode**: "Money Death Spiral". Repeated whiteouts drain all money. The bot cannot buy Poké Balls or Potions, crippling future catch/sustain logic.
*   **Detection**: `gSaveBlock1Ptr->money` hits 0. Friendship values in `gPlayerParty` drop to base levels.

### 3. Emulator State Savestates (Save-Scumming)
*   **Mechanism**: Bot takes a libmgba state snapshot at the start of Turn 1. If it makes a bad move or loses to RNG (crit/miss), it restores the state and changes the PRNG seed (by altering timing) or chooses a different move.
*   **Cost**: Zero in-game resource cost.
*   **Failure Mode**: Overfitting to a specific RNG seed. The bot might find a "1% crit" path to win a fight it is vastly underleveled for, leaving it even further behind the stat curve for the next boss.
*   **Detection**: Win achieved, but `gPlayerParty` average level is $\ge$ 5 levels below the next area's wild encounters.

### 4. Suicidal Scouting
*   **Mechanism**: Deposit all money (buy items), enter boss fight. Bot reads `gEnemyParty` (Levels, Stats, Moves, Types). Bot intentionally loses, respawns, then re-orders its party or teaches TMs specifically to counter the scouted team before returning.
*   **Cost**: Requires complex inventory management to dump money into assets before the fight.
*   **Failure Mode**: Bot teaches a limited-use TM (Gen 3 TMs break after one use) to counter a specific Gym, but overwrites a move vital for later progression.
*   **Detection**: Bot detects it no longer has a move of a specific type or utility required for standard combat loops.

## D. TRAPS

Automated players are highly susceptible to these permanent state alterations.

| Trap / Softlock | Mechanism | Recovery / Prevention |
| :--- | :--- | :--- |
| **TM Exhaustion** | In Emerald, TMs are single-use. If the bot's learning algorithm randomly overwrites moves with TMs to test them, it will exhaust finite resources (e.g., TM 26 Earthquake). | **PREVENT**: Hardcode TM usage restrictions. Bot cannot use TMs without passing a strict heuristic check. |
| **Friendship Evolution Lock** | Whiteout grinding drops friendship. If the bot designates a Golbat, Togepi, or Pichu as a carry, it will never evolve if it frequently dies to bosses. | **OBSERVE**: Track `friendship` in `gPlayerParty`. If it trends downward, force the bot to use a different Pokémon or pivot to a non-fainting grind strategy. |
| **EXP Leeching Trap** | Bot brings a low-level type-advantage Pokémon to a boss. It dies in one hit. The bot loses, retries, and the low-level Pokémon never gains EXP because it never survives a kill. | **OBSERVE**: Compare `gBattleMons[i].hp` at the end of the turn an enemy faints. If the counter-Pokémon is dead, it gets 0 EXP. Switch to wild grinding. |
| **PP Exhaustion Softlock** | Elite Four gauntlet. The bot uses all attacking PP on Sidney/Phoebe. By Drake/Wallace, it is forced to use `Struggle`. Bot wipes, retries, uses same moves, wipes again. | **PREVENT**: Bot must read `gPlayerParty[i].pp`. If total attacking PP across party < required turns to kill remaining E4 members, it must consume Leppa Berries/Elixirs between battles. |
| **One-Shot Legendary Kills** | The bot encounters Rayquaza/Groudon/Kyogre/Latias, calculates it as a threat, and kills it instead of catching it. `FLAG_DEFEATED_...` is set. The Pokémon is permanently gone. | **PREVENT**: Hardcode exceptions for species IDs. If `gEnemyParty[0].species` matches a legendary ID, force `ITEM_POKE_BALL` loop or `Flee` behavior. |
| **Roamer Poison Death** | Bot poisons Latios/Latias. The roamer flees. Next encounter, the roamer takes poison damage immediately and dies before the bot can throw a ball. | **PREVENT**: Bot must parse `gEnemyParty[0].species`. If it is a roamer (Species 197/198 in Emerald), explicitly forbid moves with `MOVE_EFFECT_POISON` or `MOVE_EFFECT_BURN`. |
| **Bicycle Softlocks** | Emerald requires specific bikes (Mach/Acro) for certain maps (e.g., Sky Pillar cracks, Safari Zone areas). If the bot cannot path correctly, it will fall through cracks indefinitely. | **PREVENT**: Read `gSaveBlock1Ptr->location.mapNum`. If traversing Sky Pillar, Mach bike must be equipped and pathing must execute at continuous 60fps movement. |