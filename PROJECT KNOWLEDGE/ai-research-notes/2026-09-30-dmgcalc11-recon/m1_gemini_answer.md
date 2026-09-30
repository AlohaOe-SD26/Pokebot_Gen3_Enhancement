> ⚠ **A GEMINI NOTE ("what to look for" only; never a source of truth).** Produced 2026-09-30 by `tools/story-dev/gemini_relay.py` (default Pro model) for design v2 step 11. The recon's decomp agent checked it claim by claim (`m1_recon_decomp.md` §5): the names are mostly right, and the placement and order are mostly WRONG (e.g. the crit placement, Charge and Helping Hand as base-power changes, Metal Powder ×1.5 instead of ×2). Do not build on it.

Here is the exhaustive enumeration for auditing a Pokémon Emerald damage predictor, citing the `pret/pokeemerald` decomp. 

### 1. Order of Operations (The Math & Battle Script Flow)
The execution flow for a standard damaging move occurs linearly via battle script commands in `src/battle_script_commands.c`, with the core math in `src/pokemon.c` (`CalculateBaseDamage`). Every step strictly uses integer math (floor/truncate toward zero at each division unless specified).

1.  **`Cmd_critcalc`**: Rolls for a critical hit. Sets a critical hit flag in `gBattleStruct` if successful.
2.  **`Cmd_damagecalc`**: The heaviest command. Gathers stats and applies modifiers *before* base math:
    *   Fetch Base Power (BP). Apply Helping Hand (`damage * 15 / 10`), Charge (`BP * 2`), and Mud Sport/Water Sport (`BP / 2`).
    *   Determine if the move is Physical or Special **by type** (Gen 3 mechanics).
    *   Fetch Attacker's raw Atk or SpAtk. Apply Stat Stages (numerator/denominator). 
    *   Apply Attacker Abilities: `ABILITY_HUGE_POWER`/`ABILITY_PURE_POWER` (`stat * 2`), `ABILITY_HUSTLE` (`stat * 15 / 10`), `ABILITY_PLUS`/`ABILITY_MINUS` (`stat * 15 / 10`), `ABILITY_GUTS`, `ABILITY_OVERGROW`, `ABILITY_BLAZE`, `ABILITY_TORRENT`, `ABILITY_SWARM` (`stat * 15 / 10`).
    *   Apply Attacker Items: `ITEM_THICK_CLUB`, `ITEM_LIGHT_BALL`, `ITEM_DEEP_SEA_TOOTH` (`stat * 2`). `ITEM_SOUL_DEW`, `ITEM_CHOICE_BAND` (`stat * 15 / 10`).
    *   Fetch Defender's raw Def or SpDef. Apply Stat Stages.
    *   Apply Defender Items: `ITEM_SOUL_DEW`, `ITEM_METAL_POWDER`, `ITEM_DEEP_SEA_SCALE` (`stat * 15 / 10` or `* 2` for DSS).
    *   Apply Defender Abilities: `ABILITY_MARVEL_SCALE` (`stat * 15 / 10`), `ABILITY_THICK_FAT` (halves the *Attacker's* SpAtk/Atk variable: `stat / 2`).
    *   Halve Defender's Def if move is `MOVE_EXPLOSION` or `MOVE_SELF_DESTRUCT`.
3.  **`CalculateBaseDamage` (in `src/pokemon.c`)**:
    *   Step A: `level * 2 / 5 + 2`. If Crit flag is set, `Step A * 2`.
    *   Step B: `Step A * Base Power * AttackStat`.
    *   Step C: `Step B / DefenseStat`.
    *   Step D: `Step C / 50`.
    *   Step E: `Step D + 2`.
4.  **`Cmd_damagecalc` (Post-Base Math)**:
    *   Apply Reflect/Light Screen: Divide damage by 2 (Singles) or `UNSURE`: multiply by 2 then divide by 3 (Doubles). Crit ignores screens.
    *   Apply Weather: Sun/Rain damage is multiplied by 15, divided by 10 (boost), or divided by 2 (reduction).
    *   Apply `ABILITY_FLASH_FIRE` boost (`damage * 15 / 10`).
5.  **`Cmd_typecalc`**:
    *   Apply STAB: `damage * 15 / 10`.
    *   Apply Type Effectiveness: Loops through defender types. Uses a multiplier array (20 = 2x, 5 = 0.5x, 0 = immune). `damage = damage * multiplier / 10`.
6.  **`Cmd_adjustnormaldamage` (or `Cmd_adjustsetdamage`)**:
    *   Apply Random Factor: `damage = (damage * Random(85 to 100)) / 100`.
    *   Apply Burn: If Attacker is burned and move is Physical (and not `MOVE_FACADE` with `ABILITY_GUTS`), `damage = damage / 2`.
    *   Minimum Damage Check: If `damage == 0` and the move is not a type immunity, `damage = 1`.

### 2. Every Modifier Grouped
*   **Stat Stages**: Applied as fractions. Max +6 (8/2), Min -6 (2/8). **Crits**: A critical hit bypasses the attacker's negative stat stages (uses 2/2) and the defender's positive stat stages (uses 2/2). 
*   **Badge Boosts**: Applied during battle stat retrieval (`UNSURE` exact file, likely `src/pokemon.c` stat getters). Grants a 1.1x boost (multiply by 11, divide by 10). Boulder = Atk, Balance = Def, Dynamo = Spd, Mind = SpAtk & SpDef (`UNSURE` if SpDef is actually boosted by Mind in Emerald decomp, verify `ApplyBadgeStatBoosts`).
*   **Abilities (Attacker)**:
    *   `ABILITY_HUGE_POWER`, `ABILITY_PURE_POWER`: Atk * 2.
    *   `ABILITY_HUSTLE`: Atk * 1.5 (Physical only).
    *   `ABILITY_GUTS`: Atk * 1.5 (If status != 0).
    *   `ABILITY_PLUS`, `ABILITY_MINUS`: SpAtk * 1.5 (If partner has the counterpart).
    *   `ABILITY_OVERGROW`, `ABILITY_BLAZE`, `ABILITY_TORRENT`, `ABILITY_SWARM`: Atk/SpAtk * 1.5 (If HP <= max / 3).
*   **Abilities (Defender)**:
    *   `ABILITY_MARVEL_SCALE`: Def * 1.5 (If status != 0).
    *   `ABILITY_THICK_FAT`: Attacker's Atk/SpAtk / 2 for Fire/Ice moves.
    *   Immunities: `ABILITY_LEVITATE`, `ABILITY_WONDER_GUARD`, `ABILITY_VOLT_ABSORB`, `ABILITY_WATER_ABSORB`, `ABILITY_FLASH_FIRE`, `ABILITY_SOUNDPROOF` nullify damage entirely (handled mostly in type checks or move effect functions).
*   **Held Items**:
    *   Type-boosting items (e.g., `ITEM_MYSTIC_WATER`): BP * 1.1.
    *   `ITEM_CHOICE_BAND`: Atk * 1.5.
    *   `ITEM_LIGHT_BALL`: SpAtk * 2 (Pikachu).
    *   `ITEM_THICK_CLUB`: Atk * 2 (Cubone/Marowak).
    *   `ITEM_DEEP_SEA_TOOTH`: SpAtk * 2 (Clamperl).
    *   `ITEM_DEEP_SEA_SCALE`: SpDef * 2 (Clamperl).
    *   `ITEM_SOUL_DEW`: SpAtk/SpDef * 1.5 (Latios/Latias).
    *   `ITEM_METAL_POWDER`: Def * 1.5 (Ditto).
*   **Weather**: Rain/Sun boost ( * 1.5) or reduce ( / 2) Water/Fire. SolarBeam BP is halved outside of Sun (`MOVE_SOLAR_BEAM`).
*   **Screens**: Reflect (Physical), Light Screen (Special). Division by 2 (Singles) or 1.5 (Doubles). Ignored by crits.
*   **Burn**: Halves physical damage at the *end* of the sequence, unless using `MOVE_FACADE`.
*   **Sports**: Mud Sport (Electric * 0.5), Water Sport (Fire * 0.5).
*   **Charge**: Electric move BP * 2.
*   **Helping Hand**: BP * 1.5 (calculated early).
*   **STAB**: Damage * 1.5.
*   **Type Effectiveness**: Multipliers (0x, 0.5x, 2x) applied per Defender type (Type 1 then Type 2). Order matters for integer flooring.
*   **Critical Hits**: Multiplier is strictly 2x (applied to the `level` term inside `CalculateBaseDamage`).
*   **Random Factor**: Multiplier from 85 to 100, then divide by 100.
*   **Minimum Damage**: 1 (handled in `Cmd_adjustnormaldamage`).

### 3. Moves Bypassing the Normal Formula
*   **Fixed Damage**: `MOVE_DRAGON_RAGE` (40), `MOVE_SONIC_BOOM` (20). *Respects type immunity (Ghost immune to Normal).*
*   **Level Damage**: `MOVE_SEISMIC_TOSS`, `MOVE_NIGHT_SHADE`. *Respects type immunity.*
*   **OHKO**: `MOVE_FISSURE`, `MOVE_HORN_DRILL`, `MOVE_GUILLOTINE`, `MOVE_SHEER_COLD`. *Respects type immunity.*
*   **HP-Based**: `MOVE_SUPER_FANG` (Target HP / 2). *Respects type immunity.*
*   **Reaction Damage**: `MOVE_COUNTER`, `MOVE_MIRROR_COAT`, `MOVE_BIDE`. (Damage taken * 2). *Respects type immunity (Ghost immune to Counter/Bide, Dark immune to Mirror Coat).*
*   **Endeavor**: `MOVE_ENDEAVOR` (Target HP - User HP). *Respects type immunity.*
*   **Dynamic Base Power (Still uses formula)**: `MOVE_PRESENT`, `MOVE_MAGNITUDE`, `MOVE_SPIT_UP`, `MOVE_BEAT_UP`, `MOVE_HIDDEN_POWER`, `MOVE_RETURN`, `MOVE_FRUSTRATION`, `MOVE_LOW_KICK`, `MOVE_FLAIL`, `MOVE_REVERSAL`, `MOVE_ERUPTION`, `MOVE_WATER_SPOUT`, `MOVE_FACADE`, `MOVE_REVENGE`, `MOVE_SMELLING_SALT`, `MOVE_WEATHER_BALL`, `MOVE_DOOM_DESIRE`, `MOVE_FUTURE_SIGHT`.

### 4. Typical Third-Party Calculator Mistakes
*   **Flooring/Integer Errors**: Applying all multipliers in a floating-point formula and rounding at the end, rather than flooring toward zero after *every single integer division* as the decomp does.
*   **Wrong Order of Operations**: Applying the random factor (85-100) *before* STAB and Type Effectiveness. The decomp applies Random last in `Cmd_adjustnormaldamage`.
*   **Physical/Special Split**: Gen 3 predicts purely by TYPE (e.g., Ghost is physical, Dark is special, `MOVE_SHADOW_BALL` uses Attack). Calculators defaulting to Gen 4+ move-specific categorizations.
*   **Crit Bypass Rules**: Failing to realize Gen 3 crits bypass *advantageous* stat changes (ignores attacker's Atk drops and defender's Def boosts), but keeps them if they favor the attacker (e.g., attacker's +2 Atk is retained). Also, failing to ignore Screens on a crit.
*   **Type Order Rounding**: Applying Type 2 weakness before Type 1. Because of truncation, `(Damage * 0.5) * 2` can yield a different number than `(Damage * 2) * 0.5`.
*   **String/Move Names**: Misspelling move constants in Gen 3 datasets. E.g., `MOVE_SONIC_BOOM` ("SonicBoom"), `MOVE_SOLAR_BEAM` ("SolarBeam"), `MOVE_FAINT_ATTACK` ("Faint Attack", not Feint), `MOVE_SMELLING_SALT` (not Smelling Salts).

### 5. Live Audit Factors (HP changed by outside events)
When checking `[min, max]` against actual HP lost across a turn, you must account for all other `gBattleMons` HP modifiers happening between action selection and the end of the turn:
*   **Weather Damage**: `WEATHER_SANDSTORM`, `WEATHER_HAIL`.
*   **Status Damage**: `STATUS1_POISON`, `STATUS1_TOXIC_POISON` (increasing counter), `STATUS1_BURN`.
*   **End of Turn Effects**: Leech Seed, Curse (Ghost type), Nightmare, Wrap/Bind (partial trapping damage).
*   **Delayed Attacks Hitting**: `MOVE_FUTURE_SIGHT` or `MOVE_DOOM_DESIRE` landing on that specific turn.
*   **Healing Items (End of turn or Threshold)**: `ITEM_LEFTOVERS`, `ITEM_SHELL_BELL`, `ITEM_ORAN_BERRY`, `ITEM_SITRUS_BERRY`, Figy/Mago berries (AI triggered mid-turn).
*   **Abilities**: `ABILITY_ROUGH_SKIN`, `ABILITY_LIQUID_OOZE`, `ABILITY_RAIN_DISH`, `ABILITY_SHED_SKIN` (curing status, changing Guts/Marvel Scale mid-turn).
*   **Recoil & Drain**: Double-Edge/Struggle recoil, Jump Kick/Hi Jump Kick crash damage, Absorb/Giga Drain healing the attacker.
*   **Substitute**: Damage was dealt to `STATUS2_SUBSTITUTE`, so the Pokémon's actual HP value did not change.
*   **Self-inflicted Damage**: Hitting oneself in confusion (`STATUS2_CONFUSION`).
*   **AI/Trainer Actions**: The opponent used a Potion/Full Restore mid-turn, or used a healing move (`MOVE_RECOVER`, `MOVE_SOFT_BOILED`, `MOVE_REST`, `MOVE_MILK_DRINK`, `MOVE_SLACK_OFF`, `MOVE_MOONLIGHT`, `MOVE_MORNING_SUN`, `MOVE_SYNTHESIS`, `MOVE_SWALLOW`).
*   **Pain Split**: `MOVE_PAIN_SPLIT` dynamically equalizing HP.