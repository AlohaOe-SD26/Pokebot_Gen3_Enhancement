> ⚠ A NOTE (step 11 prediction support, 2026-09-30). See ../2026-09-30-dmgcalc11-PREDICTIONS.md.

> Derived by a fresh agent FORBIDDEN to read the calculator (decomp only).

# M1a rows: the game's damage, derived by hand from the pret/pokeemerald decomp

Source: pret/pokeemerald `master` @ `f90719c46ce710427cfcae65419a3fa684b34a8a`, fetched 2026-09-30 with
`gh api -H "Accept: application/vnd.github.raw" repos/pret/pokeemerald/contents/<path>`.
Nothing under `sandbox-pokebot` (the calculator under test) was read or run. The arithmetic was re-checked with a
separate 60-line script written from the steps below (`scratchpad/m1_handcheck.py`); it agrees on every row.

File abbreviations: `P` = src/pokemon.c, `BSC` = src/battle_script_commands.c, `BS1` = data/battle_scripts_1.s,
`BM` = src/battle_main.c, `BMV` = src/data/battle_moves.h, `BH` = include/battle.h, `BU` = src/battle_util.c,
`CB` = include/constants/battle.h, `CP` = include/constants/pokemon.h.

All divisions are C integer divisions on non-negative values, so each one floors.

---

## 0. The pipeline, and the lines every row uses

A plain damaging move runs `BS1:241-252`: `attackcanceler, accuracycheck, attackstring, ppreduce, critcalc, damagecalc,
typecalc, adjustnormaldamage`. Effects that route there: EFFECT_HIT (`BS1:21` -> `BS1:236`), PARALYZE_HIT (Spark,
`BS1:370-372`), FLINCH_HIT (Bite, `BS1:668-670`), ACCURACY_DOWN_HIT (Mud-Slap, `BS1:1060-1062`), CONFUSE_HIT (Signal Beam,
`BS1:1071-1073`), QUICK_ATTACK (`BS1:124` maps to BattleScript_EffectHit), RECOIL (Struggle, `BS1:897-901`),
HIDDEN_POWER (`BS1:1740-1742`: `hiddenpowercalc` then goto EffectHit).

Per-move defaults: `gCritMultiplier = 1` and `gBattleScripting.dmgMultiplier = 1` (`BU:91-92` HandleAction_UseMove;
also `BSC:3624-3625` MoveValuesCleanUp); `gBattleStruct->dynamicMoveType = 0`, `gDynamicBasePower = 0` (`BU:677-678`).

1. **CalculateBaseDamage** (`P:3106-3372`). Stage 0 ratio is {10,10} (`P:1876`), so APPLY_STAT_MOD (`P:3100-3104`)
   leaves a stat unchanged. Level factor `2*50/5+2 = 22` at L50 (`P:3246` physical, `P:3301` special).
   Physical if type < TYPE_MYSTERY (9), special if > 9 (`BH:466-467`; type ids `CP:6-23`).
   Physical: `damage = atk` -> `*power` (`P:3245`) -> `*22` (`P:3246`) -> `/def` (`P:3259`) -> `/50` (`P:3260`)
   -> burn halving (`P:3263-3264`) -> Reflect (`P:3267-3273`) -> min 1 (`P:3280-3281`).
   Special: same with spAtk/spDef (`P:3300`, `P:3301`, `P:3314`, `P:3315`), then Light Screen (`P:3318-3324`), then weather
   (`P:3331-3363`). Return `damage + 2` (`P:3371`).
2. **Cmd_damagecalc** (`BSC:1290-1304`): `dmg = B * gCritMultiplier * dmgMultiplier` (`BSC:1296`); then if the attacker
   has STATUS3_CHARGED_UP **and `gBattleMoves[gCurrentMove].type == TYPE_ELECTRIC`** (the move table's static type, not the
   dynamic one), `dmg *= 2` (`BSC:1298-1299`).
3. **Cmd_typecalc** (`BSC:1355-1424`): returns at once for MOVE_STRUGGLE (`BSC:1360-1364`). Move type via GET_MOVE_TYPE
   (`BSC:1366`; macro `BH:458-464`: the dynamic type when one is set). STAB: `dmg = dmg*15; dmg = dmg/10`
   (`BSC:1369-1373`). Then it walks **gTypeEffectiveness in TABLE order** (`BSC:1386-1406`): for each row whose attacking
   type matches, it checks defender type1 (`BSC:1398-1399`) then type2 (`BSC:1401-1403`), each hit calling
   **ModulateDmgByType**: `dmg = dmg*mult/10`, and if that is 0 while mult != 0 it becomes 1 (`BSC:1323-1325`);
   mult 0 sets MOVE_RESULT_DOESNT_AFFECT_FOE (`BSC:1329-1330`). Rows after the TYPE_FORESIGHT sentinel (`BM:445`:
   Normal->Ghost `BM:446`, Fighting->Ghost `BM:447`) are applied only when the target does NOT have Foresight
   (`BSC:1388-1393`).
   **Consequence: the multiplications happen in the order of the table's rows, not in defender type order.** With a
   floor after every step, that order changes the result (rows D-N1 and D-O1).
4. **Cmd_adjustnormaldamage** (`BSC:1658-1698`) calls **ApplyRandomDmgMultiplier** (`BSC:1639-1651`):
   `randPercent = 100 - (Random() % 16)`; if dmg != 0: `dmg = dmg*randPercent/100`, min 1. r=15 -> 85 (min), r=0 -> 100
   (max). No Focus Band/Endure/False Swipe here, so nothing further.
5. **HP is changed only if the move affected the target**: `Cmd_healthbarupdate` (`BSC:1812`) and `Cmd_datahpupdate`
   (`BSC:1862`) both skip on `MOVE_RESULT_NO_EFFECT`, which includes DOESNT_AFFECT_FOE (`CB:223`, `CB:228`). So a type
   immunity deals 0 whatever gBattleMoveDamage holds, and that includes the fixed-damage moves, whose scripts run
   `typecalc` and only clear SE/NVE afterwards (`bicbyte ... SUPER_EFFECTIVE | NOT_VERY_EFFECTIVE`).

Relevant gTypeEffectiveness rows (`BM:335-449`):
`BM:337` NORMAL->ROCK 5 · `BM:338` NORMAL->STEEL 5 · `BM:353` ELECTRIC->WATER 20 · `BM:357` ELECTRIC->FLYING 20 ·
`BM:360` GRASS->WATER 20 · `BM:377` FIGHTING->NORMAL 20 · `BM:380` FIGHTING->FLYING 5 · `BM:383` FIGHTING->ROCK 20 ·
`BM:393` GROUND->ELECTRIC 20 · `BM:399` GROUND->STEEL 20 · `BM:415` BUG->FLYING 5 · `BM:419` BUG->STEEL 5 ·
`BM:427` GHOST->NORMAL 0 (before the Foresight sentinel, so always applied) · `BM:436` DARK->GHOST 20 ·
`BM:437` DARK->DARK 5 · `BM:445` FORESIGHT sentinel · `BM:446` NORMAL->GHOST 0 · `BM:447` FIGHTING->GHOST 0.
There is no row for WATER->DARK, DARK->NORMAL, PSYCHIC->NORMAL, NORMAL->NORMAL or NORMAL->WATER. A missing row means x1.

---

## Group D: B given (the value CalculateBaseDamage returns, +2 included); start at Cmd_damagecalc

### D-A1: Fighting move, attacker Fighting (STAB), defender Normal/Rock, B=3, crit, no Charge
Assumption: "a Fighting move" is any physical Fighting move whose script runs critcalc/damagecalc/typecalc/
adjustnormaldamage (EffectHit, or Brick Break's `BS1:2424-2427` with no screens up); with B given, which one does not matter.
- damagecalc `BSC:1296`: 3 x 2 (crit) x 1 = **6**. Charge: none.
- STAB `BSC:1371-1372`: 6x15 = 90, /10 = **9**.
- Table order: `BM:377` FIGHTING->NORMAL 20 matches type1 (`BSC:1398`): 9x20/10 = **18**.
  `BM:383` FIGHTING->ROCK 20 matches type2 (`BSC:1401`): 18x20/10 = **36**.
- Random `BSC:1646-1647`: 36x85/100 = 30.6 -> **30**; 36x100/100 = **36**.
- **[30, 36]**

### D-A2: Spark (Electric), attacker Electric (STAB), defender Water/Flying, B=3, crit, Charge
Spec note: the row calls Spark "physical in Gen 3". It is not: TYPE_ELECTRIC = 13 (`CP:19`) > TYPE_MYSTERY = 9, so
IS_TYPE_SPECIAL (`BH:467`). With B given this does not change the result, but the label is wrong.
- damagecalc `BSC:1296`: 3 x 2 x 1 = **6**.
- Charge `BSC:1298-1299`: STATUS3_CHARGED_UP set and `gBattleMoves[MOVE_SPARK].type == TYPE_ELECTRIC` (`BMV:2724`) ->
  6x2 = **12**.
- STAB: 12x15 = 180, /10 = **18**.
- `BM:353` ELECTRIC->WATER 20 (type1): 18x20/10 = **36**. `BM:357` ELECTRIC->FLYING 20 (type2): 36x20/10 = **72**.
- Random: 72x85/100 = 61.2 -> **61**; max **72**.
- **[61, 72]**

### D-A3: Mud-Slap (Ground), attacker Water/Ground (STAB), defender Electric/Steel, B=5, crit
- damagecalc: 5 x 2 x 1 = **10**. Charge: not Electric.
- STAB (attacker type2 = Ground, IS_BATTLER_OF_TYPE `BH:471`): 10x15 = 150, /10 = **15**.
- Levitate check `BSC:1375` does not fire (no ability of note).
- `BM:393` GROUND->ELECTRIC 20 (type1): 15x20/10 = **30**. `BM:399` GROUND->STEEL 20 (type2): 30x20/10 = **60**.
- Random: 60x85/100 = **51**; max **60**.
- **[51, 60]**

### D-N1: Bite (Dark), attacker Dark (STAB), defender Dark/Ghost, B=5, no crit
- damagecalc: 5 x 1 x 1 = **5**.
- STAB: 5x15 = 75, /10 = 7.5 -> **7**.
- **Table order**: `BM:436` DARK->GHOST 20 comes BEFORE `BM:437` DARK->DARK 5.
  `BM:436` matches type2 (Ghost): 7x20/10 = **14**. Then `BM:437` matches type1 (Dark): 14x5/10 = **7**.
- Random: 7x85/100 = 5.95 -> **5**; 7x100/100 = **7**.
- **[5, 7]**
- (Trap: applying defender type order instead (Dark x0.5 first: 7x5/10 = 3, then x2 = 6) gives [5, **6**]. The game
  gives 7 at the max roll.)

### D-N2: Signal Beam (Bug), attacker Water (no STAB), defender Steel/Flying, B=2, no crit
- damagecalc: **2**. No STAB (`BSC:1369` false).
- Table order: `BM:415` BUG->FLYING 5 (type2) comes before `BM:419` BUG->STEEL 5 (type1).
  2x5/10 = **1**. Then 1x5/10 = 0 -> mult != 0 so it becomes **1** (`BSC:1324-1325`).
- Random: 1x85/100 = 0 -> dmg was non-zero so it is floored back to **1** (`BSC:1648-1649`); max **1**.
- **[1, 1]** (the order does not matter here: both orders give 1)

### D-O1: Fighting move, attacker Water (no STAB), defender Rock/Flying, B=3, no crit
- damagecalc: **3**. No STAB.
- **Table order**: `BM:380` FIGHTING->FLYING 5 comes BEFORE `BM:383` FIGHTING->ROCK 20.
  `BM:380` matches type2 (Flying): 3x5/10 = 1.5 -> **1**. Then `BM:383` matches type1 (Rock): 1x20/10 = **2**.
- Random: 2x85/100 = 1.7 -> **1**; max **2**.
- **[1, 2]**
- (Trap: defender type order (Rock x2 first: 6, then x0.5 = 3) gives [2, 3]. Both ends differ from the game.)

---

## Group B: the full calculation

Common: L50 -> level factor 22 (`P:3246`/`P:3301`). No items, stages 0, no crit (gCritMultiplier 1), dmgMultiplier 1,
no weather unless stated, no badges unless stated. `ShouldGetStatBadgeBoost` (`P:3407-3419`) returns FALSE for every
non-player-side battler (`P:3411-3412`), and with the badge flag clear it returns FALSE anyway (`P:3415-3418`).
Assumption for every Group B row: an ordinary single battle (not link, e-Reader, recorded link, Frontier, or Secret Base).

### B-MS1: Tackle (Normal 35, `BMV:432-436`, EFFECT_HIT). Ours L50 Atk 100 Water, healthy. Foe Def 100 Water, Marvel Scale, BURNED
- Marvel Scale `P:3213-3214`: defender ability MARVEL_SCALE and status1 != 0 -> defense = 150x100/100 = **150**.
- Physical (Normal=0). `P:3243` damage = 100; `P:3245` x35 = 3500; `P:3246` x22 = 77000; `P:3259` /150 = 513.33 ->
  **513**; `P:3260` /50 = 10.26 -> **10**. Attacker not burned (`P:3263`). No Reflect. +2 (`P:3371`) -> **B = 12**.
- damagecalc: 12x1x1 = 12. typecalc: no STAB (attacker Water, move Normal); no NORMAL->WATER row -> **12**.
- Random: 12x85/100 = 10.2 -> **10**; max **12**.
- **[10, 12]**

### B-MS2: Tackle. Ours L50 Atk 100 Water, POISONED. Foe Def 100 Water, Marvel Scale, healthy
- Marvel Scale needs the DEFENDER's status1 (`P:3213`); the defender is healthy -> defense stays 100. The attacker's
  poison changes nothing (only BURN is checked, `P:3263`).
- 100x35 = 3500; x22 = 77000; /100 = **770**; /50 = 15.4 -> **15**; +2 -> **B = 17**.
- typecalc: no STAB, neutral -> **17**.
- Random: 17x85/100 = 14.45 -> **14**; max **17**.
- **[14, 17]**

### B-GUTS: Quick Attack (Normal 40, `BMV:1277-1281`; EFFECT_QUICK_ATTACK -> BattleScript_EffectHit `BS1:124`). Ours L50 Atk 100 Normal, GUTS, BURNED. Foe Def 100 Water
- Guts `P:3211-3212`: ability GUTS and status1 != 0 -> attack = 150x100/100 = **150**.
- 150x40 = 6000; x22 = 132000; /100 = **1320**; /50 = 26.4 -> **26**.
- Burn halving `P:3263-3264`: attacker is burned BUT its ability is GUTS -> **no halving**. +2 -> **B = 28**.
- damagecalc: 28. STAB (attacker Normal, move Normal): 28x15 = 420, /10 = **42**. No NORMAL->WATER row -> 42.
- Random: 42x85/100 = 35.7 -> **35**; max **42**.
- **[35, 42]**

### B-BB: Brick Break (Fighting 75, `BMV:3643-3647`, EFFECT_BRICK_BREAK). Ours L50 Atk 100 Fighting. Foe Def 100 Normal, REFLECT on the foe's side
- Script `BS1:2418-2427`: `removelightscreenreflect` runs **before** `critcalc`/`damagecalc`.
  `Cmd_removelightscreenreflect` (`BSC:9883-9903`): if the opposing side's reflectTimer or lightscreenTimer is non-zero,
  it clears SIDE_STATUS_REFLECT and SIDE_STATUS_LIGHTSCREEN (`BSC:9887-9890`).
  Assumption: Reflect was set the normal way, so `reflectTimer = 5` (`BSC:6706-6707`), which is non-zero.
- damagecalc reads `sideStatus` afresh (`BSC:1292`), and Reflect is already gone -> `P:3267` is false.
- 100x75 = 7500; x22 = 165000; /100 = **1650**; /50 = **33**; no burn; no Reflect; +2 -> **B = 35**.
- STAB: 35x15 = 525, /10 = **52**. `BM:377` FIGHTING->NORMAL 20 (type1; the foe is mono-Normal, so type2 == type1 and the
  second check is skipped, `BSC:1402`): 52x20/10 = **104**.
- Random: 104x85/100 = 88.4 -> **88**; max **104**.
- `typecalc2` in the hit half (`BS1:2437`, `BSC:4500-4594`) only sets flags; it does not touch gBattleMoveDamage.
- **[88, 104]**
- (For reference only: if Reflect had applied, B = 33/2 + 2 = 18 -> [45, 54]. The game does not do that here.)

### B-KI110: FOE Water Gun (Water 40, `BMV:718-722`, EFFECT_HIT) on OURS. Foe L50 SpAtk 100 Water; ours SpDef 100, HP 200, Dark
Water is special (11 > 9).
- Badge checks (`P:3161-3168`) only ever look at BADGE01 (attacker Atk), BADGE05 (defender Def) and BADGE07 (attacker
  SpAtk `P:3165`, defender SpDef `P:3167`). **BADGE08 is not referenced anywhere in CalculateBaseDamage**; the only
  BADGE08 use in battle code is obedience (`BU:3930`).
- The attacker is the foe: `ShouldGetStatBadgeBoost(..., foe)` -> `GetBattlerSide != B_SIDE_PLAYER` -> FALSE (`P:3411-3412`).
  No foe stat is ever badge-boosted.

**(a) BADGE07 set, BADGE08 clear.** The defender is ours (player side) and FLAG_BADGE07_GET is set -> `P:3167-3168`:
spDefense = 110x100/100 = **110**.
- 100x40 = 4000; x22 = 88000; /110 = **800**; /50 = **16**; no Light Screen; no weather; +2 -> **B = 18**.
- STAB (foe Water, move Water): 18x15 = 270, /10 = **27**. No WATER->DARK row -> 27.
- Random: 27x85/100 = 22.95 -> **22**; max **27**.
- **[22, 27]**

**(b) BADGE08 set, BADGE07 clear.** No badge applies -> spDefense **100**.
- 88000/100 = **880**; /50 = 17.6 -> **17**; +2 -> **B = 19**.
- STAB: 19x15 = 285, /10 = **28**. Neutral.
- Random: 28x85/100 = 23.8 -> **23**; max **28**.
- **[23, 28]**

### B-KI111: Solarbeam (Grass 120, `BMV:991-995`, EFFECT_SOLAR_BEAM). Ours L50 SpAtk 100 Grass; foe SpDef 100 Water; RAIN on the damage turn
- Script: under rain it is not the sun shortcut (`BS1:1906`), so turn 1 charges (`BS1:1907-1912`) and turn 2 runs
  `BattleScript_TwoTurnMovesSecondTurn` (`BS1:785-793`) -> `BattleScript_HitFromAccCheck` -> critcalc/damagecalc/typecalc/
  adjustnormaldamage (`BS1:243-252`).
- Grass is special (12 > 9). 100x120 = 12000; x22 = 264000; /100 = **2640**; /50 = 52.8 -> **52**.
- Weather `P:3331` (no Cloud Nine/Air Lock). `P:3334` rain-temporary block: switch only on FIRE/WATER -> nothing for Grass.
  `P:3348-3349`: `gBattleWeather & B_WEATHER_RAIN` (`CB:235`: temporary|downpour|permanent, so any rain) and
  `gCurrentMove == MOVE_SOLAR_BEAM` -> 52/2 = **26**. +2 -> **B = 28**.
- STAB (Grass): 28x15 = 420, /10 = **42**. `BM:360` GRASS->WATER 20: 42x20/10 = **84**.
- Random: 84x85/100 = 71.4 -> **71**; max **84**.
- **[71, 84]**
- (For reference: without the rain halving, B = 54 -> [137, 162].)

### B-STR: Struggle (Normal 50, `BMV:2148-2152`, EFFECT_RECOIL -> EffectHit `BS1:897-901`). Ours L50 Atk 100 Normal; foe Def 100, HP 200, Ghost
- 100x50 = 5000; x22 = 110000; /100 = **1100**; /50 = **22**; +2 -> **B = 24**.
- damagecalc: 24.
- **typecalc returns immediately for MOVE_STRUGGLE** (`BSC:1360-1364`): no STAB (even though the attacker is Normal), no
  type chart, so Normal->Ghost (`BM:446`) is never consulted and no DOESNT_AFFECT_FOE flag is set -> **24**.
- Random: 24x85/100 = 20.4 -> **20**; max **24**.
- **[20, 24]** (it hits the Ghost; the 1/4 recoil is not part of this number)

### B-HP: Hidden Power (`BMV:3084-3088`: power 1, type NORMAL, EFFECT_HIDDEN_POWER). Ours L50 SpAtk 100 Normal, all IVs 31; foe SpDef 100 Normal
- `Cmd_hiddenpowercalc` (`BSC:8889-8915`):
  - powerBits (`BSC:8891-8896`): each stat contributes `(IV & 2)`, so 31 = 0b11111 sets every bit -> **63**.
  - typeBits (`BSC:8898-8903`): each stat contributes `(IV & 1)`, order HP, Atk, Def, Spe, SpA, SpD -> **63**.
  - power `BSC:8905`: 40x63/63 + 30 = **70**.
  - type `BSC:8909`: (NUMBER_OF_MON_TYPES - 3) x 63 / 63 + 1 = (18-3) + 1 = **16** (`CP:24` NUMBER_OF_MON_TYPES 18);
    `BSC:8910-8911`: 16 >= TYPE_MYSTERY -> 17 = **TYPE_DARK** (`CP:23`). Flags added in `BSC:8912`.
  - **Hidden Power: Dark, 70.**
- CalculateBaseDamage gets `powerOverride = gDynamicBasePower = 70` (`BSC:1294`, `P:3122`) and
  `type = dynamicMoveType & DYNAMIC_TYPE_MASK = Dark` (`P:3127`, `BH:454`) -> Dark (17 > 9) is **special**.
- 100x70 = 7000; x22 = 154000; /100 = **1540**; /50 = 30.8 -> **30**; +2 -> **B = 32**.
- damagecalc: 32 (no Charge). typecalc uses the dynamic type (`BH:460-461`): Dark; the attacker is Normal -> no STAB.
  No DARK->NORMAL row -> **32**.
- Random: 32x85/100 = 27.2 -> **27**; max **32**.
- **Dark 70, [27, 32]**

### B-HPC: Hidden Power Electric, CHARGED. Ours L50 SpAtk 100 Normal; foe SpDef 100 Water
- **IVs chosen: HP 31, Atk 31, Def 31, Spe 31, SpA 30, SpD 31.**
  - typeBits = 1 (HP) + 2 (Atk) + 4 (Def) + 8 (Spe) + 0 (SpA 30 is even, so bit 4 = 16 is clear) + 32 (SpD) = **47**. `BSC:8909`: 15x47/63 + 1 = 705/63 = 11 -> **12**;
    `BSC:8910-8911`: 12 >= 9 -> **13 = TYPE_ELECTRIC** (`CP:19`).
    (Only typeBits 47..50 give Electric: 46 -> 690/63 = 10 -> 11 -> 12 Grass; 51 -> 765/63 = 12 -> 13 -> 14 Psychic.)
  - powerBits: 30 = 0b11110 still has bit 1 set, so every stat contributes -> 63 -> power **70** (`BSC:8905`).
- CalculateBaseDamage: type Electric (13 > 9) -> **special**; power 70.
  100x70 = 7000; x22 = 154000; /100 = 1540; /50 = **30**; +2 -> **B = 32**.
- damagecalc `BSC:1296`: 32x1x1 = 32.
  **Charge `BSC:1298`: tests `gBattleMoves[gCurrentMove].type == TYPE_ELECTRIC`, the static table type. Hidden Power's
  table type is TYPE_NORMAL (`BMV:3088`), so the x2 does NOT apply.** -> **32**.
- typecalc: dynamic type Electric; the attacker is Normal -> no STAB. `BM:353` ELECTRIC->WATER 20: 32x20/10 = **64**.
- Random: 64x85/100 = 54.4 -> **54**; max **64**.
- **Electric 70, [54, 64]**
- (Trap: applying Charge to a dynamic-Electric Hidden Power gives [108, 128]. The game does not.)

### B-SONIC: Sonicboom (`BMV:640-644`: Normal, EFFECT_SONICBOOM). Ours L30 Normal; foe HP 200 Normal
- Script `BS1:1720-1729`: `typecalc` (`BS1:1725`): no NORMAL->NORMAL row, so no immunity flag (whatever it does to the
  stale damage is overwritten next). `bicbyte` clears SE/NVE only (`BS1:1726`). `setword gBattleMoveDamage, 20`
  (`BS1:1727`). `adjustsetdamage` (`BSC:5861-5899`): no Focus Band, Endure or False Swipe -> unchanged, and **no random
  factor** (it never calls ApplyRandomDmgMultiplier).
- **20** (fixed; no random factor)

### B-PSY: Psywave (`BMV:1940-1944`: Psychic, EFFECT_PSYWAVE). Ours L30 Psychic; foe HP 200 Normal
- Script `BS1:1206-1215`: typecalc (no PSYCHIC->NORMAL row -> neutral, no flag), `psywavedamageeffect`, `adjustsetdamage`
  (no random factor).
- `Cmd_psywavedamageeffect` (`BSC:7932-7941`): `while ((randDamage = Random() % 16) > 10);` -> randDamage uniform on
  0..10 (`BSC:7936`); `randDamage *= 10` (`BSC:7938`); `damage = level x (randDamage + 50) / 100` (`BSC:7939`).
  L30: 30x50/100 = **15** ... 30x150/100 = **45**, in steps of 3.
- **Psywave's own range [15, 45]**: the 11 equiprobable values {15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45}. There is
  no 85-100% factor.

### B-NS: Night Shade (`BMV:1316-1320`: **Ghost**, EFFECT_LEVEL_DAMAGE). Ours L30 Ghost; foe HP 200 Normal
- Script `BS1:1195-1204`: typecalc (`BS1:1200`): `BM:427` GHOST->NORMAL **0** sits BEFORE the Foresight sentinel, so it is
  always applied -> ModulateDmgByType(0) sets MOVE_RESULT_DOESNT_AFFECT_FOE (`BSC:1329-1330`). `bicbyte` (`BS1:1201`)
  does not clear it. `dmgtolevel` (`BSC:7926-7929`) writes 30 into gBattleMoveDamage, but `Cmd_datahpupdate` skips the HP
  change on MOVE_RESULT_NO_EFFECT (`BSC:1862`).
- **0 (immune: "It doesn't affect...")**. (Would have been 30 if the immunity were missed.)

### B-ST: Seismic Toss (`BMV:900-904`: **Fighting**, EFFECT_LEVEL_DAMAGE). Ours L30 Fighting; foe HP 200 Ghost
- typecalc: FIGHTING->GHOST 0 is `BM:447`, after the sentinel `BM:445`; the foe has no Foresight, so the loop continues past
  the sentinel (`BSC:1388-1393`) and applies it -> DOESNT_AFFECT_FOE. The dmgtolevel value (30) is never applied (`BSC:1862`).
- **0 (immune)**. (Would have been 30.)

### B-SF: Super Fang (`BMV:2109-2113`: **Normal**, EFFECT_SUPER_FANG). Ours L30 Normal; foe current HP 200, Ghost
- Script `BS1:809-817`: typecalc (`BS1:814`): `BM:446` NORMAL->GHOST 0 (after the sentinel, no Foresight) ->
  DOESNT_AFFECT_FOE. `damagetohalftargethp` (`BSC:7577-7584`) would write 200/2 = 100; not applied (`BSC:1862`).
- **0 (immune)**. (Would have been 100.)

---

## Summary table

| Row | Game damage | Key step |
|---|---|---|
| D-A1 | [30, 36] | 3x2 crit = 6 -> STAB 9 -> x2 x2 = 36 |
| D-A2 | [61, 72] | crit 6 -> Charge x2 = 12 (Spark's table type is Electric) -> STAB 18 -> x2 x2 = 72. The spec's "physical" is wrong: Electric is special. |
| D-A3 | [51, 60] | crit 10 -> STAB 15 -> x2 x2 = 60 |
| D-N1 | [5, 7] | STAB 7; the TABLE order applies DARK->GHOST x2 (14) before DARK->DARK x0.5 = 7. Defender order would give 6. |
| D-N2 | [1, 1] | 2 -> x0.5 = 1 -> x0.5 = 0 -> 1 (floor-to-1 in ModulateDmgByType); random 0 -> 1 |
| D-O1 | [1, 2] | the TABLE order applies FIGHTING->FLYING x0.5 (3 -> 1) before FIGHTING->ROCK x2 = 2. Defender order would give 3. |
| B-MS1 | [10, 12] | Marvel Scale (burned defender): Def 150 -> 77000/150 = 513 /50 = 10 +2 |
| B-MS2 | [14, 17] | no Marvel Scale (the defender is healthy; the attacker's poison is irrelevant) -> 15 +2 = 17 |
| B-GUTS | [35, 42] | Guts Atk 150, and burn does NOT halve under Guts -> 26+2 = 28 -> STAB 42 |
| B-BB | [88, 104] | removelightscreenreflect runs before damagecalc, so no Reflect -> 35 -> STAB 52 -> x2 = 104 |
| B-KI110 (BADGE07 set) | [22, 27] | our (player-side) defender's SpDef x1.1 = 110 -> 800/50 = 16 +2 = 18 -> STAB 27 |
| B-KI110 (BADGE08 set, 07 clear) | [23, 28] | BADGE08 is not in CalculateBaseDamage -> SpDef 100 -> 17 +2 = 19 -> STAB 28 |
| B-KI111 | [71, 84] | rain halves Solarbeam after /50: 52 -> 26 +2 = 28 -> STAB 42 -> x2 = 84 |
| B-STR | [20, 24] | typecalc returns at once for Struggle: no STAB, no Ghost immunity -> 24 |
| B-HP | Dark 70, [27, 32] | all IVs 31 -> typeBits 63 -> 16 -> 17 Dark; power 70; special, no STAB -> 32 |
| B-HPC | Electric 70, [54, 64] | IVs 31/31/31/31/SpA30/31 (typeBits 47); Charge NOT applied (it tests the static type, Normal); x2 vs Water -> 64 |
| B-SONIC | 20 (no random) | setword 20; adjustsetdamage has no random factor |
| B-PSY | [15, 45] (11 values, step 3) | L30 x (50..150 step 10)/100 |
| B-NS | 0 | Ghost -> Normal x0 (`BM:427`, before the Foresight sentinel) |
| B-ST | 0 | Fighting -> Ghost x0 (`BM:447`, no Foresight) |
| B-SF | 0 | Normal -> Ghost x0 (`BM:446`, no Foresight) |

## Assumptions stated
1. Ordinary single battle: not link, e-Reader, recorded link, Frontier, or Secret Base (these would disable badge boosts,
   `P:3409-3414`). No Cloud Nine/Air Lock on the field. No Mud/Water Sport. The target has no Foresight, Substitute,
   Levitate or Wonder Guard, and holds no item.
2. D-A1 and D-O1 "a Fighting move": any Fighting move whose script uses critcalc/damagecalc/typecalc/adjustnormaldamage.
   With B given, the identity of the move does not matter.
3. B-BB: Reflect was set normally (reflectTimer 5, non-zero), so Brick Break removes it. If the Reflect bit were set with a
   zero timer (an inconsistent state), Reflect would stay and the result would be [45, 54].
4. B-KI111: "rain" is any of B_WEATHER_RAIN's bits. The Solarbeam halving (`P:3348`) uses the full B_WEATHER_RAIN mask, so
   Rain Dance and permanent rain behave the same for this Grass move.
5. B-HPC: IVs 31/31/31/31/30/31 (HP/Atk/Def/Spe/SpA/SpD). Any typeBits 47-50 gives Electric. Power is 70 while every IV has
   bit 1 set.
6. D-A2: the row's "physical in Gen 3" label is wrong (Electric is special). This is harmless because B is given.


## Appendix: the agent's arithmetic cross-check script (m1_handcheck.py)

```python
# arithmetic re-check of the hand derivation (C integer semantics, all values non-negative)
def rnd(d):
    out=[]
    for pct in (85,100):
        x=d*pct//100
        if d!=0 and x==0: x=1
        out.append(x)
    return out
def mod(d,m):
    d=d*m//10
    if d==0 and m!=0: d=1
    return d
def stab(d): return d*15//10
def base(a,p,lvl,dfn): return a*p*(2*lvl//5+2)//dfn//50
# Group D
print("D-A1", rnd(mod(mod(stab(3*2),20),20)))
print("D-A2", rnd(mod(mod(stab(3*2*2),20),20)))
print("D-A3", rnd(mod(mod(stab(5*2),20),20)))
print("D-N1 table", rnd(mod(mod(stab(5),20),5)), "def-order", rnd(mod(mod(stab(5),5),20)))
print("D-N2 table", rnd(mod(mod(2,5),5)))
print("D-O1 table", rnd(mod(mod(3,5),20)), "def-order", rnd(mod(mod(3,20),5)))
# Group B
print("MS1", rnd(base(100,35,50,100*150//100)+2))
print("MS2", rnd(base(100,35,50,100)+2))
print("GUTS", rnd(stab(base(100*150//100,40,50,100)+2)))
print("BB", rnd(mod(stab(base(100,75,50,100)+2),20)))
print("BB-if-reflect-kept", rnd(mod(stab(base(100,75,50,100)//2+2),20)))
print("KI110 b7", rnd(stab(base(100,40,50,110*100//100)+2)), "b8", rnd(stab(base(100,40,50,100)+2)))
print("KI111", rnd(mod(stab(base(100,120,50,100)//2+2),20)), "no-rain", rnd(mod(stab(base(100,120,50,100)+2),20)))
print("STR", rnd(base(100,50,50,100)+2))
# hidden power
def hp(ivs):
    h,a,d,s,sa,sd=ivs
    pb=((h&2)>>1)|((a&2)<<0)|((d&2)<<1)|((s&2)<<2)|((sa&2)<<3)|((sd&2)<<4)
    tb=((h&1)<<0)|((a&1)<<1)|((d&1)<<2)|((s&1)<<3)|((sa&1)<<4)|((sd&1)<<5)
    pw=40*pb//63+30
    t=15*tb//63+1
    if t>=9: t+=1
    return pw,t,pb,tb
print("HP all31", hp((31,)*6))
print("HPC ivs", hp((31,31,31,31,30,31)))
for tb in range(64):
    t=15*tb//63+1
    if t>=9:t+=1
    if t==13: print("elec typeBits",tb)
print("HP dmg", rnd(base(100,70,50,100)+2))
print("HPC dmg", rnd(mod(base(100,70,50,100)+2,20)), "if charge applied", rnd(mod((base(100,70,50,100)+2)*2,20)))
print("PSY", sorted({30*(k*10+50)//100 for k in range(11)}))

```
