> ⚠ **A NOTE, NOT A SOURCE OF TRUTH.** Output of one agent of the design v2 step 11 recon (2026-09-30, a workflow of five fresh Claude agents; decomp read at pret/pokeemerald f90719c4). The design that uses it is `../2026-09-30-dmgcalc11-DESIGN.md`, whose author re-read every load-bearing claim it relies on (marked ✔ there). Line numbers are as of branch `wt/dmgcalc11` at `241929d7`. Scratch scripts it mentions were not committed.

# M1 recon: adversarial deviation hunt (design v2 step 11)

**The claim under attack:** "For an ordinary damaging move against a wild or trainer foe, the true non-crit damage always lies within [min, max] of `calculate_move_damage_range`, and the true crit damage never exceeds its crit maximum."

**Verdict: REFUTED on both halves**, though narrowly for the plain case:
- **Non-crit, plain hit (EFFECT_HIT family), a single-hit move, no in-turn state change.** Our base-damage path matches the decomp statement for statement, and the random layer matches exactly. A differential fuzz of the real code against an independent decomp port confirms this (§0). The only residual is **1 HP of under-prediction** from two rounding causes: the type-application order (D2) and the missing minimum of 1 per type step (D3).
- **Crit.** The crit maximum is **under-predicted by up to 4 HP** (a 4×-effective STAB move), and by up to 8 HP with Charge (D1). That exceeds the design's MARGIN of 3 HP, so the M1b acceptance "0 over crit_max + 3" can fail on a perfectly correct game.
- **"Ordinary damaging move", read broadly.** The claim collapses. Fixed-damage, variable-power, multi-hit, damage-doubling and typeless moves are under-predicted by 1.5× up to unbounded. So are several abilities, and so is any in-turn state change between the decision read and the move's execution.

**Sources.**
- Our code: worktree `C:/Remote Projects/pokebot-wt-ch24`, branch `wt/dmgcalc11`, HEAD `241929d7`, read-only.
- The decomp: `pret/pokeemerald` master `f90719c46c` (2026-09-29), fetched with `gh api` on 2026-09-30.
- Every line number below is from those revisions. Anything not read directly is marked **UNVERIFIED**.

---

## 0. Method, and what was ruled out

1. **Line-by-line read.**
   - Ours: `_calculate_base_move_damage`, `sandbox-pokebot/modules/battle_strategies/_util.py:296-520`, against `CalculateBaseDamage`, `src/pokemon.c:3106-3372`.
   - Ours: the tail of `calculate_move_damage_range`, `_util.py:165-242`, against `Cmd_critcalc`, `src/battle_script_commands.c:1253-1288`; `Cmd_damagecalc`, `:1290-1304`; `ModulateDmgByType`, `:1321-1353`; `Cmd_typecalc`, `:1355-1424`; and `ApplyRandomDmgMultiplier`, `:1639-1651`.
2. **Differential fuzz of the REAL calculator.**
   - Scratch harness `scratchpad/m1_harness.py`. It imports the real `BattleStrategyUtil`, builds synthetic 0x58-byte `gBattleMons` records plus a `BattleState`, and stubs `get_event_flag`. `sys.dont_write_bytecode` is set, and nothing in the worktree changed; I checked `git status` and mtimes.
   - It is compared against my independent decomp port, `scratchpad/m1_decomp_port.py`. That port reads the type table straight out of `battle_main.c:335-449`.
   - Inputs: plain-effect moves, random species, levels 2-70, stats 5-300, stat stages including ±6, burn, poison and paralysis, Reflect and Light Screen, rain, sun and sand, badges 1/5/7, and crit.
   - **Run 1** (`m1_fuzz.py`, 21,412 samples):
     - non-crit: exact 10,585, under-predicted by 1 HP 86 times, over-predicted by 1 HP 59 times;
     - crit: exact 9,033, under-predicted by 1/2/3/4 HP 1,467/210/4/8 times.
   - **Run 2** (`m1_fuzz2.py`, 27,381 samples, adding Thick Fat and Pure Power holders): the same classes, nothing new.
   - ⇒ **Every mismatch belongs to D1, D2 or D3.**
3. **Things I checked that are NOT deviations:**
   - **Stat-stage ratios.** `_util.py:32-33` equals `gStatStageRatios`, `pokemon.c:1868-1883`.
   - **Crit's stage rules.** Ignoring our Atk drops and the foe's Def boosts: `_util.py:424,435,467,477` equals `pokemon.c:3234-3255,3289-3310`.
   - **Crit ignores screens.** `_util.py:449,487` equals `pokemon.c:3267,3318`.
   - **Burn order, the physical min-1 floor, the +2, and the order of Huge Power, badges, items and Hustle.**
   - **The type chart.** `modules/data/types.json` equals `gTypeEffectiveness` for all pairs; I diffed them programmatically: 0 differences.
   - **Hidden Power.** Power and type: `battle_state.py:677-702` equals `battle_script_commands.c:8889-8912`.
   - **Weather bit decoding.** `battle_state.py:312-322`. Overworld rain and Drizzle both set `RAIN_TEMPORARY|RAIN_PERMANENT` (`battle_util.c:2486,2521`), so the decomp's `B_WEATHER_RAIN_TEMPORARY`-only test at `pokemon.c:3334` sees every rain.
   - **The random factor.** 85-100 inclusive, with a min-1 floor: `_util.py:242` equals `:1639-1651`.
   - **Spread moves.** Earthquake, Explosion and Magnitude are `FOES_AND_ALLY` in `moves.json`, so they are correctly NOT halved; `BOTH` moves are halved only with 2 alive, which matches `pokemon.c:3276,3327` via the absent flags.

---

## 1. Deviations ranked by the size of the UNDER-prediction

**Columns.** "Ours" is the real calculator's output. "True" is the decomp's. Stats are **illustrative** (plausible for the level, not read from a ROM or save). Every row marked "(harness)" was computed by running the real `_util.py` code and my decomp port side by side (`scratchpad/m1_examples.py`, `m1_dbg*.py`). The other rows are hand-computed from the cited formula.

### Tier A: unbounded, or more than 5× (the calculator is not modelling the move at all)

| # | Deviation | Ours (cite) | Decomp (cite) | Example: ours vs true | Worst case |
|---|---|---|---|---|---|
| A1 | **OHKO moves** (Fissure, Horn Drill, Guillotine, Sheer Cold; power 1 in `moves.json`) | the normal formula, power 1, `_util.py:176-178` | `Cmd_tryKO` sets damage = target HP, `battle_script_commands.c:7490-7560` (`:7559`) | foe at 55 HP: ours [2,3] vs true 55 | the foe's whole HP |
| A2 | **Rollout / Ice Ball** (data power 30); **Fury Cutter** (10) | base power only | ×2 per consecutive hit, and ×2 after Defense Curl: `:8536-8566` (up to 480, or 960 after Curl); Fury Cutter up to 160 (`:8580-8600`) | (harness) L20 Geodude, Rollout 5th hit after Curl vs L20 Zigzagoon: **ours [12,15] vs true [328,387]**, 25.8× | 32× (Rollout + Curl), 16× (Fury Cutter) |
| A3 | **Weather Ball** in weather | Normal, 50 power, *physical* path | `Cmd_setweatherballtype` `:9787-9800`: dmgMultiplier 2 and a type change (Water in rain, Fire in sun, Rock in sand, Ice in hail), so it runs on the SPECIAL path with the new type's STAB, effectiveness and rain boost | (harness) L30 Castform in rain vs L30 Numel: **ours [15,18] vs true [336,396]**, 22× | about 20×+ |
| A4 | **Variable-power moves stored as power 1:** Flail/Reversal (to 200), Return/Frustration (to 102), Magnitude (10-150), Present (40/80/120), Low Kick (20-120) | power 1, `_util.py:176-178` | `:8303-8316` (`sFlailHpScaleToPowerTable` `:749`), `:8603-8611`, `:8670-8710`, `:8613-8630`, `:9467-9480` (`sWeightToDamageTable` `:774`) | (harness) L20 Taillow, Return at friendship 255 (power 102) vs Zigzagoon: **ours [3,4] vs true [28,33]**, 8.25× | up to ~100× (Flail at 1 HP) |
| A5 | **KI-109 Sonicboom** (the name check never matches: `_util.py:218` says "Sonic Boom", the data says "Sonicboom") | the power-1 formula | `setword gBattleMoveDamage, 20`, `battle_scripts_1.s:1720-1729` | (harness) L20 Magnemite vs L20 Zigzagoon: **ours [2,3] vs true 20** | about 10× |
| A6 | **KI-109 Psywave** (`_util.py:227` says "Psy Wave", the data says "Psywave") | the power-1 formula | `level*(r*10+50)/100`, r ∈ 0..10, `:7932-7941` | (harness) L30 attacker: **ours [2,3] vs true [15,45]** | 1.5·L |
| A7 | **Endeavor, Counter, Mirror Coat, Bide** (power 1; `_util.py:172` todo) | power-1 formula | foe HP minus our HP (`:9366-9377`); 2× the physical damage taken (`:7943-7968`); the same for special damage (Mirror Coat); 2× the damage stored (Bide, `battle_scripts_1.s:573`) | foe at 55, us at 10: Endeavor ours ~3 vs true 45 | unbounded |
| A8 | **Foresight / Odor Sleuth** used on a Ghost: Normal and Fighting moves then hit it | Ghost immunity always applied (`_util.py:212-213`) → **max = 0** | the `TYPE_FORESIGHT` entry at `battle_main.c:445` makes the loop `break` before the Ghost immunities (`battle_script_commands.c:1388-1393`) | (harness) Poochyena Tackle vs a foresighted Shuppet: **ours [1,0] vs true [9,11]** | unbounded (ours says 0). Poochyena learns Odor Sleuth (**UNVERIFIED** level) and Mt Pyre has Shuppet |
| A9 | **Struggle** is typeless in Gen 3 | STAB and type effectiveness applied (Normal) | `Cmd_typecalc` returns early for `MOVE_STRUGGLE` (`:1360-1364`): no STAB, no effectiveness | (harness) vs Shuppet: **ours [1,0] vs true [12,15]**; vs Geodude (Rock/Ground): ours [3,4] vs true [5,6] | unbounded (vs Ghost); 4× vs a double resist |
| A10 | **Future Sight / Doom Desire** | not modelled | damage is computed when used (`:8929-8950`, `futureSightDmg` at `:8941`) and lands two turns later, at end of turn | M1b would attribute the delayed hit to that turn's move | the size of the whole Future Sight hit (not a calc bug, but a sample hazard; see §3) |

### Tier B: 1.5× to 5×

| # | Deviation | Ours | Decomp | Example: ours vs true | Worst |
|---|---|---|---|---|---|
| B1 | **Multi-hit**: 2-5 hits (Double Slap, Comet Punch, Fury Attack, Pin Missile, Spike Cannon, Barrage, Fury Swipes, Bone Rush, **Arm Thrust**, **Bullet Seed**, Icicle Spear, Rock Blast); 2 hits (Double Kick, Bonemerang, Twineedle); Triple Kick (10+20+30); Beat Up (one hit per party member) | one hit | `setmultihitcounter` `:7139-7154` (2-5 hits; P = 3/8, 3/8, 1/8, 1/8); the loop `battle_scripts_1.s:604-626`, with **critcalc per hit** (`:620`); Triple Kick `:1384-1405` | (harness) L14 Makuhita, Arm Thrust vs L14 Zigzagoon: **one hit [10,12]; 5 hits → true max 60 vs ours max 12** | 5× (6× Triple Kick), and each hit can crit independently |
| B2 | **dmgMultiplier = 2** moves: Facade (while we are statused), SmellingSalt (foe paralysed), Revenge (we were hit first by this foe), Stomp/Astonish/Needle Arm/Extrasensory (foe Minimized), EQ/Magnitude (foe underground), **Surf** (EFFECT_HIT!)/Whirlpool (foe underwater), Gust/Twister (foe airborne), Pursuit (on a switch) | not modelled | `Cmd_damagecalc` multiplies by `dmgMultiplier` BEFORE typecalc (`:1296`); set at `battle_scripts_1.s:240` (Surf), `:834` (Whirlpool), `:1829` (Twister), `:1843` (EQ), `:1895` (Gust), `:1900` (Stomp), `:2257` (Facade), `:2274` (SmellingSalt), `:3091` (Pursuit); Revenge at `battle_script_commands.c:9339-9348` | (harness) Facade, poisoned Guts Taillow: **ours [33,39] vs true [66,78]**; SmellingSalt vs a paralysed foe: **[19,23] vs [39,46]**; EQ vs Dig: **[48,57] vs [96,114]** | 2×. ‼ **SmellingSalt vs a target the weaken policy just paralysed** is exactly the policy's own sequence; it also CURES the paralysis (`setmoveeffect MOVE_EFFECT_REMOVE_PARALYSIS`, `battle_scripts_1.s:2270`) |
| B3 | **Guts + burn**: the decomp exempts Guts from the burn halving | `_util.py:444-446` halves whenever the attacker is burned | `pokemon.c:3263-3264`: `&& attacker->ability != ABILITY_GUTS` | (harness) L22 burned Guts Taillow, Peck: **ours [10,12] vs true [17,21]** | about 2×. Taillow and Makuhita (Guts) are common Hoenn party members |
| B4 | **Brick Break through Reflect** | Reflect halving applied | `removelightscreenreflect` runs BEFORE `damagecalc` (`battle_scripts_1.s:2418-2427`) | (harness) L20 Makuhita vs Zigzagoon behind Reflect: **ours [30,36] vs true [56,66]** | about 2× |
| B5 | **In-turn stat raise on OUR side** (the foe's Swagger/Flatter gives +2 Atk/SpA, when the foe moves first) | uses the stages read at the decision | stages are read at execution (`pokemon.c:3243,3298`) | (harness) Taillow Peck, stage 0 at the decision and +2 at execution: **ours [11,13] vs true [20,24]** | 2× (it also confuses us; our self-hit is not the foe's HP) |
| B6 | **Cloud Nine / Air Lock** present, with rain + Fire or sun + Water | weather always applied (`_util.py:497` todo) | `WEATHER_HAS_EFFECT2` (`pokemon.c:3331`, `include/battle_util.h:48`) scans ALL battlers, fainted included (`battle_util.c:3114-3123`) | (harness) Ember in rain with Cloud Nine present: **ours [7,9] vs true [12,15]** | 2× |
| B7 | **Plus/Minus with the partner ability ANYWHERE on the field** (the foe included, in singles) | only `attacker_partner`, i.e. our own side (`_util.py:392-396`) | `ABILITY_ON_FIELD2` = `AbilityBattleEffects(ABILITYEFFECT_FIELD_SPORT, 0, id, 0, 0)` (`include/battle_util.h:38`), whose default branch loops over every battler (`battle_util.c:3114-3123`) | (harness) our Plusle Spark vs a wild Minun: **ours [10,12] vs true [15,18]** | 1.5× (Route 110 has both, **UNVERIFIED** encounter table) |
| B8 | **Marvel Scale keyed on the wrong battler's status** | `_util.py:399` tests `attacker_status` | `pokemon.c:3213` tests `defender->status1` | (harness) our poisoned Mightyena Headbutt vs a healthy Milotic: **ours [18,22] vs true [28,33]** (and the reverse: +11 over) | 1.5×. In Gen 3 only Milotic has Marvel Scale (a trainer foe) |
| B9 | **Pinch ability crossing maxHP/3 during the turn** (Torrent, Blaze, Overgrow, Swarm) | uses our HP at the decision | HP is read at execution (`pokemon.c:3219-3226`) | (harness) Mudkip at 14/35 HP when deciding, 11/35 when its Water Gun fires: **ours [8,10] vs true [12,15]** | 1.5×. All three starters; happens once per battle in a long weaken fight |
| B10 | **Flash Fire activated** | not modelled (`_util.py:518` todo) | `pokemon.c:3367-3368` | (harness) Vulpix Ember: **ours [12,15] vs true [17,21]** | 1.5× |
| B11 | **Helping Hand** (doubles only) | todo (`_util.py:240`) | `:1300-1301` | n/a | 1.5× |
| B12 | **Spit Up** (1-3 stockpiles; no random factor, no crit) | a 100-power single hit with the random factor | `Cmd_stockpiletobasedamage` `:6868-6890` (base × count), then typecalc, then `adjustsetdamage` (`battle_scripts_1.s:2094-2103`) | ours max = base; true = base × count | 3× |
| B13 | **In-turn weather set by the foe moving first** (Sunny Day before our Fire move, Rain Dance before our Water move) | uses the weather at the decision | weather is read at execution (`pokemon.c:3331-3364`) | same arithmetic as B6 | 1.5× |
| B14 | **The foe's in-turn Minimize, or its Dig/Fly/Dive/Bounce first turn**, before our Stomp-family, EQ, Gust or Surf | the design DEFERs a semi-invulnerable target only at the decision | the dmgMultiplier branches in B2 | as B2 | 2× |
| B15 | **Ability read from the species slot, not from `gBattleMons.ability` (0x20)** | `battle_state.py:566-570` | Trace, Role Play and Skill Swap rewrite `gBattleMons[].ability`, which is what `pokemon.c:3158-3214` reads | e.g. our Kirlia (Trace) copies Pure Power from a wild Meditite: true physical ×2, ours ×1 | 2× on the attacker side; the defender-side cases are mostly over-predictions |
| B16 | **A frozen Flash Fire foe** | `_util.py:201-202` always returns 0 for Fire | Flash Fire does not absorb while frozen (`battle_util.c:2690`) | ours 0 vs true full damage | unbounded (rare) |

### Tier C: rounding, at most 8 HP (the dangerous rows versus MARGIN = 3 HP)

| # | Deviation | Ours | Decomp | Measured bound (exhaustive over the base damage B, `m1_bound.py`) | Example (harness) |
|---|---|---|---|---|---|
| **D1** | **Crit ×2 (and Charge ×2) applied AFTER the STAB and type floors, not before** | `_util.py:230-238`, after `:207-213` | `Cmd_damagecalc` multiplies by `gCritMultiplier` (`:1296`) and Charge (`:1298-1299`) BEFORE `Cmd_typecalc`'s STAB and type steps (`:1369-1406`) | crit under-predicts by: 1 HP (STAB, neutral); 2 HP (STAB, 2×); **4 HP (STAB, 4×)**; 3 HP (STAB with a mixed 2×/0.5×). Charge non-crit: up to 4. **Crit + Charge: up to 8** | L16 Mudkip Water Gun crit vs Geodude (4×): **ours crit [108,128] vs true [112,132]**; Lotad Mega Drain crit vs Aron: ours [20,24] vs true [22,27] |
| **D2** | **The type multipliers are applied in the DEFENDER's type order, not in `gTypeEffectiveness` table order** | `_util.py:212-213` iterates `defender_types` = [type1, type2] from `gBattleMons` (`battle_state.py:577-584`) | table order, `battle_script_commands.c:1386-1406`; the table is `battle_main.c:335-449` | non-crit: **1 HP**, exactly when the table applies 2× first, we apply 0.5× first, and the pre-type damage is odd | Bite vs Sableye (Dark/Ghost; `DARK,GHOST` 2× at `battle_main.c:436` precedes `DARK,DARK` 0.5× at `:437`): **ours [10,12] vs true [11,13]** |
| **D3** | **No minimum of 1 after each type step** | `_percentage` can reach 0 | `ModulateDmgByType` `:1323-1325` floors to 1 | 1 HP; ours returns `max=0 < min=1` | Signal Beam vs Skarmory (0.25×), base 2: ours (1,0) vs true (1,1) |

**The Hoenn species hit by D2** (ROM type order from `src/data/pokemon/species_info.h`, e.g. Aron `{STEEL, ROCK}` at `:10769`, Skarmory `{STEEL, FLYING}` at `:6819`, Nincada `{BUG, GROUND}` at `:8339`, Sableye `{DARK, GHOST}` at `:8969`):
- Grass vs Aron, Lairon, Aggron, Nincada and Surskit;
- Steel vs the Aron line;
- Electric vs Altaria and Salamence;
- Fire and Flying vs Anorith, Armaldo, Lileep and Cradily;
- Poison vs Lileep and Cradily;
- Ice vs Numel, Camerupt and Skarmory;
- Rock vs Skarmory;
- Dark vs Sableye;
- Bug, Dark and Ghost vs the Beldum line;
- Ground vs Dustox.

⚠ `modules/data/species.json` stores some species in a DIFFERENT order from the ROM: Aron as [Rock, Steel], Lotad as [Grass, Water], Skarmory as [Flying, Steel]. For a `BattlePokemon` defender this does not matter, because it reads `gBattleMons` 0x21/0x22. **An offline M1a probe that builds its rows from `species.json` types will test the wrong order.** It must use the ROM order.

### Tier D: over-predictions (the safe direction, listed so M1a does not mistake them for fidelity)

- **KI-111, Solarbeam.** `_util.py:508` compares against "Solar Beam", but the data says "Solarbeam", so the rain, sand and hail halving (`pokemon.c:3348`) is never applied: ours predicts 2× the true damage. (It is also a two-turn move: the charge turn deals 0.)
- **The badge exceptions are missing.** `pokemon.c:3407-3419` gives no badge boost in link, e-Reader, recorded, Frontier or Secret Base battles; ours still applies BADGE01 and BADGE07 to our attacks, a 10% over-prediction there.
- **Mud Sport and Water Sport** (`_util.py:402-406` todo vs `pokemon.c:3215-3218`); **Focus Band, Endure and False Swipe** clamping to HP−1 (`:1677-1696`).
- **Fixed-damage returns ignore type immunity.** `_util.py:215-228` returns *after* multiplying by 0, so Seismic Toss vs Ghost and Night Shade vs Normal (and Sonicboom vs Ghost, once KI-109 is fixed) are predicted at full damage, while the game's `typecalc` makes them miss (`battle_scripts_1.s:1200,1725`). This is already noted in KI-109.
- **Eruption and Water Spout** use 150 power; the true power is `150*hp/maxHP` (`:9379-9390`).
- **Hidden Power Electric under Charge.** Ours doubles it; the decomp keys Charge on the static type (`:1298`).
- **Psywave's MIN, if the name is fixed.** `_util.py:228` returns min = L, but the true min is `L*50/100` (`:7939`). For KI-109 as filed this is an *over*-statement of the min. It matters for a "guaranteed progress" test built on `min`.

### KI-110: not in the audited direction at all

- `_util.py:342-343` (BADGE08 → our Sp. Def) only fires when `defender_is_player`. M1 audits OUR attacks on the foe, so `defender_is_player` is always False.
  - ⇒ **Any M1a row "pinning the BADGE07 Sp. Def finding" in the our-attack direction passes VACUOUSLY.** It must be a foe→us row.
- Even in that direction, KI-110 only *over*-predicts incoming special damage, and only between badge 7 and badge 8. That is the safe side for survival. The one exception is a Secret Base or Frontier battle after badge 8: there ours applies a boost the game does not, and so under-predicts incoming damage by about 9%.
- This matches KI-110's own "Reach today: none" (`05-KNOWN-ISSUES.md:3122`).

---

## 2. Implications for M1a (the pure probe)

1. **Port order matters.** Apply crit, dmgMultiplier, Charge and Helping Hand to the base damage BEFORE STAB and type. Apply types in `gTypeEffectiveness` order with a min-1 floor per step. Apply the random factor last. That is `Cmd_damagecalc` `:1296-1301`, then `Cmd_typecalc` `:1369-1406`, then `:1639-1651`. A port that copies our order will report 0 deviation, by construction.
2. **Report the maximum under-prediction by enumeration, not sampling.** The error depends only on the post-base value B, STAB and the multiplier multiset. An exhaustive sweep over B from 2 to 5000 took about 1 s here (`m1_bound.py`). **The expected results, to pre-register:**
   - non-crit: 1 HP (D2/D3);
   - crit: **4 HP**;
   - crit with Charge: **8 HP**.
3. **MARGIN 3 < 4.** The acceptance "0 over crit_max + 3" can be broken by a correct 4×-effective STAB crit, whenever B is odd. Realistic cases:
   - Makuhita's Fighting moves vs the Aron line (Granite Cave);
   - Marshtomp's Mud Shot or Mud-Slap vs Magnemite;
   - Electrike's Electric moves vs Wingull and Pelipper;
   - Grass moves vs Barboach and Geodude.

   Any one of these fails M1b. Choose one fix:
   - (a) fix D1 in `_util.py` (move the crit and Charge multiplications ahead of the STAB/type block);
   - (b) compute `crit_max` for M1b with the decomp-order port;
   - (c) set MARGIN ≥ 4, or 8 if Charge can occur.

   For comparison, stage 2's `ub = ceil(W·crit_max·1.10)+3` already absorbs D1 whenever crit_max ≥ 10 (checked: at B = 3, 36 ≤ ceil(32 × 1.1) + 3 = 39).
4. **KI-109 rows.** Sonicboom: ours [2,3] vs true 20. Psywave at L30: ours [2,3] vs true [15,45]. After the fix, test Psywave's min separately: L vs L/2.
5. **The KI-110 row must use foe→us.** Our-attack rows are vacuous (§1).
6. **The whitelist must be keyed on EFFECT, and EFFECT_HIT alone is not enough.**
   - Surf is `EFFECT_HIT` yet takes the ×2 underwater branch (`battle_scripts_1.s:236-240`).
   - The safe family is the single-hit, fixed-power effects: HIT, the `*_HIT` secondary-effect set, HIGH_CRITICAL, QUICK_ATTACK, ALWAYS_HIT, TRI_ATTACK, THAW_HIT, POISON_FANG, BLAZE_KICK, POISON_TAIL, VITAL_THROW, SECRET_POWER, PAY_DAY, KNOCK_OFF, THIEF, RAPID_SPIN, ABSORB, RECOIL, DOUBLE_EDGE, SUPERPOWER, OVERHEAT, FAKE_OUT, RAMPAGE, RECHARGE, UPROAR, SKY_UPPERCUT, THUNDER and RAGE. **That set is what the fuzz exercised.**
   - It is only safe provided none of B2, B5, B6, B9, B13 or B14 applies. Exclude everything in Tier A, B1-B4 and B12.
   - Move names that diverge from display spelling in `moves.json`: "Sonicboom", "Psywave", "Solarbeam", "Selfdestruct", "Doubleslap", "Smellingsalt". **Never dispatch on names.**
7. **Rows for the ability deviations:** Guts + burn (B3), Marvel Scale on the wrong battler (B8), Plus/Minus against the foe (B7), Flash Fire frozen (B16) and Struggle (A9). Each is a one-line decomp citation and an exact expected value.

## 3. Implications for M1b (the live audit): sample hazards that will READ as under-predictions

Recommendation: compute the prediction at BOTH reads and compare against the larger. That is, `pred_before` from the decision state, and `pred_after` from the post-turn state with the foe's HP restored. This mechanically absorbs B5, B9, B13 and B14 and the in-turn status for Guts and Facade. If that is not done, the following must be explicit exclusions:

1. **Our side changed during the turn:**
   - our HP crossed maxHP/3 with a pinch ability matching the move type (B9);
   - our status1 changed while we have Guts, or we used Facade (B3, B2);
   - our Atk or SpA stage rose (B5);
   - our Flash Fire flag was set (B10).
2. **Field or foe changed during the turn:**
   - the weather changed (B13);
   - the foe's `status3` gained Minimized, Underground, Underwater or On Air (B14);
   - the foe's Def or SpD stage fell before our hit (e.g. its own Superpower).
3. ‼ **Every foe-side exclusion must be evaluated at EITHER read, not only the "before" read.**
   - Our own Ember or Poison Sting can burn or poison the foe THIS turn, and the end-of-turn tick lands the same turn. A before-read test misses it.
   - Our Confusion can confuse a slower foe, which may then hit itself the same turn.
   - Our own trap move (Wrap, Fire Spin, Whirlpool, Sand Tomb, Clamp, Bind) starts its end-of-turn chip immediately.
   - The spec's wording, "the foe is poisoned, burned or toxic", is ambiguous on this.
4. **Our Future Sight or Doom Desire pending against the foe** (A10). This is not in the spec's list.
5. **Multi-hit moves** (B1): the HP delta is the SUM of the hits. Either exclude them or compare against `hits × crit_max`.
6. **Double battles.** The spec does not exclude them. Both our battlers can hit the same foe, and the foe's partner's Earthquake or Explosion hits it too. Exclude doubles, or attribute per hit.
7. **Struggle** (A9): exclude it, or model it as typeless.
8. **A possible instrument that sidesteps most exclusions (rule 7: instrument the ACTION).**
   - `Cmd_datahpupdate` records the HP our hit dealt in `gProtectStructs[foe].physicalDmg` or `specialDmg`, together with `physicalBattlerId` or `specialBattlerId`, and skips passive end-of-turn damage (`battle_script_commands.c:1938-1960`, the `HITMARKER_PASSIVE_HP_UPDATE` test).
   - But `TurnValuesCleanUp(FALSE)` zeroes `gProtectStructs` at the END of every turn (`battle_main.c:3974` → `:4871-4873`). So it must be polled **mid-turn**. It is not readable at the next decision.
   - A multi-hit move overwrites it per hit.
   - Hidden Power is recorded as physical (the comment at `:1850-1853`).
   - **Feasibility of mid-turn polling in our harness: UNVERIFIED.**
9. **The trainer stratum.** Besides AI item use and switching (already listed), a trainer's Milotic (B8), its Reflect or Light Screen with our Brick Break (B4), and Helping Hand in doubles (B11) are all live there.

## 4. Implications for W stage 2 (outside M1's remit, flagged because it is the consumer)

- **The in-turn raises exist for the policy itself**, not only for the audit: B5 (a foe that knows Swagger/Flatter), B9 (our pinch ability with our HP ≤ maxHP/3 plus the foe's max hit), B13 (a foe that knows Sunny Day or Rain Dance), B14 (a foe that knows Minimize, Dig or Fly), and B3 (a foe that can burn a Guts attacker).
- The design names "Swagger/Rain/Air Lock" rows (DESIGN-v2 `:638`). **W's full definition was not located (UNVERIFIED)**. If it does not cover pinch, Guts, Minimize or semi-invulnerable, Flash Fire and Sunny Day, then `ub` under-bounds them.
- ‼ **SmellingSalt vs a target the policy paralysed** doubles the damage AND removes the paralysis (B2). Keep SMELLINGSALT off the damage whitelist.

## 5. Side findings (not damage-formula deviations)

- **A party `Pokemon` attacker "works" only by accident.**
  - `BattleStateSide.__contains__` returns `NotImplemented` for a non-`BattlePokemon` (`battle_state.py:370-377`), and `x in side` then evaluates `bool(NotImplemented)`. Measured on Python 3.12: **True, with a DeprecationWarning**. (Python 3.14 behaviour: UNVERIFIED; I believe it becomes a TypeError.)
  - `partner_for` then returns our own active battler as the attacker's "partner" (`:431-435`).
  - The same object type also ignores stat stages (`_util.py:428-429,471-472`), which under-predicts after Howl, Growth, Swords Dance and similar.
  - The KI-95 ranker passes party `Pokemon` objects (`story_mode.py:459-481`). **M1b and W must pass the `BattlePokemon`.**
- **The crit branch has never run in production.** No caller passes `is_critical_hit=True`: the only call sites are `_util.py:262`, `lose_on_purpose.py:26` and `story_mode.py:481`. M1a is its first user; the fuzz above is its first test.
- **Defense can reach 0 with Explosion at −6 on a foe with Def ≤ 7.** `pokemon.c:3230` halves Def, then the −6 ratio at `:3257` takes it to 0. Ours raises `ZeroDivisionError` (`_util.py:438`), and `get_strongest_move_against` does not catch it. This is an edge case.

## Scratch artifacts (not in the repo)

These are in `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/`:
- `m1_harness.py`: drives the real calculator from synthetic `gBattleMons`.
- `m1_decomp_port.py`: the independent port.
- `m1_examples.py`, `m1_dbg2.py`, `m1_dbg3.py`: the worked examples.
- `m1_fuzz.py`, `m1_fuzz2.py`: the differential fuzz.
- `m1_bound.py`: the exhaustive rounding bounds.
- `decomp/`: the fetched pokeemerald sources.
