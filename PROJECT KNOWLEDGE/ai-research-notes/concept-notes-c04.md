## A. MECHANICS THE ROM ENFORCES

### 1. Type Effectiveness
The ROM enforces a predefined multiplier lookup table based on Attacker Type vs Defender Type. 
*   **File:** `src/battle_main.c` (`gTypeEffectiveness`)
*   **Multiplier Values:** 0 = 0x (Immune), 5 = 0.5x (Resist), 10 = 1.0x (Neutral), 20 = 2.0x (Super Effective). **VERIFIED**
*   **Dual Types:** Multipliers stack (e.g., 20 * 20 / 10 = 4.0x). **VERIFIED**
*   **Overrides:** 
    *   *Foresight / Odor Sleuth:* Negates Ghost immunity to Normal/Fighting.
    *   *Levitate:* Grants Ground immunity (unless holding Iron Ball, which doesn't exist in Gen 3, or Gravity is active, also doesn't exist. Mold Breaker doesn't exist in Gen 3). **VERIFIED**

### 2. Turn Order & Priority
Determined at the start of the turn in `src/battle_main.c` (`GetWhoStrikesFirst`).
| Step | Mechanic | Rule | Status |
|---|---|---|---|
| 1 | Move Priority | Ranges from -6 (Roar/Whirlwind) to +5 (Helping Hand). Protect/Detect/Endure are +3. Quick Attack/Mach Punch/Fake Out are +1. | **VERIFIED** (`gBattleMoves[move].priority`) |
| 2 | Item Override | Quick Claw gives a 20% chance to act first within the *same* priority bracket. | **VERIFIED** |
| 3 | Speed Stat | Active Speed stat (includes stat stages, IVs, EVs). | **VERIFIED** |
| 4 | Modifiers | Paralysis cuts Speed to 25% (Speed / 4). Dynamo Badge boosts Speed by 10% (`Speed = (Speed * 110) / 100`). | **VERIFIED** |
| 5 | RNG Tie-Break | If Priority, Item, and modified Speed match, 50/50 RNG decides (`Random() & 1`). | **VERIFIED** |

### 3. Trapping & Escape
In Gen 3, **Ghost-types are NOT immune to trapping** (that is a Gen 6 mechanic). **VERIFIED**
| Mechanic | Enforced Rules | Pokeemerald ref |
|---|---|---|
| **Abilities** | Shadow Tag blocks all switches except opposing Shadow Tag. Arena Trap blocks all grounded Pokémon (Flying type or Levitate are immune). Magnet Pull blocks Steel types. | `src/battle_util.c` (`GetBattlerAbility`) |
| **Moves** | Mean Look / Block / Spider Web permanently trap until the user leaves the field. | `src/battle_main.c` (`IsTrapped`) |
| **Baton Pass** | Bypasses all trapping moves and abilities. | **VERIFIED** |
| **Pursuit** | Base Power doubles (40 -> 80). Calculates damage and executes *before* the switch. If Pursuit faints the target, the switch is cancelled. | `src/battle_main.c` (`CheckAndSetPursuit`) |
| **Smoke Ball** | Guarantees escape from *wild* battles. Does NOT allow switching/fleeing in Trainer battles. | **VERIFIED** |

### 4. Trainer AI (Switching & Move Selection)
Trainer AI does not act like a human. It evaluates moves based on an initial score of 100, modifying the score via a bitmask of flags assigned to the specific Trainer class.
*   **File:** `src/battle_ai_main.c`, `src/battle_ai_switch_items.c`
*   **Moves:** Modifiers check `gTypeEffectiveness`, current HP, and status. `AI_FLAG_CHECK_BAD_MOVE` prevents using status moves on a mon that already has that status, or using Ground moves on Flying types. **VERIFIED**
*   **Switching:** Emerald AI *rarely* switches voluntarily. It primarily evaluates switches if:
    1. It is afflicted by Perish Song with a count of 0.
    2. It is locked into a move it cannot execute (e.g., Choice Band + Disabled).
    3. The trainer has `AI_FLAG_CHECK_VIABILITY` and the AI calculates its current mon has exactly 0 viable offensive options. **VERIFIED**

## B. WHAT THE BOT CAN OBSERVE

Because you are using an emulator with full memory read/write, the bot does not need to guess. Fog of War is entirely bypassable. 

| Data Point | Location in Memory (Pokeemerald naming) | Readability |
|---|---|---|
| **Opponent Base Party** | `gEnemyParty` (Array of `struct Pokemon`) | **100% Observable.** Bot can read exact Species, IVs, EVs, Moves, PID, OTID, Held Item, and exact level of every Pokémon before they even enter the field. |
| **Active Battle State** | `gBattleMons[1]` (and `[3]` for doubles) | **100% Observable.** Contains mid-battle calculated stats: `hp`, `maxHP`, `status1` (BRN/PAR/SLP/FRZ/PSN), `status2` (Confusion, Leech Seed), `statStages` (ATK, DEF, SPE, etc.), actual current `ability` (reflects Skill Swap/Trace), and `item` (reflects Knock Off/Trick). |
| **Trainer AI Flags** | `gBattleResources->ai->aiFlags` | **Observable.** Bot can read the exact 32-bit integer dictating the AI's logic for the current turn. |
| **RNG State** | `gRngValue` (32-bit integer) | **Observable.** Bot can read the exact seed and predict the AI's tie-breakers, damage rolls (85-100%), and move selections if scores tie. |
| **Trapped Status** | `gBattleStruct->monToSwitchIntoId` / `gStatuses3` | **Inferred/Observable.** The bot must check `gBattleMons[1].ability` for Shadow Tag/Arena Trap, or `gStatuses2` for Mean Look flags, to know if the ROM will reject a switch command. |

## C. OPTION SPACE

### Strategy 1: Omniscient Pre-Calculation (The Terminator)
Use memory reads of `gEnemyParty` and `gRngValue` to run `CalculateBaseDamage` locally in the bot before acting.
*   **Mechanics:** Bot simulates the turn. If the incoming damage roll is lethal, or if an enemy attack is super-effective and a bench mon resists it, switch. 
*   **Cost:** High computational and architectural cost. Requires re-implementing Emerald's damage formula and AI evaluation tree in the bot's language.
*   **Failure Mode:** Pursuit trapping. The bot calculates a switch is optimal, but switching triggers an enemy Pursuit that becomes lethal due to the 2x multiplier.
*   **Detection:** The simulation engine must explicitly check the enemy's moveset in `gEnemyParty` for `MOVE_PURSUIT` and flag switches as fatal.

### Strategy 2: AI-Baiting & Setup Sweeping
Exploit the ROM's deterministic AI evaluation. Emerald AI heavily prioritizes Super Effective moves.
*   **Mechanics:** Bot sends out a Pokémon weak to an enemy move (e.g., Gyarados weak to Electric). The AI scores Thunderbolt highest. Bot switches to a Ground-type (immune). Ground-type sets up Swords Dance/Dragon Dance on the free turn. 
*   **Cost:** Requires maintaining a perfectly curated team composition to ensure baits exist for all types.
*   **Failure Mode:** AI with `AI_FLAG_RISKY` or without `AI_FLAG_PREFER_STRONGEST_MOVE` (common in lower-level trainers) might select a non-super-effective move randomly, ruining the bait.
*   **Detection:** Bot reads the opponent's active move index from `gBattleResults.lastUsedMove` at turn end. If it doesn't match the expected bait, the strategy desyncs.

### Strategy 3: Brute Force & Item Spam (The Juggernaut)
Ignore switching entirely to negate Trapping and Pursuit risks. Rely purely on Level advantage and X-Items/Potions.
*   **Mechanics:** Only switch when a Pokémon faints. Use memory to read enemy `hp` and `type`. Spam the highest BP move. If `hp < 30%`, use Hyper Potion.
*   **Cost:** High in-game resource drain (Pokédollars for items). Action economy inefficiency.
*   **Failure Mode:** Softlocked by Ghost-type immunities if the bot's only remaining Pokémon only knows Normal/Fighting moves (e.g., a Slaking with only Return and Earthquake facing a Misdreavus with Levitate).
*   **Detection:** Bot observes `gBattleResults.lastMoveFailed` or checks type effectiveness internally and sees all available moves return `0` multiplier.

## D. TRAPS

Because the bot repeats actions infinitely, these edge-cases will wedge the bot or drain its resources permanently.

| Trap / Softlock | Mechanical Cause | How the Bot Wedges Itself | Prevention / Resolution |
|---|---|---|---|
| **The "Trapped" Menu Loop** | `IsTrapped` check fails. Rom prevents menu transition. | Bot sends `DPAD_UP, A` to select "POKEMON" menu to switch. The ROM flashes "Cannot switch out!" and stays on the Battle menu. Bot blindly sends `A` to confirm the switch target, but actually selects "FIGHT" and fires a random move. | Bot *must* check the enemy's Ability (Shadow Tag/Arena Trap) and volatile status (`gStatuses2` for Mean Look) in memory before queuing a switch action. |
| **Pursuit Suicide Loop** | `CheckAndSetPursuit` triggers before switch. | Bot decides to switch. Enemy uses Pursuit. Bot takes damage but survives. Switch executes. Next turn, bot switches *back* to original mon. Repeat until fainted. | Bot must evaluate Pursuit lethality/damage *before* deciding a switch is "safer" than staying in. |
| **Truant/Protect Desync** | Slaking's Ability + AI Protect. | Bot uses an attack on Truant's active turn. AI uses Protect. Bot does 0 damage. Next turn, Bot is loafing. AI attacks. Repeat until Bot faints. | Bot must read `gBattleMons[1].item` and moveset for Protect/Detect, and track consecutive turns to break the loop. |
| **Encore / Torment Lock** | `gStatuses2` flags `STATUS2_ENCORE`. | Bot uses a setup move (Swords Dance). AI uses Encore. Bot wants to use an attack, but the ROM forces Swords Dance. Bot endlessly wastes turns or PP. | Bot must read `DisableStruct->encoredMove` in memory and adapt its action plan to the forced state. |
| **PP Struggle Exhaustion** | PP reaches 0 (`gBattleMons[0].pp[i]`). | Bot faces an opposing Pokémon with high evasion (Double Team) or healing (Rest/Protect). Bot expends all PP, enters Struggle, and kills itself via recoil. | Track PP in memory. If total PP of viable moves < 5, execute an emergency switch or use an Ether. |
| **Roar / Whirlwind Desync** | Force-switch moves (`effect == EFFECT_ROAR`). | Bot plans a 5-turn setup sweep. Enemy uses Roar. ROM forces a random bench Pokémon into the active slot. Bot executes turn 2 of the setup plan with the wrong Pokémon. | Bot must verify `gBattleMons[0].species` at the start of *every* turn to ensure the expected actor is currently on the field. |