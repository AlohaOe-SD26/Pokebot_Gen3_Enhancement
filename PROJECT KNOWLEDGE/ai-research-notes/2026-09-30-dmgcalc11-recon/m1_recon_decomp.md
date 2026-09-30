> ⚠ **A NOTE, NOT A SOURCE OF TRUTH.** Output of one agent of the design v2 step 11 recon (2026-09-30, a workflow of five fresh Claude agents; decomp read at pret/pokeemerald f90719c4). The design that uses it is `../2026-09-30-dmgcalc11-DESIGN.md`, whose author re-read every load-bearing claim it relies on (marked ✔ there). Line numbers are as of branch `wt/dmgcalc11` at `241929d7`. Scratch scripts it mentions were not committed.

# M1 recon: the decomp's damage formula, transcribed, and an adversarial check of the Gemini note

**Angle:** the decomp, transcribed. **Status: a NOTE, not truth.** Every decomp line below was read by me from
`pret/pokeemerald` **master `f90719c46ce7` (2026-09-29)**, fetched fresh with `gh api -H "Accept: application/vnd.github.raw"`
into private copies (`scratchpad/decomp/m1_*`). The shared `scratchpad/decomp/` folder also holds other agents' copies
under other names, and I did not use them. "Our code" lines are from the worktree `C:/Remote Projects/pokebot-wt-ch24`
(branch `wt/dmgcalc11`), which I did not modify.

File abbreviations: `pokemon.c` = `src/pokemon.c`; `bsc.c` = `src/battle_script_commands.c`; `bmain.c` = `src/battle_main.c`;
`butil.c` = `src/battle_util.c`; `bs1.s` = `data/battle_scripts_1.s`; `battle.h` = `include/battle.h`;
`c_battle.h` = `include/constants/battle.h`; `_util.py` = `sandbox-pokebot/modules/battle_strategies/_util.py`.

---

## 0. The findings that matter most for the design

1. **The crit ×2 multiplies CalculateBaseDamage's RETURN, including the +2, BEFORE STAB, type and random**
   (`bsc.c:1293-1296`, then `typecalc` `bs1.s:251` → `bsc.c:1369-1373`, then `adjustnormaldamage` `bs1.s:252` →
   `bsc.c:1662`). Our code doubles **after** STAB and type (`_util.py:208-213`, then `:230-231`). Over every base value
   2..1000, with the same base in both, my arithmetic (`scratchpad/m1calc/order_check.py`) finds that our code
   **under-predicts crit_max by up to 4 HP** (crit, STAB, ×4; every odd base) and non-crit max by up to 1 HP. It never
   over-predicts. So M1a has a known, bounded, **systematic** crit-order error to report. Gemini put the crit on the
   level term, which is wrong.
2. **Type effectiveness is applied in `gTypeEffectiveness` TABLE order, not types[0] then types[1]**
   (`bsc.c:1386-1406` walks `bmain.c:335-448` row by row). Each step also floors a zero result to 1
   (`bsc.c:1323-1325`). Our code loops over the defender's types (`_util.py:212-213`), with no floor to 1. That costs
   up to 1 HP when a ×2 and a ×0.5 are mixed. Real cases: Grass vs **Nincada** `{BUG, GROUND}`
   (`species_info.h:8347`): the table does Ground ×2 (`bmain.c:363`) before Bug ×0.5 (`:365`), and ours does Bug first.
   Grass vs **Aron** `{STEEL, ROCK}` (`species_info.h:10777`; rows `:366` before `:368`) is the same.
3. **Random factor:** `randPercent = 100 - (Random() % 16)`, so 16 equally likely values from 85 to 100. Then
   `dmg = dmg * randPercent / 100`, floored to 1 **only if dmg was nonzero** (`bsc.c:1639-1651`). It runs **last**,
   after STAB and type (`bs1.s:249-252`). So max = the post-type value exactly, and min = ⌊0.85·value⌋. Our `:242`
   matches this.
4. **Fixed-damage moves run `typecalc` BEFORE setting the damage** (`bs1.s:1725-1727` Sonicboom, `:824-826` Dragon
   Rage, `:1200-1202` Level Damage, `:1211-1213` Psywave, `:814-816` Super Fang). So type immunity, Levitate and
   Wonder Guard still block them. `adjustsetdamage` has **no random factor** (`bsc.c:5861-5899`).
   - **Psywave** = `level * (50 + 10k) / 100`, with k uniform over 0..10 (rejection sampling, `bsc.c:7936-7939`). So
     min = `level*50//100` and max = `level*150//100`. Our `:228` sets min = `level`. **That is wrong, and it is not in
     KI-109** (KI-109 covers the name only). The max is right.
   - **Super Fang** = `hp/2`, min 1 (`bsc.c:7579-7581`). Its script has no `adjustsetdamage`, so Focus Band and Endure
     are not rolled.
5. **Burn halving is inside CalculateBaseDamage.** It applies to physical moves only, before screens and before the
   +2, and **Guts exempts it** (`pokemon.c:3262-3264`). Our `:445-446` has no Guts exemption, so it under-predicts a
   burned Guts attacker by about 2×. Facade's ×2 is `sDMG_MULTIPLIER` (`bs1.s:2252-2257`), applied in
   `Cmd_damagecalc` (`bsc.c:1296`). A burned Facade user without Guts is still halved.
6. **Marvel Scale is keyed on the DEFENDER's status in the decomp** (`pokemon.c:3213`: `defender->status1`). **Our
   `_util.py:399` tests `attacker_status`.** This is a NEW bug, not in KI-109/110/111. When we are statused and a
   healthy Marvel Scale foe is not, we under-predict.
7. **`dmgMultiplier` = 2 doubles the WHOLE damage** (`bsc.c:1296`), and our calculator models none of these cases:
   - Facade (`bs1.s:2257`), SmellingSalt (`:2274`), Revenge (`bsc.c:9339-9347`), Weather Ball in weather
     (`bsc.c:9787-9792`, which also changes the type);
   - Gust/Twister vs Fly (`bs1.s:1895`, `:1829`), Earthquake/Magnitude vs Dig (`:1843`), Surf/Whirlpool vs Dive
     (`:240`, `:834`);
   - Stomp-effect moves vs Minimize (`:1900`), Pursuit on a switch (`:3091`).

   Multi-hit moves re-roll crit, damage and random on **every** hit (`bs1.s:617-624`). All of these must stay outside
   the M1 whitelist.
8. **What the foe "actually lost" is `min(dmg, hp)`** (`bsc.c:1920-1929`). A Substitute absorbs the hit
   (`bsc.c:1865-1892`). **Focus Band, Endure and False Swipe clamp the damage to hp-1** (`bsc.c:1677-1696`). M1b
   already excludes held items. It should also exclude **our False Swipe** and **a foe that knows Endure**.
9. **Design gap in M1b (my inference from the mechanism, not a decomp line saying so):** the damage reads the
   attacker's `hp`, `status1` and stat stages, and the weather, **at hit time** (`pokemon.c:3100-3104`,
   `:3211-3226`, `:3331`). If the foe moves first and drops **our** HP to ≤ maxHP/3, our Overgrow/Blaze/Torrent turns
   on and the power is ×1.5 (`pokemon.c:3219-3224`). That is exactly our **starter's** ability. A crit then exceeds a
   crit_max computed at selection time by up to 50%, which would fail the acceptance "for good". Suggested
   exclusions: our pinch-state or status1 differs between the reads; the weather differs; the foe's Def/SpDef stage
   differs between the reads.
10. **Badge boosts** (`pokemon.c:3161-3168`, `:3407-3419`) apply only to the **player side**, and never in link,
    e-Reader, recorded-link or Frontier battles or against Secret Base trainers:
    - BADGE01 → our Atk;
    - BADGE05 → our Def;
    - BADGE07 → our SpAtk **and** our SpDef (KI-110 confirmed);
    - Speed is BADGE03, in the turn-order code (`bmain.c:4640-4645`).

---

## 1. The integer-exact specification: a standard damaging move in singles

The script for `EFFECT_HIT` is (`bs1.s:236-269`): `attackcanceler`, `accuracycheck`, `attackstring`, `ppreduce`,
**`critcalc` → `damagecalc` → `typecalc` → `adjustnormaldamage`** (`:249-252`), then `attackanimation` …
`healthbarupdate` → **`datahpupdate`** (`:259-260`). Before each move, `gCritMultiplier = 1` and `dmgMultiplier = 1`
(`butil.c:91-92`; `movevaluescleanup` `bsc.c:3621-3625`). All arithmetic is C integer arithmetic (`s32`, truncation;
the values are non-negative, so this is a floor). `/` below means floor division.

### 1a. `Cmd_critcalc` (`bsc.c:1253-1288`)
- **Stage** (`:1267-1274`), summed from:
  - 2 × Focus Energy;
  - +1 each for EFFECT_HIGH_CRITICAL, SKY_ATTACK, BLAZE_KICK and POISON_TAIL;
  - +1 for Scope Lens;
  - +2 for Lucky Punch on Chansey and +2 for Stick on Farfetch'd.

  The stage is capped at 4 (`:1276-1277`).
- **Chance** = 1 / `sCriticalHitChance[stage]`, where the table is `{16, 8, 4, 3, 2}` (`bsc.c:606`).
- **No crit** if the target has Battle Armor or Shell Armor, if `STATUS3_CANT_SCORE_A_CRIT` is set, or in the Wally
  tutorial or FIRST_BATTLE (`:1279-1282`).
- The result is the global `gCritMultiplier = 2` or `1` (`:1283-1285`). It is not a flag in `gBattleStruct`.

### 1b. `CalculateBaseDamage` (`pokemon.c:3106-3372`, the spec's range is exact)

Inputs: attacker, defender, move, `sideStatus = gSideStatuses[side of TARGET]` (`bsc.c:1292`),
`powerOverride = gDynamicBasePower`, `typeOverride = dynamicMoveType` (`bsc.c:1293-1295`).

| # | Operation (in order) | Decomp line | Side |
|---|---|---|---|
| 1 | `power = gBattleMoves[move].power`, or the override if nonzero | 3119-3122 | move |
| 2 | `type = gBattleMoves[move].type`, or `typeOverride & 0x3F` | 3124-3127 | move |
| 3 | `attack = atk.attack; defense = def.defense; spAttack = atk.spAttack; spDefense = def.spDefense` (u16 locals) | 3129-3132 | both |
| 4 | Huge Power / Pure Power: `attack *= 2` | 3158-3159 | attacker ability |
| 5 | BADGE01 (attacker on the player side): `attack = 110*attack/100` | 3161-3162 | attacker |
| 6 | BADGE05 (defender on the player side): `defense = 110*defense/100` | 3163-3164 | defender |
| 7 | BADGE07 (attacker on the player side): `spAttack = 110*spAttack/100` | 3165-3166 | attacker |
| 8 | BADGE07 (defender on the player side): `spDefense = 110*spDefense/100` | 3167-3168 | defender |
| 9 | Type-boost item matching the move type: physical → `attack = attack*(param+100)/100`, else the same on `spAttack`. `param` is 10 for most items (e.g. Charcoal `items.h:2645`) and **5 for Sea Incense** (`items.h:2709`) | 3171-3182 | attacker item |
| 10 | Choice Band: `attack = 150*attack/100` | 3185-3186 | attacker item |
| 11 | Soul Dew (Latias/Latios, not Frontier): `spAttack = 150*spAttack/100` | 3187-3188 | attacker item |
| 12 | Soul Dew (defender): `spDefense = 150*spDefense/100` | 3189-3190 | defender item |
| 13 | Deep Sea Tooth (Clamperl): `spAttack *= 2` | 3191-3192 | attacker item |
| 14 | Deep Sea Scale (Clamperl): `spDefense *= 2` | 3193-3194 | defender item |
| 15 | Light Ball (Pikachu): `spAttack *= 2` (Sp. Atk only in Gen 3) | 3195-3196 | attacker item |
| 16 | Metal Powder (Ditto): **`defense *= 2`** | 3197-3198 | defender item |
| 17 | Thick Club (Cubone/Marowak): `attack *= 2` | 3199-3200 | attacker item |
| 18 | **Defender** Thick Fat and a Fire or Ice move: `spAttack /= 2` | 3203-3204 | defender ability, acts on the attacker's stat |
| 19 | Hustle: `attack = 150*attack/100` | 3205-3206 | attacker ability |
| 20 | Plus when ABILITY_ON_FIELD2(Minus): `spAttack = 150*spAttack/100`, and Minus/Plus the same way | 3207-3210 | attacker ability. The check scans **all battlers** (`butil.c:3114-3122`), not only the partner |
| 21 | Guts and `attacker.status1 != 0`: `attack = 150*attack/100` | 3211-3212 | attacker |
| 22 | Marvel Scale and **`defender.status1 != 0`**: `defense = 150*defense/100` | 3213-3214 | defender |
| 23 | Electric move and Mud Sport on the field: `power /= 2` | 3215-3216 | field |
| 24 | Fire move and Water Sport on the field: `power /= 2` | 3217-3218 | field |
| 25 | Overgrow (Grass), Blaze (Fire), Torrent (Water) or Swarm (Bug), when `atk.hp <= atk.maxHP/3`: **`power = 150*power/100`** (the POWER, not a stat) | 3219-3226 | attacker ability |
| 26 | `gCurrentMove` has EFFECT_EXPLOSION: `defense /= 2` | 3229-3230 | defender (keyed on the effect) |

**Physical branch**, taken when `type < TYPE_MYSTERY(9)` (`battle.h:466`; Normal, Fighting, Flying, Poison, Ground,
Rock, Bug, Ghost, Steel):

| # | Operation | Line |
|---|---|---|
| P1 | `damage = attack * R[atkStage].num / R[atkStage].den`. On a crit, the stage applies only if `atkStage > 6` (a positive stage); otherwise the raw `attack` is used | 3234-3243 (macro 3100-3104) |
| P2 | `damage = damage * power` | 3245 |
| P3 | `damage *= (2*level/5 + 2)` (the `2*level` is floored before `/5`) | 3246 |
| P4 | `helper = defense * R[defStage]`. On a crit, the stage applies only if `defStage < 6` (a negative stage); otherwise the raw `defense` | 3248-3257 |
| P5 | `damage = damage / helper` | 3259 |
| P6 | `damage /= 50` | 3260 |
| P7 | The attacker is burned and does **not** have Guts: `damage /= 2` | 3263-3264 |
| P8 | Reflect on the target's side and **not** a crit: in a double with 2 targets alive, `damage = 2*(damage/3)`; otherwise `damage /= 2` | 3267-3273 |
| P9 | Double battle, a move that targets both foes, 2 alive: `damage /= 2` | 3276-3277 |
| P10 | `if damage == 0: damage = 1` | 3280-3281 |

Then **`type == TYPE_MYSTERY` → `damage = 0`** (`3284-3285`).

**Special branch**, taken when `type > 9` (`battle.h:467`; Fire, Water, Grass, Electric, Psychic, Ice, Dragon, Dark):

| # | Operation | Line |
|---|---|---|
| S1 | `damage = spAttack * R[spaStage]`. On a crit, only if `spaStage > 6` | 3289-3298 |
| S2 | `damage *= power`, then `damage *= (2*level/5 + 2)` | 3300-3301 |
| S3 | `helper = spDefense * R[spdStage]`. On a crit, only if `spdStage < 6` | 3303-3312 |
| S4 | `damage = damage / helper`, then `damage /= 50` | 3314-3315 |
| S5 | Light Screen and not a crit: `2*(damage/3)` (a double with 2 alive) or `damage /= 2` | 3318-3324 |
| S6 | A move that targets both foes in a double: `damage /= 2` | 3327-3328 |
| S7 | Only when neither Cloud Nine nor Air Lock is on the field (`WEATHER_HAS_EFFECT2`, `battle_util.h:48`): Rain (the `B_WEATHER_RAIN_TEMPORARY` bit, which every rain setter also sets, `butil.c:2486`, `:2521`) makes Fire `damage /= 2` and Water `damage = 15*damage/10` | 3331-3345 |
| S8 | (inside S7's gate) Rain, Sandstorm or Hail and `gCurrentMove == MOVE_SOLAR_BEAM`: `damage /= 2` (**not** in clear weather) | 3348-3349 |
| S9 | (inside S7's gate) Sun makes Fire `damage = 15*damage/10` and Water `damage /= 2` | 3352-3363 |
| S10 | Flash Fire activated on the attacker and a Fire move: `damage = 15*damage/10` | 3367-3368 |

**No floor to 1 in the special branch.** Then **`return damage + 2`** (`3371`).

The stat-stage table is `R = {10/40, 10/35, 10/30, 10/25, 10/20, 10/15, 10/10, 15/10, 20/10, 25/10, 30/10, 35/10,
40/10}`, indexed by stage 0..12 with 6 neutral (`pokemon.c:1868-1883`). Our `_calculate_modified_stat`
(`_util.py:32-33`) gives the same floors.

Consequence: the smallest base damage is **3 for a physical move** (floor 1, then +2) and **2 for a special move**.

### 1c. `Cmd_damagecalc` (`bsc.c:1290-1304`), after the base
| # | Operation | Line |
|---|---|---|
| D1 | `dmg = base * gCritMultiplier * dmgMultiplier` (exact) | 1296 |
| D2 | Attacker Charged and the move's **base** type (`gBattleMoves[].type`) is Electric: `dmg *= 2` | 1298-1299 |
| D3 | Helping Hand: `dmg = dmg*15/10` | 1300-1301 |

`dmgMultiplier = 2` is set by:
- Surf vs Dive (`bs1.s:240`); Whirlpool vs Dive (`:834`); Twister vs Fly (`:1829`); Earthquake/Magnitude vs Dig
  (`:1843`); Gust vs Fly (`:1895`); the Stomp effect vs Minimize (`:1900`);
- Facade when the user is statused (`:2257`); SmellingSalt vs a paralysed target (`:2274`); Pursuit on a switch
  (`:3091`);
- Revenge after being damaged by the target (`bsc.c:9346`); Weather Ball in any weather (`bsc.c:9792`).

### 1d. `Cmd_typecalc` (`bsc.c:1355-1424`)
| # | Operation | Line |
|---|---|---|
| T0 | `gCurrentMove == MOVE_STRUGGLE` → skip everything (no STAB, no type; Struggle hits Ghosts) | 1360-1364 |
| T1 | The move type is the dynamic type when one is set (`GET_MOVE_TYPE`, `battle.h:458-464`) | 1366 |
| T2 | **STAB:** the attacker's types[0] or types[1] equals the move type → `dmg = dmg*15`, then `dmg = dmg/10` | 1369-1373 |
| T3 | The target has Levitate and a Ground move → MISSED and DOESNT_AFFECT_FOE (no damage) | 1375-1383 |
| T4 | Otherwise, **walk `gTypeEffectiveness` in TABLE order** (`bmain.c:335-448`, triples (atk, def, mult), mult ∈ {20, 10, 5, 0}). For each row whose attack type = the move type: if def = types[0], apply `ModulateDmgByType(mult)`; if def = types[1] and types[0] ≠ types[1], apply it again | 1386-1406 |
| T4a | `ModulateDmgByType`: `dmg = dmg*mult/10`; **if `dmg == 0 && mult != 0` → `dmg = 1`**. mult 0 sets DOESNT_AFFECT_FOE | 1321-1333 |
| T4b | The row `TYPE_FORESIGHT` (`bmain.c:445`) is a separator. If the target is Foresighted, the loop **breaks** there, skipping Normal→Ghost and Fighting→Ghost 0× (`bmain.c:446-447`, the only rows after it) | 1388-1394 |
| T5 | Wonder Guard: the move has power, it is not a charging turn, and it is not (SE and not NVE) → MISSED | 1409-1419 |

**The order of the type multiply matters only for mixed ×2/×0.5** (and for the floor to 1 at dmg = 1):
- `⌊⌊2d⌋·0.5⌋ = d`, but `⌊⌊d·0.5⌋·2⌋ = d − (d mod 2)`;
- ×2×2 and ×0.5×0.5 do not depend on the order.

Some attack types list their rows in an order that differs from a species' types[0]/types[1]:
- Ice: Flying (373) before Steel (375), and **Fire last (376)**;
- Grass: Ground (363) before Bug (365), Rock (366) before Steel (368);
- Rock: Ground (423) before Bug (425).

### 1e. `Cmd_adjustnormaldamage` (`bsc.c:1658-1698`)
| # | Operation | Line |
|---|---|---|
| A1 | `ApplyRandomDmgMultiplier`: `r = 100 - Random()%16` (85..100, 16 equally likely values; 65536 is divisible by 16). If `dmg != 0`: `dmg = dmg*r/100`, and if it becomes 0, `dmg = 1` | 1639-1651, 1662 |
| A2 | Focus Band (holdEffectParam 10, `items.h:2401`) rolls `Random()%100 < param` | 1677-1681 |
| A3 | No Substitute, and (EFFECT_FALSE_SWIPE, or Endured, or Focus-Banded), and `hp <= dmg` → `dmg = hp - 1` | 1682-1696 |

### 1f. `Cmd_datahpupdate` (`bsc.c:1844-…`): what "the foe lost" means
- If the result flags hold NO_EFFECT (MISSED | DOESNT_AFFECT_FOE | FAILED, `c_battle.h:228`), nothing happens
  (`bsc.c:1862`).
- If a Substitute is up, it takes the damage and the HP is untouched (`1865-1892`).
- Otherwise: if `hp > dmg`, then `hp -= dmg`; else `hp = 0` (`1920-1929`).
- ⇒ **observed loss = min(dmg, hp_before)**. It is informative only while the foe survives, which M1b already
  requires.

### 1g. Summary of the damage ranges that M1a should reproduce
- **Non-crit:** `[max(1, ⌊0.85·X⌋), X]`, where X = the value after D1-D3 (crit = 1) and T2, T4.
- **Crit:** the same with the ×2 at D1, **before** STAB and type, and with the crit rules at P1, P4, S1, S3 and at
  the screens (P8, S5).
- A transcription sketch with a line-cited comment on every step is at
  `scratchpad/m1calc/decomp_sketch.py`. I smoke-ran it: a hand check of 50 Atk, 40 power, L20, 45 Def, STAB gives
  (13, 16) non-crit and (28, 33) crit. It is a reference, not the probe.

---

## 2. The fixed-damage and special-damage effects (for the stage-1 "exact-damage" set)

| Effect | Script (bs1.s) | Damage | Random? | Type check | Line |
|---|---|---|---|---|---|
| SONICBOOM (power 1, Normal, `battle_moves.h:642-644`) | 1720-1729 | 20 | no | typecalc → Ghost immune; Wonder Guard blocks | `setword 20` 1727, `adjustsetdamage` `bsc.c:5861-5899` |
| DRAGON_RAGE (Dragon) | 819-828 | 40 | no | typecalc (Dragon has no 0× row) | 826 |
| LEVEL_DAMAGE (Seismic Toss, Fighting; Night Shade, Ghost) | 1195-1204 | attacker level | no | typecalc: Fighting→Ghost 0× (`bmain.c:447`), Ghost→Normal 0× (`bmain.c:427`) | `Cmd_dmgtolevel` `bsc.c:7926-7930` |
| PSYWAVE (Psychic) | 1206-1215 | `level*(50+10k)/100`, k ∈ 0..10 uniform | its own roll | Psychic→Dark 0× (`bmain.c:409`) | `bsc.c:7932-7941` |
| SUPER_FANG (Normal) | 809-817 | `hp/2`, min 1 | no | typecalc → Ghost immune | `bsc.c:7577-7584`; no `adjustsetdamage` |
| OHKO | 762-771 | KO | – | typecalc, `jumpifmovehadnoeffect` | (tryKO NOT CHECKED) |
| Endeavor | 2479-2491 | target hp − user hp | no | typecalc | (setdamagetohealthdifference NOT CHECKED) |
| Counter / Mirror Coat | 1217-1225 / 1801-1809 | 2 × `physicalDmg` / `specialDmg` (= gHpDealt, the clamped HP loss, `bsc.c:1941`, `:1957`) | no | typecalc2 (immunity only, `bsc.c:4500-4575`): Ghost immune to Counter, Dark to Mirror Coat | `bsc.c:7952`, `:7976` |
| Bide | 3292-3314 | 2 × `gBideDmg` (accumulates `gBattleMoveDamage`, pre-clamp, `bsc.c:1912`) | no | typecalc → Ghost immune | `butil.c:2221` |

`typecalc` runs **before** `setword` in these scripts. It multiplies the stale `gBattleMoveDamage`, which `setword`
then overwrites, so only the **result flags** survive. `bicbyte` clears SE/NVE and keeps DOESNT_AFFECT_FOE
(`bs1.s:1726`). For stage 1, the exact-damage set is:
- LEVEL_DAMAGE = level; SONICBOOM = 20; DRAGON_RAGE = 40;
- SUPER_FANG = hp//2 (hp 1 → 1, which KOs, so the spec's "only when hp ≥ 2" is right);
- each only when the type chart does not make it 0.

---

## 3. Our `calculate_move_damage_range` against the decomp (quick diff, for M1a's rows)

(I read `_util.py:1-40`, `:160-245` and `:296-521`. Of `battle_state.py` I read only `:577-584`, where `types` is
deduplicated for mono-types, so there is no double multiply.)

| # | Our code | Decomp | Direction of the error | New? |
|---|---|---|---|---|
| C1 | crit ×2 after STAB and type (`:208-213` → `:230-231`); Charge ×2 after them too (`:233-238`) | ×2 before STAB and type (`bsc.c:1296-1299`) | **under** by ≤4 (crit), measured by `order_check.py` | new (quantified) |
| C2 | type loop over `defender_types` (types[0], types[1]); no floor to 1 (`:212-213`) | table order and a floor to 1 (`bsc.c:1386-1406`, `:1324-1325`) | ±1 (under for Grass vs Nincada or Aron) | new |
| C3 | Marvel Scale tests `attacker_status` (`:399`) | `defender->status1` (`pokemon.c:3213`) | under when we are statused | **new bug** |
| C4 | Burn halving has no Guts exemption (`:445-446`) | `&& ability != ABILITY_GUTS` (`pokemon.c:3263`) | under by about 2× for a burned Guts attacker | **new bug** |
| C5 | Psywave returns `(level, level*150//100)` (`:227-228`), besides the name miss | min `level*50//100` (`bsc.c:7939`) | min too high; max right | new (beyond KI-109) |
| C6 | Fixed-damage returns ignore a 0× type (`:215-228`); an immune target gives `DamageRange(max(1, 0), 0)` = min 1 > max 0 (`:242`) | typecalc before setword; no HP change | over (safe), but min > max is malformed | KI-109 covers the immunity; min > max is new |
| C7 | Plus/Minus only via the partner (`:392-396`) | any battler on the field (`butil.c:3114-3122`) | under in a single vs the counterpart ability | new (edge) |
| C8 | No Mud/Water Sport (`:402-406` TODO) | `pokemon.c:3215-3218` | over (safe) | known TODO |
| C9 | No Flash Fire boost (`:518` TODO) | `pokemon.c:3367-3368` | under if our Flash Fire mon was hit by Fire first | known TODO |
| C10 | No Cloud Nine / Air Lock (`:497` TODO) | `pokemon.c:3331` | over or under (Water in rain) | known TODO |
| C11 | Struggle gets STAB and type (`:207-213`) | skipped (`bsc.c:1360-1364`) | ±50% | new (edge) |
| C12 | `is_special` = index ≥ 9 includes ??? (`pokemon.py:312-313`) | `> 9` (`battle.h:467`) | none (??? moves have power 0) | trivia |
| C13 | Badge boost has no link/Frontier/Secret Base exception (`:336-343`) | `pokemon.c:3409-3414` | over (safe) in the Frontier | noted in KI-110 |
| C14 | "Solar Beam" name (`:508`) | `MOVE_SOLAR_BEAM` (`pokemon.c:3348`); the in-game name is "SOLARBEAM" (`move_names.h:79`) | over (safe) | KI-111 |
| C15 | Charge keyed on `move_type` (the Hidden Power dynamic type) (`:236`) | `gBattleMoves[].type` (the base type) (`bsc.c:1298`) | edge | new (edge) |

These match the decomp:
- the stat-stage ratios (`:32-33`) and the crit stage rules (`:424-438`, `:467-482`);
- the level term (`:432`);
- the physical floor to 1 (`:460`) and the screens (`:449-453`, `:487-491`);
- the rain/sun order (`:501-516`);
- the type-item param (`:348-355`), Metal Powder ×2 (`:374-375`) and Thick Fat on Sp. Atk (`:388-389`);
- the Overgrow-family boost on POWER (`:408-415`);
- the random min/max (`:242`).

---

## 4. M1b implications from the decomp (exclusions and observation)

- **Observation:** loss = `min(dmg, hp_before)` (`bsc.c:1920-1929`). A Substitute hides the hit (`:1865-1892`). A
  miss, Protect or immunity gives 0 (NO_EFFECT, `:1862`). These are below-min samples and cannot fail the
  over-crit_max acceptance, but they pollute any "within [min, max]" statistic. Log them as a separate reason.
- **Clamp to hp-1:** Focus Band (held item, already excluded), **Endure (the foe's move; add it)**, **False Swipe
  (our move; add it, or clamp the prediction)** (`bsc.c:1677-1696`).
- **State read at hit time, not at selection** (my inference from `pokemon.c:3100-3104`, `:3211-3226`, `:3263`,
  `:3331-3368`). These can make the real damage exceed a selection-time crit_max:
  - our HP crossing maxHP/3 with Overgrow/Blaze/Torrent/Swarm (×1.5 power; **our starters carry these abilities**);
  - our status1 changing with Guts (×1.5 Atk; a burn inflicted first halves the damage when we lack Guts);
  - the weather changing (the foe's Rain Dance or Sunny Day, ×1.5);
  - the foe's Def/SpDef stage dropping (e.g. its own Superpower). A negative stage is kept on a crit, `pokemon.c:3251`.

  Proposal: log our HP/maxHP, status1 and stages, the foe's stages, and the weather at both reads. Exclude the sample
  (reason logged) when any of them differs.
- **Self-HP costs of the FOE that are not "recoil/crash/drain/heal/Substitute":**
  - Belly Drum takes `maxHP/2` (`bsc.c:8785-8795`; I read only the head of the function);
  - a Ghost's Curse takes `maxHP/2` of the user's HP (`bsc.c:8477`);
  - Pain Split (referenced at `bsc.c:1938`; its calculation is NOT CHECKED).

  Add these three to the "the foe knows …" list.
- **End-of-turn heal not listed in the spec:** Rain Dish heals `maxHP/16` in rain (`butil.c:2593-2600`). Add it to the
  ability exclusions (Rough Skin is there). Leftovers and Shell Bell are held items, already excluded.
- **Delayed damage:** Future Sight / Doom Desire store `CalculateBaseDamage` (no crit, no random) at use time
  (`bsc.c:8929-8946`) and land two turns later. Exclude when one of ours is pending.
- **Multi-hit:** every hit re-rolls (`bs1.s:617-624`). Keep EFFECT_MULTI_HIT, DOUBLE_HIT, TRIPLE_KICK and TWINEEDLE
  off the whitelist (or model the sum of N hits).

---

## 5. Adversarial check of the Gemini note (`m1_gemini_answer.md`)

The note's claims are bullets in five sections, not numbered, so I number them G§.n in reading order. Verdicts:
**CONFIRMED** (with a line), **WRONG** (with the correct fact and line), **PARTIAL**, or **NOT CHECKED**.

### §1 Order of operations
| # | Gemini claim | Verdict |
|---|---|---|
| G1.1 | `Cmd_critcalc` rolls and "sets a critical hit flag in `gBattleStruct`" | **PARTIAL/WRONG detail.** It sets the global `gCritMultiplier` = 2 or 1 (`bsc.c:1283-1285`), and the chance table is `{16,8,4,3,2}` (`bsc.c:606`). |
| G1.2 | `Cmd_damagecalc` is "the heaviest command" and gathers stats and modifiers before the base math | **WRONG.** It is 14 lines (`bsc.c:1290-1304`). All stat, item and ability modifiers live in `CalculateBaseDamage` (`pokemon.c:3158-3230`). |
| G1.3 | Helping Hand `damage*15/10` | **CONFIRMED** formula (`bsc.c:1300-1301`). **WRONG** placement: it comes after the base and the crit, not "before base math". |
| G1.4 | Charge `BP * 2` | **WRONG.** `gBattleMoveDamage *= 2` after the crit (`bsc.c:1298-1299`), keyed on the base type. |
| G1.5 | Mud Sport / Water Sport `BP / 2` | **CONFIRMED** (`pokemon.c:3215-3218`). The location is CalculateBaseDamage, after the stat modifiers. |
| G1.6 | Physical/Special decided by type | **CONFIRMED** (`battle.h:466-467`; `pokemon.c:3232`, `:3287`). |
| G1.7 | Stat stages applied to the raw stat, then abilities and items | **WRONG order.** Stages are applied LAST, at `pokemon.c:3232-3257` / `:3287-3312`, after the badges, items and abilities (`:3158-3230`). |
| G1.8 | Attacker abilities: Huge/Pure Power ×2; Hustle, Plus/Minus, Guts ×1.5 on the stat; Overgrow/Blaze/Torrent/Swarm ×1.5 on the stat | **CONFIRMED** for Huge/Pure Power (`3158-3159`), Hustle (`3205-3206`), Plus/Minus (`3207-3210`) and Guts (`3211-3212`). **WRONG** for Overgrow/Blaze/Torrent/Swarm: they multiply **power** (`3219-3226`). |
| G1.9 | Attacker items: Thick Club, Light Ball, Deep Sea Tooth ×2; Soul Dew, Choice Band ×1.5 | **CONFIRMED** (`pokemon.c:3185-3200`). |
| G1.10 | Defender items: Soul Dew, Metal Powder ×1.5; Deep Sea Scale ×2 | **CONFIRMED** for Soul Dew (`3189-3190`) and DSS (`3193-3194`). **WRONG** for Metal Powder: `defense *= 2` (`3197-3198`). |
| G1.11 | Marvel Scale ×1.5; Thick Fat halves the attacker's Atk/SpAtk | Marvel Scale **CONFIRMED** (`3213-3214`). Thick Fat **PARTIAL**: it halves `spAttack` only (`3203-3204`). The result is the same because Fire and Ice are special. |
| G1.12 | Explosion and Self-Destruct halve Def | **CONFIRMED** (`pokemon.c:3229-3230`), keyed on EFFECT_EXPLOSION. |
| G1.13 | Step A `level*2/5+2`, and "if crit, Step A × 2" | Level term **CONFIRMED** (`3246`). Crit **WRONG**: ×2 on the returned base damage, including the +2 (`bsc.c:1296`). |
| G1.14 | Steps B-E: ×BP×Atk, ÷Def, ÷50, +2 | Arithmetic **CONFIRMED** (`3245-3260`, `3371`). **WRONG** that +2 follows ÷50 directly: burn, screens, the both-targets halving, the floor to 1, weather and Flash Fire all come before it (`3263-3368`). |
| G1.15 | Screens are post-base: singles ÷2, doubles "UNSURE: ×2 then ÷3"; crits ignore them | Crit ignoring **CONFIRMED** (`3267`, `3318`). **WRONG** location (inside CalculateBaseDamage, before +2) and **WRONG** doubles order: `2*(damage/3)`, only with 2 targets alive (`3269-3270`, `3320-3321`). |
| G1.16 | Weather is post-base: ×15/10 or ÷2 | Multipliers **CONFIRMED** (`3334-3363`). **WRONG** location: before +2, in the special branch only, gated by Cloud Nine and Air Lock (`3331`). |
| G1.17 | Flash Fire `×15/10` | **CONFIRMED** (`pokemon.c:3367-3368`). The location is CalculateBaseDamage. |
| G1.18 | `Cmd_typecalc` applies STAB `×15/10` | **CONFIRMED** (`bsc.c:1369-1373`). |
| G1.19 | Type loop "through defender types"; 20/5/0; `×mult/10` | Formula **CONFIRMED** (`bsc.c:1323`). **WRONG** loop: it walks the table's rows (`bsc.c:1386-1406`; `bmain.c:335-448`). Omitted: the floor to 1 per step (`1324-1325`) and the Foresight separator (`1388-1394`). |
| G1.20 | `Cmd_adjustnormaldamage` (or `Cmd_adjustsetdamage`) applies the random factor | **PARTIAL.** Yes for adjustnormaldamage (`bsc.c:1662`). **WRONG** for adjustsetdamage, which has no random (`bsc.c:5861-5899`). |
| G1.21 | Burn is in adjustnormaldamage, "not Facade with Guts" | **WRONG.** It is in CalculateBaseDamage, physical only, before screens, and Guts is the exemption (`pokemon.c:3262-3264`). Facade does not exempt. |
| G1.22 | Minimum 1 unless immune | **CONFIRMED** in substance: there are three floors, at `pokemon.c:3280-3281` (physical, before +2), `bsc.c:1324-1325` (per type step) and `bsc.c:1648-1649` (after random, only if it was nonzero). |

### §2 Modifiers
| # | Claim | Verdict |
|---|---|---|
| G2.1 | Stages as fractions, +6 = 8/2, −6 = 2/8 | **CONFIRMED** in value. The decomp writes 40/10 and 10/40 (`pokemon.c:1870`, `:1882`), and every stage floors identically. |
| G2.2 | A crit ignores the attacker's negative and the defender's positive stages, and keeps the others | **CONFIRMED** (`pokemon.c:3234-3257`, `3289-3312`). |
| G2.3 | Badges: "Boulder" = Atk, Balance = Def, Dynamo = Spd, Mind = SpAtk & SpDef, ×11/10, "likely stat getters" | Flags **CONFIRMED**: BADGE01 → Atk (`3161`), BADGE05 → Def (`3163`), BADGE07 → SpAtk and SpDef (`3165-3168`), BADGE03 → speed (`bmain.c:4641`); `110*x/100` gives the same floor. **WRONG**: "Boulder" is the Kanto name; the badge-name ↔ number mapping is UNVERIFIED by me (not in the files read). **WRONG** location (inside CalculateBaseDamage, not the stat getters). **Omitted**: player side only, and the link/e-Reader/recorded/Frontier/Secret Base exclusions (`3407-3419`). |
| G2.4 | Attacker abilities (the same list as G1.8, Hustle physical only) | Same verdict as G1.8. Pinch abilities **WRONG** (they boost power, `3219-3226`). |
| G2.5 | Defender immunities: Levitate, Wonder Guard, Volt Absorb, Water Absorb, Flash Fire, Soundproof | **CONFIRMED**: Levitate and Wonder Guard in typecalc (`bsc.c:1375-1383`, `1409-1419`); Volt/Water Absorb and Flash Fire via ABILITYEFFECT_ABSORBING (`butil.c:2662-2690`; Volt and Water require power ≠ 0, and Flash Fire does not fire while frozen); Soundproof via MOVES_BLOCK (`butil.c:2645-2653`). |
| G2.6 | Type-boost items: `BP × 1.1` | **WRONG.** They multiply the **attack or sp. attack stat** by `(param+100)/100` (`pokemon.c:3171-3182`). The param is 10, or **5 for Sea Incense** (`items.h:2709`). |
| G2.7 | Weather: Rain/Sun ×1.5 or ÷2; "SolarBeam BP is halved outside of Sun" | Rain/Sun **CONFIRMED** (`3334-3363`). SolarBeam **WRONG**: it is the **damage** that is halved, and only in Rain, Sand or Hail, not in clear weather (`3348-3349`). |
| G2.8 | Screens: ÷2 singles, ÷1.5 doubles, ignored by crits | **PARTIAL.** The doubles form is `2*(d/3)` (`3270`), not a division by 1.5. Crit ignoring is **CONFIRMED**. |
| G2.9 | Burn halves "at the end of the sequence, unless Facade" | **WRONG** (see G1.21). |
| G2.10 | Sports on power / Charge BP×2 / Helping Hand BP×1.5 early / STAB ×1.5 / type T1 then T2 / crit on the level term / random 85-100 / minimum 1 in adjustnormaldamage | Sports **CONFIRMED**. Charge **WRONG** (`bsc.c:1298-1299`). Helping Hand **WRONG** (damage, late, `bsc.c:1300-1301`). STAB **CONFIRMED**. Type order **WRONG** (table order). Crit **WRONG** (`bsc.c:1296`). Random **CONFIRMED** (`bsc.c:1639-1651`). Minimum damage **PARTIAL** (G1.22). |

### §3 Moves that bypass the formula
| # | Claim | Verdict |
|---|---|---|
| G3.1 | Dragon Rage 40 and Sonic Boom 20 respect type immunity | **CONFIRMED** (`bs1.s:819-828`, `1720-1729`; typecalc before setword). |
| G3.2 | Seismic Toss and Night Shade deal the level and respect immunity | **CONFIRMED** (`bs1.s:1195-1204`; `bsc.c:7926-7930`). |
| G3.3 | OHKO moves respect immunity | **CONFIRMED** for the script (`bs1.s:767-768`). tryKO is NOT CHECKED. |
| G3.4 | Super Fang = target HP/2, respects immunity | **CONFIRMED** (`bs1.s:809-817`; `bsc.c:7577-7584`). Omitted: the floor to 1, and no adjustsetdamage. |
| G3.5 | Counter, Mirror Coat and Bide deal 2× the damage taken; Ghost is immune to Counter and Bide, Dark to Mirror Coat | **CONFIRMED** (`bsc.c:7952`, `:7976`; `butil.c:2221`; typecalc2 `bsc.c:4500-4575`; Bide's typecalc `bs1.s:3299`). Detail: Counter and Mirror Coat use the clamped gHpDealt, while Bide uses the unclamped damage (`bsc.c:1912`). |
| G3.6 | Endeavor = target HP − user HP, respects immunity | **CONFIRMED** for the script (`bs1.s:2479-2491`). The HP-difference command is NOT CHECKED. |
| G3.7 | Dynamic base power, still through the formula: Present, Magnitude, Spit Up, Beat Up, Hidden Power, Return, Frustration, Low Kick, Flail, Reversal, Eruption, Water Spout, Facade, Revenge, SmellingSalt, Weather Ball, Doom Desire, Future Sight | **PARTIAL.** `gDynamicBasePower` is **CONFIRMED** for Flail/Reversal (`bsc.c:8314`), Return/Frustration (`8606-8608`), Present (`8619-8627`), Magnitude (`8676-8706`), Hidden Power (`8905`), Eruption/Water Spout (`9384`) and Low Kick (`9477`). **WRONG** mechanism for Facade, Revenge, SmellingSalt and Weather Ball: they are `dmgMultiplier` ×2 on the whole damage (`bs1.s:2257`, `2274`; `bsc.c:9346`, `9792`), not base power. Spit Up and Beat Up are NOT CHECKED. Future Sight: the damage is stored at use time (`bsc.c:8941-8946`). **Omitted:** Psywave; Rollout and Fury Cutter (`bsc.c:8559`, `8594`); Triple Kick; and every ×2 against a semi-invulnerable or Minimized target, and Pursuit (§1c). |

### §4 Common calculator mistakes
| # | Claim | Verdict |
|---|---|---|
| G4.1 | Floor after every division | **CONFIRMED** (throughout §1). |
| G4.2 | Random applied last | **CONFIRMED** (`bs1.s:249-252`; `bsc.c:1662`). Only the Focus Band/Endure/False Swipe clamp follows it (`bsc.c:1677-1696`). |
| G4.3 | Gen 3 split by type; Shadow Ball uses Attack | **CONFIRMED** (TYPE_GHOST = 7 < 9, `constants/pokemon.h:13`; `battle.h:466`). |
| G4.4 | A crit keeps a favourable stage and ignores the screens | **CONFIRMED** (`pokemon.c:3234-3257`, `3267`, `3318`). |
| G4.5 | "Applying Type 2 before Type 1" as the rounding mistake | **WRONG** premise. The game uses neither types order; it uses **table order** (`bsc.c:1386-1406`). Example: the game multiplies Grass vs Nincada `{BUG, GROUND}` by Ground ×2 first, so types[0]-first is the mistake. |
| G4.6 | Names: SonicBoom, SolarBeam, Faint Attack, Smelling Salt | **CONFIRMED** in substance: the in-game names are "SONICBOOM", "SOLARBEAM", "FAINT ATTACK" and "SMELLINGSALT" (`move_names.h:52`, `79`, `188`, `268`). Its camel-case "SonicBoom"/"SolarBeam" is not how our data spells them: "Sonicboom" and "Solarbeam", per KI-109/KI-111. I did not open `moves.json`. |

### §5 Live-audit factors
| # | Claim | Verdict |
|---|---|---|
| G5.1 | Weather damage (Sandstorm, Hail) | NOT CHECKED here (the spec already excludes it). |
| G5.2 | Poison, toxic and burn damage | NOT CHECKED (already excluded). |
| G5.3 | Leech Seed, Curse, Nightmare, Wrap/Bind | NOT CHECKED (the spec cites `butil.c`). |
| G5.4 | A Future Sight or Doom Desire landing | **CONFIRMED** as a mechanism (`bsc.c:8929-8946`). Relevant only if we used it. |
| G5.5 | Leftovers, Shell Bell, Oran/Sitrus, Figy/Mago "(AI triggered mid-turn)" | **WRONG** framing: berries are held-item triggers, not AI actions. The lines are NOT CHECKED. The held-item exclusion covers them. |
| G5.6 | Rough Skin, Liquid Ooze, Rain Dish, Shed Skin | Rain Dish **CONFIRMED** (`butil.c:2593-2600`, maxHP/16, gated by the weather). The others are NOT CHECKED. Rain Dish is missing from the spec's list. |
| G5.7 | Recoil, crash and drain | NOT CHECKED (already excluded). |
| G5.8 | Substitute absorbs, the HP is unchanged | **CONFIRMED** (`bsc.c:1865-1892`). |
| G5.9 | A confusion self-hit | NOT CHECKED (already excluded). |
| G5.10 | AI Potion/Full Restore; healing moves | NOT CHECKED here (the spec cites `battle_ai_switch_items.c`). |
| G5.11 | Pain Split | Partly: `MOVE_PAIN_SPLIT` is referenced at `bsc.c:1938`; the calculation is NOT CHECKED. Missing from the spec's list. |
| (omitted by Gemini) | Endure, Focus Band, False Swipe clamp to hp-1; Belly Drum and a Ghost's Curse cut the user's own HP; the hit-time state changes of §4 | `bsc.c:1677-1696`; `bsc.c:8785-8795`; `bsc.c:8477`; see §4. |

**Gemini score (my tally):** the names and the list of modifiers are largely right. But nearly every **placement and
order** detail that decides integer-exact output is wrong:
- the crit location, the +2 position, the screen/weather/burn location and the doubles-screen order;
- the type-multiply order;
- Charge, Helping Hand, the pinch abilities and the type items, each applied to the wrong operand;
- the Metal Powder value, the SolarBeam condition, and random in adjustsetdamage.

This matches the project's measured rule: grade Gemini's NAMES high and its DETAILS low.

---

## 6. What I did NOT verify
- `tryKO`, `setdamagetohealthdifference`, Spit Up, Beat Up, Triple Kick, the Pain Split calculation and the body of
  Belly Drum past `bsc.c:8795`.
- The end-of-turn damage lines the spec already cites (`butil.c` `:1505`, `:1557` and the others).
- The badge-name ↔ number mapping (Stone/Knuckle/Dynamo/Heat/Balance/Feather/Mind/Rain) is UNVERIFIED (general
  knowledge). The flag numbers are verified.
- `moves.json` spellings (taken from KI-109/KI-111, not opened).
- Whether our `BattlePokemon.stats` are exactly `gBattleMons` raw stats (assumed from the field names).
- The under-prediction bound in §0.1 is **pure arithmetic over the post-base pipeline**, given the same base value.
  Base-level discrepancies (C3, C4, C7, C9) add to it depending on the inputs. It is not a live measurement.
