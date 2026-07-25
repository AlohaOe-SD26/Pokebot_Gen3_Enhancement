## A. MECHANICS THE ROM ENFORCES

**Catch Calculation Logic** (`src/battle_script_commands.c` -> `Cmd_trycatchpokemon`):
When a Poké Ball is thrown, the ROM calculates a modified catch rate ($a$). Integer truncation (floor) occurs after every division.

### 1. The Base Formula ($a$)
$a = \lfloor \frac{\lfloor \frac{3 \times HP_{max} - 2 \times HP_{current}}{3 \times HP_{max}} \times Rate_{base} \times Bonus_{ball} \rfloor \times Bonus_{status}}{10} \rfloor$

*   $Rate_{base}$: 1 to 255 (from `src/data/pokemon/base_stats.h`).
*   **VERIFIED**: If $a \ge 255$, the Pokémon is caught instantly without shake checks.

### 2. Status Multiplier ($Bonus_{status}$)
*   **Freeze / Sleep**: 20 (Divides by 10 later to yield 2.0x) **VERIFIED**.
*   **Paralysis / Poison / Burn**: 15 (Divides by 10 later to yield 1.5x) **VERIFIED**.
*   **None**: 10 (Yields 1.0x) **VERIFIED**.

### 3. Shake Check Maths ($b$)
If $a < 255$, the ROM calculates the shake probability threshold ($b$).
*   **Equation**: $b = \lfloor 1048560 / \sqrt{\sqrt{16711680 / a}} \rfloor$ **VERIFIED**.
    *   *Math Note*: This is the ROM's integer approximation of $b = 65536 \times (a / 255)^{0.25}$.
*   **The Check**: The RNG (`Random()`, returning 0 to 65535) is called 4 times.
    *   If `Random() >= b`, the check fails, the ball breaks, and the Pokémon escapes.
    *   If all 4 checks pass, the Pokémon is caught.
*   **Critical Capture**: **VERIFIED** DOES NOT EXIST in Generation 3. It was introduced in Gen 5.

### 4. Ball Multipliers ($Bonus_{ball}$)
Ball logic is handled via a switch statement checking `itemID`.

| Ball | Multiplier ($Bonus_{ball}$) | Condition / Formula (Gen 3) | Status |
| :--- | :--- | :--- | :--- |
| **Poke** | 1.0x (10/10) | Default. | **VERIFIED** |
| **Premier** | 1.0x (10/10) | Default. | **VERIFIED** |
| **Luxury** | 1.0x (10/10) | Default. Gives caught mon +1 starting friendship. | **VERIFIED** |
| **Great** | 1.5x (15/10) | Default. | **VERIFIED** |
| **Safari** | 1.5x (15/10) | Default (used only in Safari Zone). | **VERIFIED** |
| **Ultra** | 2.0x (20/10) | Default. | **VERIFIED** |
| **Net** | 3.0x (30/10) | If target type 1 or 2 is Water or Bug. Else 1.0x. | **VERIFIED** |
| **Dive** | 3.5x (35/10) | **EMERALD:** If surfing, fishing, or underwater. Else 1.0x. *(Note: R/S is underwater ONLY).* | **VERIFIED** |
| **Nest** | 1.0x to 3.0x | $\lfloor \frac{41 - Level}{10} \rfloor$. Minimum 1.0x. | **RECALL** |
| **Repeat** | 3.0x (30/10) | If target species has `FLAG_GET_CAUGHT` in Pokédex. Else 1.0x. | **VERIFIED** |
| **Timer** | 1.0x to 4.0x | $\lfloor \frac{Turns_{battle} + 10}{10} \rfloor$. Maximum 4.0x at 30 turns. | **VERIFIED** |
| **Master** | N/A | Bypasses formula ($a$ calculation skipped, automatic catch). | **VERIFIED** |

---

## B. WHAT THE BOT CAN OBSERVE

To compute expected balls and optimal policy, the bot must read the following memory addresses / structs:

| Variable | Struct / Field / Location | Read / Infer |
| :--- | :--- | :--- |
| **$HP_{current}$** | `gBattleMons[1].hp` (Index 1 is enemy in single battles) | Direct Read |
| **$HP_{max}$** | `gBattleMons[1].maxHP` | Direct Read |
| **$Level$** | `gBattleMons[1].level` (Needed for Nest Ball) | Direct Read |
| **$Rate_{base}$** | `gBaseStats[gBattleMons[1].species].catchRate` | Direct Read |
| **$Status$** | `gBattleMons[1].status1` (Bitmask: Sleep is `0x7`, Freeze is `0x20`) | Direct Read |
| **Types** | `gBaseStats[gBattleMons[1].species].type1` / `.type2` | Direct Read |
| **Pokedex State** | `GetSetPokedexFlag(species, FLAG_GET_CAUGHT)` equivalent in RAM | Direct Read |
| **$Turns_{battle}$** | `gBattleResults.battleTurnCounter` | Direct Read |
| **Environment** | `gBattleTypeFlags` (Check for `BATTLE_TYPE_SURF` or `BATTLE_TYPE_FISHING`) | Direct Read |

**Calculating Expected Balls-per-Catch ($E$):**
1. Bot reads memory to construct $a$.
2. If $a \ge 255$, $E = 1$.
3. Else, Bot calculates $b$.
4. Probability of 1 shake passing: $P_{shake} = b / 65536.0$.
5. Probability of catch: $P_{catch} = (P_{shake})^4$.
6. Expected balls: $E = 1 / P_{catch}$.

---

## C. OPTION SPACE

### 1. Optimal Observable Policy (Calculated Catching)
The bot reads target stats on Turn 1, evaluates $E$ for all available balls in its inventory, and chooses the action that minimises resource cost.
*   **HP Fraction Target**: $HP_{current} = 1$ (achieved via False Swipe).
*   **Status Target**: Sleep (`status1 & 0x7`). (Freeze is 2.0x but cannot be inflicted reliably).
*   **Ball Selection**: Sort inventory by highest $Bonus_{ball}$ currently applicable (e.g., Dive Ball if surfing, Timer if Turn > 30, Repeat if owned, else Ultra).
*   **Cost**: Requires a False Swipe user + Spore/Sleep Powder user. Requires ~3-5 turns of setup per encounter.
*   **Failure Mode**: Target wakes up, target heals, or target damages itself.
*   **Detection**: `gBattleMons[1].hp == 0` (Fainted) or Battle state exits to Overworld without updating Pokedex/PC.

### 2. Turn-1 Net/Repeat/Dive Spam (Fast Catch)
Bot throws the optimal conditional ball on Turn 1 at full HP with no status.
*   **HP/Status Target**: 100% HP, No status.
*   **Ball Selection**: Dive Ball (if fishing/surfing) $\rightarrow$ Repeat Ball (if owned) $\rightarrow$ Net Ball (if Water/Bug) $\rightarrow$ Ultra Ball.
*   **Cost**: Consumes significantly more balls and money.
*   **Failure Mode**: Bot runs out of balls or target wipes the bot's team while the bot spams items.
*   **Detection**: Bag quantity for target ball drops to 0 (`gSaveBlock1Ptr->bagPocket_Pokeballs`).

### 3. Stall & Timer Spam
Bot swaps between tank Pokémon to increment `gBattleResults.battleTurnCounter` until $> 30$, then spams Timer Balls.
*   **Cost**: High real-time cost, consumes healing items.
*   **Failure Mode**: Target exhausts PP and uses Struggle, killing itself.

---

## D. TRAPS (Permanent Value Loss & Softlocks)

An autonomous bot will wedge itself or destroy resources if it does not explicitly handle these rules:

| Trap | Mechanism | Permanent Consequence / Fix |
| :--- | :--- | :--- |
| **The Full Box Lock** | **VERIFIED:** In Gen 3, if the *currently selected PC box is full* (30/30), the game strictly prohibits throwing any Poké Ball. It does not auto-switch boxes. | **SOFTLOCK:** Bot loops trying to throw a ball, gets "The box is full!" message, wasting infinite turns. Bot MUST read `StorageGetCurrentBox()` and switch boxes at a PC when full. |
| **Recoil Suicide** | Target uses Take Down, Double-Edge, or Roar of Time (Wait, Roar of Time is Gen 4, Gen 3 has Submission, Double-Edge). | **VALUE LOSS:** If bot False Swipes to 1HP, the target will kill itself on its next recoil attack. Bot must check `gBattleMoves` of the target's species/level. |
| **Weather Suicide** | Hail or Sandstorm is active. | **VALUE LOSS:** 1HP target dies at end of turn. Bot must abort False Swipe if `gBattleWeather` is active. |
| **Status Suicide** | Bot uses Poison or Burn to get a 1.5x catch multiplier. | **VALUE LOSS:** Target takes end-of-turn damage and dies. Bot must *never* use Poison/Burn for catching. |
| **Struggle Suicide** | Bot takes too long (e.g., Timer Ball stalling), target runs out of total PP for all moves. | **VALUE LOSS:** Target uses Struggle, takes recoil, and dies. Bot must track `gBattleMons[1].pp`. |
| **Flee Mechanics** | Target is Roaming Latias/Latios or has Roar/Whirlwind/Teleport. | **VALUE LOSS:** Target forces battle end. Bot must trap (Mean Look / Shadow Tag) or prioritize Turn-1 Master Ball. |
| **Curse Suicide** | Target is a Ghost-type with Curse (e.g., Shuppet/Duskull). | **VALUE LOSS:** Target cuts its own HP by 50% to curse the bot, killing itself if $< 50\%$ HP. |
| **Bag Slot Exhaustion**| Gen 3 Poké Ball pocket holds 16 item *slots*, each capped at 99. | **SOFTLOCK:** If bot tries to buy 999 Ultra balls, it fails. If pocket is filled with 16 types of $\le 99$ items, bot cannot receive/buy new ball types. |
| **Safari Zone Flee** | Safari Zone uses entirely different mechanics (`gBattleStruct->safariCatchFactor` and `safariEscapeFactor`). Standard $a$ formula does not apply. | **VALUE LOSS:** Standard HP/Status logic fails. Bot must read `safariCatchFactor` and balance throwing Mud/Bait vs catching. |