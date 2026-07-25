## A. MECHANICS THE ROM ENFORCES

### 1. Experience Calculation Formula
All experience calculations occur at the moment an opposing Pokémon faints, processed in `src/battle_script_commands.c` (often initiated by `Cmd_getexp`).

| Mechanic | Implementation / Formula | Status |
| :--- | :--- | :--- |
| **Base Yield** | `Base = (gBaseStats[species].expYield * Level) / 7` | **VERIFIED** |
| **Trainer Multiplier** | If Trainer battle: `Total = (Base * 15) / 10`. Wild battles skip this. | **VERIFIED** |
| **Participant Split** | `s_out` = number of un-fainted Pokémon that entered the battle.<br>`s_share` = number of un-fainted Pokémon in party holding `ITEM_EXP_SHARE`.<br>All division rounds *down* (truncates integer). Minimum yield is 1. | **VERIFIED** |
| **EXP Share Logic** | If `s_share > 0`: Pool is halved.<br>Battlers get: `(Total / 2) / s_out`<br>Holders get: `(Total / 2) / s_share`<br>If a Pokémon both battled *and* holds EXP Share, it receives the sum of both. | **VERIFIED** |
| **No Share Logic** | If `s_share == 0`: Battlers get `Total / s_out`. | **VERIFIED** |
| **Traded Multiplier** | Applied individually after split: `Exp = (Exp * 15) / 10` if OT/ID mismatch. | **VERIFIED** |
| **Lucky Egg** | Applied individually after split: `Exp = (Exp * 15) / 10` if holding `ITEM_LUCKY_EGG`. | **VERIFIED** |
| **Whiteout Survival**| **Mid-battle EXP survives a whiteout.** EXP is written directly to `gPlayerParty` when the opposing Pokémon faints. `CB2_WhiteOut` only heals the party (`HealPlayerParty`) and halves money; it does *not* roll back save states. | **VERIFIED** |

### 2. Growth Rates (Levelling Curves)
Defined in `include/constants/pokemon.h` and precalculated as 2D arrays in `src/pokemon.c` (`gExperienceTables`). The game does not calculate polynomials at runtime; it does an array lookup: `gExperienceTables[growthRate][level]`.

| Name | Enum | Curve Shape / Max EXP | Common Species | Status |
| :--- | :--- | :--- | :--- | :--- |
| Erratic | `GROWTH_ERRATIC` | Fast early, incredibly slow late. Max: 600,000 | Nincada, Feebas | **VERIFIED** |
| Fast | `GROWTH_FAST` | `0.8 * L^3`. Max: 800,000 | Jigglypuff, Skitty | **VERIFIED** |
| Med Fast | `GROWTH_MEDIUM_FAST` | `L^3`. Max: 1,000,000 | Starters, Poochyena | **VERIFIED** |
| Med Slow | `GROWTH_MEDIUM_SLOW` | `1.2*L^3 - 15*L^2 + 100*L - 140`. Max: 1,059,860 | Ralts, Geodude | **VERIFIED** |
| Slow | `GROWTH_SLOW` | `1.25 * L^3`. Max: 1,250,000 | Aron, Legendaries | **VERIFIED** |
| Fluctuating | `GROWTH_FLUCTUATING`| Highly variable piece-wise. Max: 1,640,000 | Makuhita, Shroomish | **VERIFIED** |

### 3. Version Differences in Trainer Rematches
*   **Emerald**: Uses **Match Call** (`src/match_call.c`). Rematches trigger based on a hidden step counter that rolls RNG against a probability table depending on the trainer's rematch tier. **VERIFIED**.
*   **Ruby/Sapphire**: Uses **Trainer's Eyes**. Completely different memory structure and flag set. **VERIFIED**.
*   **FireRed/LeafGreen**: Uses **VS Seeker**. On-demand item use with a strict 100-step battery charge. Emerald bots *cannot* use this logic. **VERIFIED**.

---

## B. WHAT THE BOT CAN OBSERVE

| State Needed | Memory Location / Inference |
| :--- | :--- |
| **Current EXP / Level** | `gPlayerParty[i].exp` and `gPlayerParty[i].level`. Can be read instantly from RAM. |
| **Target EXP for Next Lvl** | Calculate locally by reading `gPlayerParty[i].species`, checking `gBaseStats[species].growthRate` from ROM, and looking up `gExperienceTables[growthRate][level + 1]`. |
| **EXP Yield of Opponent** | `gBaseStats[gBattleMons[1].species].expYield`. Read directly from ROM during battle. |
| **Is Opponent Trainer?** | `gBattleTypeFlags & BATTLE_TYPE_TRAINER`. Read from RAM `gBattleTypeFlags`. |
| **Rematch Availability** | Read `gSaveBlock1Ptr->trainerRematches[i]`. If > 0, the trainer at index `i` is ready for a rematch. |

---

## C. OPTION SPACE: WILD GRINDING VS BOSS RE-FIGHTS

To evaluate the most efficient grinding method, the bot must continuously evaluate the **XP-per-frame (XPF)** of available strategies.

### Mathematical Comparison Framework
The bot should evaluate the expected XPF for a target grinding zone/trainer using:
`XPF = Expected_EXP / Expected_Frames`

### Strategy 1: Wild Encounter Grinding
*   **Mechanics**: Run back and forth in grass/caves.
*   **Formula**: `XPF = (Yield * Level / 7) / (Enc_Frames + Battle_Frames)`
    *   `Enc_Frames`: Average steps to encounter * frames per step + transition animation.
    *   `Battle_Frames`: Attack animations + text delays.
*   **Cost**: Consumes PP. May require walking back to a Pokémon Center (adds frames to the denominator).
*   **Failure Mode**: Bot runs out of PP, uses Struggle, and whites out.
*   **Detection**: Monitor `gPlayerParty[i].pp`. If sum of usable PP == 0, abort loop and path to Center.

### Strategy 2: Match Call Re-battles (Gabby & Ty Loop)
*   **Mechanics**: In Emerald, Interviewers Gabby & Ty move between Route 111, 118, and 120. They are immediately re-battleable upon finding them at their next location, completely bypassing the RNG step-counter required for normal Match Call trainers.
*   **Formula**: `XPF = (Yield * Level * 1.5 / 7 * 2) / (Pathing_Frames + Transition_Frames + Double_Battle_Frames)`
*   **Cost**: High pathing complexity. Bot must navigate open-world routes precisely.
*   **Failure Mode**: Bot gets stuck on terrain/NPCs during the long inter-route transit.
*   **Detection**: Pathing coordinate delta (X, Y) does not change for 120 frames while trying to move.

### Strategy 3: Standard Match Call Waiting
*   **Mechanics**: Walk back and forth to increment the step counter and trigger `StepCallback_MatchCall`, waiting for `gSaveBlock1Ptr->trainerRematches` to flip for a high-yield Gym Leader.
*   **Formula**: `XPF = (Yield * Level * 1.5 / 7 * N_Mons) / (RNG_Step_Frames + Battle_Frames)`
*   **Cost**: RNG reliant. The probability of triggering a specific high-tier rematch per step is exceptionally low.
*   **Failure Mode**: Step-grinding takes so long that `RNG_Step_Frames` dwarfs the EXP yield, resulting in lower XPF than simply killing wild Poochyenas.
*   **Detection**: Continuous polling of the XPF moving average. If XPF drops below the Wild Grinding baseline, fallback to Strategy 1.

---

## D. TRAPS

The following are ways an automated player can permanently damage the save file or enter an unrecoverable logic loop regarding levelling:

| Trap | Consequence | Remediation / Avoidance |
| :--- | :--- | :--- |
| **Evolution Skipping (B-Mash)** | Level up screens trigger evolution (`CB2_EvolutionScene`). If the bot is spamming the `B` button to clear text quickly, it will cancel the evolution. This wastes the massive stat increases of the evolved form. | The bot must read `gMain.callback2`. If it equals `CB2_EvolutionScene`, **only** press `A`, never `B`. |
| **Move Learning Overwrites** | When levelling up, if a move is learned, the game halts until a move is forgotten or skipped. Blind A-mashing will overwrite Slot 1. Blind B-mashing will skip learning the new move entirely. | Read `gTasks` to detect `Task_LearnMove`. Inject a hardcoded Move Priority List (e.g., never overwrite Surf) to safely resolve the menu. |
| **Disobedient Traded Mons** | If the bot acquires a traded Pokémon, strict Level/Badge caps apply (e.g., Level 30 for Knuckle Badge). If the bot over-levels a traded Pokémon, it will randomly ignore inputs (`src/battle_util.c:IsMonDisobedient`). | Check `gPlayerParty[i].otId` against `gSaveBlock2Ptr->playerTrainerId`. If mismatched, cap grinding target to current obedience threshold. |
| **Wilderness Softlock (EXP Trap)** | If the bot purposefully drops all HM slaves in the PC to maximize EXP share distribution for a specific carry, and then saves the game on an island (e.g., Dewford), it cannot Surf or Fly away. | Ensure the bot's party state always contains `MOVE_SURF` and `MOVE_FLY` (if unlocked) before initiating any grinding routines. |
| **White-out Money Bleed** | Because mid-battle EXP is kept on whiteout, a naive bot might purposely use whiteouts as a "free teleport" back to the Pokémon Center to restore PP. This halves the player's money (`gSaveBlock1Ptr->money /= 2`) every time. | Track `gSaveBlock1Ptr->money`. If grinding, force a walk back to the PC when `PP <= 5` instead of intentionally wiping. |
| **Struggle Recoil Death** | If PP is 0, the bot uses Struggle. In Gen 3, Struggle recoil is `1/4 of max HP` (Gen 4 changed this from 1/4 damage dealt). A bot trying to grind low-level mons with a high-level 0 PP mon will kill itself in 4 turns. | Never allow a grinding routine to persist if all high-level carries have 0 PP. |