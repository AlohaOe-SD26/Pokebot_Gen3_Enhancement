> ⚠ A NOTE (step 11 prediction support, 2026-09-30). See ../2026-09-30-dmgcalc11-PREDICTIONS.md.

# M1a row spec (design v2 step 11) — the INPUTS of every pre-registered row

Common to every row unless the row says otherwise: a SINGLE battle; no weather; no screens; no held items; all stat
stages 0; no status; no badges (every badge flag clear); no crit; attacker level 50; the random factor spans its full
range (report [min, max] = the r = 15 and r = 0 ends: 85% and 100%); IVs irrelevant except in the Hidden Power rows.
"Ours" = our side (player), "foe" = the opponent. Types are given in ROM order (gBattleMons type1, type2).

## Group D: after-the-base arithmetic (the base damage B is GIVEN: the value CalculateBaseDamage returns, +2 included)

| Row | Move (type, category) | Attacker types | Defender types (ROM order) | B | crit | Charge |
|---|---|---|---|---|---|---|
| D-A1 | a Fighting move (physical) | Fighting (STAB) | Normal, Rock | 3 | yes | no |
| D-A2 | Spark (Electric, physical in Gen 3) | Electric (STAB) | Water, Flying | 3 | yes | yes |
| D-A3 | Mud-Slap (Ground) | Water, Ground (STAB) | Electric, Steel | 5 | yes | no |
| D-N1 | Bite (Dark) | Dark (STAB) | Dark, Ghost | 5 | no | no |
| D-N2 | Signal Beam (Bug) | Water (no STAB) | Steel, Flying | 2 | no | no |
| D-O1 | a Fighting move | Water (no STAB) | Rock, Flying | 3 | no | no |

## Group B: the base term (full inputs; every stat is the battle stat, stages 0)

| Row | Attacker (side, level, relevant stat, types, ability, status) | Defender (side, relevant stat, HP, types, ability, status) | Move | Other |
|---|---|---|---|---|
| B-MS1 | ours, L50, Atk 100, Water, no ability of note, healthy | foe, Def 100, HP 200, Water, Marvel Scale, BURNED | Tackle (Normal, 35) | — |
| B-MS2 | ours, L50, Atk 100, Water, POISONED | foe, Def 100, HP 200, Water, Marvel Scale, healthy | Tackle (Normal, 35) | — |
| B-GUTS | ours, L50, Atk 100, Normal, GUTS, BURNED | foe, Def 100, HP 200, Water, no ability of note | Quick Attack (Normal, 40) | STAB |
| B-BB | ours, L50, Atk 100, Fighting, healthy | foe, Def 100, HP 200, Normal | Brick Break (Fighting, 75) | REFLECT on the foe's side |
| B-KI110 | FOE attacks us: L50, SpAtk 100, Water | OURS, SpDef 100, HP 200, Dark | Water Gun (Water, 40) | BADGE07 set, BADGE08 clear; also report the same row with BADGE08 set and BADGE07 clear |
| B-KI111 | ours, L50, SpAtk 100, Grass | foe, SpDef 100, HP 200, Water | Solarbeam (Grass, 120) | RAIN (the damage turn) |
| B-STR | ours, L50, Atk 100, Normal | foe, Def 100, HP 200, Ghost | Struggle (Normal, 50) | — |
| B-HP | ours, L50, SpAtk 100, Normal, IVs HP31 Atk31 Def31 Spe31 SpA31 SpD31 | foe, SpDef 100, HP 200, Normal | Hidden Power | report its type and power, then the damage |
| B-HPC | ours, L50, SpAtk 100, Normal, IVs chosen so Hidden Power rolls ELECTRIC (state them) | foe, SpDef 100, HP 200, Water | Hidden Power | our side CHARGED (STATUS3_CHARGED_UP) |
| B-SONIC | ours, L30, Normal | foe, HP 200, Normal | Sonicboom | — |
| B-PSY | ours, L30, Psychic | foe, HP 200, Normal | Psywave | — |
| B-NS | ours, L30, Ghost | foe, HP 200, Normal | Night Shade | — |
| B-ST | ours, L30, Fighting | foe, HP 200, Ghost | Seismic Toss | — |
| B-SF | ours, L30, Normal | foe, HP 200 (current), Ghost | Super Fang | — |

For each row report the damage as [min, max] with the random factor's two ends (where the move has no random factor,
say so and give the single value; for Psywave give its own range), and 0 where the move cannot hit (type immunity).
